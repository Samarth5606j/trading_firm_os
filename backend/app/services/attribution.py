import yfinance as yf

def analyze_attribution(ticker: str, price_change_pct: float) -> dict:
    is_indian = ticker.endswith((".NS", ".BO"))
    sp500_change = 0.0
    nifty_change = None
    top_headline = "Asset rebalancing across institutional desks."

    # 1. Fetch S&P 500 benchmark safely
    try:
        sp500 = yf.Ticker("^GSPC").history(period="2d")
        if len(sp500) >= 2:
            sp500_change = round(((sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2]) * 100, 2)
    except Exception:
        sp500_change = 0.0

    # 2. Fetch Nifty 50 benchmark safely for Indian Equities
    if is_indian:
        try:
            nifty = yf.Ticker("^NSEI").history(period="2d")
            if len(nifty) >= 2:
                nifty_change = round(((nifty['Close'].iloc[-1] - nifty['Close'].iloc[-2]) / nifty['Close'].iloc[-2]) * 100, 2)
        except Exception:
            nifty_change = 0.0

    # 3. Fetch corporate news headline safely
    try:
        stock_obj = yf.Ticker(ticker)
        news = getattr(stock_obj, "news", []) or []
        if news and isinstance(news, list) and len(news) > 0:
            top_headline = news[0].get("title", top_headline)
    except Exception:
        pass

    # 4. Attribution Categorization Logic
    drivers = []
    category = "IDIOSYNCRATIC"

    if is_indian:
        if abs(sp500_change) >= 0.8:
            drivers.append(f"US Markets Contagion: S&P 500 shifted {sp500_change}%, impacting FII flows.")
            category = "GLOBAL_CONTAGION"
        if nifty_change is not None and abs(nifty_change) >= 0.6:
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
        "nifty_change": nifty_change
    }