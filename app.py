from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from bson.objectid import ObjectId
import calendar
import os

# =========================================================
# App & DB Setup
# =========================================================

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = MongoClient(os.getenv("MONGO_URI"))
db = client["expense_tracker"]

expenses_collection = db["expenses"]          # Personal expenses
shared_collection = db["shared_expenses"]     # Shared expenses
budgets_collection = db["budgets"]            # Budgets


# =========================================================
# Utility Helpers (DRY)
# =========================================================

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def now_year_month():
    now = datetime.now()
    return now.year, now.month

def month_name(num):
    return calendar.month_name[num]


# =========================================================
# Dashboard Calculation Helpers
# =========================================================



def get_monthly_total(month, year):
    return sum(
        exp["amount"] for exp in expenses_collection.find({
            "month": month,
            "year": year,
            "is_deleted": False,
            "is_shared": False
        })
    )

def get_yearly_total(year):
    return sum(
        exp["amount"] for exp in expenses_collection.find({
            "year": year,
            "is_deleted": False,
            "is_shared": False
        })
    )

def get_category_totals(month=None, year=None):
    query = {"is_deleted": False, "is_shared": False}
    if month:
        query["month"] = month
    if year:
        query["year"] = year

    totals = {}
    for exp in expenses_collection.find(query):
        totals[exp["category"]] = totals.get(exp["category"], 0) + exp["amount"]
    return totals

def get_monthly_breakdown(year):
    current_year, current_month = now_year_month()
    months_to_show = current_month if year == current_year else 12

    breakdown = {month_name(m): 0 for m in range(1, months_to_show + 1)}

    for exp in expenses_collection.find({
        "year": year,
        "is_deleted": False,
        "is_shared": False
    }):
        if exp["month"] <= months_to_show:
            breakdown[month_name(exp["month"])] += exp["amount"]

    return breakdown

def highest_spending_month(year):
    data = get_monthly_breakdown(year)
    if not data:
        return None, 0
    m = max(data, key=data.get)
    return m, data[m]

def highest_spending_category(year):
    data = get_category_totals(year=year)
    if not data:
        return None, 0
    c = max(data, key=data.get)
    return c, data[c]

def average_monthly_spend(year):
    current_year, current_month = now_year_month()
    months = current_month if year == current_year else 12
    if months == 0:
        return 0
    return round(get_yearly_total(year) / months, 2)

def chart_data(data_dict):
    return {
        "labels": list(data_dict.keys()),
        "data": list(data_dict.values())
    }

def available_years():
    return sorted(expenses_collection.distinct("year"))

def budget_alerts(month, year):
    alerts = []
    totals = get_category_totals(month=month, year=year)

    for b in budgets_collection.find():
        spent = totals.get(b["category"], 0)
        if spent > b["monthly_limit"]:
            alerts.append({
                "category": b["category"],
                "limit": b["monthly_limit"],
                "spent": spent
            })
    return alerts


# =========================================================
# Shared Expense Helpers
# =========================================================

def calculate_net_balances():
    balances = {}

    for exp in shared_collection.find({"is_settled": False}):
        paid_by = exp["paid_by"]
        participants = exp["participants"]
        per_person = exp["per_person_amount"]

        balances.setdefault(paid_by, 0)
        balances[paid_by] += exp["total_amount"]

        for p in participants:
            balances.setdefault(p, 0)
            balances[p] -= per_person

    return balances


# =========================================================
# Routes — Dashboard
# =========================================================

@app.route("/dashboard")
def dashboard():
    current_year, current_month = now_year_month()
    year = request.args.get("year", type=int, default=current_year)

    month_num = current_month if year == current_year else None
    month_label = month_name(month_num) if month_num else "Full Year"

    monthly_total = get_monthly_total(month_num, year) if month_num else None
    yearly_total = get_yearly_total(year)

    monthly_data = get_monthly_breakdown(year)

    high_month, high_month_amt = highest_spending_month(year)
    top_cat, top_cat_amt = highest_spending_category(year)
    avg_spend = average_monthly_spend(year)

    return render_template(
        "dashboard.html",
        year=year,
        month_name=month_label,
        monthly_total=monthly_total,
        yearly_total=yearly_total,
        monthly_breakdown=monthly_data,
        monthly_chart=chart_data(monthly_data),
        category_chart=chart_data(get_category_totals(year=year)),
        highest_month=high_month,
        highest_month_amount=high_month_amt,
        top_category=top_cat,
        top_category_amount=top_cat_amt,
        avg_monthly_spend=avg_spend,
        available_years=available_years(),
        budget_alerts=budget_alerts(month_num, year) if month_num else []
    )


# =========================================================
# Routes — Personal Expenses
# =========================================================

@app.route("/")
def home():
    return redirect(url_for("add_expense"))

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        date_obj = parse_date(request.form["date"])

        expenses_collection.insert_one({
            "amount": float(request.form["amount"]),
            "category": request.form["category"],
            "description": request.form["description"],
            "payment_mode": request.form["payment_mode"],
            "date": request.form["date"],
            "month": date_obj.month,
            "year": date_obj.year,
            "is_shared": False,
            "is_deleted": False,
            "created_at": datetime.now()
        })
        return redirect(url_for("add_expense"))

    return render_template("add_expense.html")

@app.route("/expenses")
def view_expenses():
    sort = request.args.get("sort", "newest")
    category = request.args.get("category")
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    date = request.args.get("date")

    query = {"is_deleted": False, "is_shared": False}
    if category: query["category"] = category
    if year: query["year"] = year
    if month: query["month"] = month
    if date: query["date"] = date

    order = -1 if sort == "newest" else 1

    expenses = list(expenses_collection.find(query).sort("date", order))

    return render_template(
        "expenses.html",
        expenses=expenses,
        categories=expenses_collection.distinct("category"),
        years=sorted(expenses_collection.distinct("year")),
        selected={
            "sort": sort,
            "category": category,
            "year": year,
            "month": month,
            "date": date
        }
    )

@app.route("/delete/<expense_id>")
def delete_expense(expense_id):
    expenses_collection.update_one(
        {"_id": ObjectId(expense_id)},
        {"$set": {"is_deleted": True}}
    )
    return redirect(url_for("view_expenses"))


# =========================================================
# Routes — Shared Expenses
# =========================================================

@app.route("/add-shared-expense", methods=["GET", "POST"])
def add_shared_expense():
    if request.method == "POST":
        paid_by = request.form["paid_by"]
        others = [
            p.strip() for p in request.form["participants"].split(",")
            if p.strip() and p.strip() != paid_by
        ]

        people = [paid_by] + others
        per_person = round(float(request.form["total_amount"]) / len(people), 2)

        shared_collection.insert_one({
            "title": request.form["title"],
            "total_amount": float(request.form["total_amount"]),
            "paid_by": paid_by,
            "participants": people,
            "per_person_amount": per_person,
            "date": request.form["date"],
            "is_settled": False,
            "settled_at": None,
            "created_at": datetime.now()
        })

        return redirect(url_for("view_shared_expenses"))

    return render_template("add_shared_expense.html")

@app.route("/shared")
def view_shared_expenses():
    sort = request.args.get("sort", "newest")
    participant = request.args.get("participant")
    status = request.args.get("status")

    query = {}
    if participant:
        query["participants"] = participant
    if status == "settled":
        query["is_settled"] = True
    elif status == "pending":
        query["is_settled"] = False

    order = -1 if sort == "newest" else 1

    expenses = list(shared_collection.find(query).sort("created_at", order))

    return render_template(
        "shared_expenses.html",
        expenses=expenses,
        participants=shared_collection.distinct("participants"),
        selected={
            "sort": sort,
            "participant": participant,
            "status": status
        }
    )

@app.route("/shared/settle/<expense_id>")
def settle_shared_expense(expense_id):
    shared_collection.update_one(
        {"_id": ObjectId(expense_id)},
        {"$set": {
            "is_settled": True,
            "settled_at": datetime.now().strftime("%Y-%m-%d")
        }}
    )
    return redirect(url_for("view_shared_expenses"))

@app.route("/shared/balances")
def shared_balances():
    return render_template(
        "shared_balances.html",
        balances=calculate_net_balances()
    )


# =========================================================
# Run App
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)
