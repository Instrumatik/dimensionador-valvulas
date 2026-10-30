"""Barra de herramientas rápidas del encabezado y sus ventanas.

Cada botón abre una ventana aparte (no modal, se puede dejar abierta mientras se trabaja) que no toca el
proyecto: conversor de unidades, propiedades de fluidos, tablas de tubería, presión-temperatura por clase,
biblioteca de materiales, calculadoras, enlaces de referencia y contacto con INSTRUMATIK.
"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
                               QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QTabWidget, QToolButton, QVBoxLayout, QWidget)

from .. import asme_b16_34 as B, contacto, herramientas as H, propiedades as P, tuberias as T, unidades as U
from ..entregables import fmt
from . import iconos

# (clave, globo de ayuda, nombre del método de la ventana principal que la abre)
HERRAMIENTAS = (
    ("conversor", "Conversor de unidades"),
    ("fluidos", "Propiedades de fluidos y tablas de vapor"),
    ("tuberia", "Tablas de tubería ASME B36.10M / B36.19M y velocidad"),
    ("rating", "Presión-temperatura por clase ASME B16.34"),
    ("materiales", "Biblioteca de materiales"),
    ("calculadoras", "Calculadoras rápidas: ΔP de bloqueo, caudal de gas, velocidad, Reynolds"),
    ("enlaces", "Enlaces de referencia (editables)"),
)

ESTILO_BOTON = ("QToolButton{background:rgba(255,255,255,0.10);border:1px solid rgba(255,255,255,0.28);"
                "border-radius:5px;padding:3px;} QToolButton:hover{background:rgba(255,255,255,0.28);"
                "border-color:#f5b700;} QToolButton:pressed{background:#f5b700;border-color:#f5b700;}")


def _numero(texto: str) -> float | None:
    t = texto.strip().replace(" ", "")
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def abrir_url(url: str, padre=None) -> bool:
    if QDesktopServices.openUrl(QUrl(url)):
        return True
    QMessageBox.information(padre, "Abrir enlace", f"No se pudo abrir el navegador. Copie la dirección:\n\n{url}")
    return False


# ----------------------------------------------------------------------------- piezas comunes
class Dato(QWidget):
    """Valor con su selector de unidad; ``base()`` lo devuelve en la unidad base de la magnitud."""

    def __init__(self, magnitud: str, unidad: str, valor: str = "", ancho: int = 110):
        super().__init__()
        self.magnitud = magnitud
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        self.edit = QLineEdit(valor)
        self.edit.setFixedWidth(ancho)
        self.unidad = QComboBox()
        self.unidad.addItems(list(H.unidades(magnitud)))
        self.unidad.setCurrentText(unidad)
        h.addWidget(self.edit)
        h.addWidget(self.unidad)
        h.addStretch(1)

    def valor(self) -> float | None:
        return _numero(self.edit.text())

    def base(self, p_atm_kpa: float = U.P_ATM_KPA) -> float | None:
        v = self.valor()
        if v is None:
            return None
        u = H.unidades(self.magnitud)[self.unidad.currentText()]
        if self.magnitud == "presion" and u.manometrica:
            return U.a_base(v, "presion", u.simbolo, p_atm_kpa)
        return u.a_base(v)


def _tabla(columnas: list[str]) -> QTableWidget:
    t = QTableWidget(0, len(columnas))
    t.setHorizontalHeaderLabels(columnas)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setAlternatingRowColors(True)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    t.verticalHeader().setDefaultSectionSize(22)
    return t


def _limpio(v: float, cifras: int = 6) -> str:
    """Número con cifras significativas pero sin ceros sobrantes a la derecha («100» y no «100,000»)."""
    t = fmt(v, cifras)
    if "," in t and "e" not in t:
        t = t.rstrip("0").rstrip(",")
    return t


def _llenar(t: QTableWidget, filas: list[list[str]], derecha=()):
    t.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, txt in enumerate(fila):
            it = QTableWidgetItem(txt)
            if j in derecha:
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            t.setItem(i, j, it)


def _copiar_tabla(t: QTableWidget):
    """Copia la tabla como texto separado por tabulaciones (se pega directo en Excel)."""
    enc = [t.horizontalHeaderItem(j).text() for j in range(t.columnCount())]
    filas = ["\t".join(enc)]
    for i in range(t.rowCount()):
        filas.append("\t".join(t.item(i, j).text() if t.item(i, j) else "" for j in range(t.columnCount())))
    QGuiApplication.clipboard().setText("\n".join(filas))


def _boton_copiar(t: QTableWidget) -> QPushButton:
    b = QPushButton("Copiar tabla")
    b.setToolTip("Copia la tabla para pegarla en Excel o en un informe")
    b.clicked.connect(lambda: _copiar_tabla(t))
    return b


def _nota(texto: str) -> QLabel:
    l = QLabel(texto)
    l.setWordWrap(True)
    l.setStyleSheet("color:#5b6b7c;font-size:8.5pt")
    return l


def _error(texto: str) -> QLabel:
    l = QLabel(texto)
    l.setWordWrap(True)
    l.setStyleSheet("color:#b00020")
    return l


class _Ventana(QDialog):
    def __init__(self, padre, titulo: str, ancho: int, alto: int):
        super().__init__(padre)
        self.setWindowTitle(titulo)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)
        self.resize(ancho, alto)
        self.sistema = getattr(padre, "sistema", "SI") if padre else "SI"

    def un(self, magnitud: str) -> str:
        return U.SISTEMAS[self.sistema][magnitud]


# ----------------------------------------------------------------------------- 1. conversor
class Conversor(_Ventana):
    def __init__(self, padre=None):
        super().__init__(padre, "Conversor de unidades", 640, 520)
        v = QVBoxLayout(self)
        f = QFormLayout()
        self.cb_mag = QComboBox()
        for k, n in H.MAGNITUDES:
            self.cb_mag.addItem(n, k)
        self.ed_valor = QLineEdit("1")
        self.cb_de = QComboBox()
        self.ed_alt = QLineEdit("0")
        self.ed_alt.setToolTip("La altitud fija la presión atmosférica que separa las presiones absolutas de "
                               "las manométricas (atmósfera estándar)")
        self.lb_patm = QLabel()
        fila_alt = QHBoxLayout()
        fila_alt.addWidget(self.ed_alt)
        fila_alt.addWidget(QLabel("m s. n. m."))
        fila_alt.addWidget(self.lb_patm, 1)
        self.w_alt = QWidget()
        self.w_alt.setLayout(fila_alt)
        fila_alt.setContentsMargins(0, 0, 0, 0)
        f.addRow("Magnitud", self.cb_mag)
        f.addRow("Valor", self.ed_valor)
        f.addRow("Unidad", self.cb_de)
        f.addRow("Altitud del sitio", self.w_alt)
        v.addLayout(f)
        self.tabla = _tabla(["Unidad", "Valor", "Nombre"])
        v.addWidget(self.tabla, 1)
        pie = QHBoxLayout()
        pie.addWidget(_nota("Los mismos factores que usa el cálculo. Cv = Kv / 0,865."), 1)
        pie.addWidget(_boton_copiar(self.tabla))
        v.addLayout(pie)
        self.cb_mag.currentIndexChanged.connect(self._magnitud)
        self.cb_de.currentTextChanged.connect(self._calcular)
        self.ed_valor.textChanged.connect(self._calcular)
        self.ed_alt.textChanged.connect(self._calcular)
        self._magnitud()

    def _magnitud(self):
        m = self.cb_mag.currentData()
        self.cb_de.blockSignals(True)
        self.cb_de.clear()
        self.cb_de.addItems(list(H.unidades(m)))
        pref = U.SISTEMAS[self.sistema].get(m)
        if pref and pref in H.unidades(m):
            self.cb_de.setCurrentText(pref)
        self.cb_de.blockSignals(False)
        self.w_alt.setVisible(m == "presion")
        self._calcular()

    def _calcular(self):
        m = self.cb_mag.currentData()
        v = _numero(self.ed_valor.text())
        alt = _numero(self.ed_alt.text()) or 0.0
        patm = H.p_atm_altitud(alt)
        self.lb_patm.setText(f"  P atm = {fmt(patm, 5)} kPa")
        if v is None:
            self.tabla.setRowCount(0)
            return
        try:
            filas = [[s, _limpio(x, 6), n] for s, n, x in H.convertir_todas(v, m, self.cb_de.currentText(), patm)]
        except (ValueError, ZeroDivisionError):
            filas = []
        _llenar(self.tabla, filas, derecha=(1,))


# ----------------------------------------------------------------------------- 2. fluidos
class Fluidos(_Ventana):
    def __init__(self, padre=None):
        super().__init__(padre, "Propiedades de fluidos", 720, 640)
        v = QVBoxLayout(self)
        if not P.DISPONIBLE:
            v.addWidget(_error("La biblioteca de propiedades (CoolProp) no está disponible en esta instalación."))
            return
        f = QFormLayout()
        self.cb_fluido = QComboBox()
        self.cb_fluido.addItems(list(P.FLUIDOS))
        self.cb_modo = QComboBox()
        self.cb_modo.addItems(["Punto: presión y temperatura", "Saturación a la presión dada",
                               "Saturación a la temperatura dada"])
        pr = "bar a" if self.sistema == "SI" else "psia"
        self.d_P = Dato("presion", pr, "10")
        self.d_T = Dato("temperatura", self.un("temperatura"), "150")
        self.cb_salida = QComboBox()
        self.cb_salida.addItems(["SI", "Imperial"])
        self.cb_salida.setCurrentText(self.sistema)
        f.addRow("Fluido", self.cb_fluido)
        f.addRow("Consulta", self.cb_modo)
        f.addRow("Presión", self.d_P)
        f.addRow("Temperatura", self.d_T)
        f.addRow("Unidades del resultado", self.cb_salida)
        v.addLayout(f)
        bt = QHBoxLayout()
        self.btn = QPushButton("Calcular")
        bt.addWidget(self.btn)
        bt.addStretch(1)
        v.addLayout(bt)
        self.msg = _error("")
        v.addWidget(self.msg)
        self.tabla = _tabla(["Propiedad", "Valor", "Unidad"])
        v.addWidget(self.tabla, 1)
        pie = QHBoxLayout()
        pie.addWidget(_nota("CoolProp (licencia MIT); agua y vapor con IAPWS-95. Es la misma biblioteca del cálculo "
                            "de la válvula. El gas natural usa la composición típica del programa."), 1)
        pie.addWidget(_boton_copiar(self.tabla))
        v.addLayout(pie)
        self.btn.clicked.connect(self._calcular)
        self.cb_modo.currentIndexChanged.connect(self._modo)
        self.cb_salida.currentTextChanged.connect(self._calcular)
        self._modo()

    def _modo(self):
        i = self.cb_modo.currentIndex()
        self.d_P.setEnabled(i in (0, 1))
        self.d_T.setEnabled(i in (0, 2))

    def _calcular(self):
        self.msg.setText("")
        i = self.cb_modo.currentIndex()
        fluido = self.cb_fluido.currentText()
        Pk, TK = self.d_P.base(), self.d_T.base()
        try:
            if i == 0:
                if Pk is None or TK is None:
                    raise ValueError("Ingrese la presión y la temperatura.")
                filas = H.propiedades_punto(fluido, Pk, TK)
            elif i == 1:
                if Pk is None:
                    raise ValueError("Ingrese la presión.")
                filas = H.saturacion(fluido, P_kPa=Pk)
            else:
                if TK is None:
                    raise ValueError("Ingrese la temperatura.")
                filas = H.saturacion(fluido, T_K=TK)
        except (ValueError, P.ErrorPropiedades) as e:
            self.msg.setText(str(e))
            self.tabla.setRowCount(0)
            return
        sis = U.SISTEMAS[self.cb_salida.currentText()]
        salida = []
        for p in filas:
            if isinstance(p.valor, str):
                salida.append([p.nombre, p.valor, ""])
            elif p.magnitud:
                u = sis[p.magnitud]
                if p.magnitud == "presion":
                    u = "bar a" if self.cb_salida.currentText() == "SI" else "psia"
                salida.append([p.nombre, fmt(U.desde_base(p.valor, p.magnitud, u), 5), u])
            else:
                salida.append([p.nombre, fmt(p.valor, 5), p.unidad])
        _llenar(self.tabla, salida, derecha=(1,))


# ----------------------------------------------------------------------------- 3. tuberías
class Tuberias(_Ventana):
    def __init__(self, padre=None):
        super().__init__(padre, "Tablas de tubería y velocidad", 860, 680)
        v = QVBoxLayout(self)
        arriba = QHBoxLayout()
        f = QFormLayout()
        self.cb_nps = QComboBox()
        for n in T.NPS:
            self.cb_nps.addItem(f"{T.texto_nps(n)}  ·  DN {T.DN[n]}", n)
        self.cb_nps.setCurrentIndex(T.NPS.index(4))
        self.cb_len = QComboBox()
        self.cb_len.addItems(["mm", "in"])
        self.cb_len.setCurrentText(self.un("longitud"))
        self.d_Q = Dato("caudal_vol", self.un("caudal_vol"))
        self.d_Q.edit.setPlaceholderText("opcional")
        f.addRow("Diámetro nominal", self.cb_nps)
        f.addRow("Unidades de longitud", self.cb_len)
        f.addRow("Caudal real (para la velocidad)", self.d_Q)
        arriba.addLayout(f, 1)
        g = QGroupBox("Diámetro para una velocidad máxima")
        fg = QFormLayout(g)
        self.d_vmax = Dato("velocidad", self.un("velocidad"), "3" if self.sistema == "SI" else "10", 70)
        self.cb_ced = QComboBox()
        self.cb_ced.addItems(T.CEDULAS)
        self.cb_ced.setCurrentText("40")
        self.lb_sug = QLabel("—")
        self.lb_sug.setWordWrap(True)
        fg.addRow("Velocidad máxima", self.d_vmax)
        fg.addRow("Cédula", self.cb_ced)
        fg.addRow("Resultado", self.lb_sug)
        arriba.addWidget(g, 1)
        v.addLayout(arriba)
        self.tabla = _tabla([])
        v.addWidget(self.tabla, 3)
        pie = QHBoxLayout()
        pie.addWidget(_nota(f"{T.REFERENCIA}. Peso del caño vacío de acero al carbono (7 850 kg/m³). "
                            "Las cédulas «S» son de acero inoxidable."), 1)
        pie.addWidget(_boton_copiar(self.tabla))
        v.addLayout(pie)
        g2 = QGroupBox("Velocidades orientativas en tubería (práctica de diseño, no son límites de norma)")
        v2 = QVBoxLayout(g2)
        tv = _tabla(["Servicio", "Velocidad"])
        _llenar(tv, [list(x) for x in H.VELOCIDADES_TIPICAS])
        tv.setMaximumHeight(200)
        v2.addWidget(tv)
        v.addWidget(g2, 2)
        for w in (self.cb_nps, self.cb_len, self.cb_ced, self.d_Q.unidad, self.d_vmax.unidad):
            w.currentIndexChanged.connect(self._calcular)
        for w in (self.d_Q.edit, self.d_vmax.edit):
            w.textChanged.connect(self._calcular)
        self._calcular()

    def _calcular(self):
        nps = self.cb_nps.currentData()
        Q = self.d_Q.base()
        mm = self.cb_len.currentText() == "mm"
        L = (lambda x: fmt(x, 4)) if mm else (lambda x: fmt(x / 25.4, 4))
        Ar = (lambda x: fmt(x, 5)) if mm else (lambda x: fmt(x / 25.4 ** 2, 4))
        un_l, un_a, un_p = ("mm", "mm²", "kg/m") if mm else ("in", "in²", "lb/ft")
        cols = ["Cédula", f"DE [{un_l}]", f"Espesor [{un_l}]", f"DI [{un_l}]", f"Área interior [{un_a}]",
                f"Peso [{un_p}]"]
        uv = self.d_vmax.unidad.currentText()
        if Q:
            cols.append(f"Velocidad [{uv}]")
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        filas = []
        for r in H.tabla_tuberia(nps):
            peso = r.peso_kg_m if mm else r.peso_kg_m / 1.48816
            fila = [T.texto_cedula(r.cedula), L(r.OD_mm), L(r.espesor_mm), L(r.DI_mm), Ar(r.area_mm2), fmt(peso, 4)]
            if Q:
                fila.append(fmt(U.desde_base(H.velocidad(Q, r.DI_mm), "velocidad", uv), 3))
            filas.append(fila)
        _llenar(self.tabla, filas, derecha=tuple(range(1, len(cols))))
        vmax = self.d_vmax.base()
        if Q and vmax:
            s = H.nps_para_velocidad(Q, vmax, self.cb_ced.currentText())
            if s:
                n, c, vel = s
                self.lb_sug.setText(f"{T.texto_nps(n)} (DN {T.DN[n]}) {T.texto_cedula(c)}: "
                                    f"{fmt(U.desde_base(vel, 'velocidad', uv), 3)} {uv}")
            else:
                self.lb_sug.setText("Ningún diámetro de la tabla alcanza: revise el caudal.")
        else:
            self.lb_sug.setText("Cargue el caudal real a la izquierda.")


# ----------------------------------------------------------------------------- 4. presión-temperatura
class Rating(_Ventana):
    def __init__(self, padre=None):
        super().__init__(padre, "Presión-temperatura por clase · ASME B16.34", 900, 680)
        v = QVBoxLayout(self)
        f = QFormLayout()
        self.cb_grupo = QComboBox()
        for g in B.GRUPOS:
            self.cb_grupo.addItem(f"{g}  ·  {B.DESCRIPCION.get(g, '')}", g)
        self.cb_un = QComboBox()
        self.cb_un.addItems(["bar g", "psig", "kPa g", "MPa g"])
        self.cb_un.setCurrentText("bar g" if self.sistema == "SI" else "psig")
        self.cb_t = QComboBox()
        self.cb_t.addItems(["°C", "°F"])
        self.cb_t.setCurrentText(self.un("temperatura") if self.un("temperatura") in ("°C", "°F") else "°C")
        f.addRow("Grupo de materiales", self.cb_grupo)
        f.addRow("Unidad de presión", self.cb_un)
        f.addRow("Unidad de temperatura", self.cb_t)
        v.addLayout(f)
        g = QGroupBox("Clase mínima para la condición de diseño")
        h = QHBoxLayout(g)
        self.ed_P = QLineEdit()
        self.ed_P.setPlaceholderText("presión")
        self.ed_T = QLineEdit()
        self.ed_T.setPlaceholderText("temperatura")
        for w in (self.ed_P, self.ed_T):
            w.setFixedWidth(100)
        self.lb_cl = QLabel("—")
        h.addWidget(QLabel("Presión"))
        h.addWidget(self.ed_P)
        h.addWidget(QLabel("Temperatura"))
        h.addWidget(self.ed_T)
        h.addWidget(self.lb_cl, 1)
        v.addWidget(g)
        self.tabla = _tabla([])
        v.addWidget(self.tabla, 1)
        pie = QHBoxLayout()
        pie.addWidget(_nota("Presión de trabajo máxima de válvulas de clase estándar, ASME B16.34 edición 2017. "
                            "Verifique contra la edición que use el proyecto. Las válvulas bridadas terminan su "
                            f"rating en {B.T_BRIDADAS_C} °C."), 1)
        pie.addWidget(_boton_copiar(self.tabla))
        v.addLayout(pie)
        for w in (self.cb_grupo, self.cb_un, self.cb_t):
            w.currentIndexChanged.connect(self._calcular)
        for w in (self.ed_P, self.ed_T):
            w.textChanged.connect(self._clase)
        self._calcular()

    def _p(self, barg: float) -> str:
        u = self.cb_un.currentText()
        v = U.convertir(barg, "presion", "bar g", u)
        dec = {"bar g": 1, "psig": 0, "kPa g": 0, "MPa g": 2}[u]
        return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _t(self, c: float) -> str:
        return _limpio(c if self.cb_t.currentText() == "°C" else c * 9 / 5 + 32, 5)

    def _calcular(self):
        ts, tabla = H.tabla_rating(self.cb_grupo.currentData())
        u, ut = self.cb_un.currentText(), self.cb_t.currentText()
        cols = [f"T [{ut}]"] + [f"Clase {c} [{u}]" for c in B.CLASES]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        _llenar(self.tabla, [[self._t(t)] + [self._p(tabla[c][i]) for c in B.CLASES] for i, t in enumerate(ts)],
                derecha=tuple(range(len(cols))))
        self._clase()

    def _clase(self):
        p, t = _numero(self.ed_P.text()), _numero(self.ed_T.text())
        if p is None or t is None:
            self.lb_cl.setText("Cargue la presión y la temperatura de diseño.")
            return
        barg = U.convertir(p, "presion", self.cb_un.currentText(), "bar g")
        tc = t if self.cb_t.currentText() == "°C" else (t - 32) * 5 / 9
        g = self.cb_grupo.currentData()
        c = B.clase_minima(g, barg, tc)
        if c is None:
            self.lb_cl.setText("Fuera de la tabla: ninguna clase estándar cubre esa condición.")
        else:
            self.lb_cl.setText(f"<b>Clase {c}</b>: admite {self._p(B.rating(g, c, tc))} {self.cb_un.currentText()} "
                               f"a {self._t(tc)} {self.cb_t.currentText()}.")


# ----------------------------------------------------------------------------- 6. calculadoras
class Calculadoras(_Ventana):
    def __init__(self, padre=None):
        super().__init__(padre, "Calculadoras rápidas", 800, 520)
        v = QVBoxLayout(self)
        self.tabs = QTabWidget()
        v.addWidget(self.tabs)
        self._liquido()
        self._gas_bloqueo()
        self._caudal_gas()
        self._velocidad()
        self._altitud()

    def _hoja(self, titulo: str, nota: str):
        w = QWidget()
        lay = QVBoxLayout(w)
        f = QFormLayout()
        lay.addLayout(f)
        res = QLabel("—")
        res.setTextFormat(Qt.RichText)
        res.setWordWrap(True)
        res.setStyleSheet("background:#f2f6fb;border:1px solid #c9d6e5;border-radius:4px;padding:8px")
        lay.addWidget(res)
        lay.addWidget(_nota(nota))
        lay.addStretch(1)
        self.tabs.addTab(w, titulo)
        return f, res

    def _conectar(self, datos, fn):
        for d in datos:
            if isinstance(d, Dato):
                d.edit.textChanged.connect(fn)
                d.unidad.currentIndexChanged.connect(fn)
            else:
                d.textChanged.connect(fn)
        fn()

    def _pdif(self, kpa: float) -> str:
        u = self.un("presion_dif")
        return f"{fmt(U.desde_base(kpa, 'presion_dif', u), 4)} {u}"

    # ΔP de bloqueo de líquidos
    def _liquido(self):
        f, res = self._hoja("ΔP de bloqueo · líquido",
                            "IEC 60534-2-1: ΔPmax = FL²·(P1 − FF·Pv), FF = 0,96 − 0,28·√(Pv/Pc). Por encima de ΔPmax "
                            "el caudal no aumenta (flujo bloqueado: cavitación plena o flashing).")
        pa = "bar a" if self.sistema == "SI" else "psia"
        P1, Pv, Pc = Dato("presion", pa, "10"), Dato("presion", pa, "0,5"), Dato("presion", pa, "220,64")
        FL = QLineEdit("0,90")
        FL.setFixedWidth(110)
        f.addRow("Presión de entrada P1", P1)
        f.addRow("Presión de vapor Pv", Pv)
        f.addRow("Presión crítica Pc", Pc)
        f.addRow("Factor de recuperación FL", FL)

        def calc():
            a, b, c, fl = P1.base(), Pv.base(), Pc.base(), _numero(FL.text())
            if None in (a, b, c, fl) or c <= 0 or b < 0:
                res.setText("Cargue los cuatro datos.")
                return
            F, dp = H.dp_bloqueado(a, b, c, fl)
            res.setText(f"FF = <b>{fmt(F, 3)}</b><br>ΔP de bloqueo = <b>{self._pdif(dp)}</b><br>"
                        f"Presión de salida mínima sin bloqueo = {self._pdif(a - dp)} (absoluta)")
        self._conectar((P1, Pv, Pc, FL), calc)

    # ΔP de bloqueo de gases
    def _gas_bloqueo(self):
        f, res = self._hoja("ΔP de bloqueo · gas",
                            "IEC 60534-2-1: x = ΔP/P1; el caudal queda bloqueado (sónico) cuando x ≥ Fγ·xT, con "
                            "Fγ = γ/1,40.")
        pa = "bar a" if self.sistema == "SI" else "psia"
        P1 = Dato("presion", pa, "10")
        xT, g = QLineEdit("0,70"), QLineEdit("1,40")
        for w in (xT, g):
            w.setFixedWidth(110)
        f.addRow("Presión de entrada P1", P1)
        f.addRow("Factor xT", xT)
        f.addRow("Exponente isoentrópico γ", g)

        def calc():
            a, x, k = P1.base(), _numero(xT.text()), _numero(g.text())
            if None in (a, x, k):
                res.setText("Cargue los tres datos.")
                return
            dp = H.dp_bloqueado_gas(a, x, k)
            res.setText(f"Fγ·xT = <b>{fmt(k / 1.4 * x, 3)}</b><br>ΔP de bloqueo = <b>{self._pdif(dp)}</b><br>"
                        f"Presión de salida crítica = {self._pdif(a - dp)} (absoluta)")
        self._conectar((P1, xT, g), calc)

    # Caudal de gas normal ↔ real ↔ másico
    def _caudal_gas(self):
        f, res = self._hoja("Caudal de gas",
                            "Caudal real = Q normal · (101,325 kPa / P) · (T / 273,15 K) · Z.  "
                            "Másico = Q normal · M / 22,414.")
        Qn = Dato("caudal_gas_std", self.un("caudal_gas_std"), "1000")
        pa = "bar a" if self.sistema == "SI" else "psia"
        Pg = Dato("presion", pa, "10")
        Tg = Dato("temperatura", self.un("temperatura"), "25")
        Z = QLineEdit("1")
        M = Dato("masa_molar", "kg/kmol", "28,96")
        Z.setFixedWidth(110)
        f.addRow("Caudal en condiciones de referencia", Qn)
        f.addRow("Presión de operación", Pg)
        f.addRow("Temperatura de operación", Tg)
        f.addRow("Factor de compresibilidad Z", Z)
        f.addRow("Masa molar (o SG)", M)

        def calc():
            q, p, t, z, m = Qn.base(), Pg.base(), Tg.base(), _numero(Z.text()), M.base()
            if None in (q, p, t, z) or p <= 0:
                res.setText("Cargue caudal, presión, temperatura y Z.")
                return
            qr = H.caudal_gas_real(q, p, t, z)
            uq, um = self.un("caudal_vol"), self.un("caudal_masico")
            txt = f"Caudal real = <b>{fmt(U.desde_base(qr, 'caudal_vol', uq), 4)} {uq}</b>"
            if m:
                txt += (f"<br>Caudal másico = <b>{fmt(U.desde_base(H.masico_desde_normal(q, m), 'caudal_masico', um), 4)}"
                        f" {um}</b><br>Densidad a la operación = "
                        f"{fmt(H.masico_desde_normal(q, m) / qr, 4)} kg/m³")
            res.setText(txt)
        self._conectar((Qn, Pg, Tg, Z, M), calc)

    # Velocidad, Reynolds y Mach
    def _velocidad(self):
        f, res = self._hoja("Velocidad y Reynolds",
                            "v = Q / A; Re = v·D/ν; Mach = v/c. Use el caudal real (en gases, a la presión y "
                            "temperatura de la línea).")
        Q = Dato("caudal_vol", self.un("caudal_vol"), "50")
        D = Dato("longitud", self.un("longitud"), "102,26" if self.sistema == "SI" else "4,026")
        nu = Dato("viscosidad_cin", "cSt", "1")
        c = Dato("velocidad", self.un("velocidad"))
        c.edit.setPlaceholderText("opcional, gases")
        f.addRow("Caudal real", Q)
        f.addRow("Diámetro interior", D)
        f.addRow("Viscosidad cinemática", nu)
        f.addRow("Velocidad del sonido", c)

        def calc():
            q, d, n, cs = Q.base(), D.base(), nu.base(), c.base()
            if None in (q, d) or d <= 0:
                res.setText("Cargue caudal y diámetro interior.")
                return
            vel = H.velocidad(q, d)
            uv = self.un("velocidad")
            txt = f"Velocidad = <b>{fmt(U.desde_base(vel, 'velocidad', uv), 4)} {uv}</b>"
            if n:
                re = H.reynolds(vel, d, n)
                txt += f"<br>Reynolds = <b>{fmt(re, 4)}</b> ({'turbulento' if re > 4000 else 'laminar' if re < 2300 else 'transición'})"
            if cs:
                txt += f"<br>Mach = <b>{fmt(H.mach(vel, cs), 3)}</b>"
            res.setText(txt)
        self._conectar((Q, D, nu, c), calc)

    # Presión atmosférica según altitud
    def _altitud(self):
        f, res = self._hoja("Presión atmosférica",
                            "Atmósfera estándar ISA: P = 101,325·(1 − 2,25577·10⁻⁵·z)^5,25588 kPa. Es la que separa "
                            "las presiones absolutas de las manométricas en el sitio.")
        z = Dato("distancia", self.un("distancia"), "0")
        f.addRow("Altitud del sitio", z)

        def calc():
            h = z.base()
            if h is None:
                res.setText("Cargue la altitud.")
                return
            p = H.p_atm_altitud(h)
            res.setText(f"P atm = <b>{fmt(p, 5)} kPa</b> = {fmt(p / 100, 5)} bar = {fmt(p / U.PSI_KPA, 5)} psi")
        self._conectar((z,), calc)


# ----------------------------------------------------------------------------- 7. enlaces
def _ruta_enlaces() -> str:
    from .. import licencia
    return os.path.join(licencia.carpeta_config(), "enlaces.json")


def leer_enlaces(ruta: str | None = None) -> list[tuple[str, str]]:
    try:
        with open(ruta or _ruta_enlaces(), encoding="utf-8") as f:
            datos = json.load(f)
        return [(str(n), str(u)) for n, u in datos if u]
    except (OSError, ValueError, TypeError):
        return list(H.ENLACES)


def guardar_enlaces(enlaces: list[tuple[str, str]], ruta: str | None = None):
    ruta = ruta or _ruta_enlaces()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump([list(e) for e in enlaces], f, ensure_ascii=False, indent=1)


class Enlaces(_Ventana):
    def __init__(self, padre=None, ruta: str | None = None):
        super().__init__(padre, "Enlaces de referencia", 640, 460)
        self.ruta = ruta
        v = QVBoxLayout(self)
        v.addWidget(_nota("Doble clic para abrir en el navegador. La lista es suya: agregue, edite o quite enlaces; "
                          "se guarda en su equipo."))
        h = QHBoxLayout()
        self.lista = QListWidget()
        h.addWidget(self.lista, 1)
        b = QVBoxLayout()
        for texto, fn in (("Abrir", self._abrir), ("Agregar…", self._agregar), ("Editar…", self._editar),
                          ("Quitar", self._quitar), ("Subir", lambda: self._mover(-1)), ("Bajar", lambda: self._mover(1)),
                          ("Restaurar lista inicial", self._restaurar)):
            bt = QPushButton(texto)
            bt.clicked.connect(fn)
            b.addWidget(bt)
        b.addStretch(1)
        h.addLayout(b)
        v.addLayout(h)
        self.lista.itemDoubleClicked.connect(lambda _: self._abrir())
        self._cargar(leer_enlaces(ruta))

    def _cargar(self, enlaces):
        self.lista.clear()
        for n, u in enlaces:
            it = QListWidgetItem(n)
            it.setData(Qt.UserRole, u)
            it.setToolTip(u)
            self.lista.addItem(it)

    def enlaces(self) -> list[tuple[str, str]]:
        return [(self.lista.item(i).text(), self.lista.item(i).data(Qt.UserRole)) for i in range(self.lista.count())]

    def _guardar(self):
        try:
            guardar_enlaces(self.enlaces(), self.ruta)
        except OSError as e:
            QMessageBox.warning(self, "Enlaces", f"No se pudo guardar la lista: {e}")

    def _abrir(self):
        it = self.lista.currentItem()
        if it:
            abrir_url(it.data(Qt.UserRole), self)

    def _pedir(self, nombre="", url="https://"):
        n, ok = QInputDialog.getText(self, "Enlace", "Nombre:", text=nombre)
        if not ok or not n.strip():
            return None
        u, ok = QInputDialog.getText(self, "Enlace", "Dirección (https://…):", text=url)
        if not ok or not u.strip():
            return None
        u = u.strip()
        if "://" not in u:
            u = "https://" + u
        return n.strip(), u

    def _agregar(self):
        e = self._pedir()
        if e:
            self._cargar(self.enlaces() + [e])
            self.lista.setCurrentRow(self.lista.count() - 1)
            self._guardar()

    def _editar(self):
        i = self.lista.currentRow()
        if i < 0:
            return
        e = self._pedir(*self.enlaces()[i])
        if e:
            lst = self.enlaces()
            lst[i] = e
            self._cargar(lst)
            self.lista.setCurrentRow(i)
            self._guardar()

    def _quitar(self):
        i = self.lista.currentRow()
        if i >= 0:
            self.lista.takeItem(i)
            self._guardar()

    def _mover(self, d):
        i = self.lista.currentRow()
        lst = self.enlaces()
        j = i + d
        if i < 0 or not 0 <= j < len(lst):
            return
        lst[i], lst[j] = lst[j], lst[i]
        self._cargar(lst)
        self.lista.setCurrentRow(j)
        self._guardar()

    def _restaurar(self):
        if QMessageBox.question(self, "Enlaces", "¿Volver a la lista inicial? Se pierden los enlaces agregados.") \
                == QMessageBox.Yes:
            self._cargar(list(H.ENLACES))
            self._guardar()


VENTANAS = {"conversor": Conversor, "fluidos": Fluidos, "tuberia": Tuberias, "rating": Rating,
            "calculadoras": Calculadoras, "enlaces": Enlaces}


# ----------------------------------------------------------------------------- la barra
class BarraHerramientas(QWidget):
    """Fila de botones chicos con icono, sin texto; el nombre aparece al pasar el cursor."""

    def __init__(self, ventana):
        super().__init__()
        self.ventana = ventana
        self.abiertas: dict[str, QDialog] = {}
        self.botones: dict[str, QToolButton] = {}
        self.setProperty("ayuda", "herramientas")
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(5)
        h.addStretch(1)
        for clave, tip in HERRAMIENTAS:
            h.addWidget(self._boton(clave, tip, lambda _=False, c=clave: self.abrir(c)))
        sep = QFrame()
        sep.setFixedSize(1, 22)
        sep.setStyleSheet("background:rgba(255,255,255,0.35)")
        h.addSpacing(3)
        h.addWidget(sep)
        h.addSpacing(3)
        for clave, tip, url in contacto.DESTINOS:
            h.addWidget(self._boton(clave, tip, lambda _=False, u=url: abrir_url(u(), self.ventana)))

    def _boton(self, clave, tip, fn) -> QToolButton:
        b = QToolButton()
        b.setIcon(iconos.icono(clave))
        b.setIconSize(QSize(18, 18))
        b.setFixedSize(28, 28)
        b.setToolTip(tip)
        b.setAccessibleName(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(ESTILO_BOTON)
        b.clicked.connect(fn)
        self.botones[clave] = b
        return b

    def abrir(self, clave: str):
        if clave == "materiales":
            self.ventana.biblioteca_materiales()
            return
        d = self.abiertas.get(clave)
        if d is None:
            d = VENTANAS[clave](self.ventana)
            self.abiertas[clave] = d
        d.show()
        d.raise_()
        d.activateWindow()
        return d
