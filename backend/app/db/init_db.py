"""
Seeds data/stock_data.db with a small SQLite database for the
Text-to-SQL agent to query.

IMPORTANT: this data is SYNTHETICALLY GENERATED (a seeded random walk),
NOT real Tata Steel financial data. It exists purely so the Text-to-SQL
agent has a real, queryable database to demo against out of the box.
Do NOT present numbers pulled from this database as real Tata Steel
figures anywhere (portfolio write-up, interview, demo narration) —
always caveat it as synthetic sample data, or swap in a real market
data feed (e.g. NSE/BSE historical data, Alpha Vantage, yfinance)
before using this for anything beyond exercising the pipeline.

Run directly to (re)build the DB:
    python -m app.db.init_db
"""
from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from app.config import settings

TICKER = "TATASTEEL"
START_PRICE = 145.0
NUM_TRADING_DAYS = 500
SEED = 42


def _generate_ohlcv(num_days: int, start_price: float, seed: int) -> list[tuple]:
    rng = random.Random(seed)
    rows = []
    price = start_price
    d = date.today() - timedelta(days=int(num_days * 1.45))  # ~ num_days weekdays back

    while len(rows) < num_days:
        if d.weekday() < 5:  # skip weekends
            drift = rng.uniform(-0.018, 0.021)
            price = max(price * (1 + drift), 1.0)
            open_p = price * (1 + rng.uniform(-0.005, 0.005))
            close_p = price
            high_p = max(open_p, close_p) * (1 + rng.uniform(0.0, 0.012))
            low_p = min(open_p, close_p) * (1 - rng.uniform(0.0, 0.012))
            volume = rng.randint(4_000_000, 22_000_000)
            rows.append(
                (
                    d.isoformat(),
                    TICKER,
                    round(open_p, 2),
                    round(high_p, 2),
                    round(low_p, 2),
                    round(close_p, 2),
                    volume,
                )
            )
        d += timedelta(days=1)
    return rows


def _generate_quarterly_financials(seed: int) -> list[tuple]:
    rng = random.Random(seed + 1)
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    years = [2023, 2024, 2025, 2026]
    rows = []
    revenue = 55000.0  # in INR crore, synthetic starting point
    for year in years:
        for q in quarters:
            revenue *= 1 + rng.uniform(-0.03, 0.06)
            ebitda_margin = rng.uniform(0.11, 0.19)
            ebitda = revenue * ebitda_margin
            net_profit = ebitda * rng.uniform(0.35, 0.55)
            rows.append(
                (
                    f"{q} FY{year}",
                    TICKER,
                    round(revenue, 1),
                    round(ebitda, 1),
                    round(ebitda_margin * 100, 2),
                    round(net_profit, 1),
                )
            )
    return rows


def build_database(db_path: str | None = None, force: bool = False) -> str:
    path = db_path or str(settings.sqlite_path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS stock_prices" if force else "SELECT 1")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_prices (
            trade_date TEXT NOT NULL,
            ticker TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL,
            volume INTEGER,
            PRIMARY KEY (trade_date, ticker)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS quarterly_financials (
            quarter TEXT NOT NULL,
            ticker TEXT NOT NULL,
            revenue_cr REAL,
            ebitda_cr REAL,
            ebitda_margin_pct REAL,
            net_profit_cr REAL,
            PRIMARY KEY (quarter, ticker)
        )
        """
    )

    cur.execute("SELECT COUNT(*) FROM stock_prices")
    if cur.fetchone()[0] == 0 or force:
        cur.execute("DELETE FROM stock_prices")
        cur.executemany(
            "INSERT INTO stock_prices VALUES (?,?,?,?,?,?,?)",
            _generate_ohlcv(NUM_TRADING_DAYS, START_PRICE, SEED),
        )

    cur.execute("SELECT COUNT(*) FROM quarterly_financials")
    if cur.fetchone()[0] == 0 or force:
        cur.execute("DELETE FROM quarterly_financials")
        cur.executemany(
            "INSERT INTO quarterly_financials VALUES (?,?,?,?,?,?)",
            _generate_quarterly_financials(SEED),
        )

    conn.commit()
    conn.close()
    return path


SCHEMA_DESCRIPTION = """\
Table: stock_prices
  trade_date TEXT (YYYY-MM-DD), ticker TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER
  One row per trading day. Currently only contains ticker = 'TATASTEEL'.

Table: quarterly_financials
  quarter TEXT (e.g. 'Q1 FY2026'), ticker TEXT, revenue_cr REAL, ebitda_cr REAL,
  ebitda_margin_pct REAL, net_profit_cr REAL
  Figures are in INR crore. One row per fiscal quarter.
"""

if __name__ == "__main__":
    p = build_database(force=True)
    print(f"Built synthetic stock DB at {p}")
    conn = sqlite3.connect(p)
    print("stock_prices rows:", conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0])
    print("quarterly_financials rows:", conn.execute("SELECT COUNT(*) FROM quarterly_financials").fetchone()[0])
    print("\nSample rows:")
    for row in conn.execute("SELECT * FROM stock_prices ORDER BY trade_date DESC LIMIT 3"):
        print(" ", row)
    conn.close()
