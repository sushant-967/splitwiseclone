from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from sqlalchemy import desc
from models.user import User
from models.expense import Expense
from models.expense_split import ExpenseSplit

from schemas import UserCreate, ExpenseCreate

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Supabase connected successfully"}

# ===== USER ENDPOINTS =====

@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "created_at": u.created_at} for u in users]

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        username=user.username
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "created_at": new_user.created_at
    }


# ===== EXPENSE ENDPOINTS =====

@app.get("/expenses")
def get_all_expenses(db: Session = Depends(get_db)):
    expenses = db.query(Expense).all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "total_amount": e.total_amount,
            "paid_by": e.paid_by,
            "comments": e.comments,
            "created_at": e.created_at
        }
        for e in expenses
    ]

@app.post("/expenses")
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):

    # STEP 1 — Create expense entry
    new_expense = Expense(
        title=expense.title,
        total_amount=expense.amount,
        paid_by=expense.paid_by,
        comments=expense.comments
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    # STEP 2 — Calculate equal split
    split_amount = expense.amount / len(expense.participants)

    # STEP 3 — Insert into expense_splits
    for user_id in expense.participants:

        paid_amount = 0

        # User who paid full amount
        if user_id == expense.paid_by:
            paid_amount = expense.amount

        # Get previous balance
        last_split = (
            db.query(ExpenseSplit)
            .filter(ExpenseSplit.user_id == user_id)
            .order_by(ExpenseSplit.id.desc())
            .first()
        )

        opening_balance = 0

        if last_split:
            opening_balance = last_split.closing_balance

        # Calculate balance change
        net_change = paid_amount - split_amount

        closing_balance = opening_balance + net_change

        # Create split row
        split = ExpenseSplit(
            expense_id=new_expense.id,
            user_id=user_id,
            amount_owed=split_amount,
            amount_paid=paid_amount,
            opening_balance=opening_balance,
            closing_balance=closing_balance
        )

        db.add(split)

    db.commit()

    return {
        "id": new_expense.id,
        "title": new_expense.title,
        "total_amount": new_expense.total_amount,
        "paid_by": new_expense.paid_by,
        "comments": new_expense.comments,
        "created_at": new_expense.created_at
    }

# Note: delete endpoint removed to prevent deleting expenses via API
# (Delete operations are disabled per project requirements)


@app.get("/balances")
def get_all_balances(db: Session = Depends(get_db)):

    users = db.query(User).all()

    result = []

    for user in users:

        latest_split = (
            db.query(ExpenseSplit)
            .filter(ExpenseSplit.user_id == user.id)
            .order_by(ExpenseSplit.id.desc())
            .first()
        )

        balance = 0

        if latest_split:
            balance = latest_split.closing_balance

        result.append({
            "user_id": user.id,
            "username": user.username,
            "current_balance": balance
        })

    return result


# ===== SPLITS ENDPOINTS =====

@app.get("/splits")
def get_all_splits(db: Session = Depends(get_db)):
    splits = db.query(ExpenseSplit).order_by(desc(ExpenseSplit.id)).limit(100).all()
    return [
        {
            "id": s.id,
            "expense_id": s.expense_id,
            "user_id": s.user_id,
            "amount_owed": s.amount_owed,
            "amount_paid": s.amount_paid,
            "opening_balance": s.opening_balance,
            "closing_balance": s.closing_balance
        }
        for s in splits
    ]


@app.get("/transactions/{limit}")
def get_transactions(limit: int, db: Session = Depends(get_db)):

    transactions = (
        db.query(Expense)
        .order_by(Expense.id.desc())
        .limit(limit)
        .all()
    )

    result = []

    for transaction in transactions:

        # Get split details
        splits = (
            db.query(ExpenseSplit)
            .filter(ExpenseSplit.expense_id == transaction.id)
            .all()
        )

        split_data = []

        for split in splits:

            user = (
                db.query(User)
                .filter(User.id == split.user_id)
                .first()
            )

            split_data.append({
                "user_id": split.user_id,
                "username": user.username,
                "amount_owed": split.amount_owed,
                "amount_paid": split.amount_paid,
                "opening_balance": split.opening_balance,
                "closing_balance": split.closing_balance
            })

        result.append({
            "expense_id": transaction.id,
            "title": transaction.title,
            "total_amount": transaction.total_amount,
            "paid_by": transaction.paid_by,
            "comments": transaction.comments,
            "created_at": transaction.created_at,
            "splits": split_data
        })

    return result