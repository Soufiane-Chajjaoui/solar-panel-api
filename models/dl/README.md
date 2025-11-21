# Deep Learning Model - MobileNet Solar Panel Cleaner

This directory contains the deep learning model for solar panel image classification.

## Model File

- `mobilenet_solar_final.keras`: Pre-trained MobileNet model for classifying solar panels as clean or dirty

Link : https://drive.google.com/file/d/1YPr2HAaA4AI4q2v8konA1rO7ah2kwKm0/view?usp=drive_link

## Usage

### Test with an Image

Use the test script to test the model with an image:

```bash
python test_dl_model.py path/to/your/image.jpg
```

### Use in Code

```python
from app.services.dl_service import predict_from_image

# Test with an image file
result = predict_from_image("C:/Users/SAMSUNG/Desktop/M2 ADIA/IoT/nettoyant intelligentes pour panneau solaire/images/SC.jpg")

if result:
    print(f"Prediction: {result['dl_prediction']}")  # "clean" or "dirty"
    print(f"Confidence: {result['dl_confidence']}")   # 0.0 to 1.0
    print(f"Probabilities: {result['dl_probability']}")  # {"clean": 0.x, "dirty": 0.y}
```

### Supported Image Formats

The model accepts:
- Image file paths (str or Path)
- PIL Image objects
- NumPy arrays
- Bytes of an image
- Base64 encoded strings

### Output Format

```json
{
  "dl_prediction": "clean" | "dirty",
  "dl_confidence": 0.95,
  "dl_probability": {
    "clean": 0.95,
    "dirty": 0.05
  }
}
```

## Requirements

Make sure you have installed TensorFlow:

```bash
pip install tensorflow>=2.13.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

