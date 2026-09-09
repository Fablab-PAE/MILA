# 12. Feuille de route (TODO)

## Must-have

### Refonte du support PAN/TILT

- [ ] Revoir le design du support PAN/TILT pour plus de stabilité.

### Amélioration & développement de la séquence de démarrage

- [ ] **Alimentation unique** : allumer tous les composants d'un coup via un interrupteur physique maître (master power switch).
- [ ] **Retravailler la détection de wake word** : Picovoice Porcupine ne fonctionne plus — une solution alternative reste à trouver (piste : moteur open source sur micro USB + Raspberry Pi 4B).
- [ ] **Séquences d'animation custom** : mouvement + son.

### Partie voix

- [ ] Concevoir un adaptateur imprimé en 3D pour connecter le smartphone.
- [ ] Utilisation d'un microphone spatial plutôt qu'un simple microphone (Type ReSpeaker USB Mic Array).
  - <https://wiki.seeedstudio.com/ReSpeaker-USB-Mic-Array/>
  - <https://www.seeedstudio.com/ReSpeaker-USB-Mic-Array-p-4247.html>

## Nice to have

### Cosmétique

- [ ] Améliorer le design global de MILA.
- [ ] **Développer des séquences d'animation spécifiques** : mouvement + son.

### Infrastructure

- [ ] Visualiser dans Uptime Kuma que le système Mila est pleinement opérationnel
- [ ] Ajouter la configuration de Heartbeats dans Uptime Kuma (jetson, raspberry pi, etc.)

### Améliorations du matériel

- [ ] **Micro spatial** : remplacer le micro simple par un ReSpeaker USB Mic Array.
- [ ] **Alternative matérielle** : tester RPi + Coral Dual Edge TPU avec un modele local pour la voix

## Retour à la table des matières

[Home](../home.md)
