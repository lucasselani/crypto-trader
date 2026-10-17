"""Resultado por fase do mercado (alta, baixa, lateral).

Cada dia é rotulado pelo retorno acumulado do mercado de referência (ex.: BTC) nos `window` dias
anteriores, só com o passado: acima de `bull` é alta, abaixo de `bear` é baixa, no meio é lateral.
Assim dá para separar "a estratégia piorou" de "o mercado mudou de fase": se o resultado dentro de
cada fase se mantém e só a mistura de fases mudou, é o mercado. Ideia adaptada do
`evidence_harness` do Vibe-Trading (MIT).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REGIMES = ("alta", "lateral", "baixa")
DAYS_PER_MONTH = 30.4375


def label_regimes(close: pd.Series, window: int = 90, bull: float = 0.20,
                  bear: float = -0.20) -> pd.Series:
    """Rótulo diário pela variação de `window` dias até aquele dia. Sem histórico suficiente: NaN."""
    daily = close.resample("D").last().ffill()
    trailing = daily / daily.shift(window) - 1
    labels = pd.Series(np.where(trailing >= bull, "alta",
                                np.where(trailing <= bear, "baixa", "lateral")), index=daily.index)
    return labels.where(trailing.notna())


def regime_stats(equity: pd.Series, labels: pd.Series) -> pd.DataFrame:
    """Por fase: dias, média mensal da estratégia e pior queda dentro da fase.

    O retorno do dia d (do fechamento de d-1 ao de d) é atribuído ao rótulo do dia d-1, que é o que
    se sabia ao entrar no dia."""
    eq = equity.resample("D").last().ffill().dropna()
    rets = eq.pct_change().dropna()
    lab = labels.shift(1).reindex(rets.index)
    rows = {}
    for regime in REGIMES:
        r = rets[lab == regime]
        if r.empty:
            rows[regime] = {"dias": 0, "mensal": np.nan, "pior_queda": np.nan}
            continue
        growth = (1 + r).cumprod()
        rows[regime] = {
            "dias": len(r),
            "mensal": float(growth.iloc[-1] ** (DAYS_PER_MONTH / len(r)) - 1),
            "pior_queda": float((growth / growth.cummax().clip(lower=1) - 1).min()),
        }
    return pd.DataFrame(rows).T


def regime_mix(labels: pd.Series, start=None, end=None) -> pd.Series:
    """Fração dos dias em cada fase no período."""
    lab = labels.loc[start:end].dropna()
    return lab.value_counts(normalize=True).reindex(list(REGIMES), fill_value=0.0)
