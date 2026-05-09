from sqlalchemy import Column, Integer, Float, ForeignKey
from database import Base

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)

    expense_id = Column(Integer, ForeignKey("expenses.id"))

    user_id = Column(Integer, ForeignKey("users.id"))

    amount_owed = Column(Float, nullable=False)

    amount_paid = Column(Float, nullable=False)

    opening_balance = Column(Float, default=0)

    closing_balance = Column(Float, default=0)