import joblib
import numpy as np

# Load scaler and model
scaler = joblib.load('scaler.joblib')
model = joblib.load('best_model_GradientBoosting.joblib')

# Example raw data simulated from sensors
R, G, B = 142, 136, 125
data = {
    "temperature": 33.5,
    "humidity": 45.2,
    "light": 380,
    "R": R, "G": G, "B": B
}
# Derived features
data["RGB_mean"] = (R + G + B) / 3.0
data["RGB_std"] = np.std([R, G, B])
data["G_over_R"] = G / (R + 1e-6)
data["B_over_R"] = B / (R + 1e-6)

# Build feature vector in correct order
X = np.array([[data["temperature"], data["humidity"], data["light"],
               data["R"], data["G"], data["B"],
               data["RGB_mean"], data["RGB_std"],
               data["G_over_R"], data["B_over_R"]]])

# Scale and predict
X_scaled = scaler.transform(X)
pred = model.predict(X_scaled)[0]
prob = model.predict_proba(X_scaled)[0][1] if hasattr(model, "predict_proba") else None

print("Prediction:", int(pred), "(1=dirty, 0=clean)")
print("Probability:", prob)
