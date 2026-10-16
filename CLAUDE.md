# CLAUDE.md

Agente de **swing trade de cripto** (spot, só comprado) em Python. Cripto é o laboratório; a B3 vem depois reaproveitando tudo menos a execução. Notas de pesquisa em `docs/` (português).

## Regras invioláveis

- **O LLM nunca decide compra ou venda.** A decisão é sempre da estratégia determinística em `src/trader/strategies/` + regras de `risk.py`. LLM só nas bordas (notícias, watchlist, revisão de código, diário). Ver `docs/arquitetura.md`.
- **Sem olhar o futuro:** sinal calculado no fechamento da barra t executa na abertura de t+1. Indicadores só podem usar dados até t (`donchian_*` excluem a barra corrente). Toda estratégia nova tem que passar em `tests/test_backtest.py::test_no_lookahead`.
- **Custos sempre ligados** em backtest e paper (taxa 0,1%/lado, slippage 0,05%). Nunca comparar resultados sem custos.
- **Métrica que vale é a fora da amostra** (`trader walkforward`). Backtest otimizado no período inteiro não é evidência.
- **Live exige dupla confirmação:** `TRADER_MODE=live` **e** `TRADER_ALLOW_LIVE=yes`. Não alterar `Settings.check_live_allowed` nem rodar `trader run` em modo live sem pedido explícito do usuário.
- Nunca commitar `.env`, `state/` ou `data/`. Nunca sugerir chave de API com permissão de saque.
- Nada aqui é recomendação de investimento; regras de imposto (`docs/cripto.md`) precisam de confirmação com contador.

## Comandos

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # setup
cp .env.example .env                                         # config (paper por padrão)

.venv/bin/pytest -q                       # testes (sem rede)
.venv/bin/ruff check src tests            # lint

.venv/bin/trader fetch --since 2018-01-01                              # baixa/atualiza candles em data/
.venv/bin/trader compare --offline                                     # estratégias × ativos
.venv/bin/trader portfolio --offline                                   # carteira com caixa compartilhado (como o agente)
.venv/bin/trader backtest --strategy donchian --symbol BTC/USDT --trades --param entry_n=40
.venv/bin/trader walkforward --strategy donchian --symbols BTC/USDT ETH/USDT --train-days 730 --test-days 180
.venv/bin/trader battery --offline                                     # walk-forward estratégias × timeframes no universo; CSV em data/results/
.venv/bin/trader run --dry-run            # decisões do agente sem executar
.venv/bin/trader run                      # um ciclo do agente (modo do .env)
```

`--offline` usa só o cache de `data/`. `--timeframe 4h` (antes do subcomando) troca o timeframe.

## Mapa do código (`src/trader/`)

| Módulo | Papel |
|---|---|
| `config.py` | `Settings.from_env()`: lê `.env` (`TRADER_*`). `symbols` = o que o agente opera; `universe` = moedas da bateria de simulações |
| `data.py` | `ccxt`: candles paginados, cache CSV incremental em `data/`. Dados sempre da exchange real, mesmo em testnet |
| `indicators.py` | SMA, EMA, RSI e ATR (Wilder), Donchian |
| `strategies/` | `Strategy` (dataclass frozen): `signals(df) -> (entry, exit)`, `warmup`, `grid` para walk-forward. Registro em `strategies/__init__.py` |
| `risk.py` | `RiskConfig`, `position_size` (risco fixo por trade), `drawdown` |
| `backtest.py` | `run_portfolio`: motor barra a barra multiativo com caixa compartilhado, limite de posições e kill switch, igual ao agente. `run_backtest` é o caso de um ativo sem kill switch. `CostModel` e métricas (CAGR, drawdown, Sharpe, Calmar, profit factor, exposição, buy & hold) |
| `walkforward.py` | Otimiza na janela de treino, testa na seguinte, encadeia o OOS; aceita ativo ou carteira. `Criteria`/`evaluate`: régua de aprovação |
| `broker.py` | `PaperBroker` (simulado, estado em `state/`) e `ExchangeBroker` (ccxt, testnet/live, stop `STOP_LOSS_LIMIT` na exchange) |
| `agent.py` | `SwingAgent.run_once()`: um ciclo por candle fechado, idempotente por barra. Se ficou dias sem rodar, sai por sinal de saída em qualquer barra perdida, mas só entra pelo último candle |
| `journal.py` | Toda decisão em `state/journal.jsonl` |
| `cli.py` | Subcomandos `fetch`, `backtest`, `compare`, `walkforward`, `run` |

## Agendamento

Timer do systemd do usuário em `deploy/systemd/` (instalado em `~/.config/systemd/user/`): roda `trader run` de hora em hora e no boot, com `Persistent=true`, porque o PC costuma estar desligado no fechamento do diário (21:00 de Brasília). O modo fica fixo no `.service` (`TRADER_MODE=paper`), não no `.env`. Logs: `journalctl --user -u crypto-trader -f`. Depois de editar as units: copiar para `~/.config/systemd/user/` e `systemctl --user daemon-reload`.

## Como adicionar uma estratégia

1. Subclasse de `Strategy` em `strategies/` como `@dataclass(frozen=True)`, com `name`, `grid`, `warmup` e `signals`.
2. Registrar na tupla de `strategies/__init__.py` (os testes parametrizados por `STRATEGIES` passam a cobri-la).
3. `pytest`, depois `trader compare` e `trader walkforward` em mais de um ativo.

## Convenções

- Código em inglês (identificadores), comentários, docstrings, mensagens e docs em português.
- Testes sem rede: dados sintéticos de `tests/conftest.py::make_candles`; para o agente, substituir `agent.candles` e usar um mercado falso (ver `tests/test_agent.py`).
- O usuário não é da área de finanças: explicar métricas e conceitos em linguagem simples, com exemplo numérico. Decisões guiadas por dados: começar com uma régua simples e ajustar medindo.
- Exchange padrão: Binance (decisão e motivos em `docs/exchange-e-api.md`); trocar de exchange deve ser só `TRADER_EXCHANGE`.

## Estado atual e próximos passos

Pré-requisitos prontos: dados, 3 estratégias de exemplo, backtest de ativo e de carteira com custos, walk-forward de ativo e de carteira, bateria de simulações com critérios, paper agendado, execução na testnet validada em 16/10/2026 (compra, stop na exchange, mover stop, cancelar, venda), diário. Ainda **não** existe: filtro de notícias/LLM, alertas, interface, controle de imposto. Imposto e exchange nacional vs. global ficaram para depois, por decisão do usuário.

Resultado da bateria de 16/10/2026 (walk-forward, 10 moedas, até 3 posições, risco de 1%): aprovadas `donchian` no diário (CAGR 16,6%, queda máxima −12%, Calmar 1,38) e `ema_cross` no 4h (CAGR 24,9%, queda −23,5%, Calmar 1,06). `rsi_pullback` reprovou nos dois timeframes. O paper roda `donchian` diário nas 10 moedas. Ver `docs/agente-swing.md`.
