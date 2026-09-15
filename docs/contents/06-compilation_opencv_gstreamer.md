# 6 Compilation OpenCV avec GStreamer (nvargus)

Le support GStreamer n'est pas activé par défaut : il faut installer GStreamer puis
**recompiler OpenCV**.

```bash
sudo apt update
# Pile GStreamer
sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools

# Dépendances de build OpenCV
sudo apt install build-essential cmake git pkg-config libgtk-3-dev \
  libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev \
  libjpeg-dev libpng-dev libtiff-dev gfortran openexr libatlas-base-dev \
  python3-dev python3-numpy libtbb-dev libgstreamer1.0-dev
```

Build via le wheel `opencv-python` (option la plus simple) :

```bash
export ENABLE_CONTRIB=0
export ENABLE_HEADLESS=1
export CMAKE_ARGS="-DWITH_GSTREAMER=ON"
python3 -m pip wheel . --verbose
python3 -m pip install opencv_python*.whl
```

Vérification : `python3 -c "import cv2; print(cv2.getBuildInformation())" | grep GStreamer` → `YES`.

## Retour à la table des matières

[Home](../home.md)
