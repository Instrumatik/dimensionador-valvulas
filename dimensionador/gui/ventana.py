"""Ventana principal de Valveselect-N25 (versión 2: líquidos)."""
from __future__ import annotations

import html as _html
import json
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QColor, QFont, QImage, QKeySequence, QShortcut, QTextDocument
from PySide6.QtWidgets import (QApplication, QComboBox, QCheckBox, QDialog, QFileDialog, QFrame,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSplitter, QTabWidget, QTextBrowser, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import __version__, ayuda, entregables as E, modelos, propiedades, tuberias, unidades as U
from ..estilos import CUERPOS, ESTILOS, TAMANOS
from ..iec60534_2_1 import RHO_AGUA_15C, CapacidadInsuficiente
from ..modelos import ErrorDatos, Severidad
from ..proyecto import (CIERRES, CONEXIONES, RATINGS, CasoLiquido, Dimensionamiento, Identificacion,
                        Instalacion, Resultado, calcular)

CASOS = ["Mínimo", "Normal", "Máximo"]
USUARIO = "Definido por el usuario"
AZUL = "#0d3b66"
VERDE = "#2e7d32"
FONDO_SALIDA = "#e3f1e6"
FONDO_AUTO = "#eef2f6"
COLORES = {Severidad.INFO: "#2f6fb0", Severidad.ADVERTENCIA: "#b07a00",
           Severidad.CRITICA: "#c0392b", Severidad.ERROR: "#7d1f9e"}
NOMBRE_SEV = E.NOMBRE_SEV
DIF = {"kPa a": "kPa", "kPa g": "kPa", "bar a": "bar", "bar g": "bar", "MPa a": "MPa", "MPa g": "MPa",
       "psia": "psi", "psig": "psi", "kg/cm² a": "kg/cm²", "kg/cm² g": "kg/cm²"}
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


# ---------------------------------------------------------------------------
# Ventana de ayuda
# ---------------------------------------------------------------------------
class VentanaAyuda(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ayuda de {E.PRODUCTO}")
        self.resize(900, 620)
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
            if f and f not in e.titulo.lower() and f not in e.texto.lower():
                continue
            por_cat.setdefault(e.categoria, []).append((e.titulo, k))
        for cat in ["Conceptos", "Datos", "Coeficientes", "Resultados", "Fenómenos"]:
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
    b = QPushButton("Ir")
    b.setFixedWidth(34)
    b.setToolTip("Ir a la explicación de este dato (F1)")
    b.setFocusPolicy(Qt.NoFocus)
    b.setStyleSheet("QPushButton{padding:1px 2px;color:#0d3b66;font-size:8pt}")
    b.clicked.connect(lambda: abrir_ayuda(clave))
    return b


class FilaUnidad:
    """Dato con selector de unidad y uno o tres valores (casos mínimo, normal y máximo)."""

    def __init__(self, clave, etiqueta, magnitudes, grid, r, abrir_ayuda, n=3, ayuda_clave=None, pos=None):
        """pos = (columna del valor, ancho, columna de la unidad) para filas de un solo valor."""
        self.clave = clave
        self.lbl = QLabel(etiqueta)
        clave_ayuda = ayuda_clave or clave
        self.btn = boton_ir(abrir_ayuda, clave_ayuda)
        self.unidad = QComboBox()
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
        col_v, ancho, col_u = pos or (3, 1 if n > 1 else 3, 2)
        grid.addWidget(self.unidad, r, col_u)
        for j in range(n):
            e = QLineEdit()
            e.setProperty("ayuda", clave_ayuda)
            e.setAlignment(Qt.AlignRight)
            e.setMinimumWidth(90)
            grid.addWidget(e, r, col_v + j, 1, ancho)
            self.edits.append(e)

    def magnitud(self) -> str:
        return self.mag_de[self.unidad.currentText()]

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

    def solo_lectura(self, si: bool):
        for e in self.edits:
            e.setReadOnly(si)
            e.setStyleSheet(f"background:{FONDO_AUTO};" if si else "")


class FilaSalida:
    def __init__(self, clave, etiqueta, ayuda_clave, magnitud, cifras, grid, r, abrir_ayuda):
        self.clave, self.magnitud, self.cifras = clave, magnitud, cifras
        self.lbl = QLabel(etiqueta)
        grid.addWidget(self.lbl, r, 0)
        grid.addWidget(boton_ir(abrir_ayuda, ayuda_clave), r, 1)
        self.lbl_unidad = QLabel("")
        grid.addWidget(self.lbl_unidad, r, 2)
        self.celdas = []
        for j in range(3):
            e = QLineEdit()
            e.setReadOnly(True)
            e.setAlignment(Qt.AlignRight)
            e.setFocusPolicy(Qt.ClickFocus)
            e.setProperty("ayuda", ayuda_clave)
            e.setStyleSheet(f"background:{FONDO_SALIDA};color:#123;font-weight:600;border:1px solid #9cc3a4")
            grid.addWidget(e, r, 3 + j)
            self.celdas.append(e)


SALIDAS = [
    # clave, etiqueta, ayuda, magnitud (None = adimensional), cifras
    ("Cv", "Coeficiente de flujo (Cv)", "kv_cv", None, 4),
    ("apertura", "Apertura estimada", "apertura", "%", 3),
    ("Kapp", "Coef. cavitación de la aplicación (Kapp)", "Kapp", None, 3),
    ("Kc", "Coef. cavitación del trim usado (Kc)", "Kc", None, 3),
    ("dP", "Presión diferencial ΔP", "dP", "presion_dif", 4),
    ("dP_P1", "Relación de caída de presión ΔP/P1", "dP_P1", None, 3),
    ("dPchoked", "ΔP para flujo estrangulado (ΔP choked)", "dPchoked", "presion_dif", 4),
    ("dPcav", "ΔP para cavitación (ΔP cav)", "dPcav", "presion_dif", 4),
    ("FF", "Factor de relación de presión crítica (FF)", "FF", None, 3),
    ("FP", "Factor de corrección por tuberías (Fp)", "FP", None, 3),
    ("FLP", "Factor de recuperación combinado (FLp)", "FLP", None, 3),
    ("visc", "Viscosidad", "viscosidad", "visc", 4),
    ("D1", "Diámetro interno aguas arriba", "D_interno", "longitud", 4),
    ("D2", "Diámetro interno aguas abajo", "D_interno", "longitud", 4),
    ("Rev", "Número de Reynolds (Rev)", "Rev", None, 4),
    ("rho", "Densidad de entrada ρ1", "rho", "densidad", 4),
    ("W", "Flujo másico", "flujo_masico", "caudal_masico", 4),
    ("Lp", "Presión sonora a 1 m (LpAe,1m)", "ruido", "dB(A)", 3),
    ("v1", "Velocidad del fluido aguas arriba", "velocidad_tuberia", "velocidad", 3),
    ("v2", "Velocidad del fluido aguas abajo", "velocidad_tuberia", "velocidad", 3),
    ("condicion", "Condición hidrodinámica", "cavitacion", "texto", 0),
]


def titulo_seccion(texto: str, color: str) -> QLabel:
    l = QLabel(texto)
    l.setStyleSheet(f"background:{color};color:white;font-weight:700;padding:5px 8px;letter-spacing:1px")
    return l


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{E.PRODUCTO} — {E.EMPRESA}  ·  versión {__version__}")
        self.resize(1360, 900)
        self.ayuda = VentanaAyuda(self)
        self.res: Resultado | None = None
        self.sistema = "SI"
        self.ruta: str | None = None
        self.campos: dict[str, QWidget] = {}
        self._construir_menu()

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._encabezado())
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._tab_instalacion(), "Inst-Valve-Data")
        self.tabs.addTab(self._tab_dimensionamiento(), "Dim-Valve-Data")
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
        self._actualizar_vistas()
        self.statusBar().showMessage("Cargue los datos de instalación y de dimensionamiento y presione "
                                     "Calcular. «Ir» o F1 explican cada dato.")

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
                     "IEC 60534 · ANSI/ISA-75.01 · Líquidos")
        sub.setStyleSheet("font-size:9pt;color:#dce8f4")
        izq.addWidget(empresa)
        izq.addWidget(producto)
        izq.addWidget(sub)
        h.addLayout(izq, 1)
        der = QHBoxLayout()
        l = QLabel("Unidades")
        self.cb_sistema = QComboBox()
        self.cb_sistema.addItems(["SI", "Imperial"])
        self.cb_sistema.setProperty("ayuda", "sistema_unidades")
        self.cb_sistema.currentTextChanged.connect(self.aplicar_sistema)
        self.btn_calc_cab = QPushButton("Calcular")
        self.btn_calc_cab.setStyleSheet("QPushButton{background:#f5b700;color:#0d3b66;font-weight:800;"
                                        "padding:6px 18px;border-radius:4px}")
        self.btn_calc_cab.clicked.connect(self.calcular)
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
        m.addSeparator()
        self._accion(m, "Salir", self.close, QKeySequence.Quit)
        mu = mb.addMenu("&Unidades")
        for s, t in (("SI", "Sistema Internacional (SI)"), ("Imperial", "Sistema imperial")):
            self._accion(mu, t, lambda _=False, s=s: self.aplicar_sistema(s))
        ma = mb.addMenu("A&yuda")
        self._accion(ma, "Flujo de trabajo", lambda: self.abrir_ayuda("flujo_trabajo"))
        self._accion(ma, "Índice de ayuda", lambda: self.abrir_ayuda("kv_cv"))
        self._accion(ma, "Acerca de", self.acerca)

    def abrir_ayuda(self, clave: str):
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

    def _fila(self, grid, r, etiqueta, widget, clave, unidad: QWidget | None = None, span=1):
        grid.addWidget(QLabel(etiqueta), r, 0)
        grid.addWidget(boton_ir(self.abrir_ayuda, clave), r, 1)
        grid.addWidget(widget, r, 2, 1, span)
        if unidad is not None:
            grid.addWidget(unidad, r, 2 + span)
        widget.setProperty("ayuda", clave)

    # ------------------------------------------------------------ Inst-Valve-Data
    def _tab_instalacion(self) -> QWidget:
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("DATOS DE INSTALACIÓN", AZUL))
        fila = QHBoxLayout()

        g = QGroupBox("Identificación")
        grid = QGridLayout(g)
        self.ed_ident = {}
        for r, (k, et) in enumerate((("proyecto", "Proyecto"), ("cliente", "Cliente"), ("tag", "Tag"),
                                     ("servicio", "Servicio"), ("documento", "N.º de documento"),
                                     ("revision", "Revisión"), ("preparado", "Preparado por"),
                                     ("fecha", "Fecha"))):
            ed = self._registrar("id_" + k, QLineEdit())
            if k == "revision":
                ed.setText("0")
            if k == "fecha":
                ed.setPlaceholderText("fecha de hoy")
            self.ed_ident[k] = ed
            self._fila(grid, r, et, ed, "identificacion")
        grid.setRowStretch(9, 1)
        fila.addWidget(g, 1)

        g = QGroupBox("Válvula e instalación")
        grid = QGridLayout(g)
        r = 0
        self.cb_cuerpo = self._registrar("cuerpo", QComboBox())
        for c in CUERPOS.values():
            self.cb_cuerpo.addItem(c.nombre, c.clave)
        self.cb_cuerpo.currentIndexChanged.connect(self._cambio_cuerpo)
        self._fila(grid, r, "Estilo de válvula", self.cb_cuerpo, "estilo_cuerpo", span=2); r += 1
        self.cb_rating = self._registrar("rating", QComboBox())
        for c in RATINGS:
            self.cb_rating.addItem(f"CL{c}", c)
        self.cb_rating.setCurrentIndex(1)
        self._fila(grid, r, "Rating", self.cb_rating, "rating", span=2); r += 1
        self.cb_nps, self.cb_sch = {}, {}
        for lado, et in (("entrada", "entrada"), ("salida", "salida")):
            cb = self._registrar("nps_" + lado, QComboBox())
            for n in tuberias.NPS:
                cb.addItem(tuberias.texto_nps(n), n)
            cb.setCurrentIndex(tuberias.NPS.index(4))
            self.cb_nps[lado] = cb
            self._fila(grid, r, f"Diámetro nominal tubería de {et}", cb, "nps", span=2); r += 1
        for lado, et in (("entrada", "entrada"), ("salida", "salida")):
            cb = self._registrar("sch_" + lado, QComboBox())
            self.cb_sch[lado] = cb
            self._fila(grid, r, f"Schedule tubería de {et}", cb, "cedula", span=2); r += 1
            self.cb_nps[lado].currentIndexChanged.connect(lambda _=0, l=lado: self._cambio_nps(l))
            cb.currentIndexChanged.connect(self._copiar_tuberias)
            self._cambio_nps(lado)
        self.ed_ruido = self._registrar("ruido", QLineEdit("85"))
        self._fila(grid, r, "Ruido permitido", self.ed_ruido, "limite_ruido", QLabel("dB(A)")); r += 1
        self.cb_conexion = self._registrar("conexion", QComboBox())
        self.cb_conexion.addItems(CONEXIONES)
        self.cb_conexion.setCurrentText("RF bridada")
        self._fila(grid, r, "Tipo de conexión a proceso", self.cb_conexion, "conexion", span=2); r += 1
        grid.addWidget(QLabel(""), r, 0); r += 1
        self.f_Pd = FilaUnidad("P_diseno", "Presión de diseño", ("presion",), grid, r, self.abrir_ayuda, 1,
                               pos=(2, 2, 4)); r += 1
        self.f_Td = FilaUnidad("T_diseno", "Temperatura de diseño", ("temperatura",), grid, r, self.abrir_ayuda, 1,
                               "T_diseno", pos=(2, 2, 4)); r += 1
        for f in (self.f_Pd, self.f_Td):
            f.edits[0].setPlaceholderText("máxima de operación")
        self.cb_cierre = self._registrar("cierre", QComboBox())
        self.cb_cierre.addItems(CIERRES)
        self.cb_cierre.setCurrentText("ANSI Clase IV")
        self._fila(grid, r, "Clase de cierre (shutoff)", self.cb_cierre, "clase_cierre", span=2); r += 1
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(r, 1)
        fila.addWidget(g, 2)
        lay.addLayout(fila)
        nota = QLabel("Estos datos definen los diámetros interiores de tubería, los trims compatibles, el límite "
                      "de ruido y las verificaciones de rating, conexión y clase de cierre. Se copian "
                      "automáticamente a Dim-Valve-Data.")
        nota.setWordWrap(True)
        nota.setStyleSheet("color:#55606d;font-style:italic;padding:4px")
        lay.addWidget(nota)
        b = QPushButton("Continuar con Dim-Valve-Data →")
        b.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(b)
        lay.addLayout(h)
        lay.addStretch()
        return self._scroll(cont)

    def _scroll(self, w):
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(w)
        return sc

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
        if not hasattr(self, "ed_tub"):
            return
        for lado in ("entrada", "salida"):
            nps = self.cb_nps[lado].currentData()
            sch = self.cb_sch[lado].currentText()
            self.ed_tub[lado].setText(tuberias.texto_nps(nps))
            try:
                di = tuberias.diametro_interior(nps, sch)
                pr = self.presentacion()
                self.ed_sch[lado].setText(f"{sch}   (DI {pr.vu(di, 'longitud')})")
            except tuberias.ErrorTuberia:
                self.ed_sch[lado].setText(sch)

    # ------------------------------------------------------------ Dim-Valve-Data
    def _tab_dimensionamiento(self) -> QWidget:
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("DATOS DE ENTRADA — LÍQUIDOS", AZUL))

        g = QGroupBox("Fluido")
        grid = QGridLayout(g)
        self.cb_fluido = self._registrar("fluido", QComboBox())
        self.cb_fluido.addItems([USUARIO, *propiedades.FLUIDOS.keys()])
        self.cb_fluido.setCurrentText("Agua / vapor de agua")
        self.cb_fluido.currentIndexChanged.connect(self._cambio_fluido)
        self._fila(grid, 0, "Fluido", self.cb_fluido, "fluido")
        self.cb_tipo_caudal = self._registrar("tipo_caudal", QComboBox())
        self.cb_tipo_caudal.addItems(["Volumétrico", "Másico"])
        self.cb_tipo_caudal.currentIndexChanged.connect(self._cambio_tipo_caudal)
        self._fila(grid, 1, "Tipo de caudal", self.cb_tipo_caudal, "tipo_caudal")
        grid.setColumnStretch(2, 1)
        lay.addWidget(g)

        g = QGroupBox("Condiciones de operación")
        grid = QGridLayout(g)
        grid.addWidget(QLabel("<b>Dato</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Unidad</b>"), 0, 2)
        self.chk_caso = []
        for j, c in enumerate(CASOS):
            ch = QCheckBox(c)
            ch.setChecked(True)
            ch.setProperty("ayuda", "casos")
            grid.addWidget(ch, 0, 3 + j)
            self.chk_caso.append(ch)
        defs = [("caudal", "Caudal", ("caudal_vol",), "caudal"),
                ("P1", "Presión de entrada", ("presion",), "P1"),
                ("P2", "Presión de salida", ("presion",), "P2"),
                ("T1", "Temperatura de entrada", ("temperatura",), "T1"),
                ("SG", "Gravedad específica", ("adimensional",), "SG"),
                ("mu", "Viscosidad dinámica", ("viscosidad_din",), "viscosidad"),
                ("Pv", "Presión de vapor", ("presion",), "Pv")]
        self.filas: dict[str, FilaUnidad] = {}
        for i, (k, et, mags, ay) in enumerate(defs, start=1):
            self.filas[k] = FilaUnidad(k, et, mags, grid, i, self.abrir_ayuda, ayuda_clave=ay)
        self.filas["SG"].unidad.setEnabled(False)
        r = len(defs) + 1
        self.f_Pc = FilaUnidad("Pc", "Presión crítica", ("presion",), grid, r, self.abrir_ayuda, 1); r += 1
        self.btn_prop = QPushButton("Calcular propiedades del fluido")
        self.btn_prop.clicked.connect(self._boton_propiedades)
        grid.addWidget(self.btn_prop, r, 3, 1, 3); r += 1
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 1)
        grid.setColumnStretch(5, 1)
        lay.addWidget(g)

        g = QGroupBox("Tubería, válvula y factores (típicos, editables)")
        grid = QGridLayout(g)
        r = 0
        self.ed_tub, self.ed_sch = {}, {}
        for lado, et in (("entrada", "entrada"), ("salida", "salida")):
            ed = QLineEdit()
            ed.setReadOnly(True)
            ed.setStyleSheet(f"background:{FONDO_AUTO}")
            self.ed_tub[lado] = ed
            self._fila(grid, r, f"Diámetro de tubería de {et}", ed, "nps", QLabel("desde Inst-Valve-Data")); r += 1
        for lado, et in (("entrada", "entrada"), ("salida", "salida")):
            ed = QLineEdit()
            ed.setReadOnly(True)
            ed.setStyleSheet(f"background:{FONDO_AUTO}")
            self.ed_sch[lado] = ed
            self._fila(grid, r, f"Schedule de tubería de {et}", ed, "cedula", QLabel("desde Inst-Valve-Data")); r += 1
        self.cb_tamano = self._registrar("tamano", QComboBox())
        self._fila(grid, r, "Diámetro de válvula", self.cb_tamano, "tamano"); r += 1
        self.cb_trim = self._registrar("trim", QComboBox())
        self.cb_trim.currentIndexChanged.connect(self._cambio_trim)
        self._fila(grid, r, "Tipo de trim hidrodinámico", self.cb_trim, "trim"); r += 1
        self.cb_caract = self._registrar("caracteristica", QComboBox())
        for k, t in E.CARACTERISTICA.items():
            self.cb_caract.addItem(t, k)
        self._fila(grid, r, "Característica inherente", self.cb_caract, "caracteristica"); r += 1
        self.ed_FL = self._registrar("FL", QLineEdit())
        self._fila(grid, r, "Factor de recuperación de presión (FL)", self.ed_FL, "FL", QLabel("típico IEC 60534-2-1")); r += 1
        self.ed_Fd = self._registrar("Fd", QLineEdit())
        self._fila(grid, r, "Modificador por estilo de válvula (Fd)", self.ed_Fd, "Fd", QLabel("típico IEC 60534-2-1")); r += 1
        self.ed_Kc = self._registrar("Kc", QLineEdit(placeholderText="estimado según IEC 60534-8-4"))
        self._fila(grid, r, "Coef. cavitación de la construcción (Kc)", self.ed_Kc, "Kc", QLabel("del trim")); r += 1
        self.ed_cvnom = self._registrar("Cv_nominal", QLineEdit(placeholderText="típico del estilo"))
        self._fila(grid, r, "Cv nominal de la válvula", self.ed_cvnom, "Cv_nominal", QLabel("opcional")); r += 1
        self.f_c = FilaUnidad("c", "Velocidad del sonido en el líquido", ("velocidad",), grid, r,
                              self.abrir_ayuda, 1, "velocidad_sonido", pos=(2, 1, 3)); r += 1
        self.f_c.edits[0].setPlaceholderText("calculada / 1 400 m/s")
        grid.setColumnStretch(2, 1)
        lay.addWidget(g)

        self.btn_calc = QPushButton("Calcular")
        self.btn_calc.setMinimumHeight(38)
        fb = self.btn_calc.font()
        fb.setBold(True)
        fb.setPointSize(fb.pointSize() + 2)
        self.btn_calc.setFont(fb)
        self.btn_calc.setStyleSheet(f"QPushButton{{background:{AZUL};color:white;border-radius:4px}}")
        self.btn_calc.clicked.connect(self.calcular)
        lay.addWidget(self.btn_calc)

        # Resultados
        lay.addSpacing(10)
        lay.addWidget(titulo_seccion("RESULTADOS", VERDE))
        self.lbl_resumen = QLabel("Sin cálculo.")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setStyleSheet(f"background:{FONDO_SALIDA};padding:8px;border:1px solid #9cc3a4")
        lay.addWidget(self.lbl_resumen)
        g = QGroupBox("Salidas por caso")
        grid = QGridLayout(g)
        grid.addWidget(QLabel("<b>Resultado</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Unidad</b>"), 0, 2)
        for j, c in enumerate(CASOS):
            grid.addWidget(QLabel(f"<b>{c}</b>"), 0, 3 + j, alignment=Qt.AlignCenter)
        self.salidas: dict[str, FilaSalida] = {}
        for i, (k, et, ay, mag, cif) in enumerate(SALIDAS, start=1):
            self.salidas[k] = FilaSalida(k, et, ay, mag, cif, grid, i, self.abrir_ayuda)
        self.cb_visc = self._registrar("visc_salida", QComboBox())
        self.cb_visc.addItems(["Dinámica", "Cinemática"])
        self.cb_visc.currentIndexChanged.connect(lambda: self.res and self._mostrar_salidas())
        fs = self.salidas["visc"]
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(fs.lbl)
        h.addWidget(self.cb_visc)
        w = QWidget()
        w.setLayout(h)
        grid.addWidget(w, list(self.salidas).index("visc") + 1, 0)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 1)
        grid.setColumnStretch(5, 1)
        lay.addWidget(g)

        lay.addWidget(titulo_seccion("ALERTAS", "#8a5a00"))
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
        self.vistas[codigo] = vista
        v.addWidget(vista, 1)
        return w

    # ------------------------------------------------------------- eventos
    def cuerpo(self):
        return CUERPOS[self.cb_cuerpo.currentData()]

    def _cambio_cuerpo(self):
        c = self.cuerpo()
        self.cb_trim.blockSignals(True)
        self.cb_trim.clear()
        for k in c.trims:
            self.cb_trim.addItem(ESTILOS[k].nombre, k)
        self.cb_trim.blockSignals(False)
        actual = self.cb_tamano.currentData()
        self.cb_tamano.clear()
        self.cb_tamano.addItem("Automático", None)
        for p, dn, _ in TAMANOS:
            if c.nps_min <= p <= c.nps_max:
                self.cb_tamano.addItem(f"{tuberias.texto_nps(p)}  (DN {dn})", p)
        i = self.cb_tamano.findData(actual)
        self.cb_tamano.setCurrentIndex(max(0, i))
        self._cambio_trim()

    def _cambio_trim(self):
        k = self.cb_trim.currentData()
        if not k:
            return
        e = ESTILOS[k]
        self.ed_FL.setText(f"{e.FL:g}".replace(".", ","))
        self.ed_Fd.setText(f"{e.Fd:g}".replace(".", ","))
        self.cb_caract.setCurrentIndex(self.cb_caract.findData(e.caracteristica))
        self.cb_trim.setToolTip(e.nota or e.nombre)

    def _cambio_fluido(self):
        manual = self.cb_fluido.currentText() == USUARIO
        self.btn_prop.setEnabled(not manual)
        for k in ("SG", "mu", "Pv"):
            self.filas[k].solo_lectura(not manual)
        self.f_Pc.solo_lectura(not manual)

    def _cambio_tipo_caudal(self):
        f = self.filas["caudal"]
        vol = self.cb_tipo_caudal.currentIndex() == 0
        mag = "caudal_vol" if vol else "caudal_masico"
        f.unidad.blockSignals(True)
        f.unidad.clear()
        f.mag_de = {}
        for s in U.unidades_de(mag):
            f.unidad.addItem(s)
            f.mag_de[s] = mag
        f.unidad.setCurrentText(U.SISTEMAS[self.sistema][mag])
        f._ant = f.unidad.currentText()
        f.unidad.blockSignals(False)
        for e in f.edits:
            e.clear()

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
        F["P1"].elegir(man)
        F["P2"].elegir(man)
        F["Pv"].elegir(pref["presion"])
        F["T1"].elegir(pref["temperatura"])
        F["mu"].elegir("cP")
        self.f_Pc.elegir(pref["presion"])
        self.f_Pd.elegir(man)
        self.f_Td.elegir(pref["temperatura"])
        self.f_c.elegir(pref["velocidad"])
        self._copiar_tuberias()
        if self.res is not None:
            self.calcular(silencioso=True)

    def presentacion(self) -> E.Presentacion:
        """Unidades de los resultados y documentos: las mismas de las entradas."""
        u = dict(U.SISTEMAS[self.sistema])
        F = self.filas if hasattr(self, "filas") else {}
        if F:
            up = F["P1"].unidad.currentText()
            u["presion"] = up
            u["presion_dif"] = DIF.get(up, u["presion_dif"])
            u["temperatura"] = F["T1"].unidad.currentText()
            u[F["caudal"].magnitud()] = F["caudal"].unidad.currentText()
            u["viscosidad_din"] = F["mu"].unidad.currentText()
            u["presion_abs"] = F["Pv"].unidad.currentText()
            if hasattr(self, "f_c"):
                u["velocidad"] = self.f_c.unidad.currentText()
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

    def _activos(self):
        return [j for j, ch in enumerate(self.chk_caso) if ch.isChecked()]

    def _boton_propiedades(self):
        try:
            self.calcular_propiedades()
        except (ValueError, propiedades.ErrorPropiedades) as e:
            QMessageBox.warning(self, "Propiedades", str(e))

    def calcular_propiedades(self):
        fluido = self.cb_fluido.currentText()
        if fluido == USUARIO:
            return
        F = self.filas
        for j in self._activos():
            P1, T1 = F["P1"].valor_base(j), F["T1"].valor_base(j)
            if P1 is None or T1 is None:
                raise ValueError(f"Caso {CASOS[j]}: ingrese P1 y T1 para obtener las propiedades.")
            p = propiedades.liquido(fluido, P1, T1)
            F["SG"].edits[j].setText(_num(p.rho / RHO_AGUA_15C))
            F["mu"].poner_base(j, p.mu)
            F["Pv"].poner_base(j, p.Pv)
            self.f_Pc.poner_base(0, p.Pc)

    def _leer(self):
        ident = Identificacion(**{k: ed.text().strip() for k, ed in self.ed_ident.items()})
        inst = Instalacion(
            cuerpo=self.cb_cuerpo.currentData(), rating=self.cb_rating.currentData(),
            nps_entrada=self.cb_nps["entrada"].currentData(), nps_salida=self.cb_nps["salida"].currentData(),
            sch_entrada=self.cb_sch["entrada"].currentText(), sch_salida=self.cb_sch["salida"].currentText(),
            ruido_permitido=self._float(self.ed_ruido, "ruido permitido"), conexion=self.cb_conexion.currentText(),
            P_diseno=self.f_Pd.valor_base(0), T_diseno=self.f_Td.valor_base(0), cierre=self.cb_cierre.currentText())
        F = self.filas
        activos = self._activos()
        if not activos:
            raise ValueError("Active al menos un caso de operación (mínimo, normal o máximo).")
        vol = self.cb_tipo_caudal.currentIndex() == 0
        casos = []
        for j in activos:
            def req(k):
                v = F[k].valor_base(j)
                if v is None:
                    raise ValueError(f"Caso {CASOS[j]}: falta «{F[k].lbl.text()}».")
                return v
            q = req("caudal")
            casos.append(CasoLiquido(CASOS[j], q if vol else None, None if vol else q, req("P1"), req("P2"),
                                     req("T1"), req("SG"), req("mu"), req("Pv")))
        Pc = self.f_Pc.valor_base(0)
        if Pc is None:
            raise ValueError("Falta la presión crítica del líquido.")
        cv = self._float(self.ed_cvnom, "Cv nominal", True)
        if cv is not None and self.cb_tamano.currentData() is None:
            raise ValueError("Para usar un Cv nominal elija también el diámetro de la válvula.")
        fluido = None if self.cb_fluido.currentText() == USUARIO else self.cb_fluido.currentText()
        dim = Dimensionamiento(casos, Pc, self.cb_trim.currentData(), self._float(self.ed_FL, "FL"),
                               self._float(self.ed_Fd, "Fd"), self._float(self.ed_Kc, "Kc", True),
                               self.cb_tamano.currentData(), cv, self.cb_caract.currentData(), fluido,
                               self.f_c.valor_base(0))
        return ident, inst, dim

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
        self.tabs.setCurrentIndex(1)

    # ----------------------------------------------------------- mostrar
    def _mostrar(self):
        res = self.res
        peor = res.peor()
        estado = {Severidad.INFO: ("#2e7d32", "Sin fenómenos que requieran acción."),
                  Severidad.ADVERTENCIA: ("#b07a00", "Hay advertencias para revisar."),
                  Severidad.CRITICA: ("#c0392b", "Hay condiciones críticas: vea las alertas y el informe técnico."),
                  Severidad.ERROR: ("#7d1f9e", "Hay datos inválidos.")}[peor]
        self.lbl_resumen.setText(
            f"<b>Válvula: {_html.escape(E._valvula_resumen(res))}</b><br>"
            f"Cv máximo requerido: <b>{fmt(max(s['Cv'] for s in res.salidas))}</b> · "
            f"<span style='color:{estado[0]}'><b>{estado[1]}</b></span>")
        self._mostrar_salidas()
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
        for k, fs in self.salidas.items():
            mag = fs.magnitud
            if k == "visc":
                mag = "viscosidad_cin" if cin else "viscosidad_din"
            fs.lbl_unidad.setText(pr.un(mag) if mag in pr.u else ("" if mag in (None, "texto") else mag))
            for j, caso in enumerate(CASOS):
                if caso not in nombres:
                    fs.celdas[j].setText("")
                    continue
                s = res.salidas[nombres.index(caso)]
                if k == "visc":
                    v = s["nu"] if cin else s["mu"]
                elif k == "apertura":
                    v = s["apertura"] * 100
                else:
                    v = s.get(k)
                if mag == "texto":
                    txt = v or ""
                elif mag in pr.u:
                    txt = pr.v(v, mag, fs.cifras)
                else:
                    txt = fmt(v, fs.cifras)
                fs.celdas[j].setText(txt)

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
            partes.append(f"<p><a href='ayuda:{a.codigo}'>Ir a la explicación del fenómeno…</a></p>")
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
                v.setHtml("<p style='color:#55606d'>Todavía no hay cálculo. Complete Inst-Valve-Data y "
                          "Dim-Valve-Data y presione <b>Calcular</b>.</p>")
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
    def _estado(self) -> dict:
        s = {"version": __version__, "sistema": self.sistema, "campos": {}, "filas": {},
             "casos_activos": [c.isChecked() for c in self.chk_caso]}
        for k, w in self.campos.items():
            s["campos"][k] = w.currentText() if isinstance(w, QComboBox) else w.text()
        for f in [*self.filas.values(), self.f_Pc, self.f_Pd, self.f_Td, self.f_c]:
            s["filas"][f.clave] = {"unidad": f.unidad.currentText(), "valores": [e.text() for e in f.edits]}
        return s

    def _cargar(self, s: dict):
        self.aplicar_sistema(s.get("sistema", "SI"))
        for k, v in s.get("campos", {}).items():
            w = self.campos.get(k)
            if isinstance(w, QComboBox):
                i = w.findText(v)
                if i >= 0:
                    w.setCurrentIndex(i)
            elif w is not None:
                w.setText(v)
        filas = {f.clave: f for f in [*self.filas.values(), self.f_Pc, self.f_Pd, self.f_Td, self.f_c]}
        for k, d in s.get("filas", {}).items():
            f = filas.get(k)
            if f is None:
                continue
            f.elegir(d["unidad"], convertir=False)
            for e, v in zip(f.edits, d["valores"]):
                e.setText(v)
        for c, v in zip(self.chk_caso, s.get("casos_activos", [])):
            c.setChecked(v)
        self.res = None
        self._actualizar_vistas()

    def nuevo(self):
        for f in [*self.filas.values(), self.f_Pc, self.f_Pd, self.f_Td, self.f_c]:
            for e in f.edits:
                e.clear()
        for ed in self.ed_ident.values():
            ed.clear()
        self.ed_ident["revision"].setText("0")
        self.ed_Kc.clear()
        self.ed_cvnom.clear()
        self.res = None
        self.ruta = None
        self.lbl_resumen.setText("Sin cálculo.")
        self.lista_alertas.clear()
        for fs in self.salidas.values():
            for c in fs.celdas:
                c.clear()
        self._actualizar_vistas()

    def guardar(self, como: bool = False):
        ruta = self.ruta
        if como or not ruta:
            ruta, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "", "Proyecto Valveselect (*.valvula)")
        if ruta:
            if not ruta.endswith(".valvula"):
                ruta += ".valvula"
            with open(ruta, "w", encoding="utf-8") as fh:
                json.dump(self._estado(), fh, ensure_ascii=False, indent=1)
            self.ruta = ruta
            self.statusBar().showMessage(f"Proyecto guardado: {os.path.basename(ruta)}")

    def abrir(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", "Proyecto Valveselect (*.valvula)")
        if ruta:
            with open(ruta, encoding="utf-8") as fh:
                s = json.load(fh)
            if "campos" not in s:
                QMessageBox.warning(self, "Proyecto de versión anterior",
                                    "El archivo es de la versión 1 y no se puede abrir en esta versión.")
                return
            self._cargar(s)
            self.ruta = ruta

    def acerca(self):
        QMessageBox.about(self, "Acerca de",
                          f"<b>{E.PRODUCTO}</b> versión {__version__}<br>{E.EMPRESA}<br><br>"
                          "Dimensionamiento de válvulas de control para líquidos según IEC 60534-2-1 / "
                          "ANSI/ISA-75.01.01, cavitación y ruido IEC 60534-8-4, tuberías ASME B36.10M / "
                          "B36.19M, rating ASME B16.34 y clases de cierre ANSI/FCI 70-2.<br><br>"
                          "Software independiente de fabricantes de válvulas.<br>"
                          "Propiedades de fluidos: CoolProp (licencia MIT).")
