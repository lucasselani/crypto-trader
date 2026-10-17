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
