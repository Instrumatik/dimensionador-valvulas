"""Ventana de activación: pide el código de licencia y muestra los términos de la demo."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout)

from .. import licencia as L
from .. import entregables as E


class DialogoActivacion(QDialog):
    def __init__(self, motivo: str = "", parent=None, carpeta: str | None = None):
        super().__init__(parent)
        self.carpeta = carpeta
        self.verificacion: L.Verificacion | None = None
        self.setWindowTitle(f"Activar {E.PRODUCTO}")
        self.resize(620, 520)
        lay = QVBoxLayout(self)
        t = QLabel(f"<h3>{E.PRODUCTO} — {E.EMPRESA}</h3>"
                   "Pegue el código de licencia que recibió (comienza con «VS1-»).")
        t.setWordWrap(True)
        lay.addWidget(t)
        self.lbl_motivo = QLabel(motivo)
        self.lbl_motivo.setWordWrap(True)
        self.lbl_motivo.setStyleSheet("color:#c0392b")
        self.lbl_motivo.setVisible(bool(motivo))
        lay.addWidget(self.lbl_motivo)
        self.ed_codigo = QPlainTextEdit()
        self.ed_codigo.setPlaceholderText("VS1-XXXXXX-XXXXXX-…")
        self.ed_codigo.setFixedHeight(90)
        lay.addWidget(self.ed_codigo)
        lay.addWidget(QLabel("<b>Términos de la versión de demostración</b>"))
        terminos = QLabel(L.TERMINOS_DEMO)
        terminos.setWordWrap(True)
        terminos.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(terminos)
        self.chk = QCheckBox("Acepto los términos")
        lay.addWidget(self.chk)
        lay.addStretch(1)
        bb = QDialogButtonBox()
        self.btn_activar = bb.addButton("Activar", QDialogButtonBox.AcceptRole)
        bb.addButton("Salir", QDialogButtonBox.RejectRole)
        bb.accepted.connect(self.activar)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def activar(self):
        codigo = self.ed_codigo.toPlainText()
        v = L.verificar(codigo, carpeta=self.carpeta)
        if v.licencia is not None and v.licencia.es_demo and not self.chk.isChecked():
            self._error("Para usar la demo debe aceptar los términos.")
            return
        v = L.activar(codigo, carpeta=self.carpeta) if v.ok else v
        if not v.ok:
            self._error(v.motivo)
            return
        self.verificacion = v
        self.accept()

    def _error(self, texto):
        self.lbl_motivo.setText(texto)
        self.lbl_motivo.setVisible(True)


def obtener_licencia(carpeta: str | None = None) -> L.Licencia | None:
    """Licencia vigente guardada en el equipo o, si no hay, la que el usuario active ahora."""
    guardado = L.guardada(carpeta)
    motivo = ""
    if guardado:
        v = L.activar(guardado, carpeta=carpeta)   # renueva la fecha de último uso
        if v.ok:
            return v.licencia
        motivo = v.motivo
    dlg = DialogoActivacion(motivo, carpeta=carpeta)
    if dlg.exec() == QDialog.Accepted:
        return dlg.verificacion.licencia
    return None
