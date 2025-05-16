#include <IRremote.hpp>
#include "Stepper.h"

#define STEPS 60                 // steps per revolution for internal gear
#define IR_RECEIVE_PIN 12
#define FULL_REV_STEPS 2038     // full revolution of the stepper motor
#define SPOOL_DIAMETER_MM 25.0
#define PI 3.14159265

Stepper small_stepper(STEPS, 8, 10, 9, 11);
int currentPosition = 0; // in steps
float stepsPerCm = FULL_REV_STEPS / (PI * SPOOL_DIAMETER_MM / 10.0); // ≈ 260 steps/cm

int steps = FULL_REV_STEPS;

const float MAX_CM = 50.0;
const int MAX_STEPS = stepsPerCm * MAX_CM;

String inputString = "";
bool stringComplete = false;

unsigned long lastActivityTime = 0;
const unsigned long RETRACT_TIMEOUT = 30000; // 30 seconds
bool retracted = false;

void setup() {
  Serial.begin(9600);
  IrReceiver.begin(IR_RECEIVE_PIN); // Initialize the global receiver object
  small_stepper.setSpeed(300);

  Serial.println("Enter a distance in cm to move string (e.g. 10 or -5):");
}

void loop() {
  // Handle Serial input
  if (stringComplete) {
    float cm = inputString.toFloat();
    int steps = stepsPerCm * cm;

    if (isMoveWithinLimits(steps)) {
      small_stepper.step(steps);
      currentPosition += steps;
      Serial.print("Moved ");
      Serial.print(cm);
      Serial.println(" cm");
    } else {
      Serial.println("❌ Move would exceed limits. Ignored.");
    }

    Serial.print("Current position: ");
    Serial.print(currentPosition / stepsPerCm);
    Serial.println(" cm");

    inputString = "";
    stringComplete = false;
  }

  // Handle IR input
  if (IrReceiver.decode()) {
    unsigned long command = IrReceiver.decodedIRData.command;
    Serial.print("Command: 0x");
    Serial.println(command, HEX);

    switch (command) {
      case 0xC: // Button 1
        steps = 50;
        if (isMoveWithinLimits(steps)) {
          small_stepper.step(50);
          currentPosition += steps;
        }
        break;

      case 0x18: // Button 2
        steps = 50;
        if (isMoveWithinLimits(-steps)) {
          small_stepper.step(-50);
          currentPosition -= steps;
        }
        break;

      case 0x46: // VOL+
        steps = 900;
        if (isMoveWithinLimits(steps)) {
          small_stepper.setSpeed(500);
          small_stepper.step(steps);
          currentPosition += steps;
        }
        break;

      case 0x15: // VOL-
        steps = 900;
        if (isMoveWithinLimits(-steps)) {
          small_stepper.setSpeed(500);
          small_stepper.step(-steps);
          currentPosition -= steps;
        }
        break;


      case 0x43: //  – Pull 10 cm
        {
          steps = stepsPerCm * 10; // 10 cm
          if (isMoveWithinLimits(steps)) {
            small_stepper.step(steps);
            currentPosition += steps;
          }
        }
        break;

      case 0x44: //  – Pull 10 cm
        {
          steps = stepsPerCm * 10; // 10 cm
          if (isMoveWithinLimits(steps)) {
            small_stepper.step(-steps);
            currentPosition -= steps;
          }
        }
        break;

      case 0x47: //  – Return to 0
        small_stepper.step(-currentPosition);
        currentPosition = 0;
        break;

      default:
        Serial.println("Unrecognized command.");
        break;
    }

    IrReceiver.resume(); // Receive the next command
  }

  // Auto-retract after inactivity
  if (!retracted && millis() - lastActivityTime > RETRACT_TIMEOUT && currentPosition != 0) {
    Serial.println("Auto-retracting...");
    small_stepper.step(-currentPosition);
    currentPosition = 0;
    retracted = true;
  }
}

// Length check
bool isMoveWithinLimits(int stepDelta) {
  int newPosition = currentPosition + stepDelta;
  bool ans = newPosition >= 0 && newPosition <= MAX_STEPS;
  if (ans){
    lastActivityTime = millis();
    retracted = false;
  }
  return ans;
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
