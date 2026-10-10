#!/usr/bin/env python3
"""Apply narrowly scoped STRYKE V43 touch-interface fixes to the existing game.

Deliberately avoid changing weapon simulation, maps, anti-cheat, and binary assets.
Each anchor is asserted exactly once; fail rather than silently patch unknown code.
"""
from pathlib import Path

path = Path("index.html")
original = path.read_text(encoding="utf-8")
s = original
MARKER = "/* V43 MOBILE INTERACTION FIXES */"
if MARKER in s:
    raise SystemExit("V43 already applied: refusing a duplicate patch")


def patch(before, after, label):
    global s
    count = s.count(before)
    if count != 1:
        raise SystemExit(f"V43 patch stopped: {label} anchor count={count}, expected 1")
    s = s.replace(before, after, 1)
    print("PATCH", label)


# Do not identify desktop PCs as mobile only because they expose touch hardware.
patch("const MOBILE = matchMedia('(pointer:coarse)').matches || navigator.maxTouchPoints > 0;",
      "const MOBILE = matchMedia('(pointer:coarse)').matches;",
      "primary touch pointer detection")

# Give the player explicit Pause and Close Shop controls.
patch('  <button id="mBoard" class="mact board" aria-label="Placar">PLACAR</button>',
      '  <button id="mBoard" class="mact board" aria-label="Placar">PLACAR</button>\n'
      '  <button id="mPause" class="mact pause" aria-label="Pausar jogo">PAUSA</button>',
      "pause button markup")
patch("setHTML('buy', `<div class=\"bmwrap\">",
      "setHTML('buy', `<button type=\"button\" id=\"mCloseBuy\" aria-label=\"Fechar loja\">FECHAR ×</button><div class=\"bmwrap\">",
      "mobile shop close button")
patch("$('#buy').addEventListener('click', e => {\n  const c = e.target.closest('[data-buy]'); if (!c) return;",
      "$('#buy').addEventListener('click', e => {\n"
      "  if (e.target.closest('#mCloseBuy')) { closeBuy(); return; }\n"
      "  const c = e.target.closest('[data-buy]'); if (!c) return;",
      "shop close handler")

# The existing mobile resume path does not fire pointerlockchange.
patch("function mobileGameOn(){\n  if(!MOBILE) return;\n  $('#mobileControls')",
      "function mobileGameOn(){\n  if(!MOBILE) return;\n"
      "  $('#pause')?.classList.add('hidden');\n  $('#mobileControls')",
      "resume closes pause overlay")
patch("function mobileGameOff(){\n  $('#mobileControls')",
      "function mobileGameOff(){\n  if (MOBILE) mobileUseEnd();\n  $('#mobileControls')",
      "stop held input on leaving")
patch("function releaseInput() { for (const k in keys) keys[k] = false;",
      "function releaseInput() { if (MOBILE && keys.KeyE) mobileUseEnd(); for (const k in keys) keys[k] = false;",
      "stop held bomb input on focus loss")

# Plant/defuse checks KeyE continuously; zombie revive/repair checks KeyF.
# Keep these flags down until pointerup/cancel just like real keyboard input.
use_logic = """
function mobileUseStart(){
  if (!inGame || !me.alive || C.buyOpen || !$('#pause')?.classList.contains('hidden')) return;
  if (ZC.on) {
    keys.KeyF = true;
    zUse(); // short presses still buy/open/use zombie objects
  } else {
    keys.KeyE = true; // the existing bomb loop performs the hold protocol
    mapInteract();   // the existing non-zombie F action
    if (!C.eTip) sendToHost({ t: 'pick' }); // E pickup when not planting/defusing
  }
}
function mobileUseEnd(){
  const hadBombHold = !!keys.KeyE;
  keys.KeyE = false;
  keys.KeyF = false;
  if (hadBombHold && C.st?.mode === 'rounds')
    sendToHost({ t: 'bomb', on: 0 }); // mirror desktop KeyE keyup
}
"""
patch("function mobileBind(){\n  if(!MOBILE) return;",
      use_logic + "function mobileBind(){\n  if(!MOBILE) return;",
      "hold-to-use implementation")
patch("  $('#mUse')?.addEventListener('pointerdown',e=>{e.preventDefault();if(ZC.on)zUse();else mapInteract();});",
      "  hold('#mUse', mobileUseStart, mobileUseEnd);",
      "use pointerdown/up/cancel semantics")
patch("    q?.addEventListener('pointercancel',()=>off?.());",
      "    q?.addEventListener('pointercancel',()=>off?.());\n"
      "    q?.addEventListener('lostpointercapture',()=>off?.());",
      "release held input on capture loss")
patch("  $('#mBuy')?.addEventListener('pointerdown',e=>{e.preventDefault();C.buyOpen?closeBuy():openBuy();});",
      "  $('#mBuy')?.addEventListener('pointerdown',e=>{e.preventDefault();mobileUseEnd();C.buyOpen?closeBuy():openBuy();});\n"
      "  $('#mPause')?.addEventListener('pointerdown',e=>{e.preventDefault();"
      "if(!inGame||C.buyOpen)return;releaseInput();showPause();});",
      "mobile pause and shop controls")

css = """
/* V43 MOBILE INTERACTION FIXES */
.mact.pause{right:4vw;top:14vh;width:62px;height:42px;border-radius:12px;font-size:10px}
#mCloseBuy{display:none}
body.mobile-game #buy:not(.hidden){
  position:fixed;inset:0;z-index:100!important;
  pointer-events:auto!important;touch-action:pan-y;
}
body.mobile-game #buy:not(.hidden) .bmwrap{
  touch-action:pan-y;overscroll-behavior:contain;
}
body.mobile-game #mCloseBuy{
  display:block;position:fixed;right:16px;top:12px;z-index:102;
  border:1px solid rgba(255,255,255,.35);
  border-radius:10px;background:#df354a;color:white;padding:10px 14px;
  font:800 12px Inter,sans-serif;touch-action:manipulation;
}
body.mobile-game:has(#buy:not(.hidden)) #mobileControls,
body.mobile-game:has(#pause:not(.hidden)) #mobileControls{
  visibility:hidden;pointer-events:none;
}
body.mobile-game:has(#buy:not(.hidden)) #rotateMobile,
body.mobile-game:has(#pause:not(.hidden)) #rotateMobile{display:none!important}
"""
patch("</style>", css + "\n</style>", "mobile overlay layer safety")
patch("STRYKE <b>4.6 // V42 MODE SELECT + MOBILE</b>",
      "STRYKE <b>4.7 // V43 MOBILE FIXES</b>",
      "version chip")

if len(s) < len(original) - 1000 or abs(len(s) - len(original)) > 10000:
    raise SystemExit("V43 size guard: unexpected file replacement")
path.write_text(s, encoding="utf-8")
print("V43 ready:", len(original), "=>", len(s), "bytes; assets and core gameplay unchanged")
