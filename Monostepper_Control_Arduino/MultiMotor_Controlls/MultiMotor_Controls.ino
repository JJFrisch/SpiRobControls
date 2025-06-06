#include <AccelStepper.h>
#include <MultiStepper.h>
#include <IRremote.hpp>


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
const long MAX_STEPS = 5000;
const long M1_MAX_STEPS = 5000;
const long M2_MAX_STEPS = 5000;
const long M3_MAX_STEPS = 5000;

#define IR_RECEIVE_PIN 12

AccelStepper stepper1(AccelStepper::FULL4WIRE, motor1_pin1, motor1_pin3, motor1_pin2, motor1_pin4);
AccelStepper stepper2(AccelStepper::FULL4WIRE, motor2_pin1, motor2_pin3, motor2_pin2, motor2_pin4);
AccelStepper stepper3(AccelStepper::FULL4WIRE, motor3_pin1, motor3_pin3, motor3_pin2, motor3_pin4);

MultiStepper steppers;


long positions[3]; // target positions for 3 motors

String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(9600);
  IrReceiver.begin(IR_RECEIVE_PIN); // Initialize the global receiver object

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
  IrReceiver.enableIRIn();

  Serial.println("Enter commands like:");
  Serial.println("M1:100 M2:-50 M3:200");
}

bool isMoveValid(int motorIndex, long targetPosition) {  
  switch (motorIndex) {
    case 0:
      if (targetPosition > M1_MAX_STEPS || targetPosition < -M1_MAX_STEPS) return false;
      break;
    case 1:
      if (targetPosition > M2_MAX_STEPS || targetPosition < -M2_MAX_STEPS) return false;
      break;
    case 2:
      if (targetPosition > M3_MAX_STEPS || targetPosition < -M3_MAX_STEPS) return false;
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
  if (IrReceiver.decode()) {
    handleIRCommand(IrReceiver.decodedIRData.command);
    IrReceiver.resume();
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
    int end1 = cmd.indexOf(' ', idx);
    String val = cmd.substring(idx + 3, end1 == -1 ? cmd.length() : end1);
    long newPos = positions[0] + val.toInt();
    if (isMoveValid(0, newPos)) {
      positions[0] = newPos;
    } else {
      Serial.println("Move for M1 blocked by limit or bounds.");
    }
  }


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

  double relax_ratio = 0.2;
  double one_click_steps = 100;
  double relax_steps = one_click_steps * relax_ratio;

  switch (command) {
    case 0xC: // Button 1: Move motor 1 +100 steps
      if (isMoveValid(0, positions[0] + one_click_steps)) {positions[0] += one_click_steps; positions[1] -= relax_steps;}
      else Serial.println("M1 move blocked by limits.");
      break;

    case 0x18: // Button 2: Move motor 1 -100 steps
      if (isMoveValid(0, positions[0] - one_click_steps)) {positions[0] -= one_click_steps; positions[1] += relax_steps;}
      else Serial.println("M1 move blocked by limits.");
      break;

    case 0x5E: // Button 3: Move motor 2 +100 steps
      if (isMoveValid(1, positions[1] + one_click_steps)) {positions[1] += one_click_steps; positions[0] -= relax_steps;}
      else Serial.println("M2 move blocked by limits.");
      break;

    case 0x8: // Button 4: Move motor 2 -100 steps
      if (isMoveValid(1, positions[1] - one_click_steps)) {positions[1] -= one_click_steps; positions[0] += relax_steps;}
      else Serial.println("M2 move blocked by limits.");
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

    case 0x4A: // Return all motors to zero
      positions[0] = M1_MAX_STEPS;
      positions[1] = M1_MAX_STEPS * relax_ratio;
      positions[2] = 0;
      Serial.println("Motors returning to 0.");
      break;

    case 0x47: // Return all motors to zero
      positions[0] = 0;
      positions[1] = 0;
      positions[2] = 0;
      Serial.println("Motors returning to 0.");
      break;

    default:
      if (command != 0 && command != 40){
        Serial.println("Unknown IR command.");
        Serial.println(command, HEX);
      }
      return;
  }


  // For the MoveTO the passive motors need to relax some of the wire
  steppers.moveTo(positions);
  Serial.print("Moving to positions: M1=");
  Serial.print(positions[0]);
  Serial.print(" M2=");
  Serial.print(positions[1]);
  Serial.print(" M3=");
  Serial.println(positions[2]);
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
