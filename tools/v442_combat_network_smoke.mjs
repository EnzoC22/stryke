import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.STRYKE_TEST_URL || 'http://127.0.0.1:8765/';
const browser = await chromium.launch({
  headless: true,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--disable-dev-shm-usage']
});
const diagnostics = [];

function instrument(html) {
  const needle = /<\/script>\s*<\/body>/i;
  assert(needle.test(html), 'Main game module tag not found');
  const hook = String.raw`
// V44.2 browser-only probe; game production source is unmodified.
window.__v441 = {
  localPeer() {
    const Native=window.Peer;
    if(typeof Native!=="function") throw Error("PeerJS not loaded");
    window.Peer=function LocalPeer(id,opts) {
      const local={host:"127.0.0.1",port:9000,path:"/peer",key:"peerjs",secure:false,
        debug:1,config:{iceServers:[]}};
      if(id && typeof id==="object") return new Native({...id,...local});
      return new Native(id,{...(opts||{}),...local});
    };
    window.Peer.prototype=Native.prototype;
  },
  setName(value){ CFG.name=value; $("#inName").value=value; },
  configureRounds(){
    if(!NET.isHost||!LB.on||typeof LB.getForm!=="function")throw Error("Host lobby unavailable");
    const old=LB.getForm;
    LB.getForm=()=>({...old(),mode:"rounds",preset:"competitive",map:"vanta",rounds:3,bots:0});
  },
  configureFiveVsFive(){
    if(!NET.isHost||!LB.on||typeof LB.getForm!=="function")throw Error("Host lobby unavailable");
    const old=LB.getForm;
    LB.getForm=()=>({...old(),mode:"rounds",preset:"competitive",map:"cargo",rounds:3,bots:8});
  },
  startMatch(){ if(!NET.isHost||!S.lobby)throw Error("Not host lobby");lobbyStart(); },
  endRound(team="t"){
    if(!NET.isHost||!["freeze","live"].includes(S.phase))throw Error("Round not active");
    if(team==="lead")team=S.score.t>=S.score.ct?"t":"ct";
    srvEndRound(team,"tempo");
  },
  nextRound(){
    if(!NET.isHost||S.phase!=="end")throw Error("Not in round-end");
    srvStartRound();srvState();
  },
  buyKevlar(){
    if(NET.isHost||!inGame)throw Error("Guest not in game");
    sendToHost({t:"buy",it:"kevlar"});
  },
  sendChat(value){
    if(!inGame)throw Error("Cannot chat outside match");
    sendToHost({t:"chat",txt:value});
  },
  closeLink(){
    if(NET.isHost||!NET.hostConn?.open)throw Error("Guest link unavailable");
    NET.hostConn.close();
  },

  suppressPositions(){
    if(NET.isHost||!NET.hostConn?.open)throw Error("Not connected guest");
    if(this._posFiltered)return;
    const original=NET.hostConn.send.bind(NET.hostConn);
    NET.hostConn.send=(msg)=>msg?.t==="pos"?undefined:original(msg);
    this._posFiltered=true;
  },
  emit(message){
    if(NET.isHost||!NET.hostConn?.open)throw Error("No live guest connection");
    sendToHost(message);
  },
  duelSetup(){
    if(!NET.isHost||S.st.mode!=="rounds"||!inGame)throw Error("Host not in rounds");
    const victim=S.players.get("h"),shooter=[...S.players.values()].find(p=>!p.isBot&&p.id!=="h");
    if(!victim||!shooter||shooter.team===victim.team)throw Error("Missing opponents");
    const nodes=NAV?.nodes||[],Y=SPAWNS.a?.[0]?.[1]??0;
    let selected=null;
    outer:for(let i=0;i<nodes.length;i++){
      const a=nodes[i];
      if(!footFree(a.x,a.z))continue;
      for(let j=i+1;j<nodes.length;j++){
        const b=nodes[j];
        const dx=a.x-b.x,dz=a.z-b.z,d=Math.hypot(dx,dz);
        if(d<3.5||d>7||!footFree(b.x,b.z))continue;
        const gun=new V3(b.x,Y+EYE_STAND,b.z),target=new V3(a.x,Y+1.15,a.z);
        if(!visaoLivre(gun,target)||!visaoLivre(new V3(a.x,Y+EYE_STAND,a.z),gun))continue;
        selected={a,b,d,Y};break outer;
      }
    }
    if(!selected)throw Error("Cannot find open duel lane in navmesh");
    const {a,b,d,Y:y}=selected;
    const yaw=Math.atan2(-(a.x-b.x),-(a.z-b.z));
    const pitch=Math.atan2((y+1.15)-(y+EYE_STAND),d);
    srvSpawn(victim,[a.x,y,a.z],true);
    srvSpawn(shooter,[b.x,y,b.z],true,yaw);
    shooter.yaw=yaw;shooter.pitch=pitch;shooter.dentroN=0;
    victim.dentroN=0;
    S.phase="live";S.phaseEnd=now+100;S.liveStart=now;srvState();
    const weapon=shooter.inv.secondary;
    if(!isW(weapon)||!temArmaZ(shooter,weapon))throw Error("Invalid shooter weapon "+weapon);
    return {shooter:shooter.id,victim:victim.id,gun:[b.x,y+EYE_STAND,b.z],
      endpoint:[a.x,y+1.15,a.z],yaw,pitch,weapon,
      hostCanSee:veJogador(shooter,victim),distance:d};
  },
  bombSetup(){
    if(!NET.isHost||!inGame||S.st.mode!=="rounds")throw Error("Not in competitive match");
    if(S.phase==="end")srvStartRound();
    const attacker=[...S.players.values()].find(p=>!p.isBot&&p.team==="t");
    const defender=[...S.players.values()].find(p=>!p.isBot&&p.team==="ct");
    if(!attacker||!defender||!curMap?.sites?.A)throw Error("No T/CT/sites");
    const r=curMap.sites.A,midX=(r[0]+r[1])/2,midZ=(r[2]+r[3])/2,y=SPAWNS.a?.[0]?.[1]??0;
    const pts=[];
    for(let x=r[0]+.7;x<r[1]-.3;x+=.7)for(let z=r[2]+.7;z<r[3]-.3;z+=.7)
      if(footFree(x,z))pts.push([x,z]);
    pts.sort((a,b)=>Math.hypot(a[0]-midX,a[1]-midZ)-Math.hypot(b[0]-midX,b[1]-midZ));
    const pt=pts[0];if(!pt)throw Error("No free planting point");
    let ctPt=pt;
    for(const q of pts){const d=Math.hypot(q[0]-pt[0],q[1]-pt[1]);if(d>.9&&d<1.8){ctPt=q;break}}
    srvSpawn(attacker,[pt[0],y,pt[1]],true);
    srvSpawn(defender,[ctPt[0],y,ctPt[1]],true);
    S.bomb={st:"carried",by:attacker.id,pos:attacker.pos.slice(),end:0,pl:false};
    S.phase="live";S.liveStart=now;S.phaseEnd=now+RC.round;
    srvState();
    return {attacker:attacker.id,defender:defender.id,site:inSite(pt[0],pt[1]),
      position:attacker.pos.slice(),defenderPos:defender.pos.slice(),
      kit:defender.kit,round:S.round,sitePoint:pt};
  },
  nextCompetitiveRound(){if(!NET.isHost||S.phase!=="end")throw Error("Round not over");srvStartRound();srvState()},
  accelerateBomb(){
    if(!NET.isHost||S.bomb?.st!=="planted")throw Error("Not a planted bomb");
    S.bomb.end=now-.25;bombTick();srvState();
  },
  snapCombat(){
    const host=NET.isHost;
    return {
      inGame,host,online:!!NET.online,phase:host?S.phase:C.phase,
      round:host?S.round:C.round,score:host?{...S.score}:C.sc,
      bomb:host?{...S.bomb}:(C.bomb ? {...C.bomb, st:C.bomb.s} : null),
      players:host?[...S.players.values()].filter(p=>!p.isBot).map(p=>({
        id:p.id,team:p.team,pos:p.pos.slice(),yaw:p.yaw,pitch:p.pitch,
        hp:p.hp,armor:p.armor,kit:p.kit,alive:p.alive,
        act:p.act?.k,anoms:p.anom?.length||0,weapon:p.inv.secondary
      })):[...C.players.values()].map(p=>({
        id:p.id,team:p.tm,hp:p.hp,alive:p.al
      })),
      myHp:me.hp,myAlive:me.alive,myPos:me.pos?.toArray?.()
    };
  },
  snapshot(){
    const host=NET.isHost;
    const all=host?[...S.players.values()]:[...C.players.values()];
    return {
      host,online:!!NET.online,code:NET.code,joining:!!NET.joining,
      connected:!!NET.hostConn?.open,inGame:!!inGame,lobby:!!(host?S.lobby:LB.on),
      lobbyVisible:!$("#lobby").classList.contains("hidden"),
      myId:C.myId,mode:(host?S.st:C.st)?.mode,map:(host?S.st:C.st)?.map,
      myMoney:me.money,myArmor:me.armor,myAlive:me.alive,
      botCount:host?all.filter(p=>p.isBot).length:null,
      teamCounts:{
        t:all.filter(p=>(host?p.team:p.tm)==="t").length,
        ct:all.filter(p=>(host?p.team:p.tm)==="ct").length
      },
      chatText:$("#chatlog")?.textContent?.slice(-350)||"",
      round:host?S.round:C.round,phase:host?S.phase:C.phase,
      bombState:host?S.bomb?.st:C.bomb?.s,
      score:host?S.score:C.sc,
      livePlayers:host?all.filter(p=>!p.isBot).map(p=>({
        id:p.id,name:p.name,team:p.team,alive:p.alive,armor:p.armor,money:p.money
      })):all.map(p=>({id:p.id,name:p.n,team:p.tm,alive:p.al})),
      roster:(LB.data?.pl||[]).map(p=>({id:p.id,name:p.n,team:p.tm})),
      joinStatus:$("#joinStatus")?.textContent||"",
      gameStatus:$("#center")?.textContent?.slice(0,120)||""
    };
  }
};
`;
  // Test-only CSP adjustment: allow the local PeerServer WebSocket during the test.
  // The checked-in game HTML and its production Content Security Policy stay unchanged.
  const htmlLocal = html.replace(/<meta\b[^>]*http-equiv\s*=\s*["']Content-Security-Policy["'][^>]*>/gi, '');
  return htmlLocal.replace(needle, hook + '\n$&');
}

async function setupPage(context, label) {
  const page = await context.newPage();
  page.on('pageerror', e => diagnostics.push(label + ' JS ' + e.message.slice(0,250)));
  page.on('console', m => {
    if (m.type()==='error') console.log('CONSOLE',label,m.text().slice(0,250));
  });
  await page.route('**/*', async route => {
    const request = new URL(route.request().url());
    const served = new URL(base);
    if (request.origin!==served.origin ||
        (request.pathname!=='/' && request.pathname!=='/index.html')) return route.continue();
    const fetched = await route.fetch();
    const html = await fetched.text();
    await route.fulfill({response:fetched,body:instrument(html)});
  });
  const response = await page.goto(base,{waitUntil:'domcontentloaded',timeout:70000});
  assert.equal(response.status(),200,'initial HTML response not 200');
  await page.locator('#btnHost').waitFor({state:'visible',timeout:60000});
  await page.waitForFunction(() => typeof window.__v441 === 'object' && typeof window.Peer === 'function',
    null, {timeout:60000});
  await page.evaluate(() => window.__v441.localPeer());
  console.log('PASS',label,'boot and local signaling configured');
  return page;
}

const state = async page => page.evaluate(() => window.__v441.snapshot());
async function until(page,predicate,label,ms=45000) {
  try {
    await page.waitForFunction(predicate, null, {timeout:ms,polling:200});
  } catch (e) {
    console.error('STATE TIMEOUT',label,JSON.stringify(await state(page)));
    throw e;
  }
}
async function output(page,label) { console.log('STATE',label,JSON.stringify(await state(page))); }

try {
  const hostContext=await browser.newContext({viewport:{width:1280,height:800}});
  const guestContext=await browser.newContext({viewport:{width:1280,height:800}});
  const host=await setupPage(hostContext,'host');
  const guest=await setupPage(guestContext,'guest');

  await host.locator('#inName').fill('V442 Host');
  await guest.locator('#inName').fill('V442 Guest');
  await host.locator('#btnHost').click({timeout:20000});
  await until(host,() => window.__v441.snapshot().online && !!window.__v441.snapshot().code,'host signaling');
  const code=(await state(host)).code;
  assert.match(code,/^[A-Z0-9]{5}$/,'unexpected room code');
  await output(host,'host lobby opened');

  await guest.locator('#inCode').fill(code);
  await guest.locator('#btnJoin').click({timeout:15000});
  await until(guest,() => {
    const s=window.__v441.snapshot();
    return s.online && s.lobby && s.roster.length>=2 && /^p\d+$/.test(s.myId||'');
  },'guest welcome + lobby roster',60000);
  await until(host,() => window.__v441.snapshot().livePlayers.length===2,
    'host receives guest',25000);
  await output(host,'two players host');
  await output(guest,'two players guest');
  assert.equal((await state(guest)).roster.length,2,'guest lobby should show two players');
  assert.equal((await state(host)).livePlayers.filter(x=>x.name==='V442 Guest').length,1,
    'host has duplicate or missing guest');
  console.log('PASS two-browser PeerJS lobby join, unique players, roster sync');


  await host.evaluate(()=>window.__v441.configureRounds());
  await host.locator('#lbGo').click({timeout:15000});
  await until(host,()=>window.__v441.snapshot().inGame && window.__v441.snapshot().round===1,
    'competitive match starts on host',45000);
  await until(guest,()=>window.__v441.snapshot().inGame &&
    window.__v441.snapshot().livePlayers.length===2,'guest sees both players',50000);
  console.log('PASS combat smoke: both real WebRTC players spawned');

  // Suppress routine position packets only during the test-only controlled combat fixtures.
  // The actual shot, hit and bomb packets still travel through PeerJS/WebRTC.
  await guest.evaluate(()=>window.__v441.suppressPositions());
  const lane=await host.evaluate(()=>window.__v441.duelSetup());
  console.log('DUEL_FIXTURE',JSON.stringify(lane));
  assert(lane.hostCanSee,'duel requires a server-visible target');
  await until(guest,()=>window.__v441.snapCombat().phase==='live',
    'round goes live',12000);
  await guest.waitForTimeout(500);
  const initialHp=(await host.evaluate(()=>window.__v441.snapCombat())).players
    .find(p=>p.id===lane.victim).hp;
  assert.equal(initialHp,100,'victim must have full HP');

  // A forged hit without a preceding authorized shot must be rejected.
  await guest.evaluate(({victim,weapon})=>
    window.__v441.emit({t:'hit',v:victim,w:weapon,z:'body',dmg:999999}),
    lane);
  await guest.waitForTimeout(450);
  assert.equal((await host.evaluate(()=>window.__v441.snapCombat())).players
    .find(p=>p.id===lane.victim).hp,100,'unpaired hit must not damage the victim');
  console.log('PASS anti-cheat: hit without preceding shot causes no damage');

  // A far-away movement packet must not teleport the opponent.
  const beforePos=(await host.evaluate(()=>window.__v441.snapCombat())).players
    .find(p=>p.id===lane.shooter).pos;
  await guest.evaluate(()=>window.__v441.emit({
    t:'pos',p:[10000,900,10000],y:0,pi:0,c:0,sq:1,ts:performance.now()/1000
  }));
  await guest.waitForTimeout(400);
  const afterPos=(await host.evaluate(()=>window.__v441.snapCombat())).players
    .find(p=>p.id===lane.shooter).pos;
  assert(Math.hypot(afterPos[0]-beforePos[0],afterPos[2]-beforePos[2])<5,
    'anti-cheat must not accept impossible teleport');
  console.log('PASS anti-cheat: implausible remote teleport rejected');

  // A genuine paired shot is relayed and the host caps an exaggerated damage claim.
  await guest.waitForTimeout(800);
  await guest.evaluate(({gun,endpoint,weapon,victim})=>{
    window.__v441.emit({t:'shot',w:weapon,o:gun,e:[endpoint]});
    window.__v441.emit({t:'hit',v:victim,w:weapon,z:'body',dmg:999999});
  },lane);
  await until(host,()=>{
    const victim=window.__v441.snapCombat().players.find(p=>p.id==='h');
    return victim && victim.hp<100;
  },'authoritative shot and damage',12000);
  const hpAfterShot=(await host.evaluate(()=>window.__v441.snapCombat())).players
    .find(p=>p.id==='h').hp;
  assert(hpAfterShot>=30 && hpAfterShot<100,
    'server must cap exaggerated damage to the weapon rules');
  console.log('PASS gunplay: real guest shot+hit accepted, damage clamped by authoritative host, HP='+hpAfterShot);
  await until(guest,()=>window.__v441.snapCombat().players.some(p=>p.id==='h'&&p.hp<100),
    'victim HP replicated to client',12000);
  console.log('PASS network: damage state replicated to remote client');

  await guest.evaluate(({victim,weapon})=>
    window.__v441.emit({t:'hit',v:victim,w:weapon,z:'body',dmg:999999}),lane);
  await guest.waitForTimeout(400);
  assert.equal((await host.evaluate(()=>window.__v441.snapCombat())).players
    .find(p=>p.id==='h').hp,hpAfterShot,
    'duplicate hit without fresh shot must be rejected');
  console.log('PASS anti-cheat: duplicate hit cannot reuse the preceding shot');

  // Deterministically isolate bomb plant/defuse state, while packets remain real.
  const stage=await host.evaluate(()=>window.__v441.bombSetup());
  console.log('BOMB_FIXTURE',JSON.stringify(stage));
  assert.equal(stage.round,1);
  assert.equal(stage.site,'A');
  assert.equal(stage.attacker,'h');
  assert.equal(stage.defender,lane.shooter);
  await until(guest,()=>window.__v441.snapCombat().bomb?.st==='carried',
    'guest sees carried bomb',12000);

  await guest.evaluate(()=>window.__v441.emit({t:'bomb',on:1}));
  await guest.waitForTimeout(400);
  assert.equal((await host.evaluate(()=>window.__v441.snapCombat())).bomb.st,'carried',
    'CT must not be allowed to plant bomb');
  console.log('PASS bomb anti-cheat: defender cannot plant attacker bomb');

  await host.evaluate(()=>sendToHost({t:'bomb',on:1}));
  await until(host,()=>window.__v441.snapCombat().bomb?.st==='planted',
    'actual planting duration',12000);
  await until(guest,()=>window.__v441.snapCombat().bomb?.st==='planted',
    'plant replication',12000);
  console.log('PASS bomb: attacker planted at site A; remote client received state');

  // Test hold E cancellation before completing defuse.
  await guest.evaluate(()=>window.__v441.emit({t:'bomb',on:1}));
  await until(host,()=>window.__v441.snapCombat().players.some(p=>p.id==='p1'&&p.act==='d'),
    'remote defuse begins',6000);
  await guest.waitForTimeout(650);
  await guest.evaluate(()=>window.__v441.emit({t:'bomb',on:0}));
  await until(host,()=>window.__v441.snapCombat().players.some(p=>p.id==='p1'&&!p.act),
    'remote defuse cancelled',6000);
  assert.equal((await host.evaluate(()=>window.__v441.snapCombat())).bomb.st,'planted',
    'releasing E should not defuse the bomb');
  console.log('PASS bomb: releasing use cancels defuse before completion');

  await guest.evaluate(()=>window.__v441.emit({t:'bomb',on:1}));
  await until(host,()=>window.__v441.snapCombat().bomb?.st==='defused',
    'remote defuse completes',22000);
  await until(guest,()=>window.__v441.snapCombat().phase==='end' &&
    window.__v441.snapCombat().score?.ct===1,'defuse victory replication',13000);
  console.log('PASS bomb: remote CT defused, round result and score replicated');

  const round2=await host.evaluate(()=>window.__v441.bombSetup());
  console.log('BOMB_EXPLOSION_FIXTURE',JSON.stringify(round2));
  await host.evaluate(()=>sendToHost({t:'bomb',on:1}));
  await until(guest,()=>window.__v441.snapCombat().bomb?.st==='planted',
    'second plant broadcast',12000);
  await host.evaluate(()=>window.__v441.accelerateBomb());
  await until(guest,()=>window.__v441.snapCombat().phase==='end' &&
    window.__v441.snapCombat().score?.t===1,'explosion victory replicated',16000);
  console.log('PASS bomb: explosion and attacker victory replicated');

  // RTT-resistant message channel: introduce test-only 450ms delay on one chat message.
  await guest.evaluate(()=>{
    const channel=NET.hostConn,original=channel.send.bind(channel);
    channel.send=(msg)=>{
      if(msg?.t==='chat' && msg.txt==='V442 LAG PROBE'){
        setTimeout(()=>original(msg),450);return;
      }
      return original(msg);
    };
    window.__v441.emit({t:'chat',txt:'V442 LAG PROBE'});
  });
  await until(host,()=>window.__v441.snapshot().chatText.includes('V442 LAG PROBE'),
    'delayed real DataChannel message',10000);
  console.log('PASS network: delayed WebRTC chat delivered without dropping match');

  await guest.evaluate(()=>window.__v441.closeLink());
  await until(host,()=>window.__v441.snapshot().livePlayers.length===1,
    'remote peer disconnect cleans roster',15000);
  console.log('PASS network: connection close removes peer without host shutdown');

  assert.deepEqual(diagnostics,[],'uncaught JavaScript exceptions');
  console.log('RESULT V44.2: TWO CLIENTS, HOST-VALIDATED COMBAT, ANTI-CHEAT, BOMB PLANT/DEFUSE/EXPLOSION, LAG AND DISCONNECT PASSED');
} catch(e) {
  console.error('FAIL V44.2',e.stack||e);
  console.error('JAVASCRIPT DIAGNOSTICS',JSON.stringify(diagnostics.slice(0,10)));
  process.exitCode=1;
} finally {
  await browser.close();
}
