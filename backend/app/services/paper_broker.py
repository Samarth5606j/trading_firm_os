import random
from app.database.models import SessionLocal, Portfolio, PaperOrder

def execute_paper_order(ticker: str, action: str, quantity: int, current_price: float) -> dict:
    action = action.upper().strip()
    db = SessionLocal()
    portfolio = db.query(Portfolio).first()
    is_indian = ticker.endswith((".NS", ".BO"))
    currency_sym = "₹" if is_indian else "$"

    # 1. Realistic Slippage Model (0.05% - 0.15%)
    slippage_rate = random.uniform(0.0005, 0.0015)
    executed_price = round(current_price * (1 + slippage_rate if action == "BUY" else 1 - slippage_rate), 2)
    slippage_cost = round(abs(executed_price - current_price) * quantity, 2)
    
    # 2. Statutory / Brokerage Fees (0.03%)
    fee = round(executed_price * quantity * 0.0003, 2)
    gross_amount = round(executed_price * quantity, 2)

    # 3. Check Active Position Quantity
    filled_orders = db.query(PaperOrder).filter(
        PaperOrder.ticker == ticker,
        PaperOrder.status == "FILLED"
    ).all()

    current_holding_qty = 0
    for o in filled_orders:
        if o.action == "BUY":
            current_holding_qty += o.quantity
        elif o.action == "SELL":
            current_holding_qty -= o.quantity

    # 4. Handle BUY vs. SELL
    if action == "BUY":
        total_debit = gross_amount + fee
        if is_indian and portfolio.inr_cash < total_debit:
            db.close()
            return {"success": False, "error": f"Insufficient INR Cash. Required: ₹{total_debit:,.2f}, Available: ₹{portfolio.inr_cash:,.2f}"}
        elif not is_indian and portfolio.usd_cash < total_debit:
            db.close()
            return {"success": False, "error": f"Insufficient USD Cash. Required: ${total_debit:,.2f}, Available: ${portfolio.usd_cash:,.2f}"}

        if is_indian:
            portfolio.inr_cash -= total_debit
        else:
            portfolio.usd_cash -= total_debit

    elif action == "SELL":
        if quantity > current_holding_qty:
            db.close()
            return {
                "success": False, 
                "error": f"Cannot sell {quantity} shares of {ticker}. Currently holding {current_holding_qty} shares."
            }
        
        # Credit cash proceeds net of fees
        net_credit = gross_amount - fee
        if is_indian:
            portfolio.inr_cash += net_credit
        else:
            portfolio.usd_cash += net_credit

    # 5. Calculate OCO Bracket Stops (±2.5%)
    buffer = executed_price * 0.025
    stop_loss = round(executed_price - buffer if action == "BUY" else executed_price + buffer, 2)
    take_profit = round(executed_price + (buffer * 1.5) if action == "BUY" else executed_price - (buffer * 1.5), 2)

    order = PaperOrder(
        ticker=ticker,
        action=action,
        quantity=quantity,
        requested_price=current_price,
        executed_price=executed_price,
        slippage_cost=slippage_cost,
        brokerage_fee=fee,
        stop_loss=stop_loss,
        take_profit=take_profit,
        status="FILLED"
    )

    portfolio.total_trades += 1
    db.add(order)
    db.commit()

    res = {
        "success": True,
        "executed_price": executed_price,
        "fee": fee,
        "action": action,
        "net_holding": current_holding_qty + (quantity if action == "BUY" else -quantity)
    }
    db.close()
    return res