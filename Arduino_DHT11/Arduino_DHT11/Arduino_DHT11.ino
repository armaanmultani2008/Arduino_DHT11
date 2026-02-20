const int LED_ROSSO = 2;
const int LED_VERDE = 4;

int intervallo = 10000;
int ultimoTempo = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_ROSSO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  dht.begin();
}

void loop() {
  
}
