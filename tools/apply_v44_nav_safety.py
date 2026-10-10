#!/usr/bin/env python3
"""V44: keep bots from walking directly into walls on unreachable navigation routes."""
from pathlib import Path

path=Path('index.html')
original=path.read_text(encoding='utf-8')
start=original.find('function navPath(ax, az, bx, bz) {')
end=original.find('\n// ================================================================',start)
if start<0 or end<=start or end-start>3500:
    raise SystemExit('Unexpected navPath region; patch safely aborted')
body=original[start:end]
replacements=[
    ('if (!NAV || !NAV.nodes.length) return [[bx, bz]];', 'if (!NAV || !NAV.nodes.length) return [];'),
    ('if (s < 0 || g < 0) return [[bx, bz]];', 'if (s < 0 || g < 0) return [];'),
    ('if (prev[g] === -2) return [[bx, bz]];', 'if (prev[g] === -2) return [];')
]
for a,b in replacements:
    if body.count(a)!=1:
        raise SystemExit('Unexpected navPath fallback signature; aborting: '+a)
    body=body.replace(a,b,1)
next_code=original[:start]+body+original[end:]
if next_code.count('function navPath(ax, az, bx, bz) {')!=1:
    raise SystemExit('Unexpected additional navigation implementation')
if abs(len(next_code)-len(original))>150:
    raise SystemExit('Unexpected diff size')
path.write_text(next_code,encoding='utf-8')
print('V44: guarded navigation fallback fix applied (3 return cases); map layouts and collisions untouched')
