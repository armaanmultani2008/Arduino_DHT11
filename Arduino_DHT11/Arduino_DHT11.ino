#include "DHT.h"
#include <LiquidCrystal.h>

#define DHTPIN 2
#define DHTTYPE DHT11

const int rs = 11, en = 12, d4 = 7, d5 = 6, d6 = 5, d7 = 4;

const int LED_ROSSO = 10;
const int LED_VERDE = 9;
const int LED_BLU = 8;
const int BUZZER = 3;
const int POTENZIOMETRO = A0;

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

const int SOGLIA_CALDA = 25;
const int SOGLIA_FREDDA = 15;
const int POT_TEMP_MIN = 15;
const int POT_TEMP_MAX = 25;
const int SOGLIA_UMIDO = 60;
const int SOGLIA_ARIDO = 40;

const unsigned long INTERVALLO_SENSORE = 10000UL;
const unsigned long INTERVALLO_LCD = 2500UL;
unsigned long ultimoTempo = 0;
unsigned long ultimoTempoLCD = 0;

float temperaturaAttuale = NAN;
float umiditaAttuale = NAN;
int   temperaturaScelta  = 20;

bool riscaldamento = false;
bool apri_finestre = false;
bool deumidificatore = false;
bool umidificatore = false;
bool allarme = true;

int paginaLCD = 0;

void setup() {
  Serial.begin(9600);

  pinMode(LED_ROSSO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_BLU, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  dht.begin();
  lcd.begin(16, 2);
  lcd.print("Avvio sistema...");
  delay(1000);
  lcd.clear();
}

int leggiPotenziometro() {
  return map(analogRead(POTENZIOMETRO), 0, 1023, POT_TEMP_MIN, POT_TEMP_MAX);
}

void aggiornaLED_Buzzer(float t) {
  digitalWrite(LED_ROSSO, LOW);
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_BLU, LOW);

  if (t >= SOGLIA_CALDA) {
    digitalWrite(LED_ROSSO, HIGH);
    if (allarme) tone(BUZZER, 1000, 1000);
  } else if (t <= SOGLIA_FREDDA) {
    digitalWrite(LED_BLU, HIGH);
    if (allarme) tone(BUZZER, 800, 500);
  } else {
    digitalWrite(LED_VERDE, HIGH);
    noTone(BUZZER);
    allarme = true;
  }
}

void aggiornaStatoTemperatura(float t) {
  if (t < temperaturaScelta) {
    riscaldamento = true;
    apri_finestre = false;
  } else if (t > temperaturaScelta) {
    riscaldamento = false;
    apri_finestre = true;
  } else {
    riscaldamento = false;
    apri_finestre = false;
  }
}

void aggiornaStatoUmidita(float h) {
  if (h > SOGLIA_UMIDO) {
    deumidificatore = true;
    umidificatore = false;
  } else if (h < SOGLIA_ARIDO) {
    deumidificatore = false;
    umidificatore = true;
  } else {
    deumidificatore = false;
    umidificatore = false;
  }
}

void stampaRiga(int riga, String testo) {
  while (testo.length() < 16) testo += " ";
  lcd.setCursor(0, riga);
  lcd.print(testo.substring(0, 16));
}

void aggiornaLCD() {
  if (isnan(temperaturaAttuale) || isnan(umiditaAttuale)) {
    stampaRiga(0, "Errore sensore!");
    stampaRiga(1, "");
    return;
  }

  stampaRiga(0, "A:" + String(temperaturaAttuale, 1) + "C S:" + String(temperaturaScelta) + "C");

  switch (paginaLCD) {

    case 0:
      if (temperaturaAttuale >= SOGLIA_CALDA)  stampaRiga(1, "Amb. caldo!");
      else if (temperaturaAttuale <= SOGLIA_FREDDA) stampaRiga(1, "Amb. freddo!");
      else stampaRiga(1, "Temp. piacevole");
      break;

    case 1:
      if (temperaturaAttuale >= SOGLIA_CALDA) {
        if(apri_finestre) stampaRiga(1, "Finestre aperte");
        else stampaRiga(1, "Apri finestre!");
      } else if (temperaturaAttuale <= SOGLIA_FREDDA) {
        if(riscaldamento) stampaRiga(1, "Risc. acceso")
      } else {
        if (riscaldamento) stampaRiga(1, "Risc. acceso");
        else if (apri_finestre) stampaRiga(1, "Finestre aperte");
        else stampaRiga(1, "Sistema OK");
      }
      break;

    case 2:
      if  (umiditaAttuale > SOGLIA_UMIDO) stampaRiga(1, "Aria umida!");
      else if (umiditaAttuale < SOGLIA_ARIDO) stampaRiga(1, "Aria secca!");
      else stampaRiga(1, "Umidita' ok");
      break;

    case 3:
      if (umiditaAttuale > SOGLIA_UMIDO) {
        if(deumidificatore) stampaRiga(1, "Deumidif. acceso");
        else stampaRiga(1, "Accendi deumidif.!")
      } else if (umiditaAttuale < SOGLIA_ARIDO) {
        if(umidificatore) stampaRiga(1, "Umidif. acceso")
        else stampaRiga(1, "Accendi umidif.!")
      } else {
        stampaRiga(1, "Umid: " + String(umiditaAttuale, 1) + "%");
      }
      break;
  }

  paginaLCD = (paginaLCD + 1) % 4; 
}

void stampaSeriale(float t, float h) {
  String statoTemp;
  if (t >= SOGLIA_CALDA) statoTemp = "CALDO";
  else if (t <= SOGLIA_FREDDA) statoTemp = "FREDDO";
  else statoTemp = "COMFORT";

  String statoUm;
  if (h > SOGLIA_UMIDO) statoUm = "UMIDO";
  else if (h < SOGLIA_ARIDO) statoUm = "SECCO";
  else statoUm = "OK";

  Serial.print(t, 1);                             
  Serial.print(",");
  Serial.print(h, 1);                             
  Serial.print(",");
  Serial.print(statoTemp);                        
  Serial.print(",");
  if(riscaldamento) Serial.print("ON");
  else Serial.print("OFF");   
  Serial.print(",");
  if(apri_finestre) Serial.print("ON");
  else Serial.print("OFF");   
  Serial.print(",");
  Serial.print(statoUm);                          
  Serial.print(",");
  if(deumidificatore) Serial.print("ON");
  else Serial.print("OFF");
  Serial.print(",");
  if(umidificatore) Serial.println("ON");
  else Serial.println("OFF");
}

void loop() {
  unsigned long adesso = millis();

  temperaturaScelta = leggiPotenziometro();

  if (adesso - ultimoTempo >= INTERVALLO_SENSORE) {
    ultimoTempo = adesso;

    float t = dht.readTemperature();
    float h = dht.readHumidity();

    if (!isnan(t) && !isnan(h)) {
      temperaturaAttuale = t;
      umiditaAttuale     = h;
      aggiornaLED_Buzzer(t);
      aggiornaStatoTemperatura(t);
      aggiornaStatoUmidita(h);
      stampaSeriale(t, h);
    } else {
      Serial.println("ERRORE,0,0,0,0,0,0,0");
    }
  }

  if (adesso - ultimoTempoLCD >= INTERVALLO_LCD) {
    ultimoTempoLCD = adesso;
    aggiornaLCD();
  }
}