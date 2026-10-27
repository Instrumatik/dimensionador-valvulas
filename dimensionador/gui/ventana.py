"""Ventana principal de N25 Valves Sizing (versión 2: líquidos)."""
from __future__ import annotations

import html as _html
import json
import os

from PySide6.QtCore import QDate, QLocale, Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QImage, QKeySequence, QShortcut, QTextDocument
from PySide6.QtWidgets import (QApplication, QCalendarWidget, QComboBox, QDateEdit, QDialog, QFileDialog, QFrame, QGridLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy,
                               QSplitter, QTabWidget, QTextBrowser, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from .. import __version__, anticavitacion as AC, ayuda, compresible as CG, entregables as E, fluido_servicio as FS, modelos, propiedades, trims as T, tuberias, unidades as U
from ..estilos import (CLAVES_ANTERIORES, CUERPOS, ESTILOS, KC_TIPICO, NOMBRE_CORTO, NOMBRES_ANTERIORES, SENTIDOS,
                       NOMBRE_GEOMETRIA, TAMANOS, clave_de_geometria, clave_trim, factores, geometria_sentido,
                       geometrias, nombre_geometria, sentidos)
from ..geometria import fraccion_in
from ..iec60534_2_1 import RHO_AGUA_15C, CapacidadInsuficiente
from ..modelos import ErrorDatos, Severidad
from . import botones
from .buscador import Buscador
from .solapa_actuador import SolapaEquipo, _bloquear_items
from .solapa_materiales import SolapaMateriales
from ..proyecto import (CIERRES, CONEXIONES, RATINGS, CasoCierre, CasoGas, CasoLiquido, Dimensionamiento,
                        Identificacion, Instalacion, Resultado, RuidoAerodinamico, calcular)

CASOS = ["Mínimo", "Normal", "Máximo", "Tight Shutoff", "Transitorio"]
CIERRE = 3                      # índice de la columna Tight Shutoff
FLUYEN = [0, 1, 2, 4]           # casos con caudal
USUARIO = "Definido por el usuario"
AZUL = "#0d3b66"
# Tablero de resultados: fondo azul claro, celdas blancas y acento azul acero
ACENTO = "#3d5a80"
FONDO_TABLERO = "#eef2f6"
BORDE_TABLERO = "#d3dce6"
BORDE_CELDA = "#c5d0dc"
FONDO_ENCABEZADO = "#dde5ee"
FONDO_AUTO = "#eef2f6"
FONDO_NO_APLICA = "#e6e6e6"
ANCHO_CELDA = 104
ANCHO_SALIDA = 132
ANCHO_A4 = 820             # ancho de una hoja A4 en pantalla (96 ppp) más márgenes
ANCHO_UNIDAD = 92
COLORES = {Severidad.INFO: "#2f6fb0", Severidad.ADVERTENCIA: "#d9771e",
           Severidad.CRITICA: "#c0392b", Severidad.ERROR: "#7d1f9e"}
NOMBRE_SEV = E.NOMBRE_SEV
DIF = {"kPa a": "kPa", "kPa g": "kPa", "bar a": "bar", "bar g": "bar", "MPa a": "MPa", "MPa g": "MPa",
       "psia": "psi", "psig": "psi", "kg/cm² a": "kg/cm²", "kg/cm² g": "kg/cm²"}
DIF_ABS = {"kPa g": "kPa a", "bar g": "bar a", "MPa g": "MPa a", "psig": "psia", "kg/cm² g": "kg/cm² a"}
LETRA = {"liquido": "L", "gas": "G", "vapor": "V", "steam": "S"}
TITULO_TIPO = {"liquido": "LÍQUIDOS", "gas": "GAS", "vapor": "VAPOR", "steam": "VAPOR DE AGUA (STEAM)"}
NOTA_TIPO = {
    "liquido": "FL, Fd y Kc: típicos del trim, uno por caso para reflejar la carrera de cada uno. Reemplácelos "
               "por los certificados del fabricante. Kc en blanco = estimado según IEC 60534-8-4.",
    "gas": "xT, FL y Fd: típicos del trim, uno por caso; reemplácelos por los certificados. Con un fluido de la "
           "lista, M, μ, γ, Z1, T2 y Z2 se calculan (expansión isoentálpica). Con «Definido por el usuario», "
           "T2 en blanco = T1 y Z2 en blanco = Z1.",
    "vapor": "xT, FL y Fd: típicos del trim, uno por caso. Con un fluido de la lista las propiedades se "
             "calculan; con «Definido por el usuario» ingrese M, ρ1, μ y γ. T2 en blanco = T1; ρ2 en blanco = "
             "ρ1·(P2/P1)·(T1/T2).",
    "steam": "Propiedades del vapor de agua según IAPWS-95: solo se ingresan caudal másico, presiones y "
             "temperatura. T1 en blanco = vapor saturado seco. T2 en blanco = expansión isoentálpica.",
}
# Entradas por caso: clave, etiqueta, magnitudes, ayuda, tipos (L líquido, G gas, V vapor, S steam)
ENTRADAS = [
    ("caudal", "Caudal", ("caudal_vol",), "caudal", "LGVS"),
    ("P1", "Presión de entrada", ("presion",), "P1", "LGVS"),
    ("P2", "Presión de salida", ("presion",), "P2", "LGVS"),
    ("T1", "Temperatura de entrada", ("temperatura",), "T1", "LGVS"),
    ("SG", "Gravedad específica", ("adimensional",), "SG", "L"),
    ("M", "Masa molar / grav. específica", ("masa_molar",), "M", "GV"),
    ("rho1", "Densidad de entrada ρ1", ("densidad",), "rho", "V"),
    ("mu", "Viscosidad dinámica", ("viscosidad_din",), "viscosidad", "LGV"),
    ("gamma", "Relación de calores esp. γ", ("adimensional",), "gamma", "GV"),
    ("Z1", "Factor de compresibilidad Z1", ("adimensional",), "Z", "G"),
    ("Pv", "Presión de vapor", ("presion",), "Pv", "L"),
    ("xT", "Factor de caída crítica (xT)", ("adimensional",), "xT", "GVS"),
    ("FL", "Factor de recuperación (FL)", ("adimensional",), "FL", "LGVS"),
    ("Fd", "Modificador de estilo (Fd)", ("adimensional",), "Fd", "LGVS"),
    ("Kc", "Coef. cavitación del trim (Kc)", ("adimensional",), "Kc", "L"),
    ("#", "Datos de salida para ruido", None, None, "GVS"),
    ("T2", "Temperatura de salida T2", ("temperatura",), "T2", "GVS"),
    ("Z2", "Factor de compresibilidad Z2", ("adimensional",), "Z", "G"),
    ("rho2", "Densidad de salida ρ2", ("densidad",), "rho2", "V"),
]
# Propiedades del fluido que se calculan con la biblioteca cuando el fluido es conocido
PROPIEDADES = ("SG", "mu", "Pv", "M", "rho1", "gamma", "Z1", "T2", "Z2", "rho2")
fmt = E.fmt


def leer_numero(texto: str) -> float | None:
    t = texto.strip().replace(" ", "")
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    return float(t)


def _num(v: float) -> str:
    """Número para un campo editable (sin separador de miles)."""
    return fmt(v, 6).replace(".", "")


class Combo(QComboBox):
    """Lista desplegable que no cambia con la rueda del mouse: solo con un clic.

    Así, al desplazar la página con la rueda sobre un dato ya cargado, el valor
    no cambia sin que el usuario lo note.
    """

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()   # la rueda desplaza la página, no cambia la selección

    def showPopup(self):
        # la lista se abre con el ancho del texto más largo, para leer las opciones completas
        self.view().setMinimumWidth(self.view().sizeHintForColumn(0) + 24)
        super().showPopup()


class Fecha(QDateEdit):
    """Fecha elegida en un calendario que se abre con un clic, sin escribirla a mano."""

    def __init__(self):
        super().__init__(QDate.currentDate())
        self.setDisplayFormat("dd/MM/yyyy")
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setCursor(Qt.PointingHandCursor)
        self.setButtonSymbols(QDateEdit.NoButtons)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip("Haga clic para elegir la fecha en el calendario")
        self.calendario = QCalendarWidget()
        self.calendario.setWindowFlags(Qt.Popup)
        self.calendario.setGridVisible(True)
        self.calendario.setLocale(QLocale(QLocale.Spanish, QLocale.Argentina))
        self.calendario.setFirstDayOfWeek(Qt.Monday)
        self.calendario.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendario.clicked.connect(self._elegida)
        self.calendario.activated.connect(self._elegida)
        self.lineEdit().installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.lineEdit() and ev.type() == ev.Type.MouseButtonPress:
            self.abrir_calendario()
            return True
        return super().eventFilter(obj, ev)

    def mousePressEvent(self, e):
        self.abrir_calendario()

    def abrir_calendario(self):
        self.calendario.setSelectedDate(self.date())
        self.calendario.move(self.mapToGlobal(self.rect().bottomLeft()))
        self.calendario.show()
        self.calendario.setFocus()

    def _elegida(self, d: QDate):
        self.setDate(d)
        self.calendario.hide()

    def wheelEvent(self, e):
        e.ignore()

    def keyPressEvent(self, e):
        # La fecha no se escribe ni se cambia con flechas; Enter o espacio abren el calendario
        if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_F4):
            self.abrir_calendario()
        elif e.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            super().keyPressEvent(e)

    def text(self) -> str:
        return self.date().toString("dd/MM/yyyy")

    def setText(self, t: str):
        d = QDate.fromString(t, "dd/MM/yyyy")
        self.setDate(d if d.isValid() else QDate.currentDate())

    def clear(self):
        self.setDate(QDate.currentDate())


# ---------------------------------------------------------------------------
# Ventana de ayuda (índice completo, desde el menú Ayuda)
# ---------------------------------------------------------------------------
class VentanaAyuda(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ayuda de {E.PRODUCTO}")
        self.resize(1100, 760)
        lay = QHBoxLayout(self)
        izq = QVBoxLayout()
        self.buscar = QLineEdit(placeholderText="Buscar tema…")
        self.lista = QListWidget()
        izq.addWidget(self.buscar)
        izq.addWidget(self.lista)
        w = QWidget()
        w.setLayout(izq)
        w.setMaximumWidth(360)
        self.lista.setWordWrap(True)
        self.texto = QTextBrowser()
        self.texto.setOpenLinks(False)
        self.texto.setLineWrapMode(QTextBrowser.WidgetWidth)
        self.texto.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.texto.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.texto.anchorClicked.connect(self._enlace)
        lay.addWidget(w)
        lay.addWidget(self.texto, 1)
        self._llenar()
        self.buscar.textChanged.connect(self._llenar)
        self.lista.currentItemChanged.connect(
            lambda it, _: it and it.data(Qt.UserRole) and self.mostrar(it.data(Qt.UserRole), False))

    def _llenar(self, filtro: str = ""):
        self.lista.clear()
        f = filtro.lower()
        por_cat: dict[str, list] = {}
        for k, e in ayuda.A.items():
            g = ayuda.GUIA.get(k, {})
            if f and f not in " ".join([e.titulo, e.texto, *map(str, g.values())]).lower():
                continue
            por_cat.setdefault(e.categoria, []).append((e.titulo, k))
        for cat in ["Conceptos", "Datos", "Coeficientes", "Resultados", "Fenómenos", "Materiales",
                    "Agentes químicos", "Normas y mecanismos"]:
            if cat not in por_cat:
                continue
            it = QListWidgetItem(cat.upper())
            it.setFlags(Qt.NoItemFlags)
            f2 = it.font()
            f2.setBold(True)
            it.setFont(f2)
            self.lista.addItem(it)
            vistos = set()
            for titulo, k in sorted(por_cat[cat]):
                if titulo in vistos:
                    continue
                vistos.add(titulo)
                it = QListWidgetItem("   " + titulo)
                it.setData(Qt.UserRole, k)
                self.lista.addItem(it)

    def _enlace(self, url: QUrl):
        s = url.toString()
        if s.startswith("ayuda:"):
            self.mostrar(s[6:])

    def mostrar(self, clave: str, seleccionar: bool = True):
        self.texto.setHtml(ayuda.html(clave))
        if seleccionar:
            for i in range(self.lista.count()):
                if self.lista.item(i).data(Qt.UserRole) == clave:
                    self.lista.blockSignals(True)
                    self.lista.setCurrentRow(i)
                    self.lista.blockSignals(False)
        self.show()
        self.raise_()
        self.activateWindow()


class PanelInfo(QFrame):
    """Panel fijo a la derecha de cada solapa de datos: muestra la ayuda pedida con «Ver»."""

    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(320)
        v = QVBoxLayout(self)
        h = QHBoxLayout()
        t = QLabel("<b>Información del parámetro</b>")
        b = QPushButton("Limpiar")
        b.setToolTip("Dejar el panel en blanco")
        b.clicked.connect(self.limpiar)
        h.addWidget(t)
        h.addStretch()
        h.addWidget(b)
        v.addLayout(h)
        self.texto = QTextBrowser()
        self.texto.setOpenLinks(False)
        self.texto.setLineWrapMode(QTextBrowser.WidgetWidth)
        self.texto.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.texto.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.texto.anchorClicked.connect(
            lambda u: u.toString().startswith("ayuda:") and self.mostrar(u.toString()[6:]))
        v.addWidget(self.texto, 1)
        self.limpiar()

    def mostrar(self, clave: str):
        self.texto.setHtml(ayuda.html(clave))

    def limpiar(self):
        self.texto.clear()


class Vista(QTextBrowser):
    """Vista previa de un entregable; entrega el gráfico de Cv como recurso."""

    def __init__(self):
        super().__init__()
        self.imagen: QImage | None = None
        self.setOpenLinks(False)

    def loadResource(self, tipo, url):
        if url.toString() == "grafico://cv" and self.imagen is not None:
            return self.imagen
        return super().loadResource(tipo, url)


# ---------------------------------------------------------------------------
# Filas de datos
# ---------------------------------------------------------------------------
def boton_ir(abrir_ayuda, clave: str) -> QPushButton:
    b = QPushButton("Ver")
    b.setFixedWidth(40)
    b.setToolTip("Ver la explicación de este dato en el panel de la derecha (F1)")
    b.setFocusPolicy(Qt.NoFocus)
    b.setStyleSheet("QPushButton{padding:1px 2px;color:#0d3b66;font-size:8pt}")
    b.clicked.connect(lambda: abrir_ayuda(clave))
    return b


def _celda(ancho=ANCHO_CELDA) -> QLineEdit:
    e = QLineEdit()
    e.setAlignment(Qt.AlignRight)
    e.setFixedWidth(ancho)
    return e


class FilaUnidad:
    """Dato con selector de unidad y uno o varios valores (uno por caso)."""

    def __init__(self, clave, etiqueta, magnitudes, grid, r, abrir_ayuda, n=len(CASOS), ayuda_clave=None,
                 col=3, ancho=ANCHO_CELDA):
        self.clave = clave
        self.lbl = QLabel(etiqueta)
        clave_ayuda = ayuda_clave or clave
        self.btn = boton_ir(abrir_ayuda, clave_ayuda)
        self.unidad = Combo()
        self.unidad.setFixedWidth(ANCHO_UNIDAD)
        self.mag_de: dict[str, str] = {}
        for m in magnitudes:
            for s in U.unidades_de(m):
                self.unidad.addItem(s)
                self.mag_de[s] = m
        self.unidad.setProperty("ayuda", clave_ayuda)
        self.unidad.currentTextChanged.connect(self._cambio_unidad)
        self._ant = self.unidad.currentText()
        self.edits = []
        grid.addWidget(self.lbl, r, 0)
        grid.addWidget(self.btn, r, 1)
        grid.addWidget(self.unidad, r, 2)
        for j in range(n):
            e = _celda(ancho)
            e.setProperty("ayuda", clave_ayuda)
            grid.addWidget(e, r, col + j)
            self.edits.append(e)
        if magnitudes == ("adimensional",):
            self.unidad.setEnabled(False)

    def magnitud(self) -> str:
        return self.mag_de[self.unidad.currentText()]

    def widgets(self) -> list:
        return [self.lbl, self.btn, self.unidad, *self.edits]

    def _cambio_unidad(self, nueva: str):
        ant, self._ant = self._ant, nueva
        if self.mag_de.get(ant) != self.mag_de.get(nueva):
            return
        for e in self.edits:
            try:
                v = leer_numero(e.text())
            except ValueError:
                continue
            if v is not None:
                e.setText(_num(U.convertir(v, self.mag_de[nueva], ant, nueva)))

    def valor_base(self, j: int = 0) -> float | None:
        t = self.edits[j].text()
        try:
            v = leer_numero(t)
        except ValueError:
            raise ValueError(f"«{t}» no es un número válido en «{self.lbl.text()}».") from None
        if v is None:
            return None
        return U.a_base(v, self.magnitud(), self.unidad.currentText())

    def poner_base(self, j: int, valor: float | None):
        if valor is None:
            self.edits[j].setText("")
        else:
            self.edits[j].setText(_num(U.desde_base(valor, self.magnitud(), self.unidad.currentText())))

    def elegir(self, simbolo: str, convertir: bool = True):
        if self.unidad.findText(simbolo) < 0:
            return
        if not convertir:
            self.unidad.blockSignals(True)
        self.unidad.setCurrentText(simbolo)
        self._ant = simbolo
        self.unidad.blockSignals(False)

    def solo_lectura(self, si: bool, columnas=None):
        for j, e in enumerate(self.edits):
            if columnas is not None and j not in columnas:
                continue
            e.setReadOnly(si)
            e.setStyleSheet(f"background:{FONDO_AUTO};" if si else "")


class FilaSalida:
    def __init__(self, clave, etiqueta, ayuda_clave, magnitud, cifras, grid, r, abrir_ayuda):
        self.clave, self.magnitud, self.cifras = clave, magnitud, cifras
        self.fila = r
        self.extra: list = []
        self.lbl = QLabel(etiqueta)
        grid.addWidget(self.lbl, r, 0)
        self.btn = boton_ir(abrir_ayuda, ayuda_clave)
        grid.addWidget(self.btn, r, 1)
        self.lbl_unidad = QLabel("")
        grid.addWidget(self.lbl_unidad, r, 2)
        self.celdas = []
        for j in range(len(CASOS)):
            e = _celda(ANCHO_SALIDA)
            e.setReadOnly(True)
            e.setFocusPolicy(Qt.ClickFocus)
            e.setProperty("ayuda", ayuda_clave)
            peso = "font-weight:500;font-size:8pt" if magnitud == "texto" else "font-weight:600"
            e.setStyleSheet(f"QLineEdit{{background:white;color:#1b2a3a;{peso};border:1px solid {BORDE_CELDA};"
                            "border-radius:3px;padding:2px 4px}")
            grid.addWidget(e, r, 3 + j)
            self.celdas.append(e)

    def widgets(self) -> list:
        return [self.lbl, self.btn, self.lbl_unidad, *self.celdas, *self.extra]


SALIDAS = [
    # clave, etiqueta, ayuda, magnitud (None = adimensional), cifras, tipos; «#» = título de sección
    ("#", "Resultados de dimensionamiento", None, None, 0, "GVS"),
    ("Cv", "Coeficiente de flujo (Cv)", "kv_cv", None, 4, "LGVS"),
    ("apertura", "Apertura estimada", "apertura", "%", 3, "LGVS"),
    ("carrera", "Carrera de operación", "carrera_nominal", "carrera", 3, "LGVS"),
    ("caudal_otro", "Flujo másico", "flujo_masico", "caudal_otro", 4, "LGVS"),
    ("Kapp", "Coef. cavitación de la aplicación (Kapp)", "Kapp", None, 3, "L"),
    ("dP", "Presión diferencial ΔP", "dP", "presion_dif", 4, "LGVS"),
    ("dP_P1", "Relación de caída de presión ΔP/P1", "dP_P1", None, 3, "LGVS"),
    ("dPchoked", "ΔP crítica de flujo estrangulado (ΔP choked)", "dPchoked", "presion_dif", 4, "LGVS"),
    ("dPcav", "ΔP para cavitación (ΔP cav)", "dPcav", "presion_dif", 4, "L"),
    ("xFzp1", "Inicio de cavitación incipiente (xFzp1)", "xFz", None, 3, "L"),
    ("FF", "Factor de relación de presión crítica (FF)", "FF", None, 3, "L"),
    ("FP", "Factor de corrección por tuberías (Fp)", "FP", None, 3, "LGVS"),
    ("FLP", "Factor de recuperación combinado (FLp)", "FLP", None, 3, "LGVS"),
    ("xTP", "Factor xT ajustado por accesorios (xTP)", "xTP", None, 3, "GVS"),
    ("M", "Masa molar / grav. específica", "M", "masa_molar", 4, "S"),
    ("rho", "Densidad de entrada ρ1", "rho", "densidad", 4, "LGS"),
    ("gamma", "Relación de calores específicos γ", "gamma", None, 4, "S"),
    ("visc", "Viscosidad", "viscosidad", "visc", 4, "LGVS"),
    ("Y", "Factor de expansión (Y)", "Y", None, 3, "GVS"),
    ("sobrecalentamiento2", "Sobrecalentamiento a P2", "sobrecalentamiento", "temperatura_dif", 3, "S"),
    ("Rev", "Número de Reynolds (Rev)", "Rev", None, 4, "LGVS"),
    ("D1", "Diámetro interno aguas arriba", "D_interno", "longitud", 4, "LGVS"),
    ("D2", "Diámetro interno aguas abajo", "D_interno", "longitud", 4, "LGVS"),
    ("tipo_calculo", "Tipo de cálculo", "tipo_calculo", "texto", 0, "GVS"),
    ("Lp", "Presión sonora a 1 m (LpAe,1m)", "ruido", "dB(A)", 3, "L"),
    ("v1", "Velocidad del fluido aguas arriba", "velocidad_tuberia", "velocidad", 3, "L"),
    ("v2", "Velocidad del fluido aguas abajo", "velocidad_tuberia", "velocidad", 3, "L"),
    ("condicion", "Condición hidrodinámica", "cavitacion", "texto", 0, "L"),
    ("k_etapa", "Kapp por etapa (trim anticavitación)", "anticav", None, 3, "L"),
    ("etapas_txt", "Etapas recomendadas: sin cavitación / incipiente", "anticav", "texto", 0, "L"),
    ("#", "Resultados de ruido (IEC 60534-8-3)", None, None, 0, "GVS"),
    ("nivel_trim", "Nivel de trim de bajo ruido requerido", "nivel_trim", "texto", 0, "GVS"),
    ("Lp_trim", "Ruido del trim LpA a 1 m", "ruido_componentes", "dB(A)", 3, "GVS"),
    ("Lp_salida", "Ruido de la salida LpA a 1 m", "ruido_componentes", "dB(A)", 3, "GVS"),
    ("Lp_g", "Ruido de la válvula LpA a 1 m", "ruido", "dB(A)", 3, "GVS"),
    ("Lp_Rn", "Ruido de la válvula LpA a Rn", "Rn", "dB(A)", 3, "GVS"),
    ("rho2", "Densidad de salida ρ2", "rho2", "densidad", 4, "GS"),
    ("#", "Resultados de velocidad", None, None, 0, "GVS"),
    ("Ma1", "Mach aguas arriba", "mach", None, 3, "GVS"),
    ("Ma_valvula", "Mach en la salida de la válvula", "mach", None, 3, "GVS"),
    ("Ma2", "Mach aguas abajo", "mach", None, 3, "GVS"),
    ("v1_g", "Velocidad del fluido aguas arriba", "velocidad_tuberia", "velocidad", 3, "GVS"),
    ("v_valvula", "Velocidad en la salida de la válvula", "velocidad_tuberia", "velocidad", 3, "GVS"),
    ("v2_g", "Velocidad del fluido aguas abajo", "velocidad_tuberia", "velocidad", 3, "GVS"),
    ("c1", "Vel. del sonido aguas arriba", "velocidad_sonido", "velocidad", 4, "GVS"),
    ("c_valvula", "Vel. del sonido salida de válvula", "velocidad_sonido", "velocidad", 4, "GVS"),
    ("c2", "Vel. del sonido aguas abajo", "velocidad_sonido", "velocidad", 4, "GVS"),
    ("A_salida", "Área de salida de la válvula usada", "area_salida", "area", 4, "GVS"),
]
# Claves de resultado que se muestran con otro nombre (filas repetidas en otra sección)
ALIAS_SALIDA = {"Lp_g": "Lp", "v1_g": "v1", "v2_g": "v2"}
# Etiquetas que cambian según el tipo de fluido
ETIQUETA_SALIDA = {("dP_P1", "L"): "Relación de caída de presión ΔP/P1",
                   **{("dP_P1", t): "Relación de caída de presión x = ΔP/P1" for t in "GVS"},
                   ("M", "S"): "Masa molar"}


# Barra de alertas según la peor severidad: (fondo, texto, leyenda)
BARRA_ALERTAS = {None: (ACENTO, "white", ""),
                 Severidad.INFO: ("#cdebd3", "#1e5e2e", "sin alarmas"),
                 Severidad.ADVERTENCIA: ("#e8892b", "white", "hay advertencias"),
                 Severidad.CRITICA: ("#c0392b", "white", "condición crítica"),
                 Severidad.ERROR: ("#c0392b", "white", "datos inválidos")}


def titulo_seccion(texto: str, color: str) -> QLabel:
    l = QLabel(texto)
    l.setStyleSheet(f"background:{color};color:white;font-weight:700;padding:5px 8px;letter-spacing:1px")
    return l


def encabezados_casos(grid, fila=0, primera="Dato", ancho=ANCHO_CELDA, estilo=""):
    grid.addWidget(QLabel(f"<b>{primera}</b>"), fila, 0)
    grid.addWidget(QLabel("<b>Unidad</b>"), fila, 2)
    for j, c in enumerate(CASOS):
        l = QLabel(f"<b>{c}</b>")
        l.setAlignment(Qt.AlignCenter)
        l.setFixedWidth(ancho)
        if estilo:
            l.setStyleSheet(estilo)
        l.setProperty("ayuda", "casos")
        grid.addWidget(l, fila, 3 + j)


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
# Fluido de la solapa 3 en proyectos 0.7.0 → calidad / variante de la solapa 2 (desde 0.7.1)
_VARIANTE_070 = {"Agua industrial": "Agua industrial / de enfriamiento", "Agua desmineralizada": "Agua desmineralizada",
                 "Agua de mar": "Agua de mar", "Agua producida": "Agua producida (yacimiento)",
                 "Condensado": "Condensado", "Crudo": "Crudo", "Diésel": "Diésel / destilados",
                 "Gas natural": "Gas natural", "Gas combustible": "Gas combustible"}
_FAMILIA_070 = {"Salmuera": "Salmuera", "Ácido": "Ácido", "Alcalino": "Alcalino (soda / potasa cáustica)",
                "Solvente": "Solvente", "Slurry": "Slurry (líquido con sólidos)"}


def _migrar_fluido(s: dict) -> dict:
    """Pasa la familia, el fluido y la fase acuosa que la versión 0.7.0 pedía en 3-Materiales a la solapa 2."""
    c = dict(s.get("campos", {}))
    if "variante" in c:
        return s
    serv = s.get("materiales", {}).get("servicio", {})
    fl = c.pop("mat_fluido", None) or serv.get("fluido")
    fam = c.pop("mat_familia_fluido", None) or serv.get("familia_fluido")
    acu = c.pop("mat_acuosa", None) or serv.get("acuosa")
    c.pop("mat_fase", None)
    var = _VARIANTE_070.get(fl) or _FAMILIA_070.get(fam)
    if var:
        c["variante"] = var
    if acu in FS.AGUA_LIBRE:
        c["agua_libre"] = acu
    # el orden importa: la variante y el agua libre se cargan después del tipo y del fluido
    orden = {k: v for k, v in c.items() if k not in ("variante", "agua_libre")}
    for k in ("variante", "agua_libre"):
        if k in c:
            orden[k] = c[k]
    return {**s, "campos": orden}


class VentanaPrincipal(SolapaMateriales, SolapaEquipo, QMainWindow):
    def __init__(self, licencia=None):
        super().__init__()
        self.licencia = licencia
        E.MARCA_AGUA = licencia.marca_agua if licencia else None
        self.setWindowTitle(f"{E.PRODUCTO} — {E.EMPRESA}  ·  versión {__version__}" + self._texto_licencia())
        self.resize(1400, 900)
        self.setStyleSheet(botones.ESTILO_GENERAL)
        self.ayuda = VentanaAyuda(self)
        self.res: Resultado | None = None
        self.sistema = "SI"
        self.ruta: str | None = None
        self.campos: dict[str, QWidget] = {}
        self.paneles: dict[int, PanelInfo] = {}
        self._construir_menu()

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._encabezado())
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._con_panel(self._tab_instalacion(), 0), "1-Sistema")
        self.tabs.addTab(self._con_panel(self._tab_dimensionamiento(), 1), "2-Cálculos Válvula")
        self.tabs.addTab(self._con_panel(self._tab_materiales(), 2), "3-Materiales")
        self.tabs.addTab(self._con_panel(self._tab_actuador(), 3), "4-Actuador")
        self.tabs.addTab(self._con_panel(self._tab_posicionador(), 4), "5-Posicionador")
        self.tabs.addTab(self._con_panel(self._tab_accesorios(), 5), "6-Accesorios")
        self.vistas: dict[str, Vista] = {}
        for codigo, titulo in (("memoria", "Memoria de cálculo"), ("hoja_datos", "Hoja de datos"),
                               ("informe_tecnico", "Informe técnico")):
            self.tabs.addTab(self._tab_vista(codigo), titulo)
        lay.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        QShortcut(QKeySequence(Qt.Key_F1), self, activated=self._ayuda_foco)
        self._cambio_cuerpo()
        self._cambio_fluido()
        self.aplicar_sistema("SI")
        self._eq_aire_inicial()
        self._act_concordancia()
        self._cambio_tipo_fluido()
        self._actualizar_vistas()
        self.statusBar().showMessage("Cargue los datos de instalación y de dimensionamiento y presione "
                                     "Calcular. «Ver» o F1 muestran la explicación de cada dato a la derecha.")

    def _con_panel(self, izquierda: QWidget, indice: int) -> QWidget:
        # Divisor arrastrable; la izquierda no baja de su ancho natural, así las celdas no se recortan
        sp = QSplitter(Qt.Horizontal)
        sp.setChildrenCollapsible(False)
        sp.addWidget(izquierda)
        panel = PanelInfo()
        self.paneles[indice] = panel
        sp.addWidget(panel)
        sp.setStretchFactor(0, 1)
        sp.setStretchFactor(1, 0)
        # Mínimos chicos: en pantallas angostas la izquierda se desplaza en horizontal y el panel de
        # información sigue entero a la vista (antes la ventana no podía achicarse y lo tapaba).
        izquierda.setMinimumWidth(480)
        if isinstance(izquierda, QScrollArea):
            izquierda.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sp.setSizes([10000, 480])
        return sp

    # ------------------------------------------------------------------ encabezado
    def _encabezado(self) -> QWidget:
        f = QFrame()
        f.setObjectName("encabezado")
        f.setStyleSheet("#encabezado{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0d3b66,"
                        "stop:1 #1f5f99);} QLabel{color:white;background:transparent}")
        h = QHBoxLayout(f)
        h.setContentsMargins(16, 8, 16, 8)
        izq = QVBoxLayout()
        empresa = QLabel(E.EMPRESA)
        empresa.setStyleSheet("font-size:9pt;letter-spacing:2px;color:#cfe0f1")
        producto = QLabel(E.PRODUCTO)
        producto.setStyleSheet("font-size:20pt;font-weight:800")
        sub = QLabel("Dimensionamiento y verificación independiente de válvulas de control · "
                     "IEC 60534 · ANSI/ISA-75.01 · Líquidos, gases y vapores")
        sub.setStyleSheet("font-size:9pt;color:#dce8f4")
        izq.addWidget(empresa)
        izq.addWidget(producto)
        izq.addWidget(sub)
        h.addLayout(izq, 1)
        der = QHBoxLayout()
        l = QLabel("Unidades")
        self.cb_sistema = Combo()
        self.cb_sistema.addItems(["SI", "Imperial"])
        self.cb_sistema.setProperty("ayuda", "sistema_unidades")
        self.cb_sistema.currentTextChanged.connect(self.aplicar_sistema)
        self.btn_calc_cab = QPushButton("Calcular")
        botones.calcular(self.btn_calc_cab, "amarillo")
        self.btn_calc_cab.clicked.connect(self.calcular)
        self.buscador = Buscador(self)
        der.addWidget(self.buscador)
        der.addSpacing(16)
        der.addWidget(l)
        der.addWidget(self.cb_sistema)
        der.addSpacing(12)
        der.addWidget(self.btn_calc_cab)
        h.addLayout(der)
        return f

    # ------------------------------------------------------------------ menú
    def _accion(self, menu, texto, fn, atajo=None):
        a = QAction(texto, self)
        a.triggered.connect(fn)
        if atajo:
            a.setShortcut(atajo)
        menu.addAction(a)
        return a

    def _construir_menu(self):
        mb = self.menuBar()
        m = mb.addMenu("&Inicio")
        self._accion(m, "Nuevo", self.nuevo, QKeySequence.New)
        self._accion(m, "Abrir proyecto…", self.abrir, QKeySequence.Open)
        self._accion(m, "Guardar proyecto", self.guardar, QKeySequence.Save)
        self._accion(m, "Guardar proyecto como…", lambda: self.guardar(como=True))
        m.addSeparator()
        ent = m.addMenu("Entregables")
        docs = (("memoria", "Memoria de cálculo"), ("hoja_datos", "Hoja de datos"),
                ("informe_tecnico", "Informe técnico"), ("todos", "Todos los entregables"))
        mw = ent.addMenu("Exportar a Word (.docx)")
        mp = ent.addMenu("Imprimir")
        for codigo, titulo in docs:
            self._accion(mw, titulo + "…", lambda _=False, c=codigo: self.exportar_word(c))
            self._accion(mp, titulo + "…", lambda _=False, c=codigo: self.imprimir(c))
        self._accion(ent, "Selección de trim y manual (PDF)…", self.exportar_manual_trim)
        m.addSeparator()
        self._accion(m, "Salir", self.close, QKeySequence.Quit)
        mu = mb.addMenu("&Unidades")
        for s, t in (("SI", "Sistema Internacional (SI)"), ("Imperial", "Sistema imperial")):
            self._accion(mu, t, lambda _=False, s=s: self.aplicar_sistema(s))
        ma = mb.addMenu("A&yuda")
        self._accion(ma, "Flujo de trabajo", lambda: self.ayuda.mostrar("flujo_trabajo"))
        self._accion(ma, "Índice de ayuda", lambda: self.ayuda.mostrar("kv_cv"))
        self._accion(ma, "Manual de selección de trim (PDF)…", self.exportar_manual_trim)
        ma.addSeparator()
        self._accion(ma, "Enviar comentarios…", self.enviar_comentarios)
        self._accion(ma, "Licencia…", self.ver_licencia)
        self._accion(ma, "Acerca de", self.acerca)

    def abrir_ayuda(self, clave: str):
        panel = self.paneles.get(self.tabs.currentIndex()) if hasattr(self, "tabs") else None
        if panel is not None:
            panel.mostrar(clave)
        else:
            self.ayuda.mostrar(clave)

    def _ayuda_foco(self):
        w = QApplication.focusWidget()
        while w is not None:
            clave = w.property("ayuda")
            if clave:
                self.abrir_ayuda(clave)
                return
            w = w.parentWidget()
        self.abrir_ayuda("flujo_trabajo")

    def _registrar(self, nombre, widget, clave_ayuda=None):
        self.campos[nombre] = widget
        if clave_ayuda:
            widget.setProperty("ayuda", clave_ayuda)
        return widget

    def _ancho_celda(self) -> int:
        """Ancho común de las celdas: 330 px o lo que necesite el texto más largo de la config dinámica de la jaula
        con la fuente del sistema, para que todas queden alineadas y ninguna corte el texto."""
        if not hasattr(self, "_ancho_cache"):
            fm = self.fontMetrics()
            textos = [T.texto_config(e, n, liq) for liq in (True, False) for cl in ("anticav", "antiruido")
                      for c in T.POR_CUERPO for e, n in T.configuraciones(c, cl, liq)]
            self._ancho_cache = max([330] + [fm.horizontalAdvance(t) + 40 for t in textos])
        return self._ancho_cache

    def _fila(self, grid, r, etiqueta, widget, clave, unidad: QWidget | None = None, ancho=None):
        ancho = self._ancho_celda() if ancho is None else ancho
        lbl = QLabel(etiqueta)
        grid.addWidget(lbl, r, 0)
        btn = boton_ir(self.abrir_ayuda, clave)
        grid.addWidget(btn, r, 1)
        if ancho:
            widget.setFixedWidth(ancho)
        grid.addWidget(widget, r, 2)
        if unidad is not None:
            grid.addWidget(unidad, r, 3)
        widget.setProperty("ayuda", clave)
        return [lbl, btn, widget] + ([unidad] if unidad is not None else [])

    def _tarjeta_kpi(self, clave: str, titulo: str) -> QFrame:
        f = QFrame()
        f.setObjectName("kpi")
        f.setStyleSheet(f"#kpi{{background:white;border:1px solid {BORDE_TABLERO};border-top:3px solid {ACENTO};"
                        "border-radius:6px}")
        f.setMinimumWidth(170)
        v = QVBoxLayout(f)
        v.setContentsMargins(10, 6, 10, 8)
        v.setSpacing(1)
        t = QLabel(titulo)
        t.setStyleSheet("color:#5b6b7d;font-size:8pt;font-weight:600;letter-spacing:1px")
        valor = QLabel("—")
        valor.setStyleSheet("color:#1f3550;font-size:15pt;font-weight:700")
        nota = QLabel("")
        nota.setStyleSheet("color:#5b6b7d;font-size:8pt")
        for w in (t, valor, nota):
            v.addWidget(w)
        self.kpi[clave] = (valor, nota)
        return f

    def _color_alertas(self, severidad):
        fondo, texto, leyenda = BARRA_ALERTAS[severidad]
        self.lbl_alertas.setText("ALERTAS" + (f"  ·  {leyenda.upper()}" if leyenda else ""))
        self.lbl_alertas.setStyleSheet(f"background:{fondo};color:{texto};font-weight:700;padding:5px 8px;"
                                       "letter-spacing:1px")

    def _llenar_kpi(self, vaciar: bool = False):
        res = self.res
        self._color_alertas(Severidad.ERROR if vaciar else (res.peor() if res is not None else None))
        for valor, nota in self.kpi.values():
            valor.setText("—")
            valor.setStyleSheet("color:#1f3550;font-size:15pt;font-weight:700")
            nota.setText("")
        self.lbl_trim_rec.setText("")
        if res is None or vaciar:
            return
        from .. import seleccion_trim
        sel = seleccion_trim.seleccionar(res)
        self.lbl_trim_rec.setText(f"<b>Trim recomendado:</b> {_html.escape(sel.trim)} "
                                  f"<span style='color:#5b6b7d'>(caso más exigente: {_html.escape(sel.caso_critico.caso)})</span>")
        pr = self.presentacion()
        nombres = [rc.caso.nombre for rc in res.informe.casos]
        sal = res.salidas
        i = max(range(len(sal)), key=lambda i: sal[i]["Cv"])
        self.kpi["Cv"][0].setText(fmt(sal[i]["Cv"]))
        self.kpi["Cv"][1].setText(f"caso {nombres[i]}")
        ap = [s["apertura"] * 100 for s in sal if s.get("apertura") is not None and not s.get("bajo_cv_minimo")]
        if any(s.get("bajo_cv_minimo") for s in sal):
            self.kpi["apertura"][0].setText(f"{E.BAJO_MINIMO} – {max(ap):.0f} %" if ap else E.BAJO_MINIMO)
            self.kpi["apertura"][1].setText("del recorrido, mín. a máx.")
        elif ap:
            self.kpi["apertura"][0].setText(f"{min(ap):.0f} – {max(ap):.0f} %")
            self.kpi["apertura"][1].setText("del recorrido, mín. a máx.")
        ruido = [(s["Lp"], n) for s, n in zip(sal, nombres) if s.get("Lp") is not None]
        if ruido:
            lp, n = max(ruido)
            self.kpi["ruido"][0].setText(f"{fmt(lp, 4)} dB(A)")
            self.kpi["ruido"][1].setText(f"caso {n}")
        clave_v = "v2" if res.dim.tipo == "liquido" else "v_valvula"
        vel = [(s[clave_v], n) for s, n in zip(sal, nombres) if s.get(clave_v) is not None]
        if vel:
            v, n = max(vel)
            self.kpi["velocidad"][0].setText(pr.vu(v, "velocidad", 3))
            self.kpi["velocidad"][1].setText(("tubería de salida" if clave_v == "v2" else "salida de la válvula")
                                             + f", caso {n}")
        peor = res.peor()
        texto = {Severidad.INFO: "Sin alertas", Severidad.ADVERTENCIA: "Advertencias",
                 Severidad.CRITICA: "Crítico", Severidad.ERROR: "Datos inválidos"}[peor]
        self.kpi["estado"][0].setText(texto)
        self.kpi["estado"][0].setStyleSheet(f"color:{COLORES[peor] if peor != Severidad.INFO else '#2e7d32'};"
                                            "font-size:15pt;font-weight:700")
        self.kpi["estado"][1].setText(f"{len(res.alertas)} alerta(s) en total")

    def _scroll(self, w):
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        return sc

    # ------------------------------------------------------------ 1-Sistema
    def _tab_instalacion(self) -> QWidget:
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("DATOS DE INSTALACIÓN", AZUL))

        g = QGroupBox("Identificación")
        grid = QGridLayout(g)
        self.ed_ident = {}
        for r, (k, et) in enumerate((("proyecto", "Proyecto"), ("cliente", "Cliente"), ("tag", "Tag"),
                                     ("servicio", "Servicio"), ("documento", "N.º de documento"),
                                     ("revision", "Revisión"), ("preparado", "Preparado por"),
                                     ("fecha", "Fecha"))):
            ed = self._registrar("id_" + k, Fecha() if k == "fecha" else QLineEdit())
            if k == "revision":
                ed.setText("0")
            self.ed_ident[k] = ed
            self._fila(grid, r, et, ed, "identificacion", ancho=140 if k == "fecha" else 380)
        grid.setColumnStretch(4, 1)
        lay.addWidget(g)

        g = QGroupBox("Válvula e instalación")
        grid = QGridLayout(g)
        r = 0
        self.cb_cuerpo = self._registrar("cuerpo", Combo())
        for c in CUERPOS.values():
            self.cb_cuerpo.addItem(c.nombre, c.clave)
        self.cb_cuerpo.currentIndexChanged.connect(self._cambio_cuerpo)
        self._fila(grid, r, "Estilo de válvula", self.cb_cuerpo, "estilo_cuerpo"); r += 1
        self.cb_rating = self._registrar("rating", Combo())
        for c in RATINGS:
            self.cb_rating.addItem(f"CL{c}", c)
        self.cb_rating.setCurrentIndex(1)
        self._fila(grid, r, "Rating", self.cb_rating, "rating"); r += 1
        self.cb_nps, self.cb_sch = {}, {}
        for lado in ("entrada", "salida"):
            cb = self._registrar("nps_" + lado, Combo())
            for n in tuberias.NPS:
                cb.addItem(tuberias.texto_nps(n), n)
            cb.setCurrentIndex(tuberias.NPS.index(4))
            self.cb_nps[lado] = cb
            self._fila(grid, r, f"Diámetro nominal tubería de {lado}", cb, "nps"); r += 1
        for lado in ("entrada", "salida"):
            cb = self._registrar("sch_" + lado, Combo())
            self.cb_sch[lado] = cb
            self._fila(grid, r, f"Schedule tubería de {lado}", cb, "cedula"); r += 1
            self.cb_nps[lado].currentIndexChanged.connect(lambda _=0, l=lado: self._cambio_nps(l))
            cb.currentIndexChanged.connect(self._copiar_tuberias)
            self._cambio_nps(lado)
        self.ed_ruido = self._registrar("ruido", QLineEdit("85"))
        self._fila(grid, r, "Ruido permitido", self.ed_ruido, "limite_ruido", QLabel("dB(A)"), ancho=ANCHO_CELDA); r += 1
        self.cb_conexion = self._registrar("conexion", Combo())
        self.cb_conexion.addItems(CONEXIONES)
        self.cb_conexion.setCurrentText("RF bridada")
        self._fila(grid, r, "Tipo de conexión a proceso", self.cb_conexion, "conexion"); r += 1
        self.f_Pd = FilaUnidad("P_diseno", "Presión de diseño", ("presion",), grid, r, self.abrir_ayuda, 1,
                               col=3); r += 1
        self.f_Td = FilaUnidad("T_diseno", "Temperatura de diseño", ("temperatura",), grid, r, self.abrir_ayuda, 1,
                               "T_diseno", col=3); r += 1
        for f in (self.f_Pd, self.f_Td):
            f.edits[0].setPlaceholderText("máx. operación")
        self.cb_cierre = self._registrar("cierre", Combo())
        self.cb_cierre.addItems(CIERRES)
        self.cb_cierre.setCurrentText("ANSI Clase IV")
        self._fila(grid, r, "Clase de cierre (shutoff)", self.cb_cierre, "clase_cierre"); r += 1
        grid.setColumnStretch(5, 1)
        lay.addWidget(g)
        nota = QLabel("Estos datos definen los diámetros interiores de tubería, los trims compatibles, el límite "
                      "de ruido y las verificaciones de rating, conexión y clase de cierre. Se copian "
                      "automáticamente a 2-Cálculos Válvula.")
        nota.setWordWrap(True)
        nota.setStyleSheet("color:#55606d;font-style:italic;padding:4px")
        lay.addWidget(nota)
        b = QPushButton("Continuar con 2-Cálculos Válvula →")
        b.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        h = QHBoxLayout()
        h.addWidget(b)
        h.addStretch()
        lay.addLayout(h)
        lay.addStretch()
        return self._scroll(cont)

    def _cambio_nps(self, lado):
        cb = self.cb_sch[lado]
        actual = cb.currentText() or "40"
        cb.blockSignals(True)
        cb.clear()
        ced = tuberias.cedulas_de(self.cb_nps[lado].currentData())
        cb.addItems(ced)
        cb.setCurrentText(actual if actual in ced else ("40" if "40" in ced else "STD"))
        cb.blockSignals(False)
        self._copiar_tuberias()

    def _copiar_tuberias(self):
        if not hasattr(self, "ed_sch"):
            return
        pr = self.presentacion()
        for lado in ("entrada", "salida"):
            nps = self.cb_nps[lado].currentData()
            sch = self.cb_sch[lado].currentText()
            self.ed_tub[lado].setText(tuberias.texto_nps(nps))
            try:
                di = tuberias.diametro_interior(nps, sch)
                self.ed_sch[lado].setText(f"{sch}   (DI {pr.vu(di, 'longitud')})")
            except tuberias.ErrorTuberia:
                self.ed_sch[lado].setText(sch)

    # ------------------------------------------------------------ 2-Cálculos Válvula
    def _tab_dimensionamiento(self) -> QWidget:
        cont = QWidget()
        lay = QVBoxLayout(cont)
        self.lbl_titulo_dim = titulo_seccion("DATOS DE ENTRADA — LÍQUIDOS", AZUL)
        lay.addWidget(self.lbl_titulo_dim)

        g = QGroupBox("Fluido, tubería y válvula")
        grid = QGridLayout(g)
        self.vis_g1: list[tuple[list, str]] = []      # (widgets, tipos en que se ven)
        r = 0
        self.cb_tipo_fluido = self._registrar("tipo_fluido", Combo())
        for k, t in CG.TIPOS.items():
            self.cb_tipo_fluido.addItem(t, k)
        self.cb_tipo_fluido.currentIndexChanged.connect(self._cambio_tipo_fluido)
        self._fila(grid, r, "Tipo de fluido", self.cb_tipo_fluido, "tipo_fluido"); r += 1
        self.cb_fluido = self._registrar("fluido", Combo())
        self.cb_fluido.addItems([USUARIO, *propiedades.FLUIDOS.keys()])
        self.cb_fluido.setCurrentText("Agua / vapor de agua")
        self.cb_fluido.currentIndexChanged.connect(self._cambio_fluido)
        self.vis_g1.append((self._fila(grid, r, "Fluido", self.cb_fluido, "fluido"), "LGV")); r += 1
        self.ed_comp_gn = self._registrar("composicion_gn", QLineEdit(propiedades.texto_composicion(
            propiedades.GN_TIPICO)))
        self.ed_comp_gn.setToolTip("% molar de cada componente separados por punto y coma; en blanco = composición "
                                   "típica. Componentes: " + ", ".join(propiedades.COMPONENTES_GN))
        self.lbl_comp_gn = QLabel("")
        self.lbl_comp_gn.setStyleSheet(f"color:{ACENTO};font-size:8pt")
        self.lbl_comp_gn.setWordWrap(True)
        self.ed_comp_gn.editingFinished.connect(self._comp_gn_resumen)
        self.ed_comp_gn.setCursorPosition(0)
        self.fila_comp_gn = self._fila(grid, r, "Composición del gas natural (% molar)", self.ed_comp_gn,
                                       "composicion_gn", self.lbl_comp_gn, ancho=420); r += 1
        self.cb_variante = self._registrar("variante", Combo())
        self.lbl_salinidad = QLabel("")
        self.lbl_salinidad.setStyleSheet(f"color:{ACENTO};font-size:8pt")
        self.lbl_salinidad.setWordWrap(True)
        self.fila_variante = self._fila(grid, r, "Calidad / variante del fluido", self.cb_variante,
                                        "variante_fluido", self.lbl_salinidad); r += 1
        self.cb_variante.currentIndexChanged.connect(self._cambio_variante)
        self.cb_agua_libre = self._registrar("agua_libre", Combo())
        self.cb_agua_libre.addItems(FS.AGUA_LIBRE)
        self.cb_agua_libre.currentIndexChanged.connect(self._fluido_a_materiales)
        self.cb_agua_libre.activated.connect(lambda *_: setattr(self, "_agua_usuario", True))
        self.fila_agua_libre = self._fila(grid, r, "Agua libre (fase acuosa)", self.cb_agua_libre, "agua_libre"); r += 1
        self.cb_tipo_caudal = self._registrar("tipo_caudal", Combo())
        self.cb_tipo_caudal.addItems(["Volumétrico", "Másico"])
        self.cb_tipo_caudal.currentIndexChanged.connect(self._cambio_tipo_caudal)
        self._fila(grid, r, "Tipo de caudal", self.cb_tipo_caudal, "tipo_caudal"); r += 1
        self.ed_tub, self.ed_sch = {}, {}
        for lado in ("entrada", "salida"):
            ed = QLineEdit()
            ed.setReadOnly(True)
            ed.setFocusPolicy(Qt.NoFocus)
            ed.setStyleSheet(f"background:{FONDO_AUTO}")
            self.ed_tub[lado] = ed
            self._fila(grid, r, f"Diámetro de tubería de {lado}", ed, "nps", QLabel("desde 1-Sistema")); r += 1
        for lado in ("entrada", "salida"):
            ed = QLineEdit()
            ed.setReadOnly(True)
            ed.setFocusPolicy(Qt.NoFocus)
            ed.setStyleSheet(f"background:{FONDO_AUTO}")
            self.ed_sch[lado] = ed
            self._fila(grid, r, f"Schedule de tubería de {lado}", ed, "cedula", QLabel("desde 1-Sistema")); r += 1
        self.cb_tamano = self._registrar("tamano", Combo())
        self._fila(grid, r, "Diámetro de válvula", self.cb_tamano, "tamano"); r += 1
        # v0.13.1: tipo de trim (sin jaula / con jaula) → guía y tipo de obturador, o jaula → config dinámica
        self.cb_tipo_trim = self._registrar("tipo_trim", Combo())
        self.cb_tipo_trim.currentIndexChanged.connect(self._cambio_tipo_trim)
        self.fila_tipo_trim = self._fila(grid, r, "Tipo de trim", self.cb_tipo_trim, "tipo_trim"); r += 1
        self.cb_guia = self._registrar("guia", Combo())
        self.cb_guia.currentIndexChanged.connect(self._cambio_guia)
        self.fila_guia = self._fila(grid, r, "Guía del obturador", self.cb_guia, "guia_obturador"); r += 1
        self.cb_trim = self._registrar("trim", Combo())
        self.cb_trim.currentIndexChanged.connect(self._cambio_trim)
        self.lbl_trim = self._fila(grid, r, "Estilo de trim", self.cb_trim, "trim")[0]; r += 1
        self.cb_jaula = self._registrar("jaula", Combo())
        self.cb_jaula.currentIndexChanged.connect(self._cambio_jaula)
        self.fila_jaula = self._fila(grid, r, "Jaula", self.cb_jaula, "clase_jaula"); r += 1
        self.cb_nivel = self._registrar("nivel", Combo())
        self.cb_nivel.currentIndexChanged.connect(self._cambio_trim)
        self.fila_nivel = self._fila(grid, r, "Config dinámica de la jaula", self.cb_nivel, "nivel_etapas"); r += 1
        self.cb_sentido = self._registrar("sentido", Combo())
        self.cb_sentido.currentIndexChanged.connect(self._cambio_estilo)
        self.fila_sentido = self._fila(grid, r, "Sentido de flujo", self.cb_sentido, "sentido_flujo"); r += 1
        self.cb_balance = self._registrar("balance", Combo())
        self.cb_balance.addItem("Desbalanceado", False)
        self.cb_balance.addItem("Balanceado", True)
        self.fila_balance = self._fila(grid, r, "Obturador balanceado o desbalanceado", self.cb_balance, "balance")
        r += 1
        self.cb_caract = self._registrar("caracteristica", Combo())
        for k, t in E.CARACTERISTICA.items():
            self.cb_caract.addItem(t, k)
        self.cb_caract.currentIndexChanged.connect(self._cambio_caracteristica)
        self._fila(grid, r, "Característica inherente", self.cb_caract, "caracteristica"); r += 1
        self.f_puerto = FilaUnidad("puerto", "Tamaño del trim (puerto) certificado", ("longitud",), grid, r,
                                   self.abrir_ayuda, 1, "trim_size")
        self.f_puerto.edits[0].setPlaceholderText("estimado")
        self.f_puerto.edits[0].setToolTip("En blanco: se estima con el diámetro de la válvula y el Cv nominal. "
                                          "Cargue el diámetro del puerto certificado de la válvula ofertada.")
        r += 1
        self.f_carrera = FilaUnidad("carrera", "Carrera nominal del vástago certificada", ("longitud",), grid, r,
                                    self.abrir_ayuda, 1, "carrera_nominal")
        self.f_carrera.edits[0].setPlaceholderText("estimada")
        self.f_carrera.edits[0].setToolTip("En blanco: carrera normalizada típica para el puerto. Solo globo y "
                                           "ángulo; en las rotativas la carrera es la rotación del eje.")
        r += 1
        self.ed_cv_red = self._registrar("Cv_reducido", QLineEdit())
        self.ed_cv_red.setPlaceholderText("estimado")
        self.ed_cv_red.setToolTip("Cv nominal certificado del trim reducido (hoja de datos del fabricante). En blanco: "
                                  "si el puerto certificado es menor que el del trim completo, el Cv se estima con "
                                  "la relación de áreas.")
        self.ed_cv_red.setFixedWidth(self.f_puerto.edits[0].sizeHint().width())
        self.ed_cv_red.setAlignment(Qt.AlignRight)
        lbl = QLabel("Cv certificado del trim reducido")
        grid.addWidget(lbl, r, 0)
        grid.addWidget(boton_ir(self.abrir_ayuda, "Cv_reducido"), r, 1)
        grid.addWidget(self.ed_cv_red, r, 3)
        self.ed_cv_red.setProperty("ayuda", "Cv_reducido")
        r += 1
        self.lbl_geo = QLabel("Se calcula con «Calcular».")
        self.lbl_geo.setStyleSheet("color:#2f6fb0;font-size:8pt")
        self.lbl_geo.setTextFormat(Qt.RichText)
        grid.addWidget(self.lbl_geo, r, 2, 1, 3)
        r += 1
        # Datos de ruido aerodinámico (compresibles); el trim de bajo ruido se elige arriba (jaula y nivel)
        sub = QLabel("<b>Datos para ruido aerodinámico (IEC 60534-8-3)</b>")
        grid.addWidget(sub, r, 0, 1, 4)
        self.vis_g1.append(([sub], "GVS")); r += 1
        self.f_Rn = FilaUnidad("Rn", "Distancia para ruido Rn", ("distancia",), grid, r, self.abrir_ayuda, 1, "Rn")
        self.f_Rn.edits[0].setText("1")
        nota_rn = QLabel("Para todas las condiciones")
        nota_rn.setStyleSheet("color:#555")
        grid.addWidget(nota_rn, r, 4)
        self.vis_g1.append((self.f_Rn.widgets() + [nota_rn], "GVS")); r += 1
        self.f_area = FilaUnidad("area_salida", "Área de salida de la válvula", ("area",), grid, r, self.abrir_ayuda,
                                 1, "area_salida")
        self.f_area.edits[0].setPlaceholderText("nominal")
        self.f_area.edits[0].setToolTip("En blanco: área del diámetro nominal de la válvula. "
                                         "Verifique la unidad seleccionada a la izquierda.")
        nota_area = QLabel("Para todas las condiciones")
        nota_area.setStyleSheet("color:#555")
        grid.addWidget(nota_area, r, 4)
        self.vis_g1.append((self.f_area.widgets() + [nota_area], "GVS")); r += 1
        grid.setColumnStretch(4, 1)
        lay.addWidget(g)

        g = QGroupBox("Condiciones de operación (deje en blanco los casos que no use)")
        grid = QGridLayout(g)
        encabezados_casos(grid)
        self.filas: dict[str, FilaUnidad] = {}
        self.tipos_fila: dict[str, str] = {}
        r = 1
        for k, et, mags, ay, tipos in ENTRADAS:
            if k == "#":
                sub = QLabel(f"<b>{et}</b>")
                grid.addWidget(sub, r, 0, 1, 3)
                self.vis_g1.append(([sub], tipos))
            else:
                self.filas[k] = FilaUnidad(k, et, mags, grid, r, self.abrir_ayuda, ayuda_clave=ay)
                self.tipos_fila[k] = tipos
            r += 1
        for k in self.filas:
            if k in ("P1", "P2", "T1"):
                continue
            e = self.filas[k].edits[CIERRE]
            e.setReadOnly(True)
            e.setFocusPolicy(Qt.NoFocus)
            e.setStyleSheet(f"background:{FONDO_NO_APLICA}")
            e.setToolTip("No aplica: en Tight Shutoff la válvula está cerrada")
        self.filas["caudal"].edits[CIERRE].setText("0")
        self.f_Pc = FilaUnidad("Pc", "Presión crítica", ("presion",), grid, r, self.abrir_ayuda, 1)
        self.vis_g1.append((self.f_Pc.widgets(), "L"))
        self.btn_prop = QPushButton("Calcular propiedades del fluido")
        self.btn_prop.clicked.connect(self._boton_propiedades)
        grid.addWidget(self.btn_prop, r, 4, 1, 3)
        r += 1
        self.lbl_nota_dim = QLabel()
        self.lbl_nota_dim.setWordWrap(True)
        self.lbl_nota_dim.setStyleSheet("color:#55606d;font-style:italic")
        grid.addWidget(self.lbl_nota_dim, r, 0, 1, 8)
        grid.setColumnStretch(8, 1)
        lay.addWidget(g)

        self.btn_calc = QPushButton("Calcular")
        self.btn_calc.setMinimumHeight(38)
        fb = self.btn_calc.font()
        fb.setBold(True)
        fb.setPointSize(fb.pointSize() + 2)
        self.btn_calc.setFont(fb)
        botones.calcular(self.btn_calc, "azul", "8px 18px")
        self.btn_calc.clicked.connect(self.calcular)
        lay.addWidget(self.btn_calc)

        # Resultados: tablero azul claro con indicadores clave y la tabla por caso
        lay.addSpacing(10)
        lay.addWidget(titulo_seccion("RESULTADOS", ACENTO))
        tablero = QFrame()
        tablero.setObjectName("tablero")
        tablero.setStyleSheet(f"#tablero{{background:{FONDO_TABLERO};border:1px solid {BORDE_TABLERO};"
                              "border-top:none}")
        tl = QVBoxLayout(tablero)
        tl.setContentsMargins(12, 12, 12, 12)
        tl.setSpacing(10)
        self.lbl_resumen = QLabel("Sin cálculo.")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setStyleSheet(f"background:white;padding:8px 10px;border:1px solid {BORDE_TABLERO};"
                                       f"border-left:4px solid {ACENTO};border-radius:4px;color:#1b2a3a")
        tl.addWidget(self.lbl_resumen)
        self.kpi: dict[str, tuple[QLabel, QLabel]] = {}
        fila_kpi = QHBoxLayout()
        fila_kpi.setSpacing(10)
        for k, titulo in (("Cv", "CV MÁXIMO REQUERIDO"), ("apertura", "APERTURA"),
                          ("ruido", "RUIDO MÁXIMO A 1 m"), ("velocidad", "VELOCIDAD MÁX. SALIDA"),
                          ("estado", "ESTADO")):
            fila_kpi.addWidget(self._tarjeta_kpi(k, titulo))
        fila_kpi.addStretch(1)
        tl.addLayout(fila_kpi)
        fila_trim = QHBoxLayout()
        self.lbl_trim_rec = QLabel("")
        self.lbl_trim_rec.setWordWrap(True)
        self.lbl_trim_rec.setStyleSheet("color:#1b2a3a")
        b = QPushButton("Selección de trim y manual (PDF)…")
        b.setToolTip("Genera un PDF con la selección de trim para este cálculo y el manual técnico completo")
        b.clicked.connect(lambda: self.exportar_manual_trim())
        fila_trim.addWidget(self.lbl_trim_rec, 1)
        fila_trim.addWidget(b)
        tl.addLayout(fila_trim)
        g = QWidget()
        grid = QGridLayout(g)
        grid.setContentsMargins(0, 4, 0, 0)
        grid.setVerticalSpacing(3)
        encabezados_casos(grid, primera="Resultado", ancho=ANCHO_SALIDA,
                          estilo=f"background:{FONDO_ENCABEZADO};color:{ACENTO};border-radius:3px;padding:3px")
        self.salidas: dict[str, FilaSalida] = {}
        self.vis_salidas: list[tuple[list, str]] = []
        r = 1
        for k, et, ay, mag, cif, tipos in SALIDAS:
            if k == "#":
                sub = QLabel(et)
                sub.setStyleSheet(f"color:{ACENTO};font-weight:700;padding-top:8px;"
                                  f"border-bottom:1px solid {BORDE_CELDA}")
                grid.addWidget(sub, r, 0, 1, 3)
                self.vis_salidas.append(([sub], tipos))
            else:
                fs = FilaSalida(k, et, ay, mag, cif, grid, r, self.abrir_ayuda)
                self.salidas[k] = fs
                self.vis_salidas.append((fs.widgets(), tipos))
            r += 1
        fs = self.salidas["carrera"]
        self.cb_carrera = self._registrar("carrera_salida", Combo())
        self.cb_carrera.addItems(["mm", "in"])
        self.cb_carrera.setFixedWidth(ANCHO_UNIDAD)
        self.cb_carrera.setToolTip("Unidad de la carrera de operación (pantalla y documentos)")
        self.cb_carrera.currentIndexChanged.connect(self._cambio_unidad_carrera)
        grid.addWidget(self.cb_carrera, fs.fila, 2)
        fs.lbl_unidad.hide()
        fs.extra.append(self.cb_carrera)
        self.cb_visc = self._registrar("visc_salida", Combo())
        self.cb_visc.addItems(["Dinámica", "Cinemática"])
        self.cb_visc.currentIndexChanged.connect(lambda: self.res and self._mostrar_salidas())
        fs = self.salidas["visc"]
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(fs.lbl)
        h.addWidget(self.cb_visc)
        h.addStretch()
        w = QWidget()
        w.setLayout(h)
        grid.addWidget(w, fs.fila, 0)
        fs.extra.append(w)
        grid.setColumnStretch(8, 1)
        tl.addWidget(g)
        lay.addWidget(tablero)

        self.lbl_alertas = titulo_seccion("ALERTAS", ACENTO)
        lay.addWidget(self.lbl_alertas)
        sp = QSplitter(Qt.Vertical)
        self.lista_alertas = QTreeWidget()
        self.lista_alertas.setHeaderLabels(["Severidad", "Caso", "Fenómeno", "Intensidad"])
        self.lista_alertas.setRootIsDecorated(False)
        self.lista_alertas.currentItemChanged.connect(self._detalle_alerta)
        self.detalle_alerta = QTextBrowser()
        self.detalle_alerta.setOpenLinks(False)
        self.detalle_alerta.anchorClicked.connect(lambda u: self.abrir_ayuda(u.toString()[6:]))
        sp.addWidget(self.lista_alertas)
        sp.addWidget(self.detalle_alerta)
        sp.setMinimumHeight(380)
        lay.addWidget(sp)
        self._copiar_tuberias()
        return self._scroll(cont)

    def _tab_vista(self, codigo) -> QWidget:
        w = QWidget()
        w.setObjectName("fondo_hoja")
        w.setAttribute(Qt.WA_StyledBackground, True)
        w.setStyleSheet("#fondo_hoja{background:white}")
        v = QVBoxLayout(w)
        h = QHBoxLayout()
        b1 = QPushButton("Exportar a Word…")
        b1.clicked.connect(lambda: self.exportar_word(codigo))
        b2 = QPushButton("Imprimir…")
        b2.clicked.connect(lambda: self.imprimir(codigo))
        h.addWidget(QLabel("Vista previa: se actualiza con cada cálculo."))
        h.addStretch()
        h.addWidget(b1)
        h.addWidget(b2)
        v.addLayout(h)
        vista = Vista()
        vista.setFixedWidth(ANCHO_A4)
        vista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        vista.setFrameShape(QFrame.Box)
        vista.setStyleSheet("QTextBrowser{background:white;border:1px solid #c5ccd4}")
        vista.document().setDocumentMargin(28)
        self.vistas[codigo] = vista
        hoja = QHBoxLayout()
        hoja.setContentsMargins(0, 0, 0, 0)
        hoja.addWidget(vista)
        hoja.addStretch(1)
        v.addLayout(hoja, 1)
        return w

    # ------------------------------------------------------------- eventos
    def cuerpo(self):
        return CUERPOS[self.cb_cuerpo.currentData()]

    def tipo(self) -> str:
        return self.cb_tipo_fluido.currentData() or "liquido"

    def letra(self) -> str:
        return LETRA[self.tipo()]

    def _balanceado(self) -> bool | None:
        return None if self.cuerpo().rotativa else self.cb_balance.currentData()

    def _cambio_cuerpo(self):
        c = self.cuerpo()
        desl = T.deslizante(c.clave)
        for w in self.fila_tipo_trim:
            w.setVisible(desl)
        self.cb_tipo_trim.blockSignals(True)
        previo = self.cb_tipo_trim.currentData()
        self.cb_tipo_trim.clear()
        for t in T.tipos(c.clave):
            self.cb_tipo_trim.addItem(T.TIPOS[t], t)
        self.cb_tipo_trim.setCurrentIndex(max(0, self.cb_tipo_trim.findData(previo)))
        self.cb_tipo_trim.setEnabled(self.cb_tipo_trim.count() > 1)
        self.cb_tipo_trim.blockSignals(False)
        self._cambio_tipo_trim(recalcular=False)
        for w in self.fila_balance:
            w.setVisible(not c.rotativa)
        actual = self.cb_tamano.currentData()
        self.cb_tamano.clear()
        self.cb_tamano.addItem("Automático", None)
        for p, dn, _ in TAMANOS:
            if c.nps_min <= p <= c.nps_max:
                self.cb_tamano.addItem(f"{tuberias.texto_nps(p)}  (DN {dn})", p)
        i = self.cb_tamano.findData(actual)
        self.cb_tamano.setCurrentIndex(max(0, i))
        self._cambio_trim()
        self._act_concordancia()

    def _llenar(self, cb: QComboBox, items: list[tuple[str, str]]):
        """Reemplaza las opciones del desplegable conservando la elegida si sigue disponible."""
        previo = cb.currentData()
        cb.blockSignals(True)
        cb.clear()
        for texto, dato in items:
            cb.addItem(texto, dato)
        cb.setCurrentIndex(max(0, cb.findData(previo)))
        cb.blockSignals(False)

    def _cambio_tipo_trim(self, *_, recalcular=True):
        """Sin jaula: guía y tipo de obturador. Con jaula: obturador cilíndrico, jaula y config dinámica."""
        c = self.cuerpo().clave
        desl = T.deslizante(c)
        tipo = self.cb_tipo_trim.currentData() if desl else None
        por_obt = tipo == "obturador"
        for w in self.fila_guia:
            w.setVisible(por_obt)
        for w in (*self.fila_jaula, *self.fila_nivel):
            w.setVisible(tipo == "jaula")
        self.cb_trim.setEnabled(tipo != "jaula")
        if por_obt:
            self._llenar(self.cb_guia, [(T.GUIAS[g].nombre, g) for g in T.guias(c)])
            for i in range(self.cb_guia.count()):
                self.cb_guia.setItemData(i, T.GUIAS[self.cb_guia.itemData(i)].nota, Qt.ToolTipRole)
            self._cambio_guia(recalcular=recalcular)
            return
        if tipo == "jaula":
            self.lbl_trim.setText("Tipo de obturador")
            self._llenar(self.cb_trim, [(T.OBTURADOR_JAULA, "cilindrico")])
            self.cb_trim.setItemData(0, "Cilindro hueco que abre las ventanas u orificios de la jaula; la "
                                        "característica la da la jaula.", Qt.ToolTipRole)
            liq = self.tipo() == "liquido"
            self._llenar(self.cb_jaula, [(T.CLASES_JAULA[k], k) for k in T.clases_jaula(c, liq)])
            self._cambio_jaula(recalcular=recalcular)
            return
        self.lbl_trim.setText("Estilo de trim")
        self._llenar(self.cb_trim, [(nombre_geometria(g), g) for g in geometrias(c)])
        for i in range(self.cb_trim.count()):
            self.cb_trim.setItemData(i, ESTILOS[clave_trim(c, self.cb_trim.itemData(i), "abre")].nombre,
                                     Qt.ToolTipRole)
        if recalcular:
            self._cambio_trim()

    def _cambio_jaula(self, *_, recalcular=True):
        """Jaula estándar: config dinámica bloqueada. Anticavitación o antiruido: cada construcción y nivel."""
        c = self.cuerpo().clave
        liq = self.tipo() == "liquido"
        cl = self.cb_jaula.currentData() or "estandar"
        cfg = T.configuraciones(c, cl, liq)
        if cfg:
            self._llenar(self.cb_nivel, [(T.texto_config(e, n, liq), f"{e}|{n}") for e, n in cfg])
            for i, (e, n) in enumerate(cfg):
                self.cb_nivel.setItemData(i, T.texto_config(e, n, liq, completo=True), Qt.ToolTipRole)
            self.cb_nivel.view().setMinimumWidth(self.cb_nivel.view().sizeHintForColumn(0) + 24)
        else:
            self._llenar(self.cb_nivel, [("No aplica (jaula estándar)", "")])
        self.cb_nivel.setEnabled(bool(cfg))
        if recalcular:
            self._cambio_trim()

    def _cambio_guia(self, *_, recalcular=True):
        c = self.cuerpo().clave
        g = self.cb_guia.currentData()
        if not g:
            return
        self.lbl_trim.setText("Tipo de obturador")
        self._llenar(self.cb_trim, [(T.ELEMENTOS[e].nombre, e) for e in T.obturadores(c, g)])
        for i in range(self.cb_trim.count()):
            k = T.clave_estilo(c, self.cb_trim.itemData(i), "abre")
            self.cb_trim.setItemData(i, ESTILOS[k].nombre, Qt.ToolTipRole)
        self.cb_guia.setToolTip(T.GUIAS[g].nota)
        if recalcular:
            self._cambio_trim()

    def eleccion(self) -> T.Eleccion | None:
        """Tipo, guía, obturador o jaula, sentido y nivel elegidos (None en cuerpos rotativos)."""
        c = self.cb_cuerpo.currentData()
        if c is None or not T.deslizante(c) or not self.cb_trim.currentData():
            return None
        tipo = self.cb_tipo_trim.currentData() or "obturador"
        sd = self.cb_sentido.currentData() or "abre"
        if tipo == "obturador":
            return T.Eleccion(tipo, self.cb_guia.currentData() or "", self.cb_trim.currentData(), sd)
        cfg = self.cb_nivel.currentData() or ""
        e, nv = cfg.split("|") if cfg and self.cb_jaula.currentData() != "estandar" else ("jaula_4v", "")
        return T.Eleccion(tipo, "", e, sd, nv)

    def trim_clave(self) -> str:
        """Clave de ESTILOS del trim, el sentido de flujo y el nivel elegidos en la solapa 2."""
        d = self.cb_trim.currentData()
        if not d or self.cb_cuerpo.currentData() is None:
            return ""
        el = self.eleccion()
        if el is None:
            return clave_trim(self.cuerpo().clave, d, self.cb_sentido.currentData() or "")
        return T.clave_estilo(self.cuerpo().clave, el.elemento, el.sentido, el.nivel)

    def trim_especial(self) -> tuple[str, str]:
        """(nivel anticavitación, nivel de bajo ruido) del trim elegido."""
        el = self.eleccion()
        if el is None:
            return "estandar", "estandar"
        return T.especial(el.elemento, el.nivel, self.tipo() == "liquido")

    def _cambio_trim(self):
        """Cambió el obturador, la jaula o su config dinámica: sentidos de flujo que admite y característica."""
        if not self.cb_trim.currentData():
            return
        c = self.cuerpo().clave
        desl = T.deslizante(c)
        el = self.eleccion()
        d = el.elemento if el else self.cb_trim.currentData()
        previo = self.cb_sentido.currentData()
        ops = T.sentidos(c, d) if desl else sentidos(c, d)
        self.cb_sentido.blockSignals(True)
        self.cb_sentido.clear()
        for sd in ops:
            self.cb_sentido.addItem(SENTIDOS[sd], sd)
        i = self.cb_sentido.findData(previo)
        self.cb_sentido.setCurrentIndex(max(0, i))
        self.cb_sentido.setEnabled(len(ops) > 1)
        self.cb_sentido.setToolTip("Sentido en que el flujo empuja al obturador. Es el mismo dato que «Flow» de la "
                                   "solapa 4, que lo toma de aquí." if ops != [""] else
                                   "En esta válvula el sentido del flujo no cambia los factores del trim.")
        self.cb_sentido.blockSignals(False)
        k = self.trim_clave()
        self.cb_caract.blockSignals(True)
        self.cb_caract.setCurrentIndex(self.cb_caract.findData(ESTILOS[k].caracteristica))
        self.cb_caract.blockSignals(False)
        self._cambio_estilo()

    def _aplicar_nivel(self):
        """El nivel o las etapas de la jaula especial reemplazan FL, xT, Fd y Kc de las condiciones de operación."""
        ac, ru = self.trim_especial()
        vals = {}
        if ac != "estandar":
            t = AC.TRIMS[ac]
            vals = {"FL": t.FL, "Fd": t.Fd, "Kc": t.Kc}
        elif ru != "estandar":
            t = CG.TRIMS_RUIDO[ru]
            vals = {"Fd": t.Fd, "xT": CG.xT_etapas(t.etapas)} if t.etapas > 1 else {"Fd": t.Fd}
        for j in FLUYEN:
            for clave, val in vals.items():
                self.filas[clave].edits[j].setText(f"{val:.3g}".replace(".", ","))

    def _cambio_estilo(self):
        """Factores típicos del trim con el sentido y la característica elegidos."""
        k = self.trim_clave()
        if not k:
            return
        e = ESTILOS[k]
        FL, xT, Fd = factores(k, self.cb_caract.currentData() or e.caracteristica)
        for j in FLUYEN:
            for clave, val in (("FL", FL), ("Fd", Fd), ("xT", xT)):
                self.filas[clave].edits[j].setText(f"{val:g}".replace(".", ","))
            kc = KC_TIPICO.get(k)
            self.filas["Kc"].edits[j].setText(f"{kc:g}".replace(".", ",") if kc else "")
        self._aplicar_nivel()
        self._caract_concordancia()
        self.cb_trim.setToolTip(e.nombre + (f"\n\n{e.nota}" if e.nota else ""))
        self._act_flujo_desde_trim(k)
        self._mat_nombres_componentes()

    def _cambio_caracteristica(self):
        k = self.trim_clave()
        if k and factores(k, "lineal") != factores(k, "isoporcentual"):
            self._cambio_estilo()

    def _caract_concordancia(self):
        """Vástago ascendente: lineal, isoporcentual o apertura rápida; rotativas: la propia del elemento."""
        k = self.trim_clave()
        if not k:
            return
        rot = self.cuerpo().rotativa
        el = self.eleccion()
        admite = T.ELEMENTOS[el.elemento].caracteristicas if el else (ESTILOS[k].caracteristica,)
        _bloquear_items(self.cb_caract, {t: "el trim elegido no la ofrece" for c, t in E.CARACTERISTICA.items()
                                         if c not in admite})
        if rot or self.cb_caract.currentData() not in admite:
            self.cb_caract.blockSignals(True)
            self.cb_caract.setCurrentIndex(self.cb_caract.findData(
                ESTILOS[k].caracteristica if ESTILOS[k].caracteristica in admite else admite[0]))
            self.cb_caract.blockSignals(False)
        self.cb_caract.setEnabled(not rot and len(admite) > 1)
        self.cb_caract.setToolTip(
            "En una válvula rotativa la característica la da la forma del disco, la bola o el segmento." if rot else
            "Curva de capacidad frente a la carrera: la define el perfil del obturador o las ventanas de la jaula. "
            "Elija la que ofrezca el fabricante para el estilo de trim elegido.")

    def _cambio_tipo_fluido(self):
        """Muestra solo las entradas y resultados del tipo de fluido elegido."""
        t, L = self.tipo(), self.letra()
        self.lbl_titulo_dim.setText(f"DATOS DE ENTRADA — {TITULO_TIPO[t]}")
        if hasattr(self, "cb_tipo_trim") and self.cb_cuerpo.currentData() is not None:
            self._cambio_tipo_trim()       # las jaulas de bajo ruido o anticavitación dependen del fluido
        for k, f in self.filas.items():
            ver = L in self.tipos_fila[k]
            for w in f.widgets():
                w.setVisible(ver)
        for ws, tipos in self.vis_g1 + self.vis_salidas:
            for w in ws:
                w.setVisible(L in tipos)
        for k, fs in self.salidas.items():
            et = ETIQUETA_SALIDA.get((k, L))
            if et:
                fs.lbl.setText(et)
        if t == "steam":
            self.cb_tipo_caudal.setCurrentIndex(1)
        self.cb_tipo_caudal.setEnabled(t != "steam")
        if t == "gas" and self.cb_fluido.currentText() == "Agua / vapor de agua":
            self.cb_fluido.setCurrentText("Aire")
        elif t == "liquido" and self.cb_fluido.currentText() == "Aire":
            self.cb_fluido.setCurrentText("Agua / vapor de agua")
        self._unidades_caudal(convertir=False)
        self._cambio_fluido()
        self.lbl_nota_dim.setText(NOTA_TIPO[t])
        self.T1_opcional()
        if self.res is not None and self.res.dim.tipo != t:
            self.res = None
            self._limpiar_resultados()

    def T1_opcional(self):
        tip = ("En vapor de agua, T1 en blanco = vapor saturado seco a P1." if self.tipo() == "steam" else "")
        for e in self.filas["T1"].edits:
            e.setPlaceholderText("saturado" if tip else "")
        self.filas["T1"].lbl.setToolTip(tip)

    def _limpiar_resultados(self):
        self.lbl_resumen.setText("Sin cálculo.")
        self.lbl_geo.setText("Se calcula con «Calcular».")
        self._llenar_kpi()
        self.lista_alertas.clear()
        self.detalle_alerta.clear()
        for fs in self.salidas.values():
            for c in fs.celdas:
                c.clear()
        self._actualizar_vistas()

    def _fluido_actual(self) -> str:
        return FS.AGUA if self.tipo() == "steam" else self.cb_fluido.currentText()

    def _cargar_variantes(self):
        """Opciones de calidad / variante según tipo y fluido (se conserva la elegida si sigue siendo válida)."""
        ops = FS.variantes(self.tipo(), self._fluido_actual())
        actual = self.cb_variante.currentText()
        self.cb_variante.blockSignals(True)
        self.cb_variante.clear()
        self.cb_variante.addItems(ops)
        if actual in ops:
            self.cb_variante.setCurrentText(actual)
        self.cb_variante.blockSignals(False)
        for w in self.fila_variante:
            w.setVisible(bool(ops))
        self._cambio_variante()

    def _cambio_variante(self):
        t, fl, var = self.tipo(), self._fluido_actual(), self.cb_variante.currentText()
        fija = FS.agua_libre_fija(t, fl, var)
        actual = self.cb_agua_libre.currentText()
        self.cb_agua_libre.blockSignals(True)
        self.cb_agua_libre.clear()
        if fija:
            self.cb_agua_libre.addItem(fija)
        else:
            self.cb_agua_libre.addItems(FS.AGUA_LIBRE)
            sug = FS.agua_libre_sugerida(t, fl, var)
            self.cb_agua_libre.setCurrentText(actual if actual in FS.AGUA_LIBRE and getattr(self, "_agua_usuario", False)
                                              else sug)
        self.cb_agua_libre.setEnabled(not fija)
        self.cb_agua_libre.blockSignals(False)
        self.cb_agua_libre.setToolTip("Lo impone el fluido elegido." if fija else "")
        sal = FS.salinidad_pct(t, fl, var, self._cloruros_materiales())
        c = FS.correccion_salina(sal)
        self.lbl_salinidad.setText(f"Propiedades corregidas por {c.texto}." if c else "")
        self._fluido_a_materiales()

    def _cloruros_materiales(self) -> float | None:
        """Cloruros (mg/L) informados en la tabla de agentes de 3-Materiales, si los hay."""
        if not hasattr(self, "mat_agentes"):
            return None
        total = None
        for fam, ag, un, ed, fa in self.mat_agentes:
            clave = ag.currentData()
            if clave not in ("cloruros", "nacl") or not ed.text().strip():
                continue
            try:
                from .. import quimica as Q
                n = Q.normalizar(Q.AgenteServicio(clave, un.currentText(), leer_numero(ed.text()), fa.currentText()),
                                 101.325, 1.0)
            except (ValueError, TypeError):
                continue
            if n.valor:
                total = (total or 0) + n.valor * (0.607 if clave == "nacl" else 1.0)
        return total

    def _fluido_a_materiales(self, *_):
        if hasattr(self, "_mat_fluido_heredado"):
            self._mat_fluido_heredado()

    def _cambio_fluido(self):
        self._agua_usuario = False
        self._cargar_variantes()
        t = self.tipo()
        manual = self.cb_fluido.currentText() == USUARIO
        self.btn_prop.setEnabled(not manual and t != "steam")
        auto = {"liquido": ("SG", "mu", "Pv"), "gas": ("M", "mu", "gamma", "Z1", "T2", "Z2"),
                "vapor": ("M", "rho1", "mu", "gamma", "T2", "rho2"), "steam": ()}[t]
        for k in PROPIEDADES:
            self.filas[k].solo_lectura(k in auto and not manual, FLUYEN)
        self.f_Pc.solo_lectura(not manual)
        gn = t == "gas" and self.cb_fluido.currentText() == propiedades.GAS_NATURAL
        for w in self.fila_comp_gn:
            w.setVisible(gn)
        if gn:
            self._comp_gn_resumen()

    def _composicion(self) -> dict | None:
        """Composición del gas natural en % molar (None si el fluido no es gas natural)."""
        if self.tipo() != "gas" or self.cb_fluido.currentText() != propiedades.GAS_NATURAL:
            return None
        return propiedades.leer_composicion(self.ed_comp_gn.text())

    def _comp_gn_resumen(self):
        try:
            c = self._composicion()
            if c is None:
                return
            M = propiedades.masa_molar_mezcla(c)
            self.lbl_comp_gn.setText(f"M = {fmt(M)} kg/kmol · SG = {fmt(M / 28.9647)} · {fmt(c.get('Metano', 0), 3)} % metano")
        except Exception as e:
            self.lbl_comp_gn.setText(str(e))

    def _magnitud_caudal(self) -> str:
        vol = self.cb_tipo_caudal.currentIndex() == 0
        if self.tipo() == "liquido":
            return "caudal_vol" if vol else "caudal_masico"
        return "caudal_gas_std" if vol and self.tipo() != "steam" else "caudal_masico"

    def _unidades_caudal(self, convertir: bool):
        f = self.filas["caudal"]
        mag = self._magnitud_caudal()
        if f.magnitud() == mag:
            return
        previos = []
        for j in FLUYEN:
            try:
                previos.append((j, f.valor_base(j), self._densidad_ref(j)))
            except ValueError:
                previos.append((j, None, None))
        f.unidad.blockSignals(True)
        f.unidad.clear()
        f.mag_de = {}
        for s in U.unidades_de(mag):
            f.unidad.addItem(s)
            f.mag_de[s] = mag
        f.unidad.setCurrentText(U.SISTEMAS[self.sistema][mag])
        f._ant = f.unidad.currentText()
        f.unidad.blockSignals(False)
        if not convertir:
            return
        a_masico = mag == "caudal_masico"
        for j, q, rho in previos:
            if q is None or not rho:
                f.edits[j].setText("")
                continue
            f.poner_base(j, q * rho if a_masico else q / rho)

    def _densidad_ref(self, j: int) -> float | None:
        """Densidad que relaciona el caudal volumétrico con el másico: real (líquido) o normal (gas)."""
        if self.tipo() == "liquido":
            sg = leer_numero(self.filas["SG"].edits[j].text())
            return sg * RHO_AGUA_15C if sg else None
        M = self.filas["M"].valor_base(j)
        return CG.densidad_normal(M) if M else None

    def _cambio_tipo_caudal(self):
        """Pasa el caudal ingresado al otro tipo (no borra datos)."""
        self._unidades_caudal(convertir=True)

    def aplicar_sistema(self, sistema: str):
        self.sistema = sistema
        if self.cb_sistema.currentText() != sistema:
            self.cb_sistema.blockSignals(True)
            self.cb_sistema.setCurrentText(sistema)
            self.cb_sistema.blockSignals(False)
        pref = U.SISTEMAS[sistema]
        man = "bar g" if sistema == "SI" else "psig"
        F = self.filas
        F["caudal"].elegir(pref[F["caudal"].magnitud()])
        for k in ("P1", "P2"):
            F[k].elegir(man)
        F["Pv"].elegir(pref["presion"])
        for k in ("T1", "T2"):
            F[k].elegir(pref["temperatura"])
        for k in ("rho1", "rho2"):
            F[k].elegir(pref["densidad"])
        F["mu"].elegir("cP")
        if F["M"].unidad.currentText() != "SG (aire = 1)":
            F["M"].elegir(pref["masa_molar"])
        self.f_Pc.elegir(pref["presion"])
        self.f_Pd.elegir(man)
        self.f_Td.elegir(pref["temperatura"])
        self.f_Rn.elegir(pref["distancia"])
        self.f_area.elegir(pref["area"])
        self.f_puerto.elegir(pref["longitud"])
        self.f_carrera.elegir(pref["longitud"])
        self.cb_carrera.blockSignals(True)
        self.cb_carrera.setCurrentText(pref["carrera"])
        self.cb_carrera.blockSignals(False)
        self.f_aire.elegir(man)
        self.f_rango.elegir(man)
        self.f_vastago.elegir(pref["longitud"])
        self.f_friccion.elegir(pref["fuerza"])
        for k, f in self.f_cert.items():
            f.elegir(man if f.magnitud() == "presion" else pref["par"] if k.startswith("cert_par") else
                     pref[f.magnitud()] if f.magnitud() != "longitud" else pref["longitud"])
        self.f_cert["cert_nominal"].elegir(pref["fuerza"])
        self._copiar_tuberias()
        if self.res is not None:
            self.calcular(silencioso=True)

    def presentacion(self) -> E.Presentacion:
        """Unidades de los resultados y documentos: las mismas de las entradas."""
        u = dict(U.SISTEMAS[self.sistema])
        F = getattr(self, "filas", None)
        if F:
            up = F["P1"].unidad.currentText()
            u["presion"] = up
            u["presion_dif"] = DIF.get(up, u["presion_dif"])
            u["presion_abs"] = F["Pv"].unidad.currentText() if self.tipo() == "liquido" else DIF_ABS.get(up, up)
            u["temperatura"] = F["T1"].unidad.currentText()
            u["temperatura_dif"] = {"K": "K", "°C": "°C", "°F": "°F", "°R": "°F"}[u["temperatura"]]
            u[F["caudal"].magnitud()] = F["caudal"].unidad.currentText()
            u["viscosidad_din"] = F["mu"].unidad.currentText()
        if getattr(self, "cb_carrera", None) is not None:
            u["carrera"] = self.cb_carrera.currentText()
            u["masa_molar"] = F["M"].unidad.currentText()
            u["densidad"] = F["rho1"].unidad.currentText()
            u["distancia"] = self.f_Rn.unidad.currentText()
            u["area"] = self.f_area.unidad.currentText()
        return E.Presentacion(u)

    # ---------------------------------------------------------- lectura
    def _float(self, ed: QLineEdit, nombre: str, opcional=False) -> float | None:
        try:
            v = leer_numero(ed.text())
        except ValueError:
            raise ValueError(f"El valor «{ed.text()}» de {nombre} no es un número.") from None
        if v is None and not opcional:
            raise ValueError(f"Falta el dato {nombre}.")
        return v

    def _columna_usada(self, j: int) -> bool:
        claves = ("P1", "P2", "T1") if j == CIERRE else ("caudal", "P1", "P2", "T1")
        return any(self.filas[k].edits[j].text().strip() for k in claves)

    def _activos(self) -> list[int]:
        return [j for j in FLUYEN if self._columna_usada(j)]

    def _boton_propiedades(self):
        try:
            self.calcular_propiedades()
        except (ValueError, propiedades.ErrorPropiedades) as e:
            QMessageBox.warning(self, "Propiedades", str(e))
        except ErrorDatos as e:
            QMessageBox.warning(self, "Propiedades", "\n".join(a.mensaje for a in e.alertas))

    def calcular_propiedades(self):
        self._cambio_variante()          # salinidad con los cloruros vigentes de 3-Materiales
        fluido = self.cb_fluido.currentText()
        t = self.tipo()
        if fluido == USUARIO or t == "steam":
            return
        F = self.filas
        for j in self._activos():
            P1, P2, T1 = F["P1"].valor_base(j), F["P2"].valor_base(j), F["T1"].valor_base(j)
            if P1 is None or T1 is None:
                raise ValueError(f"Caso {CASOS[j]}: ingrese P1 y T1 para obtener las propiedades.")
            if t == "liquido":
                p = propiedades.liquido(fluido, P1, T1)
                c = FS.correccion_salina(FS.salinidad_pct(t, fluido, self.cb_variante.currentText(),
                                                          self._cloruros_materiales()))
                fr, fm, fp = (c.f_rho, c.f_mu, c.f_Pv) if c else (1.0, 1.0, 1.0)
                F["SG"].edits[j].setText(_num(p.rho * fr / RHO_AGUA_15C))
                F["mu"].poner_base(j, p.mu * fm)
                F["Pv"].poner_base(j, p.Pv * fp)
                self.f_Pc.poner_base(0, p.Pc)
                continue
            if P2 is None:
                raise ValueError(f"Caso {CASOS[j]}: ingrese P2 para obtener las condiciones de salida.")
            e = CG.resolver_estado(CG.CasoGas(CASOS[j], 1.0, None, P1, P2, T1), t, fluido, self._composicion())
            F["M"].poner_base(j, e.M)
            F["mu"].poner_base(j, e.mu)
            F["gamma"].edits[j].setText(_num(e.gamma))
            F["T2"].poner_base(j, e.T2)
            if t == "gas":
                F["Z1"].edits[j].setText(_num(e.Z1))
                F["Z2"].edits[j].setText(_num(e.Z2))
            else:
                F["rho1"].poner_base(j, e.rho1)
                F["rho2"].poner_base(j, e.rho2)

    def _leer(self):
        """Datos de las seis solapas: identificación, instalación, dimensionamiento, materiales y equipo."""
        return (*self._leer_calculo(), self._servicio_materiales(), self._equipo_datos())

    def _leer_calculo(self):
        ident = Identificacion(**{k: ed.text().strip() for k, ed in self.ed_ident.items()})
        inst = Instalacion(
            cuerpo=self.cb_cuerpo.currentData(), rating=self.cb_rating.currentData(),
            nps_entrada=self.cb_nps["entrada"].currentData(), nps_salida=self.cb_nps["salida"].currentData(),
            sch_entrada=self.cb_sch["entrada"].currentText(), sch_salida=self.cb_sch["salida"].currentText(),
            ruido_permitido=self._float(self.ed_ruido, "ruido permitido"), conexion=self.cb_conexion.currentText(),
            P_diseno=self.f_Pd.valor_base(0), T_diseno=self.f_Td.valor_base(0), cierre=self.cb_cierre.currentText())
        F = self.filas
        t = self.tipo()
        activos = self._activos()
        if not activos:
            raise ValueError("Cargue al menos un caso de operación con caudal (mínimo, normal, máximo o "
                             "transitorio).")
        vol = self._magnitud_caudal() != "caudal_masico"
        casos = []
        for j in activos:
            def req(k):
                v = F[k].valor_base(j)
                if v is None:
                    raise ValueError(f"Caso {CASOS[j]}: falta «{F[k].lbl.text()}».")
                return v

            def opc(k):
                return F[k].valor_base(j)
            q = req("caudal")
            if t == "liquido":
                casos.append(CasoLiquido(CASOS[j], q if vol else None, None if vol else q, req("P1"), req("P2"),
                                         req("T1"), req("SG"), req("mu"), req("Pv"), req("FL"), req("Fd"),
                                         F["Kc"].valor_base(j), criterio=j != 4))
                continue
            gas, vap = t == "gas", t == "vapor"
            casos.append(CasoGas(
                CASOS[j], None if vol else q, q if vol else None, req("P1"), req("P2"),
                opc("T1") if t == "steam" else req("T1"),
                M=None if t == "steam" else req("M"), mu=None if t == "steam" else req("mu"),
                gamma=None if t == "steam" else req("gamma"), Z1=req("Z1") if gas else None,
                rho1=req("rho1") if vap else None, xT=req("xT"), FL=req("FL"), Fd=req("Fd"),
                T2=opc("T2"), Z2=opc("Z2") if gas else None, rho2=opc("rho2") if vap else None,
                criterio=j != 4))
        cierre = None
        if self._columna_usada(CIERRE):
            P1, P2 = F["P1"].valor_base(CIERRE), F["P2"].valor_base(CIERRE)
            if P1 is None or P2 is None:
                raise ValueError("Caso Tight Shutoff: cargue la presión de entrada y la de salida con la "
                                 "válvula cerrada.")
            cierre = CasoCierre(CASOS[CIERRE], P1, P2, F["T1"].valor_base(CIERRE))
        fluido = None if self.cb_fluido.currentText() == USUARIO else self.cb_fluido.currentText()
        if t == "liquido":
            Pc = self.f_Pc.valor_base(0)
            if Pc is None:
                raise ValueError("Falta la presión crítica del líquido.")
            return ident, inst, Dimensionamiento(casos, Pc, self.trim_clave(), self.cb_tamano.currentData(),
                                                 self.cb_caract.currentData(), fluido, cierre,
                                                 balanceado=self._balanceado(), **self._geo_cert(),
                                                 anticav=self.trim_especial()[0], guia=self._guia(),
                                                 **self._datos_fluido())
        ruido_g = RuidoAerodinamico(self.trim_especial()[1], self.f_Rn.valor_base(0) or 1.0,
                                    self.f_area.valor_base(0))
        dim = Dimensionamiento(casos, None, self.trim_clave(), self.cb_tamano.currentData(),
                               self.cb_caract.currentData(), "Agua / vapor de agua" if t == "steam" else fluido,
                               cierre, tipo=t, ruido=ruido_g, balanceado=self._balanceado(), **self._geo_cert(),
                               composicion=self._composicion(), guia=self._guia(), **self._datos_fluido())
        return ident, inst, dim

    def _guia(self) -> str:
        el = self.eleccion()
        return el.guia if el else ""

    def _geo_cert(self) -> dict:
        """Puerto y carrera certificados (en blanco = estimados por el programa)."""
        out = {}
        for k, f in (("puerto_mm", self.f_puerto), ("carrera_mm", self.f_carrera)):
            v = f.valor_base(0)
            if v is not None and v <= 0:
                raise ValueError(f"«{f.lbl.text()}» debe ser mayor que cero.")
            out[k] = v
        t = self.ed_cv_red.text().strip()
        cv = leer_numero(t) if t else None
        if t and (cv is None or cv <= 0):
            raise ValueError("«Cv certificado del trim reducido» debe ser un número mayor que cero.")
        out["Cv_reducido_cert"] = cv
        return out

    def _datos_fluido(self) -> dict:
        t, fl, var = self.tipo(), self._fluido_actual(), self.cb_variante.currentText()
        agua = self.cb_agua_libre.currentText()
        sal = FS.salinidad_pct(t, fl, var, self._cloruros_materiales()) if fl != USUARIO else 0.0
        return {"variante": var, "agua_libre": "" if agua == FS.AUTO_AGUA else agua, "salinidad_pct": sal}

    def calcular(self, silencioso: bool = False):
        pr = self.presentacion()
        modelos.PRESENTACION.update({k: pr.u[k] for k in modelos.PRESENTACION})
        try:
            self.calcular_propiedades()
            self.res = calcular(*self._leer())
        except ErrorDatos as e:
            self._mostrar_errores(e.alertas)
            return
        except (ValueError, propiedades.ErrorPropiedades, CapacidadInsuficiente) as e:
            if not silencioso:
                QMessageBox.warning(self, "Datos incompletos o inválidos", str(e))
            return
        self._mostrar()
        self.statusBar().showMessage("Cálculo terminado. Memoria, hoja de datos e informe técnico actualizados.")

    def _mostrar_errores(self, alertas):
        self.lista_alertas.clear()
        for a in alertas:
            it = QTreeWidgetItem([NOMBRE_SEV[a.severidad], "", a.titulo, ""])
            it.setForeground(0, QColor(COLORES[a.severidad]))
            it.setData(0, Qt.UserRole, a)
            self.lista_alertas.addTopLevelItem(it)
        if alertas:
            self.lista_alertas.setCurrentItem(self.lista_alertas.topLevelItem(0))
        self.lbl_resumen.setText("<b style='color:#7d1f9e'>No se pudo calcular: hay datos inválidos. "
                                 "Vea las alertas.</b>")
        self._llenar_kpi(vaciar=True)
        self.tabs.setCurrentIndex(1)

    # ----------------------------------------------------------- mostrar
    def _mostrar(self):
        res = self.res
        A = next((x.get("A_salida") for x in res.salidas if x.get("A_salida")), None)
        u = self.f_area.unidad.currentText()
        self.f_area.edits[0].setPlaceholderText(
            f"nominal: {fmt(U.desde_base(A, 'area', u))}" if A and not self.f_area.edits[0].text().strip()
            else "nominal")
        peor = res.peor()
        estado = {Severidad.INFO: ("#2e7d32", "Sin fenómenos que requieran acción."),
                  Severidad.ADVERTENCIA: ("#d9771e", "Hay advertencias para revisar."),
                  Severidad.CRITICA: ("#c0392b", "Hay condiciones críticas: vea las alertas y el informe técnico."),
                  Severidad.ERROR: ("#7d1f9e", "Hay datos inválidos.")}[peor]
        geo = res.geometria
        tr = res.trim_reducido
        txt_geo = _html.escape(f"Calculado: {geo.nombre_puerto.lower()} {geo.texto_puerto} · "
                               + (geo.texto_carrera.lower() if geo.rotativa else f"carrera {geo.texto_carrera}"))
        if tr is not None:
            txt_geo += (f"<br><b>Trim completo típico:</b> puerto {fraccion_in(tr.puerto_tipico_mm / 25.4)}, Cv "
                        f"{fmt(tr.Cv_tipico)} · <b>trim reducido:</b> puerto {fraccion_in(tr.puerto_mm / 25.4)}, "
                        f"<b>Cv {_html.escape(tr.texto_Cv)}</b>, usado en apertura, carrera y actuador")
        else:
            txt_geo += f" · Cv nominal típico {fmt(res.Cv_nominal)}"
        self.lbl_geo.setText(txt_geo)
        self.lbl_resumen.setText(
            f"<b>Válvula: {_html.escape(E._valvula_resumen(res))}</b><br>"
            f"{_html.escape(geo.nombre_puerto)}: <b>{_html.escape(geo.texto_puerto)}</b> · "
            f"{'Rotación' if geo.rotativa else 'Carrera nominal'}: <b>{_html.escape(geo.texto_carrera)}</b><br>"
            f"Cv máximo requerido: <b>{fmt(max(s['Cv'] for s in res.salidas))}</b> · "
            f"<span style='color:{estado[0]}'><b>{estado[1]}</b></span>")
        self._mostrar_salidas()
        self._llenar_kpi()
        self._mostrar_materiales()
        self._mostrar_equipo()
        self.lista_alertas.clear()
        for caso, a in res.alertas:
            inten = ""
            if a.intensidad is not None:
                n = int(round(a.intensidad / 10))
                inten = "█" * n + "░" * (10 - n) + f" {a.intensidad:.0f} %" + (f" {a.nivel}" if a.nivel else "")
            it = QTreeWidgetItem([NOMBRE_SEV[a.severidad], caso, a.titulo, inten])
            it.setForeground(0, QColor(COLORES[a.severidad]))
            it.setForeground(3, QColor(COLORES[a.severidad]))
            it.setData(0, Qt.UserRole, a)
            self.lista_alertas.addTopLevelItem(it)
        for i in range(4):
            self.lista_alertas.resizeColumnToContents(i)
        if self.lista_alertas.topLevelItemCount():
            self.lista_alertas.setCurrentItem(self.lista_alertas.topLevelItem(0))
        else:
            self.detalle_alerta.setHtml("<p>Sin alertas.</p>")
        self._actualizar_vistas()

    def _mostrar_salidas(self):
        res, pr = self.res, self.presentacion()
        nombres = [rc.caso.nombre for rc in res.informe.casos]
        cin = self.cb_visc.currentIndex() == 1
        t = res.dim.tipo
        if t == "liquido":
            vol = all(c.Q is not None for c in res.dim.casos)
            otro, clave_otro = ("caudal_masico", "W") if vol else ("caudal_vol", "Q")
            et_otro = "Flujo másico" if vol else "Caudal volumétrico"
        elif t == "steam":
            otro, clave_otro, et_otro = "caudal_vol", "Q1", "Caudal volumétrico real (entrada)"
        else:
            vol = all(c.QN is not None for c in res.dim.casos)
            otro, clave_otro = ("caudal_masico", "W") if vol else ("caudal_gas_std", "QN")
            et_otro = "Flujo másico" if vol else "Caudal volumétrico estándar"
        self.salidas["caudal_otro"].lbl.setText(et_otro)
        rot = res.geometria.rotativa
        fs = self.salidas["carrera"]
        fs.lbl.setText("Rotación de operación" if rot else "Carrera de operación")
        self.cb_carrera.setVisible(not rot)
        fs.lbl_unidad.setVisible(rot)
        for k, fs in self.salidas.items():
            mag = fs.magnitud
            if k == "carrera" and rot:
                mag = "°"
            if k == "visc":
                mag = "viscosidad_cin" if cin else "viscosidad_din"
            elif k == "caudal_otro":
                mag = otro
            fs.lbl_unidad.setText(pr.un(mag) if mag in pr.u else ("" if mag in (None, "texto") else mag))
            for j, caso in enumerate(CASOS):
                txt = ""
                if j == CIERRE and res.dim.cierre is not None:
                    c = res.dim.cierre
                    if k == "dP":
                        txt = pr.v(c.dP, "presion_dif", fs.cifras)
                    elif k == "dP_P1":
                        txt = fmt(c.dP / c.P1, fs.cifras)
                    elif k in ("condicion", "tipo_calculo"):
                        txt = "cierre"
                elif caso in nombres:
                    s = res.salidas[nombres.index(caso)]
                    if k == "visc":
                        v = s["nu"] if cin else s["mu"]
                    elif k == "apertura":
                        v = s["apertura"] * 100
                    elif k == "caudal_otro":
                        v = s[clave_otro]
                    elif k == "carrera":
                        v = s.get("rotacion") if res.geometria.rotativa else s.get("carrera_mm")
                    else:
                        v = s.get(ALIAS_SALIDA.get(k, k))
                    if mag == "texto":
                        txt = v or ""
                    elif mag in pr.u:
                        txt = pr.v(v, mag, fs.cifras)
                    else:
                        txt = fmt(v, fs.cifras)
                    if k in ("apertura", "carrera") and s.get("bajo_cv_minimo"):
                        txt = E.BAJO_MINIMO
                c = fs.celdas[j]
                c.setText(txt)
                c.setToolTip(txt if mag == "texto" else "")
                if txt == E.BAJO_MINIMO:
                    c.setToolTip(f"Cv requerido menor que el Cv mínimo controlable de la válvula "
                                 f"({fmt(s.get('Cv_minimo'), 3)}): ver la alerta.")
                if mag == "texto":
                    c.setAlignment(Qt.AlignLeft)
                    c.setCursorPosition(0)
                    c.setToolTip(txt)

    def _cambio_unidad_carrera(self, *_):
        if self.res is not None:
            self._mostrar_salidas()
            self._actualizar_vistas()

    def _detalle_alerta(self, it, _=None):
        if it is None:
            return
        a = it.data(0, Qt.UserRole)
        partes = [f"<h3 style='color:{COLORES[a.severidad]}'>{_html.escape(a.titulo)}</h3>",
                  f"<p>{_html.escape(a.mensaje)}</p>"]
        if a.intensidad is not None:
            partes.append(f"<p><b>Intensidad:</b> {a.intensidad:.0f} %" + (f" ({a.nivel})" if a.nivel else "") + "</p>")
        if a.remedios:
            partes.append("<p><b>Posibles soluciones:</b></p><ul>"
                          + "".join(f"<li>{_html.escape(r)}</li>" for r in a.remedios) + "</ul>")
        if a.referencia:
            partes.append(f"<p><i>Referencia: {_html.escape(a.referencia)}</i></p>")
        if ayuda.obtener(a.codigo):
            partes.append(f"<p><a href='ayuda:{a.codigo}'>Ver la explicación del fenómeno a la derecha…</a></p>")
        self.detalle_alerta.setHtml("".join(partes))

    # -------------------------------------------------------- entregables
    def _documentos(self, codigo):
        pr = self.presentacion()
        codigos = list(E.CONSTRUCTORES) if codigo == "todos" else [codigo]
        return [E.CONSTRUCTORES[c](self.res, pr) for c in codigos]

    def _imagen(self):
        from ..grafico import imagen_cv
        return imagen_cv(self.res)

    def _actualizar_vistas(self):
        if self.res is None:
            for v in self.vistas.values():
                v.setHtml("<p style='color:#55606d'>Todavía no hay cálculo. Complete 1-Sistema y "
                          "2-Cálculos Válvula y presione <b>Calcular</b>.</p>")
            return
        img = self._imagen()
        for codigo, v in self.vistas.items():
            v.imagen = img
            v.setHtml(E.a_html(self._documentos(codigo)[0]))

    def _hay_calculo(self) -> bool:
        if self.res is None:
            QMessageBox.information(self, "Sin cálculo", "Primero realice un cálculo.")
            return False
        return True

    def exportar_manual_trim(self, ruta: str | None = None):
        """PDF del manual de selección de trim; con un cálculo hecho, empieza por la selección de esta válvula."""
        from .. import manual_trim
        base = (self.res.ident.tag or "valvula").replace("/", "-").replace("\\", "-") if self.res else ""
        nombre = f"{base}_seleccion_de_trim.pdf" if base else "Manual_seleccion_de_trim.pdf"
        if not ruta:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar manual de selección de trim", nombre, "PDF (*.pdf)")
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"
        manual_trim.exportar_pdf(ruta, self.res, self.presentacion() if self.res else None)
        self.statusBar().showMessage(f"PDF guardado: {ruta}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
        return ruta

    def exportar_word(self, codigo: str, ruta: str | None = None):
        if not self._hay_calculo():
            return
        docs = self._documentos(codigo)
        base = (self.res.ident.tag or "valvula").replace("/", "-").replace("\\", "-")
        nombre = f"{base}_{'entregables' if codigo == 'todos' else codigo}.docx"
        if not ruta:
            ruta, _ = QFileDialog.getSaveFileName(self, "Exportar a Word", nombre, "Documento de Word (*.docx)")
        if not ruta:
            return
        if not ruta.lower().endswith(".docx"):
            ruta += ".docx"
        from ..grafico import png_cv
        try:
            E.a_docx(docs, ruta, png_cv(self.res))
        except OSError as e:
            QMessageBox.warning(self, "No se pudo guardar", f"No se pudo escribir {ruta}: {e}")
            return
        self.statusBar().showMessage(f"Documento guardado: {ruta}")
        return ruta

    def documento_impresion(self, codigo: str) -> QTextDocument:
        partes = []
        for k, d in enumerate(self._documentos(codigo)):
            h = E.a_html(d)
            cuerpo = h[h.index("<body>") + 6:h.index("</body>")]
            partes.append(cuerpo if k == 0 else f"<div style='page-break-before:always'>{cuerpo}</div>")
        doc = QTextDocument()
        doc.setHtml(f"<html><head><style>{E.CSS}</style></head><body>{''.join(partes)}</body></html>")
        doc.addResource(QTextDocument.ImageResource, QUrl("grafico://cv"), self._imagen())
        return doc

    def imprimir(self, codigo: str):
        if not self._hay_calculo():
            return
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("Imprimir entregable")
        if dlg.exec() == QDialog.Accepted:
            self.documento_impresion(codigo).print_(printer)

    # ------------------------------------------------------------ archivo
    def _todas_las_filas(self):
        return [*self.filas.values(), self.f_Pc, self.f_Pd, self.f_Td, self.f_Rn, self.f_area, self.f_puerto,
                self.f_carrera, self.f_aire, self.f_vastago, self.f_friccion, self.f_rango, *self.f_cert.values()]

    def _estado(self) -> dict:
        s = {"version": __version__, "sistema": self.sistema, "campos": {}, "filas": {}}
        for k, w in self.campos.items():
            s["campos"][k] = w.currentText() if isinstance(w, QComboBox) else w.text()
        for f in self._todas_las_filas():
            s["filas"][f.clave] = {"unidad": f.unidad.currentText(), "valores": [e.text() for e in f.edits]}
        s["materiales"] = self._mat_estado()
        s["equipo"] = {k: (w.currentText() if isinstance(w, QComboBox) else w.text()) for k, w in self.eq_w.items()}
        return s

    def _cargar(self, s: dict):
        self.aplicar_sistema(s.get("sistema", "SI"))
        s = _migrar_fluido(s)
        v0130 = None
        if s.get("campos", {}).get("tipo_trim") in ("Guiado por obturador", "Guiado por jaula"):
            s = {**s, "campos": dict(s["campos"])}           # v0.13.0: el elemento y el nivel se eligen después
            v0130 = {k: s["campos"].pop(k, "") for k in ("tipo_trim", "guia", "trim", "nivel")}
        for k, v in s.get("campos", {}).items():
            w = self.campos.get(k)
            if isinstance(w, QComboBox):
                i = w.findText(v)
                if i < 0 and v in NOMBRES_ANTERIORES:
                    i = w.findData(NOMBRES_ANTERIORES[v])
                if i < 0 and w is self.cb_nivel and self.cb_nivel.count() > 1:   # redacción de v0.13.1
                    cfg = T.config_desde_texto(self.cuerpo().clave, self.tipo() == "liquido", v)
                    i = w.findData(f"{cfg[0]}|{cfg[1]}") if cfg else -1
                if i < 0 and w is self.cb_trim:   # proyectos de v0.11.0 y anteriores: el trim incluía el sentido
                    if self._migrar_trim(s["campos"]):
                        continue
                if i >= 0:
                    w.setCurrentIndex(i)
            elif w is not None:
                w.setText(v)
        if v0130 is not None:
            self._migrar_v0130(v0130, s["campos"])
        elif "tipo_trim" not in s.get("campos", {}) and T.deslizante(self.cuerpo().clave):
            self._migrar_trim(s["campos"])     # proyectos de v0.12 y anteriores: trim especial aparte
        filas = {f.clave: f for f in self._todas_las_filas()}
        for k, d in s.get("filas", {}).items():
            f = filas.get(k)
            if f is None:
                continue
            if f.unidad.findText(d["unidad"]) < 0 and k == "caudal":
                continue
            f.elegir(d["unidad"], convertir=False)
            for e, v in zip(f.edits, d["valores"]):
                e.setText(v)
        self.filas["caudal"].edits[CIERRE].setText("0")
        self._mat_cargar(s.get("materiales", {}))
        for k, v in s.get("equipo", {}).items():  # en orden de registro: el tipo antes que la señal
            w = self.eq_w.get(k)
            if isinstance(w, QComboBox):
                if w.findText(v) >= 0:
                    w.setCurrentText(v)
            elif w is not None:
                w.setText(v)
        self._act_concordancia()  # un proyecto anterior puede traer un actuador que no corresponde a la válvula
        self._caract_concordancia()  # y una característica que no corresponde a una rotativa
        self.res = None
        self._actualizar_vistas()

    def _migrar_trim(self, campos: dict) -> bool:
        """Trim guardado por una versión anterior: nombre de la clave vieja (v0.11) o estilo de trim, sentido,
        trim anticavitación y trim para ruido elegidos aparte (v0.12). Elige tipo, guía, obturador o jaula,
        nivel, sentido y, si la clave la llevaba, la característica."""
        c = self.cuerpo().clave
        v = campos.get("trim", "")
        sd = next((k for k, t in SENTIDOS.items() if t == campos.get("sentido")), "abre")
        k = NOMBRES_ANTERIORES.get(v) or next((c2 for c2, e in ESTILOS.items()
                                               if v in (e.nombre, NOMBRE_CORTO.get(c2))), None)
        if k is None:
            g = next((g for g, n in NOMBRE_GEOMETRIA.items() if n == v), None)
            k = clave_de_geometria(c, g, sd) if g else None
        if k is None:
            return False
        k, car = CLAVES_ANTERIORES.get(k, (k, None))
        if T.deslizante(c):
            ac = next((x for x, t in AC.TRIMS.items() if t.nombre == campos.get("anticav")), "estandar")
            ru = next((x for x, t in CG.TRIMS_RUIDO.items() if t.nombre == campos.get("trim_ruido")), "estandar")
            el = T.desde_claves(c, k, "", ac, ru, self.tipo() == "liquido")
            if el is None:
                return False
            self.aplicar_eleccion(el)
        else:
            g, sd = geometria_sentido(k)
            i = self.cb_trim.findData(g)
            if i < 0:
                return False
            self.cb_trim.setCurrentIndex(i)
            j = self.cb_sentido.findData(sd)
            if j >= 0:
                self.cb_sentido.setCurrentIndex(j)
        if car:
            self.cb_caract.setCurrentIndex(self.cb_caract.findData(car))
        return True

    def _migrar_v0130(self, viejo: dict, campos: dict):
        """Proyecto de v0.13.0 (guiado por obturador / por jaula, jaula especial y nivel aparte): sin jaula o con
        jaula, jaula estándar, anticavitación o antiruido y su config dinámica. El disco plano y la jaula de
        retención de asiento pasan a obturador contorneado."""
        liq = self.tipo() == "liquido"
        c = self.cuerpo().clave
        sd = next((k for k, t in SENTIDOS.items() if t == campos.get("sentido")), "abre")
        e = next((k for k, x in T.ELEMENTOS.items() if x.nombre == viejo["trim"]), "")
        if viejo["trim"] in ("Obturador de disco plano", "Jaula de retención de asiento, obturador contorneado"):
            e = "contorneado"
        if not e:
            return
        if T.ELEMENTOS[e].tipo == "obturador":
            g = next((k for k, x in T.GUIAS.items() if x.nombre == viejo["guia"]), "")
            g = g if g and e in T.GUIAS[g].obturadores else T.guia_por_defecto(e)
            el = T.Eleccion("obturador", g, e, sd)
        else:
            cfg = T.config_desde_texto(c, liq, viejo["nivel"], e)
            nv = cfg[1] if cfg else ""
            el = T.Eleccion("jaula", "", e, sd, nv or (T.niveles(e, liq) or [""])[0])
        self.aplicar_eleccion(el)
        i = self.cb_caract.findText(campos.get("caracteristica", ""))
        if i >= 0:
            self.cb_caract.setCurrentIndex(i)

    def aplicar_eleccion(self, el: T.Eleccion):
        """Elige en los desplegables de la solapa 2 el tipo, la guía, el obturador o la jaula, el nivel y el sentido."""
        clase = "estandar" if not el.nivel else ("anticav" if self.tipo() == "liquido" else "antiruido")
        cfg = f"{el.elemento}|{el.nivel}" if el.nivel else ""
        for cb, dato in ((self.cb_tipo_trim, el.tipo), (self.cb_guia, el.guia), (self.cb_trim, el.elemento),
                         (self.cb_jaula, clase if el.tipo == "jaula" else ""), (self.cb_nivel, cfg),
                         (self.cb_sentido, el.sentido)):
            i = cb.findData(dato)
            if dato and i >= 0:
                cb.setCurrentIndex(i)

    def nuevo(self):
        for f in self._todas_las_filas():
            for e in f.edits:
                if not e.isReadOnly() or f.clave in (*PROPIEDADES, "Pc"):
                    e.clear()
        self.filas["caudal"].edits[CIERRE].setText("0")
        self.f_Rn.edits[0].setText("1")
        for ed in self.ed_ident.values():
            ed.clear()
        self.ed_ident["revision"].setText("0")
        self.ed_cv_red.clear()
        self._mat_nuevo()
        self._eq_nuevo()
        self._cambio_trim()
        self.res = None
        self.ruta = None
        self.lbl_resumen.setText("Sin cálculo.")
        self.lbl_geo.setText("Se calcula con «Calcular».")
        self._llenar_kpi()
        self.lista_alertas.clear()
        for fs in self.salidas.values():
            for c in fs.celdas:
                c.clear()
        self._actualizar_vistas()

    def guardar(self, como: bool = False):
        ruta = self.ruta
        if como or not ruta:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "", "Proyecto N25 Valves Sizing (*.valvula)")
        if ruta:
            if not ruta.endswith(".valvula"):
                ruta += ".valvula"
            with open(ruta, "w", encoding="utf-8") as fh:
                json.dump(self._estado(), fh, ensure_ascii=False, indent=1)
            self.ruta = ruta
            self.statusBar().showMessage(f"Proyecto guardado: {os.path.basename(ruta)}")

    def abrir(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", "Proyecto N25 Valves Sizing (*.valvula)")
        if ruta:
            with open(ruta, encoding="utf-8") as fh:
                s = json.load(fh)
            if "campos" not in s:
                QMessageBox.warning(self, "Proyecto de versión anterior",
                                    "El archivo es de la versión 1 y no se puede abrir en esta versión.")
                return
            self._cargar(s)
            self.ruta = ruta

    def _texto_licencia(self) -> str:
        lic = self.licencia
        if lic is None or not lic.es_demo:
            return ""
        from datetime import date
        return f"  ·  DEMO de {lic.nombre}, quedan {lic.dias_restantes(date.today())} días"

    def ver_licencia(self):
        from .. import licencia as L
        lic = self.licencia
        texto = lic.descripcion() if lic else "Sin licencia (modo de desarrollo)."
        r = QMessageBox.question(self, "Licencia", texto + "\n\n¿Desea ingresar otro código?",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r == QMessageBox.Yes:
            from .activacion import DialogoActivacion
            dlg = DialogoActivacion(parent=self)
            if dlg.exec():
                self.licencia = dlg.verificacion.licencia
                E.MARCA_AGUA = self.licencia.marca_agua
                self.setWindowTitle(f"{E.PRODUCTO} — {E.EMPRESA}  ·  versión {__version__}"
                                    + self._texto_licencia())
                if self.res is not None:
                    self._actualizar_vistas()
                QMessageBox.information(self, "Licencia", self.licencia.descripcion())

    def enviar_comentarios(self):
        from PySide6.QtGui import QDesktopServices
        contacto = self.licencia.contacto if self.licencia else ""
        if not contacto:
            QMessageBox.information(self, "Enviar comentarios",
                                    f"Envíe sus comentarios a {E.EMPRESA} por el medio por el que recibió el programa.")
            return
        asunto = QUrl.toPercentEncoding(f"Comentarios {E.PRODUCTO} {__version__}").data().decode()
        cuerpo = QUrl.toPercentEncoding(
            "Caso o pantalla:\n\nQué esperaba:\n\nQué obtuvo (adjunte capturas o el proyecto .json):\n").data().decode()
        if not QDesktopServices.openUrl(QUrl(f"mailto:{contacto}?subject={asunto}&body={cuerpo}")):
            QMessageBox.information(self, "Enviar comentarios", f"Envíe sus comentarios a {contacto}.")

    def acerca(self):
        QMessageBox.about(self, "Acerca de",
                          f"<b>{E.PRODUCTO}</b> versión {__version__}<br>{E.EMPRESA}<br><br>"
                          "Dimensionamiento de válvulas de control para líquidos según IEC 60534-2-1 / "
                          "ANSI/ISA-75.01.01, cavitación y ruido IEC 60534-8-4, tuberías ASME B36.10M / "
                          "B36.19M, rating ASME B16.34 y clases de cierre ANSI/FCI 70-2.<br><br>"
                          "Software independiente de fabricantes de válvulas.<br>"
                          "Propiedades de fluidos: CoolProp (licencia MIT).")
