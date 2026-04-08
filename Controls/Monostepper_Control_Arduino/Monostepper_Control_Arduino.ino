
/**
 * Monostepper_Control_Arduino.ino
 *
 * Basic single-motor control for the 28BYJ-48 unipolar stepper motor using
 * the built-in Arduino Stepper library. Tracks cumulative wire displacement
 * in inches and enforces a configurable max-length safety limit.
 *
 * Motor wiring (28BYJ-48 + ULN2003 driver board):
 *   IN1 -> Arduino pin  8
 *   IN2 -> Arduino pin  9
 *   IN3 -> Arduino pin 10
 *   IN4 -> Arduino pin 11
 *
 * Key parameters:
 *   StepsPerRevolution  2038    (28BYJ-48 with gear reduction)
 *   max_length          30 in   (safety cutoff: motor stops if cumulative wire
 *                                displacement exceeds this value)
 *   radius_of_spin      0.2 in  (spool radius used to convert steps -> inches)
 */

#include <Stepper.h>

#define StepsPerRevolution 2038

#define max_length 30 // in inches
#define radius_of_spin 0.2 // in inches
double circumference = 2 * 3.14159265359 * radius_of_spin;

double steps_taken = 0;
int rpm = 5;

Stepper mainStepper (StepsPerRevolution, 8, 10, 9, 11);

void setup(){
  Serial.begin(9600);
  mainStepper.setSpeed(rpm);
}

void move(int steps, int velocity=10){
  Serial.println("Steps, velocity: " + String(steps) + " " + String(velocity));
//  print_length_pulled();
  mainStepper.setSpeed(velocity);
  int dir = steps/abs(steps);
  for (int i=0; i<steps; i++){
    if (get_length_pulled() > max_length){ 
      Serial.println(String(steps_taken) + " steps taken.");
      print_length_pulled();
      return; 
    }

    mainStepper.step(1);
    steps_taken += dir;
  }
  return;
}

double get_length_pulled (){
  return (steps_taken / StepsPerRevolution) * circumference;
}

double get_length_pulled (double steps){
  return ((steps_taken+steps) / StepsPerRevolution) * circumference;
}

void print_length_pulled(){
  Serial.println(String(get_length_pulled()) + " inches pulled.");
}

void loop(){

  move(StepsPerRevolution); // steps, speed=10
  delay(1000);

  move(3000, 12); // steps, speed
  delay(1000);
}
