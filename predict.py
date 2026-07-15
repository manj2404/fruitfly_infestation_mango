import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image

# ----------------------------
# LOAD TRAINED MODEL
# ----------------------------
model = tf.keras.models.load_model("model.keras")

# ----------------------------
# IMAGE PATH
# ----------------------------
img_path = "test.jpg"

# ----------------------------
# LOAD IMAGE
# ----------------------------
img = image.load_img(img_path, target_size=(224, 224))

# Convert image to array
img_array = image.img_to_array(img)

# Normalize image
img_array = img_array / 255.0

# Expand dimensions
img_array = np.expand_dims(img_array, axis=0)

# ----------------------------
# PREDICTION
# ----------------------------
prediction = model.predict(img_array)

# Confidence score
confidence = float(np.max(prediction) * 100)

# ----------------------------
# CLASS LABELS
# ----------------------------
classes = ["healthy", "infected"]

# Predicted class
predicted_class = classes[int(prediction[0][0] > 0.5)]

# ----------------------------
# DISPLAY RESULT
# ----------------------------
print("\n====================================")
print("   FRUIT FLY DETECTION RESULT")
print("====================================")

print(f"Prediction    : {predicted_class.upper()}")
print(f"Confidence    : {confidence:.2f}%")

# ----------------------------
# CONFIDENCE WARNING
# ----------------------------
if confidence < 80:
    print("Warning       : Low confidence prediction")

# ----------------------------
# HEALTHY CONDITION
# ----------------------------
if predicted_class == "healthy":

    print("Risk Level    : SAFE")

    print("\nRECOMMENDATION:")
    print("✓ Crop condition is good")
    print("✓ Continue regular monitoring")
    print("✓ Maintain field sanitation")
    print("✓ Use preventive fruit fly traps")

# ----------------------------
# INFECTED CONDITION
# ----------------------------
else:

    # Risk Level
    if confidence > 90:
        risk = "HIGH"
    elif confidence > 75:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    print(f"Risk Level    : {risk}")

    print("\nRECOMMENDATION:")

    # High Risk
    if risk == "HIGH":
        print("✓ Immediate pesticide spray required")
        print("✓ Use pheromone traps")
        print("✓ Remove infected fruits")
        print("✓ Monitor orchard daily")

    # Medium Risk
    elif risk == "MEDIUM":
        print("✓ Apply biological pest control")
        print("✓ Use sticky traps")
        print("✓ Inspect nearby fruits")

    # Low Risk
    else:
        print("✓ Continue observation")
        print("✓ Early symptoms detected")
        print("✓ Use preventive measures")

print("====================================")