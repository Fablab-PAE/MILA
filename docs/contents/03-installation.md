# 3 Installation

## 3.1 Jetson (JetPack 6)

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

### 3.1.1 Vérification de l'environnement Jetson

| Composant | Commande | Version cible |
| ----------- | ---------- | --------------- |
| JetPack / L4T | `dpkg -l \| grep nvidia-l4t-core` | 36.3 (arm64/aarch64) |
| Ubuntu | `lsb_release -a` | 22.04.4 LTS |
| Python pip | `sudo apt install python3-pip` | — |
| OpenCV | `python3 -c "import cv2; print(cv2.__version__)"` | 4.8.0 |
| GStreamer (OpenCV) | `python3 -c "import cv2; print(cv2.getBuildInformation())" \| grep GStreamer` | YES (1.20.3) |
| CUDA | `nvcc --version` | 12.2.140 |
| TensorRT | `dpkg -l \| grep nvinfer` | 8.6.2 |
| GPU | `nvidia-smi` | — |

## 3.2 Installation Raspberry Pi

### 3.2.1 Installer le projet à partir du dépôt Github

1. Installer NodeJS, npm et git

```bash
sudo apt update && sudo apt install nodejs git mosquitto-clients -y;
# Télécharger nvm pour obtenir la dernière version de nodeJS sinon Angular ne fonctionne pas.
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash

# redémarre le shell
\. "$HOME/.nvm/nvm.sh"

# installer Node.js:
nvm install node

# Verifier version:
node -v && npm -v

sudo ln -sfn "$(nvm which default)" /opt/mila/node
```

2. Cloner le projet MILA héberger chez Github

```bash
cd ~
git clone https://github.com/Fablab-PAE/MILA.git &&\
cd MILA
```

3. Installer le projet

> **⚠️ IMPORTANT!**
>
> Utiliser le fichier RaspberryPi/services/myenv.conf-example comme gabarit pour le fichier /etc/systemd/system/server-mila.service.d/myenv.conf, changer les informations suivante quand d'éditeur nano s'ouvre dans le terminal :
>
>- username : le username du projet
>- groupname : le groupe dans lequel le username est rattaché
>- project parent directory : le chemin vers le dossier parent au projet

**BACK-END SERVEUR ExpressJS, s'assurer que vous êtes dans le dossier du projet <parent path>/MILA/**

```bash
cd RaspberryPi &&\
npm --prefix node-server/ install &&\
sudo systemctl link services/server-mila.service &&\
sudo mkdir -p /etc/systemd/system/server-mila.service.d &&\
sudo nano /etc/systemd/system/server-mila.service.d/myenv.conf &&\
mkdir -p node-server/logs &&\
sudo systemctl daemon-reload &&\
sudo systemctl enable --now server-mila &&\
cd ..
```

**FRONT-END ANGULAR, s'assurer que vous êtes dans le dossier du projet <parent path>/MILA/**
```bash
cd RaspberryPi/node-server/front-end &&\
npm install &&\
ng build
```

4. Mettre le projet MILA à jour

**S'assurer que vous êtes dans le dossier du projet <parent path>/MILA/**

```bash
git checkout main &&\
git pull &&\
npm --prefix RaspberryPi/node-server install &&\
sudo systemctl daemon-reload &&\
sudo systemctl restart server-mila &&\
cd RaspberryPi/node-server/front-end &&\
npm install &&\
ng build
```

5. Verification du service server-mila.service

```bash
systemctl cat server-mila # doit afficher le unit + le drop-in fusionnés
systemd-analyze verify /etc/systemd/system/server-mila.service
systemctl status server-mila
```

## Retour à la table des matières

[Table des matières](../home.md)
