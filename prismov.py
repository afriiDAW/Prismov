import psutil
import time
import json
import os
import datetime
import requests
import random
import string
import webbrowser
from supabase import create_client
import io
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = "https://ejtmmwqhetlhwihxejdu.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqdG1td3FoZXRsaHdpaHhlamR1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTQzMjEyMCwiZXhwIjoyMDg3MDA4MTIwfQ.gK6H0XdiPe9UbL_4VedDjbSmRhoft22Z7gE-uY6hP_M"  # Usa la service_role, NO la anon
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVqdG1td3FoZXRsaHdpaHhlamR1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE0MzIxMjAsImV4cCI6MjA4NzAwODEyMH0.nX6mfYsecLuKaNCIm4PMbe94Ygmc1CTgzNxV6MipiK8"
supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

usuario_actual = None


def supabase_configurado():
    global usuario_actual
    config = cargar_config()

    return (
        usuario_actual is not None and
        config.get("supabase_activo", False)
    )

def activar_supabase():
    config = cargar_config()
    config["supabase_activo"] = True
    guardar_config(config)

def desactivar_supabase():
    config = cargar_config()
    config["supabase_activo"] = False
    guardar_config(config)

def subir_snapshot_a_storage(snapshot):
    global usuario_actual
    if not usuario_actual:
        print("⚠ No hay usuario logueado.")
        return False
    try:
        html_reporte = generar_reporte_html(snapshot)
        ts = snapshot.get("timestamp") or datetime.datetime.now().isoformat()
        safe_ts = ts.replace(":", "-").replace(" ", "_")
        filename = f"reporte_{safe_ts}.html"

        # Corrección para el error de 'list' en el username
        username_data = cargar_config().get("username")
        username = username_data[0] if isinstance(username_data, list) else username_data
        
        user_folder = f"reportes/{username}"

        # CRUCIAL: 'content-type' para que el navegador renderice el HTML
        # Usamos 'x-upsert': 'true' para permitir sobrescribir si fuera necesario
        resp = supabase.storage.from_("prismov-reportes").upload(
            path=f"{user_folder}/{filename}",
            file=html_reporte.encode("utf-8"),
            file_options={
                "content-type": "text/html",
                "x-upsert": "true"
            }
        )
        print(f"✅ Reporte renderizable subido: {filename}")
        return True
    except Exception as e:
        print("❌ ERROR AL SUBIR (MIME TYPE):", repr(e))
        return False

def abrir_directorio_supabase():
    username = cargar_config().get("username")

    url = supabase.storage.from_("prismov-reportes").get_public_url(
        f"reportes/{username}/"
    )

    webbrowser.open(url)
    
def registrar_usuario():
    global usuario_actual

    email = input("Email: ")
    password = input("Password: ")

    response = supabase.auth.sign_up({
        "email": email,
        "password": password
    })

    if response.user:
        print("✔ Usuario registrado.")
    else:
        print("❌ Error al registrar.")


def login_usuario():
    global usuario_actual

    email = input("Email: ")
    password = input("Password: ")

    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    if response.user:
        usuario_actual = response.user

        # ⭐ Crear username simple desde email
        username = email.split("@")[0]

        # ⭐ Guardar en config.json
        config = cargar_config()
        config["username"] = username
        config["supabase_activo"] = True
        guardar_config(config)

        print("✔ Login correcto.")
    else:
        print("❌ Credenciales incorrectas.")






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
    default_config = {
        "chat_id": None,
        "programacion": {},
        "supabase_activo": False
    }

    try:
        if not os.path.exists(CONFIG_PATH):
            return default_config

        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            contenido = f.read().strip()

            if not contenido:
                return default_config

            data = json.loads(contenido)

            # Asegurar campos mínimos
            for k, v in default_config.items():
                if k not in data:
                    data[k] = v

            return data

    except:
        return default_config

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

# ============================================================
# CÓDIGO DE VINCULACIÓN DE USUARIOS
# ============================================================

def generar_codigo_vinculacion():
    """Genera un código aleatorio de 6 caracteres para vincular usuarios"""
    caracteres = string.ascii_uppercase + string.digits
    codigo = ''.join(random.choices(caracteres, k=6))
    return codigo

def cargar_codigo_vinculacion():
    """Carga el código de vinculación actual"""
    config = cargar_config()
    codigo = config.get("codigo_vinculacion")
    
    # Si no hay código, generar uno nuevo
    if not codigo:
        codigo = generar_codigo_vinculacion()
        config["codigo_vinculacion"] = codigo
        guardar_config(config)
    
    return codigo

def generar_nuevo_codigo():
    """Genera un nuevo código de vinculación"""
    codigo = generar_codigo_vinculacion()
    config = cargar_config()
    config["codigo_vinculacion"] = codigo
    guardar_config(config)
    return codigo

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

def telegram_configurado():
    """Verifica si Telegram está configurado"""
    return cargar_chat_id() is not None


def borrar_chat_id():
    """Elimina el chat_id almacenado (cierra sesión de Telegram)"""
    config = cargar_config()
    config["chat_id"] = None
    guardar_config(config)

def obtener_chat_id_y_validar_codigo():
    """
    Obtiene el chat_id pero verificando que el último mensaje contenga el código de vinculación correcto
    Retorna: (chat_id, código_valido) o (None, False)
    """
    codigo_esperado = cargar_codigo_vinculacion()
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        r = requests.get(url).json()
        
        if "result" in r and len(r["result"]) > 0:
            ultimo_mensaje = r["result"][-1].get("message", {})
            texto_mensaje = ultimo_mensaje.get("text", "").upper()
            chat_id = ultimo_mensaje.get("chat", {}).get("id")
            
            # Verificar si el mensaje contiene el código
            if codigo_esperado in texto_mensaje:
                return chat_id, True
            else:
                return None, False
        
        return None, False
    except:
        return None, False

def obtener_chat_id():
    """Obtiene solo el chat_id del último mensaje"""
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
            info = p.info
            procesos.append({
                "pid": info["pid"],
                "nombre": info["name"],
                "cpu": round(info["cpu_percent"], 2),
                "ram_mb": round(info["memory_info"].rss / (1024 * 1024), 2)
            })
        except:
            pass
    return sorted(procesos, key=lambda x: x["ram_mb"], reverse=True)

def analizar_tendencias(historial):
    """Analiza tendencias en el historial"""
    if len(historial) < 2:
        return "Datos insuficientes", "Datos insuficientes", []
    
    # Comparar últimos dos registros
    ultimo = historial[-1]
    anterior = historial[-2]
    
    cpu_actual = ultimo["cpu_percent"]
    cpu_anterior = anterior["cpu_percent"]
    ram_actual = ultimo["ram_percent"]
    ram_anterior = anterior["ram_percent"]
    
    # Determinar tendencia de CPU
    if cpu_actual > cpu_anterior + 10:
        tendencia_cpu = "↑ Creciente"
    elif cpu_actual < cpu_anterior - 10:
        tendencia_cpu = "↓ Decreciente"
    else:
        tendencia_cpu = "→ Estable"
    
    # Determinar tendencia de RAM
    if ram_actual > ram_anterior + 5:
        tendencia_ram = "↑ Creciente"
    elif ram_actual < ram_anterior - 5:
        tendencia_ram = "↓ Decreciente"
    else:
        tendencia_ram = "→ Estable"
    
    # Detectar procesos con consumo creciente
    procesos_crecientes = []
    procesos_actuales = {p["nombre"]: p for p in ultimo["procesos"]}
    procesos_anteriores = {p["nombre"]: p for p in anterior["procesos"]}
    
    for nombre, proc_actual in procesos_actuales.items():
        if nombre in procesos_anteriores:
            proc_anterior = procesos_anteriores[nombre]
            if proc_actual["ram_mb"] > proc_anterior["ram_mb"] + 50:  # Más de 50MB de aumento
                procesos_crecientes.append({
                    "nombre": nombre,
                    "ram_anterior": proc_anterior["ram_mb"],
                    "ram_actual": proc_actual["ram_mb"]
                })
    
    return tendencia_cpu, tendencia_ram, procesos_crecientes

def detectar_procesos_sospechosos(procesos):
    """Detecta procesos que consumen recursos anormales"""
    sospechosos = []
    
    # Obtener estadísticas
    if not procesos:
        return sospechosos
    
    # Procesos procesados
    procesos_con_recursos = [p for p in procesos if p["ram_mb"] > 0 or p["cpu"] > 0]
    
    if not procesos_con_recursos:
        return sospechosos
    
    ram_values = [p["ram_mb"] for p in procesos_con_recursos]
    ram_promedio = sum(ram_values) / len(ram_values)
    ram_desv = (sum((x - ram_promedio) ** 2 for x in ram_values) / len(ram_values)) ** 0.5
    
    cpu_values = [p["cpu"] for p in procesos_con_recursos if p["cpu"] > 0]
    cpu_promedio = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    
    # Procesos que consumen >30% del RAM promedio o >5% CPU
    for proc in procesos_con_recursos:
        razon_ram = proc["ram_mb"] / ram_promedio if ram_promedio > 0 else 0
        
        if (proc["ram_mb"] > 500 and razon_ram > 2) or proc["cpu"] > 10:
            sospechosos.append({
                "nombre": proc["nombre"],
                "ram_mb": proc["ram_mb"],
                "cpu": proc["cpu"],
                "razon": f"Alto consumo de {'RAM' if proc['ram_mb'] > 500 else 'CPU'}"
            })
    
    return sorted(sospechosos, key=lambda x: x["ram_mb"], reverse=True)

def analisis_avanzado(snapshot, historial):
    """Análisis avanzado y preciso del sistema"""
    tendencia_cpu, tendencia_ram, procesos_crecientes = analizar_tendencias(historial)
    sospechosos = detectar_procesos_sospechosos(snapshot["procesos"])
    
    # Procesos frecuentes (top 5 por RAM)
    procesos_frecuentes = [p["nombre"] for p in snapshot["procesos"][:5]]
    
    # Calcular promedios históricos
    if len(historial) > 1:
        cpu_promedio = sum(s["cpu_percent"] for s in historial[-10:]) / min(10, len(historial))
        ram_promedio = sum(s["ram_percent"] for s in historial[-10:]) / min(10, len(historial))
    else:
        cpu_promedio = snapshot["cpu_percent"]
        ram_promedio = snapshot["ram_percent"]
    
    # Determinar riesgo
    riesgo = "BAJO"
    if len(sospechosos) > 3:
        riesgo = "ALTO"
    elif len(sospechosos) > 0:
        riesgo = "MEDIO"
    elif snapshot["cpu_percent"] > 80 or snapshot["ram_percent"] > 85:
        riesgo = "MEDIO"
    
    # Recomendaciones
    recomendaciones = []
    if snapshot["cpu_percent"] > 80:
        recomendaciones.append("CPU muy alta. Considera cerrar aplicaciones innecesarias.")
    if snapshot["ram_percent"] > 85:
        recomendaciones.append("RAM muy alta. Reinicia el sistema si es posible.")
    if len(sospechosos) > 0:
        recomendaciones.append(f"Detectados {len(sospechosos)} proceso(s) con alto consumo de recursos.")
    if not recomendaciones:
        recomendaciones.append("El sistema funciona correctamente.")
    
    return {
        "tendencias": {
            "cpu": tendencia_cpu,
            "ram": tendencia_ram,
            "procesos_crecientes": procesos_crecientes
        },
        "sospechosos_persistentes": sospechosos,
        "huella_del_sistema": {
            "cpu_promedio": round(cpu_promedio, 2),
            "ram_promedio": round(ram_promedio, 2),
            "procesos_frecuentes": procesos_frecuentes,
            "procesos_pesados_constantes": [p["nombre"] for p in snapshot["procesos"][:3]]
        },
        "procesos_nuevos": [p["nombre"] for p in snapshot["procesos"][:3]],
        "score_detallado": {
            "riesgo_sistema": riesgo
        },
        "recomendaciones": recomendaciones
    }

# ============================================================
# GENERAR REPORTES HTML
# ============================================================

REPORTES_DIR = os.path.join(DATA_DIR, "reportes")
os.makedirs(REPORTES_DIR, exist_ok=True)

def generar_reporte_html(snapshot):
    """Genera un reporte HTML detallado y atractivo"""
    a = snapshot["analisis_avanzado"]
    timestamp = snapshot["timestamp"]
    
    # Determinar color según riesgo
    riesgo = a["score_detallado"]["riesgo_sistema"]
    if riesgo == "BAJO":
        color_riesgo = "#4CAF50"  # Verde
        bg_riesgo = "#E8F5E9"
    elif riesgo == "MEDIO":
        color_riesgo = "#FF9800"  # Naranja
        bg_riesgo = "#FFF3E0"
    else:
        color_riesgo = "#F44336"  # Rojo
        bg_riesgo = "#FFEBEE"
    
    # Procesos sospechosos HTML
    procesos_html = ""
    if a["sospechosos_persistentes"]:
        for proc in a["sospechosos_persistentes"]:
            procesos_html += f"""
            <tr>
                <td>{proc['nombre']}</td>
                <td>{proc['ram_mb']:.2f} MB</td>
                <td>{proc['cpu']:.2f}%</td>
                <td>{proc['razon']}</td>
            </tr>
            """
    else:
        procesos_html = "<tr><td colspan='4' style='text-align:center; color:#999;'>✓ Ninguno detectado</td></tr>"
    
    # Procesos crecientes HTML
    procesos_crec_html = ""
    if a["tendencias"]["procesos_crecientes"]:
        for proc in a["tendencias"]["procesos_crecientes"]:
            procesos_crec_html += f"""
            <tr>
                <td>{proc['nombre']}</td>
                <td>{proc['ram_anterior']:.2f} MB</td>
                <td>{proc['ram_actual']:.2f} MB</td>
                <td>↑ +{proc['ram_actual'] - proc['ram_anterior']:.2f} MB</td>
            </tr>
            """
    else:
        procesos_crec_html = "<tr><td colspan='4' style='text-align:center; color:#999;'>✓ Ninguno detectado</td></tr>"
    
    # Procesos frecuentes
    procesos_freq_html = ""
    if a["huella_del_sistema"]["procesos_frecuentes"]:
        for proc in a["huella_del_sistema"]["procesos_frecuentes"]:
            procesos_freq_html += f"<li>{proc}</li>"
    
    # Recomendaciones
    recomendaciones_html = ""
    for rec in a["recomendaciones"]:
        recomendaciones_html += f"<li>{rec}</li>"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PRISMOV - Informe del Sistema</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .header p {{
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .section {{
                margin-bottom: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 20px;
            }}
            .section:last-child {{
                border-bottom: none;
            }}
            .section h2 {{
                color: #667eea;
                font-size: 20px;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .stat-card {{
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .stat-card .label {{
                color: #666;
                font-size: 12px;
                text-transform: uppercase;
                margin-bottom: 8px;
            }}
            .stat-card .value {{
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
            }}
            .stat-card .unit {{
                font-size: 14px;
                color: #999;
            }}
            .risk-box {{
                background: {bg_riesgo};
                border-left: 5px solid {color_riesgo};
                padding: 20px;
                border-radius: 5px;
                margin: 15px 0;
            }}
            .risk-box .risk-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}
            .risk-box .risk-value {{
                font-size: 24px;
                font-weight: bold;
                color: {color_riesgo};
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            table th {{
                background: #f5f5f5;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #ddd;
            }}
            table td {{
                padding: 12px;
                border-bottom: 1px solid #eee;
            }}
            table tr:hover {{
                background: #f9f9f9;
            }}
            .trend-good {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .trend-warning {{
                color: #FF9800;
                font-weight: bold;
            }}
            .trend-danger {{
                color: #F44336;
                font-weight: bold;
            }}
            ul {{
                margin-left: 20px;
                margin-top: 10px;
            }}
            ul li {{
                margin-bottom: 8px;
                color: #333;
            }}
            .footer {{
                background: #f5f5f5;
                padding: 20px;
                text-align: center;
                color: #999;
                font-size: 12px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 PRISMOV</h1>
                <p>Informe de Análisis del Sistema</p>
                <p>{timestamp}</p>
            </div>
            
            <div class="content">
                <!-- RESUMEN RÁPIDO -->
                <div class="section">
                    <h2>⚡ Resumen Rápido</h2>
                    <div class="stats">
                        <div class="stat-card">
                            <div class="label">Uso de CPU</div>
                            <div class="value">{snapshot['cpu_percent']:.1f}<span class="unit">%</span></div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Uso de RAM</div>
                            <div class="value">{snapshot['ram_percent']:.1f}<span class="unit">%</span></div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Procesos Activos</div>
                            <div class="value">{len(snapshot['procesos'])}</div>
                        </div>
                        <div class="stat-card">
                            <div class="label">Riesgo del Sistema</div>
                            <div class="value" style="color: {color_riesgo};">{riesgo}</div>
                        </div>
                    </div>
                </div>

                <!-- EVALUACIÓN DE RIESGO -->
                <div class="section">
                    <h2>⚠️ Evaluación de Riesgo</h2>
                    <div class="risk-box">
                        <div class="risk-label">Nivel de Riesgo del Sistema</div>
                        <div class="risk-value">{riesgo}</div>
                    </div>
                </div>

                <!-- TENDENCIAS -->
                <div class="section">
                    <h2>📈 Tendencias</h2>
                    <table>
                        <tr>
                            <th>Recurso</th>
                            <th>Tendencia</th>
                            <th>Promedio (últimas 10 muestras)</th>
                        </tr>
                        <tr>
                            <td>CPU</td>
                            <td><span class="trend-good">{a['tendencias']['cpu']}</span></td>
                            <td>{a['huella_del_sistema']['cpu_promedio']:.2f}%</td>
                        </tr>
                        <tr>
                            <td>RAM</td>
                            <td><span class="trend-good">{a['tendencias']['ram']}</span></td>
                            <td>{a['huella_del_sistema']['ram_promedio']:.2f}%</td>
                        </tr>
                    </table>
                </div>

                <!-- PROCESOS SOSPECHOSOS -->
                <div class="section">
                    <h2>🕵️ Procesos con Alto Consumo</h2>
                    <table>
                        <tr>
                            <th>Nombre del Proceso</th>
                            <th>Memoria (MB)</th>
                            <th>CPU (%)</th>
                            <th>Razón</th>
                        </tr>
                        {procesos_html}
                    </table>
                </div>

                <!-- PROCESOS CON AUMENTO DE RECURSOS -->
                <div class="section">
                    <h2>📊 Procesos con Aumento de Recursos</h2>
                    <table>
                        <tr>
                            <th>Proceso</th>
                            <th>RAM Anterior (MB)</th>
                            <th>RAM Actual (MB)</th>
                            <th>Cambio</th>
                        </tr>
                        {procesos_crec_html}
                    </table>
                </div>

                <!-- PROCESOS PRINCIPALES -->
                <div class="section">
                    <h2>🔝 Procesos Principales</h2>
                    <ul>
                        {procesos_freq_html if procesos_freq_html else "<li>No hay procesos principales detectados</li>"}
                    </ul>
                </div>

                <!-- RECOMENDACIONES -->
                <div class="section">
                    <h2>💡 Recomendaciones</h2>
                    <ul>
                        {recomendaciones_html}
                    </ul>
                </div>
            </div>

            <div class="footer">
                <p>PRISMOV © 2026 - Sistema de Monitorización Avanzado del Sistema</p>
                <p>Reporte generado automáticamente</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def guardar_reporte(snapshot):
    """Guarda el reporte en HTML"""
    html = generar_reporte_html(snapshot)
    
    # Nombre del archivo con timestamp
    timestamp = snapshot["timestamp"].replace(":", "-").replace(" ", "_")
    filename = f"reporte_{timestamp}.html"
    filepath = os.path.join(REPORTES_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    return filepath

import webbrowser
from tkinter import messagebox, simpledialog, Tk, Listbox, Button, SINGLE

def abrir_reportes_nube():
    username_data = cargar_config().get("username")
    username = username_data[0] if isinstance(username_data, list) else username_data
    if not username: return
    try:
        response = supabase.storage.from_('prismov-reportes').list(f'reportes/{username}')
        root = Tk()
        root.title(f"Logs de {username}")
        lista = Listbox(root, width=60, height=15, selectmode=SINGLE)
        lista.pack(padx=20, pady=20)
        
        for item in response:
            if item['name'] != '.emptyFolderPlaceholder': lista.insert('end', item['name'])
        
        def ver_en_browser():
            if lista.curselection():
                archivo = lista.get(lista.curselection()[0])
                # Usamos la URL pública de Supabase
                url = f"{SUPABASE_URL}/storage/v1/object/public/prismov-reportes/reportes/{username}/{archivo}"
                webbrowser.open(url)

        Button(root, text="Visualizar en Navegador", command=ver_en_browser, bg="#764ba2", fg="white").pack(pady=10)
        root.mainloop()
    except Exception as e: print(f"Error al listar: {e}")

def generar_vista_previa_html(contenido_log, nombre_archivo):
    html_template = f"""
    <html>
    <head>
        <title>Log: {nombre_archivo}</title>
        <style>
            body {{ background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace; padding: 20px; }}
            .container {{ border-left: 3px solid #007acc; padding-left: 15px; white-space: pre-wrap; }}
            h2 {{ color: #569cd6; border-bottom: 1px solid #333; padding-bottom: 10px; }}
        </style>
    </head>
    <body>
        <h2>Vista de Log: {nombre_archivo}</h2>
        <div class="container">{contenido_log}</div>
    </body>
    </html>
    """
    # Guardar temporalmente y abrir
    with open("temp_log.html", "w", encoding="utf-8") as f:
        f.write(html_template)
    
    webbrowser.open('file://' + os.path.realpath("temp_log.html"))

def abrir_reporte(filepath):
    """Abre el reporte en el navegador por defecto"""
    try:
        webbrowser.open(f"file:///{filepath.replace(chr(92), '/')}")
        return True
    except:
        return False

# ============================================================
# EJECUTAR ANÁLISIS
# ============================================================

def ejecutar_analisis(historial):
    """Ejecuta un análisis completo y genera reporte"""
    print("🔥 DEBUG → entrando en ejecutar_analisis")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    procesos = analizar_procesos()

    # Snapshot base REAL
    snapshot_base = {
        "cpu_percent": cpu,
        "ram_percent": ram,
        "procesos": procesos
    }

    # Análisis avanzado con datos reales
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

    # Guardar reporte HTML
    filepath_reporte = guardar_reporte(snapshot)

    # Enviar a Telegram si está configurado
    if telegram_configurado():
        # Crear mensaje resumido para Telegram
        a = snapshot["analisis_avanzado"]
        mensaje = f"""
📊 *PRISMOV - Informe Rápido*
📅 {snapshot["timestamp"]}

🖥 *Recursos*
• CPU: {snapshot["cpu_percent"]:.1f}%
• RAM: {snapshot["ram_percent"]:.1f}%

📈 *Tendencias*
• CPU: {a["tendencias"]["cpu"]}
• RAM: {a["tendencias"]["ram"]}

⚠️ *Riesgo: {a["score_detallado"]["riesgo_sistema"]}*

💾 Reporte completo guardado localmente.
        """
        enviar_telegram(mensaje)

        # Subir a Supabase si está activado
    if supabase_configurado():
        print("🔥 DEBUG → supabase_configurado =", supabase_configurado())
        exito = subir_snapshot_a_storage(snapshot)
        if exito:
            print("✔ Reporte subido a Supabase.")
           
        else:
            print("❌ Error al subir reporte a Supabase.")
    return filepath_reporte



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
        print("4) Registrarse")
        print("5) Iniciar sesión")
        print("6) Salir")
        


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
            registrar_usuario()

        elif opcion == "5":
            login_usuario()
        
        elif opcion == "6":
            print("Saliendo...")
            break


        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()
