import json
from datetime import datetime
import psutil

umbral_ram_MB= 100

with open("perfil_base.json", "r") as archivo:
    datos = json.load(archivo)

print(datos)

fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cpu = psutil.cpu_percent(interval=1)
ram = psutil.virtual_memory()
ram_total_gb = round(ram.total / (1024**3), 2)
ram_usada_gb = round(ram.used / (1024**3), 2)
ram_percent = ram.percent



procesos = []

for p in psutil.process_iter(['pid', 'name', 'memory_info']):
    try:
        procesos.append({
            "pid": p.info['pid'],
            "nombre": p.info['name'],
            "ram_mb": round(p.info['memory_info'].rss / (1024**2), 2)
        })
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue


snapshot = {
    "fecha": fecha_actual,
    "cpu_percent": cpu,
    "ram_total_gb": ram_total_gb,
    "ram_usada_gb": ram_usada_gb,
    "ram_percent": ram_percent,
    "procesos": procesos
}

datos.append(snapshot)

with open("perfil_base.json", "w") as archivo:
    json.dump(datos, archivo, indent=4)
    
with open("perfil_base.json", "r") as archivo:
    datos = json.load(archivo)

print(f"Snapshot añadida correctamente: {fecha_actual}")

suma_cpu = 0
suma_ram = 0

for snapshot in datos:
    suma_cpu += snapshot["cpu_percent"]
    suma_ram += snapshot["ram_usada_gb"]

media_cpu = suma_cpu / len(datos)
media_ram = suma_ram / len(datos)

var_cpu = 0 
var_ram = 0

for snapshot in datos:
    var_cpu += (snapshot["cpu_percent"] - media_cpu) ** 2
    var_ram += (snapshot["ram_usada_gb"] - media_ram) ** 2

# DIVISIÓN ENTRE NÚMERO DE SPASHOTS
var_cpu = 0 
var_ram = 0

var_cpu /= len(datos)
var_ram /= len(datos)

# RAÍZ CUADRADA DE LOS DATOS

desv_cpu = 0
desv_ram = 0

desv_cpu = var_cpu ** 0.5
desv_ram = var_ram ** 0.5

# DETECCIÓN DE ANOMALÍAS EN LA RAM Y CPU

ultima = datos[-1]

if ultima["cpu_percent"] > media_cpu + 2 * desv_cpu:
    print("⚠️ Pico de CPU detectado")

if ultima["ram_usada_gb"] > media_ram + 2 * desv_ram:
    print("⚠️ Pico de RAM detectado")

procesos_habituales = set()

procesos_habituales = set()

for s in datos[:-1]:
    for p in s["procesos"]:
        procesos_habituales.add(p["nombre"])

print("\n--- PROCESOS CON ALTO CONSUMO DE RAM ---")
for p in procesos:
    print(f"{p['pid']} - {p['nombre']} - {p['ram_mb']} MB")

print("\n--- PROCESOS NUEVOS DETECTADOS ---")
for p in procesos:
    if p["nombre"] not in procesos_habituales:
        print(f"Nuevo proceso: {p['nombre']} ({p['ram_mb']} MB)")

for snapshot in datos:
    for proceso in snapshot["procesos"]:
        procesos_habituales.add(proceso["nombre"])

ultima = datos[-1]

for proceso in ultima["procesos"]:
    if proceso["nombre"] not in procesos_habituales:
        print(f"⚠️ Nuevo proceso detectado: {proceso['nombre']}")

print(f"Snapshot añadida correctamente: {fecha_actual}")




















