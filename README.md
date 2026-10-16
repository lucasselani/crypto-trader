# crypto-trader

Notas de pesquisa para um dia montar agentes de trading (cripto primeiro, B3 depois). Ainda não tem código: este repositório guarda o que foi levantado em 16/10/2026 para retomar o assunto sem começar do zero.

> Nada aqui é recomendação de investimento. São anotações técnicas e de pesquisa. Regras de imposto mudam: confirme com um contador antes de operar com dinheiro real.

## Resumo em uma página

- **Dá para fazer?** Sim, tecnicamente. Ganhar dinheiro é outra história: o estudo da FGV (Chague, De-Losso e Giovannetti, 2019) com day traders de mini-índice mostrou que, entre os que insistiram por mais de 300 pregões, cerca de 97% perderam dinheiro.
- **O LLM não deve decidir a compra e a venda.** A estratégia fica em código determinístico e backtestado. O LLM trabalha nas bordas: triagem de notícias, montagem da watchlist, geração e revisão de código de estratégia, diário de operações e conferência de imposto.
- **A parte mais valiosa é o filtro** ("separar o trigo do joio"): decidir o que vale olhar hoje antes de qualquer análise. Ver [docs/filtro-noticias.md](docs/filtro-noticias.md).
- **Cripto é o melhor laboratório:** API aberta, testnet gratuita, `ccxt`, sem MetaTrader. Monta e valida o pipeline inteiro em cripto e depois adapta só a camada de execução para a B3.
- **Swing é mais viável que day trade** para um dev sozinho: latência importa pouco, dá para revisar antes de executar e na B3 existe a isenção de R$ 20 mil/mês em vendas de ações.
- **Nenhuma ferramenta pronta da lista resolve.** AutoHedge é só Solana; Fincept é a mais próxima (notícias + agentes + paper trading), mas com foco global.

## Documentos

| Arquivo | Conteúdo |
|---|---|
| [docs/ferramentas.md](docs/ferramentas.md) | Avaliação das ferramentas de trading e das que ajudam no pipeline (dados, notícias, scraping, engenharia) |
| [docs/arquitetura.md](docs/arquitetura.md) | Arquitetura proposta: coleta → filtro → estratégia → backtest → simulação → execução |
| [docs/filtro-noticias.md](docs/filtro-noticias.md) | Como montar a triagem de notícias e a watchlist pré-pregão |
| [docs/simulacao-backtest.md](docs/simulacao-backtest.md) | Backtest, replay, simulador e onde cada um "mente" |
| [docs/cripto.md](docs/cripto.md) | Cripto no Brasil: regulação do BC, APIs, riscos e impostos |
| [docs/b3.md](docs/b3.md) | Ações e futuros na B3: MetaTrader 5, Profit, impostos de day trade e swing |
| [docs/referencias/ferramentas-instagram.md](docs/referencias/ferramentas-instagram.md) | Lista original de ferramentas coletada dos posts do Instagram |

## Próximos passos (quando voltar)

1. Escolher a exchange (brasileira para aproveitar a isenção, ou estrangeira pela liquidez) e criar a chave de testnet.
2. Coletor de dados com `ccxt` salvando candles e trades em arquivos/banco.
3. Primeiro protótipo do filtro de notícias gerando uma watchlist diária (sem executar nada).
4. Backtester com custos reais (taxas, slippage) e walk-forward.
5. Semanas de paper trading/testnet antes de qualquer real.
