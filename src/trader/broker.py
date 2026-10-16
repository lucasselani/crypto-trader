"""Execução de ordens. Mesma interface para o simulador local (paper) e para a exchange via ccxt
(testnet ou real): trocar de modo é só configuração."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import ccxt
import pandas as pd


@dataclass
class Fill:
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    order_id: str | None = None


class Broker(ABC):
    @abstractmethod
    def cash(self) -> float:
        """Saldo na moeda de cotação (ex.: USDT)."""

    @abstractmethod
    def last_price(self, symbol: str) -> float: ...

    @abstractmethod
    def buy(self, symbol: str, qty: float) -> Fill: ...

    @abstractmethod
    def sell(self, symbol: str, qty: float) -> Fill: ...

    @abstractmethod
    def protect(self, symbol: str, qty: float, stop: float, previous_id: str | None) -> str | None:
        """Coloca (ou move) o stop de proteção. Retorna o id da ordem, se houver ordem real."""

    @abstractmethod
    def cancel_protection(self, symbol: str, order_id: str | None) -> None: ...

    @abstractmethod
    def stop_fill(
        self, symbol: str, qty: float, stop: float, order_id: str | None, bars: pd.DataFrame
    ) -> Fill | None:
        """Retorna o fill se o stop foi executado desde a última checagem."""


class PaperBroker(Broker):
    """Simulador local: saldo em JSON, preços reais, taxas e slippage do CostModel.
    O stop é virtual: considerado executado se a mínima de algum candle novo tocou nele."""

    def __init__(self, state_path: Path, market: ccxt.Exchange, initial_cash: float,
                 fee_rate: float, slippage: float):
        self.path = Path(state_path)
        self.market = market
        self.fee_rate, self.slippage = fee_rate, slippage
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
        else:
            self.state = {"cash": initial_cash, "holdings": {}}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, indent=2))

    def cash(self) -> float:
        return float(self.state["cash"])

    def last_price(self, symbol: str) -> float:
        return float(self.market.fetch_ticker(symbol)["last"])

    def _fill(self, symbol: str, side: str, qty: float, ref: float) -> Fill:
        price = ref * (1 + self.slippage if side == "buy" else 1 - self.slippage)
        fee = qty * price * self.fee_rate
        holdings = self.state["holdings"]
        if side == "buy":
            self.state["cash"] -= qty * price + fee
            holdings[symbol] = holdings.get(symbol, 0.0) + qty
        else:
            self.state["cash"] += qty * price - fee
            holdings[symbol] = holdings.get(symbol, 0.0) - qty
            if holdings[symbol] <= 1e-12:
                holdings.pop(symbol)
        self.save()
        return Fill(symbol, side, qty, price, fee)

    def buy(self, symbol: str, qty: float) -> Fill:
        return self._fill(symbol, "buy", qty, self.last_price(symbol))

    def sell(self, symbol: str, qty: float) -> Fill:
        return self._fill(symbol, "sell", qty, self.last_price(symbol))

    def protect(self, symbol, qty, stop, previous_id):
        return None

    def cancel_protection(self, symbol, order_id):
        return None

    def stop_fill(self, symbol, qty, stop, order_id, bars):
        hit = bars[bars["low"] <= stop]
        if hit.empty:
            return None
        ref = min(float(hit["open"].iloc[0]), stop)
        return self._fill(symbol, "sell", qty, ref)


class ExchangeBroker(Broker):
    """Ordens reais via ccxt (testnet ou conta real). O stop fica na exchange como STOP_LOSS_LIMIT,
    para proteger a posição mesmo com o bot desligado."""

    STOP_LIMIT_GAP = 0.01  # limite 1% abaixo do gatilho; gaps maiores podem não executar

    def __init__(self, ex: ccxt.Exchange, quote: str):
        self.ex = ex
        self.quote = quote
        self.ex.load_markets()

    def cash(self) -> float:
        return float(self.ex.fetch_balance()["total"].get(self.quote, 0.0))

    def last_price(self, symbol: str) -> float:
        return float(self.ex.fetch_ticker(symbol)["last"])

    def _to_fill(self, symbol: str, side: str, order: dict) -> Fill:
        base = self.ex.market(symbol)["base"]
        qty = float(order.get("filled") or order.get("amount") or 0.0)
        fee_cost = 0.0
        for fee in order.get("fees") or ([order["fee"]] if order.get("fee") else []):
            if fee and fee.get("cost"):
                fee_cost += float(fee["cost"])
                if side == "buy" and fee.get("currency") == base:
                    qty -= float(fee["cost"])  # taxa cobrada no ativo comprado
        return Fill(symbol, side, qty, float(order.get("average") or order.get("price") or 0.0),
                    fee_cost, str(order.get("id")))

    def buy(self, symbol: str, qty: float) -> Fill:
        amount = float(self.ex.amount_to_precision(symbol, qty))
        order = self.ex.create_order(symbol, "market", "buy", amount)
        return self._to_fill(symbol, "buy", self.ex.fetch_order(order["id"], symbol))

    def sell(self, symbol: str, qty: float) -> Fill:
        amount = float(self.ex.amount_to_precision(symbol, qty))
        order = self.ex.create_order(symbol, "market", "sell", amount)
        return self._to_fill(symbol, "sell", self.ex.fetch_order(order["id"], symbol))

    def protect(self, symbol, qty, stop, previous_id):
        self.cancel_protection(symbol, previous_id)
        amount = float(self.ex.amount_to_precision(symbol, qty))
        trigger = float(self.ex.price_to_precision(symbol, stop))
        limit = float(self.ex.price_to_precision(symbol, stop * (1 - self.STOP_LIMIT_GAP)))
        order = self.ex.create_order(symbol, "limit", "sell", amount, limit,
                                     {"stopLossPrice": trigger, "timeInForce": "GTC"})
        return str(order["id"])

    def cancel_protection(self, symbol, order_id):
        if not order_id:
            return
        try:
            self.ex.cancel_order(order_id, symbol)
        except ccxt.OrderNotFound:
            pass

    def stop_fill(self, symbol, qty, stop, order_id, bars):
        if not order_id:
            return None
        order = self.ex.fetch_order(order_id, symbol)
        if order.get("status") == "closed":
            return self._to_fill(symbol, "sell", order)
        return None
