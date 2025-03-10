import os
import json
import warnings
from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)

# โหลดค่าในไฟล์ .env
load_dotenv()

app = Flask(__name__, template_folder='custom_templates')
socketio = SocketIO(app)

# อ่านค่าตัวแปรจาก .env
MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
MQTT_ACCESS_KEY = os.environ.get('MQTT_ACCESS_KEY')

# ดึงค่า MAPBOX_ACCESS_TOKEN สำหรับแสดงแผนที่
MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN')

# สร้าง client MQTT
client = mqtt.Client(client_id="myClientID", protocol=mqtt.MQTTv311)
client.username_pw_set(username=MQTT_USERNAME, password=MQTT_ACCESS_KEY)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
        # ตัวอย่าง: subscribe topic บน The Things Network
        client.subscribe("v3/smartdevice-physics@ttn/devices/my-tracker01/up")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        if "uplink_message" in payload and "decoded_payload" in payload["uplink_message"]:
            decoded = payload["uplink_message"]["decoded_payload"]
            data = {
                'timestamp': payload.get('received_at', ''),
                'latitude': decoded.get("latitude", 0.0),
                'longitude': decoded.get("longitude", 0.0),
                'heartRate': decoded.get("heartRate", 0),
                'spo2': decoded.get("spo2", 0)
            }
            print(f"Received data: {data}")
            # ส่งข้อมูลแบบ real-time ไปยัง client (หน้าเว็บ) ผ่าน Socket.IO
            socketio.emit('new_location', data)
        else:
            print("Error: Missing uplink_message or decoded_payload.")
    except Exception as e:
        print(f"Error: {e}")

client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_start()

@app.route('/')
def index():
    # ส่งค่า mapbox_token ไปยัง index.html
    return render_template('index.html', mapbox_token=MAPBOX_ACCESS_TOKEN)

if __name__ == '__main__':
    # เปิดใช้งานแอป Flask ร่วมกับ SocketIO
    socketio.run(app, debug=True, port=5001)
