STRYKE 3.7.1 // V33 MAP BOUNDS FIX
===================================

Base: V32 Structural Map Rework.

CORREÇÃO PRINCIPAL
------------------
A V31 ainda adicionava alguns covers por coordenadas absolutas depois de o layout ter sido alterado.
Essas peças podiam atravessar paredes/void ou ficar visualmente fora da área útil.

Na V33:
- o V31_COVER_PASS foi removido completamente;
- covers novos usam caracteres do próprio grid:
  h = cover retangular horizontal;
  i = cover retangular vertical;
- cada cover ocupa apenas 62% x 26% da célula, portanto permanece dentro do espaço jogável;
- Vanta, Frostline e Kairo receberam covers de bombsite/Mid diretamente no layout;
- o envelope geral dos mapas foi mantido porque o problema não exigia aumentar o mapa inteiro.

PRESERVADO
----------
- armas e braços originais da V30;
- WebSR;
- otimizações V29;
- sprays;
- espectador;
- recoil/dano/movimento/economia;
- spawns e identidade dos três mapas.
