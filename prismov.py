import json
import os
from datetime import datetime
import psutil

# -------------------------------
# CONFIGURACIÓN
# -------------------------------

IGNORAR = {
    "svchost.exe", "System", "Registry", "Idle", "services.exe",
    "lsass.exe", "csrss.exe", "wininit.exe", "winlogon.exe"
}

UMBRAL_RAM_MB = 200          # Procesos que consumen más de X MB
MAX_SNAPSHOTS = 200         # Máximo de snapshots guardados

# Ruta relativa del JSON
RUTA_JSON = os.path.join(os.path.dirname(__file__), "perfil_base.json")

# -------------------------------
# CARGAR O CREAR ARCHIVO JSON
# -------------------------------

if not os.path.exists(RUTA_JSON):
    with open(RUTA_JSON, "w") as f:
        json.dump([], f, indent=4)

with open(RUTA_JSON, "r") as archivo:
    datos = json.load(archivo)

# Limitar tamaño del historial
if len(datos) > MAX_SNAPSHOTS:
    datos = datos[-MAX_SNAPSHOTS:]

# -------------------------------
# CAPTURA DE DATOS DEL SISTEMA
# -------------------------------

fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cpu = psutil.cpu_percent(interval=1)
ram = psutil.virtual_memory()

ram_total_gb = round(ram.total / (1024**3), 2)
ram_usada_gb = round(ram.used / (1024**3), 2)
ram_percent = ram.percent

# -------------------------------
# FILTRAR PROCESOS
# -------------------------------

procesos_filtrados = []

for p in psutil.process_iter(['pid', 'name', 'memory_info']):
    try:
        nombre = p.info['name']
        if not nombre or nombre in IGNORAR:
            continue

        ram_mb = round(p.info['memory_info'].rss / (1024**2), 2)

        # Guardar solo procesos relevantes
        if ram_mb >= UMBRAL_RAM_MB:
            procesos_filtrados.append({
                "pid": p.info['pid'],
                "nombre": nombre,
                "ram_mb": ram_mb
            })

    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

# -------------------------------
# CREAR SNAPSHOT
# -------------------------------

snapshot = {
    "fecha": fecha_actual,
    "cpu_percent": cpu,
    "ram_total_gb": ram_total_gb,
    "ram_usada_gb": ram_usada_gb,
    "ram_percent": ram_percent,
    "procesos": procesos_filtrados
}

datos.append(snapshot)

# Guardar JSON
with open(RUTA_JSON, "w") as archivo:
    json.dump(datos, archivo, indent=4)

print(f"Snapshot añadida correctamente: {fecha_actual}")

# -------------------------------
# CÁLCULO DE MEDIA Y DESVIACIÓN
# -------------------------------

if len(datos) > 1:  # Evitar división entre cero

    suma_cpu = sum(s["cpu_percent"] for s in datos)
    suma_ram = sum(s["ram_usada_gb"] for s in datos)

    media_cpu = suma_cpu / len(datos)
    media_ram = suma_ram / len(datos)

    var_cpu = sum((s["cpu_percent"] - media_cpu) ** 2 for s in datos) / len(datos)
    var_ram = sum((s["ram_usada_gb"] - media_ram) ** 2 for s in datos) / len(datos)

    desv_cpu = var_cpu ** 0.5
    desv_ram = var_ram ** 0.5

    # -------------------------------
    # DETECCIÓN DE ANOMALÍAS
    # -------------------------------

    ultima = datos[-1]

    if ultima["cpu_percent"] > media_cpu + 2 * desv_cpu:
        print("⚠️ Pico de CPU detectado")

    if ultima["ram_usada_gb"] > media_ram + 2 * desv_ram:
        print("⚠️ Pico de RAM detectado")

# -------------------------------
# DETECCIÓN DE NUEVOS PROCESOS
# -------------------------------

procesos_habituales = set()

for snapshot in datos[:-1]:  # Excluir el último
    for proceso in snapshot["procesos"]:
        procesos_habituales.add(proceso["nombre"])

for proceso in datos[-1]["procesos"]:
    if proceso["nombre"] not in procesos_habituales:
        print(f"⚠️ Nuevo proceso detectado: {proceso['nombre']}")
