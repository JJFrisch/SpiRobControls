











#include <Stepper.h>

#define StepsPerRevolution 2038

#define max_length 3 // in inches
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

  move(300, 12); // steps, speed
  delay(1000);
}


  














































// Define stepper motor connections and steps per revolution:
//#define DIR_PIN 2
//#define STEP_PIN 3
//#define STEPS_PER_REVOLUTION 200
//
//#define max_length 3 // in inches
//#define radius_of_spin 0.2 // in inches
//double circumference = 2 * 3.14159265359 * radius_of_spin;
//
//int steps_taken = 0;
//
//void setup() {
//  // Declare pins as output:
//  Serial.begin(12345);
//  pinMode(STEP_PIN, OUTPUT);
//  pinMode(DIR_PIN, OUTPUT);
//}
//
//void Clockwise(int speed, int steps){ // speed in ms delay between steps
//  Serial.println("Spinning clockwise: " + String(speed));
//  digitalWrite(DIR_PIN, HIGH);
//
//  // Spin the stepper motor for step number of steps
//  for (int i = 0; i < steps; i++) {
//    if (get_length_pulled() > max_length){ return; } // Check movement is available
//    else{
//        // These four lines result in 1 step:
//        digitalWrite(STEP_PIN, HIGH);
//        delayMicroseconds(speed);
//        digitalWrite(STEP_PIN, LOW);
//        delayMicroseconds(speed);
//        steps_taken ++;
//    }
//  }
//}
//
//void CounterClockwise(int speed, int steps){
//  Serial.println("Spinning counterclockwise: " + String(speed));
//  digitalWrite(DIR_PIN, LOW);
//
//  for (int i = 0; i < steps; i++) {
//    if (abs(get_length_pulled()) > max_length){ return; } // Check movement is available
//    else{
//      digitalWrite(STEP_PIN, HIGH);
//      delayMicroseconds(speed);
//      digitalWrite(STEP_PIN, LOW);
//      delayMicroseconds(speed);
//      steps_taken --;
//    }
//  }
//}
//
//double get_length_pulled (){
//  return (steps_taken / STEPS_PER_REVOLUTION) * circumference;
//}
//
//void print_length_pulled(){
//  Serial.println(String(get_length_pulled()) + " inches pulled.");
//}
//
//void loop() {
//
//  Clockwise(2000, 1);
//  // delay(1000);
//  // Clockwise(1000, 40);
//  // delay(1000);
//
//  // print_length_pulled();
//
//  // CounterClockwise(500, 300);
//  // delay(1000);
//  // CounterClockwise(1000, 200);
//  // delay(1000);
//
//  // print_length_pulled();
//
//  // CounterClockwise(1000, 1000);
//  // delay(1000);
//
//  print_length_pulled();
//
//}
