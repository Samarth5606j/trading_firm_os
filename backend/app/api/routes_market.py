from fastapi import APIRouter, HTTPException
from app.data.ingestor import fetch_market_data
from app.services.attribution import analyze_attribution

router = APIRouter(prefix="/api/market", tags=["market"])

@router.get("/{ticker}")
def get_market_overview(ticker: str):
    try:
        data = fetch_market_data(ticker)
        attribution = analyze_attribution(ticker, data["change_pct"])
        return {
            "ticker": data["ticker"],
            "currency": data["currency_symbol"],
            "current_price": data["current_price"],
            "change_pct": data["change_pct"],
            "rsi": data["rsi"],
            "sma_20": data["sma_20"],
            "sma_50": data["sma_50"],
            "pe_ratio": data["pe_ratio"],
            "attribution": attribution,
            "candles": data["candles"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))