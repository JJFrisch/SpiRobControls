#include <AccelStepper.h>
#include <MultiStepper.h>

// Define pins for 3 stepper motors
#define motor1_pin1 8
#define motor1_pin2 9
#define motor1_pin3 10
#define motor1_pin4 11

#define motor2_pin1 4
#define motor2_pin2 5
#define motor2_pin3 6
#define motor2_pin4 7

#define motor3_pin1 2
#define motor3_pin2 3
#define motor3_pin3 A0
#define motor3_pin4 A1

// max steps for each motor
const long M1_MAX_STEPS = 3000;
const long M2_MAX_STEPS = 2500;
const long M3_MAX_STEPS = 2000;

#define IR_RECEIVE_PIN 12

AccelStepper stepper1(AccelStepper::FULL4WIRE, motor1_pin1, motor1_pin3, motor1_pin2, motor1_pin4);
AccelStepper stepper2(AccelStepper::FULL4WIRE, motor2_pin1, motor2_pin3, motor2_pin2, motor2_pin4);
AccelStepper stepper3(AccelStepper::FULL4WIRE, motor3_pin1, motor3_pin3, motor3_pin2, motor3_pin4);

MultiStepper steppers;

IRrecv irrecv(IR_RECEIVE_PIN);
decode_results results;

long positions[3]; // target positions for 3 motors

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);

  // Add steppers to MultiStepper controller
  steppers.addStepper(stepper1);
  steppers.addStepper(stepper2);
  steppers.addStepper(stepper3);

  // Set speed and acceleration for each motor
  stepper1.setMaxSpeed(500);
  stepper1.setAcceleration(200);

  stepper2.setMaxSpeed(500);
  stepper2.setAcceleration(200);

  stepper3.setMaxSpeed(500);
  stepper3.setAcceleration(200);

  // Initialize IR receiver
  irrecv.enableIRIn();

  Serial.println("Enter commands like:");
  Serial.println("M1:100 M2:-50 M3:200");
}

bool isMoveValid(int motorIndex, long targetPosition) {
  // Check position bounds
  if (targetPosition < 0) {
    // Check limit switch for zero position
    switch (motorIndex) {
      case 0:
        if (digitalRead(M1_LIMIT_PIN) == LOW) { // pressed
          Serial.println("M1 limit switch triggered - move blocked");
          return false;
        }
        break;
      case 1:
        if (digitalRead(M2_LIMIT_PIN) == LOW) {
          Serial.println("M2 limit switch triggered - move blocked");
          return false;
        }
        break;
      case 2:
        if (digitalRead(M3_LIMIT_PIN) == LOW) {
          Serial.println("M3 limit switch triggered - move blocked");
          return false;
        }
        break;
    }
  }

  switch (motorIndex) {
    case 0:
      if (targetPosition > M1_MAX_STEPS) return false;
      break;
    case 1:
      if (targetPosition > M2_MAX_STEPS) return false;
      break;
    case 2:
      if (targetPosition > M3_MAX_STEPS) return false;
      break;
  }

  return true;
}


void loop() {
  // Check serial input for commands
  if (stringComplete) {
    parseSerialCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Check IR remote input
  if (irrecv.decode(&results)) {
    handleIRCommand(results.value);
    irrecv.resume();
  }

  // Move motors toward target positions
  steppers.run();
}

void parseSerialCommand(String cmd) {
  positions[0] = stepper1.currentPosition();
  positions[1] = stepper2.currentPosition();
  positions[2] = stepper3.currentPosition();

  int idx;

  idx = cmd.indexOf("M1:");
  if (idx != -1) {
    int end = cmd.indexOf(' ', idx);
    String val = cmd.substring(idx + 3, end == -1 ? cmd.length() : end);
    long newPos = positions[0] + val.toInt();
    if (isMoveValid(0, newPos)) {
      positions[0] = newPos;
    } else {
      Serial.println("Move for M1 blocked by limit or bounds.");
    }
  }

  idx = cmd.indexOf("M2:");
  if (idx != -1) {
    int end = cmd.indexOf(' ', idx);
    String val = cmd.substring(idx + 3, end == -1 ? cmd.length() : end);
    long newPos = positions[1] + val.toInt();
    if (isMoveValid(1, newPos)) {
      positions[1] = newPos;
    } else {
      Serial.println("Move for M2 blocked by limit or bounds.");
    }
  }

  idx = cmd.indexOf("M3:");
  if (idx != -1) {
    int end = cmd.indexOf(' ', idx);
    String val = cmd.substring(idx + 3, end == -1 ? cmd.length() : end);
    long newPos = positions[2] + val.toInt();
    if (isMoveValid(2, newPos)) {
      positions[2] = newPos;
    } else {
      Serial.println("Move for M3 blocked by limit or bounds.");
    }
  }

  steppers.moveTo(positions);

  Serial.print("Moving to positions: M1=");
  Serial.print(positions[0]);
  Serial.print(" M2=");
  Serial.print(positions[1]);
  Serial.print(" M3=");
  Serial.println(positions[2]);
}

void handleIRCommand(unsigned long command) {
  positions[0] = stepper1.currentPosition();
  positions[1] = stepper2.currentPosition();
  positions[2] = stepper3.currentPosition();

  switch (command) {
    case 0xC: // Button 1: Move motor 1 +100 steps
      if (isMoveValid(0, positions[0] + 100)) positions[0] += 100;
      else Serial.println("M1 move blocked by limits.");
      break;

    case 0x18: // Button 2: Move motor 1 -100 steps
      if (isMoveValid(0, positions[0] - 100)) positions[0] -= 100;
      else Serial.println("M1 move blocked by limits.");
      break;

    case 0x46: // VOL+ : Move all motors +200 steps
      for (int i = 0; i < 3; i++) {
        if (!isMoveValid(i, positions[i] + 200)) {
          Serial.print("Motor ");
          Serial.print(i+1);
          Serial.println(" move blocked by limits.");
          return;
        }
      }
      for (int i = 0; i < 3; i++) positions[i] += 200;
      break;

    case 0x15: // VOL- : Move all motors -200 steps
      for (int i = 0; i < 3; i++) {
        if (!isMoveValid(i, positions[i] - 200)) {
          Serial.print("Motor ");
          Serial.print(i+1);
          Serial.println(" move blocked by limits.");
          return;
        }
      }
      for (int i = 0; i < 3; i++) positions[i] -= 200;
      break;

    case 0x47: // Return all motors to zero
      positions[0] = 0;
      positions[1] = 0;
      positions[2] = 0;
      break;

    default:
      Serial.println("Unknown IR command.");
      return;
  }

  steppers.moveTo(positions);
  Serial.println("Motors moving to new positions.");
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}
