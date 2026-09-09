# 4 Contrôle des servomoteurs (ESP32 + Python)

Le Jetson envoie des commandes texte (`PAN:<angle>\n` ou `TILT:<angle>\n`) sur le port
série ; l'ESP32 les convertit en largeur d'impulsion PWM.

## 4.1 Firmware ESP32 — `sketch_servo_PAN_TILT.ino`

Principe : PWM 50 Hz, résolution 14 bits, largeur d'impulsion 500–2500 µs mappée sur 0–270°.

```cpp
#include "driver/ledc.h"

#define SERVO_PAN_PIN 17
#define SERVO_TILT_PIN 16
#define SERVO_PAN_CHANNEL LEDC_CHANNEL_1
#define SERVO_TILT_CHANNEL LEDC_CHANNEL_0
#define LEDC_BASE_FREQ 50        // Servo à 50 Hz
#define MAX_DUTY_CYCLE 16383     // résolution 14 bits
#define PULSE_WIDTH_MIN 500      // µs
#define PULSE_WIDTH_MAX 2500     // µs

uint32_t pulseWidthToDutyCycle(uint32_t pulseWidth) {
  return (pulseWidth * MAX_DUTY_CYCLE) / 20000;   // période 20 ms
}

void setupPWM(uint8_t pin, ledc_channel_t channel) {
  ledc_timer_config_t ledc_timer = {
    .speed_mode = LEDC_LOW_SPEED_MODE,
    .duty_resolution = LEDC_TIMER_14_BIT,
    .timer_num = LEDC_TIMER_0,
    .freq_hz = LEDC_BASE_FREQ,
    .clk_cfg = LEDC_AUTO_CLK,
  };
  ledc_timer_config(&ledc_timer);

  ledc_channel_config_t ledc_channel = {
    .gpio_num = pin,
    .speed_mode = LEDC_LOW_SPEED_MODE,
    .channel = channel,
    .intr_type = LEDC_INTR_DISABLE,
    .timer_sel = LEDC_TIMER_0,
    .duty = 0,
    .hpoint = 0
  };
  ledc_channel_config(&ledc_channel);
}

void setServoAngle(ledc_channel_t channel, int angle) {
  if (angle < 0 || angle > 270) { Serial.print("Invalid angle: "); Serial.println(angle); return; }
  uint32_t pulseWidth = map(angle, 0, 270, PULSE_WIDTH_MIN, PULSE_WIDTH_MAX);
  uint32_t dutyCycle = pulseWidthToDutyCycle(pulseWidth);
  ledc_set_duty(LEDC_LOW_SPEED_MODE, channel, dutyCycle);
  ledc_update_duty(LEDC_LOW_SPEED_MODE, channel);
}

void setup() {
  Serial.begin(115200);
  setupPWM(SERVO_PAN_PIN, SERVO_PAN_CHANNEL);
  setupPWM(SERVO_TILT_PIN, SERVO_TILT_CHANNEL);
  Serial.println("Setup complete, waiting for commands...");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    if (input.startsWith("PAN:"))  setServoAngle(SERVO_PAN_CHANNEL,  input.substring(4).toInt());
    else if (input.startsWith("TILT:")) setServoAngle(SERVO_TILT_CHANNEL, input.substring(5).toInt());
  }
}
```

> Historique : des sketches séparés `sketch_servo_PAN.ino` / `sketch_servo_TILT.ino`
> existaient avant d'être fusionnés dans ce fichier unique.

## 4.2 Côté Python

Helper commun d'envoi de commande :

```python
import serial

def move_servo(servo, position):
    command = f"{servo}:{position}\n"
    ser.write(command.encode())
```

- **`servo_control_PAN_TILT.py`** : balayage automatique de test, alterne les deux servomoteurs
  entre leurs bornes (PAN 0–270°, milieu 125° ; TILT 20–270°, milieu 140°).
- **`servo_control_XBOX.py`** : contrôle manuel au D-pad d'une manette Xbox (via `pygame`),
  ±1° par appui, positions initiales PAN=125 / TILT=140.
- **`servo_control_XBOX_RATE.py`** (version de référence) : contrôle manuel cadencé à
  **30 instructions/s** (fenêtre de 33 ms, calquée sur les 30 FPS caméra), avec :
  - incréments distincts : **PAN 4°**, **TILT 2°** par instruction ;
  - bornes logicielles TILT restreintes (30°–76°) pour protéger la mécanique ;
  - retour progressif ("smooth") aux positions initiales à la sortie.

## 4.3 Manette Xbox — règle udev

Alias stable pour la manette :

```ini
# /etc/udev/rules.d/99-joystick.rules
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="02d1", MODE="0666", GROUP="input", SYMLINK+="xbox_controller"
```

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
ls -l /dev/xbox_controller   # -> input/eventN
```

## 4.4 Débogage série

```bash
# Voir les logs série de l'ESP32
sudo minicom -b 115200 -D /dev/esp32s3serial   # quitter : Ctrl+A puis X
# Si le port est occupé
sudo lsof | grep /dev/esp32s3serial
sudo kill <PID>
```

## Retour à la table des matières

[Home](../home.md)
