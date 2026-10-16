# Exchange e API

Decisão tomada em 16/10/2026. Status regulatório e regras de imposto mudam: confirme antes de colocar dinheiro real.

## Recomendação

| Fase | Onde | Conta? | Custo |
|---|---|---|---|
| 1. Backtest e walk-forward | Dados públicos da **Binance** via `ccxt` | Não precisa | Grátis |
| 2. Simulador local (`TRADER_MODE=paper`) | Preços reais da Binance, ordens simuladas no `state/` | Não precisa | Grátis |
| 3. Testnet (`TRADER_MODE=testnet`) | **Binance Spot Testnet** (https://testnet.binance.vision) | Login com GitHub, sem KYC | Grátis, saldo fictício |
| 4. Real (`TRADER_MODE=live`) | **Binance** (conta com KYC, depósito por Pix em BRL) | Sim | 0,1% por lado (menos com BNB/VIP) |

**API: `ccxt`** (Python), falando com a API REST de spot da Binance. É a mesma biblioteca para dados e ordens, e o mesmo código serve para testnet e real: só mudam a chave e o `set_sandbox_mode`.

### Por que Binance

- **Testnet de spot com a mesma API da conta real.** É o que permite rodar muito simulador e depois virar a chave sem reescrever nada. As exchanges brasileiras não oferecem testnet.
- **Histórico longo e gratuito** de candles (BTC/USDT desde 2017) sem chave, o que alimenta o backtest e o walk-forward.
- **Liquidez:** spread menor e slippage menor que nas exchanges nacionais, importante mesmo em swing.
- **Pares em BRL e Pix** para entrar e sair do real.
- **Suporte de primeira classe no `ccxt`**, incluindo stop na exchange (`STOP_LOSS_LIMIT`), que protege a posição mesmo com o bot desligado.

### Pontos contra (decidir antes do real)

- **Imposto:** é provável que a Receita trate a Binance como exchange estrangeira: 15% sobre o lucro, apuração anual (Lei 14.754/2023), **sem** a isenção de R$ 35 mil/mês. A própria Binance diz que operações pela entidade nacional poderiam ter a isenção; as fontes divergem. Ver [cripto.md](cripto.md).
- **Autorização do Banco Central:** quem já operava teve 270 dias após 02/02/2026 para pedir autorização como SPSAV, e o processo pode levar anos. Conferir no site do BC se a Binance (e a alternativa escolhida) está em situação regular.
- **Risco de custódia:** manter na exchange só o capital do bot.

### Alternativa nacional

Se o volume de vendas ficar abaixo de R$ 35 mil/mês e a isenção valer, uma exchange brasileira pode compensar a liquidez menor. Candidatas com API e suporte no `ccxt`: **Mercado Bitcoin**, **Foxbit**, **NovaDAX** (verificar a cobertura de cada uma no `ccxt` antes, em especial ordens stop). Nenhuma tem testnet, então o caminho seria: validar tudo na Binance testnet e trocar só `TRADER_EXCHANGE` para o real, com valor pequeno no começo.

## Como criar a chave da testnet

1. Entrar em https://testnet.binance.vision com a conta do GitHub.
2. "Generate HMAC_SHA256 Key", copiar API Key e Secret Key (o secret aparece uma vez só).
3. No `.env`: `TRADER_MODE=testnet`, `TRADER_API_KEY=...`, `TRADER_API_SECRET=...`.
4. `trader run --dry-run` para ver as decisões e depois `trader run`.

A testnet reinicia os saldos de tempos em tempos e os preços dela não seguem exatamente o mercado real. Por isso os **sinais** são calculados sempre com candles da Binance real, e a testnet serve para validar **execução** (ordens, precisão, stops, saldo, taxa cobrada no ativo).

## Chave da conta real (quando chegar lá)

- Permissões: **leitura + spot trading**. **Nunca** habilitar saque (withdraw) nem margem/futuros.
- Restringir a chave por IP (o IP do servidor onde o bot roda).
- `TRADER_ALLOW_LIVE=yes` só quando a decisão for consciente; sem isso o modo live recusa rodar.
- Começar com um valor que se aceite perder inteiro.

## Fontes

- [Adriano Freire – Como declarar criptomoedas no IR 2026](https://www.adrianofreire.com.br/blog/como-declarar-criptomoedas-ir-2026)
- [Nord Investimentos – Binance no Brasil: implicações jurídicas e tributárias](https://www.nordinvestimentos.com.br/blog/binance-sede-no-brasil/)
- [Acionista – Binance sediada no Brasil: repercussões](https://acionista.com.br/binance-sediada-no-brasil-saiba-as-repercussoes-juridicas-e-tributarias/)
- [TabNews – A isenção de R$ 35 mil em cripto não acabou](https://www.tabnews.com.br/eliasborgesdasilva/pitch-limite35k-a-isencao-de-r-35-mil-em-cripto-nao-acabou-e-boa-parte-do-que-o-google-devolve-sobre-2026-esta-errado)
- [Capital Aberto – Novo marco regulatório das PSAVs e prioridades do BCB para 2026](https://capitalaberto.com.br/artigos/2026/03/novo-marco-regulatorio-e-contabil-das-psavs-prioridades-do-bcb)
