STRYKE 4.3 // V39 ANTI-CHEAT HARDENING
=========================================

BASE
- V38.2 Cargo Only.
- Gameplay, mapa Cargo, armas/braços originais, WebSR, sprays e pré-round preservados.

O QUE FOI FEITO
----------------
1. Console/debug
- localhost não ativa mais DEBUG.
- window.__T e a API interna de testes foram removidos da build distribuída.
- F12, Ctrl+Shift+I/J/C, Ctrl+U e menu de contexto são bloqueados como deterrência.
- Isso NÃO é a fronteira de segurança: DevTools não pode ser tornado impossível por uma página web.

2. Movimento
- Speedhack PvP acima da faixa legítima é descartado pelo host.
- Noclip/fly/teleporte continuam validados e ficaram mais estritos.
- Pré-round continua clampado no servidor.

3. Tiro/hit
- O cliente agora envia SHOT antes de HIT.
- O host cria um ticket por disparo.
- HIT sem disparo recente da mesma arma é rejeitado.
- O raio declarado pelo tiro precisa passar pela zona corporal alegada.
- Headshot falso via console é rejeitado quando o raio não cruza a cabeça.
- Origem, direção, alcance, arma possuída e cadência continuam validados.
- Dano máximo agora inclui falloff por distância.

4. Munição
- O host mantém um espelho de mag/reserva para impedir munição infinita/no-reload.
- Recarga é inferida pelo intervalo temporal legítimo; shotguns usam shellTime.

5. Rede
- Tipos de mensagem têm whitelist.
- Rate limits existentes continuam ativos.
- Granadas sem inventário ou vetores impossíveis geram anomalia.

6. Enforcement
- Ações impossíveis severas valem mais pontos.
- Cliente remoto com score de anomalia muito alto é removido automaticamente.

LIMITAÇÃO IMPORTANTE
--------------------
STRYKE ainda usa host P2P. O host é a autoridade da partida e possui o processo que contém o estado autoritativo.
Nenhum JavaScript executado nesse mesmo computador consegue tornar um host malicioso criptograficamente confiável.
Para ranked público sério, o próximo passo obrigatório é mover simulação/validação para servidor dedicado.
