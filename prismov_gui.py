import sys
import threading
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

        # Botón de análisis
        self.btn_analizar = QPushButton("Ejecutar análisis ahora")
        self.btn_analizar.clicked.connect(self.ejecutar_analisis)
        layout.addWidget(self.btn_analizar)

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

    # ---------------------------------------------------------
    # EJECUTAR ANÁLISIS
    # ---------------------------------------------------------
    def ejecutar_analisis(self):
        try:
            prismov.ejecutar_analisis(self.historial)
            self.texto.append("✔ Análisis ejecutado correctamente.\n")
        except Exception as e:
            self.mostrar_error(e)

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
                prismov.ejecutar_analisis(self.historial)
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
