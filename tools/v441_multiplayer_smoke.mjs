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
  const hook = [
    '// V44.1 test-only probe. This code is injected in the served response, never saved to index.html.',
    'window.__v441 = {',
    '  localPeer() {',
    '    const Native = window.Peer;',
    '    if (typeof Native !== "function") throw Error("PeerJS is not loaded");',
    '    window.Peer = function LocalPeer(id, opts) {',
    '      const local = {host:"127.0.0.1",port:9000,path:"/peer",key:"peerjs",secure:false,debug:1,config:{iceServers:[]}};',
    '      if (id && typeof id === "object") return new Native({...id,...local});',
    '      return new Native(id, {...(opts||{}),...local});',
    '    };',
    '    window.Peer.prototype = Native.prototype;',
    '  },',
    '  setName(value) { CFG.name=value; $("#inName").value=value; },',
    '  configureRounds() {',
    '    if (!NET.isHost || !LB.on || typeof LB.getForm !== "function") throw Error("Host lobby is not configured");',
    '    const old = LB.getForm;',
    '    LB.getForm = () => ({...old(),mode:"rounds",preset:"competitive",map:"vanta",rounds:3,bots:0});',
    '  },',
    '  startMatch() { if (!NET.isHost || !S.lobby) throw Error("Not host lobby"); lobbyStart(); },',
    '  endRound() { if (!NET.isHost || !["freeze","live"].includes(S.phase)) throw Error("Round not active"); srvEndRound("t","tempo"); },',
    '  nextRound() { if (!NET.isHost || S.phase!=="end") throw Error("Not in round-end"); srvStartRound(); srvState(); },',
    '  closeLink() { if (NET.isHost || !NET.hostConn?.open) throw Error("No guest link"); NET.hostConn.close(); },',
    '  snapshot() {',
    '    const host = NET.isHost;',
    '    return { host, online:!!NET.online, code:NET.code, joining:!!NET.joining,',
    '      connected:!!NET.hostConn?.open, inGame:!!inGame, lobby:!!(host?S.lobby:LB.on),',
    '      lobbyVisible:!$("#lobby").classList.contains("hidden"),',
    '      myId:C.myId, mode:(host?S.st:C.st)?.mode, map:(host?S.st:C.st)?.map,',
    '      round:host?S.round:C.round, phase:host?S.phase:C.phase,',
    '      score:host?S.score:C.sc,',
    '      livePlayers:host?[...S.players.values()].filter(p=>!p.isBot).map(p=>({id:p.id,name:p.name,team:p.team,alive:p.alive, money:p.money})):',
    '        [...C.players.values()].map(p=>({id:p.id,name:p.n,team:p.tm,alive:p.al})),',
    '      roster:(LB.data?.pl||[]).map(p=>({id:p.id,name:p.n,team:p.tm})),',
    '      joinStatus:$("#joinStatus")?.textContent || "",',
    '      gameStatus:$("#center")?.textContent?.slice(0,120) || ""',
    '    };',
    '  }',
    '};'
  ].join('\n');
  // Test-only CSP adjustment: allow the local PeerServer WebSocket during the test.
  // The checked-in game HTML and its production Content Security Policy stay unchanged.
  const htmlLocal = html.replace(/<meta\\b[^>]*http-equiv\\s*=\\s*["']Content-Security-Policy["'][^>]*>/gi, '');
  return htmlLocal.replace(needle, hook + '\n  return html.replace(needle, hook + '\n$&');');
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

  await host.locator('#inName').fill('V441 Host');
  await guest.locator('#inName').fill('V441 Guest');
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
  assert.equal((await state(host)).livePlayers.filter(x=>x.name==='V441 Guest').length,1,
    'host has duplicate or missing guest');
  console.log('PASS two-browser PeerJS lobby join, unique players, roster sync');

  await host.evaluate(() => window.__v441.configureRounds());
  await host.evaluate(() => window.__v441.startMatch());
  await until(host,() => window.__v441.snapshot().inGame &&
      window.__v441.snapshot().round===1, 'host round one',60000);
  await until(guest,() => {
    const s=window.__v441.snapshot(); return s.inGame && s.mode==='rounds' &&
      s.round===1 && s.livePlayers.length===2;
  },'guest round one',65000);
  await output(host,'game started host');
  await output(guest,'game started guest');
  console.log('PASS round one starts on host and guest with both players');

  await host.evaluate(() => window.__v441.endRound());
  await until(guest,() => {
    const s=window.__v441.snapshot();return s.score?.t===1 && s.phase==='end';
  },'first round end replicates',20000);
  console.log('PASS round result and economy phase replicated');

  await host.evaluate(() => window.__v441.nextRound());
  await until(guest,() => window.__v441.snapshot().round===2 &&
    window.__v441.snapshot().phase==='freeze','round two after reset',20000);
  console.log('PASS next round and respawn state replicated');

  await host.evaluate(() => window.__v441.endRound());
  await until(guest,() => window.__v441.snapshot().score?.t===2,'second round result',20000);
  await host.evaluate(() => window.__v441.nextRound());
  await until(guest,() => window.__v441.snapshot().round===3,'third round',20000);
  await host.evaluate(() => window.__v441.endRound());
  await until(guest,() => {
    const s=window.__v441.snapshot();
    return s.phase==='over' && s.score?.t===3;
  },'match victory replicated',20000);
  console.log('PASS victory, score and match completion replicated');

  await until(guest,() => window.__v441.snapshot().lobby && !window.__v441.snapshot().inGame,
    'return to lobby',30000);
  await until(host,() => window.__v441.snapshot().lobby && !window.__v441.snapshot().inGame,
    'host returns to lobby',10000);
  console.log('PASS match-end return to lobby on two browsers');

  await guest.evaluate(() => window.__v441.closeLink());
  await until(host,() => window.__v441.snapshot().livePlayers.length===1,
    'guest leaving removes server player',15000);
  console.log('PASS disconnect cleans up remote player without ending host room');

  assert.deepEqual(diagnostics,[],'uncaught JavaScript exceptions');
  console.log('RESULT V44.1: TWO REAL WEBRTC CLIENTS, ROOM JOIN, THREE ROUNDS, MATCH END, LOBBY RETURN AND DISCONNECT ALL PASSED');
} catch(e) {
  console.error('FAIL V44.1',e.stack||e);
  console.error('JAVASCRIPT DIAGNOSTICS',JSON.stringify(diagnostics.slice(0,10)));
  process.exitCode=1;
} finally {
  await browser.close();
}
