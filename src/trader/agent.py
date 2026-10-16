"""Agente de swing: roda uma vez por candle fechado (ex.: diário, via cron) e decide por ativo.

Para cada ativo, em ordem:
1. Posição aberta e stop executado → registra a saída.
2. Posição aberta e sinal de saída → vende e cancela o stop.
3. Posição aberta sem sinal → sobe o trailing stop se o preço subiu.
4. Sem posição e sinal de entrada → dimensiona pelo risco, compra e coloca o stop.

Nenhuma decisão vem de LLM: tudo sai da estratégia determinística e das regras de risco.
"""

from __future__ import annotations

import json
from pathlib import Path

import ccxt
import pandas as pd

from trader import journal
from trader.broker import Broker
from trader.config import Settings
from trader.data import load_candles
from trader.journal import Decision
from trader.risk import drawdown, position_size
from trader.strategies import Strategy


class SwingAgent:
    def __init__(self, settings: Settings, strategy: Strategy, broker: Broker,
                 market: ccxt.Exchange, state_path: Path, journal_path: Path):
        self.s = settings
        self.strategy = strategy
        self.broker = broker
        self.market = market
        self.state_path = Path(state_path)
        self.journal_path = Path(journal_path)
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return {"positions": {}, "last_bar": {}, "peak_equity": 0.0}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2))

    def candles(self, symbol: str) -> pd.DataFrame:
        tf_s = self.market.parse_timeframe(self.s.timeframe)
        since = pd.Timestamp.now(tz="UTC") - pd.Timedelta(seconds=tf_s * self.strategy.warmup * 3)
        return load_candles(symbol, self.s.timeframe, since, exchange_id=self.s.exchange,
                            data_dir=self.s.data_dir, ex=self.market)

    def run_once(self, dry_run: bool = False) -> list[Decision]:
        frames = {sym: self.strategy.generate(self.candles(sym)) for sym in self.s.symbols}
        positions: dict = self.state["positions"]
        cash = self.broker.cash()
        equity = cash + sum(p["qty"] * float(frames[sym]["close"].iloc[-1])
                            for sym, p in positions.items() if sym in frames)
        self.state["peak_equity"] = max(self.state.get("peak_equity", 0.0), equity)
        dd = drawdown(equity, self.state["peak_equity"])
        killed = dd > self.s.risk.max_drawdown

        decisions = []
        for sym, sig in frames.items():
            d = self._decide(sym, sig, equity, killed, dd, dry_run)
            d.mode = self.s.mode + (" (dry-run)" if dry_run else "")
            decisions.append(d)

        if not dry_run:
            self._save_state()
            journal.append(self.journal_path, decisions)
        return decisions

    def _decide(self, sym: str, sig: pd.DataFrame, equity: float, killed: bool, dd: float,
                dry_run: bool) -> Decision:
        last = sig.iloc[-1]
        bar = sig.index[-1].isoformat()
        mult = self.strategy.stop_atr_mult
        positions = self.state["positions"]
        pos = positions.get(sym)

        if self.state["last_bar"].get(sym) == bar:
            return Decision(sym, "hold", "barra já processada", bar)
        if not dry_run:
            self.state["last_bar"][sym] = bar

        if pos:
            new_bars = sig[sig.index > pd.Timestamp(pos["last_checked"])]
            fill = None if dry_run else self.broker.stop_fill(
                sym, pos["qty"], pos["stop"], pos.get("stop_order_id"), new_bars)
            if fill:
                positions.pop(sym)
                return Decision(sym, "stop", "stop executado", bar, fill.price, fill.qty, pos["stop"])
            if not dry_run:
                pos["last_checked"] = bar

            # Se o agente ficou dias sem rodar, um sinal de saída em qualquer barra perdida vale.
            # Entrada só no último candle: não persegue sinal velho.
            if new_bars["exit"].any():
                if dry_run:
                    return Decision(sym, "sell", "sinal de saída", bar, float(last["close"]), pos["qty"])
                self.broker.cancel_protection(sym, pos.get("stop_order_id"))
                fill = self.broker.sell(sym, pos["qty"])
                positions.pop(sym)
                return Decision(sym, "sell", "sinal de saída", bar, fill.price, fill.qty)

            trail = float(last["close"]) - mult * float(last["atr"])
            if trail > pos["stop"]:
                if not dry_run:
                    pos["stop_order_id"] = self.broker.protect(sym, pos["qty"], trail,
                                                               pos.get("stop_order_id"))
                    pos["stop"] = trail
                return Decision(sym, "trail", "stop sobe com o preço", bar, float(last["close"]),
                                pos["qty"], trail)
            return Decision(sym, "hold", "posição aberta, sem sinal", bar, float(last["close"]),
                            pos["qty"], pos["stop"])

        if not last["entry"]:
            return Decision(sym, "hold", "sem sinal de entrada", bar, float(last["close"]))
        if killed:
            return Decision(sym, "skip", f"kill switch: drawdown de {dd:.1%}", bar)
        if len(positions) >= self.s.risk.max_open_positions:
            return Decision(sym, "skip", "limite de posições abertas", bar)

        price = self.broker.last_price(sym)
        stop = price - mult * float(last["atr"])
        qty = position_size(equity, price, stop, self.broker.cash(), self.s.risk, self.s.costs.fee_rate)
        if qty <= 0:
            return Decision(sym, "skip", "tamanho de posição abaixo do mínimo", bar, price)
        if dry_run:
            return Decision(sym, "buy", "sinal de entrada", bar, price, qty, stop)

        fill = self.broker.buy(sym, qty)
        stop_id = self.broker.protect(sym, fill.qty, stop, None)
        positions[sym] = {
            "qty": fill.qty, "entry_price": fill.price, "entry_bar": bar, "stop": stop,
            "stop_order_id": stop_id, "last_checked": bar,
        }
        return Decision(sym, "buy", "sinal de entrada", bar, fill.price, fill.qty, stop)
