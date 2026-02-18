import sys
import threading
import os
import glob
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QLabel, QMessageBox, QDialog, QCheckBox,
    QHBoxLayout, QTimeEdit, QSpinBox, QGridLayout
)
from PyQt5.QtCore import Qt, QTime
import prismov


# ============================================================
# VENTANA DE CONFIGURACIÓN DE PROGRAMACIÓN
# ============================================================

class VentanaProgramacion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar programación - RA: Criterio 5b) Ciclo de vida del dato")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Selecciona los días:"))
        dias_layout = QGridLayout()

        self.dias_check = {}
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

        for i, d in enumerate(dias):
            chk = QCheckBox(d.capitalize())
            self.dias_check[d] = chk
            dias_layout.addWidget(chk, i // 2, i % 2)

        layout.addLayout(dias_layout)

        layout.addWidget(QLabel("Hora de inicio:"))
        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setDisplayFormat("HH:mm")
        layout.addWidget(self.hora_inicio)

        layout.addWidget(QLabel("Hora de fin:"))
        self.hora_fin = QTimeEdit()
        self.hora_fin.setDisplayFormat("HH:mm")
        layout.addWidget(self.hora_fin)

        layout.addWidget(QLabel("Intervalo (minutos):"))
        self.intervalo = QSpinBox()
        self.intervalo.setRange(1, 1440)
        layout.addWidget(self.intervalo)

        btn_guardar = QPushButton("Guardar programación")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)

        self.setLayout(layout)
        self.cargar_programacion()

    def cargar_programacion(self):
        prog = prismov.cargar_programacion()

        for d in prog["dias"]:
            if d in self.dias_check:
                self.dias_check[d].setChecked(True)

        self.hora_inicio.setTime(QTime.fromString(prog["hora_inicio"], "HH:mm"))
        self.hora_fin.setTime(QTime.fromString(prog["hora_fin"], "HH:mm"))
        self.intervalo.setValue(prog["intervalo_minutos"])

    def guardar(self):
        dias = [d for d, chk in self.dias_check.items() if chk.isChecked()]

        nueva_prog = {
            "activo": True,
            "dias": dias,
            "hora_inicio": self.hora_inicio.time().toString("HH:mm"),
            "hora_fin": self.hora_fin.time().toString("HH:mm"),
            "intervalo_minutos": self.intervalo.value()
        }

        prismov.guardar_programacion(nueva_prog)
        QMessageBox.information(self, "Guardado", "Programación guardada correctamente.")
        self.close()


# ============================================================
# GUI PRINCIPAL
# ============================================================

class PrismovGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PRISMOV - Monitorización del Sistema")
        self.setGeometry(200, 200, 600, 500)

        self.dark_mode = False

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Botón explicación RA
        self.btn_explicar = QPushButton("📚 Explicación de RA")
        self.btn_explicar.clicked.connect(self.mostrar_explicacion_ra)
        self.btn_explicar.setObjectName("btnExplicar")
        self.btn_explicar.setToolTip("Muestra por qué cada parte del programa cumple los criterios RA.")
        layout.addWidget(self.btn_explicar)

        # Modo oscuro
        self.chk_dark = QCheckBox("Modo oscuro")
        self.chk_dark.stateChanged.connect(self.toggle_dark_mode)
        self.chk_dark.setToolTip("Activa o desactiva el modo oscuro.")
        layout.addWidget(self.chk_dark)

        # Sección Telegram
        self.info_telegram = QLabel("📱 TELEGRAM (Opcional pero recomendado)")
        self.info_telegram.setObjectName("infoTelegram")
        self.info_telegram.setAlignment(Qt.AlignCenter)
        self.info_telegram.setToolTip("Permite vincular tu bot de Telegram para recibir reportes.")
        layout.addWidget(self.info_telegram)

        codigo = prismov.cargar_codigo_vinculacion()
        self.codigo_label = QLabel(f"📝 TU CÓDIGO DE VINCULACIÓN:\n{codigo}")
        self.codigo_label.setObjectName("instr")
        self.codigo_label.setAlignment(Qt.AlignCenter)
        self.codigo_label.setToolTip("Código que debes enviar al bot para vincular tu cuenta.")
        layout.addWidget(self.codigo_label)

        self.btn_nuevo_codigo = QPushButton("🔄 Generar nuevo código")
        self.btn_nuevo_codigo.clicked.connect(self.generar_nuevo_codigo)
        self.btn_nuevo_codigo.setToolTip("Genera un nuevo código de vinculación.")
        layout.addWidget(self.btn_nuevo_codigo)

        self.instruccion = QLabel(
            "Pasos para configurar:\n"
            "1. Abre @PrisMovBot\n"
            "2. Envíale el código\n"
            "3. Pulsa 'Configurar Telegram'"
        )
        self.instruccion.setObjectName("instr")
        self.instruccion.setToolTip("Guía rápida para vincular Telegram.")
        layout.addWidget(self.instruccion)

        self.ra_telegram = QLabel("RA: 5i) Seguridad y regulación de datos")
        self.ra_telegram.setObjectName("raLabel")
        layout.addWidget(self.ra_telegram)

        self.btn_telegram = QPushButton("⚙️ Configurar Telegram")
        self.btn_telegram.clicked.connect(self.configurar_telegram)
        self.btn_telegram.setObjectName("btnTelegram")
        self.btn_telegram.setToolTip("Vincula Telegram para recibir reportes y alertas.")
        layout.addWidget(self.btn_telegram)

        self.btn_logout = QPushButton("🚪 Cerrar sesión Telegram")
        self.btn_logout.clicked.connect(self.logout_telegram)
        self.btn_logout.setObjectName("btnLogout")
        self.btn_logout.setToolTip("Desvincula Telegram eliminando el chat_id.")
        layout.addWidget(self.btn_logout)

        # Análisis inmediato
        self.ra_analisis = QLabel("RA: 2e) Implicación THD en negocio y planta")
        self.ra_analisis.setObjectName("raLabel")
        layout.addWidget(self.ra_analisis)

        self.btn_analizar = QPushButton("📊 Ejecutar análisis ahora")
        self.btn_analizar.clicked.connect(self.ejecutar_analisis)
        self.btn_analizar.setObjectName("btnAnalizar")
        self.btn_analizar.setToolTip("Realiza un análisis inmediato y genera un informe.")
        layout.addWidget(self.btn_analizar)

        # Abrir reporte
        self.ra_reporte = QLabel("RA: 2g) Informe THD")
        self.ra_reporte.setObjectName("raLabel")
        layout.addWidget(self.ra_reporte)

        self.btn_abrir_reporte = QPushButton("📄 Abrir último reporte")
        self.btn_abrir_reporte.clicked.connect(self.abrir_reporte)
        self.btn_abrir_reporte.setObjectName("btnReporte")
        self.btn_abrir_reporte.setToolTip("Abre el informe más reciente generado por el sistema.")
        layout.addWidget(self.btn_abrir_reporte)

        # Modo automático
        self.ra_auto = QLabel("RA: 5f) Almacenaje en la nube")
        self.ra_auto.setObjectName("raLabel")
        layout.addWidget(self.ra_auto)

        self.btn_auto = QPushButton("Iniciar modo automático")
        self.btn_auto.clicked.connect(self.iniciar_modo_automatico)
        self.btn_auto.setObjectName("btnAuto")
        self.btn_auto.setToolTip("Ejecuta análisis periódicos automáticamente.")
        layout.addWidget(self.btn_auto)

        # Programación
        self.ra_prog = QLabel("RA: 5b) Ciclo de vida del dato")
        self.ra_prog.setObjectName("raLabel")
        layout.addWidget(self.ra_prog)

        self.btn_prog = QPushButton("Configurar programación")
        self.btn_prog.clicked.connect(self.abrir_programacion)
        self.btn_prog.setObjectName("btnProg")
        self.btn_prog.setToolTip("Configura días, horas e intervalos del análisis automático.")
        layout.addWidget(self.btn_prog)

        # Área de texto
        self.texto = QTextEdit()
        self.texto.setReadOnly(True)
        self.texto.setToolTip("Aquí se muestran mensajes, reportes y estados del sistema.")
        layout.addWidget(self.texto)

        self.setLayout(layout)

        self.historial = prismov.cargar_historial()
        self.auto_thread = None
        self.auto_activo = False

        self.update_telegram_status()
        self.apply_theme()

    # ============================================================
    # ESTILO PROFESIONAL + ANIMACIONES
    # ============================================================

    def apply_theme(self):
        if self.dark_mode:
            bg = "#1f1f1f"
            fg = "#f5f5f5"
            card = "#2b2b2b"
            accent = "#4a90e2"
            border = "#3a3a3a"
            shadow = "rgba(0,0,0,0.6)"
        else:
            bg = "#f4f6f9"
            fg = "#222"
            card = "#ffffff"
            accent = "#4a90e2"
            border = "#d0d0d0"
            shadow = "rgba(0,0,0,0.25)"

        stylesheet = f"""
            QWidget {{
                background-color: {bg};
                color: {fg};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
            }}

            QTextEdit {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 8px;
            }}

            QLabel#infoTelegram, QLabel#instr {{
                background-color: {card};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 10px;
            }}

            QLabel#raLabel {{
                font-style: italic;
                padding: 4px;
            }}

            QPushButton {{
                background-color: {card};
                border: 2px solid {border};
                border-radius: 18px;
                padding: 10px 18px;
                font-weight: bold;
                color: {fg};
                transition: all 200ms ease-in-out;
            }}

            QPushButton:hover {{
                background-color: {accent};
                color: white;
                border: 2px solid {accent};
                transform: scale(1.05);
                box-shadow: 0px 4px 12px {shadow};
            }}

            QPushButton#btnLogout {{
                background-color: #d9534f;
                color: white;
                border: none;
            }}

            QPushButton#btnLogout:hover {{
                background-color: #c9302c;
                transform: scale(1.05);
                box-shadow: 0px 4px 12px {shadow};
            }}
        """

        self.setStyleSheet(stylesheet)

    def toggle_dark_mode(self):
        self.dark_mode = self.chk_dark.isChecked()
        self.apply_theme()

    # ============================================================
    # EXPLICACIÓN RA (VENTANA COMPLETA)
    # ============================================================

    def mostrar_explicacion_ra(self):
        texto = (
            "📘 **EXPLICACIÓN DE CUMPLIMIENTO DE RA**\n\n"
            "🔹 **RA 5b – Ciclo de vida del dato**\n"
            "La programación permite definir cuándo se generan datos, cómo se almacenan y cuándo se procesan.\n\n"
            "🔹 **RA 5f – Almacenaje en la nube**\n"
            "El modo automático simula almacenamiento periódico de datos y reportes.\n\n"
            "🔹 **RA 5i – Seguridad y regulación**\n"
            "La vinculación con Telegram usa códigos únicos y permite cerrar sesión para proteger datos.\n\n"
            "🔹 **RA 2e – Implicación THD en negocio y planta**\n"
            "El análisis evalúa el rendimiento y genera conclusiones útiles para ambos entornos.\n\n"
            "🔹 **RA 2g – Informe THD**\n"
            "Los reportes HTML relacionan tecnologías con sus áreas de aplicación.\n"
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Explicación de RA")
        v = QVBoxLayout(dialog)

        label = QTextEdit()
        label.setReadOnly(True)
        label.setText(texto)
        v.addWidget(label)

        btn = QPushButton("Cerrar")
        btn.clicked.connect(dialog.accept)
        v.addWidget(btn)

        dialog.exec_()

    # ============================================================
    # LÓGICA (SIN CAMBIOS)
    # ============================================================

    def ejecutar_analisis(self):
        try:
            filepath_reporte = prismov.ejecutar_analisis(self.historial)
            self.ultima_ruta_reporte = filepath_reporte

            self.texto.append("✔ Análisis ejecutado correctamente.\n")
            self.texto.append("RA: 2e) Implicación THD\n")
            self.texto.append(f"📄 Reporte guardado: {filepath_reporte}\n")

            if QMessageBox.question(self, "✔ Análisis Completado",
                                    "¿Deseas abrir el reporte?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                prismov.abrir_reporte(filepath_reporte)

        except Exception as e:
            self.mostrar_error(e)

    def abrir_reporte(self):
        try:
            if hasattr(self, 'ultima_ruta_reporte'):
                prismov.abrir_reporte(self.ultima_ruta_reporte)
                return

            reportes = glob.glob(os.path.join(prismov.REPORTES_DIR, "*.html"))
            if reportes:
                reporte_reciente = max(reportes, key=os.path.getctime)
                prismov.abrir_reporte(reporte_reciente)
                self.ultima_ruta_reporte = reporte_reciente
            else:
                QMessageBox.warning(self, "Error", "No hay reportes generados.")

        except Exception as e:
            self.mostrar_error(e)

    def configurar_telegram(self):
        chat_id, codigo_valido = prismov.obtener_chat_id_y_validar_codigo()
        self.texto.append("RA: 5i) Seguridad de datos\n")

        if codigo_valido and chat_id:
            prismov.guardar_chat_id(chat_id)
            QMessageBox.information(self, "✔ Telegram Configurado",
                                    f"Chat ID: {chat_id}")
            self.update_telegram_status()
        else:
            QMessageBox.warning(self, "❌ Error",
                                "Código incorrecto o no detectado.")
            self.texto.append("❌ Código incorrecto.\n")

    def generar_nuevo_codigo(self):
        nuevo_codigo = prismov.generar_nuevo_codigo()
        QMessageBox.information(self, "✔ Nuevo código generado",
                                f"Tu nuevo código es:\n\n{nuevo_codigo}")
        self.codigo_label.setText(f"📝 TU CÓDIGO DE VINCULACIÓN:\n{nuevo_codigo}")

    def refresh_telegram_section(self):
        if prismov.telegram_configurado():
            self.info_telegram.hide()
            self.codigo_label.hide()
            self.btn_nuevo_codigo.hide()
            self.instruccion.hide()
            self.btn_logout.show()
        else:
            self.info_telegram.show()
            self.codigo_label.show()
            self.btn_nuevo_codigo.show()
            self.instruccion.show()
            self.btn_logout.hide()

    def update_telegram_status(self):
        if prismov.telegram_configurado():
            self.btn_telegram.setText("✔ Telegram Configurado")
        else:
            self.btn_telegram.setText("⚙️ Configurar Telegram")

        self.refresh_telegram_section()

    def logout_telegram(self):
        prismov.borrar_chat_id()
        QMessageBox.information(self, "✔ Sesión cerrada", "Telegram desconectado.")
        self.update_telegram_status()

    def iniciar_modo_automatico(self):
        if self.auto_activo:
            QMessageBox.information(self, "Modo automático", "Ya está en ejecución.")
            return

        self.auto_activo = True
        self.texto.append("⏳ Modo automático iniciado...\n")

        self.auto_thread = threading.Thread(target=self.loop_automatico, daemon=True)
        self.auto_thread.start()

    def loop_automatico(self):
        while self.auto_activo:
            try:
                filepath_reporte = prismov.ejecutar_analisis(self.historial)
                self.ultima_ruta_reporte = filepath_reporte
                self.texto.append("✔ Análisis automático ejecutado.\n")
            except Exception as e:
                self.texto.append(f"❌ Error: {str(e)}\n")

            prog = prismov.cargar_programacion()
            intervalo = prog.get("intervalo_minutos", 60)
            prismov.time.sleep(intervalo * 60)

    def abrir_programacion(self):
        ventana = VentanaProgramacion(self)
        ventana.exec_()

    def mostrar_error(self, error):
        QMessageBox.critical(self, "Error", str(error))
        self.texto.append(f"❌ Error: {str(error)}\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PrismovGUI()
    ventana.show()
    sys.exit(app.exec_())
