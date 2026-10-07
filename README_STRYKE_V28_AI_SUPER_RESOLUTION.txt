STRYKE 3.4 // V28 AI SUPER RESOLUTION
========================================

BASE
----
STRYKE 3.3 V27 VISUAL POLISH 3 MAPS.
Nenhuma mecânica, geometria competitiva, arma, recoil, hit-reg, bot, economia, input ou protocolo multiplayer foi alterado.
PROTO permanece 19 porque esta versão é visual-only.

O QUE FOI ADICIONADO
--------------------
- WebSR 0.0.16 via jsDelivr / WebGPU.
- Rede em tempo real: anime4k/cnn-2x-s (2x).
- Segundo canvas #gameSR, usado só para apresentação do frame final.
- O canvas original #game continua sendo o único canvas de Three.js e continua recebendo toda a renderização da V27.
- HUD permanece DOM/native-resolution e não passa pela IA, preservando nitidez e input.
- Super Resolução por IA nas Configurações: Desligada / WebSR Auto / WebSR Qualidade.

PIPELINE
--------
V27: scene -> viewmodel -> pós-processamento -> canvas#game
V28: scene -> viewmodel -> pós-processamento -> canvas#game -> WebSR/WebGPU 2x -> canvas#gameSR

OTIMIZAÇÃO / FPS
-----------------
- Auto começa com ~0.50x de pixel ratio interno e reconstrói 2x.
- Se houver folga, sobe gradualmente até 0.65x.
- Se a inferência de IA ou frame-time ficar pesado, reduz até 0.45x.
- Se mesmo no mínimo a IA continuar lenta por várias janelas, o jogo desliga o WebSR automaticamente e restaura o render nativo.
- Apenas uma inferência fica em voo; frames são descartados enquanto a anterior não terminou, evitando fila/latência acumulada.
- Aba oculta não executa upscale.
- Falha de CDN, pesos ou WebGPU nunca impede o jogo: fallback automático para V27 nativa.

REQUISITOS
----------
- Chrome/Edge moderno com WebGPU para o modo IA.
- Internet na primeira carga para @websr/websr e pesos via jsDelivr. O navegador pode cachear os arquivos depois.
- Sem WebGPU: o jogo funciona normalmente, apenas sem super resolução.

NOTA
----
WebSR ainda é um projeto novo/experimental. Por isso a integração é isolada e possui fallback agressivo, em vez de tornar o jogo dependente da biblioteca.
