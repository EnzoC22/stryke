STRYKE 4.4 // V40 ANTI-ESP + CONSOLE LOCKDOWN
================================================
Base: V39.

- window.__T removido/travado.
- hooks globais de teste só existem em DEBUG, que fica false na build pública.
- posição de inimigo passa por PVS/fog-of-war no host: sem linha de visão, o cliente deixa de receber coordenadas exatas atuais.
- teammates continuam sincronizados; pre-round nunca revela inimigos entre times.
- 300 ms de grace evita pop visual durante peeks.
- cliente recebe 'fog', limpa interpolação e oculta o modelo.
- V39 mantém validação host-side de velocidade/noclip/fly, arma, cadência, munição, origem do tiro, raio do acerto e teto de dano.

Limite: browser/P2P não torna o host criptograficamente confiável e não elimina screen-reading aimbot em alvo já visível. Ranked sério requer servidor dedicado.
