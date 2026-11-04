# Procédure de lancement manuel

## Procédure de démarrage avec un navigateur internet

Ouvrir un navigateur internet connecté sur le même réseau que le Raspberry PI.

- **Démarrer MILA**
  - entrer l'adresse suivante dans le navigateur `http://<Raspberry IP>:3000/mila/start`
- **Arrêter MILA**
  - entrer l'adresse suivante dans le navigateur `http://<Raspberry IP>:3000/mila/stop`

## Procédure de démarrage de base avec SSH

1. Brancher l'alimentation du Jetson (cable avec ruban **ROUGE**).
2. Brancher le cable d'alimentation (cable avec ruban **VERT**).
3. Les deux périphériques (Jetson et Raspberry Pi) sont connectés sur le même réseau wifi, vous devez vous connecter au même réseau (wifi ou Ethernet) avec votre ordinateur (PC). Demander au responsable pour savoir sur quel réseau vous connecter.
4. Ouvrir un terminal
    - Windows -> PowerShell
    - Linux -> Bash
    - Mac -> Zsh

### DÉMARRAGE MILA : Connectez-vous au Raspberry Pi avec SSH, démarrer Mila et déconnection du Raspberry Pi

```bash
# Commande pour activer Mila
ssh <username>@<raspberryPi4B address> mosquitto_pub -h <Jetson address> -t mila/control -m start_main_script
# Entrer le mot de passe du Raspberry PI
```

### ARRÊT MILA : Reconnectez-vous au Raspberry Pi avec SSH, arrêter Mila et deconnectez-vous du Raspberry Pi

```bash
# Commande pour désactiver Mila
ssh <username>@<raspberryPi4B adress> mosquitto_pub -h <Jetson address> -t mila/control -m stop_main_script
# Entrer le mot de passe
```

### STATUS MILA : Reconnectez-vous au Raspberry Pi avec SSH, obtenir l'état de Mila et deconnectez-vous du Raspberry Pi

#### Obtenir la dernière commande reçue

```bash
mosquitto_sub -h <jetson IP> -t 'mila/#' -v -q 1 -i "rpi-status-test-$$"
```

-t 'mila/#' : écoute mila/status, mila/handler/availability et mila/control en même temps.
-v : affiche le sujet avec chaque message.
-q 1 : QoS 1.

```bash
# BACKUP COMMAND
# Pour une vérification ponctuelle, qui se termine seule :
mosquitto_sub -h <jetson IP> -t mila/status -C 1 -W 5 -q 1; echo "code=$?"
```

-C 1 : s'arrête après un message.
-W 5 : abandonne après 5 secondes.
Code 0 : un état a été reçu.
Code 27 : timeout. Aucun état n'est conservé, ou le gestionnaire ne publie pas encore sur mila/status.

Pour tester sans modifier le gestionnaire, tu peux simuler un état conservé :

```bash
mosquitto_pub -h <jetson IP> -t mila/status -r -q 1 -m '{"state":"stopped"}'
```
Ce message sera écrasé par la vraie publication du gestionnaire. Si tu veux effacer cet état de test, publie un message vide avec -r -n.



## Procédure de démarage avec la voix (non fonctionnel)

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
