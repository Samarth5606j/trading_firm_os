from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.models import SessionLocal, Portfolio, PaperOrder
from app.services.paper_broker import execute_paper_order

router = APIRouter(prefix="/api/paper", tags=["paper"])

class OrderPayload(BaseModel):
    ticker: str
    action: str
    quantity: int
    current_price: float

@router.post("/order")
def place_paper_order(payload: OrderPayload):
    result = execute_paper_order(
        ticker=payload.ticker,
        action=payload.action,
        quantity=payload.quantity,
        current_price=payload.current_price,
    )
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Order failed."))
    return result

@router.get("/portfolio")
def get_portfolio():
    db = SessionLocal()
    portfolio = db.query(Portfolio).first()
    orders = db.query(PaperOrder).order_by(PaperOrder.timestamp.desc()).limit(10).all()
    recent = [
        {
            "id": o.id, "ticker": o.ticker, "action": o.action, "quantity": o.quantity,
            "executed_price": o.executed_price, "stop_loss": o.stop_loss,
            "take_profit": o.take_profit, "fee": o.brokerage_fee, "status": o.status,
        }
        for o in orders
    ]
    res = {
        "inr_cash": round(portfolio.inr_cash, 2),
        "usd_cash": round(portfolio.usd_cash, 2),
        "total_trades": portfolio.total_trades,
        "recent_orders": recent,
    }
    db.close()
    return res