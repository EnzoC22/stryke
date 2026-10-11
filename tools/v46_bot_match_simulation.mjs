// STRYKE V46: real host-side 5v5 bot simulations in Chromium.
// Test-only hooks are injected into the HTTP response; index.html and CSP are never changed.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.STRYKE_TEST_URL || 'http://127.0.0.1:8765/';
const MAPS = ['vanta', 'frostline', 'kairo', 'cargo'];
const ROUNDS = Math.max(1, Math.min(4, Number(process.env.V46_ROUNDS || 2)));
const DT = 0.10;
const MAX_STEPS = 1600; // 160 simulated seconds, including bomb timer
const report = { version: 'V46', kind: 'actual host-side bot/physics simulation',
  disclaimer: 'Small diagnostic sample, not statistically valid balance or win-rate inference',
  generated: new Date().toISOString(), roundsPerMap: ROUNDS, dt: DT, maps: [] };
const browser = await chromium.launch({ headless: true,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--disable-dev-shm-usage'] });

function instrument(html) {
  const anchor = /<\/script>\s*<\/body>/i;
  assert(anchor.test(html), 'Final inline game module not found');
  const hook = String.raw\`
    // V46 test fixture. None of this is present in deployed production HTML.
    window.__strykeV46 = {
      simulationTime: 0, startTime: 0, roundNumber: 0, current: null,
      setup(map, seed) {
        if (!['vanta','frostline','kairo','cargo'].includes(map)) throw Error('Invalid competitive map');
        if (NET.isHost || NET.online || inGame) throw Error('Fixture requires an idle offline test page');
        this.seed = seed >>> 0;
        Math.random = () => { this.seed = (Math.imul(1664525, this.seed) + 1013904223) >>> 0; return this.seed / 4294967296; };
        S.players.clear();
        S.st = C.st = { mode:'rounds', map, rounds:13, bots:10, diff:1, botRank:false, preset:'competitive' };
        S.lobby = false; S.fromLobby = false;
        buildMap(map);
        for (let i=0; i<10; i++) {
          const p=srvAddPlayer('sim'+i, 'V46 Bot '+i, true);
          setTeam(p, i<5?'t':'ct');
        }
        srvStartMatch();
        const ps=[...S.players.values()];
        if (ps.length!==10 || ps.some(p=>!p.isBot)) throw Error('Fixture must contain exactly ten real engine bots');
        if (ps.filter(p=>p.team==='t').length!==5 || ps.filter(p=>p.team==='ct').length!==5) throw Error('Teams must be 5v5');
        this.simulationTime = now;
        this.roundNumber = 0;
        return { map, roster:ps.map(p=>({id:p.id,team:p.team,bot:!!p.isBot})), navNodes:NAV?.nodes?.length||0,
          sites:Object.keys(curMap.sites||{}),phase:S.phase };
      },
      startRound() {
        if (S.phase==='end') { now=this.simulationTime; srvStartRound(); }
        if (S.phase!=='freeze') throw Error('Expected freeze before round '+S.round+': '+S.phase);
        now=S.phaseEnd+.01; // advance buy/freeze period without changing game rules
        this.simulationTime=now;
        srvTick(.05); // original authoritative timer transition
        if(S.phase!=='live') throw Error('Authoritative round did not transition to live');
        this.roundNumber=S.round;
        const ps=[...S.players.values()];
        this.current = { round:S.round, objective:S.bSite, winner:null, reason:null, seconds:0,
          firstArrival:{t:{A:null,B:null},ct:{A:null,B:null}}, stalls:[], routeSamples:0,
          players: Object.fromEntries(ps.map(p=>[p.id, {team:p.team, role:p.bot?.role,
            last:[p.pos[0],p.pos[2]], still:0, flagged:false, travel:0,
            waypoints:0, reachedSite:false}])) };
        return {round:S.round,phase:S.phase,teams:{t:ps.filter(p=>p.team==='t').length,ct:ps.filter(p=>p.team==='ct').length}};
      },
      advance(steps) {
        if (!this.current || S.phase!=='live') return {phase:S.phase,steps:0};
        const n=Math.max(1,Math.min(100,steps|0));
        for(let j=0;j<n && S.phase==='live';j++) {
          now=this.simulationTime+=.10;
          srvTick(.10); // real authoritative bot AI, movement, combat and bomb state
          this.current.seconds=Math.round((now-S.liveStart)*10)/10;
          if (j%5!==0) continue;
          for(const p of S.players.values()) {
            if(!p.isBot || !p.alive) continue;
            const tr=this.current.players[p.id], xy=[p.pos[0],p.pos[2]];
            if (!Number.isFinite(xy[0]) || !Number.isFinite(xy[1])) throw Error('Non-finite bot position '+p.id);
            const delta=Math.hypot(xy[0]-tr.last[0],xy[1]-tr.last[1]);
            tr.travel+=delta; tr.last=xy;
            const active=!!p.bot?.path?.length && !p.bot?.target && !p.act;
            if(active && delta<.20) tr.still+=.5;
            else { tr.still=0; tr.flagged=false; }
            if(active) {tr.waypoints=Math.max(tr.waypoints,p.bot.path.length);this.current.routeSamples++;}
            if(tr.still>=5 && !tr.flagged) {
              this.current.stalls.push({id:p.id,team:p.team,at:this.current.seconds,
                pos:xy.map(v=>Math.round(v*10)/10),remainingWaypoints:p.bot.path.length});
              tr.flagged=true;
            }
            const site=inSite(xy[0],xy[1]);
            if(site && this.current.firstArrival[p.team][site]===null)
              this.current.firstArrival[p.team][site]=this.current.seconds;
          }
        }
        if(S.phase==='end'||S.phase==='over') {
          const last=S.hist?.[S.hist.length-1]||[];
          this.current.winner=last[0]||null;
          this.current.reason=last[1]||null;
          this.current.finalBomb=S.bomb?.st||null;
          this.current.score={...S.score};
          this.current.kills=Object.fromEntries([...S.players.values()].map(p=>[p.id,p.kills]));
        }
        return {phase:S.phase,seconds:this.current.seconds,score:{...S.score},stalls:this.current.stalls.length};
      },
      roundReport(){return JSON.parse(JSON.stringify(this.current));},
      roster(){return [...S.players.values()].map(p=>({id:p.id,team:p.team,alive:p.alive,bot:p.isBot,role:p.bot?.role}));}
    };
  \`;
  return html.replace(anchor, hook+'\n$&');
}

const errors=[];
async function runMap(map, index) {
  const ctx=await browser.newContext({viewport:{width:1280,height:720}});
  const page=await ctx.newPage();
  page.on('pageerror', e=>errors.push(map+': '+e.message.slice(0,300)));
  await page.route('**/*', async route=>{
    const u=new URL(route.request().url()), base=new URL(BASE);
    if(u.origin!==base.origin || !['/','/index.html'].includes(u.pathname))
      return route.continue();
    const response=await route.fetch();
    return route.fulfill({response,body:instrument(await response.text())});
  });
  try {
    const response=await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:65000});
    assert.equal(response.status(),200,'Game HTML unavailable');
    await page.locator('#btnHost').waitFor({state:'visible',timeout:65000});
    await page.waitForFunction(()=>!!window.__strykeV46,null,{timeout:30000});
    const seed=46000+index*109;
    const initial=await page.evaluate(({map,seed})=>window.__strykeV46.setup(map,seed),{map,seed});
    assert.equal(initial.roster.length,10,map+' missing bots');
    assert(initial.navNodes>0,map+' navgraph not built');
    assert.deepEqual(initial.sites.sort(),['A','B']);
    const perMap={map,seed,navNodes:initial.navNodes,rounds:[]};
    for(let round=0;round<ROUNDS;round++) {
      const start=await page.evaluate(()=>window.__strykeV46.startRound());
      assert.equal(start.phase,'live',map+' never entered live');
      assert.equal(start.teams.t,5);
      assert.equal(start.teams.ct,5);
      let status;
      for(let steps=0;steps<MAX_STEPS;steps+=100) {
        status=await page.evaluate(n=>window.__strykeV46.advance(n),Math.min(100,MAX_STEPS-steps));
        if(status.phase!=='live') break;
      }
      assert(['end','over'].includes(status.phase),map+' round never ended by engine: '+JSON.stringify(status));
      const summary=await page.evaluate(()=>window.__strykeV46.roundReport());
      assert(['t','ct'].includes(summary.winner),map+' missing real winner');
      assert(summary.seconds>0 && summary.seconds<=160,map+' unexpected round duration');
      perMap.rounds.push(summary);
      console.log('V46 ROUND',JSON.stringify({map,round:summary.round,winner:summary.winner,
        reason:summary.reason,seconds:summary.seconds,firstArrival:summary.firstArrival,
        stalls:summary.stalls.length,finalBomb:summary.finalBomb}));
      if(status.phase==='over') break;
    }
    const wins={t:perMap.rounds.filter(r=>r.winner==='t').length,
      ct:perMap.rounds.filter(r=>r.winner==='ct').length};
    perMap.wins=wins;
    perMap.stalls=perMap.rounds.reduce((n,r)=>n+r.stalls.length,0);
    console.log('V46 MAP',JSON.stringify({map,wins,stalls:perMap.stalls,rounds:perMap.rounds.length}));
    return perMap;
  } finally { await ctx.close(); }
}

try {
  for(let i=0;i<MAPS.length;i++) report.maps.push(await runMap(MAPS[i],i));
  assert.equal(report.maps.length,4,'not all maps simulated');
  assert(report.maps.every(m=>m.rounds.length>0),'map without completed round');
  assert.deepEqual(errors,[],'Uncaught browser JS errors');
  fs.mkdirSync('reports',{recursive:true});
  fs.writeFileSync('reports/v46-bot-simulation.json',JSON.stringify(report,null,2)+'\n');
  console.log('PASS V46 actual engine bot rounds',JSON.stringify(report.maps.map(
    m=>({map:m.map,wins:m.wins,stalls:m.stalls,rounds:m.rounds.length}))));
} catch(e) {
  console.error('FAIL V46',e.stack||e,'BROWSER_ERRORS',JSON.stringify(errors.slice(0,15)));
  process.exitCode=1;
} finally {await browser.close();}
