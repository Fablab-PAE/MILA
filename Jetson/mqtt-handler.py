# INSTALLÉ DANS JETSON
# ANCIEN NOM DE FICHIER: ~/Desktop/wake-word-handler/wake_word_handler.py
import paho.mqtt.client as mqtt
import subprocess
import psutil
import os
import signal
import time

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "mila/control"

MAIN_SCRIPT_DIR = f"/home/{os.getenv('USERNAME')}/Desktop/ultralytics"
MAIN_SCRIPT_NAME = "2_Automated_servo_control_no_display_v2.py"
VENV_PATH = f"/home/{os.getenv('USERNAME')}/myenv/bin/activate"

main_process = None

def is_main_script_running():
    global main_process
    if main_process and main_process.poll() is None:
        return True
    return False

def start_main_script():
    global main_process
    if not is_main_script_running():
        cmd = f"source {VENV_PATH} && python3 {MAIN_SCRIPT_NAME}"
        main_process = subprocess.Popen(cmd, shell=True, executable='/bin/bash', cwd=MAIN_SCRIPT_DIR, preexec_fn=os.setsid)
        print(f"Started {MAIN_SCRIPT_NAME}")
    else:
        print(f"{MAIN_SCRIPT_NAME} is already running")

def stop_main_script():
    global main_process
    if is_main_script_running():
        print(f"Stopping {MAIN_SCRIPT_NAME}")
        os.killpg(os.getpgid(main_process.pid), signal.SIGTERM)
        time.sleep(2)  # Give some time for the script to cleanup and reset servos
        if is_main_script_running():
            os.killpg(os.getpgid(main_process.pid), signal.SIGKILL)
        print(f"Stopped {MAIN_SCRIPT_NAME}")
    else:
        print(f"{MAIN_SCRIPT_NAME} is not running")

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, message):
    command = message.payload.decode()
    print(f"Received command: {command}")
    if command == "start_main_script":
        start_main_script()
    elif command == "stop_main_script":
        stop_main_script()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)

print(f"Listening for commands on topic {MQTT_TOPIC}... Press Ctrl+C to exit.")

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Stopping...")
finally:
    if is_main_script_running():
        stop_main_script()
    client.disconnect()