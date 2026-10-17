"""Generador de códigos de licencia de Valveselect-N25 (uso exclusivo de INSTRUMATIK S.A.S.).

Necesita el archivo de clave privada (clave_privada_valveselect.pem). Cada código generado se
anota en «registro_codigos.csv», en la misma carpeta que la clave.
"""
import csv
import os
import secrets
import sys
from datetime import date, timedelta

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from dimensionador import licencia as L


class Generador(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de códigos · Valveselect-N25")
        self.resize(640, 560)
        self.cfg = QSettings("INSTRUMATIK", "Generador-Valveselect")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        fila = QHBoxLayout()
        self.ed_clave = QLineEdit(self.cfg.value("clave", ""))
        self.ed_clave.setPlaceholderText("Archivo clave_privada_valveselect.pem")
        b = QPushButton("Buscar…")
        b.clicked.connect(self._buscar_clave)
        fila.addWidget(self.ed_clave)
        fila.addWidget(b)
        form.addRow("Clave privada", fila)
        self.ed_nombre = QLineEdit()
        self.ed_empresa = QLineEdit()
        self.cb_tipo = QComboBox()
        for k, t in L.NOMBRE_TIPO.items():
            self.cb_tipo.addItem(t, k)
        self.cb_tipo.currentIndexChanged.connect(self._cambio_tipo)
        self.sp_dias = QSpinBox()
        self.sp_dias.setRange(1, 3650)
        self.sp_dias.setSuffix(" días")
        self.de_emision = QDateEdit(QDate.currentDate())
        self.de_emision.setCalendarPopup(True)
        self.de_emision.setDisplayFormat("dd/MM/yyyy")
        self.ed_contacto = QLineEdit(self.cfg.value("contacto", ""))
        self.ed_contacto.setPlaceholderText("Correo para comentarios de los usuarios")
        form.addRow("Nombre del usuario", self.ed_nombre)
        form.addRow("Empresa", self.ed_empresa)
        form.addRow("Tipo de licencia", self.cb_tipo)
        form.addRow("Validez", self.sp_dias)
        form.addRow("Fecha de emisión", self.de_emision)
        form.addRow("Contacto", self.ed_contacto)
        lay.addLayout(form)
        b = QPushButton("Generar código")
        b.clicked.connect(self.generar)
        lay.addWidget(b)
        lay.addWidget(QLabel("Mensaje para enviar al usuario:"))
        self.txt = QPlainTextEdit()
        self.txt.setReadOnly(True)
        lay.addWidget(self.txt)
        b = QPushButton("Copiar mensaje")
        b.clicked.connect(lambda: QApplication.clipboard().setText(self.txt.toPlainText()))
        lay.addWidget(b)
        self._cambio_tipo()

    def _cambio_tipo(self):
        dias = L.DIAS_TIPO[self.cb_tipo.currentData()]
        self.sp_dias.setEnabled(dias is not None)
        if dias:
            self.sp_dias.setValue(dias)

    def _buscar_clave(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Clave privada", "", "Clave (*.pem)")
        if ruta:
            self.ed_clave.setText(ruta)

    def generar(self):
        ruta = self.ed_clave.text().strip()
        nombre = self.ed_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Falta el nombre", "Ingrese el nombre del usuario.")
            return
        try:
            with open(ruta, "rb") as f:
                clave = L.cargar_clave_privada(f.read())
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "Clave privada", f"No se pudo leer la clave privada:\n{e}")
            return
        tipo = self.cb_tipo.currentData()
        emision = self.de_emision.date().toPython()
        vence = None if L.DIAS_TIPO[tipo] is None else emision + timedelta(days=self.sp_dias.value())
        lic = L.Licencia(tipo, nombre, self.ed_empresa.text().strip(), self.ed_contacto.text().strip(),
                         emision, vence, secrets.randbits(32))
        codigo = L.firmar(lic, clave)
        L.leer(codigo, clave.public_key())   # verificación de ida y vuelta
        self.cfg.setValue("clave", ruta)
        self.cfg.setValue("contacto", lic.contacto)
        registro = os.path.join(os.path.dirname(ruta), "registro_codigos.csv")
        nuevo = not os.path.exists(registro)
        with open(registro, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            if nuevo:
                w.writerow(["Fecha", "Id", "Tipo", "Nombre", "Empresa", "Vence", "Código"])
            w.writerow([date.today().isoformat(), lic.id, L.NOMBRE_TIPO[tipo], lic.nombre, lic.empresa,
                        vence.isoformat() if vence else "sin vencimiento", codigo])
        hasta = f"hasta el {vence:%d/%m/%Y}" if vence else "sin vencimiento"
        self.txt.setPlainText(
            f"Hola {nombre}:\n\n"
            f"Este es tu código de {L.NOMBRE_TIPO[tipo].lower()} de Valveselect-N25, válido {hasta}:\n\n"
            f"{codigo}\n\n"
            "Al abrir el programa por primera vez, pega el código completo en la ventana de activación.\n"
            + ("Los documentos que generes llevarán una marca de agua de demostración. "
               "Tus comentarios nos ayudan a validar el software: puedes enviarlos desde "
               "Ayuda > Enviar comentarios.\n" if tipo == "demo" else "")
            + "\nINSTRUMATIK S.A.S.")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    g = Generador()
    g.show()
    if "--prueba-gui" in sys.argv:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
