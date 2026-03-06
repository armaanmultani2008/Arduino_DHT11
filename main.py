import threading
import queue
import time
import csv
import os
from datetime import datetime
import serial
import dearpygui.dearpygui as dpg


# ==============================================================================
# CONFIGURAZIONE
# ==============================================================================
FILE_CSV  = "storico.csv"
MAX_PUNTI_GRAFICO = 60  

SOGLIA_CALDA = 25.0
SOGLIA_FREDDA = 15.0
SOGLIA_UMIDO = 60.0
SOGLIA_ARIDO = 40.0


# ==============================================================================
# VARIABILI GLOBALI CONDIVISE TRA I THREAD
# ==============================================================================

dati_queue = queue.Queue()

lock = threading.Lock()

temperatura = None
umidita = None
stato_temp  = "---"  
stato_um  = "---"  
riscaldamento  = "OFF"
finestre = "OFF"
deumidificatore= "OFF"
umidificatore = "OFF"

lista_temp = []
lista_hum = []
lista_tempo = []   

tempo_avvio = time.time()


# ==============================================================================
# FUNZIONE: inizializza il file CSV
# ==============================================================================
def inizializza_csv():
    if not os.path.exists(FILE_CSV):
        with open(FILE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "temperatura", "umidita",
                "stato_temp", "riscaldamento", "finestre",
                "stato_um", "deumidificatore", "umidificatore"
            ])


# ==============================================================================
# FUNZIONE: salva una riga nel CSV
# ==============================================================================
def salva_csv(dati):
    with open(FILE_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            dati["temperatura"],
            dati["umidita"],
            dati["stato_temp"],
            dati["riscaldamento"],
            dati["finestre"],
            dati["stato_um"],
            dati["deumidificatore"],
            dati["umidificatore"]
        ])


# ==============================================================================
# FUNZIONE: carica lo storico CSV all'avvio per pre-riempire il grafico
# ==============================================================================
def carica_storico():
    if not os.path.exists(FILE_CSV):
        return

    with open(FILE_CSV, "r", encoding="utf-8") as f:
        righe = list(csv.DictReader(f))

    righe = righe[-MAX_PUNTI_GRAFICO:]

    for i, riga in enumerate(righe):
        lista_temp.append(float(riga["temperatura"]))
        lista_hum.append(float(riga["umidita"]))
        lista_tempo.append(float(i))


# ==============================================================================
# THREAD PRODUTTORE: legge dalla porta seriale
# ==============================================================================
def produttore():
    ser = serial.Serial(PORTA_SERIALE, 9600, timeout=2)
    print(f"[PRODUTTORE] Connesso su {PORTA_SERIALE}")

    while True:
        riga_bytes = ser.readline()
        riga = riga_bytes.decode("utf-8", errors="ignore").strip()

        if riga != "":
            dati_queue.put(riga)


# ==============================================================================
# THREAD CONSUMATORE: prende dalla queue, aggiorna variabili e CSV
# ==============================================================================
def consumatore():
    global temperatura, umidita, stato_temp, stato_um
    global riscaldamento, finestre, deumidificatore, umidificatore

    ultimo_salvataggio = time.time()

    while True:
        riga = dati_queue.get()

        parti = riga.split(",")

        if len(parti) != 8:
            print(f"[CONSUMATORE] Riga non valida, scartata: {riga}")
            dati_queue.task_done()
            continue

        try:
            temp_letta = float(parti[0])
            hum_letta = float(parti[1])
        except ValueError:
            print(f"[CONSUMATORE] Valori non numerici, scartati: {riga}")
            dati_queue.task_done()
            continue

        with lock:
            temperatura = temp_letta
            umidita = hum_letta
            stato_temp = parti[2].strip()
            riscaldamento = parti[3].strip()
            finestre = parti[4].strip()
            stato_um = parti[5].strip()
            deumidificatore = parti[6].strip()
            umidificatore = parti[7].strip()

            t_relativo = time.time() - tempo_avvio
            lista_temp.append(temperatura)
            lista_hum.append(umidita)
            lista_tempo.append(t_relativo)

            if len(lista_temp) > MAX_PUNTI_GRAFICO:
                lista_temp.pop(0)
                lista_hum.pop(0)
                lista_tempo.pop(0)

        if time.time() - ultimo_salvataggio >= 10:
            salva_csv({
                "temperatura": temperatura,
                "umidita": umidita,
                "stato_temp": stato_temp,
                "riscaldamento": riscaldamento,
                "finestre": finestre,
                "stato_um": stato_um,
                "deumidificatore":deumidificatore,
                "umidificatore": umidificatore
            })
            ultimo_salvataggio = time.time()
            print(f"[CONSUMATORE] Salvato: T={temperatura}°C  H={umidita}%")

        dati_queue.task_done()


# ==============================================================================
# GUI: aggiorna la finestra ad ogni frame
# ==============================================================================
def aggiorna_gui():
    with lock:
        temp = temperatura
        hum = umidita
        st = stato_temp
        su = stato_um
        risc = riscaldamento
        fin = finestre
        deum = deumidificatore
        umid = umidificatore
        t_list = list(lista_tempo)
        temp_list = list(lista_temp)
        hum_list = list(lista_hum)

    if temp is None:
        return

    dpg.set_value("txt_temp", f"{temp:.1f} °C")
    dpg.set_value("txt_hum",  f"{hum:.1f} %")

    if st == "CALDO":
        dpg.configure_item("txt_temp", color=(220, 70, 70, 255))
        dpg.set_value("txt_sug_temp", "Temperatura alta! Apri le finestre")
        dpg.configure_item("txt_sug_temp", color=(220, 70, 70, 255))
    elif st == "FREDDO":
        dpg.configure_item("txt_temp", color=(80, 140, 220, 255))
        dpg.set_value("txt_sug_temp", "Temperatura bassa! Avvia riscaldamento")
        dpg.configure_item("txt_sug_temp", color=(80, 140, 220, 255))
    else:
        dpg.configure_item("txt_temp", color=(80, 200, 100, 255))
        dpg.set_value("txt_sug_temp", "Temperatura nella norma")
        dpg.configure_item("txt_sug_temp", color=(80, 200, 100, 255))

    if su == "UMIDO":
        dpg.configure_item("txt_hum", color=(60, 200, 200, 255))
        dpg.set_value("txt_sug_um", "Aria umida! Avvia deumidificatore")
        dpg.configure_item("txt_sug_um", color=(60, 200, 200, 255))
    elif su == "SECCO":
        dpg.configure_item("txt_hum", color=(220, 140, 60, 255))
        dpg.set_value("txt_sug_um", "Aria secca! Avvia umidificatore")
        dpg.configure_item("txt_sug_um", color=(220, 140, 60, 255))
    else:
        dpg.configure_item("txt_hum", color=(80, 200, 100, 255))
        dpg.set_value("txt_sug_um", "Umidita' nella norma")
        dpg.configure_item("txt_sug_um", color=(80, 200, 100, 255))

    for tag, etichetta, valore in [
        ("ind_risc", "RISCALDAMENTO", risc),
        ("ind_fin",  "FINESTRE",      fin),
        ("ind_deum", "DEUMIDIF.",     deum),
        ("ind_umid", "UMIDIFIC.",     umid),
    ]:
        if valore == "ON":
            dpg.set_value(tag, f"● {etichetta}: ON")
            dpg.configure_item(tag, color=(80, 200, 100, 255))
        else:
            dpg.set_value(tag, f"○ {etichetta}: OFF")
            dpg.configure_item(tag, color=(130, 130, 150, 255))

    if t_list:
        dpg.set_value("serie_temp", [t_list, temp_list])
        dpg.set_value("serie_hum",  [t_list, hum_list])
        dpg.fit_axis_data("asse_x")
        dpg.fit_axis_data("asse_y_temp")
        dpg.fit_axis_data("asse_y_hum")


# ==============================================================================
# COSTRUZIONE FINESTRA GRAFICA
# ==============================================================================
def build_gui():
    dpg.create_context()
    dpg.create_viewport(title="Monitor Ambientale", width=920, height=700,
                        resizable=False)
    dpg.setup_dearpygui()

    with dpg.theme() as tema:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,  (18,  18,  28,  255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg,   (28,  28,  42,  255))
            dpg.add_theme_color(dpg.mvThemeCol_Text,      (220, 220, 240, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border,    (60,  60,  90,  255))
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding,  6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding,  12, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing,     8,  6)
    dpg.bind_theme(tema)

    with dpg.window(tag="finestra", no_close=True, no_move=True,
                    no_resize=True, no_title_bar=True):

        dpg.add_text("Monitor Efficienza Energetica", color=(80, 200, 100, 255))
        dpg.add_separator()
        dpg.add_spacer(height=6)

        with dpg.group(horizontal=True):

            with dpg.child_window(width=440, height=100, border=True):
                dpg.add_text("TEMPERATURA", color=(130, 130, 150, 255))
                dpg.add_text("-- °C", tag="txt_temp", color=(220, 220, 240, 255))
                dpg.add_spacer(height=4)
                dpg.add_text("In attesa di dati...", tag="txt_sug_temp",
                             color=(130, 130, 150, 255), wrap=425)

            dpg.add_spacer(width=8)

            with dpg.child_window(width=440, height=100, border=True):
                dpg.add_text("UMIDITA'", color=(130, 130, 150, 255))
                dpg.add_text("-- %", tag="txt_hum", color=(220, 220, 240, 255))
                dpg.add_spacer(height=4)
                dpg.add_text("In attesa di dati...", tag="txt_sug_um",
                             color=(130, 130, 150, 255), wrap=425)

        dpg.add_spacer(height=10)

        dpg.add_text("STATO DISPOSITIVI", color=(130, 130, 150, 255))
        dpg.add_spacer(height=4)

        with dpg.group(horizontal=True):
            for tag, etichetta in [
                ("ind_risc", "RISCALDAMENTO"),
                ("ind_fin",  "FINESTRE"),
                ("ind_deum", "DEUMIDIF."),
                ("ind_umid", "UMIDIFIC."),
            ]:
                with dpg.child_window(width=212, height=36, border=True):
                    dpg.add_text(f"○ {etichetta}: OFF", tag=tag,
                                 color=(130, 130, 150, 255))
                dpg.add_spacer(width=4)

        dpg.add_spacer(height=10)
        dpg.add_separator()
        dpg.add_spacer(height=6)

        dpg.add_text("ANDAMENTO NEL TEMPO", color=(130, 130, 150, 255))
        dpg.add_spacer(height=4)

        with dpg.plot(height=370, width=-1):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="Tempo (s)", tag="asse_x")

            with dpg.plot_axis(dpg.mvYAxis, label="Temperatura (°C)",
                               tag="asse_y_temp"):
                dpg.add_line_series([], [], label="Temperatura °C",
                                    tag="serie_temp")
                dpg.add_inf_line_series([SOGLIA_CALDA],
                    label=f"Soglia calda ({SOGLIA_CALDA}°C)",
                    horizontal=True, color=(220, 70, 70, 100))
                dpg.add_inf_line_series([SOGLIA_FREDDA],
                    label=f"Soglia fredda ({SOGLIA_FREDDA}°C)",
                    horizontal=True, color=(80, 140, 220, 100))

            with dpg.plot_axis(dpg.mvYAxis, label="Umidita' (%)",
                               tag="asse_y_hum", no_gridlines=True):
                dpg.set_axis_limits("asse_y_hum", 0, 100)
                dpg.add_line_series([], [], label="Umidita' %",
                                    tag="serie_hum")
                dpg.add_inf_line_series([SOGLIA_UMIDO],
                    label=f"Soglia umida ({SOGLIA_UMIDO}%)",
                    horizontal=True, color=(60, 200, 200, 100))
                dpg.add_inf_line_series([SOGLIA_ARIDO],
                    label=f"Soglia secca ({SOGLIA_ARIDO}%)",
                    horizontal=True, color=(220, 140, 60, 100))

    dpg.set_primary_window("finestra", True)
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        aggiorna_gui()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    inizializza_csv()
    carica_storico()

    t1 = threading.Thread(target=produttore, daemon=True)
    t1.start()

    t2 = threading.Thread(target=consumatore, daemon=True)
    t2.start()

    build_gui()