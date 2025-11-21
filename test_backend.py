import requests

try:
    # Test the backend predict endpoint with the user's Cloudinary URL
    cloudinary_url = 'https://res.cloudinary.com/djkyys3rt/image/upload/v1763582225/smart-solar-panel-cleaner/panel_P-TEST-1_1763582223932.jpg'
    response = requests.post('http://localhost:8000/predict', json={'panel_id': 'P-TEST-1', 'image_url': cloudinary_url})
    print('Backend response status:', response.status_code)
    print('Backend response:', response.text)
except Exception as e:
    print('Backend test failed:', e)