#!/usr/bin/env python3
"""V44 surgical Cargo attack spawn placement; no geometry or asset edits."""
from pathlib import Path

p=Path('index.html')
old=p.read_text(encoding='utf-8')
anchor='function buildMap(id) {'
marker='/* V44 CARGO SPAWN ROUTE BALANCE */'
if old.count(anchor)!=1 or marker in old:raise SystemExit('Refusing unmatched or duplicate Cargo change')
patch="""/* V44 CARGO SPAWN ROUTE BALANCE */
// Based on Chromium collision, line-of-sight, barrier and nav tests.
// Keeps five distinct attacker spawns and all structural map geometry.
if (MAPS.cargo?.spawns?.length === 5) {
  MAPS.cargo.spawns.splice(0, 5, [-8,13], [-5,13], [-2,13], [1,13], [4,13]);
} else {
  console.warn('[STRYKE V44] Cargo spawn balance skipped: map structure changed');
}

"""
next_code=old.replace(anchor,patch+anchor,1)
chip='STRYKE <b>4.7 // V43 MOBILE FIXES</b>'
if next_code.count(chip)!=1:raise SystemExit('Unexpected STRYKE version chip; stop without writing')
next_code=next_code.replace(chip,'STRYKE <b>4.8 // V44 COMPETITIVE FOUNDATION</b>',1)
if abs(len(next_code)-len(old))>1000:raise SystemExit('Unexpected diff size')
p.write_text(next_code,encoding='utf-8')
print('V44 Cargo: five T starts moved closer to midfield; core collision geometry unchanged')
