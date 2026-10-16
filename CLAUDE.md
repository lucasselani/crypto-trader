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
.venv/bin/trader backtest --strategy donchian --symbol BTC/USDT --trades --param entry_n=40
.venv/bin/trader walkforward --strategy donchian --symbol BTC/USDT --train 730 --test 180
.venv/bin/trader run --dry-run            # decisões do agente sem executar
.venv/bin/trader run                      # um ciclo do agente (modo do .env)
```

`--offline` usa só o cache de `data/`. `--timeframe 4h` (antes do subcomando) troca o timeframe.

## Mapa do código (`src/trader/`)

| Módulo | Papel |
|---|---|
| `config.py` | `Settings.from_env()`: lê `.env` (`TRADER_*`) |
| `data.py` | `ccxt`: candles paginados, cache CSV incremental em `data/`. Dados sempre da exchange real, mesmo em testnet |
| `indicators.py` | SMA, EMA, RSI e ATR (Wilder), Donchian |
| `strategies/` | `Strategy` (dataclass frozen): `signals(df) -> (entry, exit)`, `warmup`, `grid` para walk-forward. Registro em `strategies/__init__.py` |
| `risk.py` | `RiskConfig`, `position_size` (risco fixo por trade), `drawdown` |
| `backtest.py` | Motor barra a barra por ativo, `CostModel`, métricas (CAGR, drawdown, Sharpe, Calmar, profit factor, exposição, buy & hold) |
| `walkforward.py` | Otimiza na janela de treino, testa na seguinte, encadeia o OOS |
| `broker.py` | `PaperBroker` (simulado, estado em `state/`) e `ExchangeBroker` (ccxt, testnet/live, stop `STOP_LOSS_LIMIT` na exchange) |
| `agent.py` | `SwingAgent.run_once()`: um ciclo por candle fechado, idempotente por barra |
| `journal.py` | Toda decisão em `state/journal.jsonl` |
| `cli.py` | Subcomandos `fetch`, `backtest`, `compare`, `walkforward`, `run` |

## Como adicionar uma estratégia

1. Subclasse de `Strategy` em `strategies/` como `@dataclass(frozen=True)`, com `name`, `grid`, `warmup` e `signals`.
2. Registrar na tupla de `strategies/__init__.py` (os testes parametrizados por `STRATEGIES` passam a cobri-la).
3. `pytest`, depois `trader compare` e `trader walkforward` em mais de um ativo.

## Convenções

- Código em inglês (identificadores), comentários, docstrings, mensagens e docs em português.
- Testes sem rede: dados sintéticos de `tests/conftest.py::make_candles`; para o agente, substituir `agent.candles` e usar um mercado falso (ver `tests/test_agent.py`).
- Exchange padrão: Binance (decisão e motivos em `docs/exchange-e-api.md`); trocar de exchange deve ser só `TRADER_EXCHANGE`.

## Estado atual e próximos passos

Pré-requisitos prontos: dados, 3 estratégias de exemplo, backtest com custos, walk-forward, paper, testnet/live via ccxt, diário. Ainda **não** existe: backtest de carteira multiativo, filtro de notícias/LLM, agendamento, alertas, interface, controle de imposto. Ver `docs/agente-swing.md`.
