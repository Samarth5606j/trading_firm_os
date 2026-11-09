import yfinance as yf
import pandas as pd

_DATA_CACHE = {}

def fetch_market_data(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    is_indian = ticker.endswith((".NS", ".BO"))
    currency = "₹" if is_indian else "$"

    # Fetch 3 months of daily data (sufficient for 50 SMA and 14 RSI)
    stock = yf.Ticker(ticker)
    df = stock.history(period="3mo")

    if df.empty or len(df) < 5:
        # Fallback to 6mo if 3mo is somehow sparse
        df = stock.history(period="6mo")

    if df.empty or len(df) < 5:
        raise ValueError(f"Could not retrieve trading history for {ticker}. Verify ticker validity.")

    df = df.dropna(subset=['Close']).copy()

    # Dynamic SMAs
    df['SMA_20'] = df['Close'].rolling(window=min(20, len(df))).mean().bfill()
    df['SMA_50'] = df['Close'].rolling(window=min(50, len(df))).mean().bfill()

    # RSI (14)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=min(14, len(df))).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=min(14, len(df))).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = (100 - (100 / (1 + rs))).fillna(50.0)

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else latest

    change_pct = 0.0
    if prev['Close'] > 0:
        change_pct = round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2)

    pe_ratio = 0.0
    try:
        fast_info = getattr(stock, 'fast_info', None)
        if fast_info and hasattr(fast_info, 'pe_ratio') and fast_info.pe_ratio:
            pe_ratio = round(float(fast_info.pe_ratio), 2)
        else:
            info = getattr(stock, 'info', {}) or {}
            pe_ratio = round(float(info.get('trailingPE') or info.get('forwardPE') or 0.0), 2)
    except Exception:
        pe_ratio = 0.0

    candles = [
        {
            "time": str(idx.date()),
            "close": round(float(row['Close']), 2),
            "sma_20": round(float(row['SMA_20']), 2),
            "sma_50": round(float(row['SMA_50']), 2),
        }
        for idx, row in df.tail(60).iterrows()
    ]

    return {
        "ticker": ticker,
        "currency_symbol": currency,
        "current_price": round(float(latest['Close']), 2),
        "change_pct": change_pct,
        "rsi": round(float(latest['RSI']), 2),
        "sma_20": round(float(latest['SMA_20']), 2),
        "sma_50": round(float(latest['SMA_50']), 2),
        "pe_ratio": pe_ratio,
        "df": df,
        "candles": candles
    }