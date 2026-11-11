import random
from app.database.models import get_connection

def execute_paper_order(ticker: str, action: str, quantity: int, current_price: float) -> dict:
    ticker = ticker.upper().strip()
    action = action.upper().strip()
    is_inr = ticker.endswith((".NS", ".BO"))

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

    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT inr_cash, usd_cash, total_trades FROM portfolio WHERE id = 1")
        row = c.fetchone()
        inr_cash, usd_cash, total_trades = row if row else (100000.0, 10000.0, 0)

        # Calculate current holdings
        c.execute("SELECT action, quantity FROM orders WHERE ticker = ? AND status = 'FILLED'", (ticker,))
        fills = c.fetchall()
        current_holding_qty = sum(q if act == "BUY" else -q for act, q in fills)

        if action == "BUY":
            total_cost = gross_value + fee
            if is_inr:
                if inr_cash < total_cost:
                    raise ValueError(f"Insufficient INR Vault funds. Required: ₹{total_cost:,.2f}")
                inr_cash = round(inr_cash - total_cost, 2)
            else:
                if usd_cash < total_cost:
                    raise ValueError(f"Insufficient USD Vault funds. Required: ${total_cost:,.2f}")
                usd_cash = round(usd_cash - total_cost, 2)
        elif action == "SELL":
            if current_holding_qty < quantity:
                raise ValueError(f"Insufficient shares of {ticker} to sell. Holding: {current_holding_qty}")
            net_credit = gross_value - fee
            if is_inr:
                inr_cash = round(inr_cash + net_credit, 2)
            else:
                usd_cash = round(usd_cash + net_credit, 2)

        c.execute(
            "UPDATE portfolio SET inr_cash = ?, usd_cash = ?, total_trades = ? WHERE id = 1",
            (inr_cash, usd_cash, total_trades + 1)
        )
        c.execute(
            """
            INSERT INTO orders (ticker, action, quantity, executed_price, stop_loss, take_profit, fee, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ticker, action, quantity, executed_price, stop_loss, take_profit, fee, "FILLED")
        )
        conn.commit()

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
        conn.close()

def evaluate_bracket_triggers(ticker: str, live_price: float) -> list:
    """Checks open BUY positions and auto-sells if Stop-Loss or Take-Profit is breached."""
    ticker = ticker.upper().strip()
    conn = get_connection()
    c = conn.cursor()
    triggered_events = []

    try:
        c.execute(
            """
            SELECT id, quantity, executed_price, stop_loss, take_profit 
            FROM orders 
            WHERE ticker = ? AND action = 'BUY' AND status = 'FILLED'
            """,
            (ticker,)
        )
        open_orders = c.fetchall()

        for order_id, qty, entry_price, sl, tp in open_orders:
            trigger_reason = None
            if sl and live_price <= sl:
                trigger_reason = "STOP_LOSS_TRIGGERED"
            elif tp and live_price >= tp:
                trigger_reason = "TAKE_PROFIT_TRIGGERED"

            if trigger_reason:
                c.execute("UPDATE orders SET status = ? WHERE id = ?", (trigger_reason, order_id))
                conn.commit()
                conn.close()

                # Execute automated closing SELL order
                execute_paper_order(ticker, "SELL", qty, live_price)

                triggered_events.append({
                    "order_id": order_id,
                    "ticker": ticker,
                    "reason": trigger_reason,
                    "quantity": qty,
                    "trigger_price": live_price,
                    "entry_price": entry_price
                })

                conn = get_connection()
                c = conn.cursor()
    except Exception:
        pass
    finally:
        conn.close()

    return triggered_events