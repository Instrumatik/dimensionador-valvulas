"""Estilo animado de los botones: cambio de color al pasar el cursor y al pulsar, y brillo en «Calcular»."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPropertyAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QPushButton

# Regla general para todos los botones de la ventana (los «Ver» y los de cada solapa la heredan)
ESTILO_GENERAL = """
QPushButton { border:1px solid #b9c6d6; border-radius:4px; background:#f6f8fb; color:#0d3b66; padding:3px 10px; }
QPushButton:hover { background:#dcebfb; border-color:#2f6fb0; color:#0d3b66; }
QPushButton:pressed { background:#2f6fb0; border-color:#1d4f86; color:white; padding-top:4px; padding-bottom:2px; }
QPushButton:disabled { background:#eef0f3; border-color:#d5dbe2; color:#9aa5b1; }
"""

_CALCULAR = {
    # fondo, texto, fondo al pasar el cursor, fondo al pulsar, texto al pulsar
    "amarillo": ("#f5b700", "#0d3b66", "#ffc933", "#c99600", "#0d3b66"),
    "azul": ("#0d3b66", "#ffffff", "#1d5a96", "#082641", "#ffffff"),
}


class _Brillo(QObject):
    """Halo animado alrededor del botón mientras el cursor está encima (efecto de leve agrandado)."""

    def __init__(self, boton: QPushButton, color: str):
        super().__init__(boton)
        self.sombra = QGraphicsDropShadowEffect(boton)
        self.sombra.setOffset(0, 0)
        self.sombra.setColor(QColor(color))
        self.sombra.setBlurRadius(0)
        boton.setGraphicsEffect(self.sombra)
        self.anim = QPropertyAnimation(self.sombra, b"blurRadius", self)
        self.anim.setDuration(160)
        boton.installEventFilter(self)

    def _a(self, fin: float):
        self.anim.stop()
        self.anim.setStartValue(self.sombra.blurRadius())
        self.anim.setEndValue(fin)
        self.anim.start()

    def eventFilter(self, obj, ev):
        t = ev.type()
        if t == QEvent.Enter:
            self._a(18)
        elif t == QEvent.Leave:
            self._a(0)
        elif t == QEvent.MouseButtonPress:
            self._a(6)
        elif t == QEvent.MouseButtonRelease:
            self._a(18 if obj.underMouse() else 0)
        return False


def calcular(boton: QPushButton, color: str = "amarillo", padding: str = "6px 18px"):
    """Botón «Calcular» destacado: colores con buen contraste, borde que crece al pasar el cursor y halo."""
    f, t, fh, fp, tp = _CALCULAR[color]
    boton.setStyleSheet(
        f"QPushButton{{background:{f};color:{t};font-weight:800;padding:{padding};border-radius:5px;"
        f"border:2px solid {f}}}"
        f"QPushButton:hover{{background:{fh};color:{t};border:2px solid #ffffff}}"
        f"QPushButton:pressed{{background:{fp};color:{tp};border:2px solid {fp};padding-top:7px;padding-bottom:5px}}")
    _Brillo(boton, "#f5b700" if color == "amarillo" else "#2f6fb0")
    return boton
