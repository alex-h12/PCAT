#include <Arduino.h>
#include <HX711.h>
#include <Servo.h>

#define HX711_DOUT 3
#define HX711_SCK 2
#define SERVO_PIN 9

HX711 scale;
Servo servo;

float calibration_factor = -7050.0;

void setup() {
  Serial.begin(115200);

  scale.begin(HX711_DOUT, HX711_SCK);
  scale.set_scale(calibration_factor);
  scale.tare();

  servo.attach(SERVO_PIN);
  servo.write(0);
}

void loop() {
  if (Serial.available()) {
    int angle = Serial.parseInt();
    angle = constrain(angle, 0, 90);
    
    servo.write(angle);
  }

  if (scale.is_ready()) {
    Serial.println(scale.get_units(3));
  }

  delay(50);
}
