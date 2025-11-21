# 🧪 Testing the Solar Panel Dashboard

This guide shows how to test the complete real-time dashboard system without fake data.

## 📋 Prerequisites

1. **Backend running**: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. **Frontend running**: `npm run dev` in the Frontend directory
3. **Firebase configured** with valid credentials
4. **HiveMQ Cloud access** (MQTT broker)

## 🚀 Quick Test Scripts

### Option 1: MQTT Sensor Data Only
Test real-time sensor updates in the dashboard:

```bash
python test_mqtt_direct.py
```

**What it does:**
- Connects to HiveMQ Cloud MQTT broker
- Sends 5 realistic sensor data messages to panel `P-TEST-3`
- Each message includes: temperature, humidity, light, RGB values, water level
- Messages are sent with 2-second intervals to simulate real sensor behavior

**Expected result:**
- Dashboard at `http://localhost:3000/dashboard` updates in real-time
- Sensor values change every 2 seconds
- Notifications appear based on sensor conditions

### Option 2: Complete Workflow Test
Test the full pipeline: MQTT → Predictions → Dashboard:

```bash
python test_complete_workflow.py
```

**What it does:**
1. **MQTT Phase**: Sends sensor data to panel `P-TEST-3`
2. **Prediction Phase**: Tests 3 different solar panel images through the prediction API
3. **Dashboard Phase**: Verifies that historical data is accessible

**Expected result:**
- Complete end-to-end test of the system
- Predictions stored in Firestore
- Dashboard shows real prediction history
- All components work together seamlessly

## 🔍 Manual Testing Steps

### 1. Start the Backend
```bash
cd /path/to/solar-panel-api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
cd Frontend
npm run dev
```

### 3. Open Dashboard
Navigate to: `http://localhost:3000/dashboard`

### 4. Send Test Data
Run one of the test scripts above.

### 5. Verify Real-time Updates
- **Sensor Data**: Should update every 2 seconds
- **Final State**: Changes based on sensor conditions
- **Notifications**: Appear based on sensor thresholds
- **Historical Data**: Accumulates with each prediction

## 📊 What Gets Tested

### Real-time Components
- ✅ Firestore listeners (`onSnapshot`)
- ✅ Sensor data display (temperature, humidity, light, RGB)
- ✅ Status calculations (clean/dirty/wait/blocked)
- ✅ Color-coded status indicators
- ✅ Live notifications system

### Prediction Pipeline
- ✅ Image URL processing
- ✅ ML model predictions
- ✅ Confidence scoring
- ✅ Result storage in Firestore
- ✅ Historical data retrieval

### Dashboard Features
- ✅ Panel selection
- ✅ Time filtering
- ✅ Chart visualizations
- ✅ Data export capabilities
- ✅ Responsive design

## 🐛 Troubleshooting

### Dashboard shows "Panel not found"
- Run `test_mqtt_direct.py` first to create the panel document
- Check Firebase console for `panels/P-TEST-3` document

### No real-time updates
- Verify backend is running on port 8000
- Check browser console for Firebase errors
- Ensure Firebase credentials are valid

### MQTT connection fails
- Verify HiveMQ Cloud credentials
- Check internet connection
- Confirm MQTT broker is accessible

### Predictions fail
- Ensure backend ML models are loaded
- Check image URLs are accessible
- Verify Cloudinary configuration (if uploading images)

## 🎯 Test Data Format

The MQTT messages follow this format:
```json
{
  "temperature": 25.3,
  "humidity": 65,
  "light": 750,
  "R": 180,
  "G": 190,
  "B": 170,
  "water_level": "OK",
  "device_status": "online",
  "battery_level": 92
}
```

## 📈 Performance Expectations

- **MQTT latency**: < 100ms
- **Prediction time**: 200-500ms per image
- **Dashboard updates**: Instant (via Firestore real-time)
- **Data persistence**: Permanent in Firestore

## 🎉 Success Indicators

When everything works correctly, you should see:
- 🌟 Real-time sensor value changes
- 🎨 RGB values updating the color display
- 📊 Status changing based on conditions
- 🔔 Contextual notifications appearing
- 📈 Historical charts populating with data
- 🔄 Live updates without page refresh

The system demonstrates a true **cloud-native real-time application**! 🚀</content>
</xai:function_call: write_file>
<parameter name="file_path">c:\Users\SAMSUNG\Documents\GitHub\solar-panel-api\TESTING_README.md