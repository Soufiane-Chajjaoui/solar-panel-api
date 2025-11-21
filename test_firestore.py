#!/usr/bin/env python3
import sys
sys.path.append('.')

from app.services.firestore_service import FirestoreService

def test_firestore():
    print("Testing FirestoreService directly...")

    # Test without panel filter
    print("\n1. Getting all predictions:")
    all_preds = FirestoreService.get_predictions(limit=5)
    print(f"Found {len(all_preds)} predictions")
    for pred in all_preds:
        print(f"  - {pred.get('panel_id')}: {pred.get('predicted_class')}")

    # Test with panel filter
    print("\n2. Getting predictions for P-TEST-3:")
    filtered_preds = FirestoreService.get_predictions(panel_id="P-TEST-3", limit=5)
    print(f"Found {len(filtered_preds)} predictions")
    for pred in filtered_preds:
        print(f"  - {pred.get('panel_id')}: {pred.get('predicted_class')}")

if __name__ == "__main__":
    test_firestore()