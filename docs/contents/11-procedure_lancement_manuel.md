# 11 Procédure de lancement manuel (résumé)

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

## Retour à la table des matières

[Home](../home.md)
