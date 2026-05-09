from pydantic import BaseModel
from typing import List


# User Schema
class UserCreate(BaseModel):
    username: str


# Expense Schema
class ExpenseCreate(BaseModel):
    title: str
    amount: float
    paid_by: int
    participants: List[int]
    comments: str | None = None