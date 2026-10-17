# Ferramentas avaliadas

Levantamento de 16/10/2026, a partir de uma lista de posts do Instagram (lista completa em [referencias/ferramentas-instagram.md](referencias/ferramentas-instagram.md)). Os READMEs de Fincept e AutoHedge foram conferidos no GitHub nessa data.

## Ferramentas de trading da lista

### AutoHedge — descartar
- https://github.com/The-Swarm-Corporation/AutoHedge
- "Hedge fund" autônomo com pipeline de agentes: Director (tese), Quant (análise técnica), Risk Manager (tamanho de posição) e Execution (ordens).
- **Suporte atual: só trading autônomo na Solana.** Coinbase "em breve", outras exchanges no roadmap. Nada de B3.
- Vale só como referência de arquitetura multiagente (separação de responsabilidades com saída em JSON).

### Fincept Terminal — a mais próxima do que queremos
- https://github.com/Fincept-Corporation/FinceptTerminal
- Terminal desktop (C++20/Qt6 com Python 3.11 embutido). Edição open source AGPL-3.0, gratuita para uso pessoal, com uma release por mês; o desenvolvimento diário está na edição Enterprise (paga, US$ 99–299/usuário/mês).
- Tem **módulo de notícias**, **37 agentes** (trader/investidor, economia, geopolítica) usando sua própria chave de LLM (OpenAI, Anthropic, Gemini, Ollama etc.).
- Mais de 100 conectores de dados, incluindo **Yahoo Finance** (cobre ações da B3 com sufixo `.SA`), FRED, IMF, Polygon, Kraken.
- **Paper trading** e 16 integrações com corretoras na versão aberta; roteamento de ordens ao vivo só no Enterprise.
- Também tem node editor visual, ferramentas MCP e um "AI Quant Lab" (ML, descoberta de fatores, RL).
- Ponto fraco: notícias do mercado brasileiro devem ser fracas, porque o foco é global. Licença AGPL: se distribuir uma versão modificada ou rodar como serviço para outros, precisa publicar o código.

### Vibe-Trading — usar como fonte de ideias, não como plataforma
- https://github.com/HKUDS/Vibe-Trading (licença MIT). Código lido em 17/10/2026 (commit `596fcf3`, de 16/10/2026); nada foi executado.
- **O que é:** um "workspace de pesquisa" movido a LLM. Você pergunta em linguagem natural e o agente gera o código da estratégia, roda o backtest e escreve o relatório. Tem times multiagente, interface web, integração com dezenas de chats, MCP e execução ao vivo via corretora (ex.: Robinhood), em que o **LLM toma as decisões** (as notas de versão falam em "sessões de decisão" com orçamento diário de uso do modelo).
- **Tamanho:** ~2.900 arquivos, ~2.000 em Python, 155 MB, com várias atualizações por dia. Foco maior em ações (China, Hong Kong, EUA); cripto entra via OKX e ccxt.
- **Por que não adotar como base:** contraria a regra principal do projeto (o LLM decidir a ordem); é grande e muda demais para depender dele; as estratégias são geradas na hora pelo LLM, não um conjunto fixo e testado.
- **O que vale aproveitar (ideias, reimplementadas aqui):**
  1. **Evidência por regime de mercado** (`strategy_discovery/evidence_harness.py`): separa o resultado da estratégia em períodos de alta, baixa e lateral, definidos pelo retorno acumulado do mercado. Responde se o resultado fraco desde 2024 é do mercado (lateral) ou da estratégia.
  2. **Monitor de decadência** (`strategy_store/decay.py`): máquina de estados saudável → atenção → decadente → desligada, por Sharpe móvel com limites (1,0 / 0,5 / 0,0) e contagem de avisos seguidos. Bom para acompanhar as contas de paper.
  3. **Fatores acadêmicos de momentum** (`factors/zoo/academic`): momentum de Carhart (retorno de 12 meses sem o último) e proximidade da máxima de 52 semanas (George & Hwang, 2004). São de **ranking entre ativos**: viram, para nós, uma estratégia de rotação (segurar as K moedas mais fortes). Precisa de suporte a ranking no motor.
  4. **Taxa de funding dos perpétuos como termômetro** (skills `perp-funding-basis` e `crypto-derivatives`): funding muito positivo = mercado alavancado e eufórico. Para spot só comprado, serve como **filtro** (não comprar com o mercado superaquecido), sem operar derivativos. Os dados são públicos na Binance.
- **O que não serve:** arbitragem de funding/base (exige derivativos e venda a descoberto), estratégias de opções, a maioria dos 478 "alphas" (feitos para ações, long-short), e o regime de correlação, que o próprio autor diz não servir para timing de compra e venda.
- Skills técnicas (`technical-basic`, `volatility`, `seasonal`) são indicadores clássicos sem nada além do que já temos.

## Outras ferramentas da lista úteis para o pipeline

| Ferramenta | Uso aqui |
|---|---|
| [Last 30 Days](https://github.com/mvanhorn/last30days-skill) | Tendências em Reddit, X, YouTube, HN e Polymarket. Útil para sentimento de cripto (narrativas, hype), não é feita para mercado. |
| [Scrapling](https://github.com/D4Vinci/Scrapling) | Coleta de notícias e páginas de fatos relevantes que não têm API. |
| [Camofox Browser](https://github.com/jo-inc/camofox-browser) | Navegação headless para fontes que bloqueiam bots. Cuidado com os termos de uso. |
| [Superpowers](https://github.com/obra/superpowers) / Systematic Debugging | Disciplina de TDD e depuração para o código de estratégia e execução. |
| [Agent Skills (Addy Osmani)](https://github.com/addyosmani/agent-skills) | Fluxo spec → plan → build; casa com o workflow SDD já usado. |
| [Context Optimization](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering) | Sessões longas de agentes processando muito texto (notícias). |
| [Diagram Design](https://github.com/cathrynlavery/diagram-design) | Documentar a arquitetura. |
| [Onyx](https://github.com/onyx-dot-app/onyx) | Base de conhecimento consultável (ex.: histórico de notícias, diário de operações). |

## Ferramentas de fora da lista que entram no projeto

| Ferramenta | Para quê |
|---|---|
| `ccxt` (Python/TypeScript) | Biblioteca única para falar com dezenas de exchanges de cripto (dados e ordens). |
| Testnet da exchange (ex.: Binance) | Mesma API da conta real, com dinheiro fictício. |
| MetaTrader 5 + pacote Python `MetaTrader5` | Dados (inclusive ticks) e ordens na B3 via corretora que ofereça MT5. Só roda no Windows. |
| Profit (Nelogica) | Plataforma brasileira com estratégias em NTSL e modo **replay de mercado**. |
| Strategy Tester do MT5 | Backtest com "ticks reais", mais confiável que backtest por candle para day trade. |
