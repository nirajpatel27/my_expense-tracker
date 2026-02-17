# 💰 Expense Tracker (Flask + MongoDB)

A simple, clean, and practical **Expense Tracker web application** built using **Flask** and **MongoDB**.  
It helps users track **personal expenses**, manage **shared expenses**, view **monthly/yearly insights**, and analyze spending patterns visually.

---

## 🚀 Features

### 📌 Personal Expenses
- Add expenses with:
  - Amount
  - Category
  - Description
  - Payment mode
  - Date
- View all expenses in a table
- Filter expenses by:
  - Category
  - Year
  - Month
  - Date
- Sort expenses by newest / oldest
- Soft delete expenses (not permanently removed)

---

### 🤝 Shared Expenses
- Add shared expenses with:
  - Title
  - Total amount
  - Paid by
  - Participants
  - Date
- Automatically splits amount equally
- Shows:
  - Per person amount
  - Split participants
  - Payment date
- Settle shared expenses
- Track settlement date
- View net balances (who owes whom)

---

### 📊 Dashboard & Insights
- Monthly total spending
- Yearly total spending
- Average monthly spend
- Highest spending month
- Highest spending category
- Monthly expense trend (Chart.js)
- Category-wise spending chart (Chart.js)

---

### 🎨 UI & UX
- Clean, professional dashboard layout
- Responsive design
- Modern navbar
- Card-based layout
- Table views with filters
- Chart.js integration for data visualization

---

## 🛠 Tech Stack

- **Backend:** Flask (Python)
- **Database:** MongoDB
- **Frontend:** HTML, CSS, Jinja2
- **Charts:** Chart.js
- **Environment Management:** python-dotenv

---

## 📂 Project Structure

'''
expense-tracker/
│
├── app.py
├── .env
├── requirements.txt
├── README.md
│
├── templates/
│ ├── base.html
│ ├── dashboard.html
│ ├── add_expense.html
│ ├── expenses.html
│ ├── add_shared_expense.html
│ ├── shared_expenses.html
│ └── shared_balances.html
│
├── static/
│ ├── css/
│
'''

## Configure Environment Variables

python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

## Run the Application

python app.py





