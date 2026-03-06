# Sistema di Monitoraggio per l'Efficienza Energetica

Il sistema acquisisce dati ambientali (temperatura e umidita') tramite Arduino
e li visualizza in tempo reale su un'applicazione desktop Python.

---

## Hardware utilizzato

- Arduino Uno
- Sensore DHT11 (temperatura e umidita')
- LCD 16x2 (interfaccia parallela)
- LED rosso, verde, blu
- Buzzer
- Potenziometro

---

## Funzionamento generale

Arduino legge periodicamente i dati dal sensore DHT11 ogni 10 secondi
e li invia al computer tramite porta seriale in formato CSV.
L'applicazione Python riceve i dati, li elabora e li mostra in una
finestra grafica aggiornata in tempo reale.

### Logica di controllo (Arduino)

La temperatura letta dal sensore viene confrontata con la temperatura
desiderata, impostata dall'utente tramite potenziometro (range 10-30 gradi).

In base al confronto il sistema attiva:
- riscaldamento, se la temperatura attuale e' inferiore a quella desiderata
- apertura finestre, se la temperatura attuale e' superiore a quella desiderata

I LED segnalano lo stato ambientale in base a soglie fisse:
- LED rosso: temperatura sopra 25 gradi (surriscaldamento)
- LED verde: temperatura nella zona di comfort (15-25 gradi)
- LED blu: temperatura sotto 15 gradi

Il buzzer emette un segnale sonoro quando la temperatura supera le soglie.

Per l'umidita' il sistema gestisce:
- deumidificatore, se l'umidita' supera il 60%
- umidificatore, se l'umidita' scende sotto il 40%

Il display LCD mostra in rotazione quattro schermate:
- stato della temperatura
- azione consigliata per la temperatura
- stato dell'umidita'
- azione consigliata per l'umidita'

### Formato dati seriale

I dati vengono inviati su una riga terminata da newline, con 9 campi separati
da virgola:

temperatura, temp_scelta, umidita, stato_temp, riscaldamento, finestre, stato_um, deumidificatore, umidificatore

Esempio:

23.5,20,58.0,COMFORT,OFF,ON,OK,OFF,OFF

---

## Applicazione Python

L'applicazione e' sviluppata con Dear PyGui e si basa sul paradigma
produttore-consumatore implementato con due thread e una coda condivisa.

### Interfaccia grafica

- Pannello temperatura: valore attuale, temperatura scelta e suggerimento
- Pannello umidita': valore attuale e suggerimento
- Indicatori ON/OFF per riscaldamento, finestre, deumidificatore, umidificatore
- Grafico temperatura e umidita' nel tempo con linee di soglia

---

## Strategie di sincronizzazione

### Paradigma produttore-consumatore

Il sistema e' strutturato attorno al classico problema del produttore-consumatore:

- Arduino e' il produttore: genera dati a intervalli regolari e li trasmette
- Python e' il consumatore: riceve i dati, li elabora e li mostra

### Thread e queue

All'interno dell'applicazione Python sono presenti due thread.

Il thread produttore (thread_seriale) legge le righe dalla porta seriale e le
inserisce in una queue. La lettura e' bloccante: il thread aspetta finche' non
arriva una riga completa terminata da newline. Questo rispecchia esattamente il
lato Arduino, che invia i dati solo quando ha completato una misurazione.

Il thread consumatore (thread_consumatore) preleva le righe dalla queue,
effettua il parsing, aggiorna le variabili globali e salva i dati nel file CSV
ogni 10 secondi.

La queue di Python (queue.Queue) e' thread-safe per design: gestisce
internamente la sincronizzazione, quindi produttore e consumatore possono
operare contemporaneamente senza conflitti.

Il thread principale esegue la GUI. Dear PyGui deve essere eseguito sul thread
principale. Ad ogni frame chiama aggiorna_gui(), che legge le variabili globali
e aggiorna la finestra.

### Lock

Le variabili globali condivise tra il thread consumatore e il thread GUI sono
protette da un threading.Lock(). Il lock viene acquisito per il tempo minimo
necessario: il consumatore lo acquisisce per aggiornare le variabili, la GUI lo
acquisisce per copiarle in variabili locali e lo rilascia subito prima di
aggiornare la finestra. In questo modo i due thread non si bloccano a vicenda
per tempi lunghi.

### Delay-less coding (Arduino)

Arduino non utilizza la funzione delay() nel loop principale, che bloccherebbe
l'esecuzione e renderebbe il sistema non reattivo. Al suo posto viene usata
millis() per misurare il tempo trascorso e decidere quando eseguire le
operazioni periodiche (lettura sensore ogni 10 secondi, aggiornamento LCD ogni
2.5 secondi). Questo permette al loop di girare continuamente e rispondere in
ogni momento agli input del potenziometro.

### Buffer seriale

La comunicazione seriale usa un protocollo a pacchetti: ogni riga inviata da
Arduino termina con un carattere newline (\n). Python usa readline() che aspetta
esattamente quel carattere prima di restituire la riga completa. Questo
garantisce che i dati non vengano mai letti a meta', sincronizzando
implicitamente i due sistemi anche se girano a velocita' diverse.

---
