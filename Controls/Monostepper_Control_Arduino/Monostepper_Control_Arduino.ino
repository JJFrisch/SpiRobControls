
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
