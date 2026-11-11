import random
from app.database.models import SessionLocal, Portfolio, Order

def execute_paper_order(ticker: str, action: str, quantity: int, current_price: float) -> dict:
    db = SessionLocal()
    ticker = ticker.upper().strip()
    action = action.upper().strip()
    is_inr = ticker.endswith((".NS", ".BO"))

    try:
        portfolio = db.query(Portfolio).filter(Portfolio.id == 1).first()
        if not portfolio:
            portfolio = Portfolio(id=1, inr_cash=100000.0, usd_cash=10000.0, total_trades=0)
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)

        # Realistic execution slippage (0.05% to 0.15%)
        slippage_pct = random.uniform(0.0005, 0.0015)
        slippage_cost = round(current_price * slippage_pct, 2)
        executed_price = round(
            current_price + slippage_cost if action == "BUY" else current_price - slippage_cost,
            2
        )

        gross_value = executed_price * quantity
        fee = round(gross_value * 0.0003, 2)  # 3 bps institutional brokerage

        # Dynamic +/- 2.5% Stop-Loss & +3.75% Take-Profit
        stop_loss = round(executed_price * 0.975, 2) if action == "BUY" else round(executed_price * 1.025, 2)
        take_profit = round(executed_price * 1.0375, 2) if action == "BUY" else round(executed_price * 0.9625, 2)

        # Calculate current holdings
        filled_orders = db.query(Order).filter(Order.ticker == ticker, Order.status == "FILLED").all()
        current_holding_qty = sum(o.quantity if o.action == "BUY" else -o.quantity for o in filled_orders)

        if action == "BUY":
            total_cost = gross_value + fee
            if is_inr:
                if portfolio.inr_cash < total_cost:
                    raise ValueError(f"Insufficient INR Vault funds. Required: ₹{total_cost:,.2f}")
                portfolio.inr_cash = round(portfolio.inr_cash - total_cost, 2)
            else:
                if portfolio.usd_cash < total_cost:
                    raise ValueError(f"Insufficient USD Vault funds. Required: ${total_cost:,.2f}")
                portfolio.usd_cash = round(portfolio.usd_cash - total_cost, 2)
        elif action == "SELL":
            if current_holding_qty < quantity:
                raise ValueError(f"Insufficient shares of {ticker} to sell. Holding: {current_holding_qty}")
            net_credit = gross_value - fee
            if is_inr:
                portfolio.inr_cash = round(portfolio.inr_cash + net_credit, 2)
            else:
                portfolio.usd_cash = round(portfolio.usd_cash + net_credit, 2)

        order = Order(
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

        net_holding = current_holding_qty + (quantity if action == "BUY" else -quantity)
        return {
            "success": True,
            "executed_price": executed_price,
            "fee": fee,
            "action": action,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "net_holding": net_holding
        }
    finally:
        db.close()

def evaluate_bracket_triggers(ticker: str, live_price: float) -> list:
    """Checks open BUY positions and auto-sells if Stop-Loss or Take-Profit is breached."""
    db = SessionLocal()
    ticker = ticker.upper().strip()
    triggered_events = []

    try:
        open_orders = db.query(Order).filter(
            Order.ticker == ticker,
            Order.action == "BUY",
            Order.status == "FILLED"
        ).all()

        for order in open_orders:
            trigger_reason = None
            if order.stop_loss and live_price <= order.stop_loss:
                trigger_reason = "STOP_LOSS_TRIGGERED"
            elif order.take_profit and live_price >= order.take_profit:
                trigger_reason = "TAKE_PROFIT_TRIGGERED"

            if trigger_reason:
                order.status = trigger_reason
                db.commit()
                
                # Execute automated closing SELL order
                execute_paper_order(ticker, "SELL", order.quantity, live_price)
                
                triggered_events.append({
                    "order_id": order.id,
                    "ticker": ticker,
                    "reason": trigger_reason,
                    "quantity": order.quantity,
                    "trigger_price": live_price,
                    "entry_price": order.executed_price
                })
    except Exception:
        pass
    finally:
        db.close()

    return triggered_events