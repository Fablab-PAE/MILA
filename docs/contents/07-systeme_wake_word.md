# 7. Système de wake word (voix)

Détection sur le **Raspberry Pi 4B** (Picovoice Porcupine), communication vers le Jetson
via **MQTT** (broker Mosquitto sur le Jetson). Deux mots d'activation personnalisés :
**"Hey Mila"** (start) et **"Mila stop"** (stop).

## 7.1 Broker MQTT (Jetson)

```bash
# Config Mosquitto : /etc/mosquitto/conf.d/custom.conf
listener 1883
# Configuration historique uniquement.
# Ne pas utiliser en production : elle autorise les clients MQTT anonymes.
# Remplacer par une authentification et des ACL avant toute exposition réseau.
allow_anonymous true

sudo systemctl status mosquitto   # vérifier
```

Topic utilisé : `mila/control` — messages `start_main_script` / `stop_main_script`.

## 7.2 Gestionnaire côté Jetson — `wake_word_handler.py`

Abonné au topic, il lance/arrête `main.py` (le script de suivi) selon la commande reçue,
avec vérification qu'il n'est pas déjà en cours.

```python
import paho.mqtt.client as mqtt
import subprocess, psutil, os, signal, time

MQTT_BROKER = "localhost"; MQTT_PORT = 1883; MQTT_TOPIC = "mila/control"
MAIN_SCRIPT_DIR  = "/home/<username>/Desktop/ultralytics"
MAIN_SCRIPT_NAME = "2_Automated_servo_control_no_display.py"
VENV_PATH        = "/home/<username>/myenv/bin/activate"
main_process = None

def is_main_script_running():
    return bool(main_process and main_process.poll() is None)

def start_main_script():
    global main_process
    if not is_main_script_running():
        cmd = f"source {VENV_PATH} && python3 {MAIN_SCRIPT_NAME}"
        main_process = subprocess.Popen(cmd, shell=True, executable='/bin/bash',
                                        cwd=MAIN_SCRIPT_DIR, preexec_fn=os.setsid)

def stop_main_script():
    global main_process
    if is_main_script_running():
        os.killpg(os.getpgid(main_process.pid), signal.SIGTERM)
        time.sleep(2)                                   # laisser les servomoteurs revenir
        if is_main_script_running():
            os.killpg(os.getpgid(main_process.pid), signal.SIGKILL)

def on_connect(client, userdata, flags, rc): client.subscribe(MQTT_TOPIC)
def on_message(client, userdata, message):
    cmd = message.payload.decode()
    if cmd == "start_main_script": start_main_script()
    elif cmd == "stop_main_script": stop_main_script()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
```

## 7.3 Détecteur côté RPi 4B — `wake_word_v3.py`

Utilise Porcupine + `PvRecorder`, publie sur MQTT à chaque détection. Points clés :
reconnexion MQTT avec retries, index d'entrée audio paramétrable, deux fichiers `.ppn`
(un par mot). Signature d'appel :

```bash
python wake_word_v3.py \
  --access_key "<PICOVOICE_ACCESS_KEY>" \
  --keyword_paths <hey-mila.ppn> <mila-stop.ppn> \
  --mqtt_broker <jetson-ip> --mqtt_port 1883 --mqtt_topic mila/control \
  --audio_device_index 0
```

Logique de publication : `result == 0` → `start_main_script`, sinon → `stop_main_script`.

## 7.4 Services systemd (démarrage automatique)

**Jetson** — `/etc/systemd/system/wake-word-handler.service` : lance `wake_word_handler.py`
après `network.target` et `mosquitto.service`, `Restart=always`.

**RPi 4B** — `/etc/systemd/system/wake-word-v3.service` :

```ini
[Unit]
Description=Wake Word Detection Service
After=network.target sound.target
Wants=network.target

[Service]
ExecStartPre=/bin/sleep 10
ExecStart=/bin/bash -c 'source /home/<username>/porcupine_env/bin/activate && \
  python /home/<username>/Desktop/wake_word_v3.py \
  --access_key "<PICOVOICE_ACCESS_KEY>" \
  --keyword_paths <hey-mila.ppn> <mila-stop.ppn> --audio_device_index 0'
WorkingDirectory=/home/<username>/Desktop
User=<username>
Group=audio
Restart=always
RestartSec=10
Environment="XDG_RUNTIME_DIR=/run/user/1000"
Environment="PULSE_RUNTIME_PATH=/run/user/1000/pulse"
Environment="AUDIODEV=hw:3,0"
StandardOutput=append:/var/log/wake-word.log
StandardError=append:/var/log/wake-word.log

[Install]
WantedBy=multi-user.target
```

Gestion :

```bash
sudo systemctl daemon-reload
sudo systemctl enable wake-word-v3.service
sudo systemctl start  wake-word-v3.service
sudo systemctl status wake-word-v3.service
tail -f /var/log/wake-word.log            # logs temps réel
```

> Les deux services doivent tourner en continu et survivre au reboot des deux cartes.
> Pensez à exécuter le service RPi sous l'utilisateur `<username>` (groupe `audio`), pas `root`.

## Retour à la table des matières

[Home](../home.md)
