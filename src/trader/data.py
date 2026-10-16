"""Coleta de candles via ccxt com cache incremental em CSV.

Os dados históricos vêm sempre da exchange real (endpoint público, sem chave), mesmo quando as
ordens vão para a testnet: os preços da testnet não são representativos do mercado.
"""

from __future__ import annotations

from pathlib import Path

import ccxt
import pandas as pd

COLUMNS = ["open", "high", "low", "close", "volume"]


def make_exchange(
    exchange_id: str = "binance",
    *,
    sandbox: bool = False,
    api_key: str | None = None,
    secret: str | None = None,
) -> ccxt.Exchange:
    cls = getattr(ccxt, exchange_id)
    ex = cls({"apiKey": api_key, "secret": secret, "enableRateLimit": True})
    if sandbox:
        ex.set_sandbox_mode(True)
    return ex


def to_frame(rows: list[list]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["time", *COLUMNS])
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df = df.drop_duplicates("time").set_index("time").sort_index()
    return df.astype(float)


def fetch_ohlcv(
    ex: ccxt.Exchange,
    symbol: str,
    timeframe: str,
    since_ms: int,
    *,
    until_ms: int | None = None,
    limit: int = 1000,
) -> pd.DataFrame:
    """Baixa candles de `since_ms` até `until_ms` (exclusivo), paginando.
    Descarta o candle ainda aberto."""
    tf_ms = ex.parse_timeframe(timeframe) * 1000
    now = ex.milliseconds()
    end = min(now, until_ms) if until_ms else now
    rows: list[list] = []
    cursor = since_ms
    while cursor < end:
        batch = ex.fetch_ohlcv(symbol, timeframe, since=cursor, limit=limit)
        if not batch:
            break
        rows.extend(batch)
        nxt = batch[-1][0] + tf_ms
        if nxt <= cursor:
            break
        cursor = nxt
    rows = [r for r in rows if r[0] + tf_ms <= now and r[0] < end]
    return to_frame(rows) if rows else pd.DataFrame(columns=COLUMNS)


def cache_path(data_dir: Path, exchange_id: str, symbol: str, timeframe: str) -> Path:
    return Path(data_dir) / f"{exchange_id}_{symbol.replace('/', '-')}_{timeframe}.csv"


def read_cache(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col="time", parse_dates=["time"])
    return df.astype(float)


def load_candles(
    symbol: str,
    timeframe: str,
    since: str | pd.Timestamp = "2018-01-01",
    *,
    exchange_id: str = "binance",
    data_dir: Path = Path("data"),
    refresh: bool = True,
    ex: ccxt.Exchange | None = None,
) -> pd.DataFrame:
    """Lê do cache e, se `refresh`, completa com o que faltar até o último candle fechado."""
    since_ts = pd.Timestamp(since, tz="UTC") if pd.Timestamp(since).tzinfo is None else pd.Timestamp(since)
    path = cache_path(data_dir, exchange_id, symbol, timeframe)
    cached = read_cache(path)

    if refresh:
        ex = ex or make_exchange(exchange_id)
        tf_ms = ex.parse_timeframe(timeframe) * 1000
        since_ms = int(since_ts.timestamp() * 1000)
        older = None
        start_ms = since_ms
        if cached is not None and len(cached):
            first_ms = int(cached.index[0].timestamp() * 1000)
            if first_ms > since_ms:
                # pedido começa antes do cache (ou antes da listagem do ativo, e aí volta vazio)
                older = fetch_ohlcv(ex, symbol, timeframe, since_ms, until_ms=first_ms)
            start_ms = int(cached.index[-1].timestamp() * 1000) + tf_ms
        fresh = fetch_ohlcv(ex, symbol, timeframe, start_ms)
        parts = [p for p in (older, cached, fresh) if p is not None and len(p)]
        df = pd.concat(parts) if parts else pd.DataFrame(columns=COLUMNS)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index_label="time")
    else:
        if cached is None:
            raise FileNotFoundError(f"Sem cache para {symbol} {timeframe}: rode `trader fetch` antes")
        df = cached
    return df[df.index >= since_ts]
