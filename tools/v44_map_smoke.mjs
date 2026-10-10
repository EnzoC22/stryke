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
        const clearSightlines=spawns.t.flatMap(a=>spawns.ct.map(b=>segClear(a[0],a[1],b[0],b[1]))).filter(Boolean).length;
        const closest={};
        for(const site of ['A','B'])closest[site]=Object.fromEntries(['t','ct'].map(team=>{
          const d=spawnData[team].map(p=>p.toSite[site]?.distance).filter(x=>Number.isFinite(x));
          return [team,d.length?Math.min(...d):null];
        }));
        return {id,size:[map.w,map.d],siteCount:Object.keys(map.sites).length,
          navNodes:nodes.length,components:sizes.sort((a,b)=>b-a).slice(0,12),
          spawnData,sites,closest,clearSightlines, collisionBoxes:COL.length};
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
      sites:Object.fromEntries(['A','B'].map(k=>[k,{plantableSamples:result.sites[k].plantableSamples,point:result.sites[k].point}]))
    };
    console.log('V44 MAP REPORT',JSON.stringify(report));
    assert(result.navNodes>0,'no nav nodes on '+id);
    assert(result.sites.A.plantableSamples>0 && result.sites.B.plantableSamples>0,'site lacks planting space '+id);
    assert.equal(result.spawnData.t.length,5,'incorrect T spawns '+id);
    assert.equal(result.spawnData.ct.length,5,'incorrect CT spawns '+id);
  }
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
