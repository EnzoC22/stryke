# STRYKE V46 — Simulação de partidas 5v5 e telemetria

## Objetivo

Instrumentar **o motor atual do STRYKE**, sem alterar o jogo publicado, para medir
possíveis problemas de movimentação, navegação e balanceamento em Vanta,
Frostline, Kairo e Cargo.

### O que é medido

- Dez bots do próprio motor, cinco atacantes e cinco defensores
- Rodadas reais processadas por `srvTick`, `botThink`, colisão, combate e `bombTick`
- Equipe vencedora e motivo do fim da rodada (eliminação, tempo ou objetivo)
- Primeira entrada de cada equipe nos bombsites A e B
- Distância percorrida por bot e comprimento máximo dos caminhos de navegação
- Eventos de possível travamento: sem deslocamento por pelo menos cinco segundos
  **enquanto existe caminho pendente e não há combate ou ação de bomba**

### Como executar

Abra **Actions → V46 Tactical Bot Simulation → Run workflow**.

Localmente, com Node.js 22 e Playwright Chromium instalados:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
# em outro terminal:
STRYKE_TEST_URL=http://127.0.0.1:8765/ V46_ROUNDS=2 node tools/v46_bot_match_simulation.mjs
```

O resultado é gravado em `reports/v46-bot-simulation.json`. No GitHub Actions,
o arquivo fica disponível como artifact por 14 dias.

### Segurança e limites

- A instrumentação é **injetada somente na resposta HTTP local do teste**,
  nunca gravada em `index.html`. Nenhum método interno é exposto pelo jogo
  publicado; o anticheat não é desabilitado.
- O simulador usa um **relógio virtual de testes**, não representa latência real
  ou taxa de quadros do jogador. Os bots usam as rotinas existentes de IA, física
  e resolução de rodadas do motor.
- Os primeiros resultados são uma **amostra pequena para diagnóstico**, não
  uma estimativa estatisticamente válida de win rate T/CT ou prova de
  balanceamento competitivo.
- O relatório de travamentos contém **suspeitas a revisar**; segurar posição
  defensiva pode ser correto e a heurística não identifica todos os bugs.
- Execute os testes V45, V44.1 e V44.2 quando alterar geometria, combate,
  anticheat ou lógica de rede. Não ajuste spawns/covers automaticamente apenas
  porque uma amostra apresentou mais vitórias de um time.

## Critério de evolução

Primeiro coletar resultados repetidos com múltiplas sementes; depois revisar
as rotas e os casos concretos de travamento em Chromium antes de propor
pequenos patches de geometria. Publicar somente após regressões aprovadas.
