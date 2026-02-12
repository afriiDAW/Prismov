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
        self.setWindowTitle("Configurar programación")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()

        # Días de la semana
        layout.addWidget(QLabel("Selecciona los días:"))
        dias_layout = QGridLayout()

        self.dias_check = {}
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

        for i, d in enumerate(dias):
            chk = QCheckBox(d.capitalize())
            self.dias_check[d] = chk
            dias_layout.addWidget(chk, i // 2, i % 2)

        layout.addLayout(dias_layout)

        # Hora inicio
        layout.addWidget(QLabel("Hora de inicio:"))
        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setDisplayFormat("HH:mm")
        layout.addWidget(self.hora_inicio)

        # Hora fin
        layout.addWidget(QLabel("Hora de fin:"))
        self.hora_fin = QTimeEdit()
        self.hora_fin.setDisplayFormat("HH:mm")
        layout.addWidget(self.hora_fin)

        # Intervalo
        layout.addWidget(QLabel("Intervalo (minutos):"))
        self.intervalo = QSpinBox()
        self.intervalo.setRange(1, 1440)
        layout.addWidget(self.intervalo)

        # Botón guardar
        btn_guardar = QPushButton("Guardar programación")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)

        self.setLayout(layout)

        # Cargar valores actuales
        self.cargar_programacion()

    def cargar_programacion(self):
        prog = prismov.cargar_programacion()

        for d in prog["dias"]:
            if d in self.dias_check:
                self.dias_check[d].setChecked(True)

        h_ini = QTime.fromString(prog["hora_inicio"], "HH:mm")
        h_fin = QTime.fromString(prog["hora_fin"], "HH:mm")

        self.hora_inicio.setTime(h_ini)
        self.hora_fin.setTime(h_fin)
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

        layout = QVBoxLayout()

        # Título
        titulo = QLabel("PRISMOV - Sistema de Análisis")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(titulo)

        # Verificar si Telegram está configurado
        if not prismov.telegram_configurado():
            self.info_telegram = QLabel("📱 TELEGRAM (Opcional pero recomendado)")
            self.info_telegram.setStyleSheet("color: #FF9800; font-weight: bold; padding: 10px; background-color: #FFF3E0;")
            self.info_telegram.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.info_telegram)

            # Mostrar código de vinculación
            codigo = prismov.cargar_codigo_vinculacion()
            self.codigo_label = QLabel(f"📝 TU CÓDIGO DE VINCULACIÓN:\n{codigo}")
            self.codigo_label.setStyleSheet("padding: 10px; background-color: #e7f3ff; border: 2px solid #0066cc; font-weight: bold; font-size: 14px;")
            self.codigo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.codigo_label)

            # Botón para generar nuevo código
            self.btn_nuevo_codigo = QPushButton("🔄 Generar nuevo código")
            self.btn_nuevo_codigo.clicked.connect(self.generar_nuevo_codigo)
            self.btn_nuevo_codigo.setStyleSheet("padding: 5px;")
            layout.addWidget(self.btn_nuevo_codigo)

            self.instruccion = QLabel(
                "Pasos para configurar (opcional):\n"
                "1. Abre tu bot en Telegram (@PrisMovBot)\n"
                "2. Envíale el código de arriba (ej: ABC123)\n"
                "3. Haz clic en 'Configurar Telegram'\n\n"
                "Los reportes análisis se guardan localmente\ny pueden verse aquí sin Telegram."
            )
            self.instruccion.setStyleSheet("padding: 10px; background-color: #FFF3E0; border: 1px solid #FF9800;")
            layout.addWidget(self.instruccion)

        # Botón configurar Telegram
        self.btn_telegram = QPushButton("⚙️ Configurar Telegram")
        self.btn_telegram.clicked.connect(self.configurar_telegram)
        self.btn_telegram.setStyleSheet("padding: 10px; font-weight: bold;")
        layout.addWidget(self.btn_telegram)

        # Botón de análisis
        self.btn_analizar = QPushButton("📊 Ejecutar análisis ahora")
        self.btn_analizar.clicked.connect(self.ejecutar_analisis)
        self.btn_analizar.setStyleSheet("padding: 10px; font-weight: bold; background-color: #4CAF50; color: white;")
        layout.addWidget(self.btn_analizar)

        # Botón abrir último reporte
        self.btn_abrir_reporte = QPushButton("📄 Abrir último reporte")
        self.btn_abrir_reporte.clicked.connect(self.abrir_reporte)
        self.btn_abrir_reporte.setStyleSheet("padding: 10px; font-weight: bold; background-color: #2196F3; color: white;")
        layout.addWidget(self.btn_abrir_reporte)

        # Botón modo automático
        self.btn_auto = QPushButton("Iniciar modo automático")
        self.btn_auto.clicked.connect(self.iniciar_modo_automatico)
        layout.addWidget(self.btn_auto)

        # Botón configuración programación
        self.btn_prog = QPushButton("Configurar programación")
        self.btn_prog.clicked.connect(self.abrir_programacion)
        layout.addWidget(self.btn_prog)

        # Área de texto
        self.texto = QTextEdit()
        self.texto.setReadOnly(True)
        layout.addWidget(self.texto)

        self.setLayout(layout)

        # Cargar historial
        self.historial = prismov.cargar_historial()

        # Hilo del modo automático
        self.auto_thread = None
        self.auto_activo = False
        
        # Inicializar referencias a widgets de Telegram
        if not hasattr(self, 'info_telegram'):
            self.info_telegram = None
        if not hasattr(self, 'codigo_label'):
            self.codigo_label = None
        if not hasattr(self, 'btn_nuevo_codigo'):
            self.btn_nuevo_codigo = None
        if not hasattr(self, 'instruccion'):
            self.instruccion = None
        
        # Actualizar estado de Telegram en el botón
        self.update_telegram_status()

    # ---------------------------------------------------------
    # EJECUTAR ANÁLISIS
    # ---------------------------------------------------------
    def ejecutar_analisis(self):
        try:
            filepath_reporte = prismov.ejecutar_analisis(self.historial)
            self.ultima_ruta_reporte = filepath_reporte
            
            self.texto.append("✔ Análisis ejecutado correctamente.\n")
            self.texto.append(f"📄 Reporte guardado: {filepath_reporte}\n")
            
            # Preguntar si desea abrir el reporte
            respuesta = QMessageBox.question(
                self,
                "✔ Análisis Completado",
                "El análisis se ha completado exitosamente.\n\n¿Deseas abrir el reporte?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                prismov.abrir_reporte(filepath_reporte)
        except Exception as e:
            self.mostrar_error(e)

    def abrir_reporte(self):
        """Abre el último reporte generado"""
        try:
            if hasattr(self, 'ultima_ruta_reporte') and self.ultima_ruta_reporte:
                prismov.abrir_reporte(self.ultima_ruta_reporte)
            else:
                # Buscar el reporte más reciente
                import glob
                reportes = glob.glob(os.path.join(prismov.REPORTES_DIR, "*.html"))
                if reportes:
                    reporte_reciente = max(reportes, key=os.path.getctime)
                    prismov.abrir_reporte(reporte_reciente)
                    self.ultima_ruta_reporte = reporte_reciente
                else:
                    QMessageBox.warning(self, "Error", "No hay reportes generados todavía.\nEjecuta primero un análisis.")
        except Exception as e:
            self.mostrar_error(e)

    # ---------------------------------------------------------
    # CONFIGURAR TELEGRAM
    # ---------------------------------------------------------
    def configurar_telegram(self):
        chat_id, codigo_valido = prismov.obtener_chat_id_y_validar_codigo()
        
        if codigo_valido and chat_id:
            prismov.guardar_chat_id(chat_id)
            QMessageBox.information(
                self,
                "✔ Telegram Configurado",
                f"Telegram se ha configurado correctamente.\nChat ID: {chat_id}\n\nAhora puedes usar todas las funciones."
            )
            self.texto.append(f"✔ Telegram configurado correctamente (Chat ID: {chat_id})\n")
            # Actualizar estado visual sin cerrar la ventana
            self.update_telegram_status()
            # Refrescar la sección de Telegram
            self.refresh_telegram_section()
        else:
            QMessageBox.warning(
                self,
                "❌ Error",
                "El código no coincide o no se pudo detectar el mensaje.\n\nAsegúrate de:\n1. Haber enviado el CÓDIGO EXACTO al bot\n2. El código debe estar en el mensaje\n3. Intentar de nuevo inmediatamente"
            )
            self.texto.append("❌ El código de vinculación no coincide. Intenta de nuevo.\n")

    def generar_nuevo_codigo(self):
        """Genera un nuevo código de vinculación"""
        nuevo_codigo = prismov.generar_nuevo_codigo()
        QMessageBox.information(
            self,
            "✔ Nuevo código generado",
            f"Tu nuevo código de vinculación es:\n\n{nuevo_codigo}\n\nEnvíaselo al bot en Telegram."
        )
        self.texto.append(f"✔ Nuevo código generado: {nuevo_codigo}\n")
        # Actualizar el código mostrado sin cerrar la ventana
        if hasattr(self, 'codigo_label'):
            self.codigo_label.setText(f"📝 TU CÓDIGO DE VINCULACIÓN:\n{nuevo_codigo}")

    def refresh_telegram_section(self):
        """Refresca la sección de Telegram sin cerrar la ventana"""
        # Ocultar todos los widgets de "no configurado" si está configurado
        if prismov.telegram_configurado():
            if hasattr(self, 'codigo_label'):
                self.codigo_label.hide()
            if hasattr(self, 'btn_nuevo_codigo'):
                self.btn_nuevo_codigo.hide()
            if hasattr(self, 'info_telegram'):
                self.info_telegram.hide()
            if hasattr(self, 'instruccion'):
                self.instruccion.hide()

    def update_telegram_status(self):
        """Actualizar estado visual de Telegram"""
        if prismov.telegram_configurado():
            self.btn_telegram.setStyleSheet("padding: 10px; font-weight: bold; background-color: #90EE90;")
            self.btn_telegram.setText("✔ Telegram Configurado")
        else:
            self.btn_telegram.setStyleSheet("padding: 10px; font-weight: bold; background-color: #FFB6C6;")
            self.btn_telegram.setText("⚙️ Configurar Telegram")

    # ---------------------------------------------------------
    # MODO AUTOMÁTICO
    # ---------------------------------------------------------
    def iniciar_modo_automatico(self):
        if self.auto_activo:
            QMessageBox.information(self, "Modo automático", "Ya está en ejecución.")
            return

        self.auto_activo = True
        self.texto.append("⏳ Modo automático iniciado...\n")

        self.auto_thread = threading.Thread(
            target=self.loop_automatico,
            daemon=True
        )
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

    # ---------------------------------------------------------
    # ABRIR CONFIGURACIÓN
    # ---------------------------------------------------------
    def abrir_programacion(self):
        ventana = VentanaProgramacion(self)
        ventana.exec_()

    # ---------------------------------------------------------
    # MOSTRAR ERRORES
    # ---------------------------------------------------------
    def mostrar_error(self, error):
        QMessageBox.critical(self, "Error", str(error))
        self.texto.append(f"❌ Error: {str(error)}\n")


# ---------------------------------------------------------
# MAIN DEL GUI
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PrismovGUI()
    ventana.show()
    sys.exit(app.exec_())
