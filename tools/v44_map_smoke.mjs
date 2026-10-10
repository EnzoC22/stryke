import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const base = process.env.STRYKE_TEST_URL || 'http://127.0.0.1:8765/';
const browser = await chromium.launch({
  headless: true,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--disable-dev-shm-usage']
});

function withHooks(html) {
  const needle = /<\/script>\s*<\/body>/i;
  if (!needle.test(html)) throw Error('Could not find final inline module');
  const hooks = `
    // V44 read-only map probes: injected into test response, not shipped.
    window.__strykeV44 = {
      isolatedNavigation: () => {
        const prior = NAV;
        try {
          NAV = { nodes: [
            {x:0,z:0,n:[]}, {x:30,z:30,n:[]}
          ]};
          const disconnected = navPath(0,0,30,30);
          NAV = null;
          const noGraph = navPath(0,0,30,30);
          return {disconnected,noGraph};
        } finally {
          NAV = prior;
        }
      },
      inspect: (id) => {
        const map = MAPS[id];
        if (!map || !map.sites || !map.bomb) throw Error('not a competitive map: ' + id);
        buildMap(id);
        const nodes = NAV?.nodes || [];
        const comp = new Int32Array(nodes.length).fill(-1);
        const sizes = [];
        for (let i=0; i<nodes.length; i++) {
          if (comp[i] !== -1) continue;
          const cid=sizes.length, q=[i];comp[i]=cid;
          for (let k=0;k<q.length;k++) for (const n of nodes[q[k]].n) if(comp[n]===-1){comp[n]=cid;q.push(n);}
          sizes.push(q.length);
        }
        const nearest = (x,z) => {
          const index = nearestNode(x,z);
          const node = nodes[index];
          return {index, offset:node?Math.hypot(node.x-x,node.z-z):null, comp:index<0?-1:comp[index]};
        };
        const shortest = (a, b) => {
          const ai=nearest(a[0],a[1]),bi=nearest(b[0],b[1]);
          if(ai.index<0 || bi.index<0 || ai.comp!==bi.comp) return null;
          const previous=new Int32Array(nodes.length).fill(-2);
          previous[ai.index]=-1;
          const q=[ai.index];
          for(let k=0;k<q.length && previous[bi.index]===-2;k++){
            const p=q[k];
            for(const n of nodes[p].n) if(previous[n]===-2){previous[n]=p;q.push(n);}
          }
          if(previous[bi.index]===-2) return null;
          let dist=ai.offset+bi.offset,cur=bi.index,hops=0;
          while(previous[cur]>=0){
            const n=nodes[cur],pp=nodes[previous[cur]];
            dist+=Math.hypot(n.x-pp.x,n.z-pp.z);hops++;cur=previous[cur];
          }
          return {distance:Math.round(dist*10)/10,hops};
        };
        const sites={};
        for(const key of ['A','B']) {
          const rect=map.sites[key];
          if(!rect)throw Error('site '+key+' missing '+id);
          const options=[];
          for(let x=rect[0]+.7;x<rect[1]-.3;x+=1)for(let z=rect[2]+.7;z<rect[3]-.3;z+=1)
            if(footFree(x,z))options.push([x,z]);
          options.sort((a,b)=>Math.hypot(a[0]-(rect[0]+rect[1])/2,a[1]-(rect[2]+rect[3])/2)-
                               Math.hypot(b[0]-(rect[0]+rect[1])/2,b[1]-(rect[2]+rect[3])/2));
          sites[key]={rect,plantableSamples:options.length,point:options[0]||null};
        }
        const spawns={
          t:SPAWNS.a.map(([x,y,z])=>[x,z]),
          ct:SPAWNS.b.map(([x,y,z])=>[x,z])
        };
        const spawnData={};
        for(const team of ['t','ct'])spawnData[team]=spawns[team].map(p=>({
          point:p,free:footFree(p[0],p[1]),nearest:nearest(p[0],p[1]),
          toSite:Object.fromEntries(['A','B'].map(k=>[k,sites[k].point?shortest(p,sites[k].point):null]))
        }));
        const trialPoints=[];
        if(['frostline','kairo','cargo'].includes(id)){
          const trialTeam = id==='cargo'?'t':'ct';
          const xs=id==='cargo'?[-11,-8,-5,-2,1,4,7,10]:[6,10,14,18,22,26,30];
          const zs=id==='cargo'?[13,16,19,22,25]:[-36,-32,-28,-24,-20,-16,-12];
          const foes=spawns[trialTeam==='ct'?'t':'ct'];
          for(const x of xs)for(const z of zs){
            if(!footFree(x,z))continue;
            const clamped=preClampXZ(trialTeam,x,z);
            if(Math.hypot(clamped[0]-x,clamped[1]-z)>.05)continue;
            if(foes.some(p=>segClear(x,z,p[0],p[1])))continue;
            const a=shortest([x,z],sites.A.point)?.distance;
            const b=shortest([x,z],sites.B.point)?.distance;
            if(!Number.isFinite(a)||!Number.isFinite(b))continue;
            const gap=Math.min(...foes.map(p=>Math.hypot(x-p[0],z-p[1])));
            if(gap<30)continue;
            const score=id==='frostline'?Math.abs(a-61)+Math.abs(b-63)*.14:
              id==='kairo'?Math.abs(b-58)+Math.abs(a-55)*.1:
                Math.abs(a-63)+Math.abs(b-63);
            trialPoints.push({point:[x,z],a,b,gap:Math.round(gap),score:Math.round(score*10)/10});
          }
          trialPoints.sort((a,b)=>a.score-b.score);
        }
        const clearSightlines=spawns.t.flatMap(a=>spawns.ct.map(b=>segClear(a[0],a[1],b[0],b[1]))).filter(Boolean).length;
        const closest={};
        for(const site of ['A','B'])closest[site]=Object.fromEntries(['t','ct'].map(team=>{
          const d=spawnData[team].map(p=>p.toSite[site]?.distance).filter(x=>Number.isFinite(x));
          return [team,d.length?Math.min(...d):null];
        }));
        return {id,size:[map.w,map.d],siteCount:Object.keys(map.sites).length,
          navNodes:nodes.length,components:sizes.sort((a,b)=>b-a).slice(0,12),
          spawnData,sites,closest,clearSightlines,trialPoints:trialPoints.slice(0,12),collisionBoxes:COL.length};
      }
    };
  `;
  return html.replace(needle, hooks + '\n$&');
}

async function boot(page, label) {
  const errors = [];
  const badImageRequests = [];
  await page.addInitScript(() => {
    window.addEventListener('error', event => {
      const element = event.target;
      if (element?.tagName === 'IMG' && element.src?.includes('%7Burl%7D')) {
        console.warn('BROKEN_IMG:', element.outerHTML.slice(0, 450),
          'PARENT:', element.parentElement?.outerHTML.slice(0, 600));
      }
    }, true);
  });
  page.on('pageerror', error => errors.push(error.message.slice(0, 350)));
  page.on('console', message => {
    if (message.type() === 'error' || message.text().startsWith('BROKEN_IMG:')) console.log(label, 'console diagnostic:', message.text().slice(0, 1400));
  });
  page.on('response', response => {
    if (response.status() === 404) {
      console.log(label, 'missing resource:', response.url());
      if (response.request().resourceType() === 'image') badImageRequests.push(response.url());
    }
  });
  const debugNetwork = await page.context().newCDPSession(page);
  debugNetwork.on('Network.requestWillBeSent', request => {
    if (request.request?.url?.includes('%7Burl%7D')) {
      console.log(label, 'BROKEN_NETWORK_INITIATOR:', request.type,
        JSON.stringify(request.initiator).slice(0, 2200));
    }
  });
  await debugNetwork.send('Network.enable');
  const response = await page.goto(base, {waitUntil: 'domcontentloaded', timeout: 60000});
  assert.equal(response.status(), 200, label + ' HTML returned non-200 status');
  await page.locator('#menu').waitFor({state: 'visible', timeout: 45000});
  await page.locator('#btnHost').waitFor({state: 'attached', timeout: 45000});
  await page.waitForTimeout(3000);
  const brokenImages = await page.evaluate(() => [...document.querySelectorAll('img[src]')]
    .filter(el => el.getAttribute('src')?.includes(String.fromCharCode(36,123,117,114,108,125)))
    .slice(0, 5).map(el => ({
      html: el.outerHTML.slice(0, 500),
      parent: el.parentElement?.outerHTML.slice(0, 650)
    })));
  if (brokenImages.length) console.log(label, 'broken image elements:', JSON.stringify(brokenImages));
  if (badImageRequests.length) throw Error(label + ' encountered missing image URL: ' + badImageRequests.join(' | '));
  if (errors.length) throw Error(label + ' JavaScript exceptions: ' + errors.join(' | '));
  console.log('PASS', label, 'boot, menu visible, no uncaught JavaScript errors');
}

try {
  const context=await browser.newContext({viewport:{width:1280,height:720}});
  const page=await context.newPage();
  await page.route('**/*',async route=>{
    const req=new URL(route.request().url());
    if(req.origin!==new URL(base).origin || (req.pathname!=='/'&&req.pathname!=='/index.html'))
      return route.continue();
    const fetched=await route.fetch();
    const html=await fetched.text();
    return route.fulfill({response:fetched,body:withHooks(html)});
  });
  await boot(page,'V44 desktop');
  await page.waitForFunction(()=>Boolean(window.__strykeV44),{timeout:45000});
  const ids=['vanta','frostline','kairo','cargo'];
  const results=[];
  for(const id of ids){
    console.log('V44 MAP START',id);
    const result=await page.evaluate(id=>window.__strykeV44.inspect(id),id);
    results.push(result);
    const report={
      name:result.id,worldSize:result.size,collisionBoxes:result.collisionBoxes,
      nodes:result.navNodes,components:result.components,
      tSpawnCount:result.spawnData.t.length,
      ctSpawnCount:result.spawnData.ct.length,
      blockedSpawns:Object.fromEntries(['t','ct'].map(t=>[t,result.spawnData[t].filter(s=>!s.free).map(s=>s.point)])),
      unreachable:Object.fromEntries(['t','ct'].map(t=>[t,result.spawnData[t].flatMap(s=>['A','B'].filter(k=>!s.toSite[k]).map(k=>[s.point,k]))])),
      sightlines:result.clearSightlines,
      spawnRoutes:Object.fromEntries(['t','ct'].map(t=>[t,result.spawnData[t].map(v=>({p:v.point,a:v.toSite.A?.distance,b:v.toSite.B?.distance}))])),
      closest:result.closest,
      sites:Object.fromEntries(['A','B'].map(k=>[k,{plantableSamples:result.sites[k].plantableSamples,point:result.sites[k].point}])),
      trialPoints:result.trialPoints
    };
    console.log('V44 MAP REPORT',JSON.stringify(report));
    assert(result.navNodes>0,'no nav nodes on '+id);
    assert(result.sites.A.plantableSamples>0 && result.sites.B.plantableSamples>0,'site lacks planting space '+id);
    assert.equal(result.spawnData.t.length,5,'incorrect T spawns '+id);
    assert.equal(result.spawnData.ct.length,5,'incorrect CT spawns '+id);
    assert.equal(result.components.length,1,'isolated bot navigation islands '+id);
    assert.equal(result.clearSightlines,0,'enemy spawns have direct line-of-sight '+id);
    for(const team of ['t','ct']){
      assert(result.spawnData[team].every(sp=>sp.free),'blocked spawn '+id+' '+team);
      assert(result.spawnData[team].every(sp=>sp.toSite.A && sp.toSite.B),'unreachable bombsite '+id+' '+team);
      for(let i=0;i<result.spawnData[team].length;i++)
        for(let j=i+1;j<result.spawnData[team].length;j++){
          const a=result.spawnData[team][i].point,b=result.spawnData[team][j].point;
          assert(Math.hypot(a[0]-b[0],a[1]-b[1])>=1.5,'overlapping teammates at spawn '+id);
        }
    }
    for(const site of ['A','B']){
      assert(result.closest[site].ct < result.closest[site].t,
        'defenders must be able to reach '+id+' '+site+' before attackers');
      if(result.closest[site].t-result.closest[site].ct>20)
        console.log('V44 BALANCE REVIEW:',id,site,'CT lead',Math.round((result.closest[site].t-result.closest[site].ct)*10)/10,'meters');
    }
    if(id==='frostline'){
      assert(result.closest.A.ct<=63 && result.closest.B.ct<=62,'Frostline CT spawn balance regressed');
    }
    if(id==='kairo'){
      assert(result.closest.A.ct<=62 && result.closest.B.ct<=60,'Kairo CT spawn balance regressed');
    }
  }
  const unreachableProof=await page.evaluate(()=>window.__strykeV44.isolatedNavigation());
  assert.deepEqual(unreachableProof.disconnected,[], 'disconnected bot path must not return a straight line through walls');
  assert.deepEqual(unreachableProof.noGraph,[], 'missing navigation graph must not return unsafe straight-line route');
  console.log('PASS V44 bot fallback: disconnected and uninitialized graphs return no route');
  const blockers=results.flatMap(r=>['t','ct'].flatMap(t=>r.spawnData[t].flatMap(s=>
    !s.free?[r.id+' '+t+' blocked spawn '+JSON.stringify(s.point)]:[])));
  const missingRoutes=results.flatMap(r=>['t','ct'].flatMap(t=>r.spawnData[t].flatMap(s=>
    ['A','B'].flatMap(k=>s.toSite[k]?[]:[r.id+' '+t+' '+k+' '+JSON.stringify(s.point)]))));
  console.log('V44 FINDINGS',JSON.stringify({blockedSpawns:blockers,unreachableRoutes:missingRoutes}));
  console.log('RESULT: V44 map audit completed for '+ids.length+' competitive maps');
  await context.close();
} catch(e){
  console.error('V44 MAP AUDIT FAIL',e.stack||e);process.exitCode=1;
} finally {await browser.close();}
