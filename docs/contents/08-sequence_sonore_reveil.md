# 8 Séquence sonore de réveil

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

## Retour à la table des matières

[Home](../home.md)
