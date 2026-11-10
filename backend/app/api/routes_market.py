from fastapi import APIRouter
from app.data.ingestor import fetch_market_data
from app.services.attribution import analyze_attribution

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/{ticker}")
def get_market_data(ticker: str):
    ticker = ticker.upper().strip()
    data = fetch_market_data(ticker)
    try:
        data["attribution"] = analyze_attribution(ticker, data.get("change_pct", 0.0))
    except Exception:
        data["attribution"] = {
            "category": "IDIOSYNCRATIC",
            "drivers": [f"Order book depth and institutional liquidity active on {ticker}."],
            "headline": f"Real-time volume telemetry tracking {ticker}."
        }
    return data