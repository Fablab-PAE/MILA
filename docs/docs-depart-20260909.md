# Documentation de départ du Projet Mila en date du 2026-09-09

Cette première documentation est à titre de référence de la documentation existante au moment de rendre le projet open source sur Github. Seuls les informations sensibles ont été retiré de cette documentation pour de la prévention de sécurité.

## Mila — Tête robotisée servant comme assistant de laboratoire

Documentation technique du projet **Mila** : une tête animatronique imprimée en 3D qui détecte et suit un visage en **temps réel** grâce à deux servomoteurs (PAN / TILT), déclenchée à la voix et dotée d'yeux animés sur écrans LCD.

- Le board Figma est disponible sur demande auprès des mainteneurs du projet.

---

## 1. Architecture générale

Le système est réparti sur trois cartes qui communiquent via le réseau (Wi-Fi) et MQTT.

| Rôle | Carte | Responsabilité |
| ------ | ------- | ---------------- |
| Cerveau / inférence | Jetson Orin Nano 8GB | Capture vidéo, détection de visage, boucle de contrôle des servomoteurs, broker MQTT |
| Actionneurs | ESP32-S3 | Génère les signaux PWM pour les deux servomoteurs, sur ordre série depuis le Jetson |
| Voix + yeux | Raspberry Pi 4B | Détection de mot d'activation (wake word), lecture audio, animation des yeux LCD |

**Flux :**

``` text
Utilisateur dit "Hey Mila"
   └─> RPi 4B (wake word) publie "start_main_script" sur MQTT
          └─> Jetson (wake_word_handler) lance main.py
                 └─> Caméra → détection visage → boucle de contrôle → ESP32 → servomoteurs

Utilisateur dit "Mila stop"
   └─> RPi 4B publie "stop_main_script" sur MQTT
          └─> Jetson arrête main.py, servomoteurs remis en position initiale
```

**Ordre d'allumage :** démarrer le Jetson (broker MQTT) avant le Raspberry Pi
(client MQTT), pour que le broker soit disponible quand le client se connecte.

---

## 2. Matériel

### Jetson Orin Nano 8GB (reComputer J3011)

- <https://www.seeedstudio.com/reComputer-J3011-p-5590.html>
- <https://wiki.seeedstudio.com/reComputer_Jetson_Series_Hardware_Layout/>
- 40 TOPS pour toute l'inférence.
- Livré à l'origine avec JetPack 5.1.1 ; reflashé en JetPack 6
- Utilise l'antenne fournie pour le Wi-Fi
- GPIOs
  - <https://www.seeedstudio.com/reComputer-J3011-p-5590.html>

### ESP32-S3

- Génère le PWM des servomoteurs via le périphérique `LEDC`.
- Broche PAN : **GPIO 17** (canal `LEDC_CHANNEL_1`).
- Broche TILT : **GPIO 16** (canal `LEDC_CHANNEL_0`).
- Exposé côté Jetson sur `/dev/esp32s3serial` (alias udev), 115200 bauds.

### servomoteurs

- 2× servomoteurs RDS 35 kg, plage 270°, pour les mouvements PAN et TILT.
  - <https://www.amazon.ca/dp/B08J7Q3PPB>
- Chaque servo est alimenté par un chargeur 5V 3A
  - <https://www.amazon.ca/dp/B0811H9GQ3?th=1>

### Caméra

- Raspberry Pi Camera Module v2 (cable CSI), flux 30 FPS.

### Yeux — écrans LCD

- 2× Waveshare LCD IPS rond 1.28" (driver GC9A01, SPI, 240×240, 65K couleurs, 60 Hz).
  - <https://www.amazon.ca/dp/B0BD54FQVS>
- intégrés au RPi 4B.

### Audio

- Haut-parleur Creative Pebble V2 (USB), branché sur le RPi 4B.
  - <https://www.amazon.ca/dp/B07VVP8BGD>
- Alimenté par son propre bloc secteur (et non par le RPi).

---

## 3. Installation du Jetson (JetPack 6)

Flash réalisé avec le **NVIDIA SDK Manager** depuis un hôte Ubuntu (VM VMware).

1. **Hôte Ubuntu** : créer une VM Ubuntu (≈10 Go RAM, 120 Go disque), `apt update && apt upgrade`.
2. **SDK Manager** : installer le `.deb` puis résoudre les dépendances.

   ```bash
   sudo dpkg -i sdkmanager_2.1.0-*.deb
   sudo apt-get install -f
   sdkmanager
   ```

3. **Connexion** : relier le reComputer à l'hôte en USB-C, le placer en **force recovery mode**
   (cavalier/jumper), ajouter le passthrough USB à la VM (`lsusb` pour vérifier).
4. **Flash** : lancer le flash depuis le SDK Manager. Garder le cavalier branché jusqu'au
   message concernant l'USB, puis laisser l'installation se terminer.
5. **Fin** : retirer le cavalier, partager la connexion Internet via Ethernet.
6. **Post-install** sur le Jetson :

   ```bash
   sudo apt update && sudo apt upgrade
   sudo reboot
   # Wi-Fi (backport iwlwifi)
   sudo apt install backport-iwlwifi-dkms
   sudo reboot
   # Métapaquet JetPack
   sudo apt-get install nvidia-jetpack
   ```

### Vérification de l'environnement

| Composant | Commande | Version cible |
| ----------- | ---------- | --------------- |
| JetPack / L4T | `dpkg -l | grep nvidia-l4t-core` | 36.3 (arm64/aarch64) |
| Ubuntu | `lsb_release -a` | 22.04.4 LTS |
| Python pip | `sudo apt install python3-pip` | — |
| OpenCV | `python3 -c "import cv2; print(cv2.__version__)"` | 4.8.0 |
| GStreamer (OpenCV) | `python3 -c "import cv2; print(cv2.getBuildInformation())" && grep GStreamer` | YES (1.20.3) |
| CUDA | `nvcc --version` | 12.2.140 |
| TensorRT | `dpkg -l && grep nvinfer` | 8.6.2 |
| GPU | `nvidia-smi` | — |

---

## 4. Contrôle des servomoteurs (ESP32 + Python)

Le Jetson envoie des commandes texte (`PAN:<angle>\n` ou `TILT:<angle>\n`) sur le port
série ; l'ESP32 les convertit en largeur d'impulsion PWM.

### 4.1 Firmware ESP32 — `sketch_servo_PAN_TILT.ino`

Principe : PWM 50 Hz, résolution 14 bits, largeur d'impulsion 500–2500 µs mappée sur 0–270°.

```cpp
#include "driver/ledc.h"

#define SERVO_PAN_PIN 17
#define SERVO_TILT_PIN 16
#define SERVO_PAN_CHANNEL LEDC_CHANNEL_1
#define SERVO_TILT_CHANNEL LEDC_CHANNEL_0
#define LEDC_BASE_FREQ 50        // Servo à 50 Hz
#define MAX_DUTY_CYCLE 16383     // résolution 14 bits
#define PULSE_WIDTH_MIN 500      // µs
#define PULSE_WIDTH_MAX 2500     // µs

uint32_t pulseWidthToDutyCycle(uint32_t pulseWidth) {
  return (pulseWidth * MAX_DUTY_CYCLE) / 20000;   // période 20 ms
}

void setupPWM(uint8_t pin, ledc_channel_t channel) {
  ledc_timer_config_t ledc_timer = {
    .speed_mode = LEDC_LOW_SPEED_MODE,
    .duty_resolution = LEDC_TIMER_14_BIT,
    .timer_num = LEDC_TIMER_0,
    .freq_hz = LEDC_BASE_FREQ,
    .clk_cfg = LEDC_AUTO_CLK,
  };
  ledc_timer_config(&ledc_timer);

  ledc_channel_config_t ledc_channel = {
    .gpio_num = pin,
    .speed_mode = LEDC_LOW_SPEED_MODE,
    .channel = channel,
    .intr_type = LEDC_INTR_DISABLE,
    .timer_sel = LEDC_TIMER_0,
    .duty = 0,
    .hpoint = 0
  };
  ledc_channel_config(&ledc_channel);
}

void setServoAngle(ledc_channel_t channel, int angle) {
  if (angle < 0 || angle > 270) { Serial.print("Invalid angle: "); Serial.println(angle); return; }
  uint32_t pulseWidth = map(angle, 0, 270, PULSE_WIDTH_MIN, PULSE_WIDTH_MAX);
  uint32_t dutyCycle = pulseWidthToDutyCycle(pulseWidth);
  ledc_set_duty(LEDC_LOW_SPEED_MODE, channel, dutyCycle);
  ledc_update_duty(LEDC_LOW_SPEED_MODE, channel);
}

void setup() {
  Serial.begin(115200);
  setupPWM(SERVO_PAN_PIN, SERVO_PAN_CHANNEL);
  setupPWM(SERVO_TILT_PIN, SERVO_TILT_CHANNEL);
  Serial.println("Setup complete, waiting for commands...");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    if (input.startsWith("PAN:"))  setServoAngle(SERVO_PAN_CHANNEL,  input.substring(4).toInt());
    else if (input.startsWith("TILT:")) setServoAngle(SERVO_TILT_CHANNEL, input.substring(5).toInt());
  }
}
```

> Historique : des sketches séparés `sketch_servo_PAN.ino` / `sketch_servo_TILT.ino`
> existaient avant d'être fusionnés dans ce fichier unique.

### 4.2 Côté Python

Helper commun d'envoi de commande :

```python
import serial

def move_servo(servo, position):
    command = f"{servo}:{position}\n"
    ser.write(command.encode())
```

- **`servo_control_PAN_TILT.py`** : balayage automatique de test, alterne les deux servomoteurs
  entre leurs bornes (PAN 0–270°, milieu 125° ; TILT 20–270°, milieu 140°).
- **`servo_control_XBOX.py`** : contrôle manuel au D-pad d'une manette Xbox (via `pygame`),
  ±1° par appui, positions initiales PAN=125 / TILT=140.
- **`servo_control_XBOX_RATE.py`** (version de référence) : contrôle manuel cadencé à
  **30 instructions/s** (fenêtre de 33 ms, calquée sur les 30 FPS caméra), avec :
  - incréments distincts : **PAN 4°**, **TILT 2°** par instruction ;
  - bornes logicielles TILT restreintes (30°–76°) pour protéger la mécanique ;
  - retour progressif ("smooth") aux positions initiales à la sortie.

### 4.3 Manette Xbox — règle udev

Alias stable pour la manette :

```ini
# /etc/udev/rules.d/99-joystick.rules
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02d1", MODE="0666", GROUP="input", SYMLINK+="xbox_controller"
```

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -l /dev/xbox_controller   # -> input/eventN
```

### 4.4 Débogage série

```bash
# Voir les logs série de l'ESP32
sudo minicom -b 115200 -D /dev/esp32s3serial   # quitter : Ctrl+A puis X
# Si le port est occupé
sudo lsof | grep /dev/esp32s3serial
sudo kill <PID>
```

### Cadence & vitesse (mesures)

- 30 instructions/s → une commande toutes les ~33 ms.
- PAN : 4°/instruction → **120°/s**.
- TILT : 2°/instruction → **60°/s**.

---

## 5. Inférence & suivi de visage

### 5.1 Environnement virtuel

Toujours travailler dans un venv héritant des paquets système :

```bash
python3 -m venv --system-site-packages /home/<username>/myenv
source /home/<username>/myenv/bin/activate
pip list
```

### 5.2 Chaîne TensorRT (modèle YOLOv8n Face, FP16)

TensorRT apporte un gain d'inférence de l'ordre de ×2–×3 par rapport à PyTorch/ONNX natif.

1. **Modèle source** : YOLOv8n Face Detection (640×640), converti en FP16 (INT8 possible).
2. **Conversion** (réalisée sur Google Colab, GPU T4) : `model.pt` → `model.onnx` → `model_FP16.trt`.
   L'ONNX sert d'intermédiaire portable entre frameworks.
3. **Inférence** sur le Jetson via TensorRT + OpenCV, affichage des bounding boxes et du FPS.

> **Piège rencontré** : `pip3 install ultralytics` réinstalle OpenCV et **casse le support
> GStreamer** précédemment compilé. Contournement : installer `ultralytics` avec un
> `requirements.txt` modifié qui **exclut** `opencv`, `torch` et `torchvision`, puis
> désinstaller l'OpenCV parasite pour conserver le build GStreamer d'origine.

Versions cohérentes obtenues après contournement :
`cv2 4.5.4`, `torch 2.3.1`, `torchvision 0.18.1`, `ultralytics 8.2.36`.

**PyTorch / Torchvision pour JetPack 6 (L4T 36.x, CUDA 12.2, Python 3.10)** — utiliser les
wheels aarch64 fournis par NVIDIA (PyTorch 2.3.0 / Torchvision 0.18) plutôt que les paquets pip standards.

### 5.3 Alternatives d'inférence évaluées

- **TensorRT + DeepStream SDK** (7.0) avec le dépôt `DeepStream-Yolo` de marcoslucianops.
- **Serveur d'inférence Roboflow auto-hébergé** (image TensorRT Jetson).
- **jetson-inference** (dusty-nv) en Docker : modèles `TAO FaceDetect` / `SSD-Mobilenet-v2`.
- **YuNet** (OpenCV Zoo) — retenu comme détecteur de visage léger pour le suivi.
- **ResNet-50 / DETR**, **YOLOv8n-cls** pour de la classification/reconnaissance.

### 5.4 Boucle de suivi temps réel

Objectif : aligner le centre de la bounding box du visage avec le centre du champ de la
caméra, dans une fenêtre de **33 ms (30 FPS)**.

**Pipeline :**

1. **Capture** OpenCV du flux CSI 1920×1080 @ 30 FPS.
2. **Prétraitement** : redimensionnement en 640×640 avec conservation du ratio + padding.
   (Le curseur de visée central, utile en debug, est retiré en production.)
3. **Détection** (YuNet) → coordonnées de la bounding box → calcul du centre.
4. **Boucle de contrôle** : erreur en x/y entre centre boîte et centre champ → commandes
   correctives aux servomoteurs.

**Charge de calcul estimée** pour un flux 30 FPS : ~43 % (détection ~33 % + reconnaissance ~10 %),
volontairement basse pour la stabilité thermique.

**Fluidité / robustesse :**

- **Multithreading** : un thread de capture (30 FPS, garde la dernière frame) + un thread
  d'inférence (≈24 FPS sur la frame la plus récente) pour réduire la latence.
- **Calibration servomoteurs** : commandes à cadence fixe (30/s) pour éviter jitter et dépassement.
- **Bornes logicielles** : empêcher la tête de sortir des angles sûrs.
- **Suivi sélectif** : filtrer pour ne suivre que le visage le plus proche.

### 5.5 Exécution

```bash
ssh <username>@<jetson-ip>
cd Desktop/ultralytics
source /home/<username>/myenv/bin/activate
python3 python3 2_Automated_servo_control_no_display_v2.py        # avec mouvements servomoteurs
sudo jtop                                   # suivi ressources CPU/GPU
```

## 6. Compilation OpenCV avec GStreamer (nvargus)

Le support GStreamer n'est pas activé par défaut : il faut installer GStreamer puis
**recompiler OpenCV**.

```bash
sudo apt update
# Pile GStreamer
sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools

# Dépendances de build OpenCV
sudo apt install build-essential cmake git pkg-config libgtk-3-dev \
  libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev \
  libjpeg-dev libpng-dev libtiff-dev gfortran openexr libatlas-base-dev \
  python3-dev python3-numpy libtbb-dev libgstreamer1.0-dev
```

Build via le wheel `opencv-python` (option la plus simple) :

```bash
export ENABLE_CONTRIB=0
export ENABLE_HEADLESS=1
export CMAKE_ARGS="-DWITH_GSTREAMER=ON"
python3 -m pip wheel . --verbose
python3 -m pip install opencv_python*.whl
```

Vérification : `python3 -c "import cv2; print(cv2.getBuildInformation())" | grep GStreamer` → `YES`.

---

## 7. Système de wake word (voix)

Détection sur le **Raspberry Pi 4B** (Picovoice Porcupine), communication vers le Jetson
via **MQTT** (broker Mosquitto sur le Jetson). Deux mots d'activation personnalisés :
**"Hey Mila"** (start) et **"Mila stop"** (stop).

### 7.1 Broker MQTT (Jetson)

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

### 7.2 Gestionnaire côté Jetson — `wake_word_handler.py`

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

### 7.3 Détecteur côté RPi 4B — `wake_word_v3.py`

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

### 7.4 Services systemd (démarrage automatique)

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

---

## 8. Séquence sonore de réveil

Audio géré sur le **RPi 4B** (proche de l'interaction, réponse plus rapide, décharge le Jetson).
Fichiers dans `mila_sounds/`.

```bash
# Test manuel d'un son
mpg123 -a hw:1,0 droid_waking_up.mp3
# Test de tous les sons
python3 test_audio_files.py
```

Le script `wake_word_v7.py` intègre la lecture audio et un paramètre de volume
(`--volume 140` = +40 %, ajustable). Le service systemd correspondant reprend la même
structure qu'au §7.4 en pointant vers `wake_word_v7.py` avec l'option `--volume`.

---

## 9. Yeux animés (écrans LCD GC9A01)

Deux écrans ronds 1.28" pilotés en SPI. Bibliothèque `lgpio` (obligatoire sous Bookworm).

```bash
cd ~/Downloads/LCD_Module_RPI_code/RaspberryPi/python/example
# Exemples fournis
sudo python blue_eyes.py
sudo python white_eyes.py
sudo python optical_illusions.py
sudo python dual_screen_matrix.py
# Animations custom
sudo python eye_animation_test.py     # 24 FPS pour plus de fluidité
```

---

## 10. Mécanique / modèle 3D

**Tête**

- Source originale du modèle que nous avons adapté
  - <https://www.etsy.com/ca/listing/904548923/spacebobs-securitydroid-inspired-body>
- Assemblage des 3 éléments de base en un seul fichier, allègement (retrait de matière),
  simplification du maillage (MeshLab / Meshmixer).
- Logement pour le Camera Module 2 (fixation/retrait faciles, trou pour la nappe 1 m).
- Fixation au servo TILT via 6 vis M3.
- Cou assez long pour la pleine amplitude de mouvement.
- Base **turntable** pour éviter le ballant dû à une fixation en un seul point sur le horn du servo PAN.

**Cou souple (TPU)** : imprimé en TPU pour stabiliser la tête, absorber son poids et
protéger la base quand l'alimentation est coupée (option flex hose envisagée).

---

## 11. Procédure de lancement manuel (résumé)

```bash
# 1) Jetson — gestionnaire de commandes
ssh <username>@<jetson-ip>
source /home/<username>/wake_word_env/bin/activate
cd Desktop/wake-word-handler
python wake_word_handler.py

# 2) RPi 4B — détecteur de wake word
ssh <username>@<rpi-ip>
source ~/porcupine_env/bin/activate
cd Desktop
python wake_word_v3.py --access_key "<PICOVOICE_ACCESS_KEY>" \
  --keyword_paths <hey-mila.ppn> <mila-stop.ppn> --audio_device_index 0
```

> Rappel : démarrer le Jetson (broker) avant le RPi (client).

---

## 12. Feuille de route (TODO)

- [ ] **Micro spatial** : remplacer le micro simple par un ReSpeaker USB Mic Array.
- [ ] **Alternative matérielle** : tester RPi + Coral Dual Edge TPU avec un modele local pour la voix

## 12. Feuille de route (TODO)

### Must-have — Refonte du support PAN/TILT

- [ ] Revoir le design du support PAN/TILT pour plus de stabilité.

### Must-have — Amélioration & développement de la séquence de démarrage

- [ ] **Alimentation unique** : allumer tous les composants d'un coup via un interrupteur physique maître (master power switch).
- [ ] **Retravailler la détection de wake word** : Picovoice Porcupine ne fonctionne plus — une solution alternative reste à trouver (piste : moteur open source sur micro USB + Raspberry Pi 4B).
- [ ] **Séquences d'animation custom** : mouvement + son.

### Must-have — Partie voix

- [ ] Concevoir un adaptateur imprimé en 3D pour connecter le smartphone.
- [ ] Utilisation d'un microphone spatial plutôt qu'un simple microphone (Type ReSpeaker USB Mic Array).
  - <https://wiki.seeedstudio.com/ReSpeaker-USB-Mic-Array/>
  - <https://www.seeedstudio.com/ReSpeaker-USB-Mic-Array-p-4247.html>

### Nice to have — Cosmétique

- [ ] Améliorer le design global de MILA.
- [ ] **Développer des séquences d'animation spécifiques** : mouvement + son.

### Nice to have — Infrastructure

- [ ] Visualiser dans Uptime Kuma que le système Mila est pleinement opérationnel
- [ ] Ajouter la configuration de Heartbeats dans Uptime Kuma (jetson, raspberry pi, etc.)
