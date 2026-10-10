#!/usr/bin/env python3
"""STRYKE V44: surgical CT spawn placement changes, no map geometry replacement."""
from pathlib import Path
p=Path("index.html")
s=p.read_text(encoding="utf-8")
anchor="function buildMap(id) {"
marker="/* V44 COMPETITIVE SPAWN BALANCE */"
if s.count(anchor)!=1 or marker in s:
    raise SystemExit("Unsafe map code version or patch already applied")
# Generated from runtime collision/nav/pre-round checks, not guessed spawn positions.
patch="""/* V44 COMPETITIVE SPAWN BALANCE */
// The five-spawn squads and all original map collision/cover assets are preserved.
// Shift a single CT start on Frostline/Kairo to allow early A/B defensive setups.
if (MAPS.frostline?.spawnsB?.length === 5 && MAPS.kairo?.spawnsB?.length === 5) {
  MAPS.frostline.spawnsB[0] = [14, -24];
  MAPS.kairo.spawnsB[0] = [10, -28];
} else {
  console.warn('[STRYKE V44] Balanced spawns not applied: map structure changed');
}

"""
s=s.replace(anchor,patch+anchor,1)
if abs(len(s)-len(p.read_text(encoding="utf-8")))>1100:
    raise SystemExit("Unexpected map diff size; refusing write")
p.write_text(s,encoding="utf-8")
print("V44 applied two guarded CT spawn adjustments; no changes to map colliders, sites or assets")
