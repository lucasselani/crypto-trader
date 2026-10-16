# Arquitetura proposta

Ideia geral: um pipeline no estilo do Darkrunner (coleta → agentes de triagem → relatório), em que o LLM **nunca** dá a ordem de compra ou venda. Ele filtra, resume e ajuda a escrever e revisar código. Quem decide é uma estratégia determinística e testada.

```
┌────────────┐   ┌──────────────────┐   ┌───────────────┐   ┌──────────┐   ┌────────────┐   ┌──────────┐
│  Coleta    │──▶│ Filtro (LLM +    │──▶│  Estratégia   │──▶│ Risco    │──▶│ Execução   │──▶│ Diário / │
│ dados +    │   │ quantitativo)    │   │ determinística│   │ (stops,  │   │ (testnet → │   │ impostos │
│ notícias   │   │ → watchlist      │   │ backtestada   │   │ limites) │   │  real)     │   │          │
└────────────┘   └──────────────────┘   └───────────────┘   └──────────┘   └────────────┘   └──────────┘
```

## Camadas

1. **Coleta**
   - Cripto: `ccxt` (candles, trades, livro de ofertas) + WebSocket da exchange.
   - B3: MetaTrader 5 via Python (ticks reais), em VM/VPS Windows.
   - Notícias: fontes oficiais primeiro, imprensa depois (ver [filtro-noticias.md](filtro-noticias.md)).
   - Tudo salvo em arquivos/banco para reprocessar e backtestar.

2. **Filtro → watchlist**
   - Parte quantitativa: gap, volume relativo, volatilidade (ATR).
   - Parte LLM: classifica relevância, impacto provável, se é novidade, qual ativo afeta.
   - Saída: lista ranqueada do que vale olhar, com uma linha de motivo cada.

3. **Estratégia**
   - Código determinístico, versionado e com testes (TDD).
   - O LLM pode gerar variações e revisar código, mas a validação é sempre pelo backtest.

4. **Risco**
   - Tamanho de posição, stop obrigatório, limite de perda diário/semanal, "kill switch".
   - Em cripto é crítico: mercado 24/7, o bot precisa se proteger sozinho às 3 da manhã de domingo.

5. **Execução**
   - Mesma interface para testnet/simulador e real; troca só configuração (URL e chave).
   - Cripto primeiro; a camada de execução da B3 vem depois, reaproveitando o resto.

6. **Diário e impostos**
   - Log de cada operação com motivo, sinal e resultado.
   - Separar day trade de swing desde o início (bases de imposto separadas).
   - Controle de vendas mensais para os limites de isenção (R$ 20 mil em ações na B3; R$ 35 mil em cripto em exchange brasileira, se ainda valer).

## Stack provável

- TypeScript ou Python. Python tem o pacote `MetaTrader5` e o ecossistema quant (pandas, vectorbt etc.); `ccxt` existe nas duas.
- Agentes: mesma abordagem do Darkrunner.
- Rodando em nuvem; para a B3, uma VPS Windows por causa do MT5.
