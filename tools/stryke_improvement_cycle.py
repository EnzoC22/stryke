#!/usr/bin/env python3
"""STRYKE 20-minute improvement shortlist and narrow, guarded automatic regressions.

No model inference occurs in this runner. It prioritizes measured source/map
signals and recurring design opportunities; only previously validated exact
regression signatures can be auto-repaired by --apply. Never randomly mutate
map geometry, weapons, models, gameplay balance or anti-cheat heuristics.
"""
import argparse, collections, json, os, re
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'index.html'
TYPES=('vanta','frostline','kairo','cargo')
SOLID=set('#cquvhipbxk')
def parse():
    src=SOURCE.read_text(encoding='utf-8')
    maps={}
    for name in TYPES:
        matches=list(re.finditer(r'MAPS\.'+name+r'\s*=\s*gridMap\(\[\s*(.*?)\s*\],\s*([\d.]+)',src,re.S))
        if not matches:raise SystemExit('Missing competitive map '+name)
        m=matches[-1]  # last grid definition wins at runtime
        rows=re.findall(r"'([#.\w]+)'",m.group(1))
        if not rows or len({len(x) for x in rows})!=1:raise SystemExit('Invalid '+name+' grid')
        maps[name]=(rows,float(m.group(2)))
    return src,maps
def shortest(rows,starting,finish):
    width=len(rows[0]);height=len(rows)
    allowed=lambda r,c:0<=r<height and 0<=c<width and rows[r][c] not in SOLID
    q=collections.deque((r,c,0) for r,c in starting if allowed(r,c))
    seen={(r,c) for r,c,_ in q}
    target=set(finish)
    while q:
        r,c,d=q.popleft()
        if (r,c) in target:return d
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr,cc=r+dr,c+dc
            if allowed(rr,cc) and (rr,cc) not in seen:
                seen.add((rr,cc));q.append((rr,cc,d+1))
    return None
def inspect_map(name,rows,cell):
    pts={ch:[] for ch in 'TCAB'}
    for r,row in enumerate(rows):
        for c,ch in enumerate(row):
            if ch in pts:pts[ch].append((r,c))
    metrics={'map':name,'T_slots':len(pts['T']),'CT_slots':len(pts['C']),'sites':{},'cover_density':0}
    for site in 'AB':
        t=shortest(rows,pts['T'],pts[site])
        ct=shortest(rows,pts['C'],pts[site])
        lead=round((t-ct)*cell,1) if t is not None and ct is not None else None
        metrics['sites'][site]={'t_steps':t,'ct_steps':ct,'ct_lead_units':lead,
                               'plant_tiles':len(pts[site])}
    return metrics
def proposals(src,maps,metrics):
    found=[]
    def add(score,category,title,reason,automatable=False):
        found.append(dict(score=score,category=category,title=title,
                          reason=reason,automatable=automatable))
    for m in metrics:
        name=m['map']
        if m['T_slots']!=5 or m['CT_slots']!=5:
            add(100,'spawn',f'{name}: restaurar posições 5v5',
                f"T={m['T_slots']} / CT={m['CT_slots']} marcadores; exigir 5 por equipe")
        for site,d in m['sites'].items():
            if d['t_steps'] is None or d['ct_steps'] is None:
                add(100,'rotas',f'{name}: reabrir acesso ao bombsite {site}',
                    'A malha de células não conecta ambas as bases ao objetivo')
            elif d['ct_lead_units']>27:
                add(93,'balanceamento',f'{name}: reduzir vantagem defensiva em {site}',
                    f'Heurística em grade sugere {d["ct_lead_units"]} unidades CT; conferir no Chromium antes de corrigir')
            elif d['ct_lead_units']< -27:
                add(85,'balanceamento',f'{name}: revisar chegada defensiva em {site}',
                    f'Heurística em grade sugere {-d["ct_lead_units"]} unidades T; confirmar no Chromium')
            if d['plant_tiles']<5:
                add(92,'bombsite',f'{name}: ampliar espaço utilizável em {site}',
                    f'Apenas {d["plant_tiles"]} células de plant no grid')
    if "return [[bx, bz]];" in src[src.index('function navPath('):src.index('function navPath(')+3000]:
        add(97,'bots','Impedir caminhos diretos por paredes','Fallback inseguro detectado em navPath',True)
    if "V44.2: a defuse cannot win" not in src:
        add(97,'bomba','Restaurar precedência da explosão','Guard V44.2 contra defuse tardio ausente',True)
    if 'MAPS.cargo.spawns.splice(0, 5' in src:
        add(100,'spawn','Cargo: remover nascimento T no meio','Override V44 da base atacante voltou',True)
    if "navigator.maxTouchPoints > 0" in src and "const MOBILE =" in src:
        add(70,'mobile','Detectar ponteiro principal para HUD mobile',
            'Desktop híbrido pode ser classificado como celular',True)
    # Fresh opportunities are hypotheses, not confirmed bugs. Rotate them
    # across runs so the team sees different useful development priorities.
    ideas=[
      ('mapas','Auditar duas rotas independentes por bombsite','Medir flancos, gargalos, covers e posições de retake'),
      ('bots','Aprimorar rotações A/B dos bots','Comparar tempo de defesa, flanco e pós-plant com seed fixa'),
      ('combate','Instrumentar impactos, recoil e registro de headshots','Registrar divergências cliente/host sem mudar autoridade'),
      ('rede','Simular perda de pacotes e 120–250ms de RTT','Verificar correção temporal e reconexão em duas abas'),
      ('visual','Comparar legibilidade de Kairo e Frostline','Eliminar pontos de luz estourada sem sobrecarga de renderização'),
      ('UX','Revisar compra e mensagens de objetivo em celulares','Checar legibilidade, arrasto e cancelamento de controles'),
      ('performance','Medir p95 frame time por mapa','Reduzir compilação de shaders e GC nas primeiras rodadas'),
      ('mapas','Revisar alturas e covers dos pontos A/B','Evitar posições dominantes e ângulos sem contra-jogo'),
    ]
    slot=int(datetime.now(timezone.utc).timestamp()//1200)
    for i in range(4):
        category,title,reason=ideas[(slot+i*2)%len(ideas)]
        add(65-i,category,title,reason)
    found.sort(key=lambda x:-x['score'])
    return found[:4]
def guarded_fix(s):
    fixes=[]
    a=s.find('function navPath(ax, az, bx, bz) {')
    b=s.find('// ================================================================',a)
    if a>=0 and a<b<a+3600:
        fragment=s[a:b]
        matches=fragment.count('return [[bx, bz]];')
        if matches==3:
            s=s[:a]+fragment.replace('return [[bx, bz]];','return [];')+s[b:]
            fixes.append('Restored safe bot navigation fallback')
    if 'V44.2: a defuse cannot win' not in s:
        a=s.find('function bombTick() {');b=s.find('function srvBuy(',a)
        if a>=0 and a<b<a+7000:
            fragment=s[a:b]
            original="    if (now < a.end) continue;\n    p.act = null; p.money = Math.min(16000, p.money + 300);"
            changed=("    if (now < a.end) continue;\n"
                     "    // V44.2: a defuse cannot win if its completion tick occurs after the bomb deadline.\n"
                     "    if (a.k === 'd' && B?.st === 'planted' && now >= B.end) { p.act = null; continue; }\n"
                     "    p.act = null; p.money = Math.min(16000, p.money + 300);")
            if fragment.count(original)==1:
                s=s[:a]+fragment.replace(original,changed)+s[b:]
                fixes.append('Restored expired-bomb priority guard')
    old="const MOBILE = matchMedia('(pointer:coarse)').matches || navigator.maxTouchPoints > 0;"
    if s.count(old)==1:
        s=s.replace(old,"const MOBILE = matchMedia('(pointer:coarse)').matches;")
        fixes.append('Restored primary-pointer mobile detection')
    # Deliberately do not rewrite T/CT spawns automatically: moving a player
    # without verifying route timing and freeze barriers caused the V44 bug.
    return s,fixes

ap=argparse.ArgumentParser()
ap.add_argument('--apply',action='store_true')
ap.add_argument('--report',default='reports/stryke-cycle-latest.json')
args=ap.parse_args()
src,maps=parse()
data=[inspect_map(name,*maps[name]) for name in TYPES]
fixsrc,fixes=guarded_fix(src)
if args.apply and fixes:
    if abs(len(fixsrc)-len(src))>800:raise SystemExit('Unexpected autofix size; refusing')
    SOURCE.write_text(fixsrc,encoding='utf-8')
report={'utc':datetime.now(timezone.utc).isoformat(),'maps':data,
        'ideas':proposals(src,maps,data),'applied':fixes if args.apply else [],
        'pending_safe_repairs':fixes,'mode':'rules-and-metrics (no background AI model)'}
path=ROOT/args.report
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary=os.environ.get('GITHUB_STEP_SUMMARY')
out=['## STRYKE · Ciclo de melhoria (20 minutos)',
     'Auditoria de mapas e ranking por regras; métricas da grade são aproximadas e não substituem o teste Chromium. **Não é uma sessão autônoma do ChatGPT.**','']
for i,idea in enumerate(report['ideas'],1):
    out.append(f"{i}. **{idea['title']}** — {idea['reason']}")
out.extend(['',f"**Correções previamente verificadas aplicadas:** {', '.join(report['applied']) or 'nenhuma (jogo preservado)'}"])
md='\n'.join(out)+'\n'
print(md)
if summary:Path(summary).open('a',encoding='utf8').write(md)
