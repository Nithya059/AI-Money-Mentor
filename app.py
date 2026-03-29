import streamlit as st
import joblib
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.title("🚀 AI Money Mentor")

# ---------- PERSONAL INPUT ----------
age = st.number_input("Age", min_value=18)
income = st.number_input("Monthly Income", min_value=1.0)
expense = st.number_input("Monthly Expense", min_value=0.0)
partner_income = st.number_input("Partner Income", min_value=0.0)

risk_profile = st.selectbox("Risk Profile", ["Low","Medium","High"])

# ---------- INPUT ----------
basic = st.number_input("Basic Salary",0.0)
hra = st.number_input("HRA",0.0)
rent = st.number_input("Rent Paid",0.0)
allow = st.number_input("Other Allowances",0.0)

# ---------- DEFINE FIRST ----------
gross = basic + hra + allow

hra_exempt = max(0,min(hra,0.5*basic,rent-0.1*basic))

# ---------- FINANCIAL ----------
st.subheader("📥 Financial Inputs")

cash = st.number_input("Liquid Cash", 0.0)
insurance = st.number_input("Insurance Cover", 0.0)
emi = st.number_input("Monthly EMI", 0.0)

d80c = st.number_input("80C", 0.0, 150000.0)
d80d = st.number_input("80D", 0.0)



# ---------- PORTFOLIO ----------
st.subheader("📊 Portfolio")

equity_amt = st.number_input("Equity", 0.0)
debt_amt = st.number_input("Debt", 0.0)
other_assets = st.number_input("Other Assets", 0.0)

# ---------- LIFE EVENT ----------
event = st.selectbox("Life Event", ["None","Marriage","Child","Bonus"])

total_income = income + partner_income
annual_income = total_income * 12

# ---------- LIFE EVENT ADVISOR ----------
st.subheader("🎯 Life Event Advisor")

adj_income = total_income
adj_expense = expense
adj_risk = risk_profile
tax_impact = 0
notes = []

if event == "Bonus":
    bonus = income * 2
    adj_income += bonus
    tax_impact = bonus * 0.3
    notes.append(f"Bonus ₹{bonus} → tax ₹{int(tax_impact)}")

elif event == "Marriage":
    adj_expense += expense * 0.3
    adj_risk = "Medium"
    notes.append("Expenses ↑30%")

elif event == "Child":
    adj_expense += expense * 0.5
    adj_risk = "Low"
    tax_impact = -15000
    notes.append("Expenses ↑50%, tax benefit")

st.write("Income:", adj_income)
st.write("Expense:", adj_expense)
st.write("Risk:", adj_risk)
st.write("Tax Impact:", tax_impact)

for n in notes:
    st.write("✔", n)

total_income = adj_income
expense = adj_expense
risk_profile = adj_risk

# ---------- GOALS ----------
st.subheader("🎯 Goals")

retirement_goal = st.number_input("Retirement Goal", 0.0)
retirement_years = st.number_input("Years to Retirement", 1)

education_goal = st.number_input("Education Goal", 0.0)
education_years = st.number_input("Years to Education", 1)

house_goal = st.number_input("House Goal", 0.0)
house_years = st.number_input("Years to House", 1)

# ---------- FIRE ENGINE ----------
goals = [
    {"name":"Retirement","goal":retirement_goal,"years":retirement_years,"inf":0.06},
    {"name":"Education","goal":education_goal,"years":education_years,"inf":0.08},
    {"name":"House","goal":house_goal,"years":house_years,"inf":0.07},
]

for g in goals:
    g["future"] = g["goal"]*((1+g["inf"])**g["years"])

goals = sorted(goals,key=lambda g:(1/g["years"])*0.7+(g["future"]/1e6)*0.3,reverse=True)

def sip(goal,yrs):
    r=0.12/12;n=yrs*12
    return goal*r/((1+r)**n-1)

for g in goals:
    g["sip"]=sip(g["future"],g["years"])

# ---------- GLIDEPATH PER GOAL ----------
def get_alloc(years):
    if years > 20:
        return 0.8, 0.2
    elif years > 10:
        return 0.6, 0.4
    else:
        return 0.4, 0.6

for g in goals:
    eq, debt = get_alloc(g["years"])
    g["equity_alloc"] = eq
    g["debt_alloc"] = debt

savings = total_income-expense
total_sip = sum(g["sip"] for g in goals)

if total_sip>savings:
    scale=savings/total_sip if total_sip>0 else 0
    for g in goals:
        g["sip"]*=scale

months=max(g["years"] for g in goals)*12

st.subheader("📅 Monthly Plan")
for m in range(min(12,months)):
    st.write(f"Month {m+1}:")
    for g in goals:
        st.write({
            "Goal": g["name"],
            "SIP": round(g["sip"],2),
            "Equity %": int(g["equity_alloc"]*100),
            "Debt %": int(g["debt_alloc"]*100)
        })

# ---------- HEALTH SCORE ----------
st.subheader("💯 Health Score")

net_worth = cash+equity_amt+debt_amt+other_assets

emergency = 10 if expense>0 and cash/expense>=6 else 5
ins = 10 if insurance>=annual_income*10 else 5

total_assets = net_worth
eq_ratio = equity_amt/total_assets if total_assets>0 else 0
div = 10 if 0.4<=eq_ratio<=0.7 else 5

debt = 10 if emi/total_income<0.3 else 5
tax = 10 if d80c>=150000 else 5

fire = expense*12*25
ret = 10 if net_worth>=fire else 5

score = emergency+ins+div+debt+tax+ret
st.write("Score:",score,"/60")

# ---------- TAX FUNCTIONS ----------
def tax_old(i):
    if i <= 250000:
        return 0
    elif i <= 500000:
        return (i - 250000) * 0.05
    elif i <= 1000000:
        return 12500 + (i - 500000) * 0.2
    else:
        return 112500 + (i - 1000000) * 0.3

def tax_new(i):
    if i <= 300000:
        return 0
    elif i <= 600000:
        return (i - 300000) * 0.05
    elif i <= 900000:
        return 15000 + (i - 600000) * 0.1
    else:
        return 45000 + (i - 900000) * 0.15

# ---------- TAX WIZARD ----------
st.subheader("💸 Tax Wizard")

# ---------- ADD EXTRA INPUTS ----------
nps = st.number_input("NPS (80CCD)",0.0)
home_loan_interest = st.number_input("Home Loan Interest",0.0)
taxable_old = gross - hra_exempt - d80c - d80d - nps - home_loan_interest

# ---------- OLD REGIME ----------

st.write("Gross:", gross)
st.write("HRA Exempt:", hra_exempt)
st.write("80C:", d80c)
st.write("80D:", d80d)
st.write("NPS:", nps)
st.write("Home Loan:", home_loan_interest)
st.write("Taxable:", taxable_old)

old = tax_old(taxable_old)

# ---------- NEW REGIME ----------
taxable_new = gross - 50000
new = tax_new(taxable_new)

st.write("📊 New Regime Taxable:", taxable_new)

# ---------- RESULT ----------
st.write("Old:", int(old))
st.write("New:", int(new))

best="Old" if old<new else "New"
st.success("Use "+best)

# ---------- RANKED ----------
st.write("📊 Tax Saving Ranking:")
st.write("1. ELSS → Medium risk, 3yr lock")
st.write("2. PPF → Low risk, long lock")
st.write("3. NPS → Tax efficient, low liquidity")

# ---------- PORTFOLIO X-RAY ----------
st.subheader("📊 Portfolio X-Ray")

# ---------- CAMS PDF UPLOAD ----------
import pdfplumber

st.subheader("📂 Upload CAMS Statement")

uploaded_file = st.file_uploader("Upload CAMS PDF", type=["pdf"])

cashflows = []
dates = []

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    lines = text.split("\n")

    for line in lines:
        parts = line.split()

        # VERY SIMPLE PARSER (works for many CAMS formats)
        if len(parts) >= 3:
            try:
                date = parts[0]
                amount = float(parts[-1].replace(",", ""))

                # negative = investment
                amount = -abs(amount)

                dates.append(pd.to_datetime(date))
                cashflows.append(amount)

            except:
                continue

    # Add current value as final positive cashflow
    if len(cashflows) > 0:
        current_value = sum(vals)
        dates.append(pd.Timestamp.today())
        cashflows.append(current_value)

# ---------- XIRR ----------
import numpy as np

def xirr(cashflows, dates):
    try:
        days = np.array([(d - dates[0]).days for d in dates]) / 365

        def npv(rate):
            return sum(cf / (1 + rate) ** d for cf, d in zip(cashflows, days))

        rate = 0.1

        for _ in range(100):
            val = npv(rate)
            rate -= val / 100000

            # 🔥 CRITICAL FIX
            if rate <= -0.99 or rate > 10:
                return 0

        return float(rate)

    except:
        return 0

if len(cashflows) > 1:
    try:
        xirr_value = xirr(cashflows, dates) * 100
        if isinstance(xirr_value, (int, float)):
            st.write("Real XIRR:", round(xirr_value, 2), "%")
        else:
            st.write("Real XIRR: Unable to compute")
    except:
        st.write("Could not calculate XIRR")

mf = st.text_input("Funds","HDFC,NIFTY")
val = st.text_input("Values","100000,50000")
names = mf.split(",")
vals = list(map(float,val.split(",")))
# ---------- STOCK OVERLAP ----------
holdings = {
    "HDFC":["ReliANCE","HDFC Bank","Infosys"],
    "NIFTY":["Reliance","Infosys","TCS"]
}

stock_count = {}

for fund in names:
    if fund in holdings:
        for stock in holdings[fund]:
            stock_count[stock] = stock_count.get(stock,0)+1

overlap = {k:v for k,v in stock_count.items() if v>1}

st.write("🔁 Overlap Stocks:", overlap)



total_port = sum(vals)
# ---------- TAX-AWARE REBALANCE ----------
holding_years = st.number_input("Holding Period (years)",1,10,1)

if holding_years < 1:
    st.write("⚠️ Avoid selling (Short-term capital gains)")
else:
    if len(overlap)>0:
        st.write("Reduce overlapping funds:")
        for f in names:
            st.write("→ Reduce:", f)
    else:
        st.write("Portfolio is diversified")

# ---------- REAL XIRR USING CASHFLOWS ----------

st.subheader("📅 Cashflow Input (for real XIRR)")

dates_input = st.text_input(
    "Dates (YYYY-MM-DD, comma separated)",
    "2020-01-01,2021-01-01,2022-01-01"
)

cashflows_input = st.text_input(
    "Cashflows (negative=invest, positive=current value)",
    "-100000,-50000,180000"
)

try:
    dates = pd.to_datetime(dates_input.split(","))
    cashflows = list(map(float, cashflows_input.split(",")))

    # XIRR function
    def xirr(cashflows, dates):
        def npv(rate):
            return sum([
                cf / ((1 + rate) ** ((dates[i] - dates[0]).days / 365))
                for i, cf in enumerate(cashflows)
            ])

        rate = 0.1
        for _ in range(100):
            rate -= npv(rate) / 100000  # iterative solve
        return rate

    xirr_value = xirr(cashflows, dates)

# 🔥 FORCE SAFE VALUE
    if not isinstance(xirr_value, (int, float)):
        xirr_value = 0

except:
    xirr_value = 0

st.write("Real XIRR:", round(xirr_value, 2), "%")

# ---------- REAL ML MODEL (FINANCIAL FEATURES) ----------

st.subheader("🤖 ML Financial Intelligence")

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# ---------- DATA ----------
ticker = st.selectbox("Select Market", ["AAPL","MSFT","GOOG"])

data = yf.download(ticker, period="2y")

# ---------- FEATURE ENGINEERING ----------
data["Return"] = data["Close"].pct_change()
data["Volatility"] = data["Return"].rolling(10).std()
data["MA20"] = data["Close"].rolling(20).mean()
data["MA50"] = data["Close"].rolling(50).mean()
data["Momentum"] = data["Close"] - data["Close"].shift(10)

data = data.dropna()

# ---------- TARGET ----------
data["Target"] = (data["Return"].shift(-1) > 0).astype(int)

# ---------- TRAIN ----------
X = data[["Return","Volatility","MA20","MA50","Momentum"]]
y = data["Target"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

# ---------- VALIDATION ----------
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

# ---------- PREDICTION ----------
latest = X.iloc[-1]
prediction = model.predict([latest])[0]

if prediction == 1:
    market_view = "Bullish"
else:
    market_view = "Bearish"

# ---------- PERSONALIZATION ----------
if risk_profile == "High":
    advice = "Increase equity exposure"
elif risk_profile == "Medium":
    advice = "Balanced allocation"
else:
    advice = "Reduce risk, increase debt"

# ---------- OUTPUT ----------
st.write("Model Accuracy:", round(acc,2))
st.write("Market Prediction:", market_view)
st.write("Personal Advice:", advice)

st.subheader("📈 Market Risk")
st.write(market_view)

# ---------- AUTONOMOUS FINANCIAL AGENT ----------

st.subheader("🤖 AI Financial Agent (Decision Engine)")

actions = []

# ---------- STEP 1: DATA COLLECTION ----------
savings = total_income - expense
net_worth = cash + equity_amt + debt_amt + other_assets
# ---------- REAL FIRE CORPUS ----------
inflation = 0.06
years_to_retire = retirement_years

monthly_need_today = expense
future_monthly_need = monthly_need_today * ((1 + inflation) ** years_to_retire)

annual_need = future_monthly_need * 12

# safe withdrawal 4%
fire_target = annual_need / 0.04

st.write("🎯 Required Retirement Corpus:", int(fire_target))

# ---------- STEP 2: PROBLEM DETECTION ----------

# Emergency issue
if expense > 0 and cash/expense < 3:
    actions.append(("HIGH","Build Emergency Fund"))

# Debt issue
if total_income > 0 and emi/total_income > 0.4:
    actions.append(("HIGH","Reduce Debt / Prepay Loans"))

# Insurance gap
if insurance < annual_income * 10:
    actions.append(("HIGH","Increase Insurance Cover"))

# Tax inefficiency
if d80c < 150000:
    actions.append(("MEDIUM","Invest in ELSS / PPF for tax saving"))

# Retirement gap
if net_worth < fire_target * 0.3:
    actions.append(("HIGH","Increase Retirement SIP"))

# Portfolio imbalance
if equity_amt + debt_amt > 0:
    eq_ratio = equity_amt / (equity_amt + debt_amt)
    if (risk_profile == "Low" and eq_ratio > 0.5) or \
       (risk_profile == "High" and eq_ratio < 0.6):
        actions.append(("MEDIUM","Rebalance Portfolio"))

# ---------- STEP 3: PRIORITY ORDERING ----------

priority_map = {"HIGH":3,"MEDIUM":2,"LOW":1}
actions = sorted(actions, key=lambda x: priority_map[x[0]], reverse=True)

# ---------- STEP 4: CONFLICT RESOLUTION ----------

final_actions = []

for level, action in actions:

    # conflict: debt vs investment
    if "Debt" in action and any("Invest" in a[1] for a in final_actions):
        continue  # prioritize debt

    # conflict: emergency vs investment
    if "Emergency" in action:
        final_actions = [a for a in final_actions if "Invest" not in a[1]]

    final_actions.append((level, action))

# ---------- STEP 5: MEMORY (SESSION STATE) ----------

if "history" not in st.session_state:
    st.session_state.history = []

st.session_state.history.append(final_actions)

# ---------- STEP 6: OUTPUT ----------

st.subheader("📋 Action Plan (What to do FIRST)")

for i, (level, action) in enumerate(final_actions):
    st.write(f"{i+1}. [{level}] {action}")

st.subheader("🧠 Agent Reasoning")

for level, action in final_actions:
    if "Emergency" in action:
        st.write("Emergency fund is critical for financial safety")
    elif "Debt" in action:
        st.write("High debt reduces wealth growth")
    elif "Insurance" in action:
        st.write("Insurance protects financial stability")
    elif "Tax" in action:
        st.write("Tax saving increases net returns")
    elif "Retirement" in action:
        st.write("Long-term compounding needed for retirement")
    elif "Portfolio" in action:
        st.write("Asset allocation must match risk profile")

# ---------- STEP 7: HISTORY ----------

st.subheader("📜 Previous Decisions")

for h in st.session_state.history[-3:]:
    st.write(h)

st.warning("⚠️ Not financial advice")