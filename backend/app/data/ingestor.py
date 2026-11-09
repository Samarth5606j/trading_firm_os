import yfinance as yf
import pandas as pd

def fetch_market_data(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    is_indian = ticker.endswith((".NS", ".BO"))
    currency = "₹" if is_indian else "$"

    stock = yf.Ticker(ticker)
    df = stock.history(period="6mo")
    if df.empty or len(df) < 50:
        raise ValueError(f"Insufficient historical data available for ticker '{ticker}'.")

    df = df.dropna(subset=['Close', 'Open', 'High', 'Low']).copy()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    valid = df.dropna(subset=['Close', 'SMA_20', 'SMA_50']).copy()
    latest = valid.iloc[-1]
    prev = valid.iloc[-2]
    change_pct = round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2)

    pe_ratio = 0.0
    try:
        pe_ratio = round(float(stock.info.get('trailingPE') or stock.info.get('forwardPE') or 0.0), 2)
    except Exception:
        pe_ratio = 0.0

    candles = [
        {
            "time": str(idx.date()),
            "close": round(float(row['Close']), 2),
            "sma_20": round(float(row['SMA_20']), 2),
            "sma_50": round(float(row['SMA_50']), 2),
        }
        for idx, row in valid.tail(60).iterrows()
    ]

    return {
        "ticker": ticker,
        "currency_symbol": currency,
        "current_price": round(float(latest['Close']), 2),
        "change_pct": change_pct,
        "rsi": round(float(latest['RSI']), 2) if pd.notna(latest['RSI']) else 50.0,
        "sma_20": round(float(latest['SMA_20']), 2),
        "sma_50": round(float(latest['SMA_50']), 2),
        "pe_ratio": pe_ratio,
        "df": valid,
        "candles": candles
    }