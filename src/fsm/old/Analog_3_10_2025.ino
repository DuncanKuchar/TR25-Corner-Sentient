void setup() {
  Serial.begin(115200);  // Start serial communication
  
  pinMode(A1, INPUT_PULLDOWN);
  pinMode(A2, INPUT_PULLDOWN);
  pinMode(A3, INPUT_PULLDOWN);
}

void loop() {
  int switch1 = analogRead(A1); // AA sensetivity controller
  int switch2 = digitalRead(A2); // DRS mode (1), non DRS (0)
  int switch3 = digitalRead(A3); // System ON (1) or System OFF (0)

  Serial.print("Switch 1: "); Serial.print(switch1);
  Serial.print(" | Switch 2: "); Serial.print(switch2);
  Serial.print(" | Switch 3: "); Serial.println(switch3);
  
  delay(500);  // Small delay to avoid spamming output
}