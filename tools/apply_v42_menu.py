from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

start=s.index('function matchForm(el, st0) {')
end=s.index('// ---------- mira:', start)
new_func=r'''function matchForm(el, st0) {
  const advanced = el.id === 'lbForm' || el.id === 'pauseForm';
  const st = { map: 'cargo', zmap: 'vila', mode: 'rounds', preset: 'competitive', rounds: 13, ff: 0, frags: 30, bots: 0, diff: 2, botRank: 0, zdiff: 1, ...st0 };
  if (!['competitive', 'swift', 'dm', 'custom', 'zombies', 'training'].includes(st.preset)) st.preset = st.mode === 'zombies' ? 'zombies' : st.mode === 'dm' ? 'dm' : (+st.rounds <= 5 ? 'swift' : 'competitive');
  if (!MAPS[st.map] || MAPS[st.map].zonly) st.map = 'cargo';
  if (!MAPS[st.zmap]?.zonly) st.zmap = 'vila';
  const ROUNDS = [3,5,8,10,13,16], FRAGS=[10,15,20,30,50];
  st.rounds = ROUNDS.includes(+st.rounds) ? +st.rounds : 13; st.frags = FRAGS.includes(+st.frags) ? +st.frags : 30; st.bots=clamp(st.bots|0,0,9); st.diff=clamp(st.diff|0,0,4); st.botRank=st.botRank?1:0; st.zdiff=clamp(st.zdiff|0,0,ZDIFF.length-1);
  const hex=c=>'#'+(c>>>0).toString(16).padStart(6,'0');
  const seg=(k,opts)=>`<div class="seg">${opts.map(([v,t])=>`<button type="button" data-k="${k}" data-v="${v}"${String(st[k])===String(v)?' class="on"':''}>${t}</button>`).join('')}</div>`;
  const PRESETS=[
    ['competitive','COMPETITIVO','5v5 · MR13 · economia completa'],
    ['swift','DISPUTA RÁPIDA','5v5 · partida curta'],
    ['dm','MATA-MATA','Respawn instantâneo · treino de mira'],
    ['custom','PERSONALIZADA','Sala com regras editáveis'],
    ['training','TREINO','Bots e aquecimento'],
    ['zombies','ZUMBIS','Cooperativo PvE']
  ];
  const applyPreset=k=>{
    st.preset=k;
    if(k==='competitive'){st.mode='rounds';st.rounds=13;st.ff=0;st.bots=0;st.diff=2;st.botRank=0;st.map='cargo';}
    else if(k==='swift'){st.mode='rounds';st.rounds=5;st.ff=0;st.bots=0;st.diff=1;st.botRank=0;st.map='cargo';}
    else if(k==='dm'){st.mode='dm';st.frags=30;st.bots=0;st.diff=2;st.botRank=0;st.map='cargo';}
    else if(k==='training'){st.mode='dm';st.frags=20;st.bots=5;st.diff=1;st.botRank=0;st.map='cargo';}
    else if(k==='custom'){st.mode='rounds';st.map='cargo';}
    else if(k==='zombies'){st.mode='zombies';st.zmap=MAPS[st.zmap]?.zonly?st.zmap:'vila';st.bots=0;}
  };
  applyPreset(st.preset);
  const modeTabs=()=>`<div class="mode-select-v42">${PRESETS.map(([k,t,d])=>`<button type="button" data-preset="${k}" class="${st.preset===k?'on':''}"><b>${t}</b><small>${d}</small></button>`).join('')}</div>`;
  const cargoCard=()=>{const m=MAPS.cargo;return `<button type="button" class="card on v42-map-card" data-map="cargo"><div class="thumb" style="background:linear-gradient(180deg,${hex(m.skyTop??m.sky)},${hex(m.fogC??m.sky)} 56%,${hex(m.theme.floor?.[1]??0x555555)} 58%,#0c0d0b)"></div><b>${m.name}</b><small>${m.desc}</small><strong class="map-select-cta">SELECIONADO</strong></button>`;};
  const customOptions=()=>{
    if(st.preset==='zombies')return `<div class="lbl">Dificuldade</div>${seg('zdiff',ZDIFF.map((d,i)=>[i,d.name]))}<div class="zdesc"><b>${ZDIFF[st.zdiff].name}:</b> ${ZDIFF[st.zdiff].desc}</div>`;
    return `<div class="optrow">${st.mode==='rounds'?`<div><div class="lbl">Rodadas para vencer</div>${seg('rounds',ROUNDS.map(n=>[n,n]))}</div><div><div class="lbl">Fogo amigo</div>${seg('ff',[[1,'Ligado'],[0,'Desligado']])}</div>`:`<div><div class="lbl">Abates para vencer</div>${seg('frags',FRAGS.map(n=>[n,n]))}</div>`}<div><div class="lbl">Bots</div>${seg('bots',[0,1,2,3,4,5,6,7,8,9].map(n=>[n,n]))}</div><div><div class="lbl">Nível dos bots</div>${seg('diff',[[0,'Treino'],[1,'Fácil'],[2,'Normal'],[3,'Difícil'],[4,'Elite']])}</div><div><div class="lbl">Bots por rank</div>${seg('botRank',[[0,'Manual'],[1,'Seu rank']])}</div></div>`;
  };
  const summary=()=>st.preset==='competitive'?'MR13 · friendly fire desligado · sem bots':st.preset==='swift'?'Primeiro a 5 · sem bots':st.preset==='dm'?'${st.frags} abates · respawn instantâneo':st.preset==='training'?'${st.bots} bots · respawn instantâneo':st.preset==='zombies'?`Cooperativo · ${ZDIFF[st.zdiff]?.name||'Normal'}`:'Regras personalizadas';
  const render=()=>{
    const selected=PRESETS.find(x=>x[0]===st.preset)||PRESETS[0];
    if(!advanced) el.innerHTML=`<div class="v42-queue-shell"><div class="v42-label">ESCOLHA O MODO</div>${modeTabs()}<div class="v42-selected-mode"><span>SELECIONADO</span><div><b>${selected[1]}</b><small>${selected[2]}</small></div></div><div class="v42-map-section"><div class="v42-label">MAPA</div>${st.preset==='zombies'?'<div class="hint">O mapa de Zumbis é escolhido dentro da sala.</div>':cargoCard()}</div><div class="v42-room-note"><i>i</i><div><b>PRONTO PARA CRIAR A SALA</b><small>Regras avançadas, bots e dificuldade só aparecem no lobby depois que a sala for criada.</small></div></div></div>`;
    else {const editable=['custom','training','zombies'].includes(st.preset);el.innerHTML=`<div class="v42-lobby-config"><div class="v42-label">MODO DA SALA</div>${modeTabs()}<div class="v42-lobby-summary"><span>${selected[1]}</span><b>${summary()}</b></div>${st.preset!=='zombies'?`<div class="v42-label">MAPA</div>${cargoCard()}`:''}<div class="v42-label">CONFIGURAÇÃO DA SALA</div>${editable?customOptions():`<div class="v42-preset-lock"><b>REGRAS DO MODO</b><span>${summary()}</span><small>Para editar rounds, bots, friendly fire e dificuldade, selecione PERSONALIZADA.</small></div>`}</div>`;}
  };
  el.onclick=e=>{const b=e.target.closest('button');if(!b||!el.contains(b))return;if(b.dataset.preset)applyPreset(b.dataset.preset);else if(b.dataset.map)st.map=b.dataset.map;else if(b.dataset.k)st[b.dataset.k]=+b.dataset.v;render();};
  render();
  return()=>({map:st.preset==='zombies'?st.zmap:st.map,cmap:st.map,zmap:st.zmap,mode:st.mode,preset:st.preset,rounds:st.rounds,ff:st.ff??0,frags:st.frags,bots:st.preset==='zombies'?0:st.bots,diff:st.diff,botRank:st.preset==='zombies'?0:(st.botRank?1:0),zdiff:st.zdiff});
}
'''
s=s[:start]+new_func+s[end:]
s=s.replace("const MODE_N = { rounds: 'Rodadas', dm: 'Mata-mata', zombies: 'Zumbis' };","const MODE_N = { rounds: 'Rodadas', dm: 'Mata-mata', zombies: 'Zumbis' };\nconst PRESET_N = { competitive:'Competitivo', swift:'Disputa Rápida', dm:'Mata-mata', custom:'Personalizada', training:'Treino', zombies:'Zumbis' };",1)
s=s.replace("mode: MODE_N[S.st?.mode] || ''","mode: PRESET_N[S.st?.preset] || MODE_N[S.st?.mode] || ''",1)
s=s.replace("Modo: <b>${MODE_N[st.mode] || '-'}</b>","Modo: <b>${PRESET_N[st.preset] || MODE_N[st.mode] || '-'}</b>",1)
s=s.replace("$('#btnHost').textContent = 'Criar sala pública';","$('#btnHost').textContent = 'Criar sala';",1)
p.write_text(s,encoding='utf-8')
print('V42 menu patched',len(s))
