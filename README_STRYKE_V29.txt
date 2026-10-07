STRYKE 3.5 // V29 PERFORMANCE + GAMEPLAY FIXES
================================================

BASE
- STRYKE 3.4 V28 AI SUPER RESOLUTION.
- Gameplay, mapas, armas, dano, recoil, economia e protocolo da V28 preservados.

PERFORMANCE
- Shadow atlas Alto: 4096 -> 2048.
- ShadowMap autoUpdate fica desligado em todos os presets.
- Sombras dinâmicas no Alto são atualizadas em scheduler de até 12 Hz.
- EffectComposer: MSAA reduzido; com WebSR ativo, o alvo HalfFloat usa 0 samples.
- WebSR Auto agora tem resolução interna 0.40–0.65, cadência adaptativa 1x/1/2x e fallback por frame-time.
- A camada IA pode atualizar a 1/2 rate sem reduzir o FPS da simulação/render WebGL.
- Bots mantêm movimento/mira por frame, mas a busca cara por novos alvos roda ~12,5 Hz.
- Sprays compartilham a mesma geometria e limitam draw calls (4 por jogador / 48 globais).

SPRAYS
- Orientação estável: o spray permanece em pé em paredes.
- Piso usa direção da câmera como referência para não girar aleatoriamente.
- Tetos e superfícies dinâmicas não recebem spray.
- Offset/polygon offset revisados para reduzir z-fighting.
- Cooldown/rede existentes preservados.

ESPECTADOR
- Corrigido o alvo invisível após a morte.
- O player observado continua renderizado.
- Só a cabeça do player observado é ocultada localmente para a câmera não ficar dentro do capacete.
- Nome sobre a cabeça do alvo observado também é escondido.
- Continua restrito ao próprio time no modo Rodadas.

SKINS ÉPICAS+
- Neon, Lava, Asiimov, Esmeralda, Ouro, Dragão e Galáxia agora têm movimentos de inspeção distintos.
- As animações são cosméticas e não alteram tiro, recoil, hitbox ou cadência.
- Funciona com armas e adiciona flourish sobre inspeções de faca quando a skin é Épica/Lendária.

TESTES RECOMENDADOS
1. Alto + WebSR Auto, observar frametime/FPS.
2. Alto sem WebSR, comparar nitidez/sombras.
3. Spray em quatro paredes com orientações diferentes e no piso.
4. Morrer e alternar espectadores com Espaço.
5. Inspecionar cada skin Épica/Lendária com Y.
6. Host com vários bots para comparar CPU.
