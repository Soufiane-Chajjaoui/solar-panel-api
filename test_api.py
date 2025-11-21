#!/usr/bin/env python3
import requests

def test_api():
    try:
        # Test health
        r = requests.get('http://localhost:8000/health', timeout=5)
        print(f'Health check: {r.status_code}')

        if r.status_code == 200:
            print('Server is responding')

            # Test predictions API without panel filter first
            r2 = requests.get('http://localhost:8000/history/predictions?limit=5', timeout=10)
            print(f'Predictions API (all): {r2.status_code}')

            if r2.status_code == 200:
                data = r2.json()
                predictions = data.get('predictions', [])
                print(f'Found {len(predictions)} total predictions')
                if predictions:
                    print(f'Latest: {predictions[0].get("predicted_class")} ({predictions[0].get("confidence", 0):.2f})')
                    print(f'Panel: {predictions[0].get("panel_id")}')
                    print(f'Image: {predictions[0].get("image_url", "None")[:50]}...')

                    # Now test with panel filter
                    r3 = requests.get('http://localhost:8000/history/predictions?panel_id=P-TEST-3&limit=5', timeout=10)
                    print(f'Predictions API (P-TEST-3): {r3.status_code}')
                    if r3.status_code == 200:
                        data3 = r3.json()
                        predictions3 = data3.get('predictions', [])
                        print(f'Found {len(predictions3)} predictions for P-TEST-3')
            else:
                print(f'API Error: {r2.text}')
        else:
            print('Server not responding')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_api()