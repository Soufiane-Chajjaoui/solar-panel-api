#!/usr/bin/env python3
"""
Test script for the feedback endpoint.
"""

import requests
import json

def test_feedback_endpoint():
    """Test the feedback endpoint."""
    url = 'http://localhost:8000/feedback'

    # Test data with real prediction details
    data = {
        'panel_id': 'P-TEST-3',
        'prediction_id': 'real_2025-11-20T10:38:48.704917Z_P-TEST-3',
        'is_correct': False,  # Test correction
        'predicted_class': 'Clean',
        'corrected_class': 'Dusty',
        'confidence': 0.90,
        'timestamp': '2025-11-20T10:38:48.704917Z',
        'reason': 'Human validation test - correcting AI prediction'
    }

    try:
        print("Testing feedback endpoint...")
        print("Sending:", json.dumps(data, indent=2))

        response = requests.post(url, json=data)

        print("Status Code:", response.status_code)

        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print("Response:", json.dumps(result, indent=2))
        else:
            print("Failed!")
            print("Error:", response.text)

    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_feedback_endpoint()