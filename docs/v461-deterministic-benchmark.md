# STRYKE V46.1 — Reprodutibilidade e inteligência competitiva

O benchmark executa o **motor real do jogo** no Chromium com bots 5x5,
sem modificar `index.html`, segurança, armas, mapas, assets ou IA em produção.

## Experimento

- **100 rodadas independentes por mapa**, total de 400 rodadas.
- Vanta, Frostline, Kairo e Cargo em jobs separados.
- Sempre os mesmos 10 bots, 5 T e 5 CT; difficulty 1.
- Cada rodada reinicia entidades, economia, score, bomba e estado autoritativo
  do servidor de teste, antes de iniciar a física, IA e combate reais.
- Tempo virtual fixo a passos de 100 ms, com o loop de renderização e
  relógio de background pausados **apenas na resposta de teste**.
- RNG congruente com sementes explícitas; o Math.random original
  é restaurado depois de cada chamada síncrona ao motor.
- A mesma semente é executada duas vezes; resultados diferentes **falham**
  a validação e impedem aceitar um benchmark não reprodutível.

**Nota metodológica:** são 100 *rodadas* independentes por mapa, **não**
100 partidas completas com economia e alternância de lados. O experimento
serve para comparar comportamento e trajetos dos bots com condições iniciais
controladas; não estima vitória de jogadores humanos.

## Telemetria

- Vitórias por lado, duração média, 95% CI Wilson da taxa observada dos bots
- Primeiro contato com adversário e primeira morte: equipe, arma, posição, tempo
- Heatmap agregado das posições das primeiras mortes (quadrantes de 10 unidades)
- Primeira chegada de T e CT aos bombsites A e B
- Distância percorrida por bot, número de alvos adquiridos, decisões de recalcular
  rota, tamanho máximo de rota e bloqueios por cinco segundos com caminho pendente
- Relatório JSON reproduzível com hash do commit e sementes

**Limitações:** reação dos bots, comportamento de rede entre dois jogadores
e taxa real de FPS não são representados por estatísticas de bots sob relógio
virtual. Apenas eventos observados são contabilizados; um gargalo com pouca
amostra não comprova viés e não justifica editar automaticamente mapas.

## Executar

No GitHub: **Actions → V46.1 Deterministic Benchmark → Run workflow**.
Padrão manual: 100 rodadas/mapa. Cada alteração dessa suíte em `main`
aciona apenas duas rodadas/mapa como smoke; na branch de desenvolvimento
`v461-deterministic-benchmark` executa o ensaio completo de 100.

Localmente:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
# outro terminal (instale Playwright e Chromium antes):
STRYKE_TEST_URL=http://127.0.0.1:8765/ V461_MAP=cargo V461_ROUNDS=100 \
  node tools/v461_deterministic_benchmark.mjs

# Depois de executar todos os quatro mapas:
python3 tools/v461_report.py --directory reports --output reports/v461-summary.json
```

O arquivo `reports/v461-<mapa>.json` contém os eventos por rodada.
A job de consolidação publica o JSON combinado e resumo Markdown nos
artifacts/Job Summary do workflow.

## Comparação de versões

As execuções usam as mesmas sementes, versão de cenário, dificuldade e
intervalos de tempo. Um baseline cacheado por branch permite mostrar as
diferenças de percentual T, duração média e travamentos na próxima execução.
A comparação só é calculada quando **sementes e número de rodadas coincidem**.
O cache pode não existir ou expirar: nesse caso a suíte segue funcionando e
declara a ausência de baseline sem inventar diferenças.

Nunca altere a geometria ou desative mecanismos anticheat apenas para
melhorar uma métrica. Use o relatório como hipótese e repita os testes
Chromium de mapas, mobile, multiplayer e combate após patches de gameplay.
