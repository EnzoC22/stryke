STRYKE 4.2.1 // V38.1 BOOT FIX
=================================

Correção crítica
- PRE_VIS das barreiras pré-round era criado antes de THREE.Scene.
- Isso causava: Cannot access 'scene' before initialization.
- O módulo parava e os botões ficavam presos em CARREGANDO...
- Agora PRE_VIS é criado de forma lazy no primeiro preVisTick(), depois do Scene existir.

Launcher
- encerra servidor STRYKE antigo;
- mata qualquer processo LISTENING na porta 8765;
- abre com ?v=38.1 para evitar cache antigo.

Todo o gameplay da V38 foi preservado.
