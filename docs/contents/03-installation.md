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
| TensorRT | `dpkg -l && grep nvinfer` | 8.6.2 |
| GPU | `nvidia-smi` | — |

## 3.2 Installation Raspberry Pi

### 3.2.1 Installer le projet à partir du dépôt Github

1. Installer NodeJS, npm et git

````bash
sudo apt update && sudo apt install nodejs npm git -y;
```

2. Cloner le projet MILA héberger chez Github

```bash
cd ~
git clone https://github.com/Fablab-PAE/MILA.git
```

3. Installer le projet

```bash
npm i ~/MILA/RaspberryPi/node-server/ &&\
sudo cp ~/MILA/RaspberryPi/server-mila.service /etc/systemd/system/
sudo systemctl start server-mila.service
```

4. Mettre le projet MILA à jour

```bash
cd ~/MILA &&\
git checkout main &&\
git pull &&\
npm i ~/MILA/RaspberryPi/node-server/ &&\
sudo cp ~/MILA/RaspberryPi/server-mila.service /etc/systemd/system/server-mila.service &&\
sudo systemctl restart server-mila.service
```

## Retour à la table des matières

[Table des matières](../home.md)
