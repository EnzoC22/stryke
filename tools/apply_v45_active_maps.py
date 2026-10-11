#!/usr/bin/env python3
"""V45: update the LAST (V36 active) grids instead of obsolete V23/V32 definitions."""
from pathlib import Path
import re
p=Path('index.html');before=p.read_text(encoding='utf-8');s=before
tag='/* V45 ACTIVE V36 MAP BASE CORRECTION */'
if tag in s:raise SystemExit('Already corrected active maps')
def rows_patch(name,index,edits,cell):
 global s
 pat=rf"(MAPS\.{name}\s*=\s*gridMap\(\[\s*)(.*?)(\s*\],\s*{cell}\s*,)"
 matches=list(re.finditer(pat,s,re.S))
 if len(matches)!=3:raise SystemExit(f'{name}: expected 3 map versions, found {len(matches)}')
 m=matches[index]
 rows=re.findall(r"'([#.\w]+)'",m.group(2))
 if not rows or len(set(map(len,rows)))!=1:raise SystemExit('Ragged '+name)
 out=[list(row) for row in rows]
 for row,col,expected,desired in edits:
  if out[row][col]!=expected:
   raise SystemExit(f'{name} r{row} c{col}: expected {expected} but got {out[row][col]}')
  out[row][col]=desired
 next_rows=[''.join(row) for row in out]
 if sum(x.count('C') for x in next_rows)!=5:raise SystemExit('CT slots are not five '+name)
 new=m.group(1)+'\n'+'\n'.join("  '"+row+"'," for row in next_rows)+'\n'+m.group(3)
 s=s[:m.start()]+new+s[m.end():]
 print('ACTIVE_GRID_PATCH',name,'index',index,'changed',len(edits))
# Restore archived grid data that is overridden by the active V36 version.
rows_patch('frostline',0,[(1,14,'.','C'),(4,13,'C','.')],'4.8')
rows_patch('kairo',0,[(3,10,'C','.'),(3,11,'.','C')],'6')
# Correct the actual V36 maps used at runtime.
rows_patch('frostline',-1,[(1,14,'C','.'),(4,13,'.','C')],'4.8')
rows_patch('kairo',-1,[(3,11,'C','.'),(3,10,'.','C')],'6')
# Reposition actual V36 map callouts, not archived labels.
old="['Base Defesa',10,18,1,4],['Hangar B'"
new="['Base Defesa',10,18,1,4],['CT Outpost',12,15,3,5],['Hangar B'"
if s.count(old)!=1:raise SystemExit('Frostline V36 callout missing')
s=s.replace(old,new,1)
old="['Base Defesa',11,16,2,5]"
new="['Base Defesa',10,16,2,5]"
if s.count(old)!=1:raise SystemExit('Kairo V36 callout missing')
s=s.replace(old,new,1)
s=s.replace('\nfunction buildMap(id) {','\n'+tag+'\nfunction buildMap(id) {',1)
# Strip regenerated whitespace-only grid lines in both archived and active
# versions, without touching unrelated game HTML.
for name in ('frostline','kairo'):
    matches=list(re.finditer(r'MAPS\.'+name+r'\s*=\s*gridMap\(\[',s))
    if len(matches)!=3:raise SystemExit('Unexpected map count')
    for m in reversed(matches):
        end=s.find('],',m.end())
        if end<0:raise SystemExit('Missing closing grid')
        section=s[m.start():end]
        cleaned='\n'.join(line.rstrip() for line in section.split('\n'))
        s=s[:m.start()]+cleaned+s[end:]
if abs(len(s)-len(before))>2100:raise SystemExit('Unexpected HTML diff width')
p.write_text(s,encoding='utf-8')
print('V45 active Frostline/Kairo spawn grids corrected, 5 defenders each')
