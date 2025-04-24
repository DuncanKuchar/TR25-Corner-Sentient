#include <Adafruit_MCP2515.h>
#include <Servo.h>

// SERVO SETUP

Servo servo1;
Servo servo2;
Servo servo3;

const int servo1Pin = 4;
const int servo2Pin = 24;
const int servo3Pin = 25;

const int onOffPin = 6;
const int DRSPin = 9;
const int sensPin = A3;

// Neutral Position is 1500
// Increase in pulse is more closed
// Decrease in pulse is more open
const int midPulse = 1500;
const int minPulse = 1000;
const int maxPulse = 1945;
const int midPulseR = 1500;
const int minPulseR = 900;
const int maxPulseR = 1945;
int frontPulse = 1945;
int rearPulse = 1945;
// Step delay is fastest at 1
// Increasing step delay (1-10) slows movement
//const int stepDelay = 1;  // Delay between steps
//unsigned long lastTime = 0;

const int pulseDelta = 1000;

unsigned long lastAttachTime = 0;
bool attached = false;

//CAN SETUP

#define CS_PIN    (19u)
// Set CAN bus baud rate
#define CAN_BAUDRATE (500000)

Adafruit_MCP2515 mcp(CS_PIN);

const int precision = 2; // UPDATE when updating racecapture precision

// CURRENT SETUP: this variable stores one packet of CAN data.
// The array indices are as follows:
/*
  0 = accel X
  1 = accel Y
  2 = TPS
  3 = wheel speed FR
  4 = wheel speed FL
  5 = brake pressure
  6 = steering angle
*/
double can_data[7];
short current_state;
short next_state;

void setup() {
  Serial.begin(115200);
  //while(!Serial) delay(10);
  Serial.println("Started setup function");
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
  servo3.attach(servo3Pin);
  Serial.println("Program started");

  Serial.println("MCP2515 Receiver test!");

  if (!mcp.begin(CAN_BAUDRATE)) {
    Serial.println("Error initializing MCP2515.");
    while(1) delay(10);
  }
  Serial.println("MCP2515 chip found");

  pinMode(onOffPin, INPUT_PULLUP);
  pinMode(DRSPin, INPUT_PULLUP);
  pinMode(sensPin, INPUT);
  //Serial.println("1");

  servo1.writeMicroseconds(maxPulse);
  servo2.writeMicroseconds((3000) - maxPulse);
  servo3.writeMicroseconds((3000) - maxPulse);

  servo1.detach();
  servo2.detach();
  servo3.detach();
  //Serial.println("2");
}

int updateState() { // Basic function to perform state updates.
  int pulse = maxPulse;
  switch (current_state) {
    case 1: // Medium Downforce
      pulse = midPulse;
    break;
    case 2: // DRS / Low Drag
      pulse = minPulse;
    break;
    default:
      pulse = maxPulse;
    break;
  }
  current_state = next_state;
  return pulse;
}


void moveServo(Servo &servoNum, int from, int to) {
  int newPos = -1;
  if (from < to) {
    newPos = from + pulseDelta;
    if (newPos > to) {
      newPos = to;
    }
    if (&servoNum != &servo1) {
      servoNum.writeMicroseconds((3000) - (newPos));
    } else {
      servoNum.writeMicroseconds(newPos);
    }
  } else if (from > to) {
    newPos = from - pulseDelta;
    if (newPos < to) {
      newPos = to;
    }
    if (&servoNum != &servo1) {
      servoNum.writeMicroseconds((3000) - (newPos));
    } else {
      servoNum.writeMicroseconds(newPos);
    }
  }
  
  if (newPos != -1) {
    if (&servoNum == &servo2) {
      rearPulse = newPos;
    } else if (&servoNum == &servo1){
      frontPulse = newPos;
    }
  }
}



short nextState() {
  int currentSens = analogRead(sensPin);
  int on = !digitalRead(onOffPin); // Invert because input_pullup means 1 = switch not flipped and 0 = switch flipped
  int low_drag = !digitalRead(DRSPin);

  double accel_x =  -can_data[0] / 100.0; // Minus sign here because apparently positive x should be positive acceleration
  double accel_y = abs(can_data[1]) / 100.0;
  double TPS = can_data[2];
  double wheel_speed = max(can_data[3],can_data[4]);
  double brake_pressure = can_data[5];
  double steering_angle = abs(can_data[6]);

  float scaling_factor = 0.8 - ((-50.0 + currentSens) / (755.0*2.0));
  //Serial.print("Scaling Factor: ");
  //Serial.println(scaling_factor, 4);

  //Serial.print("Accel_x: ");
  //Serial.println(accel_x);
  //Serial.print("Accel_y: ");
  //Serial.println(accel_y);
  //Serial.print("TPS: ");
  //Serial.println(TPS);
  //Serial.print("wheel_speed: ");
  //Serial.println(wheel_speed);
  //Serial.print("brake_pressure: ");
  //Serial.println(brake_pressure);
  //Serial.print("steering_angle: ");
  //Serial.println(steering_angle);

  int lowDragPack = 0;
  if (on && low_drag) {
    lowDragPack = 1;
  }
  mcp.beginPacket(0x3);
  mcp.write(lowDragPack);
  mcp.endPacket();

  switch (current_state) {
    case 1: // Medium Downforce
      if (!on) {
        next_state = 0;
      } else if (low_drag) {
        next_state = 2;
      } else if ((  brake_pressure > 30
                  || accel_x > 0.3)
                || (steering_angle > 40
                  || accel_y > 1.1)
                ) {
        next_state = 0;
      } else if (  accel_y < 0.7
                && steering_angle < 20
                && TPS > 15
              ) {
        next_state = 2;
      }
    break;

    case 2: // DRS / Low Drag
      // System disabled, should default to low drag
      if (!on) {
        next_state = 0;
      } else if (!low_drag) {
        if (   TPS < 50
          && (steering_angle > 40
              || accel_y > 1.1
            || ( brake_pressure > 30
              || accel_x > 0.3
              )
            )
          ) {
          next_state = 0;
        } else if (  wheel_speed > 15
                  && ( accel_y > 0.7
                    || steering_angle > 20
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
        } else if (  TPS > 50
                  && steering_angle < 30
                  && accel_y < 0.7
                  && brake_pressure < 30) {
          next_state = 2;
        } else if ( wheel_speed > 15 
                  && ( accel_y < 1.1
                    && steering_angle < 30
                  )
                  && (brake_pressure < 50 
                    && accel_x < 0.4)) {
          next_state = 1;
        }
      }
    break;
  }
  return(next_state);
}

void loop() {
  mcp.beginPacket(0x2);
  mcp.write(1);
  //mcp.endPacket();
  bool success = mcp.endPacket();
  if (!success) {
    Serial.println("CAN transmit failed!");
  }

  // try to parse packet
  int packetSize = mcp.parsePacket();
  
  unsigned long currentTime = millis();
  if (attached && ((currentTime - lastAttachTime) > 500)) {
    servo1.detach();
    servo2.detach();
    servo3.detach();
    //Serial.println("DETACHED");
    attached = false;
  }


  if (packetSize) {
    // received a packet
    //Serial.print("Received ");

    //if (mcp.packetExtended()) {
      //Serial.print("extended ");
    //}

    //if (mcp.packetRtr()) {
      // Remote transmission request, packet contains no data
      //Serial.print("RTR ");
    //}

    //Serial.print("packet with id 0x");
    //Serial.print(mcp.packetId(), HEX);

    if (mcp.packetRtr()) {
      Serial.print(" and requested length ");
      Serial.println(mcp.packetDlc());
    } else {
      //Serial.print(" and length ");
      //Serial.println(packetSize);
      
      int i = 0;
      // only print packet data for non-RTR packets
      // This while loop extracts all of the CAN data and puts it into the data array.
      while (mcp.available()) {
        can_data[i] = (double)mcp.read();
        //Serial.print(can_data[i]);
        i++;
      }
    }

    // At this point we have read the current CAN packet and can begin processing
    nextState(); // Calculates next state
    //unsigned long currentTime = millis();
    //if (currentTime - lastTime >= stepDelay) {
      int pulseTarget = updateState(); // Updates the current state and addresses the servos if the state changed.
      int rearPulseTarget = maxPulseR;
      switch (current_state) {
        case 1:
          rearPulseTarget = midPulseR;
          break;
        case 2:
          rearPulseTarget = minPulseR;
          break;
        default:
          break;
      }

      if (pulseTarget != frontPulse) {
        servo1.attach(servo1Pin);
        servo3.attach(servo3Pin);
        if (pulseTarget == minPulse) {
          int lPulseTarget = pulseTarget + 175; // Manual offset for FL
          moveServo(servo3, frontPulse, lPulseTarget);
        } else {
          moveServo(servo3, frontPulse, pulseTarget);
        }
        moveServo(servo1, frontPulse, pulseTarget);
      }

      if (rearPulseTarget != rearPulse) {
        servo2.attach(servo2Pin);
        moveServo(servo2, rearPulse, rearPulseTarget);
        attached = true;
        lastAttachTime = millis();
        //Serial.println("ATTACHED");
      }
    
      //lastTime = currentTime;
    //}
    //Serial.print("Current State: ");
    //Serial.println(current_state);
    //Serial.print("Front State: ");
    //Serial.println(frontPulse);
  }
}