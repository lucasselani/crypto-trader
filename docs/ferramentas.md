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

### Vibe-Trading — não verificado
- https://github.com/HKUDS/Vibe-Trading
- O README não carregou na consulta. Pelos tópicos do repositório: agente de IA, trading algorítmico, backtesting, MCP, multiagente, Python. A descrição da lista fala em agentes que "debatem" antes de operar.
- Pendente: confirmar se busca notícias e quais mercados/exchanges suporta.

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
