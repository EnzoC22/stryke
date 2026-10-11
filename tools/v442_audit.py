#!/usr/bin/env python3
"""Read-only V44.2 audit: surface existing combat/bomb protocol and anti-cheat invariants."""
from pathlib import Path
import re
s=Path('index.html').read_text(encoding='utf-8')
lines=s.splitlines()
print('LINES',len(lines),'BYTES',len(s.encode('utf8')))
needles=[
  'function srvHandle(', "case 'shot':", "case 'hit':", "case 'bomb':",
  'function srvDamage(', 'function bombTick(', 'function srvStartRound(', 'function srvSpawn(',
  'function srvEndRound(', 'function inSite(', 'function serverShot(',
  'function acShotAngleOk(', 'function acShotMatches(', 'function posPlausivel(',
  'function clientShoot(', 'function fire(', 'function srvState(', 'function sendToHost(',
  'const BOMB', 'function srvCheckTimeouts(', 'function srvDrop(', 'function reconnect(',
  'function srvBomb', 'function preClamp', 'function srvBuy(', 'function localSpawn(', 
  'function srvAfterMatch(', 'function segClear(', 'function srvPlant(', 'function bombExplode(',
  'function srvTick(', 'function veJogador(', 'function acAmmoShot(', 'function arm',
  'function clientHeartbeat(', 'function matchForm('
]
for needle in needles:
  hits=[i for i,line in enumerate(lines) if needle in line]
  for idx in hits[:2 if needle.startswith('function') else 3]:
    n=45 if 'srvDamage' in needle or 'bombTick' in needle or 'srvStartRound' in needle or 'srvState' in needle or 'srvSpawn(' in needle else 26
    print('\n@@',needle,'LINE',idx+1)
    for j in range(max(0,idx-2),min(len(lines),idx+n)):
      print(f'{j+1}: {lines[j][:400]}')

print("\n=== C.BOMB uses ===")
for i,line in enumerate(lines):
  if "C.bomb" in line or "m.bomb" in line:
    print(i+1,line[:1000])
print("\n=== ON MSG state handler ===")
for i,line in enumerate(lines):
  if "case 'state':" in line:
    for j in range(i,min(len(lines),i+30)):print(j+1,lines[j][:800])
    break
