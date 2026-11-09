"""Run the adversarial multi-agent trading recommendation."""
import json
import os
import re
from pydantic import BaseModel, Field
from app.config.settings import GROQ_API_KEY, LLM_MODEL

class TradeRecommendation(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    action: str = Field(description="Action: BUY, SELL, or HOLD")
    confidence_score: float = Field(description="Confidence score between 0.0 and 1.0")
    allocated_capital_pct: float = Field(description="Recommended portfolio fraction")
    rationale_summary: str = Field(description="Brief synthesis of the debate")

def extract_json(raw_text: str, default_ticker: str = "TICKER") -> dict:
    text = str(raw_text).strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()
        
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    text_cleaned = re.sub(r'(?<!\\)\n', ' ', text)
    try:
        return json.loads(text_cleaned, strict=False)
    except Exception:
        pass

    def find_val(pattern, fallback):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1) if m else fallback

    action = find_val(r'"action"\s*:\s*"([A-Za-z]+)"', "HOLD").upper()
    if action not in ["BUY", "SELL", "HOLD"]:
        action = "HOLD"

    try:
        conf = float(find_val(r'"confidence_score"\s*:\s*([0-9\.]+)', 0.5))
    except ValueError:
        conf = 0.5

    try:
        alloc = float(find_val(r'"allocated_capital_pct"\s*:\s*([0-9\.]+)', 0.0))
    except ValueError:
        alloc = 0.0

    rationale = find_val(r'"rationale_summary"\s*:\s*"([^"]+)"', text[:300])

    return {
        "ticker": default_ticker,
        "action": action,
        "confidence_score": min(max(conf, 0.0), 1.0),
        "allocated_capital_pct": min(max(alloc, 0.0), 0.05),
        "rationale_summary": rationale.strip()
    }

def run_trading_crew(market_data: dict) -> TradeRecommendation:
    if not GROQ_API_KEY:
        raise RuntimeError("Set the GROQ_API_KEY environment variable before running simulations.")
    
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY.strip()
    from crewai import Agent, Crew, LLM, Process, Task

    llm_instance = LLM(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY.strip(),
        temperature=0.2,
    )

    ticker = market_data["ticker"]
    analysts = [
        Agent(
            role="Technical Analyst",
            goal=f"Analyze momentum and moving averages for {ticker}.",
            backstory="A quantitative analyst focused on RSI and moving averages.",
            llm=llm_instance,
            verbose=False,
            cache=False,
        ),
        Agent(
            role="Fundamental Specialist",
            goal=f"Assess valuation and PE metrics for {ticker}.",
            backstory="A valuation analyst investigating corporate fundamentals.",
            llm=llm_instance,
            verbose=False,
            cache=False,
        ),
        Agent(
            role="Chief Risk Officer",
            goal="Identify downside risk and enforce strict capital constraints.",
            backstory="A conservative risk officer focused on protecting downside capital.",
            llm=llm_instance,
            verbose=False,
            cache=False,
        ),
        Agent(
            role="Portfolio Manager",
            goal="Synthesize the debate into a final consensus.",
            backstory="An executive portfolio manager responsible for concise action.",
            llm=llm_instance,
            verbose=False,
            cache=False,
        ),
    ]

    task = Task(
        description=(
            f"Analyze {ticker}: price {market_data['current_price']}, RSI {market_data['rsi']}, "
            f"SMA20 {market_data['sma_20']}, SMA50 {market_data['sma_50']}, "
            f"P/E {market_data['pe_ratio']}. Debate technical, fundamental, and risk views.\n"
            "CRITICAL: Output ONLY a single valid JSON object on one line without raw newlines. Format:\n"
            '{"ticker": "' + ticker + '", "action": "BUY", "confidence_score": 0.85, "allocated_capital_pct": 0.04, "rationale_summary": "One clear sentence summary without quotes."}'
        ),
        expected_output="A single valid JSON object containing ticker, action, confidence_score, allocated_capital_pct, and rationale_summary.",
        agent=analysts[-1],
    )

    result = Crew(
        agents=analysts,
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        cache=False,
        memory=False,
    ).kickoff()

    parsed = extract_json(str(result.raw), default_ticker=ticker)
    return TradeRecommendation(**parsed)