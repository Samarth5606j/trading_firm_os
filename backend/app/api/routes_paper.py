from fastapi import APIRouter
from app.database.models import get_connection

router = APIRouter(prefix="/api/paper", tags=["Paper Broker"])

@router.get("/portfolio")
def get_portfolio():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT inr_cash, usd_cash, total_trades FROM portfolio WHERE id = 1")
    row = c.fetchone()
    c.execute("SELECT id, ticker, action, quantity, executed_price, stop_loss, take_profit, fee, status, timestamp FROM orders ORDER BY id DESC LIMIT 10")
    orders = [
        {
            "id": r[0], "ticker": r[1], "action": r[2], "quantity": r[3],
            "executed_price": r[4], "stop_loss": r[5], "take_profit": r[6],
            "fee": r[7], "status": r[8], "timestamp": r[9]
        }
        for r in c.fetchall()
    ]
    conn.close()
    return {
        "inr_cash": row[0] if row else 89591.57,
        "usd_cash": row[1] if row else 7149.65,
        "total_trades": row[2] if row else len(orders),
        "recent_orders": orders
    }

@router.get("/positions")
def get_open_positions():
    """Computes active holdings and net cost basis from the order ledger."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT ticker, action, quantity, executed_price FROM orders WHERE status = 'FILLED'")
    fills = c.fetchall()
    conn.close()

    positions = {}
    for ticker, action, qty, price in fills:
        if ticker not in positions:
            positions[ticker] = {"quantity": 0, "total_cost": 0.0}
        
        if action == "BUY":
            positions[ticker]["quantity"] += qty
            positions[ticker]["total_cost"] += (qty * price)
        elif action == "SELL":
            # Realize sale against average cost basis
            if positions[ticker]["quantity"] > 0:
                avg_cost = positions[ticker]["total_cost"] / positions[ticker]["quantity"]
                positions[ticker]["quantity"] -= qty
                positions[ticker]["total_cost"] -= (qty * avg_cost)

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