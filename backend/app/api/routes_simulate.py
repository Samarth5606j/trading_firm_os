from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.data.ingestor import fetch_market_data
from app.agents.crew_engine import run_trading_crew
from app.execution.risk_gatekeeper import apply_safety_guardrails
from app.services.pedagogical import generate_dual_mode_analysis

router = APIRouter(prefix="/api", tags=["simulate"])

class SimulationRequest(BaseModel):
    ticker: str

@router.post("/simulate")
def run_simulation(req: SimulationRequest):
    ticker = req.ticker.upper().strip()
    try:
        market_data = fetch_market_data(ticker)
        raw_recommendation = run_trading_crew(market_data)
        raw_dict = raw_recommendation.dict() if hasattr(raw_recommendation, "dict") else dict(raw_recommendation)
        audited = apply_safety_guardrails(raw_dict)
        dual_analysis = generate_dual_mode_analysis(ticker, market_data, audited)

        return {
            "ticker": ticker,
            "raw_action": audited.get("raw_action", audited.get("final_action", "HOLD")),
            "final_action": audited.get("final_action", "HOLD"),
            "confidence_score": audited.get("confidence_score", 0.5),
            "final_allocation_pct": audited.get("final_allocation_pct", 0.0),
            "override_triggered": audited.get("override_triggered", False),
            "audit_notes": audited.get("audit_notes", []),
            "rationale": audited.get("rationale", "Consensus concluded."),
            "decision": audited,
            "analysis": dual_analysis,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))