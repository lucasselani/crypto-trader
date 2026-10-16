# Como o agente decide comprar e vender

O "agente" é código determinístico. Ele não pergunta nada a um LLM: lê candles fechados, aplica uma estratégia testada e as regras de risco, executa e registra. O LLM entra depois, nas bordas (filtro de notícias, watchlist, revisão de código), como em [arquitetura.md](arquitetura.md).

## Ciclo

O agente age **uma vez por candle fechado**, mas pode ser chamado quantas vezes quiser: execuções repetidas no mesmo candle não fazem nada. Por isso o agendamento (`deploy/systemd/`) roda de hora em hora e no boot. Se o PC estava desligado no fechamento (21:00 de Brasília no diário), o agente age assim que ligar. Na testnet e no real o stop fica na exchange, então a posição continua protegida com o PC desligado.

Se o agente ficou dias sem rodar, um sinal de saída em qualquer um dos candles perdidos vale (vende). Já a entrada só acontece pelo último candle: não compra sinal velho.

```
para cada ativo do universo (TRADER_SYMBOLS):
  candles fechados → estratégia → sinal de entrada/saída + ATR
  se tem posição:
      stop executado?          → registra "stop"
      sinal de saída?          → vende a mercado, cancela o stop, registra "sell"
      preço subiu?             → sobe o trailing stop (nunca desce), registra "trail"
  se não tem posição:
      sinal de entrada, sem kill switch e abaixo do limite de posições
                               → calcula tamanho pelo risco, compra a mercado, coloca o stop
  toda decisão, inclusive "não fazer nada", vai para state/journal.jsonl
```

Rodar duas vezes no mesmo candle não opera duas vezes (a barra já processada é ignorada).

## Estratégias incluídas

Todas são só compradas (spot), com filtro de regime (preço acima da média de 150/200 barras: não compra em mercado de baixa) e stop inicial de `stop_atr_mult × ATR` com trailing pelo fechamento.

| Nome | Entrada | Saída | Perfil |
|---|---|---|---|
| `donchian` | Fechamento acima da máxima das últimas N barras | Fechamento abaixo da mínima das últimas M barras | Seguidor de tendência (Turtle). Poucos acertos, ganhos grandes |
| `ema_cross` | Média rápida cruza a lenta para cima | Média rápida abaixo da lenta | Tendência, mais lento, menos operações |
| `rsi_pullback` | RSI abaixo do limite dentro de tendência de alta | RSI acima do limite de saída | Compra correção; mais acertos, ganhos menores |

São pontos de partida, não estratégias "boas". O trabalho é rodar o simulador até ter evidência fora da amostra.

## Risco

- **Tamanho de posição por risco fixo:** compra a quantidade que faz o stop custar `TRADER_RISK_PER_TRADE` (1%) do patrimônio, limitada a `TRADER_MAX_POSITION_PCT` (30%) por posição.
- **Máximo de posições abertas:** `TRADER_MAX_OPEN_POSITIONS`.
- **Kill switch:** se o patrimônio cair mais que `TRADER_MAX_DRAWDOWN` (20%) do pico, o agente para de abrir posições. As abertas continuam com seus stops.
- **Stop na exchange** (testnet/live) como `STOP_LOSS_LIMIT` 1% abaixo do gatilho: protege às 3 da manhã de domingo. Em gap maior que 1% a ordem pode não executar; o próximo ciclo do agente vê o sinal de saída e vende a mercado.

Com 1% de risco e stop de 3 ATR, a posição fica em torno de 10% do patrimônio. Por isso os retornos do backtest parecem pequenos perto do buy & hold: o drawdown também é. Compare estratégias por **Calmar** (CAGR / drawdown máximo) e Sharpe, não só por retorno total.

## Como validar (simulador)

1. `trader compare` – todas as estratégias × ativos com parâmetros padrão. Visão rápida.
   `trader portfolio` – a mesma coisa como carteira: os ativos dividem o caixa, com limite de posições e kill switch, como o agente opera de verdade.
2. `trader backtest --strategy X --symbol Y --trades` – detalhe de uma combinação, com a lista de operações.
3. `trader walkforward --strategy X --symbol Y` – otimiza em 2 anos, testa nos 6 meses seguintes, avança e repete. **Só o resultado fora da amostra conta.** Se os parâmetros escolhidos mudam muito de janela para janela ou o OOS é muito pior que o in-sample, a estratégia está sobreajustada.
4. `TRADER_MODE=paper trader run` diário por algumas semanas, comparando o diário com o que o backtest faria no mesmo período.
5. Testnet por algumas semanas para validar a execução real (precisão, taxas, stops).
6. Só então live, com pouco dinheiro.

## Regras do backtest (para não mentir)

- O sinal do fechamento da barra t executa na **abertura de t+1**.
- Taxa de 0,1% por lado e slippage de 0,05% em toda execução (`TRADER_FEE_RATE`, `TRADER_SLIPPAGE`).
- Stop atingido dentro da barra sai no preço do stop; se a barra abriu abaixo (gap), sai na abertura.
- Há um teste (`test_no_lookahead`) que altera o futuro e confere que as operações passadas não mudam.

## Ainda falta (próximas etapas)

- Walk-forward de **carteira** (hoje o walk-forward é por ativo; o backtest de carteira já existe).
- Critério de aprovação de estratégia definido antes da bateria de testes.
- Filtro de notícias/LLM gerando watchlist ou veto de regime.
- Alertas (Telegram) e interface.
- Controle de imposto (vendas mensais, lucro apurado) a partir do diário.
