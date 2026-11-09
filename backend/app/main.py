from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_market, routes_simulate, routes_paper
from app.database.models import init_db

init_db()

app = FastAPI(title="Autonomous Trading Desk OS", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_market.router)
app.include_router(routes_simulate.router)
app.include_router(routes_paper.router)

@app.get("/")
def health_check():
    return {"status": "online", "system": "Autonomous Trading Desk Monorepo"}