# 1 Architecture générale

Le système est réparti sur trois cartes qui communiquent via le réseau (Wi-Fi) et MQTT.

| Rôle | Carte | Responsabilité |
| ------ | ------ | ---------------- |
| Cerveau / inférence | Jetson Orin Nano 8GB | Capture vidéo, détection de visage, boucle de contrôle des servomoteurs, broker MQTT |
| Actionneurs | ESP32-S3 | Génère les signaux PWM pour les deux servomoteurs, sur ordre série depuis le Jetson |
| Voix + yeux | Raspberry Pi 4B | Détection de mot d'activation (wake word), lecture audio, animation des yeux LCD |

## Flux d'activation vocale désirée (2026-09-08)

``` text
Utilisateur dit "Hey Mila"
   └─> RPi 4B (wake word) publie "start_main_script" sur MQTT
          └─> Jetson (wake_word_handler) lance main.py
                 └─> Caméra → détection visage → boucle de contrôle → ESP32 → servomoteurs

Utilisateur dit "Mila stop"
   └─> RPi 4B publie "stop_main_script" sur MQTT
          └─> Jetson arrête main.py, servomoteurs remis en position initiale
```

## Ordre d'allumage actuel (2026-09-08)

1. Démarrer le Jetson **(broker MQTT)**
2. Attendre quelques millisecondes, pour que le **(broker MQTT)** soit disponible quand le **(client MQTT)** se connecte.
3. Démarrer le Raspberry Pi **(client MQTT)**

## Retour à la table des matières

[Home](../home.md)
