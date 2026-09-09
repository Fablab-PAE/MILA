# 5 Inférence & suivi de visage

## 5.1 Environnement virtuel

Toujours travailler dans un venv héritant des paquets système :

```bash
python3 -m venv --system-site-packages /home/<username>/myenv
source /home/<username>/myenv/bin/activate
pip list
```

## 5.2 Chaîne TensorRT (modèle YOLOv8n Face, FP16)

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

## 5.3 Alternatives d'inférence évaluées

- **TensorRT + DeepStream SDK** (7.0) avec le dépôt `DeepStream-Yolo` de marcoslucianops.
- **Serveur d'inférence Roboflow auto-hébergé** (image TensorRT Jetson).
- **jetson-inference** (dusty-nv) en Docker : modèles `TAO FaceDetect` / `SSD-Mobilenet-v2`.
- **YuNet** (OpenCV Zoo) — retenu comme détecteur de visage léger pour le suivi.
- **ResNet-50 / DETR**, **YOLOv8n-cls** pour de la classification/reconnaissance.

## 5.4 Boucle de suivi temps réel

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

## 5.5 Exécution

```bash
ssh <username>@<jetson-ip>
cd Desktop/ultralytics
source /home/<username>/myenv/bin/activate
python3 2_Automated_servo_control_no_display_v2.py        # avec mouvements servomoteurs
sudo jtop                                   # suivi ressources CPU/GPU
```

## Retour à la table des matières

[Home](../home.md)
