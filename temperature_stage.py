# ----------------------------------
# TEMPERATURE BASED STAGE PREDICTION
# ----------------------------------

# Base temperature
BASE_TEMP = 10

# -----------------------------
# INPUT TEMPERATURE
# -----------------------------
temp_max = float(input("Enter Maximum Temperature (°C): "))
temp_min = float(input("Enter Minimum Temperature (°C): "))

# -----------------------------
# CALCULATE GDD
# -----------------------------
gdd = ((temp_max + temp_min) / 2) - BASE_TEMP

# Avoid negative values
if gdd < 0:
    gdd = 0

print("\n====================================")
print(" FRUIT FLY STAGE PREDICTION ")
print("====================================")

print(f"Calculated GDD : {gdd:.2f}")

# -----------------------------
# STAGE PREDICTION
# -----------------------------
if gdd < 15:

    stage = "EGG STAGE"
    risk = "LOW"

    recommendations = [
        "Monitor orchard regularly",
        "Use preventive fruit fly traps",
        "Maintain field sanitation"
    ]

elif gdd < 25:

    stage = "LARVA STAGE"
    risk = "MEDIUM"

    recommendations = [
        "Apply biological pest control",
        "Use sticky traps",
        "Inspect nearby fruits carefully"
    ]

elif gdd < 35:

    stage = "PUPA STAGE"
    risk = "HIGH"

    recommendations = [
        "Remove infected fruits immediately",
        "Apply recommended pesticides",
        "Monitor orchard daily"
    ]

else:

    stage = "ADULT STAGE"
    risk = "VERY HIGH"

    recommendations = [
        "Immediate pesticide spray required",
        "Use pheromone traps",
        "Destroy severely infected fruits",
        "Continuous monitoring needed"
    ]

# -----------------------------
# DISPLAY RESULTS
# -----------------------------
print(f"Predicted Stage : {stage}")
print(f"Risk Level      : {risk}")

print("\nRECOMMENDATIONS:")

for rec in recommendations:
    print(f"✓ {rec}")

print("====================================")