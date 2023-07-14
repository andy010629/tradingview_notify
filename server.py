from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

# SQLAlchemy
engine = create_engine(
    "sqlite:///./test.db", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    webhook_url = Column(String)
    line_notify_token = Column(String)
    alerts = relationship("Alert", back_populates="strategy")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    strategy = relationship("Strategy", back_populates="alerts")

Base.metadata.create_all(bind=engine)

# Pydantic models
class AlertBase(BaseModel):
    data: str

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    strategy_id: int
    class Config:
        orm_mode = True

class StrategyBase(BaseModel):
    name: str
    webhook_url: str
    line_notify_token: str

class StrategyCreate(StrategyBase):
    pass

class Strategy(StrategyBase):
    id: int
    alerts: List[Alert] = []
    class Config:
        orm_mode = True

# FastAPI
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/strategies/", response_model=Strategy)
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    db_strategy = Strategy(name=strategy.name, webhook_url=strategy.webhook_url, line_notify_token=strategy.line_notify_token)
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

@app.get("/strategies/", response_model=List[Strategy])
def read_strategies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    strategies = db.query(Strategy).offset(skip).limit(limit).all()
    return strategies

@app.post("/strategies/{strategy_id}/alerts/", response_model=Alert)
def create_alert_for_strategy(strategy_id: int, alert: AlertCreate, db: Session = Depends(get_db)):
    db_alert = Alert(**alert.dict(), strategy_id=strategy_id)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@app.get("/alerts/", response_model=List[Alert])
def read_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    alerts = db.query(Alert).offset(skip).limit(limit).all()
    return alerts

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)