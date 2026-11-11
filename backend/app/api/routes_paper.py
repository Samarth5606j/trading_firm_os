from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.models import SessionLocal, Portfolio, Order
from app.services.paper_broker import execute_paper_order

router = APIRouter(prefix="/api/paper", tags=["Paper Broker"])

class OrderRequest(BaseModel):
    ticker: str
    action: str
    quantity: int
    current_price: float

@router.post("/order")
def create_order(req: OrderRequest):
    try:
        return execute_paper_order(req.ticker, req.action, req.quantity, req.current_price)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
def get_portfolio():
    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.id == 1).first()
        orders = db.query(Order).order_by(Order.id.desc()).limit(15).all()
        
        return {
            "inr_cash": portfolio.inr_cash if portfolio else 100000.0,
            "usd_cash": portfolio.usd_cash if portfolio else 10000.0,
            "total_trades": portfolio.total_trades if portfolio else len(orders),
            "recent_orders": [
                {
                    "id": o.id,
                    "ticker": o.ticker,
                    "action": o.action,
                    "quantity": o.quantity,
                    "executed_price": o.executed_price,
                    "stop_loss": o.stop_loss,
                    "take_profit": o.take_profit,
                    "fee": o.brokerage_fee,
                    "status": o.status
                }
                for o in orders
            ]
        }
    finally:
        db.close()

@router.get("/positions")
def get_open_positions():
    db = SessionLocal()
    try:
        fills = db.query(Order).filter(Order.status == "FILLED").all()
        positions = {}

        for o in fills:
            if o.ticker not in positions:
                positions[o.ticker] = {"quantity": 0, "total_cost": 0.0}
            if o.action == "BUY":
                positions[o.ticker]["quantity"] += o.quantity
                positions[o.ticker]["total_cost"] += (o.quantity * o.executed_price)
            elif o.action == "SELL" and positions[o.ticker]["quantity"] > 0:
                avg_cost = positions[o.ticker]["total_cost"] / positions[o.ticker]["quantity"]
                positions[o.ticker]["quantity"] -= o.quantity
                positions[o.ticker]["total_cost"] -= (o.quantity * avg_cost)

        active_positions = []
        for sym, pos in positions.items():
            if pos["quantity"] > 0:
                avg_entry = round(pos["total_cost"] / pos["quantity"], 2)
                is_inr = sym.endswith((".NS", ".BO"))
                active_positions.append({
                    "ticker": sym,
                    "quantity": pos["quantity"],
                    "avg_price": avg_entry,
                    "currency_symbol": "₹" if is_inr else "$"
                })

        return {"positions": active_positions}
    finally:
        db.close()