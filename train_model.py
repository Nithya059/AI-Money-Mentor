import yfinance as yf
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# ---------- DOWNLOAD REAL DATA ----------
data = yf.download("AAPL", period="5y")

# ---------- FEATURE ENGINEERING ----------
data["Return"] = data["Close"].pct_change()
data["Volatility"] = data["Return"].rolling(10).std()
data["MA"] = data["Close"].rolling(10).mean()

data = data.dropna()

# ---------- LABEL (RISK BASED ON VOLATILITY) ----------
def label(vol):
    if vol > 0.02:
        return 0   # High Risk
    elif vol > 0.01:
        return 1   # Medium Risk
    else:
        return 2   # Low Risk

data["Risk"] = data["Volatility"].apply(label)

# ---------- FEATURES ----------
X = data[["Return", "Volatility", "MA"]]
y = data["Risk"]

# ---------- TRAIN ----------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

print("Accuracy:", model.score(X_test, y_test))

# ---------- SAVE ----------
joblib.dump(model, "model.pkl")

print("Model saved successfully")