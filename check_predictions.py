#!/usr/bin/env python3
import requests

def check_predictions():
    try:
        response = requests.get('http://localhost:8000/history/predictions?limit=10')
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f'Real predictions found: {len(predictions)}')
            for i, pred in enumerate(predictions[:3]):
                print(f'  {i+1}. {pred.get("panel_id")}: {pred.get("predicted_class")} ({pred.get("confidence", 0):.2f})')
                print(f'     Image: {pred.get("image_url", "None")}')
                print(f'     Timestamp: {pred.get("timestamp")}')
        else:
            print(f'Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_predictions()