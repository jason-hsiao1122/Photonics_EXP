#define X_DIR 5
#define X_STP 2
#define en 8
int receivedChar;
int steps = 10;
void setup() {
Serial.begin(115200);
Serial.setTimeout(1);
pinMode(X_DIR, OUTPUT);
pinMode(X_STP, OUTPUT);
pinMode(en, OUTPUT);
digitalWrite(en, HIGH); }

void loop() {
while (Serial.available() > 0) {
receivedChar = Serial.read();
if (receivedChar == '1') {
digitalWrite(en, LOW);
digitalWrite(X_DIR, HIGH);
Serial.println("前進"); }
if (receivedChar == '2') {
digitalWrite(en, LOW);
digitalWrite(X_DIR, LOW);
Serial.println("後退"); }
if (receivedChar == '3') {
digitalWrite(en, HIGH);
Serial.println("停止"); } }
for (int i = 0; i < steps; i++) {
digitalWrite(X_STP, HIGH);
delayMicroseconds(200);
digitalWrite(X_STP, LOW);
delayMicroseconds(200); 
}
}