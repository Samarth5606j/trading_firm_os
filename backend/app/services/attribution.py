import yfinance as yf
from datetime import datetime, timedelta

# Simple in-memory cache for macro benchmark moves to prevent redundant downloads
_MACRO_CACHE = {
    "timestamp": None,
    "sp500": 0.0,
    "nifty": 0.0
}

def _get_benchmark_changes():
    now = datetime.utcnow()
    if _MACRO_CACHE["timestamp"] and (now - _MACRO_CACHE["timestamp"]) < timedelta(minutes=15):
        return _MACRO_CACHE["sp500"], _MACRO_CACHE["nifty"]

    sp500_change = 0.0
    nifty_change = 0.0

    try:
        sp500 = yf.Ticker("^GSPC").history(period="2d")
        if len(sp500) >= 2:
            sp500_change = round(((sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2]) * 100, 2)
    except Exception:
        pass

    try:
        nifty = yf.Ticker("^NSEI").history(period="2d")
        if len(nifty) >= 2:
            nifty_change = round(((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100, 2)
    except Exception:
        pass

    _MACRO_CACHE["sp500"] = sp500_change
    _MACRO_CACHE["nifty"] = nifty_change
    _MACRO_CACHE["timestamp"] = now
    return sp500_change, nifty_change


def analyze_attribution(ticker: str, price_change_pct: float) -> dict:
    is_indian = ticker.endswith((".NS", ".BO"))
    sp500_change, nifty_change = _get_benchmark_changes()
    
    top_headline = "Asset rebalancing across institutional desks."
    try:
        stock_obj = yf.Ticker(ticker)
        # Fast read of news without hanging
        news = getattr(stock_obj, "news", []) or []
        if news and isinstance(news, list) and len(news) > 0:
            top_headline = news[0].get("title", top_headline)
    except Exception:
        pass

    drivers = []
    category = "IDIOSYNCRATIC"

    if is_indian:
        if abs(sp500_change) >= 0.8:
            drivers.append(f"US Markets Contagion: S&P 500 shifted {sp500_change}%, impacting FII flows.")
            category = "GLOBAL_CONTAGION"
        if abs(nifty_change) >= 0.6:
            drivers.append(f"Domestic Index Momentum: Nifty 50 moved {nifty_change}%, carrying high-beta components.")
            category = "DOMESTIC_MACRO"
    else:
        if abs(sp500_change) >= 1.0:
            drivers.append(f"Broader US Index Trend: S&P 500 recorded a {sp500_change}% swing, dominating single-stock beta.")
            category = "MACRO_DOMINATED"

    if not drivers:
        drivers.append("Asset movement is decoupled from broader macro indices; price action driven by asset-specific order book volume.")

    return {
        "category": category,
        "drivers": drivers,
        "headline": top_headline,
        "sp500_change": sp500_change,
        "nifty_change": nifty_change if is_indian else None
    }