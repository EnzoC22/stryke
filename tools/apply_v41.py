from pathlib import Path

p=Path("index.html")
s=p.read_text(encoding="utf-8")
if "V41 OPERATIONS UI + VISUAL OVERHAUL" in s:
    print("V41 already applied")
    raise SystemExit(0)

repls=[
(
'<nav class="tabs"><button data-tab="play" class="on">JOGAR</button><button data-tab="career">CARREIRA</button><button data-tab="rank">RANK</button><button data-tab="skins">COLEÇÃO</button><button data-tab="cases">CAIXAS</button><button data-tab="store">LOJA</button><button data-tab="social">SOCIAL</button><button data-tab="cfg">⚙</button></nav>',
'<nav class="tabs"><button data-tab="play" class="on">JOGAR</button><button data-tab="skins">ARSENAL</button><button data-tab="career">CARREIRA</button><button data-tab="rank">RANK</button><button data-tab="cases">INVENTÁRIO</button><button data-tab="store">LOJA</button><button data-tab="social">SOCIAL</button><button data-tab="cfg">CONFIGURAÇÕES</button></nav>'
),
(
'<section class="stryke-stage"><canvas id="lobbyPrev"></canvas><div class="stage-copy"><div class="eyebrow">STRYKE // TACTICAL FPS</div><h2>AIM. MOVE. WIN.</h2><p>Controle o meio, abra espaço para o time e execute o site. Movimento preciso e leitura de mapa vencem a rodada.</p><div class="stage-chips"><span>COUNTER-STRAFE</span><span>SPRAY CONTROL</span><span>TACTICAL MAPS</span><span>RANKED</span></div></div><div class="stage-rank"><small>SEASON 01</small><b id="stageRank">PRATA II</b><i></i></div></section>',
'<section class="stryke-stage"><canvas id="lobbyPrev"></canvas><div class="stage-copy"><div class="eyebrow">SEASON 01</div><h2>COMPETITIVE<br>TACTICAL FPS</h2><div class="stage-opline">OPERATION <span>//</span> CARGO</div><p>Disciplina, estratégia e trabalho em equipe. Monte o grupo, domine o mapa e execute cada round com leitura, utilidade e precisão.</p><div class="stage-chips"><span>COUNTER-STRAFE</span><span>SPRAY CONTROL</span><span>CLUTCH 5x5</span><span>RANKED CORE</span></div></div><div class="stage-rank"><small>RANK ATUAL</small><b id="stageRank">PRATA II</b><i></i></div><div class="stage-bottom-cards"><button class="stage-mini" data-v41tab="rank"><span>SEASON 01</span><b>RANK COMPETITIVO</b><small>Acompanhe RR, vitórias e evolução.</small></button><button class="stage-mini" data-v41tab="skins"><span>ARSENAL</span><b>COLEÇÃO & SKINS</b><small>Equipe armas e organize o loadout.</small></button><button class="stage-mini" data-v41tab="cases"><span>INVENTÁRIO</span><b>CAIXAS E RECOMPENSAS</b><small>Abra drops e compre novas caixas.</small></button></div></section>'
),
("<h3>Criar partida</h3>","<h3>Jogar agora</h3>"),
("<h3>Entrar com código</h3>","<h3>Sala personalizada</h3>"),
("STRYKE <b>4.4 // V40 ANTI-ESP + CONSOLE LOCKDOWN</b>","STRYKE <b>4.5 // V41 OPERATIONS UI + VISUAL OVERHAUL</b>"),
("[STRYKE] V40 ANTI-ESP + CONSOLE LOCKDOWN — no debug surface + server-side visibility filtering","[STRYKE] V41 OPERATIONS UI + VISUAL OVERHAUL — unified menu, HUD and cinematic presentation"),
("const BLOOM0 = { s: .5, r: .45, t: .85 };","const BLOOM0 = { s: .58, r: .48, t: .88 };"),
("renderer.toneMappingExposure = 1.15;","renderer.toneMappingExposure = 1.08;")
]
for a,b in repls:
    if a not in s:
        print("missing anchor:",a[:80])
    s=s.replace(a,b,1)

css=r"""
/* ===== V41 OPERATIONS UI + VISUAL OVERHAUL ===== */
:root{--s-red:#ff3d4d;--s-lime:#86ff47;--s-blue:#7aa8ff;--acc:var(--s-red);--acc2:var(--s-lime)}
#menu{background:linear-gradient(90deg,#020407f8,#020407d8 20%,#02040794 48%,#020407c8),radial-gradient(circle at 77% 14%,#ff3d4d24,transparent 27%),radial-gradient(circle at 74% 18%,#7aa8ff20,transparent 34%),linear-gradient(135deg,#07101a,#020407 72%)}
#menu .mshell{display:grid;grid-template-columns:310px minmax(0,1fr);height:100%}
#menu .mtop{grid-column:1;display:flex;flex-direction:column;align-items:stretch;gap:15px;height:100%;padding:25px 23px 21px;background:linear-gradient(180deg,#04080df7,#04080de3);border-right:1px solid #ffffff14;border-bottom:0}
#menu .mlogo{font-size:48px;line-height:.9;letter-spacing:2px;font-weight:800;display:flex;align-items:center;gap:9px;color:#fff;margin-bottom:5px;text-shadow:none}
#menu .mlogo small{font-size:9px;letter-spacing:.32em;color:#788697;margin-left:0}
#menu .stryke-mark{width:32px;height:32px;background:var(--s-red);font-size:21px}
#menu .tabs{display:flex;flex-direction:column;gap:7px;flex:none;height:auto;align-items:stretch;margin:7px 0 3px}
#menu .tabs button{opacity:1!important;position:relative;display:flex;align-items:center;justify-content:flex-start;min-height:54px;padding:0 17px;border-radius:5px;border:1px solid #ffffff13;background:linear-gradient(180deg,#ffffff09,#ffffff03);color:#b6c2d0;font-size:16px;font-weight:700;letter-spacing:.12em}
#menu .tabs button:after{content:'›';margin-left:auto;color:#758394;font-size:22px}
#menu .tabs button:hover{color:#fff;border-color:#ffffff29;background:#ffffff0d}
#menu .tabs button.on{border-color:#ff3d4d6b;background:linear-gradient(90deg,#ff3d4d3b,#ff3d4d0e 57%,#ffffff05);color:#fff;box-shadow:inset 7px 0 var(--s-red)}
#menu .hub-badges{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:2px 0 5px}
#menu .hub-pill{padding:7px 8px;background:#ffffff08;border:1px solid #ffffff13;text-align:center;font-size:9px;color:#8f9eaf}
#menu .hub-pill b{display:block;margin-top:3px;color:#fff;font-size:13px}
#menu .mplayer{margin-top:auto;min-width:0;border-radius:16px;padding:8px 11px 9px 8px;background:linear-gradient(180deg,#ffffff0b,#ffffff04);border:1px solid #ffffff14}
#menu .mav{width:52px;height:52px;border-radius:13px;background:linear-gradient(135deg,var(--s-red),#b5182b);font-size:25px;color:#fff}
#menu .mpsub b{color:var(--s-lime)}#menu .mpxp i{background:linear-gradient(90deg,var(--s-red),#ff7b86)}
#menu .mbody{grid-column:2;overflow:auto;padding:27px 29px}.playgrid{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:18px;align-items:start}
#menu .box,#menu .store-item,#menu .case-stat,#menu .hub-card,#menu .rank-card,#menu .rank-ladder,#menu .vcoll{background:linear-gradient(180deg,#070b10db,#080d14c7);border:1px solid #ffffff14;border-radius:20px;box-shadow:0 24px 80px #00000042;backdrop-filter:blur(10px)}
.stryke-stage{grid-column:1;grid-row:2/span 2;min-height:670px;height:auto;position:relative;overflow:hidden;border-radius:26px;border:1px solid #ffffff17;clip-path:none;box-shadow:0 28px 90px #00000061;background:radial-gradient(circle at 74% 18%,#ff3d4d21,transparent 21%),radial-gradient(circle at 75% 23%,#7aa8ff1f,transparent 30%),linear-gradient(135deg,#08111a,#020508 76%)}
.stryke-stage:before{content:'';position:absolute;inset:0;z-index:2;pointer-events:none;background:linear-gradient(90deg,#04080ce6 0%,#04080cb8 33%,#04080c1f 67%,#04080c80 100%),linear-gradient(180deg,#ffffff08,transparent 18%,transparent 86%,#ff3d4d0d)}
#lobbyPrev{position:absolute;inset:-10% -8% -8% 28%;width:80%;height:116%;z-index:1;filter:saturate(.78) contrast(1.14) brightness(.74) drop-shadow(0 24px 80px #000)}
.stage-copy{position:absolute;left:40px;top:39px;max-width:500px;z-index:3}.stage-copy .eyebrow{color:var(--s-red);font-size:12px;letter-spacing:.34em}.stage-copy h2{font:800 76px/.88 Rajdhani,sans-serif;letter-spacing:.015em;margin:11px 0 7px;color:#fff}.stage-opline{font:700 24px Rajdhani,sans-serif;letter-spacing:.08em;color:#dce5ef;margin:18px 0}.stage-opline span{color:var(--s-red);margin:0 8px}.stage-copy p{color:#c0cbd8;font-size:14px;line-height:1.52;max-width:410px}.stage-chips{display:flex;gap:9px;margin-top:17px;flex-wrap:wrap}.stage-chips span{padding:7px 11px;border-radius:999px;background:#ffffff0b;border:1px solid #ffffff1a;font-size:10px;letter-spacing:.13em;color:#dbe4ee}
.stage-rank{position:absolute;left:40px;bottom:154px;right:auto;top:auto;padding:17px 19px;min-width:270px;background:#070b10df;border:1px solid #ffffff14;border-radius:18px;text-align:left;z-index:3}.stage-rank b{display:block;margin-top:6px;font:800 34px Rajdhani,sans-serif;color:#fff}.stage-rank i{display:block;width:100%;height:7px;border-radius:30px;margin-top:13px;background:linear-gradient(90deg,var(--s-red),#ff8d75)}
.stage-bottom-cards{position:absolute;left:22px;right:22px;bottom:22px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;z-index:3}.stage-mini{padding:15px 17px 17px;text-align:left;border-radius:16px;border:1px solid #ffffff14;background:#070b10dc;color:#fff;backdrop-filter:blur(10px)}.stage-mini:hover{transform:translateY(-2px);border-color:#ff3d4d61;background:linear-gradient(180deg,#ff3d4d29,#070b10c2)}.stage-mini span{display:block;font-size:9px;letter-spacing:.23em;color:#8ba0b6;margin-bottom:7px}.stage-mini b{display:block;font:800 20px Rajdhani,sans-serif;color:#fff;margin-bottom:6px}.stage-mini small{color:#b7c3d1;font-size:11px}
#hostBox{grid-column:2;grid-row:2}#pside{grid-column:2;grid-row:3;display:flex;flex-direction:column;gap:14px}#hostBox .actbar{display:grid;grid-template-columns:1fr;gap:9px}#menu button.big{clip-path:none;border-radius:16px;min-height:56px;background:linear-gradient(180deg,#ff4e5d,#cc2137);box-shadow:0 14px 34px #ff3d4d38}
#hp,#ammo{padding:10px 14px 9px;background:linear-gradient(180deg,#070b10d9,#070b1085);border:1px solid #ffffff14;border-radius:16px;box-shadow:0 18px 50px #00000038}#hp{border-left:4px solid var(--s-red)}#ammo{border-right:4px solid var(--s-red)}#money{color:var(--s-lime);background:#070b10c7;border:1px solid #ffffff14;border-radius:13px;padding:7px 11px}#reload i{background:linear-gradient(90deg,var(--s-red),#ff8b72)}
#board{border-radius:20px;background:linear-gradient(180deg,#070b10eb,#080c12e0);border:1px solid #ff3d4d2e;box-shadow:0 24px 80px #0000006b;backdrop-filter:blur(12px)}#board tr.me td{color:var(--s-lime)}
#buy{background:radial-gradient(circle at 50% 0%,#ff3d4d1f,transparent 24%),linear-gradient(180deg,#05080cf5,#030508fa)}.bmwrap{padding:23px;border-radius:26px;border:1px solid #ffffff14;background:#070b10e8;box-shadow:0 30px 90px #00000073}.bmcred{color:var(--s-lime)}.bmc{border-radius:16px}.bmc:hover,.bmc.own{border-color:#ff3d4d61;background:linear-gradient(180deg,#ff3d4d24,#ffffff05)}
#chatlog div{background:#070b10c2;border-left:2px solid #ff3d4d8f;border-radius:8px;padding:4px 10px}#toast{border-radius:15px;background:#070b10e0;border:1px solid #ff3d4d33;box-shadow:0 18px 50px #00000052}
.stryke-build{padding:7px 11px;border-radius:999px;background:#04080c94}
@media(max-width:1100px){#menu .mshell{grid-template-columns:270px 1fr}.stage-copy h2{font-size:64px}.stage-bottom-cards{grid-template-columns:1fr}.stage-rank{bottom:246px}}
@media(max-width:940px){#menu .mshell{display:flex;flex-direction:column}#menu .mtop{height:auto;padding:15px;border-right:0;border-bottom:1px solid #ffffff14}#menu .tabs{flex-direction:row;flex-wrap:wrap}#menu .tabs button{flex:1 1 calc(50% - 8px);min-height:44px;font-size:13px}.playgrid{grid-template-columns:1fr}.stryke-stage{grid-column:1;grid-row:auto;min-height:600px}#hostBox,#pside{grid-column:1;grid-row:auto}}
"""
s=s.replace("</style>",css+"\n</style>",1)

hook="document.querySelectorAll('#menu .tabs button').forEach(b => b.onclick = () => {"
nav="document.addEventListener('click',e=>{const b=e.target.closest('[data-v41tab]');if(!b)return;document.querySelector('#menu .tabs [data-tab=\"'+b.dataset.v41tab+'\"]')?.click();});\n"
if hook not in s:
    raise SystemExit("tab hook not found")
s=s.replace(hook,nav+hook,1)

p.write_text(s,encoding="utf-8")
print("V41 applied",len(s))
