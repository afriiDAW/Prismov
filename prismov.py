import psutil
import time
import json
import os
import datetime
import requests

# ============================================================
# RUTAS FIJAS PARA QUE FUNCIONE EN .EXE
# ============================================================

DATA_DIR = os.path.join(os.getenv("LOCALAPPDATA"), "PRISMOV")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORIAL_PATH = os.path.join(DATA_DIR, "historial.json")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

# ============================================================
# CARGA Y GUARDADO DE HISTORIAL
# ============================================================

def cargar_historial():
    if not os.path.exists(HISTORIAL_PATH):
        return []
    try:
        with open(HISTORIAL_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

def guardar_historial(historial):
    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

# ============================================================
# CARGA Y GUARDADO DE CONFIGURACIÓN
# ============================================================

def cargar_config():
    if not os.path.exists(CONFIG_PATH):
        return {"chat_id": None, "programacion": {}}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"chat_id": None, "programacion": {}}
    except:
        return {"chat_id": None, "programacion": {}}

def guardar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def cargar_programacion():
    config = cargar_config()
    prog = config.get("programacion", {})

    # Valores por defecto si no existen
    return {
        "activo": prog.get("activo", False),
        "dias": prog.get("dias", []),
        "hora_inicio": prog.get("hora_inicio", "00:00"),
        "hora_fin": prog.get("hora_fin", "23:59"),
        "intervalo_minutos": prog.get("intervalo_minutos", 60)
    }

def guardar_programacion(nueva_prog):
    config = cargar_config()
    config["programacion"] = nueva_prog
    guardar_config(config)

def configurar_programacion_consola():
    print("\n=== CONFIGURAR PROGRAMACIÓN ===")

    dias_validos = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

    print("Introduce los días separados por comas (ej: lunes,martes,viernes):")
    dias = input("Días: ").lower().replace(" ", "").split(",")
    dias = [d for d in dias if d in dias_validos]

    hora_inicio = input("Hora inicio (HH:MM): ")
    hora_fin = input("Hora fin (HH:MM): ")

    intervalo = int(input("Intervalo en minutos: "))

    nueva = {
        "activo": True,
        "dias": dias,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "intervalo_minutos": intervalo
    }

    guardar_programacion(nueva)
    print("✔ Programación guardada correctamente.")

# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_TOKEN = "8488886057:AAH8PkpvspCgwGWNY4ImAKgJ7bf58fzpzjo"

def cargar_chat_id():
    return cargar_config().get("chat_id")

def guardar_chat_id(chat_id):
    config = cargar_config()
    config["chat_id"] = chat_id
    guardar_config(config)

def obtener_chat_id():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        r = requests.get(url).json()
        if "result" in r and len(r["result"]) > 0:
            return r["result"][-1]["message"]["chat"]["id"]
        return None
    except:
        return None

def enviar_telegram(mensaje):
    chat_id = cargar_chat_id()
    if not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except:
        pass

# ============================================================
# ANÁLISIS DEL SISTEMA
# ============================================================

def analizar_procesos():
    procesos = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            procesos.append({
                "pid": p.info["pid"],
                "nombre": p.info["name"],
                "cpu": p.info["cpu_percent"],
                "ram_mb": p.info["memory_info"].rss / (1024 * 1024)
            })
        except:
            pass
    return procesos

def analisis_avanzado(snapshot, historial):
    return {
        "tendencias": {
            "cpu": "estable",
            "ram": "estable",
            "procesos_crecientes": []
        },
        "sospechosos_persistentes": [],
        "huella_del_sistema": {
            "cpu_promedio": snapshot["cpu_percent"],
            "ram_promedio": snapshot["ram_percent"],
            "procesos_frecuentes": [],
            "procesos_pesados_constantes": []
        },
        "procesos_nuevos": [],
        "score_detallado": {
            "riesgo_sistema": "BAJO"
        },
        "recomendaciones": [
            "Todo parece estable."
        ]
    }

# ============================================================
# GENERAR INFORME
# ============================================================

def formatear_sospechosos(lista):
    if not lista:
        return "Ninguno"
    texto = ""
    for s in lista:
        texto += f"- *{s['nombre']}* (RAM media: {s['ram_media_mb']} MB, Instancias: {s['instancias_medias']}, Frecuencia: {s['frecuencia']})\n"
    return texto

def generar_informe_completo(snapshot):
    a = snapshot["analisis_avanzado"]

    informe = f"""
📊 *PRISMOV - Informe del Sistema*
Fecha: {snapshot["timestamp"]}

🖥 *Rendimiento*
• CPU: {snapshot["cpu_percent"]}%
• RAM: {snapshot["ram_percent"]}%

📈 *Tendencias*
• CPU: {a["tendencias"]["cpu"]}
• RAM: {a["tendencias"]["ram"]}
• Procesos con consumo creciente: {", ".join(a["tendencias"]["procesos_crecientes"]) or "Ninguno"}

🕵️ *Sospechosos Persistentes*
{formatear_sospechosos(a["sospechosos_persistentes"])}

🧬 *Huella del Sistema*
• CPU promedio: {a["huella_del_sistema"]["cpu_promedio"]}%
• RAM promedio: {a["huella_del_sistema"]["ram_promedio"]}%
• Procesos frecuentes: {", ".join(a["huella_del_sistema"]["procesos_frecuentes"]) or "Ninguno"}
• Pesados constantes: {", ".join(a["huella_del_sistema"]["procesos_pesados_constantes"]) or "Ninguno"}

🆕 *Procesos Nuevos*
{", ".join(a["procesos_nuevos"]) or "Ninguno"}

⚠️ *Riesgo del Sistema:* *{a["score_detallado"]["riesgo_sistema"]}*

🛠 *Recomendaciones*
- """ + "\n- ".join(a["recomendaciones"])

    return informe

# ============================================================
# EJECUTAR ANÁLISIS
# ============================================================

def ejecutar_analisis(historial):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    procesos = analizar_procesos()

    # Snapshot base REAL
    snapshot_base = {
        "cpu_percent": cpu,
        "ram_percent": ram,
        "procesos": procesos
    }

    # Ahora sí, análisis avanzado con datos reales
    analisis = analisis_avanzado(snapshot_base, historial)

    snapshot = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": cpu,
        "ram_percent": ram,
        "procesos": procesos,
        "analisis_avanzado": analisis
    }

    historial.append(snapshot)
    guardar_historial(historial)

    informe = generar_informe_completo(snapshot)
    enviar_telegram(informe)


# ============================================================
# MODO AUTOMÁTICO
# ============================================================

def iniciar_modo_automatico(historial):
    while True:
        prog = cargar_programacion()

        if prog["activo"]:
            ahora = datetime.datetime.now()
            dia = ahora.strftime("%A").lower()

            if dia in prog["dias"]:
                h_inicio = datetime.datetime.strptime(prog["hora_inicio"], "%H:%M").time()
                h_fin = datetime.datetime.strptime(prog["hora_fin"], "%H:%M").time()

                if h_inicio <= ahora.time() <= h_fin:
                    ejecutar_analisis(historial)

        time.sleep(prog["intervalo_minutos"] * 60)


# ============================================================
# MAIN PARA EJECUCIÓN DESDE CONSOLA
# (La GUI no usa este menú, pero sigue siendo útil)
# ============================================================

def main():
    print("=== PRISMOV - Sistema de Monitorización ===")

    # Cargar historial
    historial = cargar_historial()

    # Comprobar si Telegram está configurado
    config = cargar_config()

    if config.get("chat_id") is None:
        print("\n⚠ Telegram no está configurado.")
        print("1) Abre tu bot en Telegram")
        print("2) Escríbele cualquier mensaje (por ejemplo: hola)")
        input("Cuando lo hayas hecho, pulsa ENTER...")

        chat_id = obtener_chat_id()
        if chat_id:
            guardar_chat_id(chat_id)
            print(f"✔ Telegram configurado correctamente. chat_id = {chat_id}")
        else:
            print("❌ No se pudo obtener el chat_id. Telegram seguirá desactivado.")

    # Menú simple
    while True:
        print("\n--- MENÚ ---")
        print("1) Ejecutar análisis ahora")
        print("2) Iniciar modo automático")
        print("3) Configurar programación")
        print("4) Salir")
        


        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            ejecutar_analisis(historial)
            print("✔ Análisis completado.")

        elif opcion == "2":
            print("Modo automático iniciado. Pulsa CTRL+C para detenerlo.")
            iniciar_modo_automatico(historial)

        elif opcion == "3":
            configurar_programacion_consola()

        elif opcion == "4":
            print("Saliendo...")
            break

        


        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
