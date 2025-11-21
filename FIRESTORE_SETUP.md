# Firestore Collections Setup

This guide explains how to recreate your Firestore collections in a new Firebase project using the provided JSON files.

## 📁 Available Collection Files

1. **`solar_panel_data.json`** - Main sensor data and ML predictions
2. **`dl_predictions.json`** - Deep learning prediction history
3. **`feedback.json`** - Human validation feedback
4. **`users.json`** - User accounts and authentication data

## 🚀 How to Import Data

### Method 1: Firebase Admin SDK (Recommended)

1. **Install Firebase Admin SDK** in your project:
   ```bash
   pip install firebase-admin
   ```

2. **Create a Python script** to import the data:
   ```python
   import firebase_admin
   from firebase_admin import credentials, firestore
   import json

   # Initialize Firebase Admin SDK
   cred = credentials.Certificate("path/to/serviceAccountKey.json")
   firebase_admin.initialize_app(cred)

   db = firestore.client()

   # Import each collection
   collections = {
       'solar_panel_data': 'solar_panel_data.json',
       'dl_predictions': 'dl_predictions.json',
       'feedback': 'feedback.json',
       'users': 'users.json'
   }

   for collection_name, filename in collections.items():
       with open(filename, 'r') as f:
           data = json.load(f)

       for doc in data:
           # Use appropriate document ID
           if collection_name == 'users':
               doc_id = doc['email']
           elif collection_name == 'solar_panel_data':
               doc_id = f"{doc['panel_id']}_{doc['timestamp'].replace(':', '').replace('-', '').replace('.', '_')}"
           elif collection_name == 'dl_predictions':
               doc_id = f"{doc['panel_id']}_{doc['timestamp'].replace(':', '').replace('-', '').replace('.', '_')}"
           elif collection_name == 'feedback':
               doc_id = f"feedback_{doc['panel_id']}_{doc['submitted_at'].replace(':', '').replace('-', '').replace('.', '_')}"

           db.collection(collection_name).document(doc_id).set(doc)
           print(f"Imported {doc_id} into {collection_name}")
   ```

### Method 2: Firebase Console

1. **Go to Firebase Console** → Your Project → Firestore Database
2. **Create collections** manually:
   - `solar_panel_data`
   - `dl_predictions`
   - `feedback`
   - `users`

3. **Import JSON data** using the Firebase Console import feature or write a script to add documents one by one.

## 🔄 Switch Back to Real Data

Once you've imported the data, update your backend to use real Firestore queries:

### 1. Update `app/routes/panel_routes.py`

Replace the mock data section with real Firestore queries:

```python
# Remove this mock data block:
# mock_panels = [...]
# return mock_panels

# Uncomment and use this instead:
if db is None:
    logger.warning("⚠️ Firestore non disponible - retour liste vide")
    return []

# Query the solar_panel_data collection
docs = db.collection("solar_panel_data").order_by("timestamp", direction="DESCENDING").limit(100).stream()

# Group by panel_id to get the latest data for each panel
panels_data = {}
for doc in docs:
    data = doc.to_dict()
    panel_id = data.get("panel_id")

    if panel_id and panel_id not in panels_data:
        panels_data[panel_id] = data

# Convert to PanelResponse format
panels = []
for panel_id, data in panels_data.items():
    # ... (rest of the conversion logic)
```

### 2. Update Individual Panel Endpoint

Replace the mock data in `get_panel()` function with real Firestore queries.

### 3. Test Your Setup

1. **Restart your backend**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. **Test the endpoints**:
   ```bash
   curl http://localhost:8000/panels
   curl http://localhost:8000/panels/panel1
   ```

## 📊 Collection Structures

### solar_panel_data
- **Purpose**: Real-time sensor data and ML predictions
- **Key Fields**: panel_id, timestamp, temperature, humidity, light, ml_prediction, ml_confidence
- **Indexing**: timestamp (descending), panel_id

### dl_predictions
- **Purpose**: Historical deep learning predictions
- **Key Fields**: panel_id, predicted_class, confidence, processing_time_ms, timestamp
- **Indexing**: timestamp (descending), panel_id

### feedback
- **Purpose**: Human validation corrections
- **Key Fields**: panel_id, original_prediction, corrected_prediction, is_correct, submitted_by
- **Indexing**: submitted_at (descending), panel_id

### users
- **Purpose**: User accounts and authentication
- **Key Fields**: email, firebase_uid, role, refresh_tokens, last_login
- **Indexing**: email (primary key)

## ⚠️ Important Notes

- **Document IDs**: The import script generates appropriate document IDs based on your existing code patterns
- **Timestamps**: All timestamps are in ISO format with milliseconds
- **Firebase Rules**: Make sure your Firestore security rules allow read/write access for authenticated users
- **Indexing**: Create composite indexes in Firebase Console for efficient queries:
  - `solar_panel_data`: panel_id + timestamp
  - `dl_predictions`: panel_id + timestamp
  - `feedback`: panel_id + submitted_at

## 🧪 Testing

After importing, your dashboard should display real data instead of mock data. The panels endpoint should return data from your Firestore collections.