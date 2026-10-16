"""CLI: `trader fetch | backtest | compare | walkforward | run`."""

from __future__ import annotations

import argparse
import json
import math
import sys

import pandas as pd

from trader.backtest import run_backtest
from trader.config import Settings
from trader.data import load_candles, make_exchange
from trader.strategies import STRATEGIES, get_strategy
from trader.walkforward import walk_forward

PCT = ("total_return", "cagr", "max_drawdown", "win_rate", "avg_trade", "exposure", "buy_hold")


def parse_params(items: list[str]) -> dict:
    """Converte ['fast=20', 'stop_atr_mult=2.5'] em {'fast': 20, 'stop_atr_mult': 2.5}."""
    out = {}
    for item in items:
        key, _, raw = item.partition("=")
        out[key] = json.loads(raw)
    return out


def fmt_metrics(m: dict) -> dict:
    return {k: (f"{v:.1%}" if k in PCT and isinstance(v, float) and not math.isnan(v) else
                round(v, 2) if isinstance(v, float) else v) for k, v in m.items()}


def _candles(s: Settings, symbol: str, since: str, refresh: bool) -> pd.DataFrame:
    return load_candles(symbol, s.timeframe, since, exchange_id=s.exchange,
                        data_dir=s.data_dir, refresh=refresh)


def cmd_fetch(s: Settings, a: argparse.Namespace) -> None:
    for sym in a.symbols or s.symbols:
        df = _candles(s, sym, a.since, refresh=True)
        print(f"{sym} {s.timeframe}: {len(df)} candles, {df.index[0].date()} → {df.index[-1].date()}")


def cmd_backtest(s: Settings, a: argparse.Namespace) -> None:
    strat = get_strategy(a.strategy, **parse_params(a.param))
    df = _candles(s, a.symbol, a.since, refresh=not a.offline)
    res = run_backtest(df, strat, initial_cash=a.cash, costs=s.costs, risk=s.risk)
    print(f"{a.symbol} {s.timeframe} {strat.name} {strat.params()}")
    for k, v in fmt_metrics(res.metrics).items():
        print(f"  {k:>14}: {v}")
    if a.trades and res.trades:
        print(res.trades_frame().to_string(index=False))


def cmd_compare(s: Settings, a: argparse.Namespace) -> None:
    rows = []
    for sym in a.symbols or s.symbols:
        df = _candles(s, sym, a.since, refresh=not a.offline)
        for name in STRATEGIES:
            m = run_backtest(df, get_strategy(name), costs=s.costs, risk=s.risk).metrics
            rows.append({"symbol": sym, "strategy": name, **fmt_metrics(m)})
    cols = ["symbol", "strategy", "total_return", "cagr", "max_drawdown", "sharpe", "trades",
            "win_rate", "profit_factor", "exposure", "buy_hold"]
    print(pd.DataFrame(rows)[cols].to_string(index=False))


def cmd_walkforward(s: Settings, a: argparse.Namespace) -> None:
    df = _candles(s, a.symbol, a.since, refresh=not a.offline)
    res = walk_forward(df, get_strategy(a.strategy), train_bars=a.train, test_bars=a.test,
                       objective=a.objective, costs=s.costs, risk=s.risk)
    print(res.windows_frame().to_string(index=False))
    print(f"\nFora da amostra ({a.symbol} {s.timeframe} {a.strategy}):")
    for k, v in fmt_metrics(res.metrics).items():
        if k != "exposure":
            print(f"  {k:>14}: {v}")


def cmd_run(s: Settings, a: argparse.Namespace) -> None:
    from trader.agent import SwingAgent
    from trader.broker import ExchangeBroker, PaperBroker

    s.check_live_allowed()
    market = make_exchange(s.exchange)
    if s.mode == "paper":
        broker = PaperBroker(s.state_dir / "paper_broker.json", market, s.paper_cash,
                             s.costs.fee_rate, s.costs.slippage)
    else:
        if not (s.api_key and s.api_secret):
            sys.exit(f"Modo {s.mode} exige TRADER_API_KEY e TRADER_API_SECRET no .env")
        ex = make_exchange(s.exchange, sandbox=s.mode == "testnet",
                           api_key=s.api_key, secret=s.api_secret)
        quotes = {sym.split("/")[1] for sym in s.symbols}
        if len(quotes) != 1:
            sys.exit("Todos os símbolos precisam ter a mesma moeda de cotação (ex.: tudo em USDT)")
        broker = ExchangeBroker(ex, quotes.pop())

    agent = SwingAgent(s, get_strategy(a.strategy or s.strategy, **parse_params(a.param)), broker,
                       market, s.state_dir / f"agent_{s.mode}.json", s.state_dir / "journal.jsonl")
    for d in agent.run_once(dry_run=a.dry_run):
        extra = " ".join(f"{k}={v:.6g}" for k, v in (("price", d.price), ("qty", d.qty),
                                                      ("stop", d.stop)) if v is not None)
        print(f"[{d.mode}] {d.symbol:<10} {d.action:<5} {d.reason} {extra}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="trader", description=__doc__)
    p.add_argument("--timeframe", help="sobrescreve TRADER_TIMEFRAME (ex.: 1d, 4h)")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="baixa/atualiza candles no cache")
    f.add_argument("--symbols", nargs="*")
    f.add_argument("--since", default="2018-01-01")

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--since", default="2018-01-01")
        sp.add_argument("--offline", action="store_true", help="usa só o cache, sem rede")

    b = sub.add_parser("backtest", help="backtest de uma estratégia em um ativo")
    b.add_argument("--strategy", required=True, choices=list(STRATEGIES))
    b.add_argument("--symbol", default="BTC/USDT")
    b.add_argument("--param", nargs="*", default=[], help="ex.: fast=20 stop_atr_mult=2.5")
    b.add_argument("--cash", type=float, default=10_000.0)
    b.add_argument("--trades", action="store_true", help="lista as operações")
    common(b)

    c = sub.add_parser("compare", help="todas as estratégias × ativos com parâmetros padrão")
    c.add_argument("--symbols", nargs="*")
    common(c)

    w = sub.add_parser("walkforward", help="otimiza e testa fora da amostra em janelas")
    w.add_argument("--strategy", required=True, choices=list(STRATEGIES))
    w.add_argument("--symbol", default="BTC/USDT")
    w.add_argument("--train", type=int, default=730, help="barras de otimização por janela")
    w.add_argument("--test", type=int, default=180, help="barras de teste por janela")
    w.add_argument("--objective", default="calmar", choices=["calmar", "sharpe", "total_return"])
    common(w)

    r = sub.add_parser("run", help="executa o agente uma vez (paper/testnet/live conforme .env)")
    r.add_argument("--strategy", choices=list(STRATEGIES))
    r.add_argument("--param", nargs="*", default=[])
    r.add_argument("--dry-run", action="store_true", help="só mostra as decisões, não executa")

    a = p.parse_args(argv)
    s = Settings.from_env()
    if a.timeframe:
        s.timeframe = a.timeframe
    {"fetch": cmd_fetch, "backtest": cmd_backtest, "compare": cmd_compare,
     "walkforward": cmd_walkforward, "run": cmd_run}[a.cmd](s, a)


if __name__ == "__main__":
    main()
