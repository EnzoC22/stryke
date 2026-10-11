import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

// Execute the actual authoritative bombTick function from the shipped game.
// Mocks only its surrounding world, never substitutes the function under test.
const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('function bombTick() {');
const end=html.indexOf('function srvBuy(',start);
assert(start>0&&end>start&&end-start<7000,'Unexpected bombTick source layout');
const source=html.slice(start,end);
assert(source.includes('now >= B.end'),'Missing bomb expiration check');

function scenario({clock,bombEnd,actionEnd=null,team='ct'}) {
  const ct={id:'ct',team:'ct',alive:true,pos:[0,0,0],money:0,act:actionEnd===null?null:
    {k:'d',x:0,z:0,end:actionEnd}};
  const t={id:'t',team:'t',alive:true,pos:[30,0,30],money:0,act:null};
  const state={bomb:{st:'planted',end:bombEnd,pos:[0,0,0],mvp:'t',site:'A',pl:true},
    players:new Map([['ct',ct],['t',t]]),phaseEnd:999};
  const result={end:[],damage:[],broadcast:[]};
  const env={S:state,now:clock,Math,BOMB:{timer:40,r:22},
    srvEndRound:(winner,why)=>{result.end.push({winner,why});},
    srvDamage:(...args)=>{result.damage.push(args);},
    broadcast:(m)=>{result.broadcast.push(m);},
    sendTo:()=>{},inSite:()=> 'A'};
  const tick=vm.runInNewContext(source+'\nbombTick;',env,{timeout:2000});
  tick();
  return {bomb:state.bomb,ct,t,end:result.end,damage:result.damage,events:result.broadcast};
}

const late=scenario({clock:10,bombEnd:9,actionEnd:9.5});
assert.equal(late.bomb.st,'exploded','Late defuse cannot override bomb expiration');
assert.equal(late.end.length,1,'Exactly one round winner for expired bomb');
assert.equal(late.end[0].winner,'t','Explosion must grant win to attackers');
assert.equal(late.ct.money,0,'Defender must not be paid for an expired defuse');
assert.equal(late.ct.act,null,'Expired defuse must be cancelled');
console.log('PASS bomb priority: expired explosion beats simultaneous late defuse');

const timely=scenario({clock:8.5,bombEnd:10,actionEnd:8});
assert.equal(timely.bomb.st,'defused','On-time defuse should still succeed');
assert.equal(timely.end[0].winner,'ct','Successful defuse should award CT');
assert.equal(timely.ct.money,300,'Successful defuse action should still pay reward');
console.log('PASS normal defuse remains valid and rewarded');

const noDefuse=scenario({clock:10,bombEnd:9,actionEnd:null});
assert.equal(noDefuse.bomb.st,'exploded');
assert.equal(noDefuse.end[0].winner,'t');
console.log('PASS normal bomb expiry still awards attackers');

const pending=scenario({clock:8.5,bombEnd:10,actionEnd:9.5});
assert.equal(pending.bomb.st,'planted');
assert.equal(pending.ct.act.k,'d');
assert.equal(pending.end.length,0);
console.log('PASS in-progress defuse stays active before its deadline');

console.log('RESULT V44.2: authoritative bombTick deadline ordering and legacy objective behavior approved');
