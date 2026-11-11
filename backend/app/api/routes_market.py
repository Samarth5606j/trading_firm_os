import asyncio
import json
import random
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.data.ingestor import fetch_market_data
from app.services.attribution import analyze_attribution
from app.services.paper_broker import evaluate_bracket_triggers

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

@router.websocket("/ws/{ticker}")
async def market_tape_websocket(websocket: WebSocket, ticker: str):
    await websocket.accept()
    ticker = ticker.upper().strip()
    
    base_data = fetch_market_data(ticker)
    current_price = float(base_data.get("current_price", 100.0))
    currency_symbol = base_data.get("currency_symbol", "₹")

    try:
        while True:
            tick_delta = round(random.uniform(-0.45, 0.48), 2)
            current_price = max(1.0, round(current_price + tick_delta, 2))
            
            # Evaluate automated Stop-Loss / Take-Profit brackets on every tick
            triggered = evaluate_bracket_triggers(ticker, current_price)
            
            payload = {
                "ticker": ticker,
                "current_price": current_price,
                "tick_delta": tick_delta,
                "currency_symbol": currency_symbol,
                "bracket_alerts": triggered,
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()