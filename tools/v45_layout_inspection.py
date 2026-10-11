#!/usr/bin/env python3
from pathlib import Path
import re
s=Path('index.html').read_text(encoding='utf-8')
for token in ('const MAPS =','const MAPS=','function buildMap(id)','function preClampXZ(','function buildNav(M)','function navPath(','/* V44 CARGO SPAWN ROUTE BALANCE */','/* V44 COMPETITIVE SPAWN BALANCE */'):
 i=s.find(token);print('\n## TOKEN',token,'OFFSET',i,'LINE',s.count('\n',0,i)+1)
 if i>=0:
  end=min(len(s),i+(19000 if token.startswith('const MAPS') else 8500 if token.startswith('function buildMap') else 3500))
  print(s[i:end])
print('\n## OTHER SPAWN / BARRIER MATCHES')
for match in list(re.finditer(r'(?:SPAWNS\.a|SPAWNS\.b|spawnsB|\.spawns\b|preClampXZ|pre[Bb]arrier|barrier|blockedSpawn)',s))[:110]:
 a=match.start()
 print(s.count('\n',0,a)+1, repr(s[max(0,a-120):min(len(s),a+240)]))

print("\n## COMPETITIVE MAP DEFINITIONS / BASE GRID")
for ident in ('vanta','frostline','kairo','cargo'):
 patterns=[rf"MAPS\.{ident}\s*=\s*gridMap\(",rf"{ident}\s*:\s*gridMap\(",rf"MAPS\.{ident}\s*="]
 found=[]
 for pat in patterns:
  found.extend(m.start() for m in re.finditer(pat,s))
 print("MAP",ident,"DEFINITION_OFFSETS",sorted(set(found))[:8])
 for a in sorted(set(found))[:2]:
  print("MAP_META",ident,"LINE",s.count('\n',0,a)+1)
  print(s[a:a+11500])
print("\n## PRE BARRIERS")
for m in list(re.finditer(r"PRE_BARRIERS\s*=",s))[:3]:
 print("PRE_OFFSET",m.start(),"LINE",s.count('\n',0,m.start())+1,"TEXT",s[m.start():m.start()+7400])
