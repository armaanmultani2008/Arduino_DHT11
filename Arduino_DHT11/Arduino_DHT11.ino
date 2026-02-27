#include "DHT.h"
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const int LED_ROSSO = 4;
const int LED_BLU = 6;
const int LED_VERDE = 8;
const int BUZZER = 12;

int intervallo = 2000;
int ultimoTempo = 0;

int min_caldo = 20;
int max_freddo = 10;

void setup() {
  Serial.begin(9600);
  pinMode(LED_ROSSO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_BLU, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  dht.begin();
}

void loop() {
  if(millis() - ultimoTempo >= intervallo) {

    ultimoTempo = millis();

    float t = dht.readTemperature();

    if(!isnan(t)) {

      digitalWrite(LED_ROSSO, LOW);
      digitalWrite(LED_VERDE, LOW);
      digitalWrite(LED_BLU, LOW);

      if(t >= min_caldo){
        digitalWrite(LED_ROSSO, HIGH);
        tone(BUZZER, 1000, 1000);

        Serial.print("Temperatura alta! Temp: ");
        Serial.println(t, 2);
      }

      else if(t <= max_freddo){
        digitalWrite(LED_BLU, HIGH);
        tone(BUZZER, 1000, 500);

        Serial.print("Temperatura bassa! Temp: ");
        Serial.println(t, 2);
      }

      else{
        digitalWrite(LED_VERDE, HIGH);

        Serial.print("Temperatura piacevole. Temp: ");
        Serial.println(t, 2);
      }
    } else {
      Serial.println("Errore nella lettura dal sensore DHT");
    }
  }
}
