#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

const int servo1Pin = A0;
const int servo2Pin = 11;
const int servo3Pin = 12;

// Neutral Position is 1500
// Increase in pulse is more open
// Decrease in pulse is more closed
const int midPulse = 1500;
const int minPulse = 1150; // 1100 currently hitting something
const int maxPulse = 1850; // FULL OPEN is 1850
// Step delay is fastest at 1
// Increasing step delay (1-10) slows movement
const int stepDelay = 1;  // Delay between steps

// Change per input (higher number is slower)
// 30 is roughly max
const int pulseDelta = 5;

void setup() {
    servo1.attach(servo1Pin);
    servo2.attach(servo2Pin);
    servo3.attach(servo3Pin);
    Serial.begin(115200);
    Serial.println("Program started");
}

void loop() {
    Serial.println("Program running");
    delay(200); 
    moveServo(servo1, 1150, 1850);
    delay(200);
    moveServo(servo1, 1850, 1150);
    delay(200); 
    moveServo(servo3, 1150, 1850);
    delay(200);
    moveServo(servo3, 1850, 1150);
    
}

void moveServo(Servo &servoNum, int from, int to) {
    if (from < to) {
        for (int pulse = from; pulse <= to; pulse += pulseDelta) {
            servoNum.writeMicroseconds(pulse);

            // Correct way to check if this is servo3
            if (&servoNum == &servo3) { 
                servoNum.writeMicroseconds(maxPulse - (pulse - minPulse));
            }

            delay(stepDelay);
        }
    } else {
        for (int pulse = from; pulse >= to; pulse -= pulseDelta) {
            servoNum.writeMicroseconds(pulse);

            // Correct way to check if this is servo3
            if (&servoNum == &servo3) { 
                servoNum.writeMicroseconds(maxPulse - (pulse - minPulse));
            }

            delay(stepDelay);
        }
    }
}
