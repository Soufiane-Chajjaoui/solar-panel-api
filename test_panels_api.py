import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("✅ Backend is running")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Backend not responding: {e}")
        return False

def test_panels():
    """Test GET /panels endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/panels")
        print(f"\n📊 GET /panels - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} panels")
            if data:
                print(f"\nFirst panel:")
                print(json.dumps(data[0], indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to fetch panels: {e}")

def test_specific_panel():
    """Test GET /panels/{panel_id} endpoint"""
    panel_id = "panel1"
    try:
        response = requests.get(f"{BASE_URL}/panels/{panel_id}")
        print(f"\n📊 GET /panels/{panel_id} - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Panel {panel_id} data:")
            print(json.dumps(data, indent=2, default=str))
        elif response.status_code == 404:
            print(f"⚠️  Panel {panel_id} not found (no data yet)")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to fetch panel: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Backend Panels API")
    print("=" * 60)
    
    if test_health():
        test_panels()
        test_specific_panel()
    else:
        print("\n🔄 Please start the backend first:")
        print("   python run_windows.bat")
