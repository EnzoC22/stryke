from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
if 'id="mobileControls"' in s:
    print('mobile already applied')
else:
    anchor='<div id="click" class="hidden">Clique para jogar</div>'
    mobile_html='''<div id="mobileControls" class="hidden" aria-label="Controles mobile">
  <div id="mLook" aria-hidden="true"></div>
  <div id="mJoy"><i></i></div>
  <button id="mFire" class="mact fire" aria-label="Atirar">ATIRAR</button>
  <button id="mAim" class="mact aim" aria-label="Mirar">MIRA</button>
  <button id="mJump" class="mact jump" aria-label="Pular">↑</button>
  <button id="mCrouch" class="mact crouch" aria-label="Agachar">AGACHAR</button>
  <button id="mReload" class="mact reload" aria-label="Recarregar">R</button>
  <button id="mUse" class="mact use" aria-label="Interagir">USAR</button>
  <button id="mBuy" class="mact buy" aria-label="Loja">LOJA</button>
  <button id="mSwap" class="mact swap" aria-label="Trocar arma">↻</button>
  <button id="mBoard" class="mact board" aria-label="Placar">PLACAR</button>
</div>
<div id="rotateMobile" class="hidden"><b>GIRE O CELULAR</b><span>STRYKE foi otimizado para jogar na horizontal.</span></div>'''
    if anchor not in s: raise SystemExit('click anchor missing')
    s=s.replace(anchor,anchor+'\n'+mobile_html,1)

old="const locked = () => document.pointerLockElement === canvas;"
if old in s:
    new="""const MOBILE = matchMedia('(pointer:coarse)').matches || navigator.maxTouchPoints > 0;
const MOB = { fw:0, st:0, crouch:false, lookId:null, joyId:null, lx:0, ly:0 };
const locked = () => MOBILE || document.pointerLockElement === canvas;
if (MOBILE && !load('mobileOptimized', false)) {
  CFG.gfx='baixo'; CFG.shadows=false; CFG.sr='off'; CFG.fov=Math.min(CFG.fov,100);
  save('gfx',CFG.gfx); save('shadows',false); save('srAI','off'); save('fov',CFG.fov); save('mobileOptimized',true);
  setTimeout(()=>{ try{ applySettings(); }catch(e){} },0);
}
"""
    s=s.replace(old,new,1)

s=s.replace("let fw = (keys.KeyW ? 1 : 0) - (keys.KeyS ? 1 : 0), st = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0);","let fw = MOBILE ? MOB.fw : (keys.KeyW ? 1 : 0) - (keys.KeyS ? 1 : 0), st = MOBILE ? MOB.st : (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0);",1)
s=s.replace("const crouchKey = me.downed || me.slideEnd > now || (!C.chatOpen && (keys.KeyC || keys.ControlLeft || keys.ControlRight));","const crouchKey = me.downed || me.slideEnd > now || (!C.chatOpen && (MOB.crouch || keys.KeyC || keys.ControlLeft || keys.ControlRight));",1)
s=s.replace("function requestLock() {\n  audioInit();","function requestLock() {\n  audioInit();\n  if (MOBILE) { mobileGameOn(); return; }",1)
s=s.replace("function enterGame() {\n  inGame = true;","function enterGame() {\n  inGame = true;\n  if (MOBILE) mobileGameOn();",1)
s=s.replace("function toMenu() {\n  inGame = false;","function toMenu() {\n  inGame = false;\n  mobileGameOff();",1)
s=s.replace("function leaveGame() { window.onbeforeunload","function leaveGame() { mobileGameOff(); window.onbeforeunload",1)
s=s.replace("function releaseInput() { for (const k in keys) keys[k] = false; mouseDown = false; G.adsHold = false; C.showBoard = false; sprayCancel(); }","function releaseInput() { for (const k in keys) keys[k] = false; if (typeof MOB!=='undefined') { MOB.fw=MOB.st=0; } mouseDown = false; G.adsHold = false; C.showBoard = false; sprayCancel(); }",1)

anchor_js="// Ctrl+W: em tela cheia, a Keyboard Lock API"
if "function mobileBind()" not in s:
    mobile_js=r'''
// ---------- V42 mobile controls ----------
function mobileGameOn(){
  if(!MOBILE) return;
  $('#mobileControls')?.classList.remove('hidden');
  $('#click')?.classList.add('hidden');
  document.body.classList.add('mobile-game');
  try { screen.orientation?.lock?.('landscape').catch(()=>{}); } catch(e) {}
}
function mobileGameOff(){
  $('#mobileControls')?.classList.add('hidden');
  document.body.classList.remove('mobile-game');
  MOB.fw=MOB.st=0; MOB.crouch=false; mouseDown=false; G.adsHold=false;
}
function mobileTapKey(code,ms=90){ keys[code]=true; setTimeout(()=>keys[code]=false,ms); }
function mobileBind(){
  if(!MOBILE) return;
  const joy=$('#mJoy'), stick=joy?.querySelector('i'), look=$('#mLook');
  const joyMove=e=>{
    if(MOB.joyId!==e.pointerId) return;
    const r=joy.getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2;
    let dx=e.clientX-cx,dy=e.clientY-cy; const lim=r.width*.32,len=Math.hypot(dx,dy)||1,k=Math.min(1,lim/len);
    dx*=k;dy*=k;MOB.st=clamp(dx/lim,-1,1);MOB.fw=clamp(-dy/lim,-1,1);
    stick.style.transform=`translate(${dx}px,${dy}px)`;e.preventDefault();
  };
  joy?.addEventListener('pointerdown',e=>{MOB.joyId=e.pointerId;joy.setPointerCapture(e.pointerId);joyMove(e);audioInit();});
  joy?.addEventListener('pointermove',joyMove);
  const joyEnd=e=>{if(MOB.joyId!==e.pointerId)return;MOB.joyId=null;MOB.fw=MOB.st=0;if(stick)stick.style.transform='translate(0,0)';};
  joy?.addEventListener('pointerup',joyEnd);joy?.addEventListener('pointercancel',joyEnd);
  look?.addEventListener('pointerdown',e=>{MOB.lookId=e.pointerId;MOB.lx=e.clientX;MOB.ly=e.clientY;look.setPointerCapture(e.pointerId);audioInit();});
  look?.addEventListener('pointermove',e=>{
    if(MOB.lookId!==e.pointerId||!me.alive||C.buyOpen)return;
    const dx=e.clientX-MOB.lx,dy=e.clientY-MOB.ly;MOB.lx=e.clientX;MOB.ly=e.clientY;
    const w=W[G.cur],scoped=(w?.scope&&G.scope>0)||(G.ads||0)>.45,k=.0042*CFG.sens*(scoped?CFG.scopeSens:1);
    me.yaw-=dx*k;me.pitch=clamp(me.pitch-dy*k,-1.55,1.55);e.preventDefault();
  });
  const lookEnd=e=>{if(MOB.lookId===e.pointerId)MOB.lookId=null;};
  look?.addEventListener('pointerup',lookEnd);look?.addEventListener('pointercancel',lookEnd);
  const hold=(id,on,off)=>{
    const q=$(id);
    q?.addEventListener('pointerdown',e=>{e.preventDefault();q.setPointerCapture?.(e.pointerId);on();});
    q?.addEventListener('pointerup',e=>{e.preventDefault();off?.();});
    q?.addEventListener('pointercancel',()=>off?.());
  };
  hold('#mFire',()=>{if(!me.alive){cycleSpec();return;}mouseDown=true;G.trigger=true;},()=>mouseDown=false);
  hold('#mAim',()=>{const w=W[G.cur];if(w&&!w.scope&&(w.slot==='primary'||w.slot==='secondary'))G.adsHold=true;else altFire();},()=>G.adsHold=false);
  $('#mJump')?.addEventListener('pointerdown',e=>{e.preventDefault();mobileTapKey('Space',120);});
  $('#mCrouch')?.addEventListener('pointerdown',e=>{e.preventDefault();MOB.crouch=!MOB.crouch;e.currentTarget.classList.toggle('on',MOB.crouch);});
  $('#mReload')?.addEventListener('pointerdown',e=>{e.preventDefault();startReload();});
  $('#mUse')?.addEventListener('pointerdown',e=>{e.preventDefault();if(ZC.on)zUse();else mapInteract();});
  $('#mBuy')?.addEventListener('pointerdown',e=>{e.preventDefault();C.buyOpen?closeBuy():openBuy();});
  $('#mSwap')?.addEventListener('pointerdown',e=>{e.preventDefault();cycleWeapon(1);});
  hold('#mBoard',()=>C.showBoard=true,()=>C.showBoard=false);
}
setTimeout(mobileBind,0);
'''
    if anchor_js not in s: raise SystemExit('mobile js anchor missing')
    s=s.replace(anchor_js,mobile_js+'\n'+anchor_js,1)

if '/* ===== V42 MODE SELECT + MOBILE ===== */' not in s:
    css=r'''
/* ===== V42 MODE SELECT + MOBILE ===== */
.v42-label{margin:14px 0 9px;color:#7f8d9e;font:800 10px Inter,sans-serif;letter-spacing:.24em}.mode-select-v42{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.mode-select-v42 button{min-height:76px;padding:12px 13px;text-align:left;border-radius:13px;border:1px solid rgba(255,255,255,.08);background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.018));color:#d2dbe6;transition:.15s}.mode-select-v42 button.on{border-color:rgba(255,70,85,.55);background:linear-gradient(180deg,rgba(255,70,85,.20),rgba(255,70,85,.04));box-shadow:inset 3px 0 #ff4655}.mode-select-v42 b{display:block;font:800 17px Rajdhani,sans-serif;letter-spacing:.06em}.mode-select-v42 small{display:block;margin-top:4px;color:#8392a4;font:500 10px/1.35 Inter,sans-serif}.v42-selected-mode{display:flex;align-items:center;gap:12px;margin:12px 0 5px;padding:12px 14px;border-radius:13px;border:1px solid rgba(255,255,255,.075);background:rgba(255,255,255,.025)}.v42-selected-mode>span{padding:5px 7px;border-radius:5px;background:#ff4655;color:#fff;font:800 8px Inter,sans-serif;letter-spacing:.12em}.v42-selected-mode b{display:block;color:#fff;font:800 17px Rajdhani,sans-serif}.v42-selected-mode small{color:#8492a3;font-size:10px}.v42-map-card{max-width:520px;position:relative}.v42-room-note{display:flex;gap:10px;align-items:center;margin-top:14px;padding:12px 13px;border-radius:13px;border:1px dashed rgba(255,255,255,.11);background:rgba(255,255,255,.018)}.v42-room-note>i{display:grid;place-items:center;width:28px;height:28px;border-radius:999px;border:1px solid rgba(255,255,255,.18);font-style:normal;color:#93a0af}.v42-room-note b{display:block;color:#cfd8e3;font:800 11px Rajdhani,sans-serif;letter-spacing:.12em}.v42-room-note small{display:block;margin-top:2px;color:#788798;font-size:10px}.v42-lobby-summary,.v42-preset-lock{margin:11px 0 15px;padding:12px 14px;border-radius:13px;border:1px solid rgba(255,255,255,.08);background:rgba(255,255,255,.025)}
#mobileControls{position:fixed;inset:0;z-index:60;pointer-events:none;touch-action:none;user-select:none;-webkit-user-select:none}#mLook{position:absolute;right:0;top:0;width:58%;height:100%;pointer-events:auto;touch-action:none}#mJoy{position:absolute;left:4.5vw;bottom:7vh;width:132px;height:132px;border-radius:50%;border:1px solid rgba(255,255,255,.18);background:radial-gradient(circle,rgba(255,255,255,.08),rgba(4,8,12,.36) 68%);box-shadow:inset 0 0 0 12px rgba(255,255,255,.025);pointer-events:auto;touch-action:none}#mJoy i{position:absolute;left:50%;top:50%;width:58px;height:58px;margin:-29px;border-radius:50%;background:linear-gradient(180deg,rgba(255,255,255,.34),rgba(255,255,255,.12));border:1px solid rgba(255,255,255,.26)}.mact{position:absolute;z-index:2;pointer-events:auto;touch-action:none;border-radius:50%;border:1px solid rgba(255,255,255,.22);background:linear-gradient(180deg,rgba(12,17,24,.82),rgba(4,8,12,.72));color:#fff;font:800 10px Rajdhani,sans-serif;min-width:52px;min-height:52px;padding:0}.mact:active,.mact.on{background:linear-gradient(180deg,#ff5b68,#d52239);border-color:#ff7a84}.mact.fire{right:4vw;bottom:8vh;width:88px;height:88px;background:linear-gradient(180deg,rgba(255,70,85,.92),rgba(174,22,43,.86));font-size:12px}.mact.aim{right:14.5vw;bottom:15vh;width:66px;height:66px}.mact.jump{right:14vw;bottom:5vh;width:58px;height:58px;font-size:22px}.mact.crouch{right:23vw;bottom:7vh;width:60px;height:60px;font-size:8px}.mact.reload{right:5vw;bottom:22vh;width:52px;height:52px;font-size:16px}.mact.use{right:5vw;bottom:31vh;width:54px;height:54px}.mact.buy{left:24vw;bottom:5vh;width:58px;height:58px}.mact.swap{right:23vw;bottom:18vh;width:54px;height:54px;font-size:20px}.mact.board{right:4vw;top:5vh;width:62px;height:40px;border-radius:12px;font-size:8px}#rotateMobile{position:fixed;inset:0;z-index:999;background:#03060af5;display:none;align-items:center;justify-content:center;flex-direction:column;text-align:center;color:#fff}.mobile-game #click{display:none!important}.mobile-game canvas{touch-action:none}
@media(max-width:900px){#menu .mbody{padding:14px}.mode-select-v42{grid-template-columns:repeat(2,minmax(0,1fr))}.playgrid{display:block}#hostBox,#pside{margin-top:12px}.stryke-stage{min-height:460px}.stage-bottom-cards{display:none}.stage-rank{bottom:22px}.stage-copy h2{font-size:42px}}
@media(pointer:coarse) and (orientation:portrait){body.mobile-game #rotateMobile{display:flex!important}}
@media(pointer:coarse) and (orientation:landscape){#mobileControls:not(.hidden){display:block!important}#top{transform:scale(.88);transform-origin:top center}#mmap{width:128px!important;height:128px!important}#hp,#ammo{transform:scale(.82);transform-origin:bottom left}#ammo{transform-origin:bottom right}#feed{transform:scale(.85);transform-origin:top right}}
'''
    s=s.replace('</style>',css+'\n</style>',1)

s=s.replace('STRYKE <b>4.5.1 // V41.1 STAGED MATCH SETUP</b>','STRYKE <b>4.6 // V42 MODE SELECT + MOBILE</b>',1)
s=s.replace('STRYKE <b>4.5 // V41 OPERATIONS UI + VISUAL OVERHAUL</b>','STRYKE <b>4.6 // V42 MODE SELECT + MOBILE</b>',1)
p.write_text(s,encoding='utf-8')
print('V42 mobile patched',len(s))
