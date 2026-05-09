from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from database import Base
from datetime import datetime

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id"))
    comments = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)