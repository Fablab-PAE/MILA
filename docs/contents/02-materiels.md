# 2 Matériels

## Environnement

| Composant | Version actuelle |
| ----------- | --------------- |
| JetPack / L4T | 36.3 (arm64/aarch64) |
| Ubuntu | 22.04.4 LTS |
| OpenCV | 4.8.0 |
| GStreamer (OpenCV) | 1.20.3 |
| CUDA | 12.2.140 |
| TensorRT | 8.6.2 |

## Jetson Orin Nano 8 GB (reComputer J3011)

- <https://www.seeedstudio.com/reComputer-J3011-p-5590.html>
- <https://wiki.seeedstudio.com/reComputer_Jetson_Series_Hardware_Layout/>
- 40 TOPS pour toute l'inférence.
- JetPack 6
- Utilise l'antenne fournie pour le Wi-Fi
- GPIOs
  - <https://www.seeedstudio.com/reComputer-J3011-p-5590.html>

## ESP32-S3

- Génère le PWM des servos via le périphérique `LEDC`.
- Broche PAN : **GPIO 17** (canal `LEDC_CHANNEL_1`).
- Broche TILT : **GPIO 16** (canal `LEDC_CHANNEL_0`).
- Exposé côté Jetson sur `/dev/esp32s3serial` (alias udev), 115200 bauds.

## Servomoteurs

- 2× servomoteurs RDS 35 kg, plage 270°, pour les mouvements PAN et TILT.
  - <https://www.amazon.ca/dp/B08J7Q3PPB>
- Chaque servomoteur est alimenté par un chargeur 5V 3A
  - <https://www.amazon.ca/dp/B0811H9GQ3?th=1>

## Caméra

- Raspberry Pi Camera Module v2 (cable CSI), flux 30 fps.

## Yeux — écrans LCD

- 2× Waveshare LCD IPS rond 1.28" (driver GC9A01, SPI, 240×240, 65K couleurs, 60 Hz).
  - <https://www.amazon.ca/dp/B0BD54FQVS>
- intégrés au RPi 4B.

## Audio

- Haut-parleur Creative Pebble V2 (USB), branché sur le RPi 4B.
  - <https://www.amazon.ca/dp/B07VVP8BGD>
- Alimenté par son propre bloc secteur (et non par le RPi).

## Retour à la table des matières

[Home](../home.md)
