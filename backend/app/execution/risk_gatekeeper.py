from app.config.settings import MAX_PORTFOLIO_RISK_PER_TRADE, MIN_CONFIDENCE_THRESHOLD

def apply_safety_guardrails(raw_decision: dict) -> dict:
    action = raw_decision.get("action", "HOLD").upper()
    confidence = float(raw_decision.get("confidence_score", 0.0))
    allocation = float(raw_decision.get("allocated_capital_pct", 0.0))
    rationale = raw_decision.get("rationale_summary", "No rationale provided.")
    
    override_triggered = False
    audit_notes = []

    if action in ["BUY", "SELL"] and confidence < MIN_CONFIDENCE_THRESHOLD:
        audit_notes.append(f"Confidence score {confidence:.2f} is below safety floor of {MIN_CONFIDENCE_THRESHOLD:.2f}. Forced to HOLD.")
        action = "HOLD"
        allocation = 0.0
        override_triggered = True

    if allocation > MAX_PORTFOLIO_RISK_PER_TRADE:
        audit_notes.append(f"Allocated capital {allocation*100:.1f}% exceeded cap of {MAX_PORTFOLIO_RISK_PER_TRADE*100:.1f}%. Clamped.")
        allocation = MAX_PORTFOLIO_RISK_PER_TRADE
        override_triggered = True

    return {
        "raw_action": raw_decision.get("action", "HOLD"),
        "final_action": action,
        "confidence_score": confidence,
        "final_allocation_pct": allocation,
        "override_triggered": override_triggered,
        "audit_notes": audit_notes,
        "rationale": rationale
    }