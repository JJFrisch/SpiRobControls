const int forwardPin = 8;
const int backwardPin = 12;
const int delayTime = 2000;


void stopSpin(){
  digitalWrite(forwardPin, LOW);
  digitalWrite(backwardPin, LOW);
  delay(delayTime);
}

void forward(){
  digitalWrite(forwardPin, HIGH);
  digitalWrite(backwardPin, LOW);
  delay(delayTime);
}

void backward(){
  digitalWrite(forwardPin, LOW);
  digitalWrite(backwardPin, HIGH);
  delay(delayTime);
}

void setup() {
  // put your setup code here, to run once:
  pinMode(forwardPin,OUTPUT);
  pinMode(backwardPin,OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:

  stopSpin();
  forward();
  stopSpin();
  backward();
  
}
