#include <Adafruit_MCP2515.h>
#include <Servo.h>

// SERVO SETUP

Servo servo1;
Servo servo2;
Servo servo3;

const int servo1Pin = A0;
const int servo2Pin = 11;
const int servo3Pin = 12;

const int onOffPin = 8; // dont know which is which could be 9 8 10, 10 8 9, etc.
const int DRSPin = 9;
const int sensPin = 10;

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
  4 = wheel speed
  5 = brake pressure
  6 = steering angle
*/
double can_data[6];
short current_state;
short next_state;

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
    // while(1) delay(10);
  }
  Serial.println("MCP2515 chip found");

  pinMode(onOffPin, INPUT);
  pinMode(DRSPin, INPUT);
  pinMode(sensPin, INPUT);
}

void loop() {
  Serial.print("onOffPi: ");
  Serial.println(digitalRead(onOffPin));
  Serial.print("DRSPin: ");
  Serial.println(digitalRead(DRSPin));
  Serial.print("sensPin: ");
  Serial.println(digitalRead(sensPin));

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

    // At this point we have read the current CAN packet and can begin processing
    //nextState(); // Calculates next state
    //updateState(); // Updates the current state and addresses the servos if the state changed.
  }
  

}
/*
short nextState() {
  int on = digitalRead(onOffPin);
  int low_drag = digitalRead(DRSPin);

  double accel_x = can_data[0]
  double accel_y = can_data[1]

  double TPS = can_data[3]
  double wheel_speed = can_data[4]
  double brake_pressure = can_data[5]
  double steering_angle = can_data[6]

  switch (current_state) {
    case 1: // Medium Downforce
      if (!on) {
        next_state = 0;
      } else if (low_drag) {
        next_state = 2;
      } else if ((  brake_pressure > ???
                  || accel_x > ???)
                || (steering_angle > ???
                  || accel_y > ???)
                ) {
        next_state = 0;
      } else if (  accel_y < ???
                && steering_angle < ???
              ) {
        next_state = 2;
      }
    break;

    case 2: // DRS / Low Drag
      // System disabled, should default to low drag
      if (!on) {
        next_state = 0;
      } else if (!low_drag) {
        if (   TPS < ???
          && (steering_angle > ???
            || ( brake_pressure > ???
              || accel_x > ???
              )
            )
          ) {
          next_state = 0;
        } else if (  wheel_speed > ???
                  && ( accel_y > ???
                    || steering_angle > ???
                  )
                ) {
          next_state = 1;
        }
      }
    break;

    default: // Maximum Downforce
      // If we're not on then we should do nothing
      if (on) {
        // If we're switched on and set to low drag, we should set our state to low drag
        if (low_drag) {
          next_state = 2;
        } else if (  TPS > ???
                  && steering_angle < ???
                  && accel_y < ???
                  && brake_pressure < ???) {
          next_state = 2;
        } else if ( wheel_speed > ??? 
                  && ( accel_y < ???
                    || steering_angle < ???
                  )) {
          next_state = 1;
        }
      }
    break;
  }
}

void updateState() { // Basic function to perform state updates.
  if (current_state != next_state) { // If the state should change, change it and perform corresponding actions
    current_state = next_state;
    switch (current_state) {
      case 1: // Medium Downforce
        //Servos are set here
      break;
      case 2: // DRS / Low Drag
        //Servos are set here
      break;
      default: // High Downforce
        //Servos are set here
      break;
    }
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
}**/

int mapValue(int input) {
    return (input * (1850 - 1150)) / 100 + 1150;
}