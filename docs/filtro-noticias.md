# Filtro de notícias e watchlist

O objetivo é "separar o trigo do joio": saber o que vale a pena olhar antes de gastar tempo com análise.

## Ressalva principal

O agente **não** vai operar a notícia em si, principalmente no day trade. Quando o LLM termina de ler, o preço já andou. O papel dele é montar a watchlist **antes** da abertura (B3) ou em janelas fixas (cripto): "hoje vale olhar esses 5, por esses motivos".

## Fontes

### B3
1. **Oficiais primeiro:** fatos relevantes e comunicados ao mercado publicados pela CVM e pela B3. São estruturados e chegam antes da repercussão na imprensa.
2. **Imprensa para contexto:** InfoMoney, Valor, Brazil Journal.

### Cripto
- Anúncios oficiais das exchanges (listagens, deslistagens, manutenção).
- Notícias de cripto e macro (juros, dólar, regulação).
- Sentimento e narrativas em redes: Reddit, X, YouTube (a skill Last 30 Days cobre parte disso).

## Combinar com sinais quantitativos

No day trade, o que "vale mexer" aparece mais nos números do que na manchete:

- **Gap** de abertura
- **Volume relativo** acima da média
- **Volatilidade** (ATR)

Regra prática: notícia sem volume é ruído; volume sem notícia aparente merece investigação.

## O que o LLM faz com cada item

Para cada notícia ou comunicado, produzir um registro estruturado (JSON):

- ativo(s) afetado(s)
- relevância (alta, média, baixa)
- impacto provável (alta, baixa, neutro)
- novidade ou repetição de algo já precificado
- resumo de uma linha

## Saída

Uma watchlist ranqueada, por exemplo antes do pregão, e só ela segue para a análise técnica e a estratégia.

## Ferramentas candidatas

- Fincept Terminal: tem módulo de notícias e agentes, mas cobertura brasileira provavelmente fraca.
- Scrapling / Camofox: coletar fontes sem API.
- Last 30 Days: tendências em redes, útil em cripto.
- Construir o próprio: é a parte mais fácil e onde um LLM realmente funciona bem (ler muito texto e classificar).
