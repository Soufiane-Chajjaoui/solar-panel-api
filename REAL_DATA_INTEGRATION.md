# Real Data Integration - Frontend ↔ Backend

## Overview
The Frontend is now displaying real sensor data from the backend instead of fake data. The data flows from IoT sensors → MQTT broker → Backend processing (ML predictions) → Firestore → Frontend API → Dashboard.

## Data Flow Architecture

```
IoT Sensors
    ↓ (MQTT: solar/panel/panel1/data)
MQTT Broker (HiveMQ Cloud)
    ↓
Backend MQTT Service
    ├─ Validate sensor data
    ├─ ML prediction (cleaning status)
    ├─ DL validation (if dirty detected)
    └─ Upload images to Cloudinary
    ↓
Firestore Database (solar_panel_data collection)
    ↓
Backend API (/panels endpoint)
    ↓
Frontend API Handler (/api/panels)
    ├─ Normalize data
    └─ Add placeholder images
    ↓
Dashboard Components
    ├─ PanelGrid (refresh every 10 seconds)
    ├─ PanelCard (displays status + ML confidence)
    └─ SensorData (displays temperature, humidity, light)
```

## Backend Implementation

### New Endpoint: GET /panels
- **Path**: `app/routes/panel_routes.py`
- **Function**: Fetches all panels with their latest sensor data and ML predictions
- **Response**:
```json
[
  {
    "panel_id": "panel1",
    "last_status": "dirty",
    "last_confidence": 0.9931557739283245,
    "thumbnail": "https://via.placeholder.com/400x300?text=panel1",
    "last_update": "2025-11-18T11:28:13.424907",
    "temperature": 24.1,
    "humidity": 60,
    "light": 200
  }
]
```

### New Endpoint: GET /panels/{panel_id}
- **Path**: `app/routes/panel_routes.py`
- **Function**: Fetches detailed information for a specific panel including all ML/DL predictions
- **Response**: Complete panel data with raw sensor values, ML/DL predictions, color data (RGB)

### Firebase Security Module
- **Path**: `app/core/firebase_security.py`
- **Function**: Handles Firebase token verification and user synchronization
- Verifies Firebase ID tokens from the Frontend
- Creates/updates users in Firestore based on Firebase authentication
- Returns JWT tokens for backend access

### Updated Auth Routes
- **Path**: `app/routes/auth_routes.py`
- **New Endpoint**: `POST /auth/sync-firebase`
- Synchronizes Firebase authentication with backend
- Automatically creates users in Firestore
- Returns JWT tokens for subsequent API calls

## Frontend Changes

### Updated API Route Handler
- **Path**: `Frontend/app/api/panels/route.js`
- Now properly calls backend `/panels` endpoint
- Normalizes backend response with proper field mapping
- Falls back to mock data if backend is unavailable

### New Dashboard Components

#### SensorData Component
- **Path**: `Frontend/app/(protected)/dashboard/SensorData.jsx`
- Displays real sensor readings from MQTT data:
  - Temperature (°C)
  - Humidity (%)
  - Light level (lux)
- Shows values only if data is available

#### Enhanced PanelCard
- **Path**: `Frontend/app/(protected)/dashboard/PanelCard.jsx`
- Displays ML prediction confidence as percentage
- Shows last update timestamp
- Integrates sensor data display
- Uses placeholder images (can be replaced with actual images when available)

### Updated Dashboard Grid
- **Path**: `Frontend/app/(protected)/dashboard/PanelGrid.jsx`
- Auto-refreshes every 10 seconds
- Displays all panels with real-time data

## Data Storage Structure

### Firestore Collections

#### solar_panel_data
Each document contains:
```
{
  "panel_id": "panel1",
  "timestamp": "2025-11-18T11:28:13.424907",
  "topic": "solar/panel/panel1/data",
  
  // Sensor data
  "temperature": 24.1,
  "humidity": 60,
  "light": 200,
  "R": 60,
  "G": 80,
  "B": 100,
  
  // ML predictions
  "ml_prediction": "dirty",
  "ml_confidence": 0.9931557739283245,
  "ml_probability": {
    "clean": 0.006844226071675452,
    "dirty": 0.9931557739283245
  },
  
  // DL predictions (if applicable)
  "dl_prediction": null,
  "dl_status": null,
  "dl_confidence": null,
  
  // Image URL (if uploaded to Cloudinary)
  "image_url": "https://res.cloudinary.com/..."
}
```

## How to Use

### 1. Start the Backend
```bash
python run_windows.bat
# or
uvicorn app.main:app --reload
```

### 2. Send Test Data via MQTT
```bash
python test_mqtt_direct.py
```

### 3. View Real Data in Frontend
1. Start Frontend: `npm run dev`
2. Login with Firebase credentials
3. Dashboard automatically syncs backend and displays real data
4. Refresh every 10 seconds automatically

## Field Mapping

### Backend → Frontend
| Backend Field | Frontend Field | Type |
|---|---|---|
| panel_id | id / panel_id | string |
| last_status | status | string |
| last_confidence | last_confidence | float (0-1) |
| thumbnail | imageUrl | URL |
| last_update | lastChecked | ISO datetime |
| temperature | temperature | float |
| humidity | humidity | float |
| light | light | float |

## Status Values

The `last_status` field displays the ML prediction result:
- **clean**: Panel is clean (green badge)
- **dirty**: Panel needs cleaning (orange badge)
- **damaged**: Panel is damaged (red badge)

Color mapping in PanelCard:
- Green: clean, healthy
- Orange: dusty, warning
- Red: damaged, critical
- Gray: unknown

## ML Prediction Confidence

The confidence is displayed as a percentage next to the status:
- 99.3% means the ML model is 99.3% confident in its prediction
- Based on the ML service's `ml_confidence` field

## Troubleshooting

### No panels showing?
1. Verify MQTT is publishing data (check backend logs)
2. Ensure data is stored in Firestore (`solar_panel_data` collection)
3. Check backend API: `curl http://localhost:8000/panels`
4. Verify Frontend can reach backend: Check network tab in DevTools

### Wrong data displaying?
1. Verify field names match backend response
2. Check normalization in `Frontend/app/api/panels/route.js`
3. Inspect browser console for errors

### Firebase sync failing?
1. Verify Firebase is configured on backend
2. Check `serviceAccountKey.json` exists
3. Ensure user is logged in with Firebase before accessing dashboard
4. Check backend logs for Firebase errors

### Placeholder images instead of real images?
- Currently using `https://via.placeholder.com/` for UI consistency
- Replace with actual image URLs when image upload is implemented
- Images can be added to the `image_url` field in Firestore

## Next Steps

### 1. Replace Placeholder Images
Option A: Upload panel images via Frontend
Option B: Capture images during MQTT data collection
Option C: Add image_url to test_mqtt_direct.py

### 2. Add More Sensor Metrics
- Add wind speed if available
- Add efficiency calculation
- Add historical data tracking

### 3. Implement Real-Time Updates
- Replace polling with WebSocket connections
- Use Server-Sent Events (SSE) for live updates
- Subscribe to Firestore changes directly

### 4. Add Alerts
- Notify when panel status changes
- Alert on threshold values (temperature, humidity)
- Email notifications for manual cleaning

### 5. Historical Data
- Display trend charts for sensor data
- Add date range filtering
- Export historical data

## Testing

### Test Endpoints

```bash
# Get all panels (requires auth token in header)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/panels

# Get specific panel
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/panels/panel1

# Health check (no auth needed)
curl http://localhost:8000/health

# Firebase connection test (no auth needed)
curl http://localhost:8000/test-firebase
```

### Expected Response (GET /panels)
```json
[
  {
    "panel_id": "panel1",
    "last_status": "dirty",
    "last_confidence": 0.9931557739283245,
    "thumbnail": "https://via.placeholder.com/400x300?text=panel1",
    "last_update": "2025-11-18T11:28:13.424907",
    "temperature": 24.1,
    "humidity": 60,
    "light": 200
  }
]
```

## Performance Optimization

- Panels are grouped by panel_id in get_panels() - only latest data per panel
- Firestore queries are ordered by timestamp in DESC
- Frontend caches data between 10-second refreshes
- Use indexes for efficient queries (already configured in Firestore)

## Security

- All backend API calls require JWT authentication
- Firebase tokens are verified server-side
- Sensor data is stored securely in Firestore
- API responses are normalized to prevent data leakage
