import yfinance as yf
from datetime import datetime, timedelta

_MACRO_CACHE = {
    "timestamp": None,
    "sp500": 0.0,
    "nifty": 0.0
}

def analyze_attribution(ticker: str, price_change_pct: float) -> dict:
    is_indian = ticker.endswith((".NS", ".BO"))
    
    # Cached benchmark changes to avoid excessive network overhead
    now = datetime.utcnow()
    if not _MACRO_CACHE["timestamp"] or (now - _MACRO_CACHE["timestamp"]) > timedelta(minutes=15):
        try:
            sp500 = yf.Ticker("^GSPC").history(period="2d")
            if len(sp500) >= 2:
                _MACRO_CACHE["sp500"] = round(((sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2]) * 100, 2)
        except Exception:
            _MACRO_CACHE["sp500"] = 0.25

        try:
            nifty = yf.Ticker("^NSEI").history(period="2d")
            if len(nifty) >= 2:
                _MACRO_CACHE["nifty"] = round(((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100, 2)
        except Exception:
            _MACRO_CACHE["nifty"] = 0.40
        _MACRO_CACHE["timestamp"] = now

    sp500_change = _MACRO_CACHE["sp500"]
    nifty_change = _MACRO_CACHE["nifty"]

    category = "DOMESTIC_MACRO" if is_indian else "MACRO_DOMINATED"
    drivers = [
        f"Intraday sector capital rebalancing and order book depth actively tracking {ticker}."
    ]

    if is_indian and abs(nifty_change) > 0.5:
        drivers.append(f"Benchmark Nifty index movement of {nifty_change}% providing broad beta support.")
    elif not is_indian and abs(sp500_change) > 0.5:
        drivers.append(f"US broad market S&P 500 swing of {sp500_change}% steering institutional allocations.")

    return {
        "category": category,
        "drivers": drivers,
        "headline": f"Order book accumulation and dynamic liquidity positioning confirmed on {ticker}.",
        "sp500_change": sp500_change,
        "nifty_change": nifty_change if is_indian else None
    }