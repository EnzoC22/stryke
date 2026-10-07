STRYKE 4.1 // V37 OFFICIAL SPRAYS
=================================

Base: V36 Reference Maps.

SPRAYS OFICIAIS
----------------
1. RULADO PELO VORCARO
2. TÁTICO 67

CONTROLE
--------
- Toque T: usa imediatamente o spray equipado.
- Segure T (~330 ms): abre o seletor com as duas artes.
- Enquanto segura T: mova o mouse para a esquerda/direita para selecionar.
- Solte T: equipa e aplica o spray escolhido.

IMPLEMENTAÇÃO
-------------
- As duas imagens fornecidas pelo usuário são assets locais PNG transparentes 1024x1024.
- Texturas são pré-carregadas, SRGB, mipmapped e com anisotropia limitada a 8x.
- Multiplayer transmite apenas índice 0/1; servidor valida o intervalo.
- Perfis antigos migram o antigo spray 67 para TÁTICO 67.
- Ambos ficam liberados para todos os perfis.
- Limite existente de 4 sprays por jogador / 48 globais preservado.
- Colocação em paredes/piso, orientação e anti-z-fighting preservados.

PRESERVADO
----------
Mapas V36, Cargo, pré-round, armas/braços originais, WebSR, recoil, dano, economia, otimizações e espectador.
