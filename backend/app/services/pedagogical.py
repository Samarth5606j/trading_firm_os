def generate_pedagogical_guidance(ticker: str, action: str, allocation_pct: float, current_price: float) -> dict:
    is_inr = ticker.endswith((".NS", ".BO"))
    sym = "₹" if is_inr else "$"
    
    if action == "BUY":
        risk_warning = (
            f"Audited BUY order for {ticker} at {sym}{current_price:,.2f}. "
            f"The quantitative risk gatekeeper caps exposure strictly to {allocation_pct * 100:.1f}%. "
            f"Ensure dynamic bracket stop-losses remain armed against unexpected intraday drawdown."
        )
    elif action == "SELL":
        risk_warning = (
            f"Audited SELL signal on {ticker}. Technical momentum exhaustion or baseline moving average breakdown "
            f"detected. Capital preservation triggered to guard against further retracement."
        )
    else:
        risk_warning = (
            f"Neutral stance for {ticker}. The asset is consolidating within its standard volatility channel. "
            f"Maintaining cash reserves until directional conviction is established."
        )

    base_pool = 100000 if is_inr else 10000
    allocated_amount = base_pool * allocation_pct
    stop_buffer_loss = allocated_amount * 0.025

    tangible_scenario = (
        f"Across a modeled {sym}{base_pool:,.0f} portfolio balance, a {allocation_pct * 100:.1f}% position sizing "
        f"allocates {sym}{allocated_amount:,.2f} into {ticker}. With a ±2.5% bracket stop buffer, "
        f"the maximum defined monetary risk is constrained to {sym}{stop_buffer_loss:,.2f}."
    )

    return {
        "plain_risk_warning": risk_warning,
        "tangible_currency_scenario": tangible_scenario
    }