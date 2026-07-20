import os
import sqlite3
from functools import wraps
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, send_file, session, redirect, url_for
from openpyxl import Workbook
import tensorflow as tf
import numpy as np
from tensorflow.keras.utils import load_img, img_to_array
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# NOTE: Change this to a long random value before deploying publicly.
app.secret_key = "fruitfly-phenology-dev-secret-key-change-me"

# ==========================
# Upload Folder
# ==========================

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HISTORY_FILE = "prediction_history.xlsx"


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ==========================
# User Database (SQLite)
# ==========================

DB_FILE = os.path.join(app.root_path, "users.db")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapped


# ==========================
# Register
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password:
        return render_template("register.html", error="❌ Please fill in all fields.",
                                form_name=name, form_email=email)

    if password != confirm_password:
        return render_template("register.html", error="❌ Passwords do not match.",
                                form_name=name, form_email=email)

    if len(password) < 6:
        return render_template("register.html", error="❌ Password must be at least 6 characters.",
                                form_name=name, form_email=email)

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()

    if existing:
        conn.close()
        return render_template("register.html", error="❌ An account with this email already exists.",
                                form_name=name, form_email=email)

    conn.execute(
        "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
        (name, email, generate_password_hash(password), datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    return render_template("login.html", success="✅ Account created successfully. Please login.")


# ==========================
# Login
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if user is None or not check_password_hash(user["password"], password):
        return render_template("login.html", error="❌ Invalid email or password.")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    return redirect(url_for("dashboard"))


# ==========================
# Logout
# ==========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==========================
# Load Models
# ==========================

fruitfly_model = tf.keras.models.load_model("model.keras")
mango_model = tf.keras.models.load_model("mango_detector.keras")

# ==========================
# Dashboard (Home)
# ==========================

@app.route("/")
@login_required
def dashboard():

    total_predictions = 0

    if os.path.exists(HISTORY_FILE):
        try:
            history = pd.read_excel(HISTORY_FILE)
            if "User Email" in history.columns:
                total_predictions = len(history[history["User Email"] == session.get("user_email")])
            else:
                total_predictions = len(history)
        except Exception:
            total_predictions = 0

    return render_template(
        "dashboard.html",
        active="dashboard",
        total_predictions=total_predictions
    )


# ==========================
# New Prediction (Form Page)
# ==========================

@app.route("/predict", methods=["GET"])
@login_required
def predict_page():
    return render_template("predict.html", active="predict")


# ==========================
# Predict (Process Form)
# ==========================

@app.route("/predict", methods=["POST"])
@login_required
def predict():

    # ----------------------
    # Upload Image
    # ----------------------

    if "image" not in request.files:
        return render_template(
            "predict.html",
            active="predict",
            error="❌ No image file was uploaded.",
            error_tamil="❌ படம் எதுவும் பதிவேற்றப்படவில்லை. தயவுசெய்து ஒரு படத்தை தேர்வு செய்யவும்."
        )

    file = request.files["image"]

    if file.filename == "":
        return render_template(
            "predict.html",
            active="predict",
            error="❌ No file selected.",
            error_tamil="❌ எந்த கோப்பும் தேர்ந்தெடுக்கப்படவில்லை."
        )

    if not allowed_file(file.filename):
        return render_template(
            "predict.html",
            active="predict",
            error="❌ Invalid file type. Please upload a PNG or JPG image.",
            error_tamil="❌ தவறான கோப்பு வகை. PNG அல்லது JPG படத்தை பதிவேற்றவும்."
        )

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    # ----------------------
    # Mango Detection
    # ----------------------

    img = load_img(
        filepath,
        target_size=(224, 224)
    )

    img_array = img_to_array(img)
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    mango_prediction = mango_model.predict(img_array)

    mango_probability = float(mango_prediction[0][0])

    print("=" * 40)
    print("Image:", filename)
    print("Raw Prediction:", mango_prediction)
    print("Probability:", mango_probability)
    print("=" * 40)

    # If your Mango folder was alphabetically first,
    # probability < 0.5 means Mango.
    # If results are reversed later, we'll change one line.

    if mango_probability > 0.5:

        return render_template(
            "predict.html",
            active="predict",
            error="❌ This is NOT a Mango image.",
            error_tamil="❌ இது மாம்பழம் அல்ல. தயவுசெய்து மாம்பழ படத்தை பதிவேற்றவும்."
        )

    # ----------------------
    # Fruit Fly Prediction
    # ----------------------

    prediction = fruitfly_model.predict(img_array)

    probability = float(prediction[0][0])
    # -------------------------
    # Healthy / Infected
    # -------------------------

    if probability > 0.5:

        predicted_class = "INFECTED"
        prediction_tamil = "பாதிக்கப்பட்டது"

        confidence = probability * 100

    else:

        predicted_class = "HEALTHY"
        prediction_tamil = "ஆரோக்கியமானது"

        confidence = (1 - probability) * 100

    # -------------------------
    # Temperature
    # -------------------------

    try:
        temp_max = float(request.form["temp_max"])
        temp_min = float(request.form["temp_min"])
    except (KeyError, ValueError):
        return render_template(
            "predict.html",
            active="predict",
            error="❌ Please enter valid maximum and minimum temperature values.",
            error_tamil="❌ சரியான அதிகபட்ச மற்றும் குறைந்தபட்ச வெப்பநிலை மதிப்புகளை உள்ளிடவும்."
        )

    BASE_TEMP = 10

    gdd = ((temp_max + temp_min) / 2) - BASE_TEMP

    if gdd < 0:
        gdd = 0

    # -------------------------
    # Fruit Fly Stage
    # -------------------------

    if gdd < 15:

        stage = "Egg Stage"
        stage_tamil = "முட்டை நிலை"

        stage_image = "stages/egg.jpg"

    elif gdd < 25:

        stage = "Larva Stage"
        stage_tamil = "புழு நிலை"

        stage_image = "stages/larva.jpg"

    elif gdd < 35:

        stage = "Pupa Stage"
        stage_tamil = "கூட்டு நிலை"

        stage_image = "stages/pupa.jpg"

    else:

        stage = "Adult Stage"
        stage_tamil = "முதிர்ந்த பழ ஈ"

        stage_image = "stages/adult.jpg"

    # -------------------------
    # Risk & Recommendation
    # -------------------------

    if predicted_class == "HEALTHY":

        risk = "SAFE"
        risk_tamil = "பாதுகாப்பானது"

        if stage == "Egg Stage":

            recommendation = "Healthy mango detected. Continue monitoring and install yellow sticky traps as a preventive measure."

            recommendation_tamil = "மாம்பழம் ஆரோக்கியமாக உள்ளது. தொடர்ந்து கண்காணித்து மஞ்சள் ஒட்டும் பொறிகளை அமைக்கவும்."

        elif stage == "Larva Stage":

            recommendation = "Healthy mango detected. Inspect fruits every 2-3 days and install pheromone traps."

            recommendation_tamil = "மாம்பழம் ஆரோக்கியமாக உள்ளது. 2-3 நாட்களுக்கு ஒருமுறை பரிசோதித்து பெரோமோன் பொறிகளை அமைக்கவும்."

        elif stage == "Pupa Stage":

            recommendation = "Healthy mango detected. Maintain orchard sanitation and remove fallen fruits."

            recommendation_tamil = "மாம்பழம் ஆரோக்கியமாக உள்ளது. தோட்டத்தை சுத்தமாக வைத்திருந்து விழுந்த பழங்களை அகற்றவும்."

        else:

            recommendation = "Healthy mango detected. Adult fruit flies are active. Increase monitoring and install methyl eugenol traps."

            recommendation_tamil = "மாம்பழம் ஆரோக்கியமாக உள்ளது. முதிர்ந்த பழ ஈக்கள் செயல்பாட்டில் உள்ளன. கண்காணிப்பை அதிகரித்து மெத்தில் யூஜினால் பொறிகளை அமைக்கவும்."

    else:

        if stage == "Egg Stage":

            risk = "MODERATE"
            risk_tamil = "மிதமான ஆபத்து"

            recommendation = "Early infection detected. Remove suspected fruits and begin preventive control immediately."

            recommendation_tamil = "ஆரம்ப பாதிப்பு கண்டறியப்பட்டது. சந்தேகப்படும் பழங்களை அகற்றி உடனடியாக கட்டுப்பாட்டு நடவடிக்கைகளை தொடங்கவும்."

        elif stage == "Larva Stage":

            risk = "HIGH"
            risk_tamil = "அதிக ஆபத்து"

            recommendation = "Larval infestation detected. Remove infected fruits, install pheromone traps and apply recommended insecticide."

            recommendation_tamil = "புழு தாக்குதல் கண்டறியப்பட்டது. பாதிக்கப்பட்ட பழங்களை அகற்றி பெரோமோன் பொறிகளை அமைத்து பரிந்துரைக்கப்பட்ட பூச்சிக்கொல்லியை பயன்படுத்தவும்."

        elif stage == "Pupa Stage":

            risk = "HIGH"
            risk_tamil = "அதிக ஆபத்து"

            recommendation = "Pupal stage detected. Destroy fallen fruits and manage orchard soil to reduce pest emergence."

            recommendation_tamil = "கூட்டு நிலை கண்டறியப்பட்டது. விழுந்த பழங்களை அழித்து தோட்ட மண்ணை சரியாக பராமரிக்கவும்."

        else:

            risk = "VERY HIGH"
            risk_tamil = "மிக அதிக ஆபத்து"

            recommendation = "Severe infestation risk. Immediately remove infected fruits, install traps and spray recommended insecticide."

            recommendation_tamil = "கடுமையான தாக்குதல் அபாயம். பாதிக்கப்பட்ட பழங்களை உடனடியாக அகற்றி பொறிகளை அமைத்து பரிந்துரைக்கப்பட்ட பூச்சிக்கொல்லியை தெளிக்கவும்."

    # -------------------------
    # Save Prediction History
    # -------------------------

    new_data = {
        "Date & Time": [datetime.now().strftime("%d-%m-%Y %H:%M:%S")],
        "User Name": [session.get("user_name", "Unknown")],
        "User Email": [session.get("user_email", "")],
        "Image": [filename],
        "Prediction": [predicted_class],
        "Confidence (%)": [round(confidence, 2)],
        "Risk": [risk],
        "Stage": [stage],
        "GDD": [round(gdd, 2)]
    }

    new_df = pd.DataFrame(new_data)

    if os.path.exists(HISTORY_FILE):

        old_df = pd.read_excel(HISTORY_FILE)

        updated_df = pd.concat(
            [old_df, new_df],
            ignore_index=True
        )

    else:

        updated_df = new_df

    updated_df.to_excel(
        HISTORY_FILE,
        index=False
    )

    # -------------------------
    # Return Results
    # -------------------------

    return render_template(

        "result.html",
        active="predict",

        prediction=predicted_class,
        prediction_tamil=prediction_tamil,

        confidence=round(confidence, 2),

        risk=risk,
        risk_tamil=risk_tamil,

        stage=stage,
        stage_tamil=stage_tamil,

        stage_image=stage_image,

        gdd=round(gdd, 2),

        recommendation=recommendation,
        recommendation_tamil=recommendation_tamil,

        uploaded_image=filename

    )


# ==========================
# Prediction History
# ==========================

@app.route("/history")
@login_required
def history_page():

    columns = []
    rows = []

    if os.path.exists(HISTORY_FILE):
        try:
            history = pd.read_excel(HISTORY_FILE)

            if "User Email" in history.columns:
                history = history[history["User Email"] == session.get("user_email")]

            columns = list(history.columns)
            rows = history.to_dict(orient="records")
        except Exception:
            columns = []
            rows = []

    return render_template(
        "history.html",
        active="history",
        columns=columns,
        rows=rows
    )


# ==========================
# About
# ==========================

@app.route("/about")
@login_required
def about_page():
    return render_template("about.html", active="about")


# ==========================
# Download Report
# ==========================

@app.route("/download")
@login_required
def download():

    wb = Workbook()
    ws = wb.active

    ws.title = "Fruit Fly Report"

    ws.append(["AI Based Oriental Fruit Fly Detection Report"])
    ws.append([])

    ws.append(["Generated For", session.get("user_name", "Unknown")])
    ws.append(["Generated On", datetime.now().strftime("%d-%m-%Y %H:%M:%S")])
    ws.append([])

    if os.path.exists(HISTORY_FILE):

        history = pd.read_excel(HISTORY_FILE)

        if "User Email" in history.columns:
            history = history[history["User Email"] == session.get("user_email")]

        ws.append(list(history.columns))

        for row in history.values.tolist():
            ws.append(row)

    report_path = f"FruitFly_Report_{session.get('user_id', 'guest')}.xlsx"

    wb.save(report_path)

    return send_file(
        report_path,
        as_attachment=True
    )


# ==========================
# Run Flask App
# ==========================

import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7860))
    )