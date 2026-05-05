from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
import joblib
import pandas as pd
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mini_grid_secret_key"

# Load AI model
model = joblib.load("fault_model.pkl")

# Login credentials
USERNAME = "admin"
PASSWORD = "1234"

# Store latest data
latest_data = {
    "panel_voltage": 0,
    "panel_current": 0,
    "battery_voltage": 0,
    "inverter_temp": 0,
    "load_current": 0
}

prediction_result = "normal"
fault_label = "Normal Operation"

# Store history for charts
history = {
    "panel_voltage": [],
    "panel_current": [],
    "battery_voltage": [],
    "inverter_temp": [],
    "load_current": []
}

MAX_HISTORY = 20


# =========================
# LOGIN PAGE
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# =========================
# DASHBOARD PAGE
# =========================
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("dashboard.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# =========================
# FAULT TYPE DETECTION LOGIC
# =========================
def detect_fault_type(data):
    if data["panel_voltage"] > 52:
        return "Panel Overvoltage"
    elif data["panel_voltage"] < 48:
        return "Panel Undervoltage"
    elif data["battery_voltage"] > 52:
        return "Battery Overvoltage"
    elif data["battery_voltage"] < 48:
        return "Battery Undervoltage"
    elif data["inverter_temp"] > 50:
        return "Inverter Overheating"
    elif data["load_current"] > 5:
        return "Load Overcurrent"
    else:
        return "Normal Operation"


# =========================
# RECEIVE SENSOR DATA
# =========================
@app.route("/predict", methods=["POST"])
def predict():
    global latest_data, prediction_result, history, fault_label

    data = request.get_json()

    latest_data = {
        "panel_voltage": float(data.get("panel_voltage", 0)),
        "panel_current": float(data.get("panel_current", 0)),
        "battery_voltage": float(data.get("battery_voltage", 0)),
        "inverter_temp": float(data.get("inverter_temp", 0)),
        "load_current": float(data.get("load_current", 0))
    }

    # AI prediction
    input_df = pd.DataFrame([latest_data])
    prediction = model.predict(input_df)[0]
    prediction_result = "fault" if prediction == 1 else "normal"

    # Fault label
    fault_label = detect_fault_type(latest_data)

    # Save history
    for key in history:
        history[key].append(latest_data[key])
        if len(history[key]) > MAX_HISTORY:
            history[key].pop(0)

    return jsonify({
        "prediction": prediction_result,
        "fault_label": fault_label
    })


# =========================
# SEND LIVE DATA TO DASHBOARD
# =========================
@app.route("/latest")
def latest():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401

    # Dynamic health score
    health_score = 100
    if fault_label != "Normal Operation":
        health_score = 65

    return jsonify({
        "latest_data": latest_data,
        "prediction": prediction_result,
        "fault_label": fault_label,
        "history": history,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "health_score": health_score
    })


# =========================
# DOWNLOAD CSV REPORT
# =========================
@app.route("/download")
def download():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Timestamp",
        "Panel Voltage",
        "Panel Current",
        "Battery Voltage",
        "Inverter Temp",
        "Load Current",
        "Prediction",
        "Fault Label"
    ])

    max_len = max(len(history["panel_voltage"]), 1)

    for i in range(max_len):
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            history["panel_voltage"][i] if i < len(history["panel_voltage"]) else "",
            history["panel_current"][i] if i < len(history["panel_current"]) else "",
            history["battery_voltage"][i] if i < len(history["battery_voltage"]) else "",
            history["inverter_temp"][i] if i < len(history["inverter_temp"]) else "",
            history["load_current"][i] if i < len(history["load_current"]) else "",
            prediction_result,
            fault_label
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=mini_grid_report.csv"
    response.headers["Content-type"] = "text/csv"
    return response


if __name__ == "__main__":
    app.run(debug=True)