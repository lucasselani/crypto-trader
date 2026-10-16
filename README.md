# crypto-trader

Agente de swing trade de cripto (B3 depois) e as notas de pesquisa que o originaram (16/10/2026). A parte básica já roda: dados via `ccxt`, estratégias determinísticas, backtest com custos, walk-forward, simulador local, testnet e execução real na Binance.

> Nada aqui é recomendação de investimento. São anotações técnicas e de pesquisa. Regras de imposto mudam: confirme com um contador antes de operar com dinheiro real.

## Resumo em uma página

- **Dá para fazer?** Sim, tecnicamente. Ganhar dinheiro é outra história: o estudo da FGV (Chague, De-Losso e Giovannetti, 2019) com day traders de mini-índice mostrou que, entre os que insistiram por mais de 300 pregões, cerca de 97% perderam dinheiro.
- **O LLM não deve decidir a compra e a venda.** A estratégia fica em código determinístico e backtestado. O LLM trabalha nas bordas: triagem de notícias, montagem da watchlist, geração e revisão de código de estratégia, diário de operações e conferência de imposto.
- **A parte mais valiosa é o filtro** ("separar o trigo do joio"): decidir o que vale olhar hoje antes de qualquer análise. Ver [docs/filtro-noticias.md](docs/filtro-noticias.md).
- **Cripto é o melhor laboratório:** API aberta, testnet gratuita, `ccxt`, sem MetaTrader. Monta e valida o pipeline inteiro em cripto e depois adapta só a camada de execução para a B3.
- **Swing é mais viável que day trade** para um dev sozinho: latência importa pouco, dá para revisar antes de executar e na B3 existe a isenção de R$ 20 mil/mês em vendas de ações.
- **Nenhuma ferramenta pronta da lista resolve.** AutoHedge é só Solana; Fincept é a mais próxima (notícias + agentes + paper trading), mas com foco global.

## Começando

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
cp .env.example .env            # modo paper por padrão, sem chave
.venv/bin/trader fetch          # baixa candles diários desde 2018
.venv/bin/trader compare        # estratégias × ativos
.venv/bin/trader walkforward --strategy donchian --symbol BTC/USDT
.venv/bin/trader run --dry-run  # o que o agente faria hoje
```

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [docs/ferramentas.md](docs/ferramentas.md) | Avaliação das ferramentas de trading e das que ajudam no pipeline (dados, notícias, scraping, engenharia) |
| [docs/exchange-e-api.md](docs/exchange-e-api.md) | Onde abrir conta, qual API usar, testnet e chaves |
| [docs/agente-swing.md](docs/agente-swing.md) | Como o agente decide comprar e vender, risco e roteiro de validação |
| [docs/arquitetura.md](docs/arquitetura.md) | Arquitetura proposta: coleta → filtro → estratégia → backtest → simulação → execução |
| [docs/filtro-noticias.md](docs/filtro-noticias.md) | Como montar a triagem de notícias e a watchlist pré-pregão |
| [docs/simulacao-backtest.md](docs/simulacao-backtest.md) | Backtest, replay, simulador e onde cada um "mente" |
| [docs/cripto.md](docs/cripto.md) | Cripto no Brasil: regulação do BC, APIs, riscos e impostos |
| [docs/b3.md](docs/b3.md) | Ações e futuros na B3: MetaTrader 5, Profit, impostos de day trade e swing |
| [docs/referencias/ferramentas-instagram.md](docs/referencias/ferramentas-instagram.md) | Lista original de ferramentas coletada dos posts do Instagram |

## Próximos passos

1. ~~Escolher a exchange e a API~~: Binance + `ccxt` (ver [docs/exchange-e-api.md](docs/exchange-e-api.md)).
2. ~~Coletor de dados com `ccxt`~~: `trader fetch`, cache em `data/`.
3. ~~Backtester com custos reais e walk-forward~~: `trader backtest` / `trader walkforward`.
4. ~~Backtest de carteira multiativo~~: `trader portfolio`.
5. ~~Paper agendado~~ (`deploy/systemd/`) e ~~execução validada na testnet~~.
6. Rodar muito simulador: critério de aprovação, walk-forward de carteira, vários ativos e timeframes.
7. Semanas de paper e depois testnet antes de qualquer real.
8. Operação: alertas, interface, filtro de notícias e controle de imposto.
