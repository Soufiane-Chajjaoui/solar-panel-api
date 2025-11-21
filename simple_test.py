from app.services.dl_service import load_dl_model, is_dl_model_loaded
import numpy as np
from PIL import Image
import io

print("Testing DL model loading...")
model = load_dl_model()
print(f"Model loaded: {model is not None}")
print(f"Is model loaded: {is_dl_model_loaded()}")

# Create a simple test image (224x224 RGB)
test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
pil_image = Image.fromarray(test_image)

print("Testing prediction with random image...")
from app.services.dl_service import predict_from_image
result = predict_from_image(pil_image)
print(f"Prediction successful: {result is not None}")
if result:
    print(f"Predicted class: {result['dl_prediction']}")
    print(f"Confidence: {result['dl_confidence']:.4f}")
    print(f"Status: {result['dl_status']}")