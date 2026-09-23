# 0 Procédure de lancement manuel

## 0.1 Procédure de démarage de base (sans voix)

1. Brancher l'alimentation du Jetson (cable avec ruban **ROUGE**).
2. Brancher le cable d'alimentation (cable avec ruban **VERT**).
3. Les deux périphériques (Jetson et Raspberry Pi) sont connectés sur le même réseau wifi, vous devez vous connecter au même réseau (wifi ou Ethernet) avec votre ordinateur (PC). Demander au responsable pour savoir sur quel réseau vous connecter.
4. Ouvrir un terminal
    - Windows -> PowerShell
    - Linux -> Bash
    - Mac -> Zsh

### Connectez-vous au Raspberry Pi avec SSH, démarer Mila et déconnection du Raspberry Pi

```bash
# Commande pour activer Mila
ssh <username>@<raspberryPi4B address> mosquitto_pub -h <Jetson address> -t mila/control -m start_main_script
# Entrer le mot de passe du Raspberry PI
```

### Reconnectez-vous au Raspberry Pi avec SSH, arrêter Mila et deconnectez-vous du Raspberry Pi

```bash
# Commande pour désactiver Mila
ssh <username>@<raspberryPi4B adress> mosquitto_pub -h <Jetson address> -t mila/control -m stop_main_script
# Entrer le mot de passe
```

## 0.2 Procédure de démarage avec la voix (non fonctionnel)

- Cette séquence de démarage fonctionnait jusqu'à ce que le logiciel ne soit plus gratuit.

### A) Jetson — gestionnaire de commandes

```bash
ssh <username>@<jetson-ip>
source /home/<username>/wake_word_env/bin/activate
cd Desktop/wake-word-handler
python wake_word_handler.py
```

### B) RPi 4B — détecteur de wake word

```bash
ssh <username>@<rpi-ip>
source ~/porcupine_env/bin/activate
cd Desktop
python wake_word_v3.py --access_key "<PICOVOICE_ACCESS_KEY>" \
  --keyword_paths <hey-mila.ppn> <mila-stop.ppn> --audio_device_index 0
```

> Rappel : démarrer le Jetson (broker) avant le RPi (client).

## Retour à la table des matières

[Table des matières](../home.md)
