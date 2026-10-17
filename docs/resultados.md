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
| **metade em cada (1%, 3 posições)** | 21,2% | −15,8% | 1,34 | **1,49** |
| metade em cada (1%, 5 posições) | 37,0% | −23,3% | 1,59 | 1,68 |
| metade em cada (2%, 3 posições) | 35,8% | −28,5% | 1,26 | 1,42 |
| metade em cada (2%, 5 posições) | 65,9% | −40,7% | 1,62 | 1,60 |

Leituras:

- **Risco 2% em vez de 1%** dobra o ganho e a queda juntos; a qualidade (Calmar) quase não muda. É uma escolha de quanto se aguenta ver cair, não de estratégia melhor.
- **5 posições em vez de 3** piora a donchian diária (cripto cai junto: mais moedas abertas = queda maior) e melhora a ema_cross 4h. Os números do 4h oscilam muito entre configurações vizinhas, sinal de que são sensíveis; não confiar nos retornos de 4 dígitos.
- **Combinar as duas** (metade do capital em cada) ajuda, mas menos do que parecia: a correlação semanal entre elas é ~0,5. O Sharpe da combinação (1,49) é um pouco maior que o de cada uma (1,29 e 1,33) e a queda máxima fica no meio.
- *Correção (17/10):* a primeira versão desta tabela dizia correlação ~0,1 e Sharpe 1,69 para a combinação. Era um erro de alinhamento ao misturar curva diária com curva de 4h (a diária parecia parada entre um dia e outro). Sharpe e correlação de combinações agora são medidos em retornos diários/semanais.
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

## 17/10/2026 – três estratégias novas e o período recente

Novas: `sma_trend` (média simples, estilo Meb Faber), `roc_momentum` (momentum em série temporal) e `keltner` (rompimento de faixa de volatilidade). Aprovada só a `keltner` no diário (17,3% ao ano, queda máxima −14%, Calmar 1,22). As outras ficaram com Calmar entre 0,45 e 0,89.

Média mensal no período todo vs. desde 2024 (risco 1%, 3 posições):

| | Mês 2020–26 | Mês desde 2024 | Pior queda | Pior queda desde 2024 |
|---|---|---|---|---|
| hold só BTC | +3,00% | +1,85% | −77% | −53% |
| ema_cross 4h | +1,87% | +1,47% | −24% | −21% |
| donchian 4h | +1,82% | +1,05% | −31% | −25% |
| keltner 4h | +1,99% | +1,03% | −30% | −27% |
| sma_trend 4h | +2,37% | +1,01% | −36% | −24% |
| roc_momentum 4h | +1,61% | +0,91% | −31% | −24% |
| metade donchian 1d + ema_cross 4h | +1,62% | +0,84% | −16% | −14% |
| roc_momentum diário | +0,58% | +0,72% | −16% | −10% |
| keltner diário | +1,34% | +0,64% | −14% | −13% |
| ema_cross diário | +0,63% | +0,55% | −11% | −11% |
| sma_trend diário | +1,24% | +0,44% | −22% | −8% |
| hold 10 moedas | +3,59% | +0,21% | −85% | −72% |
| donchian diário | +1,29% | +0,06% | −12% | −11% |
| rsi_pullback diário / 4h | +0,02% / −0,25% | +0,06% / −0,59% | −5% / −35% | |

Leituras: desde 2024 o 4h foi melhor que o diário em todas as estratégias; nenhuma diária passou de 0,75%/mês. As estratégias de rompimento diárias (donchian e keltner) são muito parecidas (correlação semanal 0,82); as outras ficam entre 0,4 e 0,6.

Decisão: não sair da renda fixa agora; colher dados. Congeladas 10 contas de paper (5 estratégias × diário e 4h) em `config/paper_accounts.json`, para medir daqui a alguns meses com `trader forward` (simulação desde o congelamento) e `trader status` (o que o paper fez).

## 17/10/2026 – resultado por fase do mercado (`trader regimes`)

Fase de cada dia pela variação do BTC nos 90 dias anteriores (só passado): alta ≥ +20%, baixa ≤ −20%, lateral no meio. Ideia adaptada do Vibe-Trading.

Mistura de fases: antes de 2024, 38% alta / 42% lateral / 20% baixa; desde 2024, 34% / **54%** / 12%.

Média mensal **dentro** de cada fase (risco 1%, 3 posições):

| | Alta antes | Alta depois | Lateral antes | Lateral depois | Baixa antes | Baixa depois |
|---|---|---|---|---|---|---|
| hold BTC | +8,5% | +6,3% | 0,0% | −1,8% | +3,1% | +6,0% |
| ema_cross 4h | +3,9% | **+3,4%** | +1,4% | +0,5% | +0,5% | +0,6% |
| donchian 4h | +4,8% | +3,0% | +1,5% | +0,1% | −0,6% | −0,4% |
| keltner 4h | +5,8% | +2,9% | +1,8% | +0,6% | −1,3% | −2,1% |
| sma_trend 4h | +7,2% | +3,8% | +1,6% | −0,7% | −0,3% | +0,7% |
| roc_momentum 4h | +4,0% | +3,0% | +1,8% | +0,1% | −0,7% | −1,3% |
| donchian diário | +3,8% | **+0,4%** | +1,6% | −0,1% | +0,2% | 0,0% |
| keltner diário | +3,7% | +2,3% | +1,0% | −0,3% | 0,0% | 0,0% |
| sma_trend diário | +4,7% | +1,6% | +0,1% | −0,3% | −0,1% | +0,3% |
| ema_cross diário | +0,9% | +2,1% | +0,9% | −0,3% | −0,1% | 0,0% |
| roc_momentum diário | +1,1% | +2,8% | +0,2% | −0,4% | −0,1% | 0,0% |

Leituras:

- **Parte é o mercado:** desde 2024 o mercado passou mais da metade do tempo lateral (54% contra 42%), fase em que as estratégias de tendência ficam perto de zero. E as altas foram mais fracas: o próprio BTC rendeu 6,3%/mês nas fases de alta, contra 8,5% antes (−25%).
- **Parte é a estratégia:** a donchian diária caiu de +3,8% para +0,4%/mês **nas fases de alta** (−90%), muito mais do que o enfraquecimento do mercado explica. Ela deixou de pegar as altas. As outras perderam entre 20% e 50% nas altas, compatível com o mercado.
- **A mais robusta é a ema_cross 4h:** quase igual nas altas (+3,9% → +3,4%) e positiva em todas as fases nos dois períodos.
- Em "baixa" o hold de BTC aparece positivo porque o rótulo usa os 90 dias passados: depois de uma queda forte, o BTC muitas vezes repica. As estratégias, por regra, quase não compram nessa fase.

## 17/10/2026 – rotação por momentum (ideia do Vibe-Trading)

Toda semana, ranqueia as 10 moedas e fica com as `top_k` mais fortes que estejam acima da média de regime; sem nenhuma elegível, fica em caixa. Duas notas: `momentum_rotation` (retorno dos últimos N dias, Carhart 1997) e `high52w_rotation` (proximidade da máxima de N dias, George & Hwang 2004). `exposure` = fração do patrimônio aplicada (o resto em caixa). Walk-forward no diário.

| | Mês 2020–26 | Mês desde 2024 | Pior queda | Queda desde 2024 | Lateral desde 2024 |
|---|---|---|---|---|---|
| momentum_rotation 25% | +1,32% | +0,34% | −21% | −18% | −0,9% |
| momentum_rotation 50% | +2,18% | +0,35% | −39% | −33% | −1,9% |
| momentum_rotation 100% | +3,64% | −0,24% | −65% | −55% | −3,7% |
| high52w_rotation 25% | +1,77% | +0,61% | −28% | −14% | −0,6% |
| high52w_rotation 50% | +3,00% | +1,12% | −47% | −27% | −1,1% |
| high52w_rotation 100% | +4,96% | +1,46% | −71% | −47% | −2,5% |
| *ema_cross 4h (referência)* | +1,87% | +1,45% | −23% | −20% | +0,5% |
| *keltner diário (referência)* | +1,34% | +0,64% | −14% | −13% | −0,3% |
| hold BTC | +3,00% | +1,85% | −77% | −53% | −1,8% |

Leituras:

- Com 100% aplicado, a rotação rende muito (2021: +772% e +802%, pegando a alta das altcoins), mas cai quase como o hold (−65% no crash de maio/2021; −71% sangrando de 11/2021 a 10/2023).
- **Com risco comparável (25%), não supera a ema_cross 4h**: rende menos no período todo e muito menos desde 2024.
- **Não ajuda no mercado lateral**, ao contrário do que se esperava: perde nessa fase (−0,6% a −3,7%/mês), porque troca de moeda atrás de altas que não continuam.
- A high52w é a melhor das duas; a 50% ficou parecida com o hold de BTC em ganho com uma queda menor (−47% vs −77%), mas ainda grande demais.
- Decisão: não vira conta de paper por enquanto (o agente também não opera rotação ainda). Critério novo: **pior queda de no máximo −30%** (a high52w 100% passava nos outros critérios com −71%). Com ele, das variações de 17/10, saem também ema_cross 4h 2%/3 e 2%/5 e donchian diário 2%/5 e 1%/5 (quedas de −25% a −45%).
