from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# -------------------------------
# LOAD MODELS
# -------------------------------
model = joblib.load("model/rf_lag_model.pkl")
auto_feature_scaler = joblib.load("model/lag_feature_scaler.pkl")
auto_target_scaler = joblib.load("model/lag_target_scaler.pkl")

baseline_model = joblib.load("model/rf_baseline_model.pkl")
feature_scaler = joblib.load("model/feature_scaler.pkl")
target_scaler = joblib.load("model/target_scaler.pkl")


# -------------------------------
# SAFE VALUE EXTRACTOR (CRITICAL FIX)
# -------------------------------
def get_value(df, i, col):
    val = df.loc[i, col]
    if isinstance(val, pd.Series):
        val = val.values[0]
    return float(val)


# -------------------------------
# PREDICTION FUNCTION
# -------------------------------
def predict_next_day(input_df):
    scaled_input = auto_feature_scaler.transform(input_df)
    pred_scaled = model.predict(scaled_input)

    prediction = auto_target_scaler.inverse_transform(
        pred_scaled.reshape(-1, 1)
    )[0][0]

    return float(round(prediction, 2))


# -------------------------------
# HOME
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------
# MANUAL PREDICTION
# -------------------------------
@app.route("/predict_manual", methods=["POST"])
def predict_manual():
    try:
        ticker = request.form["ticker"]

        open_price = float(request.form["open"])
        high_price = float(request.form["high"])
        low_price = float(request.form["low"])
        close_price = float(request.form["close"])
        volume = float(request.form["volume"])

        input_data = np.array([[open_price, high_price, low_price, close_price, volume]])

        scaled_input = feature_scaler.transform(input_data)
        pred_scaled = baseline_model.predict(scaled_input)

        predicted_close = target_scaler.inverse_transform(
            pred_scaled.reshape(-1, 1)
        )[0][0]

        # confidence
        tree_preds = [tree.predict(scaled_input)[0] for tree in baseline_model.estimators_]
        std = np.std(tree_preds)
        confidence = round(min(max(0, 100 - std * 10), 100), 2)

        direction = "BULLISH" if predicted_close > close_price else "BEARISH"
        percent_change = ((predicted_close - close_price) / close_price) * 100

        return jsonify({
            "ticker": ticker,
            "predicted_close": round(predicted_close, 2),
            "direction": direction,
            "change": round(percent_change, 2),
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)})


# -------------------------------
# AUTO PREDICTION (FIXED)
# -------------------------------
@app.route("/predict_auto", methods=["POST"])
def predict_auto():
    try:
        ticker = request.form["ticker"]
        selected_date = request.form["date"]

        data = yf.download(ticker, period="3mo", auto_adjust=True)

        if data is None or data.empty:
            return jsonify({"error": "No data found"})

        # 🔥 FIX MULTIINDEX
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna().reset_index()
        data["Date"] = pd.to_datetime(data["Date"]).dt.strftime("%Y-%m-%d")

        if selected_date not in data["Date"].values:
            return jsonify({"error": "Date not found in trading data"})

        i = data.index[data["Date"] == selected_date][0]

        if i < 3 or i >= len(data) - 1:
            return jsonify({"error": "Not enough data"})

        # ✅ SAFE EXTRACTION
        open_price = get_value(data, i, "Open")
        high_price = get_value(data, i, "High")
        low_price = get_value(data, i, "Low")
        close_today = get_value(data, i, "Close")

        close_lag1 = get_value(data, i - 1, "Close")
        close_lag2 = get_value(data, i - 2, "Close")
        close_lag3 = get_value(data, i - 3, "Close")

        volume_lag1 = get_value(data, i - 1, "Volume")

        input_df = pd.DataFrame([{
            "Open Price": open_price,
            "High Price": high_price,
            "Low Price": low_price,
            "Close_Lag_1": close_lag1,
            "Close_Lag_2": close_lag2,
            "Close_Lag_3": close_lag3,
            "Volume_Lag_1": volume_lag1
        }])

        prediction = predict_next_day(input_df)

        scaled_input = auto_feature_scaler.transform(input_df)
        tree_preds = [tree.predict(scaled_input)[0] for tree in model.estimators_]

        std = np.std(tree_preds)
        confidence = round(min(max(0, 100 - std * 10), 100), 2)

        direction = "BULLISH" if prediction > close_today else "BEARISH"
        percent_change = ((prediction - close_today) / close_today) * 100

        return jsonify({
            "predicted_close": prediction,
            "direction": direction,
            "change": round(percent_change, 2),
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# --------------------------------------------------
# CHART DATA
# --------------------------------------------------
@app.route("/get_chart_data", methods=["GET"])
def get_chart_data():

    try:

        ticker = request.args.get("ticker")

        if not ticker:
            return jsonify({"error":"Ticker missing"})

        data = yf.download(ticker, period="3mo")

        if data.empty:
            return jsonify({"error":"No data found"})

        chart_data = []

        for i in range(len(data)):

            date = data.index[i]
            close_price = data["Close"].iloc[i].item()

            chart_data.append({
                "time": date.strftime("%Y-%m-%d"),
                "value": close_price
            })

        return jsonify(chart_data)

    except Exception as e:

        return jsonify({"error": str(e)})
    
# -------------------------------
# BACKTEST (MATCHES AUTO)
# -------------------------------
@app.route("/backtest", methods=["GET"])
def backtest():
    try:
        ticker = request.args.get("ticker")

        data = yf.download(ticker, period="3mo", auto_adjust=True)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna().reset_index()

        predictions = []
        actuals = []
        dates = []

        for i in range(3, len(data) - 1):

            open_price = get_value(data, i, "Open")
            high_price = get_value(data, i, "High")
            low_price = get_value(data, i, "Low")

            close_lag1 = get_value(data, i - 1, "Close")
            close_lag2 = get_value(data, i - 2, "Close")
            close_lag3 = get_value(data, i - 3, "Close")

            volume_lag1 = get_value(data, i - 1, "Volume")

            input_df = pd.DataFrame([{
                "Open Price": open_price,
                "High Price": high_price,
                "Low Price": low_price,
                "Close_Lag_1": close_lag1,
                "Close_Lag_2": close_lag2,
                "Close_Lag_3": close_lag3,
                "Volume_Lag_1": volume_lag1
            }])

            prediction = predict_next_day(input_df)
            actual_next = get_value(data, i + 1, "Close")

            predictions.append(prediction)
            actuals.append(actual_next)
            dates.append(str(data.loc[i + 1, "Date"].date()))

        mae = round(np.mean(np.abs(np.array(predictions) - np.array(actuals))), 2)

        return jsonify({
            "dates": dates,
            "predictions": predictions,
            "actuals": actuals,
            "mae": mae
        })

    except Exception as e:
        return jsonify({"error": str(e)})


# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
