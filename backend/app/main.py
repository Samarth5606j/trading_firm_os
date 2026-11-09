from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.models import init_db
from app.api.routes_market import router as market_router
from app.api.routes_simulate import router as simulate_router
from app.api.routes_paper import router as paper_router

app = FastAPI(title="Autonomous Multi-Agent Trading Desk", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(market_router)
app.include_router(simulate_router)
app.include_router(paper_router)

@app.get("/")
def health():
    return {"status": "online"}