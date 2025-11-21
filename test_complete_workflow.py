#!/usr/bin/env python3
"""
Complete workflow test script for the solar panel dashboard.
Tests MQTT sensor data + image upload + prediction in sequence.
"""

import paho.mqtt.client as mqtt
import json
import time
import ssl
import random
import requests

# Configuration
MQTT_BROKER = "d991e6f845314d0aa0594029c0cc9086.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "solar_panel"
MQTT_PASSWORD = "Solar_panel/1234"
CLIENT_ID = "workflow-test-client"

PANEL_ID = "P-TEST-3"
FASTAPI_URL = "http://localhost:8000"

# Test image URLs (you can replace these with actual Cloudinary URLs)
TEST_IMAGES = [
    "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=640&h=480&fit=crop",  # Clean panel
    "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=640&h=480&fit=crop",   # Dusty panel
    "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=640&h=480&fit=crop",   # Clean panel
]

def generate_sensor_data():
    """Generate realistic sensor data."""
    return {
        "temperature": round(random.uniform(22.0, 32.0), 1),
        "humidity": random.randint(35, 75),
        "light": random.randint(200, 900),
        "R": random.randint(100, 200),
        "G": random.randint(120, 220),
        "B": random.randint(80, 180),
        "water_level": "OK",
        "device_status": "online",
        "battery_level": random.randint(85, 100),
    }

def send_mqtt_data():
    """Send MQTT sensor data."""
    print("🚀 Step 1: Sending MQTT sensor data...")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")

            # Send sensor data
            sensor_data = generate_sensor_data()
            topic = f"solar/panel/{PANEL_ID}/data"

            result = client.publish(topic, json.dumps(sensor_data), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Sensor data sent to {topic}")
                print(f"   📊 T={sensor_data['temperature']}°C, H={sensor_data['humidity']}%, L={sensor_data['light']}lux")
            else:
                print(f"❌ Failed to send MQTT data: {result.rc}")

            client.disconnect()
        else:
            print(f"❌ MQTT connection failed: {rc}")

    client = mqtt.Client(client_id=CLIENT_ID, clean_session=True)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    client.tls_set_context(context)

    client.on_connect = on_connect

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
        return True
    except Exception as e:
        print(f"❌ MQTT error: {e}")
        return False

def test_prediction(image_url):
    """Test image prediction."""
    print(f"🤖 Step 2: Testing prediction with image...")

    try:
        # Make prediction request
        response = requests.post(
            f"{FASTAPI_URL}/predict",
            json={"panel_id": PANEL_ID, "image_url": image_url},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Prediction successful!")
            print(f"   🎯 Result: {result['predicted_class']} ({result['confidence']*100:.1f}%)")
            print(f"   📊 Status: {result['status']}")
            print(f"   ⚡ Processing time: {result['processing_time_ms']}ms")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False

def test_dashboard_data():
    """Test dashboard data retrieval."""
    print("📊 Step 3: Testing dashboard data...")

    try:
        # Test stats endpoint
        response = requests.get(f"{FASTAPI_URL}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Dashboard stats retrieved!")
            print(f"   📈 Total predictions: {stats.get('total_predictions', 0)}")
            print(f"   🎯 Avg confidence: {stats.get('avg_confidence', 0.0)*100:.1f}%")
            print(f"   ⚡ Avg processing time: {stats.get('avg_processing_time', 0.0):.1f}ms")
        else:
            print(f"❌ Stats retrieval failed: {response.status_code}")

        # Test predictions endpoint
        response = requests.get(f"{FASTAPI_URL}/history/predictions?limit=3", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recent predictions retrieved: {len(data.get('predictions', []))} items")
        else:
            print(f"❌ Predictions retrieval failed: {response.status_code}")

        return True

    except Exception as e:
        print(f"❌ Dashboard test error: {e}")
        return False

def main():
    """Run complete workflow test."""
    print("🌟 SOLAR PANEL DASHBOARD - COMPLETE WORKFLOW TEST")
    print("=" * 60)

    # Step 1: Send MQTT sensor data
    if not send_mqtt_data():
        print("❌ Workflow test failed at MQTT step")
        return

    time.sleep(3)  # Wait for backend processing

    # Step 2: Test prediction with different images
    print("\n🖼️  Testing predictions with multiple images...")
    for i, image_url in enumerate(TEST_IMAGES, 1):
        print(f"\n📸 Image {i}/{len(TEST_IMAGES)}:")
        if not test_prediction(image_url):
            print(f"⚠️  Prediction {i} failed, continuing...")

        if i < len(TEST_IMAGES):  # Don't wait after last image
            time.sleep(2)

    time.sleep(2)  # Wait for predictions to be stored

    # Step 3: Test dashboard data
    if not test_dashboard_data():
        print("❌ Workflow test failed at dashboard step")
        return

    print("\n" + "=" * 60)
    print("🎉 COMPLETE WORKFLOW TEST FINISHED!")
    print("🔍 Check your dashboard at: http://localhost:3000/dashboard")
    print("   You should see:")
    print("   ✅ Real-time sensor data updates")
    print("   ✅ Prediction results with images")
    print("   ✅ Historical data in charts")
    print("   ✅ Live notifications")
    print("=" * 60)

if __name__ == "__main__":
    main()