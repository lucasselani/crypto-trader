# Backtest, replay e simulador

Ordem recomendada:

1. **Backtest** com dados históricos e custos reais (corretagem/taxas, emolumentos, slippage).
2. **Replay** de pregões passados como se fossem ao vivo.
3. **Simulador / testnet ao vivo** por algumas semanas, para ver o comportamento real de execução.
4. Só então dinheiro real, e só um valor que se aceite perder inteiro.

## Ferramentas por etapa

| Etapa | B3 | Cripto |
|---|---|---|
| Dados históricos | MetaTrader 5 via Python (inclusive ticks reais) | `ccxt` / API da exchange (candles e trades tick a tick) |
| Backtest | Strategy Tester do MT5 no modo "ticks reais"; backtester próprio em Python | Backtester próprio em Python/TS |
| Replay | Profit (Nelogica): roda pregões passados como ao vivo, dá para testar dezenas de dias numa tarde | Reproduzir trades gravados no próprio backtester |
| Ao vivo sem risco | Conta demo/simulador da corretora | Testnet da exchange (ex.: Binance), mesma API da real |

## Onde o simulador mente (principalmente no day trade)

- **Execução otimista:** o simulador executa a ordem limitada assim que o preço toca nela; na vida real existe a fila e você pode não ser executado. Ordens a mercado em volatilidade saem piores do que no simulado.
- **Custos:** sem slippage e custos desde o início, uma estratégia de poucos pontos parece lucrativa e não é.
- **Latência:** o bot real tem atraso entre sinal, envio e confirmação; o simulador não.
- **Psicologia:** no simulado ninguém desliga o robô depois de três stops seguidos. No real, isso é o que mais quebra estratégia boa.
- **Overfitting:** estratégia que funciona perfeitamente no passado e morre ao vivo. É o problema clássico de quant amador e o motivo de desconfiar de backtests bonitos em READMEs.

## Swing trade não exige esperar semanas

Dá para validar com anos de dados diários em minutos usando **walk-forward**: otimiza num período, testa no período seguinte, avança a janela e repete. O teste ao vivo de semanas fica só como confirmação final.
