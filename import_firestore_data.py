#!/usr/bin/env python3
"""
Firestore Data Import Script

This script imports JSON data into Firestore collections.
Make sure you have your serviceAccountKey.json in the project root.

Usage:
    python import_firestore_data.py
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

def import_collection_data(db, collection_name, filename):
    """Import data from JSON file into Firestore collection"""
    print(f"\nImporting {collection_name} from {filename}...")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        imported_count = 0

        for doc in data:
            # Generate appropriate document ID based on collection
            if collection_name == 'users':
                doc_id = doc['email']
            elif collection_name == 'solar_panel_data':
                # Create ID like: panel1_20251121081500000
                timestamp = doc['timestamp'].replace(':', '').replace('-', '').replace('.', '_')
                doc_id = f"{doc['panel_id']}_{timestamp}"
            elif collection_name == 'dl_predictions':
                # Create ID like: panel1_20251121081500000
                timestamp = doc['timestamp'].replace(':', '').replace('-', '').replace('.', '_')
                doc_id = f"{doc['panel_id']}_{timestamp}"
            elif collection_name == 'feedback':
                # Create ID like: feedback_panel2_20251121081200000
                timestamp = doc['submitted_at'].replace(':', '').replace('-', '').replace('.', '_')
                doc_id = f"feedback_{doc['panel_id']}_{timestamp}"
            else:
                # Fallback: use auto-generated ID
                doc_id = None

            # Convert timestamp strings to Firestore timestamps where needed
            if 'created_at' in doc and isinstance(doc['created_at'], str):
                try:
                    doc['created_at'] = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
                except:
                    pass  # Keep as string if conversion fails

            if 'updated_at' in doc and isinstance(doc['updated_at'], str):
                try:
                    doc['updated_at'] = datetime.fromisoformat(doc['updated_at'].replace('Z', '+00:00'))
                except:
                    pass

            if 'last_login' in doc and isinstance(doc['last_login'], str):
                try:
                    doc['last_login'] = datetime.fromisoformat(doc['last_login'].replace('Z', '+00:00'))
                except:
                    pass

            # Set document in Firestore
            if doc_id:
                db.collection(collection_name).document(doc_id).set(doc)
                print(f"  Imported {doc_id}")
            else:
                db.collection(collection_name).add(doc)
                print(f"  Imported with auto-generated ID")

            imported_count += 1

        print(f"Successfully imported {imported_count} documents into {collection_name}")
        return True

    except FileNotFoundError:
        print(f"File not found: {filename}")
        return False
    except Exception as e:
        print(f"Error importing {collection_name}: {e}")
        return False

def main():
    print("Firestore Data Import Script")
    print("=" * 40)

    # Check if service account key exists
    service_account_path = "serviceAccountKey.json"
    if not os.path.exists(service_account_path):
        print(f"Service account key not found: {service_account_path}")
        print("Please place your serviceAccountKey.json in the project root.")
        return

    try:
        # Initialize Firebase Admin SDK
        print("Initializing Firebase Admin SDK...")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

        db = firestore.client()
        print("Connected to Firestore")

        # Collections to import
        collections = {
            'solar_panel_data': 'solar_panel_data.json',
            'dl_predictions': 'dl_predictions.json',
            'feedback': 'feedback.json',
            'users': 'users.json'
        }

        # Import each collection
        success_count = 0
        for collection_name, filename in collections.items():
            if import_collection_data(db, collection_name, filename):
                success_count += 1

        print(f"\nImport completed! {success_count}/{len(collections)} collections imported successfully.")

        if success_count == len(collections):
            print("\nNext steps:")
            print("1. Update panel_routes.py to use real Firestore queries")
            print("2. Remove mock data from the endpoints")
            print("3. Restart your backend server")
            print("4. Test the endpoints: curl http://localhost:8000/panels")

    except Exception as e:
        print(f"Firebase initialization error: {e}")
        print("Make sure your serviceAccountKey.json is valid and has proper permissions.")

if __name__ == "__main__":
    main()