#!/usr/bin/env python3
"""V45 flank corridors, authored defender staging and matching freeze gates."""
from pathlib import Path
import re
p=Path('index.html'); old=p.read_text(encoding='utf-8'); s=old
tag="/* V45 TWO-LANE ATTACKER ACCESS */"
if tag in s:raise SystemExit('V45 corridor already applied')
def update_grid(name, edits, cell):
 global s
 pat=rf"(MAPS\.{name}\s*=\s*gridMap\(\[\s*)(.*?)(\s*\],\s*{cell}\s*,)"
 m=re.search(pat,s,re.S)
 if not m:raise SystemExit(f'Authored {name} grid missing')
 rows=re.findall(r"'([#.\w]+)'",m.group(2))
 assert rows and len(set(map(len,rows)))==1
 changed=[list(x) for x in rows]
 for row,col,expect,value in edits:
  if changed[row][col]!=expect:
   raise SystemExit(f'{name} grid unexpected at row={row},col={col}: {changed[row][col]}, expected {expect}')
  changed[row][col]=value
 new=[''.join(x) for x in changed]
 for team in 'TC':
  if sum(x.count(team) for x in new)!=5:raise SystemExit(f'{name} lost {team} team slots')
 body=m.group(1)+'\n'+'\n'.join("  '"+x+"'," for x in new)+'\n'+m.group(3)
 s=s[:m.start()]+body+s[m.end():]
 print('UPDATED',name)
 for i,(a,b) in enumerate(zip(rows,new)):
  if a!=b:print('ROW',i,a,'=>',b)

# Defender spawn marks are now physically located at their actual initial positions.
# Frostline has a deliberately split CT staging area with a near-side outpost,
# instead of an invisible spawn exception and one giant off-site buy barrier.
update_grid('frostline',[(1,14,'C','.'),(4,13,'.','C')],'4.8')
# Kairo CT flank is a true authored C tile; remove forward-offset runtime override.
update_grid('kairo',[(3,11,'C','.'),(3,10,'.','C')],'6')
# Cargo 5v5 T remains at the southern staging base. Open two equal-width
# connections between the center and side corridors in the attacker's half.
# Without these, all south-to-site trips loop back through the northern
# intersection, producing a 30+ metre defender advantage.
update_grid('cargo',[(13,8,'q','.'),(13,15,'q','.')],'3.8')
a="  MAPS.frostline.spawnsB[0] = [14, -24];"
b="  MAPS.kairo.spawnsB[0] = [10, -28];"
if s.count(a)!=1 or s.count(b)!=1:raise SystemExit('V44 runtime CT overrides unexpectedly changed')
s=s.replace(a,"  // Frostline outpost is now an authored C tile.",1)
s=s.replace(b,"  // Kairo defender flank is now an authored C tile.",1)
s=s.replace("// Shift a single CT start on Frostline/Kairo to allow early A/B defensive setups.",
            "// V45: fixed layout in grid instead of invisible forward-spawn overrides.",1)
# Freeze two Frostline CT staging groups close to their specific spawn exit.
oldct="""ct:[{ax:'z',v:-35,a:-55,b:-8,side:'lte'},{ax:'z',v:-35,a:-8,b:55,side:'lte'}]"""
newct="""ct:[{ax:'z',v:-21,a:-55,b:18,side:'lte'},{ax:'z',v:-35,a:18,b:55,side:'lte'}]"""
if s.count(oldct)!=1:raise SystemExit('Frostline freeze config changed')
s=s.replace(oldct,newct,1)
# Correct the callout formerly marking a defender base at the wrong row.
wrong="['Base Defesa',11,13,5,6]"
good="['Base Defesa',10,16,1,5]"
if s.count(wrong)!=1:raise SystemExit('Kairo outdated defender callout missing')
s=s.replace(wrong,good,1)
# Add a readable callout for Frostline's forward defender staging pocket.
a="['Base Defesa',7,13,2,6],['Hangar'"
b="['Base Defesa',7,13,2,6],['CT Outpost',12,15,3,5],['Hangar'"
if s.count(a)!=1:raise SystemExit('Frostline CT callout missing')
s=s.replace(a,b,1)
s=s.replace("\nfunction buildMap(id) {",f"\n{tag}\nfunction buildMap(id) {{",1)
if abs(len(s)-len(old))>2300:raise SystemExit('Unexpected diff size')
p.write_text(s,encoding='utf-8')
print('V45: restored balanced attacker flanks and legitimate CT site staging')
