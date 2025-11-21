#!/usr/bin/env python3
import requests

def check_panels():
    try:
        response = requests.get('http://localhost:8000/history/predictions?limit=20')
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f'Total predictions: {len(predictions)}')

            # Group by panel_id
            panels = {}
            for pred in predictions:
                panel_id = pred.get('panel_id')
                if panel_id not in panels:
                    panels[panel_id] = []
                panels[panel_id].append(pred)

            for panel_id, preds in panels.items():
                print(f'\n{panel_id}: {len(preds)} predictions')
                for i, pred in enumerate(preds[:2]):  # Show first 2
                    print(f'  {i+1}. {pred.get("predicted_class")} ({pred.get("confidence", 0):.2f}) - {pred.get("timestamp")[:19]}')
        else:
            print('Error:', response.status_code)
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_panels()