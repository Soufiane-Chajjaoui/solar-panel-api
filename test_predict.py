import requests

# Test the health endpoint
try:
    response = requests.get('http://localhost:8000/health')
    print("Health check:", response.json())
except Exception as e:
    print("Health check failed:", e)

# Test the predict endpoint with a dummy image URL
try:
    data = {
        "panel_id": "test_panel_1",
        "image_url": "https://via.placeholder.com/224x224.jpg"  # Placeholder image
    }
    response = requests.post('http://localhost:8000/predict', json=data)
    print("Predict response status:", response.status_code)
    print("Predict response:", response.json())
except Exception as e:
    print("Predict test failed:", e)