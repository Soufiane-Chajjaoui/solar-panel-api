#!/usr/bin/env python3
import requests

def debug_panel_ids():
    try:
        # Get all predictions
        response = requests.get('http://localhost:8000/history/predictions?limit=20')
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])

            print(f'Total predictions: {len(predictions)}')
            panel_ids = set()

            for pred in predictions:
                panel_id = pred.get('panel_id')
                panel_ids.add(panel_id)
                print(f'Panel ID: "{panel_id}" (type: {type(panel_id)})')

            print(f'\nUnique panel IDs: {sorted(panel_ids)}')

            # Check if P-TEST-3 exists
            p_test_3_preds = [p for p in predictions if p.get('panel_id') == 'P-TEST-3']
            print(f'Predictions with panel_id="P-TEST-3": {len(p_test_3_preds)}')

        else:
            print(f'Error: {response.status_code}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    debug_panel_ids()