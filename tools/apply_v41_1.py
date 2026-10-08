from pathlib import Path
p=Path("index.html")
s=p.read_text(encoding="utf-8")
if "V41.1 STAGED MATCH SETUP" in s:
    print("V41.1 already applied")
    raise SystemExit(0)

m=s.index("function matchForm(el, st0)")
start=s.index("  const render = () => {",m)
end=s.index("  return () => {",start)
new=r'''  let mapConfirmed = false;
  const render = () => {
    if (st.mode === 'rounds' && !STRYKE_COMP_MAPS.includes(st.map)) st.map = 'cargo';
    if (st.mode === 'dm') st.map = 'cargo';
    const z = st.mode === 'zombies', cur = z ? st.zmap : st.map;
    const maps = Object.entries(MAPS).filter(([k, m]) => z ? !!m.zonly : k === 'cargo');
    const opts = z
      ? \`<div class="lbl">Dificuldade</div>\${seg('zdiff', ZDIFF.map((d, i) => [i, d.name]))}<div class="zdesc"><b>\${ZDIFF[st.zdiff].name}:</b> \${ZDIFF[st.zdiff].desc}</div>\`
      : \`<div class="optrow">\${st.mode === 'rounds' ? \`<div><div class="lbl">Rodadas para vencer</div>\${seg('rounds', [3, 5, 8, 10, 13, 16].map(n => [n, n]))}</div><div><div class="lbl">Fogo amigo</div>\${seg('ff', [[1, 'Ligado'], [0, 'Desligado']])}</div>\` : \`<div><div class="lbl">Abates para vencer</div>\${seg('frags', [10, 15, 20, 30, 50].map(n => [n, n]))}</div>\`}
        <div><div class="lbl">Bots</div>\${seg('bots', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => [n, n]))}</div>
        <div><div class="lbl">Nível dos bots</div>\${seg('diff', [[0, 'Treino'], [1, 'Fácil'], [2, 'Normal'], [3, 'Difícil'], [4, 'Elite']])}</div>
        <div><div class="lbl">Bots por rank</div>\${seg('botRank', [[0, 'Manual'], [1, 'Seu rank']])}</div></div>\`;
    const config = mapConfirmed
      ? \`<div class="match-config-reveal"><div class="match-step-head"><span>03</span><div><b>CONFIGURAÇÃO DA PARTIDA</b><small>Ajuste as regras antes de criar a sala.</small></div></div>\${opts}</div>\`
      : \`<div class="match-config-lock"><span>03</span><div><b>CONFIGURAÇÃO DA PARTIDA</b><small>Selecione um mapa acima para liberar rounds, bots, dificuldade e outras regras.</small></div></div>\`;
    el.innerHTML = \`<div class="match-setup-progress"><i class="done">01</i><em></em><i class="\${mapConfirmed?'done':''}">02</i><em></em><i class="\${mapConfirmed?'active':''}">03</i></div>
      <div class="match-step-title"><span>01</span><div><b>MODO</b><small>Escolha como a partida será jogada.</small></div></div>
      <div class="cards">\${MODES.map(([k, t, d]) => \`<button type="button" class="card\${st.mode === k ? ' on' : ''}" data-mode="\${k}"><span class="micon">\${MICON[k]}</span><b>\${t}</b><small>\${d}</small></button>\`).join('')}</div>
      <div class="match-step-title"><span>02</span><div><b>MAPA</b><small>Escolha o campo de batalha para continuar.</small></div></div>
      <div class="cards">\${maps.map(([k, m]) => \`<button type="button" class="card\${mapConfirmed && cur === k ? ' on' : ''}" data-map="\${k}"><div class="thumb" style="background:linear-gradient(180deg,\${hex(m.skyTop ?? m.sky)},\${hex(m.fogC ?? m.sky)} 56%,\${hex(m.theme.floor?.[1] ?? 0x555555)} 58%,#0c0d0b)"></div><b>\${m.name}</b><small>\${m.desc}</small><strong class="map-select-cta">\${mapConfirmed && cur === k ? 'SELECIONADO' : 'SELECIONAR MAPA'}</strong></button>\`).join('')}</div>
      \${config}\`;
  };
  el.onclick = e => {
    const b = e.target.closest('button'); if (!b || !el.contains(b)) return;
    if (b.dataset.mode) { st.mode = b.dataset.mode; mapConfirmed = false; }
    else if (b.dataset.map) { st[st.mode === 'zombies' ? 'zmap' : 'map'] = b.dataset.map; mapConfirmed = true; }
    else if (b.dataset.k) st[b.dataset.k] = +b.dataset.v;
    render();
  };
  render();
'''
s=s[:start]+new+s[end:]

css=r'''
/* V41.1 staged match creation */
.match-setup-progress{display:flex;align-items:center;gap:8px;margin:2px 0 18px}.match-setup-progress i{width:30px;height:30px;border-radius:999px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.035);color:#6f7c8d;font:800 11px Inter,sans-serif;font-style:normal;letter-spacing:.04em}.match-setup-progress i.done{border-color:rgba(255,61,77,.5);background:rgba(255,61,77,.16);color:#fff}.match-setup-progress i.active{border-color:rgba(134,255,71,.45);background:rgba(134,255,71,.12);color:#baff92}.match-setup-progress em{width:42px;height:1px;background:rgba(255,255,255,.10)}
.match-step-title,.match-step-head{display:flex;align-items:center;gap:11px;margin:18px 0 10px}.match-step-title>span,.match-step-head>span,.match-config-lock>span{display:grid;place-items:center;width:31px;height:31px;flex:none;border-radius:8px;background:rgba(255,61,77,.12);border:1px solid rgba(255,61,77,.26);color:#ff6a76;font:800 10px Inter,sans-serif;letter-spacing:.06em}.match-step-title b,.match-step-head b,.match-config-lock b{display:block;color:#f2f5f8;font:800 13px Rajdhani,sans-serif;letter-spacing:.16em}.match-step-title small,.match-step-head small,.match-config-lock small{display:block;margin-top:2px;color:#718094;font:500 10px/1.35 Inter,sans-serif}.map-select-cta{position:absolute;left:12px;top:10px;padding:4px 7px;border-radius:5px;background:rgba(5,8,12,.72);border:1px solid rgba(255,255,255,.12);color:#b8c4d2;font:800 8px Inter,sans-serif;letter-spacing:.12em}.card.on .map-select-cta{background:#ff4655;border-color:#ff6875;color:#fff}.match-config-reveal{margin-top:18px;padding-top:2px;border-top:1px solid rgba(255,255,255,.08);animation:matchReveal .22s ease both}.match-config-lock{display:flex;align-items:center;gap:12px;margin-top:18px;padding:15px 14px;border-radius:14px;border:1px dashed rgba(255,255,255,.11);background:rgba(255,255,255,.018);opacity:.78}.match-config-lock>span{background:rgba(255,255,255,.035);border-color:rgba(255,255,255,.10);color:#687587}@keyframes matchReveal{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
'''
s=s.replace("</style>",css+"\n</style>",1)
s=s.replace("STRYKE <b>4.5 // V41 OPERATIONS UI + VISUAL OVERHAUL</b>","STRYKE <b>4.5.1 // V41.1 STAGED MATCH SETUP</b>",1)
p.write_text(s,encoding="utf-8")
print("V41.1 patched",len(s))
