from dataclasses import dataclass
from typing import ClassVar

import pandas as pd

from tests.conftest import make_candles
from trader.agent import SwingAgent
from trader.broker import PaperBroker
from trader.config import Settings
from trader.risk import RiskConfig
from trader.strategies import Strategy


@dataclass(frozen=True)
class Toggle(Strategy):
    want_entry: bool = True
    want_exit: bool = False
    atr_period: int = 2
    stop_atr_mult: float = 2.0
    name: ClassVar[str] = "toggle"

    @property
    def warmup(self) -> int:
        return 3

    def signals(self, df):
        return (pd.Series(self.want_entry, index=df.index),
                pd.Series(self.want_exit, index=df.index))


class FakeMarket:
    def __init__(self, price):
        self.price = price

    def fetch_ticker(self, symbol):
        return {"last": self.price}

    def parse_timeframe(self, tf):
        return 86400


def make_agent(tmp_path, strategy, candles, price=100.0):
    s = Settings(symbols=["BTC/USDT"], risk=RiskConfig(max_position_pct=0.5), state_dir=tmp_path)
    market = FakeMarket(price)
    broker = PaperBroker(tmp_path / "paper.json", market, 10_000, 0.001, 0.0)
    agent = SwingAgent(s, strategy, broker, market, tmp_path / "agent.json", tmp_path / "j.jsonl")
    agent.candles = lambda sym: candles
    return agent, broker


def test_buys_on_entry_and_is_idempotent(tmp_path):
    candles = make_candles([100.0] * 10)
    agent, broker = make_agent(tmp_path, Toggle(), candles)
    d = agent.run_once()[0]
    assert d.action == "buy" and d.qty > 0 and d.stop < 100
    assert broker.cash() < 10_000
    assert agent.run_once()[0].reason == "barra já processada"
    assert (tmp_path / "j.jsonl").read_text().count("\n") == 2


def test_dry_run_changes_nothing(tmp_path):
    agent, broker = make_agent(tmp_path, Toggle(), make_candles([100.0] * 10))
    assert agent.run_once(dry_run=True)[0].action == "buy"
    assert broker.cash() == 10_000 and not agent.state["positions"]
    assert not (tmp_path / "j.jsonl").exists()


def test_paper_stop_triggers_on_new_bar(tmp_path):
    candles = make_candles([100.0] * 10)
    agent, broker = make_agent(tmp_path, Toggle(), candles)
    agent.run_once()
    stop = agent.state["positions"]["BTC/USDT"]["stop"]
    crash = make_candles([100.0] * 10 + [stop * 0.9])
    agent.candles = lambda sym: crash
    agent.strategy = Toggle(want_entry=False)
    d = agent.run_once()[0]
    assert d.action == "stop"
    assert not agent.state["positions"] and "BTC/USDT" not in broker.state["holdings"]


def test_exit_signal_sells(tmp_path):
    agent, broker = make_agent(tmp_path, Toggle(), make_candles([100.0] * 10))
    agent.run_once()
    agent.candles = lambda sym: make_candles([100.0] * 11)
    agent.strategy = Toggle(want_entry=False, want_exit=True)
    assert agent.run_once()[0].action == "sell"
    assert not broker.state["holdings"]


def test_kill_switch_blocks_entries(tmp_path):
    agent, _ = make_agent(tmp_path, Toggle(), make_candles([100.0] * 10))
    agent.state["peak_equity"] = 20_000  # patrimônio caiu 50%
    d = agent.run_once()[0]
    assert d.action == "skip" and "kill switch" in d.reason
