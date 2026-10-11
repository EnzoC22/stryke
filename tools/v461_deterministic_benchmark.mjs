// STRYKE V46.1 - deterministic real-engine competitive match benchmark.
// Instrumentation is injected into test HTTP response only; shipped game is untouched.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const MAPS = ['vanta', 'frostline', 'kairo', 'cargo'];
const MAP = (process.env.V461_MAP || 'cargo').toLowerCase();
assert(MAPS.includes(MAP), 'V461_MAP must be one of '+MAPS.join(', '));
const ROUNDS = Number(process.env.V461_ROUNDS || 2);
assert(Number.isInteger(ROUNDS) && ROUNDS>=1 && ROUNDS<=100, 'V461_ROUNDS must be between 1 and 100');
const SEED = Number(process.env.V461_SEED || 461000);
assert(Number.isSafeInteger(SEED) && SEED>=1 && SEED<=0xffffffff, 'V461_SEED must be a valid uint32');
const REPLAY = process.env.V461_REPLAY !== '0';
const BASE = process.env.STRYKE_TEST_URL || 'http://127.0.0.1:8765/';
const MAX_TICKS = 1600;
const STEP = 0.1;
const errors = [];

function instrument(html) {
  const anchor = /<\/script>\s*<\/body>/i;
  assert(anchor.test(html), 'Final inline script anchor not found');
  // Freeze ONLY the browser-render/background clocks during benchmark iterations.
  // Code changes are HTTP response rewrites and are never committed to index.html.
  const frameAnchor = 'function frame() {\n  requestAnimationFrame(frame);';
  const workerAnchor = 'tw.onmessage = () => {\n    if (!inGame';
  assert.equal(html.split(frameAnchor).length, 2, 'Main frame guard anchor moved');
  assert.equal(html.split(workerAnchor).length, 2, 'Background frame guard anchor moved');
  html = html.replace(frameAnchor, frameAnchor + '\n  if (window.__strykeV461?.active) return;');
  html = html.replace(workerAnchor, 'tw.onmessage = () => {\n    if (window.__strykeV461?.active) return;\n    if (!inGame');
  const fixture = String.raw`
    // Test-only scope: no production debug hooks, no security-policy changes.
    window.__strykeV461 = {
      active: false, current: null, map: null, time: 1000, state: 0,
      rand() {
        this.state = (Math.imul(1664525, this.state) + 1013904223) >>> 0;
        return this.state / 4294967296;
      },
      withRng(fn) {
        const original = Math.random;
        Math.random = () => this.rand();
        try { return fn(); } finally { Math.random = original; }
      },
      setup(map) {
        if (this.active || NET.isHost || NET.online || inGame) throw Error('Only idle offline fixture supported');
        this.active = true; this.map = map;
        // Build real collision and navgraph once; rendering is paused for deterministic rounds.
        buildMap(map);
        const n = NAV?.nodes?.length || 0;
        if (n < 20) throw Error('Navigation not initialized');
        if (!curMap.sites?.A || !curMap.sites?.B) throw Error('Two bombsites required');
        const priorKill = srvKill;
        const probe = this;
        srvKill = function(v, a, w, hs) {
          if (probe.current && S.phase === 'live' && v?.alive) {
            const evt = { t: Math.round((now-S.liveStart)*10)/10,
              victim:v.id, victimTeam:v.team, attacker:a?.id||null,
              attackerTeam:a?.team||null, weapon:w||null, headshot:!!hs,
              position:[Math.round(v.pos[0]*10)/10,Math.round(v.pos[2]*10)/10] };
            probe.current.deaths.push(evt);
            if (!probe.current.firstDeath) probe.current.firstDeath = evt;
          }
          return priorKill(v,a,w,hs);
        };
        return { map, nodes:n, version:'V46.1' };
      },
      start(seed) {
        if (!this.active || !this.map) throw Error('Setup required');
        this.time = 1000;
        now = this.time;
        S.players.clear();
        S.nextId = 1; S.colorI = 0; S.stateT = 0;
        S.st = C.st = {mode:'rounds',map:this.map,rounds:13,bots:10,
          diff:1,botRank:false,preset:'competitive'};
        S.lobby = false; S.fromLobby = false;
        S.drops?.clear();
        this.current = null;
        // The map renderer performs an implementation-dependent number of
        // cosmetic random draws as models/materials warm up. Use a SEPARATE
        // deterministic stream for the world, then reseed the gameplay stream.
        // Otherwise map initialization changes site selection / bot tactics.
        this.state = (seed ^ 0x9e3779b9) >>> 0;
        this.withRng(() => buildMap(this.map));
        this.state = seed >>> 0;
        this.withRng(() => {
          for (let i=0;i<10;i++) {
            const p=srvAddPlayer('bot'+i,'V461 Bot '+i,true);
            setTeam(p,i<5?'t':'ct');
          }
          srvStartMatch();
        });
        if(S.phase!=='freeze') throw Error('Real engine failed to start freeze phase: '+S.phase);
        const ps=[...S.players.values()];
        if (ps.length!==10 || ps.filter(p=>p.team==='t').length!==5 ||
            ps.filter(p=>p.team==='ct').length!==5 ||
            ps.some(p=>!p.isBot)) throw Error('Not a valid 5v5 bot round');
        this.time=now=S.phaseEnd+.01;
        this.withRng(() => srvTick(.05));
        if(S.phase!=='live') throw Error('Round did not transition to live: '+S.phase);
        this.current={ seed: seed >>> 0, map:this.map, round:S.round,
          attackSite:S.bSite, winner:null, reason:null, seconds:0,
          firstArrival:{t:{A:null,B:null},ct:{A:null,B:null}},
          firstContact:null,firstDeath:null,deaths:[],stalls:[],routeSamples:0,
          bots:Object.fromEntries(ps.map(p=>[p.id,{
            team:p.team,role:p.bot.role,travel:0,last:[p.pos[0],p.pos[2]],
            stationary:0,stallFlagged:false,maxWaypoints:0,repathCount:0,
            lastRepath:p.bot.repathAt,targetChanges:0,lastTarget:null,
            firstEnemySeen:null
          }]))};
        return {seed,phase:S.phase,players:ps.length,
          starts:ps.map(p=>({id:p.id,team:p.team,position:p.pos,role:p.bot?.role}))};
      },
      advance(ticks) {
        if(!this.current) throw Error('No active round');
        const limit=Math.min(100,Math.max(1,ticks|0));
        for(let j=0;j<limit && S.phase==='live';j++) {
          now=this.time=Math.round((this.time+0.1)*1000)/1000;
          this.withRng(()=>srvTick(.1));
          const r=this.current;
          r.seconds=Math.round((now-S.liveStart)*10)/10;
          if(j%5!==0) continue;
          for(const p of S.players.values()) {
            if(!p.isBot || !p.alive) continue;
            const b=p.bot, m=r.bots[p.id], xy=[p.pos[0],p.pos[2]];
            if(!xy.every(Number.isFinite)) throw Error('Nonfinite position: '+p.id);
            const dist=Math.hypot(xy[0]-m.last[0],xy[1]-m.last[1]);
            m.travel=Math.round((m.travel+dist)*1000)/1000;
            m.last=xy;
            const t=b.target && S.players.get(b.target)?.alive ? b.target:null;
            if(t && t!==m.lastTarget) {
              m.targetChanges++;
              if(m.firstEnemySeen===null) m.firstEnemySeen=r.seconds;
              if(r.firstContact===null) r.firstContact={
                time:r.seconds,observer:p.id,team:p.team,target:t,
                position:xy.map(v=>Math.round(v*10)/10)};
            }
            m.lastTarget=t;
            if(b.repathAt!==m.lastRepath) {m.lastRepath=b.repathAt;m.repathCount++;}
            const routing=b.path?.length>0 && !t && !p.act;
            if(routing) {r.routeSamples++;m.maxWaypoints=Math.max(m.maxWaypoints,b.path.length);}
            if(routing && dist<0.2) m.stationary+=0.5;
            else {m.stationary=0;m.stallFlagged=false;}
            if(m.stationary>=5 && !m.stallFlagged) {
              r.stalls.push({bot:p.id,team:p.team,at:r.seconds,
                position:xy.map(v=>Math.round(v*10)/10),remaining:b.path.length});
              m.stallFlagged=true;
            }
            const site=inSite(xy[0],xy[1]);
            if(site && r.firstArrival[p.team][site]===null)
              r.firstArrival[p.team][site]=r.seconds;
          }
        }
        const r=this.current;
        if(S.phase==='end'||S.phase==='over') {
          const last=S.hist?.[S.hist.length-1]||[];
          r.winner=last[0]||null;r.reason=last[1]||null;
          r.finalBomb=S.bomb?.st||null;
          r.score={...S.score};
          r.teamKills={t:0,ct:0};
          for(const e of r.deaths) if(e.attackerTeam && e.attackerTeam!==e.victimTeam)
            r.teamKills[e.attackerTeam]++;
          for(const b of Object.values(r.bots)) {
            delete b.last;delete b.lastRepath;delete b.lastTarget;
            delete b.stationary;delete b.stallFlagged;
          }
        }
        return {phase:S.phase,seconds:r.seconds};
      },
      result(){return structuredClone(this.current);}
    };
  `.replaceAll('\\`','`');
  return html.replace(anchor, fixture + '\n$&');
}

const browser = await chromium.launch({headless:true,args:[
  '--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--disable-dev-shm-usage']});
const report={schema:1,version:'V46.1',map:MAP,baseSeed:SEED,roundsRequested:ROUNDS,
  simulation:'real STRYKE 5v5 bot AI/physics/combat at fixed 100ms steps',
  caveat:'Diagnostic bot-versus-bot scenarios, not real-human win rates',
  commit:process.env.GITHUB_SHA||null,rounds:[],replayPassed:false,summary:{}};

try {
  const context=await browser.newContext({viewport:{width:1280,height:720}});
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message.slice(0,500)));
  await page.route('**/*',async route=>{
    const req=new URL(route.request().url()),site=new URL(BASE);
    if(req.origin!==site.origin || !['/','/index.html'].includes(req.pathname)) return route.continue();
    const res=await route.fetch();
    return route.fulfill({response:res,body:instrument(await res.text())});
  });
  const response=await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:70000});
  assert.equal(response.status(),200,'Game HTML not reachable');
  await page.locator('#btnHost').waitFor({state:'visible',timeout:70000});
  await page.waitForFunction(()=>!!window.__strykeV461,null,{timeout:45000});
  const init=await page.evaluate(map=>window.__strykeV461.setup(map),MAP);
  report.navNodes=init.nodes;

  async function oneRound(seed) {
    const started=await page.evaluate(seed=>window.__strykeV461.start(seed),seed);
    assert.equal(started.phase,'live');
    assert.equal(started.players,10);
    let status={phase:'live'};
    for(let k=0;k<MAX_TICKS && status.phase==='live';k+=100)
      status=await page.evaluate(n=>window.__strykeV461.advance(n),Math.min(100,MAX_TICKS-k));
    assert(['end','over'].includes(status.phase),'Unfinished simulation '+MAP+' seed '+seed);
    const round=await page.evaluate(()=>window.__strykeV461.result());
    assert(['t','ct'].includes(round.winner),'Missing winner');
    assert(round.seconds>0 && round.seconds<=160,'Invalid elapsed time');
    assert(Object.keys(round.bots).length===10,'Bot roster changed unexpectedly');
    return round;
  }
  // Re-run identical seed on same page after complete reset. Entire report must match.
  if(REPLAY) {
    const sampleSeed=(SEED+MAPS.indexOf(MAP)*100000)>>>0;
    const first=await oneRound(sampleSeed);
    const again=await oneRound(sampleSeed);
    assert.deepEqual(again,first,'Determinism regression for '+MAP+' seed '+sampleSeed);
    report.replayPassed=true;
    console.log('PASS V461 REPLAY',JSON.stringify({map:MAP,seed:sampleSeed,winner:first.winner,seconds:first.seconds}));
  }
  for(let i=0;i<ROUNDS;i++) {
    const seed=(SEED+MAPS.indexOf(MAP)*100000+i)>>>0;
    const r=await oneRound(seed);
    report.rounds.push(r);
    if(i<5 || i%20===19 || i===ROUNDS-1)
      console.log('V461 ROUND',JSON.stringify({map:MAP,index:i+1,seed,
        winner:r.winner,seconds:r.seconds,firstContact:r.firstContact?.time??null,
        firstDeath:r.firstDeath?.t??null,stalls:r.stalls.length}));
  }
  assert.deepEqual(errors,[],'Unexpected browser JavaScript errors');
  const won={t:report.rounds.filter(r=>r.winner==='t').length,
    ct:report.rounds.filter(r=>r.winner==='ct').length};
  const duration=report.rounds.reduce((n,r)=>n+r.seconds,0)/report.rounds.length;
  const stalls=report.rounds.reduce((n,r)=>n+r.stalls.length,0);
  const deaths=report.rounds.flatMap(r=>r.deaths);
  const firstDeaths=report.rounds.filter(r=>!!r.firstDeath).map(r=>r.firstDeath);
  const killedByTeam={t:firstDeaths.filter(d=>d.attackerTeam==='t').length,
    ct:firstDeaths.filter(d=>d.attackerTeam==='ct').length,none:firstDeaths.filter(d=>!d.attackerTeam).length};
  const avg=(xs)=>xs.length?Math.round(xs.reduce((a,b)=>a+b,0)/xs.length*10)/10:null;
  const arrivals={};
  for(const tm of ['t','ct'])for(const site of ['A','B'])
    arrivals[tm+'_'+site]=avg(report.rounds.map(r=>r.firstArrival[tm][site]).filter(Number.isFinite));
  report.summary={count:report.rounds.length,wins:won,attackerWinPct:Math.round(won.t/ROUNDS*1000)/10,
    avgDuration:Math.round(duration*10)/10,stallSignals:stalls,
    firstDeathsByAttacker:killedByTeam,totalDeaths:deaths.length,
    firstSiteArrivals:arrivals,
    averageFirstDeathTime:avg(firstDeaths.map(d=>d.t))};
  fs.mkdirSync('reports',{recursive:true});
  fs.writeFileSync('reports/v461-'+MAP+'.json',JSON.stringify(report,null,2)+'\n');
  console.log('PASS V461',JSON.stringify({map:MAP,...report.summary,replay:report.replayPassed}));
  await context.close();
} catch(e) {
  console.error('FAIL V461',e.stack||e,'BROWSER_ERRORS',JSON.stringify(errors.slice(0,8)));
  process.exitCode=1;
} finally {
  await browser.close();
}
