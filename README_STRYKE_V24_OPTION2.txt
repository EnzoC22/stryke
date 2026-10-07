STRYKE 3.0 // V24 OPTION 2

Objetivo desta build
--------------------
Testar a "Opção 2": em vez de aplicar uma fórmula genérica aos cinco mapas, Vanta foi redesenhado como uma vertical slice específica, área por área, para validar uma linguagem de level design antes de replicá-la.

VANTA // OPTION 2
-----------------
- B Compound: site fechado no noroeste, duas aproximações relevantes.
- Rotação Norte: caminho macro de rotação/retake no topo.
- Base Defesa: nicho no leste/nordeste; não enxerga a Base Ataque no início.
- Corredor Leste: rota em S que alimenta A e Mid.
- A Plaza: site mais aberto que B, com Warehouse de retake.
- Mid Market: área central de disputa e informação.
- Hotel Central: grande massa sólida que quebra sightlines e organiza as lanes.
- Flanco Oeste: rota longa que conecta ataque, Mid e B.
- Base Ataque: bolsão sudoeste com decisões rápidas para B/Mid/A.

BALANCEAMENTO TEÓRICO
---------------------
Com cell=4,6 m e velocidade RUN atual=6,65 m/s:
T -> A: 12 células ~ 8,30 s
CT -> A: 11 células ~ 7,61 s
vantagem CT em A: ~0,69 s

T -> B: 15 células ~ 10,38 s
CT -> B: 14 células ~ 9,68 s
vantagem CT em B: ~0,69 s

Linha de visão direta T Spawn <-> CT Spawn: 0 / 238 pares testados no grid.

IMPORTANTE
----------
Esses são tempos de rota teóricos da malha e não substituem playtest humano. A V24 foi feita para você testar a sensação real de first contact, entradas, retakes, rotações e leitura do mapa.

OUTRAS MUDANÇAS
---------------
- O tuning genérico antigo da V18 foi desativado em Vanta para não contaminar esta planta autoral.
- As paredes estruturais de Vanta continuam sendo geradas pelo sistema sólido da grid e entram nos colliders.
- F3 mantém o diagnóstico competitivo: callout, frame time/p95, FPS, ping, velocidade, spread e recoil.
- Os outros mapas permanecem na V23 apenas para comparação; esta build é propositalmente um teste de vertical slice em Vanta.

COMO ABRIR
----------
1. Extraia o ZIP.
2. Dê dois cliques em ABRIR_STRYKE.bat.
3. Crie uma partida de Rodadas e selecione "Vanta // Option 2".
4. Use F3 durante o teste para acompanhar diagnóstico.
