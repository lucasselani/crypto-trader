from trader.accounts import Account, AccountBook
from trader.config import Settings


def test_account_book_roundtrip_and_settings(tmp_path):
    book = AccountBook("2026-10-17", [
        Account("donchian_1d", "donchian", "1d", {"entry_n": 40}, 0.02, 5),
        Account("ema_cross_4h", "ema_cross", "4h"),
    ])
    path = tmp_path / "accounts.json"
    book.save(path)
    loaded = AccountBook.load(path)
    assert loaded == book
    assert loaded.accounts[0].build().entry_n == 40

    base = Settings(mode="testnet", state_dir=tmp_path)
    cfg = loaded.accounts[0].settings(base)
    assert cfg.mode == "paper"  # contas congeladas nunca operam real
    assert cfg.timeframe == "1d" and cfg.symbols == base.universe
    assert cfg.risk.risk_per_trade == 0.02 and cfg.risk.max_open_positions == 5
    assert cfg.state_dir == tmp_path / "accounts" / "donchian_1d"
    assert base.risk.risk_per_trade == 0.01  # não altera a configuração original
