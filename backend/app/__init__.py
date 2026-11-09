import os
from pathlib import Path
from dotenv import load_dotenv
import litellm

BACKEND_DIR = Path(__file__).resolve().parents[2]
env_path = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
if GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

litellm.drop_params = True
_orig_completion = litellm.completion

def _clean_msg(msg):
    if isinstance(msg, dict):
        m = dict(msg)
        m.pop("cache_breakpoint", None)
        return m
    return msg

def _safe_completion(*args, **kwargs):
    if "messages" in kwargs and isinstance(kwargs["messages"], list):
        kwargs["messages"] = [_clean_msg(m) for m in kwargs["messages"]]
    return _orig_completion(*args, **kwargs)

litellm.completion = _safe_completion

DATABASE_PATH = BACKEND_DIR / "paper_trading.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

MAX_PORTFOLIO_RISK_PER_TRADE = 0.05
MIN_CONFIDENCE_THRESHOLD = 0.70
LLM_MODEL = "groq/openai/gpt-oss-20b"