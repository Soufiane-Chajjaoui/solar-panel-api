#!/usr/bin/env python3
import requests

def test_cloudinary_prediction():
    """Test prediction with a Cloudinary image URL."""
    url = 'http://localhost:8000/predict'

    # Use a working image URL (simulating Cloudinary)
    image_url = 'https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=640&h=480&fit=crop'

    data = {
        'panel_id': 'P-TEST-3',
        'image_url': image_url
    }

    try:
        print("Testing prediction with Cloudinary image...")
        print(f"Image URL: {image_url}")

        response = requests.post(url, json=data)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Predicted: {result['predicted_class']} ({result['confidence']*100:.1f}%)")
            print(f"Panel ID: {result.get('panel_id')}")
            print(f"Timestamp: {result.get('timestamp')}")
            print(f"All fields: {list(result.keys())}")
            # Check if image_url is in the response
            if 'image_url' in result:
                print(f"Image URL stored: {result['image_url']}")
            else:
                print("Image URL not in response (but should be stored in DB)")
        else:
            print("Failed!")
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cloudinary_prediction()