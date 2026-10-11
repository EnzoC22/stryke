#!/usr/bin/env python3
"""V45 surgical tactical-map layout correction.

- Restore Cargo's authored south attacker spawn (the five T grid cells).
- Relocate Cargo A/B from the defender doorstep to guarded mid-map side lanes.
- Realign freeze barriers around *both* teams' own spawn, not around the sites.
- Keep weapons, map textures, models, economy, AI and anticheat untouched.
"""
from pathlib import Path
import re
p=Path('index.html')
before=p.read_text(encoding='utf-8')
s=before
marker="/* V45 COMPETITIVE SPAWNS AND FREEZE BALANCE */"
if marker in s: raise SystemExit("Already patched V45")

# Remove the earlier mistaken central Cargo spawn override, which put T outside
# the grid's intended "TTTTT" base and gave them open mid access on round start.
a=s.find('/* V44 CARGO SPAWN ROUTE BALANCE */')
b=s.find('\nfunction buildMap(id) {',a)
if a<0 or b<=a or b-a>700:
    raise SystemExit('V44 Cargo override signature changed; refusing patch')
chunk=s[a:b]
if 'MAPS.cargo.spawns.splice(0, 5' not in chunk:
    raise SystemExit('Expected old Cargo override not found')
s=s[:a]+marker+"\n// Cargo attacker starts use the authored T-only spawn grid, not center lane.\n"+s[b:]

# Edit the original grid, not a runtime-only position override. New A and B
# rooms sit in mid-map side lanes; center lane and existing container corridors
# remain open. Their sites have 5 ground tiles each plus one interior cover.
m=re.search(r"(MAPS\.cargo\s*=\s*gridMap\(\[\s*)(.*?)(\s*\],\s*3\.8\s*,)",s,re.S)
if not m: raise SystemExit('Cargo authored grid definition missing')
rows=re.findall(r"'([#.\w]+)'",m.group(2))
if len(rows)!=19 or any(len(row)!=23 for row in rows):
    raise SystemExit('Cargo grid changed shape; refusing patch')
if sum(row.count('T') for row in rows)!=5 or sum(row.count('C') for row in rows)!=5:
    raise SystemExit('Cargo teams no longer have five designated cells')
if sum(row.count('A') for row in rows)!=5 or sum(row.count('B') for row in rows)!=5:
    raise SystemExit('Cargo authored bombsites count changed')
new=[list(row.replace('A','.').replace('B','.')) for row in rows]
for r,cols,label in [
    (8,[3,5],'B'),(9,[3,4,5],'B'),
    (8,[17,19],'A'),(9,[17,18,19],'A')
]:
    for col in cols:
        if new[r][col]!='.': raise SystemExit(f'New {label} bombsite obstructed {r}:{col}')
        new[r][col]=label
for r,c in [(8,4),(8,18)]:
    if new[r][c]!='.':raise SystemExit('Site half-cover would block a corridor')
    new[r][c]='i'
for i,oldrow in enumerate(rows):
    if oldrow!=rows[i]:raise SystemExit('Unexpected row mutation')
out=[''.join(row) for row in new]
if sum(row.count('A') for row in out)!=5 or sum(row.count('B') for row in out)!=5:
    raise SystemExit('Bombsites must retain 5 plantable tiles each')
if any(out[i].count('T')!=rows[i].count('T') or out[i].count('C')!=rows[i].count('C') for i in range(len(rows))):
    raise SystemExit('Team bases must not move')
replacement=m.group(1)+"\n"+"\n".join("  '"+row+"'," for row in out)+"\n"+m.group(3)
s=s[:m.start()]+replacement+s[m.end():]
# Repair inaccurate map location names/callouts to match relocated sites.
area_replacements=[
    ("['Bomb B / Red Stack',2,6,3,6]","['Bomb B / Red Stack',2,6,7,10]"),
    ("['Bomb A / Blue Stack',16,20,3,6]","['Bomb A / Blue Stack',16,20,7,10]")
]
for old,newtext in area_replacements:
    if s.count(old)!=1:raise SystemExit('Cargo callout changed: '+old)
    s=s.replace(old,newtext,1)

# Keep freeze-time movement symmetric. Old CT gates at +25/+30/+29/+6
# permitted CTs to walk almost to T spawn *before* a round began.
# Old T gates at +34 (Frostline) and +32 (Kairo) clamped some T players
# to the wrong side of their original authored start.
a=s.find('const PRE_BARRIERS = Object.freeze({')
b=s.find('\n});',a)
if a<0 or b<0 or b-a>2600:raise SystemExit('Pre-round barrier block changed')
pblock=s[a:b]
gate_values={
    'vanta':(29,-29),'frostline':(31,-35),
    'kairo':(24,-24),'cargo':(23,-23)
}
for key,(t,ct) in gate_values.items():
    pat=rf"({key}:\s*\{{)(.*?)(\n\s*\}})"
    found=re.search(pat,pblock,re.S)
    if not found:raise SystemExit(f'No {key} barrier')
    group=found.group(2)
    zt=re.search(r"t:\s*\[(.*?)\]\s*,\s*ct:",group,re.S)
    zct=re.search(r"ct:\s*\[(.*?)\]",group,re.S)
    if not zt or not zct:raise SystemExit(f'Unknown {key} freeze segments')
    old_t=zt.group(1)
    old_ct=zct.group(1)
    valuesT=re.findall(r"v:\s*(-?\d+)",old_t)
    valuesCT=re.findall(r"v:\s*(-?\d+)",old_ct)
    if len(valuesT)!=2 or len(valuesCT)!=2:
        raise SystemExit('Expected two T and CT freeze segments on '+key)
    revisedT=re.sub(r"v:\s*-?\d+",f"v:{t}",old_t)
    revisedCT=re.sub(r"v:\s*-?\d+",f"v:{ct}",old_ct)
    group=group.replace(old_t,revisedT,1).replace(old_ct,revisedCT,1)
    pblock=pblock[:found.start(2)]+group+pblock[found.end(2):]
s=s[:a]+pblock+s[b:]
if abs(len(s)-len(before))>2900:
    raise SystemExit('Unexpectedly broad HTML change')
p.write_text(s,encoding='utf-8')
print('V45 FIXED: original Cargo T base restored, A/B moved to mid-side rooms with cover,')
print('          pre-round CT/T gates aligned to their real spawn on four maps, callouts fixed')
print('Map row diff:')
for i,(old,new) in enumerate(zip(rows,out)):
    if old!=new:print(i,'BEFORE',old,'AFTER ',new)
print('HTML size delta',len(s)-len(before))
