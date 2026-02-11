import json
import psutil
from datetime import datetime

# ---------------- CONFIGURACIÓN ----------------

ARCHIVO_JSON = "perfil_base.json"
UMBRAL_RAM_MB = 100
MAX_SNAPSHOTS = 100

PROCESOS_IGNORADOS = {
    "svchost.exe",
    "System",
    "Registry",
    "Idle",
    "services.exe",
    "lsass.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe"
}

# ---------------- FUNCIONES ----------------

def obtener_fecha():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def obtener_datos_sistema():
    cpu_percent = psutil.cpu_percent(interval=1)

    ram = psutil.virtual_memory()
    ram_total_gb = round(ram.total / (1024 ** 3), 2)
    ram_usada_gb = round(ram.used / (1024 ** 3), 2)
    ram_percent = ram.percent

    return cpu_percent, ram_total_gb, ram_usada_gb, ram_percent


def obtener_procesos_filtrados():
    procesos = []

    for p in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            nombre = p.info['name']
            if not nombre:
                continue

            ram_mb = round(p.info['memory_info'].rss / (1024 ** 2), 2)

            if ram_mb >= UMBRAL_RAM_MB and nombre not in PROCESOS_IGNORADOS:
                procesos.append({
                    "pid": p.info['pid'],
                    "nombre": nombre,
                    "ram_mb": ram_mb
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return procesos


def cargar_historial():
    try:
        with open(ARCHIVO_JSON, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def guardar_historial(datos):
    with open(ARCHIVO_JSON, "w") as f:
        json.dump(datos, f, indent=4)


def limpiar_snapshots_antiguas(datos):
    if len(datos) > MAX_SNAPSHOTS:
        datos = datos[-MAX_SNAPSHOTS:]
    return datos


def calcular_perfil_base(datos):
    suma_cpu = sum(s["cpu_percent"] for s in datos)
    suma_ram = sum(s["ram_usada_gb"] for s in datos)

    media_cpu = suma_cpu / len(datos)
    media_ram = suma_ram / len(datos)

    var_cpu = sum((s["cpu_percent"] - media_cpu) ** 2 for s in datos) / len(datos)
    var_ram = sum((s["ram_usada_gb"] - media_ram) ** 2 for s in datos) / len(datos)

    desv_cpu = var_cpu ** 0.5
    desv_ram = var_ram ** 0.5

    return media_cpu, media_ram, desv_cpu, desv_ram


def detectar_anomalias(snapshot, media_cpu, media_ram, desv_cpu, desv_ram):
    alertas = []

    if snapshot["cpu_percent"] > media_cpu + 2 * desv_cpu:
        alertas.append("Pico anómalo de CPU")

    if snapshot["ram_usada_gb"] > media_ram + 2 * desv_ram:
        alertas.append("Pico anómalo de RAM")

    return alertas

def calcular_score_riesgo(snapshot, alertas, datos):
    score = 0
    motivos = []

    # Pico CPU o RAM
    if "Pico anómalo de CPU" in alertas:
        score += 1
        motivos.append("Pico de CPU")

    if "Pico anómalo de RAM" in alertas:
        score += 1
        motivos.append("Pico de RAM")

    # RAM muy alta en general
    if snapshot["ram_percent"] > 80:
        score += 1
        motivos.append("RAM superior al 80%")

    # Muchos procesos pesados
    if len(snapshot["procesos"]) > 5:
        score += 1
        motivos.append("Muchos procesos de alto consumo")

    # Procesos nuevos
    procesos_habituales = set()
    for s in datos[:-1]:
        for p in s["procesos"]:
            procesos_habituales.add(p["nombre"])

    nuevos = 0
    for p in snapshot["procesos"]:
        if p["nombre"] not in procesos_habituales:
            nuevos += 1

    if nuevos > 0:
        score += 1
        motivos.append("Procesos nuevos detectados")

    return score, motivos

def analizar_procesos_historicos(datos):
    estadisticas = {}

    for snap in datos:
        for p in snap["procesos"]:
            nombre = p["nombre"]
            ram = p["ram_mb"]

            if nombre not in estadisticas:
                estadisticas[nombre] = {
                    "veces": 0,
                    "ram_total": 0
                }

            estadisticas[nombre]["veces"] += 1
            estadisticas[nombre]["ram_total"] += ram

    # Calcular RAM media
    for nombre in estadisticas:
        veces = estadisticas[nombre]["veces"]
        total = estadisticas[nombre]["ram_total"]
        estadisticas[nombre]["ram_media"] = total / veces

    return estadisticas

def detectar_procesos_nuevos(snapshot, datos):
    procesos_anteriores = set()

    for snap in datos[:-1]:  # excluimos la snapshot actual
        for p in snap["procesos"]:
            procesos_anteriores.add(p["nombre"])

    nuevos = []

    for p in snapshot["procesos"]:
        if p["nombre"] not in procesos_anteriores:
            nuevos.append(p["nombre"])

    return nuevos

def detectar_procesos_persistentes(estadisticas):
    sospechosos = []

    for nombre, info in estadisticas.items():
        if info["veces"] > 5 and info["ram_media"] > 300:
            sospechosos.append(nombre)

    return sospechosos


# ---------------- PROGRAMA PRINCIPAL ----------------

def main():

    fecha = obtener_fecha()
    cpu, ram_total, ram_usada, ram_percent = obtener_datos_sistema()
    procesos = obtener_procesos_filtrados()

    snapshot = {
        "fecha": fecha,
        "cpu_percent": cpu,
        "ram_total_gb": ram_total,
        "ram_usada_gb": ram_usada,
        "ram_percent": ram_percent,
        "procesos": procesos
    }

    datos = cargar_historial()
    datos.append(snapshot)
    if len(datos) > 20:
        datos = datos[-20:]
    datos = limpiar_snapshots_antiguas(datos)
    guardar_historial(datos)

    print("\n--- ESTADO DEL SISTEMA ---")
    print(f"Fecha: {fecha}")
    print(f"CPU: {cpu}%")
    print(f"RAM usada: {ram_usada} GB ({ram_percent}%)")

    if len(datos) > 1:
        media_cpu, media_ram, desv_cpu, desv_ram = calcular_perfil_base(datos)
        alertas = detectar_anomalias(snapshot, media_cpu, media_ram, desv_cpu, desv_ram)

        if alertas:
            print("\n--- ALERTAS ---")
            for alerta in alertas:
                print(alerta)
        else:
            print("\nSistema estable.")

    print("\n--- PROCESOS RELEVANTES ---")
    for p in procesos:
        print(f"{p['pid']} - {p['nombre']} - {p['ram_mb']} MB")

    print("\nSnapshot guardada correctamente.")

    if len(datos) > 1:
        media_cpu, media_ram, desv_cpu, desv_ram = calcular_perfil_base(datos)
        alertas = detectar_anomalias(snapshot, media_cpu, media_ram, desv_cpu, desv_ram)

    score, motivos = calcular_score_riesgo(snapshot, alertas, datos)
    estadisticas = analizar_procesos_historicos(datos)

    nuevos = detectar_procesos_nuevos(snapshot, datos)

    persistentes = detectar_procesos_persistentes(estadisticas)
    
    if nuevos:
        print("\nProcesos nuevos detectados:")
    for n in nuevos:
        print("-", n)

    if persistentes:
        print("\nProcesos persistentes sospechosos:")
    for p in persistentes:
        print("-", p)


    print("\n--- SCORE DE RIESGO ---")
    print(f"Puntuación: {score}/5")

    if score <= 1:
        print("Estado: ESTABLE")
    elif score <= 3:
        print("Estado: INESTABLE")
    else:
        print("Estado: RIESGO ALTO")

    if motivos:
        print("Motivos:")
        for m in motivos:
            print("-", m)

if __name__ == "__main__":
    main()
