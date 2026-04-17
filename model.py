import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# MODELS
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR

# METRICS
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# --------------------------------------
# LOAD DATA
# --------------------------------------
df = pd.read_csv("stock_features_target.csv")

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values(by=["Ticker", "Date"]).reset_index(drop=True)


# --------------------------------------
# FEATURES & TARGET (BASIC MODEL)
# --------------------------------------
feature_cols = [
    "Open Price",
    "High Price",
    "Low Price",
    "Close Price",
    "Volume Traded"
]

X = df[feature_cols]
y = df["Next_Day_Close"]


# --------------------------------------
# TIME SERIES SPLIT
# --------------------------------------
split = int(len(df) * 0.8)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]


# --------------------------------------
# SCALING
# --------------------------------------
scaler = MinMaxScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


# --------------------------------------
# MODEL LIST
# --------------------------------------
models = {
    "Linear Regression": LinearRegression(),
    "Decision Tree": DecisionTreeRegressor(max_depth=10),
    "Random Forest": RandomForestRegressor(n_estimators=200),
    "Gradient Boosting": GradientBoostingRegressor(),
    "KNN": KNeighborsRegressor(n_neighbors=5),
    "SVR": SVR()
}


# --------------------------------------
# TRAIN + EVALUATE
# --------------------------------------
results = []

for name, model in models.items():

    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    results.append([name, mae, rmse, r2])


# --------------------------------------
# RESULTS TABLE
# --------------------------------------
results_df = pd.DataFrame(results, columns=["Model", "MAE", "RMSE", "R2"])

print("\n📊 MODEL COMPARISON")
print(results_df.sort_values(by="R2", ascending=False))