# STRYKE · Ciclo de melhoria automatizado

Este repositório executa `.github/workflows/stryke-autopilot.yml` a cada **20 minutos**, por cron GitHub Actions (`7,27,47 * * * *`). O GitHub pode atrasar ou pular uma execução agendada; o relógio não é garantido.

## O que faz

1. Inspeciona o `index.html` e as **últimas definições ativas** de Vanta, Frostline, Kairo e Cargo (definições antigas no mesmo arquivo são sobrescritas).
2. Mede, por heurística rápida de grade, acesso T/CT aos bombsites e quantidade de spawns, e seleciona **quatro prioridades** — problemas graves têm precedência sobre hipóteses de melhoria. Os números da grade **não substituem** as rotas e colisões reais do Chromium.
3. Salva o ranking no resumo da execução e no arquivo `stryke-cycle-latest.json` (artifacts), retido por sete dias.
4. Só aplica automaticamente **correções já conhecidas e com correspondência exata**: fallback de bot que atravessaria paredes, prazo da bomba quando falta proteção, detecção incorreta de desktop touchscreen.
5. Antes de qualquer commit automático, exige: sintaxe de todos os blocos JavaScript, contrato dos quatro mapas, testes unitários da bomba, mapas e HUD mobile no Chromium e dois navegadores conectados via WebRTC (partida 5v5, combate e objetivos).
6. Se **todos** os testes passam, publica somente `index.html`, aciona o deploy GitHub Pages e as suítes completas. Se **qualquer** teste falha ou não há mudança segura, **não há publicação**.

## Limites de autonomia

- O workflow **não é o ChatGPT rodando continuamente** e **não cria quatro patches novos por rodada**. O ranking é derivado de regras e de um catálogo rotativo de hipóteses. Gerar código novo por IA exigiria modelo externo/credenciais e novas garantias de segurança.
- Nunca altera automaticamente a geometria dos mapas, spawns, covers, armas, anti-cheat ou assets 3D por simples ranking. Essas mudanças devem ser validada em branch e testadas antes do merge.
- Logs e recomendações: **Actions → STRYKE Autonomous Improvement Cycle**.
- A execução manual está disponível em **Run workflow**. Para interromper os ciclos, desative o workflow no GitHub Actions.
- Futuras mudanças reais de arquitetura, navegação tática, gunplay e performance necessitam testes humanos em desktops e celulares físicos, além de automação.

## Mapas V45

Os cinco terroristas de Cargo nascem na base sul definida por `T`. A/B são objetivos laterais intermediários conectados por flancos, com covers; os CTs continuam no norte. As quatro arenas possuem barreiras de freeze do próprio time próximas dos spawns originais. Os testes reais de mapas também cobrem caminhos A/B, colisões e linhas de visão no spawn.
