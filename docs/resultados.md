# Resultados das simulações

Registro das baterias para decidir com dados. Todas são walk-forward (só períodos fora da amostra, ~2020 a 10/2026), nas 10 moedas do universo, com taxa de 0,1% e slippage de 0,05%. Viés de sobrevivência: as moedas são as que existem hoje. **Espere quedas maiores no futuro do que as daqui.**

## 16/10/2026 – bateria inicial (risco de 1%, até 3 posições)

| Estratégia | Gráfico | Ganho/ano | Pior queda | Calmar | Aprovada |
|---|---|---|---|---|---|
| donchian | diário | 16,6% | −12,1% | 1,38 | ✅ |
| ema_cross | 4h | 24,9% | −23,5% | 1,06 | ✅ |
| donchian | 4h | 24,1% | −30,8% | 0,78 | ❌ |
| ema_cross | diário | 7,8% | −10,9% | 0,71 | ❌ |
| rsi_pullback | diário / 4h | 0,3% / −3,0% | −5,3% / −34,6% | ~0 | ❌ |

Comprar e segurar as 10 moedas no mesmo período: ~1.400%, com queda de até −85%.

## 17/10/2026 – variações de risco e de nº de posições

| Configuração | Ganho/ano | Pior queda | Calmar | Sharpe |
|---|---|---|---|---|
| donchian diário, 1%, 3 posições | 16,6% | −12,1% | 1,38 | 1,29 |
| donchian diário, 2%, 3 posições | 32,1% | −22,5% | 1,43 | 1,32 |
| donchian diário, 1%, 5 posições | 23,0% | −25,5% | 0,90 | 1,36 |
| donchian diário, 2%, 5 posições | 36,7% | −41,9% | 0,88 | 1,27 |
| ema_cross 4h, 1%, 3 posições | 24,9% | −23,5% | 1,06 | 1,33 |
| ema_cross 4h, 1%, 5 posições | 45,7% | −28,5% | 1,60 | 1,62 |
| ema_cross 4h, 2%, 3 posições | 39,0% | −40,5% | 0,96 | 1,23 |
| ema_cross 4h, 2%, 5 posições | 79,9% | −44,8% | 1,78 | 1,70 |
| **metade em cada (1%, 3 posições)** | 21,2% | −15,8% | 1,34 | **1,69** |
| metade em cada (1%, 5 posições) | 37,0% | −23,3% | 1,59 | 1,86 |
| metade em cada (2%, 3 posições) | 35,8% | −28,5% | 1,26 | 1,57 |
| metade em cada (2%, 5 posições) | 65,9% | −40,7% | 1,62 | 1,80 |

Leituras:

- **Risco 2% em vez de 1%** dobra o ganho e a queda juntos; a qualidade (Calmar) quase não muda. É uma escolha de quanto se aguenta ver cair, não de estratégia melhor.
- **5 posições em vez de 3** piora a donchian diária (cripto cai junto: mais moedas abertas = queda maior) e melhora a ema_cross 4h. Os números do 4h oscilam muito entre configurações vizinhas, sinal de que são sensíveis; não confiar nos retornos de 4 dígitos.
- **Combinar as duas** (metade do capital em cada) funciona: a correlação entre elas é ~0,1 (ganham em momentos diferentes), e o Sharpe da combinação é maior que o de qualquer uma sozinha.
- Decisão atual: paper segue com donchian diária, 1%, 3 posições (funciona com o PC desligado à noite). A combinação com 4h fica para quando houver um servidor ligado 24h.

Como reproduzir: `trader battery --timeframes 1d --strategies donchian --risk 0.01 0.02 --max-positions 3 5` (idem para `4h ema_cross`); as curvas ficam em `data/results/equity_*.csv`.

## 17/10/2026 – média mensal vs. hold (01/2020 a 10/2026, 82 meses)

Média mensal composta (a taxa fixa por mês que leva ao mesmo resultado final), em USDT, antes de imposto. Risco de 1% e 3 posições, salvo indicação.

| | Média/mês | Meses no positivo | Pior mês | Pior queda | R$ 10 mil viram |
|---|---|---|---|---|---|
| donchian diário (1%) | +1,28% | 43% | −4,7% | −12% | 28.442 |
| donchian diário (2%) | +2,33% | 43% | −9,1% | −23% | 66.303 |
| ema_cross diário | +0,62% | 35% | −2,8% | −11% | 16.660 |
| rsi_pullback diário | +0,02% | 26% | −3,6% | −5% | 10.185 |
| donchian 4h | +1,80% | 38% | −5,0% | −31% | 43.271 |
| ema_cross 4h | +1,86% | 54% | −4,6% | −24% | 45.308 |
| rsi_pullback 4h | −0,25% | 29% | −5,4% | −35% | 8.131 |
| metade donchian diário + ema_cross 4h | +1,60% | 55% | −3,6% | −16% | 36.875 |
| hold só BTC | +2,98% | 56% | −37,3% | −77% | 110.980 |
| hold 10 moedas | +3,56% | 55% | −33,4% | −85% | 175.818 |

"Meses no positivo" baixo nas estratégias diárias é porque muitos meses ficam em caixa (0%). Desde 2024 a donchian diária sozinha ficou perto de 0%/mês; a combinação, perto de 0,8%/mês; o hold de BTC, perto de 2%/mês.
