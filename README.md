# Mila — Une tête robotisée servant comme assistant de laboratoire

Le Projet **Mila** est une initiative de l'organisme [Place à l'emploi](https://placealemploi.ca/) de Longueuil dans le cadre du plateau d'exploration professionnel nommé **Robo-Tic**. Ce plateau exploratoire est destiné à des personnes sans emploi et qui ne sont pas aux études afin de leur permettre de développer de nouvelles compétences et d'expérimenter concrètement de nouveaux outils utiles sur le marché. Le but de **Mila** est de permettre l'exploration du domaine de la robotique de base aux participants.

## Qu'est-ce que le projet **Mila** ?

**Mila** est une tête imprimée en 3D qui détecte et suit le visage d'un passant en **temps réel (souple)**. C'est grâce à une caméra miniature et deux servomoteurs donnant une mobilité à une tête de robot verticalement et horizontalement. La tête de robot est également dotée d'yeux animés avec deux écrans LCD.

L'activation vocale et l'uniformité de la séquence d'allumages sont des fonctionnalités en cours de développement. (2026-09-08)

## Architecture générale

Le système est réparti sur trois cartes qui communiquent via le réseau (Wi-Fi) et MQTT.

| Rôle | Carte | Responsabilité |
| ------ | ------ | ---------------- |
| Cerveau / inférence | Jetson Orin Nano 8GB | Capture vidéo, détection de visage, boucle de contrôle des servomoteurs, broker MQTT |
| Actionneurs | ESP32-S3 | Génère les signaux PWM pour les deux servomoteurs, sur ordre série depuis le Jetson |
| Voix + yeux | Raspberry Pi 4B | Détection de mot d'activation (wake word), lecture audio, animation des yeux LCD |

### Flux d'activation vocale désirée (2026-09-08)

``` text
Utilisateur dit "Hey Mila"
   └─> RPi 4B (wake word) publie "start_main_script" sur MQTT
          └─> Jetson (wake_word_handler) lance main.py
                 └─> Caméra → détection visage → boucle de contrôle → ESP32 → servomoteurs

Utilisateur dit "Mila stop"
   └─> RPi 4B publie "stop_main_script" sur MQTT
          └─> Jetson arrête main.py, servomoteurs remis en position initiale
```

### Ordre d'allumage actuel (2026-09-08)

1. Démarrer le Jetson **(broker MQTT)**
2. Attendre quelques millisecondes, pour que le **(broker MQTT)** soit disponible quand le **(client MQTT)** se connecte.
3. Démarrer le Raspberry Pi **(client MQTT)**

## Matériel

### Environnement

| Composant | Version actuelle |
| ----------- | --------------- |
| JetPack / L4T | 36.3 (arm64/aarch64) |
| Ubuntu | 22.04.4 LTS |
| OpenCV | 4.8.0 |
| GStreamer (OpenCV) | 1.20.3 |
| CUDA | 12.2.140 |
| TensorRT | 8.6.2 |

### Jetson Orin Nano 8 GB (reComputer J3011)

- <https://www.seeedstudio.com/reComputer-J3011-p-5590.html>
- <https://wiki.seeedstudio.com/reComputer_Jetson_Series_Hardware_Layout/>
- 40 TOPS pour toute l'inférence.
- JetPack 6
- Utilise l'antenne fournie pour le Wi-Fi
- GPIOs
  - <https://www.seeedstudio.com/reComputer-J3011-p-5590.html>

### ESP32-S3

- Génère le PWM des servos via le périphérique `LEDC`.
- Broche PAN : **GPIO 17** (canal `LEDC_CHANNEL_1`).
- Broche TILT : **GPIO 16** (canal `LEDC_CHANNEL_0`).
- Exposé côté Jetson sur `/dev/esp32s3serial` (alias udev), 115200 bauds.

### Servos

- 2× servomoteurs RDS 35 kg, plage 270°, pour les mouvements PAN et TILT.
  - <https://www.amazon.ca/dp/B08J7Q3PPB>
- Chaque servomoteur est alimenté par un chargeur 5V 3A
  - <https://www.amazon.ca/dp/B0811H9GQ3?th=1>

### Caméra

- Raspberry Pi Camera Module v2 (cable CSI), flux 30 fps.

### Yeux — écrans LCD

- 2× Waveshare LCD IPS rond 1.28" (driver GC9A01, SPI, 240×240, 65K couleurs, 60 Hz).
  - <https://www.amazon.ca/dp/B0BD54FQVS>
- intégrés au RPi 4B.

### Audio

- Haut-parleur Creative Pebble V2 (USB), branché sur le RPi 4B.
  - <https://www.amazon.ca/dp/B07VVP8BGD>
- Alimenté par son propre bloc secteur (et non par le RPi).

## Mécanique / modèle 3D

### Tête

- Source originale du modèle que nous avons adapté [->Source](https://www.etsy.com/ca/listing/904548923/spacebobs-securitydroid-inspired-body?click_key=d7a92b065a90da3a2e78b3c99f8ba92b996ab0e8%3A904548923&click_sum=26bc1f7f&ref=shop_home_recs_3&crt=1&sts=1)
- Assemblage des 3 éléments de base en un seul fichier, allègement (retrait de matière),
simplification du maillage (MeshLab / Meshmixer).
- Logement pour le Camera Module 2 (fixation/retrait facile, trou pour la nappe 1 m).
- Fixation au servomoteur TILT via 6 vis M3.
- Cou assez long pour la pleine amplitude de mouvement.
- Base *turntable* pour éviter le ballant dû à une fixation en un seul point sur le *horn* du servomoteur PAN.

### Cou souple (TPU)

- Imprimé en TPU pour stabiliser la tête, absorber son poids et protéger la base quand l'alimentation est coupée (une option *flex hose* est envisagée).

## Feuille de route (TODO)

### Must-have — Refonte du support PAN/TILT

- [ ] Revoir le design du support PAN/TILT pour plus de stabilité.

### Must-have — Amélioration & développement de la séquence de démarrage

- [ ] **Alimentation unique** : allumer tous les composants d'un coup via un interrupteur physique maître (master power switch).
- [ ] **Retravailler la détection de *wake word*** : Picovoice Porcupine ne fonctionne plus — une solution alternative reste à trouver (piste : moteur *open source* sur micro-USB + Raspberry Pi 4B).
- [ ] **Séquences d'animation custom** : mouvement + son.

### Must-have — Partie voix

- [ ] Concevoir un adaptateur imprimé en 3D pour connecter un téléphone intelligent.
- [ ] Utilisation d'un microphone spatial plutôt qu'un simple microphone (Type ReSpeaker USB Mic Array).
  - <https://wiki.seeedstudio.com/ReSpeaker-USB-Mic-Array/>
  - <https://www.seeedstudio.com/ReSpeaker-USB-Mic-Array-p-4247.html>

### Nice to have — Cosmétique

- [ ] Améliorer le design global de MILA.
- [ ] **Développer des séquences d'animation spécifiques** : mouvement + son.

### Nice to have — Infrastructure

- [ ] Visualiser dans Uptime Kuma que le système Mila est pleinement opérationnel
- [ ] Ajouter la configuration de Heartbeats dans Uptime Kuma (jetson, raspberry pi, etc.)
- [ ] **Micro spatial** : remplacer le micro simple par un ReSpeaker USB Mic Array.
- [ ] **Alternative matérielle** : tester RPi + Coral Dual Edge TPU avec un modèle local pour la voix
