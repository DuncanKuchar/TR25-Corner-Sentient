#include <Adafruit_MCP2515.h>
#include <Servo.h>

// SERVO SETUP

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

//CAN SETUP

#define CS_PIN    (19u)
// Set CAN bus baud rate
#define CAN_BAUDRATE (1000000)

Adafruit_MCP2515 mcp(CS_PIN);

const int precision = 2; // UPDATE when updating racecapture precision

// CURRENT SETUP: this variable stores one packet of CAN data.
// The array indices are as follows:
/*
  0 = accel X
  1 = accel Y
  2 = accel Z
  3 = TPS
*/
double can_data[4];

void setup() {
  Serial.begin(115200);
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  servo3.attach(servo3Pin);
  Serial.println("Program started");

  while(!Serial) delay(10);

  Serial.println("MCP2515 Receiver test!");

  if (!mcp.begin(CAN_BAUDRATE)) {
    Serial.println("Error initializing MCP2515.");
    while(1) delay(10);
  }
  Serial.println("MCP2515 chip found");
}

void loop() {
  mcp.beginPacket(0x2);
  mcp.write(1);
  mcp.endPacket();

  // try to parse packet
  int packetSize = mcp.parsePacket();

  if (packetSize) {
    // received a packet
    Serial.print("Received ");

    if (mcp.packetExtended()) {
      Serial.print("extended ");
    }

    if (mcp.packetRtr()) {
      // Remote transmission request, packet contains no data
      Serial.print("RTR ");
    }

    Serial.print("packet with id 0x");
    Serial.print(mcp.packetId(), HEX);

    if (mcp.packetRtr()) {
      Serial.print(" and requested length ");
      Serial.println(mcp.packetDlc());
    } else {
      Serial.print(" and length ");
      Serial.println(packetSize);
      
      int i = 0;
      // only print packet data for non-RTR packets
      // This while loop extracts all of the CAN data and puts it into the data array.
      while (mcp.available()) {
        can_data[i] = (double)mcp.read();
        Serial.print(can_data[i]);
        i++;
      }
      Serial.println("\nGot TPS value: " + String(can_data[3]));
    }

    Serial.println();
    int mapedValue = mapValue(can_data[3]);
    servo1.writeMicroseconds(mapedValue);
    servo3.writeMicroseconds(1850 - (mapedValue - 1150));
  }
  

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

int mapValue(int input) {
    return (input * (1850 - 1150)) / 100 + 1150;
}