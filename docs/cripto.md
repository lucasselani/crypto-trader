# Cripto no Brasil

Situação levantada em 16/10/2026. Confirme as regras de imposto com um contador antes de operar.

## É permitido?

Sim. Desde **2 de fevereiro de 2026** o setor está regulado pelo Banco Central (Resoluções BCB nº 519, 520 e 521, publicadas em 10/11/2025):

- Exchanges e custodiantes precisam de **autorização prévia** do BC para funcionar e passam a ser Sociedades Prestadoras de Serviços de Ativos Virtuais (SPSAVs).
- Capital mínimo bem maior que antes, regras de governança, segurança cibernética e prevenção à lavagem de dinheiro.
- **Segregação patrimonial:** as criptos dos clientes ficam separadas dos recursos da empresa (resposta a colapsos como o da FTX).
- Pagamentos e transferências internacionais com cripto, operações com stablecoins e transferências para carteiras autocustodiadas passam a ser tratados como operações de câmbio.

## Por que é mais simples tecnicamente que ações

- **APIs abertas** REST e WebSocket para pessoa física, sem MetaTrader, sem VPS Windows.
- **`ccxt`** (Python/TypeScript): o mesmo código fala com dezenas de exchanges.
- **Testnet** com a mesma API da conta real: trocando URL e chave, o bot passa a operar de verdade.
- **Dados de graça**, inclusive livro de ofertas e trades tick a tick.

## O que é mais difícil

- **Mercado 24/7:** o bot precisa ser robusto, com stop e limite de perda automáticos.
- **Volatilidade alta** e muitos bots profissionais disputando as mesmas oportunidades.
- **Liquidez das exchanges brasileiras** bem menor que das estrangeiras; ordens maiores executam a preços piores.
- **Risco da corretora:** diminuiu com a regulação, mas existe.

## Impostos (pessoa física)

| Situação | Regra |
|---|---|
| Exchange brasileira, vendas até R$ 35 mil/mês | Lucro isento (declarar como rendimento isento) |
| Exchange brasileira, vendas acima de R$ 35 mil/mês | Ganho de capital de 15% a 22,5% sobre o lucro, DARF mensal |
| Exchange estrangeira (Binance, Kraken, OKX…) | Lei 14.754: 15% sobre o lucro, **sem isenção**, apurado anualmente |
| Day trade de cripto | Sem regra clara. Há entendimento de que não entra na isenção e seria tributado como renda variável, 20% |
| Permuta cripto por cripto | Considerada alienação, sujeita a tributação |

- **Declaração mensal à Receita (DeCripto / antiga IN 1.888):** obrigatória para quem opera em exchange estrangeira ou P2P acima de R$ 30 mil/mês. Multa de R$ 500 a R$ 1.500 por mês não declarado.
- **Atenção:** as fontes divergem sobre a isenção de R$ 35 mil. Algumas dizem que acabou em 2026 (ligado à proposta de reforma/alíquota fixa); outras, de junho de 2026, ainda a tratam como válida em exchange brasileira. **Confirmar antes de operar.**

## Fontes

- [Adriano Freire – Como declarar criptomoedas no IR 2026](https://www.adrianofreire.com.br/blog/como-declarar-criptomoedas-ir-2026)
- [Awake Trader – IR Criptomoedas 2026](https://www.awaketrader.com/pt/educacao/imposto-renda-criptomoedas-receita-federal-2026)
- [Jornal Contábil – O que muda para as criptomoedas em 2026](https://jornalcontabil.com.br/noticia/o-que-muda-para-as-criptomoedas-em-2026-com-a-reforma-tributaria/)
- [brapi – Como declarar criptomoedas no IR 2026](https://brapi.dev/blog/como-declarar-criptomoedas-imposto-renda-2026)
- [Giro News – Banco Central regulamenta mercado de criptoativos](https://gironews.com/negocios/banco-central-regulamenta-mercado-de-criptoativos/)
- [InvestNews – BC publica regulamentação das criptomoedas](https://investnews.com.br/investimentos/bc-publica-regulamentacao-das-criptomoedas-veja-o-que-muda/)
- [Movimento Econômico – regulação do BC](https://movimentoeconomico.com.br/?p=105662)
