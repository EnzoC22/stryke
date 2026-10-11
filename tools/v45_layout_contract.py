#!/usr/bin/env python3
"""V45 canonical map contract: print tactical occupancy, validate base, gate and site layout."""
import re
from pathlib import Path
s=Path('index.html').read_text(encoding='utf-8')
maps={}
for name in ('vanta','frostline','kairo','cargo'):
    m=re.search(r'MAPS\.'+name+r'\s*=\s*gridMap\(\[\s*(.*?)\s*\],\s*([\d.]+)',s,re.S)
    assert m,'missing grid '+name
    rows=re.findall(r"'([#.\w]+)'",m.group(1))
    unit=float(m.group(2))
    assert rows and len(set(map(len,rows)))==1,name+' ragged rows'
    width=len(rows[0]);height=len(rows)
    p={c:[] for c in 'TCAB'}
    for ri,row in enumerate(rows):
        for ci,ch in enumerate(row):
            if ch in p:p[ch].append((round(((ci+.5)-width/2)*unit,2),round(((ri+.5)-height/2)*unit,2)))
    for side in 'TC':
        assert len(p[side])==5,(name,side,'not 5 base cells')
    for site in 'AB':
        assert len(p[site])>=5,(name,site,'insufficient bombsite')
    print('MAP',name,'BOMBS',{
        key:[round(sum(x[i] for x in p[key])/len(p[key]),1) for i in (0,1)] for key in 'AB'})
    print('BASES',name,p['T'],p['C'])
    maps[name]=p
# Cargo must not be overrun by a mid-corridor start masquerading as an attacker base.
assert 'MAPS.cargo.spawns.splice(0, 5' not in s,'Cargo T start is overridden to mid!'
assert all(abs(z-26.6)<.1 for x,z in maps['cargo']['T']),'Cargo attacker base lost'
assert all(-6<=z<=4 for key in 'AB' for x,z in maps['cargo'][key]),'Cargo objective still next to CT spawn'
# Validate authored barrier positions and flag any altered CT starts pushed through solid walls.
match=re.search(r'const PRE_BARRIERS\s*=\s*Object\.freeze\(\{(.*?)\n\}\);',s,re.S)
assert match,'missing freeze barriers'
for name in maps:
    m=re.search(r'\b'+name+r'\s*:\s*\{(.*?)\n\s*\}',match.group(1),re.S)
    assert m,'barriers missing '+name
    b=m.group(1)
    t=re.search(r'\bt\s*:\s*\[(.*?)\],\s*ct\s*:',b,re.S)
    ct=re.search(r'\bct\s*:\s*\[(.*?)\]',b,re.S)
    assert t and ct,'bad barrier '+name
    tvals=[int(x) for x in re.findall(r'\bv:\s*(-?\d+)',t.group(1))]
    cvals=[int(x) for x in re.findall(r'\bv:\s*(-?\d+)',ct.group(1))]
    assert len(tvals)==len(cvals)==2,(name,tvals,cvals)
    assert len(set(tvals))==len(set(cvals))==1,'split barriers out of sync '+name
    tgate,cgate=tvals[0],cvals[0]
    assert all(z>=tgate+1.0 for x,z in maps[name]['T']), 'T spawns across own freeze barrier '+name
    assert all(z<=cgate-1.0 for x,z in maps[name]['C']), 'CT spawns across own freeze barrier '+name
    print('GATES',name,'T',tgate,'CT',cgate,'author-base OK')
print('PASS four authored spawn areas and Cargo objective relocation')
