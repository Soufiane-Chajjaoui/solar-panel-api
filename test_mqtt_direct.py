#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import time
import ssl
import random

# HiveMQ Cloud settings
BROKER = "d991e6f845314d0aa0594029c0cc9086.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "solar_panel"
PASSWORD = "Solar_panel/1234"
CLIENT_ID = "terminal-test-client"

# Panel ID to test (matches dashboard default)
PANEL_ID = "P-TEST-8"

def generate_panel_data():
    """Generate realistic sensor data for testing."""
    return {
        "temperature": round(random.uniform(20.0, 35.0), 1),  # Random temp 20-35°C
        "humidity": random.randint(30, 90),  # Random humidity 30-90%
        "light": random.randint(50, 1000),  # Random light 50-1000 lux
        "R": random.randint(0, 255),  # Random RGB values
        "G": random.randint(0, 255),
        "B": random.randint(0, 255),
        "water_level": random.choice(["OK", "VIDE", "LOW"]),  # Water reservoir status
        "device_status": "online",  # Device connectivity status
        "battery_level": random.randint(70, 100),  # Battery percentage
        "last_maintenance": "2024-01-15T10:00:00Z"  # ISO timestamp
    }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to HiveMQ Cloud!")
        print(f"🎯 Testing panel: {PANEL_ID}")
        print("📡 Sending real-time sensor data...")

        # Send multiple messages to simulate real-time updates
        for i in range(5):
            # Generate realistic sensor data
            sensor_data = generate_panel_data()

            # Topic format: solar/panel/{panel_id}/data
            topic = f"solar/panel/{PANEL_ID}/data"

            # Add some variation to simulate real sensor changes
            if i > 0:
                # Slightly vary the values for realism
                sensor_data["temperature"] += random.uniform(-2, 2)
                sensor_data["humidity"] += random.randint(-5, 5)
                sensor_data["light"] += random.randint(-50, 50)

                # Ensure values stay in realistic ranges
                sensor_data["temperature"] = round(max(15, min(40, sensor_data["temperature"])), 1)
                sensor_data["humidity"] = max(20, min(95, sensor_data["humidity"]))
                sensor_data["light"] = max(10, min(1200, sensor_data["light"]))

            result = client.publish(topic, json.dumps(sensor_data), qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 [{i+1}/5] Message sent to topic: {topic}")
                print(f"   📊 Data: T={sensor_data['temperature']}°C, H={sensor_data['humidity']}%, L={sensor_data['light']}lux")
                print(f"   🎨 RGB: ({sensor_data['R']}, {sensor_data['G']}, {sensor_data['B']})")
                print(f"   💧 Water: {sensor_data['water_level']}")
            else:
                print(f"❌ [{i+1}/5] Failed to send message: {result.rc}")

            # Wait between messages to simulate real sensor intervals
            if i < 4:  # Don't wait after last message
                time.sleep(2)

        print("✅ All test messages sent!")
        print("🔍 Check your dashboard at http://localhost:3000/dashboard")
        print("   The panel data should update in real-time!")

    else:
        print(f"❌ Connection failed with code: {rc}")
        error_messages = {
            1: "Protocol version error",
            2: "Client ID rejected",
            3: "Server unavailable",
            4: "Bad username/password",
            5: "Not authorized"
        }
        print(f"Error: {error_messages.get(rc, 'Unknown error')}")

def on_publish(client, userdata, mid):
    print("✅ Message published successfully!")

def on_disconnect(client, userdata, rc):
    print("👋 Disconnected from broker")

# Global counter for messages sent
messages_sent = 0
total_messages = 5

def on_publish(client, userdata, mid):
    global messages_sent
    messages_sent += 1
    print(f"✅ Message {messages_sent}/{total_messages} published successfully!")

    # Disconnect after all messages are sent
    if messages_sent >= total_messages:
        print("🔌 All messages sent, disconnecting...")
        client.disconnect()

# Create MQTT client
print("🔗 Creating MQTT client...")
client = mqtt.Client(client_id=CLIENT_ID, clean_session=True)

# Set credentials
client.username_pw_set(USERNAME, PASSWORD)

# Configure TLS for HiveMQ Cloud
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
client.tls_set_context(context)

# Set callbacks
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect

print(f"🔗 Connecting to {BROKER}:{PORT}...")
print(f"🎯 Target panel: {PANEL_ID}")
print(f"📡 Will send {total_messages} test messages with 2-second intervals")
print("=" * 60)

try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
except Exception as e:
    print(f"❌ Connection error: {e}")