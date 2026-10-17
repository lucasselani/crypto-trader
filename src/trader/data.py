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


def perp_symbol(symbol: str) -> str:
    """Spot 'BTC/USDT' → perpétuo linear do ccxt 'BTC/USDT:USDT'."""
    return symbol if ":" in symbol else f"{symbol}:{symbol.split('/')[1]}"


def fetch_funding(ex: ccxt.Exchange, symbol: str, since_ms: int, *, limit: int = 1000) -> pd.Series:
    """Histórico de funding (decimal por período, ex.: 0.0001 = 0,01% a cada 8h), paginado."""
    rows: list[tuple[int, float]] = []
    cursor = since_ms
    now = ex.milliseconds()
    while cursor < now:
        batch = ex.fetch_funding_rate_history(perp_symbol(symbol), since=cursor, limit=limit)
        if not batch:
            break
        rows.extend((b["timestamp"], float(b["fundingRate"])) for b in batch)
        nxt = batch[-1]["timestamp"] + 1
        if nxt <= cursor:
            break
        cursor = nxt
    if not rows:
        return pd.Series(dtype=float, name="funding")
    s = pd.Series(dict(rows), name="funding").sort_index()
    s.index = pd.to_datetime(s.index, unit="ms", utc=True)
    s.index.name = "time"
    return s[~s.index.duplicated(keep="last")]


def load_funding(
    symbol: str,
    since: str | pd.Timestamp = "2019-01-01",
    *,
    exchange_id: str = "binanceusdm",
    data_dir: Path = Path("data"),
    refresh: bool = True,
    ex: ccxt.Exchange | None = None,
) -> pd.Series:
    """Funding do perpétuo do ativo, com cache CSV incremental. Vazio se não houver perpétuo."""
    path = Path(data_dir) / f"funding_{exchange_id}_{symbol.replace('/', '-')}.csv"
    cached = None
    if path.exists():
        cached = pd.read_csv(path, index_col="time")["funding"]
        cached.index = pd.to_datetime(cached.index, utc=True, format="ISO8601")
    if refresh:
        ex = ex or make_exchange(exchange_id)
        start = pd.Timestamp(since, tz="UTC") if pd.Timestamp(since).tzinfo is None else pd.Timestamp(since)
        start_ms = int(start.timestamp() * 1000)
        if cached is not None and len(cached):
            start_ms = int(cached.index[-1].timestamp() * 1000) + 1
        try:
            fresh = fetch_funding(ex, symbol, start_ms)
        except ccxt.BadSymbol:
            fresh = pd.Series(dtype=float, name="funding")
        parts = [p for p in (cached, fresh) if p is not None and len(p)]
        s = pd.concat(parts) if parts else pd.Series(dtype=float, name="funding")
        s = s[~s.index.duplicated(keep="last")].sort_index().rename("funding")
        path.parent.mkdir(parents=True, exist_ok=True)
        s.to_frame().to_csv(path, index_label="time")
        return s
    if cached is None:
        raise FileNotFoundError(f"Sem cache de funding para {symbol}: rode `trader fetch-funding` antes")
    return cached


def attach_funding(candles: pd.DataFrame, funding: pd.Series, timeframe_s: int,
                   window: int = 21) -> pd.DataFrame:
    """Adiciona a coluna `funding`: média dos últimos `window` pagamentos (21 = 7 dias) já
    conhecidos no **fechamento** de cada candle (o índice do candle é a abertura). Sem dados: NaN."""
    out = candles.copy()
    if funding.empty:
        out["funding"] = float("nan")
        return out
    avg = funding.rolling(window, min_periods=window).mean()
    close_times = out.index + pd.Timedelta(seconds=timeframe_s) - pd.Timedelta(milliseconds=1)
    pos = avg.index.searchsorted(close_times, side="right") - 1
    vals = avg.to_numpy()
    out["funding"] = [vals[p] if p >= 0 else float("nan") for p in pos]
    return out


def with_funding(candles: pd.DataFrame, symbol: str, timeframe_s: int, *,
                 data_dir: Path = Path("data"), refresh: bool = True) -> pd.DataFrame:
    """Candles + coluna `funding` (atualiza o cache de funding se `refresh`)."""
    since = candles.index[0] - pd.Timedelta(days=10) if len(candles) else "2019-01-01"
    return attach_funding(candles, load_funding(symbol, since, data_dir=data_dir, refresh=refresh),
                          timeframe_s)
