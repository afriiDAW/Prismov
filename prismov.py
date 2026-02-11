import psutil
import json
import os
from datetime import datetime, timedelta
import time
ARCHIVO_JSON = "perfil_base.json"
LIMITE_SNAPSHOTS = 20

IGNORAR = {
    "svchost.exe", "System", "Registry", "Idle", "services.exe",
    "lsass.exe", "csrss.exe", "wininit.exe", "winlogon.exe"
}
DIAS_MAP = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6
}


UMBRAL_RAM_MB = 200
VENTANA_TENDENCIAS = 10  # últimos N snapshots para análisis


# ==============================
# UTILIDADES BÁSICAS
# ==============================


def cargar_programacion(historial):
    # Si no existe, crear configuración por defecto
    if not historial or "programacion" not in historial[-1]:
        return {
            "activo": False,
            "dias": ["lunes", "martes", "miercoles", "jueves", "viernes"],
            "hora_inicio": "08:00",
            "hora_fin": "23:00",
            "intervalo_minutos": 10
        }
    return historial[-1]["programacion"]


def dentro_del_horario(programacion):
    if not programacion["activo"]:
        return False

    ahora = datetime.now()
    dia_actual = ahora.weekday()

    dias_permitidos = [DIAS_MAP[d.lower()] for d in programacion["dias"]]

    if dia_actual not in dias_permitidos:
        return False

    h_inicio = datetime.strptime(programacion["hora_inicio"], "%H:%M").time()
    h_fin = datetime.strptime(programacion["hora_fin"], "%H:%M").time()

    if h_inicio <= ahora.time() <= h_fin:
        return True

    return False


def esperar_hasta_siguiente_intervalo(programacion):
    intervalo = programacion["intervalo_minutos"]
    time.sleep(intervalo * 60)

def cargar_historial():
    if os.path.exists(ARCHIVO_JSON):
        with open(ARCHIVO_JSON, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def guardar_historial(datos):
    if len(datos) > LIMITE_SNAPSHOTS:
        datos = datos[-LIMITE_SNAPSHOTS:]
    with open(ARCHIVO_JSON, "w") as f:
        json.dump(datos, f, indent=4)


# ==============================
# SNAPSHOT
# ==============================

def crear_snapshot():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent

    procesos_dict = {}

    for proc in psutil.process_iter(["name", "memory_info", "exe"]):
        try:
            nombre = proc.info["name"]
            if not nombre or nombre in IGNORAR:
                continue

            ram_mb = proc.info["memory_info"].rss / (1024 * 1024)
            if ram_mb < UMBRAL_RAM_MB:
                continue

            ruta = proc.info.get("exe") or "desconocida"

            if nombre not in procesos_dict:
                procesos_dict[nombre] = {
                    "instancias": 0,
                    "ram_total_mb": 0.0,
                    "rutas": set()
                }

            procesos_dict[nombre]["instancias"] += 1
            procesos_dict[nombre]["ram_total_mb"] += ram_mb
            procesos_dict[nombre]["rutas"].add(ruta)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    procesos = []
    for nombre, info in procesos_dict.items():
        procesos.append({
            "nombre": nombre,
            "instancias": info["instancias"],
            "ram_total_mb": round(info["ram_total_mb"], 2),
            "ram_media_mb": round(info["ram_total_mb"] / info["instancias"], 2),
            "rutas": list(info["rutas"])
        })

    snapshot = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": cpu,
        "ram_percent": ram,
        "procesos": procesos
    }

    return snapshot


# ==============================
# DETECCIÓN DE NUEVOS
# ==============================

def detectar_nuevos(snapshot, historial):
    if not historial:
        return []

    ultimo = historial[-1]
    if "procesos" not in ultimo:
        return []

    nombres_antes = {p["nombre"] for p in ultimo.get("procesos", [])}
    nombres_ahora = {p["nombre"] for p in snapshot.get("procesos", [])}

    nuevos = list(nombres_ahora - nombres_antes)
    return sorted(nuevos)


# ==============================
# TENDENCIAS
# ==============================

def analizar_tendencias(historial):
    if not historial:
        return {
            "cpu": "desconocido",
            "ram": "desconocido",
            "procesos_crecientes": []
        }

    ventana = historial[-VENTANA_TENDENCIAS:]

    cpu_vals = [s.get("cpu_percent", 0) for s in ventana]
    ram_vals = [s.get("ram_percent", 0) for s in ventana]

    def tendencia(lista):
        if len(lista) < 2:
            return "insuficiente"
        if lista[-1] > lista[0] + 10:
            return "subiendo"
        if lista[-1] < lista[0] - 10:
            return "bajando"
        return "estable"

    # procesos crecientes: los que aumentan su ram_media_mb en la ventana
    procesos_por_snapshot = [s.get("procesos", []) for s in ventana]
    crecimiento = {}

    for procesos in procesos_por_snapshot:
        for p in procesos:
            nombre = p["nombre"]
            ram = p["ram_media_mb"]
            if nombre not in crecimiento:
                crecimiento[nombre] = []
            crecimiento[nombre].append(ram)

    procesos_crecientes = []
    for nombre, lista in crecimiento.items():
        if len(lista) >= 2 and lista[-1] > lista[0] + 50:  # +50 MB media
            procesos_crecientes.append(nombre)

    return {
        "cpu": tendencia(cpu_vals),
        "ram": tendencia(ram_vals),
        "procesos_crecientes": sorted(procesos_crecientes)
    }


# ==============================
# SOSPECHOSOS PERSISTENTES
# ==============================

def detectar_sospechosos_persistentes(historial):
    if not historial:
        return []

    # procesos que aparecen en la mayoría de snapshots y con consumo relevante
    apariciones = {}
    total_snaps = len(historial)

    for snap in historial:
        for p in snap.get("procesos", []):
            nombre = p["nombre"]
            ram = p["ram_media_mb"]
            if nombre not in apariciones:
                apariciones[nombre] = {
                    "veces": 0,
                    "ram_acumulada": 0.0,
                    "instancias_acumuladas": 0
                }
            apariciones[nombre]["veces"] += 1
            apariciones[nombre]["ram_acumulada"] += ram
            apariciones[nombre]["instancias_acumuladas"] += p.get("instancias", 1)

    sospechosos = []
    for nombre, info in apariciones.items():
        frecuencia = info["veces"] / total_snaps
        ram_media = info["ram_acumulada"] / info["veces"]
        inst_media = info["instancias_acumuladas"] / info["veces"]

        razones = []

        if frecuencia > 0.8:
            razones.append("Aparece en casi todos los snapshots")
        if ram_media > 400:
            razones.append("Consumo medio de RAM muy elevado")
        if inst_media > 3:
            razones.append("Demasiadas instancias en promedio")

        # algo “no visto antes”: marcar procesos que no son típicos de usuario
        if nombre.lower() not in {"chrome.exe", "firefox.exe", "explorer.exe", "discord.exe"} and frecuencia > 0.5 and ram_media > 250:
            razones.append("Proceso inusual con presencia y consumo relevantes")

        if razones:
            sospechosos.append({
                "nombre": nombre,
                "frecuencia": round(frecuencia, 2),
                "ram_media_mb": round(ram_media, 2),
                "instancias_medias": round(inst_media, 2),
                "razones": razones
            })

    # ordenar por ram_media
    sospechosos.sort(key=lambda x: x["ram_media_mb"], reverse=True)
    return sospechosos


# ==============================
# HUELLA DEL SISTEMA
# ==============================

def calcular_huella(historial):
    if not historial:
        return {}

    cpu_vals = [s.get("cpu_percent", 0) for s in historial]
    ram_vals = [s.get("ram_percent", 0) for s in historial]

    conteo_procesos = {}
    for snap in historial:
        for p in snap.get("procesos", []):
            nombre = p["nombre"]
            if nombre not in conteo_procesos:
                conteo_procesos[nombre] = 0
            conteo_procesos[nombre] += 1

    procesos_frecuentes = sorted(conteo_procesos.items(), key=lambda x: x[1], reverse=True)
    procesos_frecuentes = [p[0] for p in procesos_frecuentes[:10]]

    # procesos pesados constantes: alta ram_media y muchas apariciones
    pesados_constantes = []
    for nombre, veces in conteo_procesos.items():
        if veces < len(historial) // 2:
            continue
        ram_medias = []
        for snap in historial:
            for p in snap.get("procesos", []):
                if p["nombre"] == nombre:
                    ram_medias.append(p["ram_media_mb"])
        if ram_medias and sum(ram_medias) / len(ram_medias) > 300:
            pesados_constantes.append(nombre)

    return {
        "cpu_promedio": round(sum(cpu_vals) / len(cpu_vals), 2),
        "ram_promedio": round(sum(ram_vals) / len(ram_vals), 2),
        "procesos_frecuentes": procesos_frecuentes,
        "procesos_pesados_constantes": pesados_constantes
    }


# ==============================
# SCORE AVANZADO + RIESGO
# ==============================

def calcular_score_avanzado(snapshot, historial, sospechosos, tendencias):
    score_rendimiento = 0
    score_estabilidad = 0
    score_seguridad = 0
    motivos = []

    cpu = snapshot.get("cpu_percent", 0)
    ram = snapshot.get("ram_percent", 0)

    if cpu > 75:
        score_rendimiento += 2
        motivos.append("CPU muy alta en el snapshot actual")
    elif cpu > 60:
        score_rendimiento += 1
        motivos.append("CPU moderadamente alta")

    if ram > 85:
        score_rendimiento += 2
        motivos.append("RAM muy alta en el snapshot actual")
    elif ram > 70:
        score_rendimiento += 1
        motivos.append("RAM moderadamente alta")

    # estabilidad: tendencias y procesos crecientes
    if tendencias["cpu"] == "subiendo":
        score_estabilidad += 1
        motivos.append("Tendencia de CPU al alza")
    if tendencias["ram"] == "subiendo":
        score_estabilidad += 1
        motivos.append("Tendencia de RAM al alza")
    if tendencias["procesos_crecientes"]:
        score_estabilidad += 1
        motivos.append("Procesos con consumo creciente: " + ", ".join(tendencias["procesos_crecientes"]))

    # seguridad: sospechosos persistentes
    if sospechosos:
        score_seguridad += min(3, len(sospechosos))
        motivos.append("Procesos sospechosos persistentes detectados")

    total = score_rendimiento + score_estabilidad + score_seguridad

    if total <= 2:
        riesgo = "BAJO"
    elif total <= 5:
        riesgo = "MEDIO"
    elif total <= 8:
        riesgo = "ALTO"
    else:
        riesgo = "CRITICO"

    return {
        "rendimiento": score_rendimiento,
        "estabilidad": score_estabilidad,
        "seguridad": score_seguridad,
        "total": total,
        "riesgo_sistema": riesgo,
        "motivos": motivos
    }


# ==============================
# RECOMENDACIONES
# ==============================

def generar_recomendaciones(snapshot, sospechosos, tendencias, huella, procesos_nuevos):
    recomendaciones = []

    cpu = snapshot.get("cpu_percent", 0)
    ram = snapshot.get("ram_percent", 0)

    if cpu > 75:
        recomendaciones.append("Cerrar aplicaciones que consuman mucha CPU o revisar procesos en segundo plano.")
    if ram > 80:
        recomendaciones.append("La RAM está muy alta, considera cerrar navegadores con muchas pestañas o apps pesadas.")

    if sospechosos:
        nombres_sos = [s["nombre"] for s in sospechosos[:5]]
        recomendaciones.append(
            f"Revisar procesos sospechosos persistentes: {', '.join(nombres_sos)}."
        )

    if tendencias["procesos_crecientes"]:
        recomendaciones.append(
            "Hay procesos cuyo consumo de RAM crece con el tiempo: " +
            ", ".join(tendencias["procesos_crecientes"]) +
            ". Podrían estar generando fugas de memoria."
        )

    if procesos_nuevos:
        recomendaciones.append(
            "Se han detectado procesos nuevos recientemente: " +
            ", ".join(procesos_nuevos) +
            ". Verifica si corresponden a software instalado por ti."
        )

    if huella:
        if huella["ram_promedio"] > 75:
            recomendaciones.append(
                "La huella del sistema indica un uso de RAM alto de forma constante. "
                "Podría ser útil ampliar memoria o reducir programas residentes."
            )
        if huella["cpu_promedio"] > 70:
            recomendaciones.append(
                "La CPU se mantiene alta en promedio. Revisa tareas en segundo plano o software que arranca con el sistema."
            )

    if not recomendaciones:
        recomendaciones.append("El sistema parece estable. Mantén el software actualizado y evita instalar programas innecesarios.")

    return recomendaciones


# ==============================
# MAIN
# ==============================

def main():
    historial = cargar_historial()

    snapshot = crear_snapshot()

    procesos_nuevos = detectar_nuevos(snapshot, historial)

    historial_extendido = historial + [snapshot]

    tendencias = analizar_tendencias(historial_extendido)
    sospechosos = detectar_sospechosos_persistentes(historial_extendido)
    huella = calcular_huella(historial_extendido)
    score_detallado = calcular_score_avanzado(snapshot, historial_extendido, sospechosos, tendencias)
    recomendaciones = generar_recomendaciones(snapshot, sospechosos, tendencias, huella, procesos_nuevos)

    analisis = {
        "score_detallado": score_detallado,
        "tendencias": tendencias,
        "sospechosos_persistentes": sospechosos,
        "huella_del_sistema": huella,
        "procesos_nuevos": procesos_nuevos,
        "total_procesos_filtrados": len(snapshot.get("procesos", [])),
        "recomendaciones": recomendaciones
    }

    snapshot["analisis_avanzado"] = analisis

    historial.append(snapshot)
    guardar_historial(historial)

    print("Snapshot guardada correctamente.")
    print("Riesgo del sistema:", score_detallado["riesgo_sistema"])
    print("Score total:", score_detallado["total"])

    print("\nMotivos:")
    for m in score_detallado["motivos"]:
        print("-", m)

    if procesos_nuevos:
        print("\nProcesos nuevos detectados:")
        for n in procesos_nuevos:
            print("-", n)

    if sospechosos:
        print("\nProcesos sospechosos persistentes:")
        for s in sospechosos[:5]:
            print(f"- {s['nombre']} (RAM media: {s['ram_media_mb']} MB, frecuencia: {s['frecuencia']})")

    print("\nRecomendaciones clave:")
    for r in recomendaciones[:5]:
        print("-", r)


if __name__ == "__main__":
    main()
