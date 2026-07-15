import os
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, send_file
from openpyxl import Workbook
import tensorflow as tf
import numpy as np
from tensorflow.keras.utils import load_img, img_to_array
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
# Load Models
# ==========================

fruitfly_model = tf.keras.models.load_model("model.keras")
mango_model = tf.keras.models.load_model("mango_detector.keras")

# ==========================
# Dashboard (Home)
# ==========================

@app.route("/")
def dashboard():

    total_predictions = 0

    if os.path.exists(HISTORY_FILE):
        try:
            history = pd.read_excel(HISTORY_FILE)
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
def predict_page():
    return render_template("predict.html", active="predict")


# ==========================
# Predict (Process Form)
# ==========================

@app.route("/predict", methods=["POST"])
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

    print("Mango Probability:", mango_probability)

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

        recommendation = """Crop condition is good.
Continue regular monitoring.
Maintain orchard sanitation.
Use preventive fruit fly traps."""

        recommendation_tamil = """பயிர் நல்ல நிலையில் உள்ளது.
தொடர்ந்து கண்காணிக்கவும்.
தோட்டத்தை சுத்தமாக வைத்திருக்கவும்.
முன்கூட்டியே பழ ஈ பொறிகளை அமைக்கவும்."""

    else:

        if stage == "Adult Stage":

            risk = "VERY HIGH"
            risk_tamil = "மிக அதிக ஆபத்து"

        else:

            risk = "HIGH"
            risk_tamil = "அதிக ஆபத்து"

        recommendation = """Infection detected.
Remove infected fruits.
Spray recommended pesticide.
Install pheromone traps.
Monitor orchard daily."""

        recommendation_tamil = """பாதிப்பு கண்டறியப்பட்டது.
பாதிக்கப்பட்ட பழங்களை அகற்றவும்.
பரிந்துரைக்கப்பட்ட பூச்சிக்கொல்லியை தெளிக்கவும்.
பெரோமோன் பொறிகளை அமைக்கவும்.
தோட்டத்தை தினமும் கண்காணிக்கவும்."""

    # -------------------------
    # Save Prediction History
    # -------------------------

    new_data = {
        "Date & Time": [datetime.now().strftime("%d-%m-%Y %H:%M:%S")],
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
def history_page():

    columns = []
    rows = []

    if os.path.exists(HISTORY_FILE):
        try:
            history = pd.read_excel(HISTORY_FILE)
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
def about_page():
    return render_template("about.html", active="about")


# ==========================
# Download Report
# ==========================

@app.route("/download")
def download():

    wb = Workbook()
    ws = wb.active

    ws.title = "Fruit Fly Report"

    ws.append(["AI Based Oriental Fruit Fly Detection Report"])
    ws.append([])

    ws.append(["Generated On", datetime.now().strftime("%d-%m-%Y %H:%M:%S")])
    ws.append([])

    if os.path.exists(HISTORY_FILE):

        history = pd.read_excel(HISTORY_FILE)

        ws.append(list(history.columns))

        for row in history.values.tolist():
            ws.append(row)

    report_path = "FruitFly_Report.xlsx"

    wb.save(report_path)

    return send_file(
        report_path,
        as_attachment=True
    )


# ==========================
# Run Flask App
# ==========================

if __name__ == "__main__":

    app.run(debug=True)