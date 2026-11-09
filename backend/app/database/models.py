import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    inr_cash = Column(Float, default=100000.0)
    usd_cash = Column(Float, default=10000.0)
    total_trades = Column(Integer, default=0)

class PaperOrder(Base):
    __tablename__ = "paper_orders"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    action = Column(String)
    quantity = Column(Integer)
    requested_price = Column(Float)
    executed_price = Column(Float)
    slippage_cost = Column(Float, default=0.0)
    brokerage_fee = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(String, default="FILLED")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(Portfolio).first():
        db.add(Portfolio())
        db.commit()
    db.close()