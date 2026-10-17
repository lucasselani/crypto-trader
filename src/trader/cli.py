"""CLI: `trader fetch | backtest | compare | portfolio | walkforward | battery | freeze | run |
status | forward | regimes`."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import replace

import pandas as pd

from trader.backtest import run_backtest, run_portfolio
from trader.config import Settings
from trader.data import load_candles, make_exchange, with_funding
from trader.risk import RiskConfig
from trader.strategies import STRATEGIES, get_strategy
from trader.walkforward import evaluate, optimize, param_grid, walk_forward

PCT = ("total_return", "cagr", "monthly", "max_drawdown", "win_rate", "avg_trade", "exposure", "buy_hold")


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


def _candles(s: Settings, symbol: str, since: str, refresh: bool,
             timeframe: str | None = None) -> pd.DataFrame:
    return load_candles(symbol, timeframe or s.timeframe, since, exchange_id=s.exchange,
                        data_dir=s.data_dir, refresh=refresh)


def bars_per_day(timeframe: str) -> float:
    return 86400 / make_exchange("binance").parse_timeframe(timeframe)


def _walk(s: Settings, data: dict, strategy: str, timeframe: str, a: argparse.Namespace,
          risk: RiskConfig | None = None):
    bpd = bars_per_day(timeframe)
    return walk_forward(data, get_strategy(strategy), train_bars=int(a.train_days * bpd),
                        test_bars=int(a.test_days * bpd), objective=a.objective,
                        costs=s.costs, risk=risk or s.risk)


def cmd_fetch(s: Settings, a: argparse.Namespace) -> None:
    for sym in a.symbols or s.symbols:
        df = _candles(s, sym, a.since, refresh=True)
        print(f"{sym} {s.timeframe}: {len(df)} candles, {df.index[0].date()} → {df.index[-1].date()}")


def cmd_fetch_funding(s: Settings, a: argparse.Namespace) -> None:
    from trader.data import load_funding

    for sym in a.symbols or s.universe:
        f = load_funding(sym, a.since, data_dir=s.data_dir)
        if f.empty:
            print(f"{sym}: sem perpétuo/funding")
        else:
            print(f"{sym}: {len(f)} pagamentos, {f.index[0].date()} → {f.index[-1].date()}, "
                  f"média {f.mean():.4%} por 8h")


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


def cmd_portfolio(s: Settings, a: argparse.Namespace) -> None:
    symbols = a.symbols or s.symbols
    data = {sym: _candles(s, sym, a.since, refresh=not a.offline) for sym in symbols}
    names = [a.strategy] if a.strategy else list(STRATEGIES)
    rows = []
    for name in names:
        strat = get_strategy(name, **(parse_params(a.param) if a.strategy else {}))
        res = run_portfolio(data, strat, initial_cash=a.cash, costs=s.costs, risk=s.risk,
                            kill_switch=not a.no_kill_switch)
        rows.append({"strategy": name, **fmt_metrics(res.metrics)})
        if a.trades and res.trades:
            print(f"\n{name}:")
            print(res.trades_frame().to_string(index=False))
    print(f"\nCarteira {', '.join(symbols)} ({s.timeframe}), até {s.risk.max_open_positions} posições:")
    print(pd.DataFrame(rows).to_string(index=False))


def cmd_walkforward(s: Settings, a: argparse.Namespace) -> None:
    symbols = a.symbols or s.symbols
    data = {sym: _candles(s, sym, a.since, refresh=not a.offline) for sym in symbols}
    res = _walk(s, data, a.strategy, s.timeframe, a)
    print(res.windows_frame().to_string(index=False))
    print(f"\nFora da amostra ({', '.join(symbols)} {s.timeframe} {a.strategy}):")
    for k, v in fmt_metrics(res.metrics).items():
        if k != "exposure":
            print(f"  {k:>14}: {v}")
    checks = evaluate(res)
    print("\nCritérios:", "  ".join(f"{k}={'ok' if v else 'falhou'}" for k, v in checks.items()))


def cmd_battery(s: Settings, a: argparse.Namespace) -> None:
    import ccxt

    symbols = a.symbols or s.universe
    rows = []
    curves: dict[str, pd.Series] = {}
    for tf in a.timeframes:
        data = {}
        for sym in symbols:
            try:
                data[sym] = _candles(s, sym, a.since, refresh=not a.offline, timeframe=tf)
            except (ccxt.BaseError, FileNotFoundError) as e:  # sem dados nessa exchange/timeframe
                print(f"  pulando {sym} {tf}: {e}", file=sys.stderr)
        for name in a.strategies or list(STRATEGIES):
            for risk_pct in a.risk or [s.risk.risk_per_trade]:
                for max_pos in a.max_positions or [s.risk.max_open_positions]:
                    risk = replace(s.risk, risk_per_trade=risk_pct, max_open_positions=max_pos)
                    label = f"{tf}_{name}_r{risk_pct:g}_p{max_pos}"
                    print(f"... {label}", file=sys.stderr, flush=True)
                    res = _walk(s, data, name, tf, a, risk)
                    curves[label] = res.equity
                    checks = evaluate(res)
                    m = res.metrics
                    rows.append({
                        "timeframe": tf, "strategy": name, "risk": risk_pct, "max_pos": max_pos,
                        **{k: m.get(k) for k in ("total_return", "monthly", "max_drawdown", "calmar",
                                                 "sharpe", "profit_factor", "trades", "buy_hold")},
                        **{f"ok_{k}": v for k, v in checks.items()},
                    })
    df = pd.DataFrame(rows)
    stamp = f"{pd.Timestamp.now(tz='UTC'):%Y%m%d_%H%M%S}"
    out = s.data_dir / "results" / f"battery_{stamp}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    # curvas de patrimônio fora da amostra (base 1.0), para combinar estratégias depois
    pd.concat(curves, axis=1).to_csv(out.with_name(f"equity_{stamp}.csv"), index_label="time")
    show = df.copy()
    for col in ("total_return", "monthly", "max_drawdown", "buy_hold"):
        show[col] = show[col].map(lambda v: f"{v:.1%}" if pd.notna(v) else "")
    for col in ("calmar", "sharpe", "profit_factor"):
        show[col] = show[col].map(lambda v: f"{v:.2f}" if pd.notna(v) else "")
    print(f"Universo: {', '.join(data)}\n")
    print(show.to_string(index=False))
    print(f"\nSalvo em {out}")


def _universe_data(s: Settings, timeframe: str, since, refresh: bool) -> dict[str, pd.DataFrame]:
    return {sym: _candles(s, sym, since, refresh=refresh, timeframe=timeframe) for sym in s.universe}


def cmd_freeze(s: Settings, a: argparse.Namespace) -> None:
    from trader.accounts import Account, AccountBook

    now = pd.Timestamp.now(tz="UTC").normalize()
    accounts = []
    for spec in a.spec:
        name, _, tf = spec.partition(":")
        bpd = bars_per_day(tf)
        data = _universe_data(s, tf, now - pd.Timedelta(days=a.train_days), refresh=not a.offline)
        base = get_strategy(name)
        candidates = [base.with_params(**p) for p in param_grid(type(base).grid)] or [base]
        best, res = optimize(data, candidates, objective=a.objective, fallback=base,
                             costs=s.costs, risk=s.risk)
        params = {k: best.params()[k] for k in type(base).grid}
        print(f"{name} {tf}: {params}  (últimos {a.train_days:g} dias, "
              f"calmar {res.metrics.get('calmar', 0):.2f}, {int(a.train_days * bpd)} barras)")
        accounts.append(Account(f"{name}_{tf}", name, tf, params, s.risk.risk_per_trade,
                                s.risk.max_open_positions))
    AccountBook(now.date().isoformat(), accounts).save(a.accounts)
    print(f"\nContas congeladas em {a.accounts}")


def cmd_status(s: Settings, a: argparse.Namespace) -> None:
    from trader.accounts import AccountBook

    book = AccountBook.load(a.accounts)
    market = make_exchange(s.exchange)
    prices = {sym: t["last"] for sym, t in market.fetch_tickers(s.universe).items()}
    rows = []
    for acc in book.accounts:
        st = acc.settings(s).state_dir
        broker_file = st / "paper_broker.json"
        if broker_file.exists():
            state = json.loads(broker_file.read_text())
        elif (st / "agent_paper.json").exists():
            state = {"cash": s.paper_cash, "holdings": {}}  # rodou, mas ainda não operou
        else:
            rows.append({"conta": acc.name, "patrimônio": "ainda não rodou"})
            continue
        holdings = state["holdings"]
        equity = state["cash"] + sum(q * prices.get(sym, 0.0) for sym, q in holdings.items())
        journal = st / "journal.jsonl"
        acts = [json.loads(line)["action"] for line in journal.read_text().splitlines()] \
            if journal.exists() else []
        rows.append({
            "conta": acc.name,
            "patrimônio": f"{equity:,.0f}",
            "resultado": f"{equity / s.paper_cash - 1:+.2%}",
            "posições": ", ".join(sorted(holdings)) or "-",
            "compras": acts.count("buy"),
            "saídas": acts.count("sell") + acts.count("stop"),
        })
    print(f"Paper desde {book.frozen_at}, {s.paper_cash:,.0f} USDT por conta\n")
    print(pd.DataFrame(rows).to_string(index=False))


def cmd_forward(s: Settings, a: argparse.Namespace) -> None:
    from trader.accounts import AccountBook

    book = AccountBook.load(a.accounts)
    rows = []
    for acc in book.accounts:
        strat = acc.build()
        bpd = bars_per_day(acc.timeframe)
        since = book.frozen_ts - pd.Timedelta(days=strat.warmup / bpd * 2 + 5)
        data = _universe_data(s, acc.timeframe, since, refresh=not a.offline)
        if strat.max_funding is not None:
            secs = int(86400 / bpd)
            data = {sym: with_funding(df, sym, secs, data_dir=s.data_dir, refresh=not a.offline)
                    for sym, df in data.items()}
        cfg = acc.settings(s)
        res = run_portfolio(data, strat, costs=s.costs, risk=cfg.risk, trade_from=book.frozen_ts)
        m = res.metrics
        if len(res.equity) < 2:
            rows.append({"conta": acc.name, "total_return": "sem candles novos ainda"})
            continue
        rows.append({"conta": acc.name, **fmt_metrics({k: m.get(k) for k in (
            "total_return", "monthly", "max_drawdown", "trades", "buy_hold") if k in m})})
    print(f"Simulação desde o congelamento ({book.frozen_at}), parâmetros congelados:\n")
    print(pd.DataFrame(rows).fillna("sem dados ainda").to_string(index=False))


def load_equity_curves(s: Settings) -> pd.DataFrame:
    """Curvas fora da amostra salvas pelas baterias (a mais recente vence em nomes repetidos)."""
    files = sorted((s.data_dir / "results").glob("equity_*.csv"))
    if not files:
        sys.exit("Nenhuma curva salva: rode `trader battery` antes")
    c = pd.concat([pd.read_csv(f, index_col="time", parse_dates=["time"]) for f in files],
                  axis=1, sort=True)
    return c.loc[:, ~c.columns.duplicated(keep="last")]


def cmd_regimes(s: Settings, a: argparse.Namespace) -> None:
    from trader.regimes import REGIMES, label_regimes, regime_mix, regime_stats

    bench = _candles(s, a.benchmark, "2018-01-01", refresh=not a.offline, timeframe="1d")["close"]
    labels = label_regimes(bench, a.window, a.bull, a.bear)
    split = pd.Timestamp(a.split, tz="UTC")
    curves = load_equity_curves(s)
    cols = [c for c in curves if c.endswith(a.suffix)]
    start = max(curves[c].first_valid_index() for c in cols)

    mix = pd.DataFrame({
        f"antes de {split.date()}": regime_mix(labels, start, split - pd.Timedelta(days=1)),
        f"desde {split.date()}": regime_mix(labels, split),
    }).T
    print(f"Fases do mercado ({a.benchmark}, variação de {a.window} dias: alta ≥ {a.bull:+.0%}, "
          f"baixa ≤ {a.bear:+.0%}) — fração dos dias:\n")
    print(mix.map(lambda v: f"{v:.0%}").to_string())

    named = {c.removesuffix(a.suffix): curves[c] for c in cols}
    named[f"HOLD {a.benchmark}"] = bench
    rows = []
    for name, eq in named.items():
        eq = eq.loc[start:].dropna()
        before = regime_stats(eq.loc[:split], labels)
        after = regime_stats(eq.loc[split:], labels)
        row = {"": name}
        for r in REGIMES:
            row[f"{r} antes"] = before.loc[r, "mensal"]
            row[f"{r} depois"] = after.loc[r, "mensal"]
        rows.append(row)
    df = pd.DataFrame(rows).set_index("")
    print(f"\nMédia mensal dentro de cada fase, antes vs. desde {split.date()} "
          f"(curvas fora da amostra desde {start.date()}):\n")
    print(df.map(lambda v: f"{v:+.1%}" if pd.notna(v) else "-").to_string())


def cmd_run(s: Settings, a: argparse.Namespace) -> None:
    from trader.agent import SwingAgent
    from trader.broker import ExchangeBroker, PaperBroker

    s.check_live_allowed()
    market = make_exchange(s.exchange)
    if a.accounts:
        from trader.accounts import AccountBook

        for acc in AccountBook.load(a.accounts).accounts:
            cfg = acc.settings(s)
            broker = PaperBroker(cfg.state_dir / "paper_broker.json", market, s.paper_cash,
                                 s.costs.fee_rate, s.costs.slippage)
            agent = SwingAgent(cfg, acc.build(), broker, market, cfg.state_dir / "agent_paper.json",
                               cfg.state_dir / "journal.jsonl")
            for d in agent.run_once(dry_run=a.dry_run):
                if d.action != "hold" or a.verbose:
                    print(f"[{acc.name}] {d.symbol:<10} {d.action:<5} {d.reason} {_extra(d)}")
            print(f"[{acc.name}] ok")
        return
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
        print(f"[{d.mode}] {d.symbol:<10} {d.action:<5} {d.reason} {_extra(d)}")


def _extra(d) -> str:
    return " ".join(f"{k}={v:.6g}" for k, v in (("price", d.price), ("qty", d.qty),
                                                ("stop", d.stop)) if v is not None)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="trader", description=__doc__)
    p.add_argument("--timeframe", help="sobrescreve TRADER_TIMEFRAME (ex.: 1d, 4h)")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="baixa/atualiza candles no cache")
    f.add_argument("--symbols", nargs="*")
    f.add_argument("--since", default="2018-01-01")

    ff = sub.add_parser("fetch-funding", help="baixa/atualiza o histórico de funding dos perpétuos")
    ff.add_argument("--symbols", nargs="*")
    ff.add_argument("--since", default="2019-01-01")

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

    pf = sub.add_parser("portfolio", help="carteira multiativo com caixa compartilhado, como o agente")
    pf.add_argument("--strategy", choices=list(STRATEGIES), help="padrão: todas")
    pf.add_argument("--symbols", nargs="*")
    pf.add_argument("--param", nargs="*", default=[], help="só com --strategy")
    pf.add_argument("--cash", type=float, default=10_000.0)
    pf.add_argument("--no-kill-switch", action="store_true")
    pf.add_argument("--trades", action="store_true")
    common(pf)

    def wf_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--symbols", nargs="*")
        sp.add_argument("--train-days", type=float, default=730, help="dias de otimização por janela")
        sp.add_argument("--test-days", type=float, default=180, help="dias de teste por janela")
        sp.add_argument("--objective", default="calmar",
                        choices=["calmar", "sharpe", "total_return"])
        common(sp)

    w = sub.add_parser("walkforward", help="otimiza e testa fora da amostra, em carteira")
    w.add_argument("--strategy", required=True, choices=list(STRATEGIES))
    wf_args(w)

    bt = sub.add_parser("battery", help="walk-forward de todas as estratégias × timeframes")
    bt.add_argument("--timeframes", nargs="*", default=["1d", "4h"])
    bt.add_argument("--strategies", nargs="*", choices=list(STRATEGIES))
    bt.add_argument("--risk", nargs="*", type=float, help="risco por operação, ex.: 0.01 0.02")
    bt.add_argument("--max-positions", nargs="*", type=int, help="ex.: 3 5")
    wf_args(bt)

    r = sub.add_parser("run", help="executa o agente uma vez (paper/testnet/live conforme .env)")
    r.add_argument("--strategy", choices=list(STRATEGIES))
    r.add_argument("--param", nargs="*", default=[])
    r.add_argument("--dry-run", action="store_true", help="só mostra as decisões, não executa")
    r.add_argument("--accounts", help="arquivo de contas de paper (roda todas, sempre em paper)")
    r.add_argument("--verbose", action="store_true", help="com --accounts, mostra também os 'hold'")

    fz = sub.add_parser("freeze", help="congela contas de paper com os melhores parâmetros de hoje")
    fz.add_argument("--spec", nargs="+", required=True, help="estratégia:timeframe, ex.: donchian:1d")
    fz.add_argument("--accounts", default="config/paper_accounts.json")
    fz.add_argument("--train-days", type=float, default=730)
    fz.add_argument("--objective", default="calmar", choices=["calmar", "sharpe", "total_return"])
    fz.add_argument("--offline", action="store_true")

    stt = sub.add_parser("status", help="patrimônio atual de cada conta de paper")
    stt.add_argument("--accounts", default="config/paper_accounts.json")

    rg = sub.add_parser("regimes", help="resultado das estratégias por fase do mercado")
    rg.add_argument("--benchmark", default="BTC/USDT")
    rg.add_argument("--window", type=int, default=90, help="dias da variação que define a fase")
    rg.add_argument("--bull", type=float, default=0.20)
    rg.add_argument("--bear", type=float, default=-0.20)
    rg.add_argument("--split", default="2024-01-01", help="data que separa antes/depois")
    rg.add_argument("--suffix", default="_r0.01_p3", help="quais curvas da bateria usar")
    rg.add_argument("--offline", action="store_true")

    fw = sub.add_parser("forward", help="simula cada conta congelada desde a data de congelamento")
    fw.add_argument("--accounts", default="config/paper_accounts.json")
    fw.add_argument("--offline", action="store_true")

    a = p.parse_args(argv)
    s = Settings.from_env()
    if a.timeframe:
        s.timeframe = a.timeframe
    {"fetch": cmd_fetch, "fetch-funding": cmd_fetch_funding, "backtest": cmd_backtest, "compare": cmd_compare, "portfolio": cmd_portfolio,
     "walkforward": cmd_walkforward, "battery": cmd_battery, "run": cmd_run,
     "freeze": cmd_freeze, "status": cmd_status, "forward": cmd_forward,
     "regimes": cmd_regimes}[a.cmd](s, a)


if __name__ == "__main__":
    main()
