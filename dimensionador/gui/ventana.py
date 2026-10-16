"""Ventana principal del dimensionador."""
from __future__ import annotations

import html as _html
import json
import math
from dataclasses import dataclass

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QPageSize, QPdfWriter, QShortcut, QTextDocument
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog,
                               QFileDialog, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QMessageBox, QPushButton, QScrollArea, QSplitter,
                               QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser, QToolButton,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import __version__, asme_b16_34, ayuda, propiedades, unidades as U
from ..estilos import ESTILOS, TAMANOS
from ..iec60534_2_1 import Bifasico, CapacidadInsuficiente, Gas, Liquido
from ..modelos import ErrorDatos, Severidad
from ..servicio import Caso, Informe, Seleccion, dimensionar

CASOS = ["Mínimo", "Normal", "Máximo"]
USUARIO = "Definido por el usuario"
COLORES = {Severidad.INFO: "#2f6fb0", Severidad.ADVERTENCIA: "#b07a00",
           Severidad.CRITICA: "#c0392b", Severidad.ERROR: "#7d1f9e"}
NOMBRE_SEV = {Severidad.INFO: "Información", Severidad.ADVERTENCIA: "Advertencia",
              Severidad.CRITICA: "Crítica", Severidad.ERROR: "Error de datos"}


def leer_numero(texto: str) -> float | None:
    t = texto.strip().replace(" ", "")
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    return float(t)


def fmt(v: float | None, cifras: int = 4) -> str:
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    if v == 0:
        return "0"
    a = abs(v)
    if a >= 1e6 or a < 1e-3:
        return f"{v:.{cifras - 1}e}".replace(".", ",")
    dec = max(0, cifras - 1 - int(math.floor(math.log10(a))))
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# Ventana de ayuda
# ---------------------------------------------------------------------------
class VentanaAyuda(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayuda del dimensionador")
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
            for titulo, k in sorted(por_cat[cat]):
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


# ---------------------------------------------------------------------------
# Fila de datos por caso
# ---------------------------------------------------------------------------
@dataclass
class DefFila:
    clave: str          # identificador interno y de ayuda
    etiqueta: str
    magnitudes: tuple   # magnitudes cuyas unidades se ofrecen
    servicios: tuple    # "liquido", "gas", "vapor"
    propiedad: bool = False   # se calcula con la biblioteca de propiedades


FILAS = [
    DefFila("caudal", "Caudal", ("caudal_vol", "caudal_masico"), ("liquido",)),
    DefFila("caudal_g", "Caudal", ("caudal_masico", "caudal_gas_std"), ("gas", "vapor")),
    DefFila("caudal_b", "Caudal másico total", ("caudal_masico",), ("bifasico",)),
    DefFila("P1", "Presión de entrada P1", ("presion",), ("liquido", "gas", "vapor", "bifasico")),
    DefFila("P2", "Presión de salida P2", ("presion",), ("liquido", "gas", "vapor", "bifasico")),
    DefFila("xg", "Fracción másica de gas/vapor", ("fraccion",), ("bifasico",)),
    DefFila("T1", "Temperatura de entrada T1", ("temperatura",), ("liquido", "gas", "vapor", "bifasico")),
    DefFila("rho", "Densidad ρ1", ("densidad",), ("liquido", "gas", "vapor"), True),
    DefFila("rho_l", "Densidad del líquido ρl", ("densidad",), ("bifasico",), True),
    DefFila("rho_g", "Densidad del gas ρg", ("densidad",), ("bifasico",), True),
    DefFila("Pv", "Presión de vapor Pv", ("presion",), ("liquido", "bifasico"), True),
    DefFila("Pc", "Presión crítica Pc", ("presion",), ("liquido", "bifasico"), True),
    DefFila("viscosidad", "Viscosidad", ("viscosidad_din", "viscosidad_cin"), ("liquido",), True),
    DefFila("M", "Masa molar M", ("masa_molar",), ("gas", "vapor"), True),
    DefFila("gamma", "Relación de calores γ", ("adimensional",), ("gas", "vapor", "bifasico"), True),
    DefFila("Z", "Compresibilidad Z", ("adimensional",), ("gas", "vapor"), True),
    DefFila("mu", "Viscosidad μ", ("viscosidad_din",), ("gas", "vapor"), True),
]
AYUDA_FILA = {"caudal_g": "caudal", "caudal_b": "bifasico", "mu": "mu"}


class Fila:
    def __init__(self, d: DefFila, grid: QGridLayout, r: int, abrir_ayuda):
        self.d = d
        self.lbl = QLabel(d.etiqueta)
        self.btn = QToolButton(text="?")
        self.btn.setToolTip("Ver explicación de este dato (F1)")
        clave_ayuda = AYUDA_FILA.get(d.clave, d.clave)
        self.btn.clicked.connect(lambda: abrir_ayuda(clave_ayuda))
        self.unidad = QComboBox()
        self.mag_de: dict[str, str] = {}
        for m in d.magnitudes:
            for s in U.unidades_de(m):
                self.unidad.addItem(s)
                self.mag_de[s] = m
        self.unidad.setProperty("ayuda", clave_ayuda)
        self.unidad.currentTextChanged.connect(self._cambio_unidad)
        self._unidad_ant = self.unidad.currentText()
        self.edits = []
        grid.addWidget(self.lbl, r, 0)
        grid.addWidget(self.btn, r, 1)
        grid.addWidget(self.unidad, r, 2)
        for j in range(3):
            e = QLineEdit()
            e.setProperty("ayuda", clave_ayuda)
            e.setAlignment(Qt.AlignRight)
            e.setMinimumWidth(80)
            grid.addWidget(e, r, 3 + j)
            self.edits.append(e)
        if d.clave == "gamma" or d.clave == "Z":
            self.unidad.setEnabled(False)

    def widgets(self):
        return [self.lbl, self.btn, self.unidad, *self.edits]

    def visible(self, v: bool):
        for w in self.widgets():
            w.setVisible(v)

    def magnitud(self) -> str:
        return self.mag_de[self.unidad.currentText()]

    def _cambio_unidad(self, nueva: str):
        ant = self._unidad_ant
        self._unidad_ant = nueva
        if self.mag_de.get(ant) != self.mag_de.get(nueva):
            return   # cambio de tipo de caudal: el número no se puede convertir sin densidad
        for e in self.edits:
            try:
                v = leer_numero(e.text())
            except ValueError:
                continue
            if v is not None:
                e.setText(fmt(U.convertir(v, self.mag_de[nueva], ant, nueva), 6).replace(".", ""))

    def valor_base(self, j: int) -> float | None:
        v = leer_numero(self.edits[j].text())
        if v is None:
            return None
        return U.a_base(v, self.magnitud(), self.unidad.currentText())

    def poner_base(self, j: int, valor: float | None):
        if valor is None:
            self.edits[j].setText("")
            return
        v = U.desde_base(valor, self.magnitud(), self.unidad.currentText())
        self.edits[j].setText(fmt(v, 6).replace(".", ""))

    def elegir_unidad(self, simbolo: str):
        if self.unidad.findText(simbolo) >= 0:
            self.unidad.setCurrentText(simbolo)


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Dimensionador de válvulas de control  {__version__}")
        self.resize(1400, 860)
        self.ayuda = VentanaAyuda(self)
        self.informe: Informe | None = None
        self.sistema = "SI"
        self._construir_menu()

        split = QSplitter()
        split.addWidget(self._panel_datos())
        split.addWidget(self._panel_resultados())
        split.setSizes([620, 780])
        self.setCentralWidget(split)
        QShortcut(QKeySequence(Qt.Key_F1), self, activated=self._ayuda_foco)
        self._cambio_servicio()
        self.aplicar_sistema("SI")
        self.statusBar().showMessage("Complete los datos y presione Calcular. F1 o «?» explican cada dato.")

    # ------------------------------------------------------------------ menú
    def _construir_menu(self):
        mb = self.menuBar()
        m = mb.addMenu("&Archivo")
        for texto, fn, atajo in [("Nuevo", self.nuevo, QKeySequence.New),
                                 ("Abrir proyecto…", self.abrir, QKeySequence.Open),
                                 ("Guardar proyecto…", self.guardar, QKeySequence.Save),
                                 ("Exportar informe PDF…", self.exportar_pdf, None),
                                 ("Exportar informe HTML…", self.exportar_html, None),
                                 ("Salir", self.close, QKeySequence.Quit)]:
            a = QAction(texto, self)
            a.triggered.connect(fn)
            if atajo:
                a.setShortcut(atajo)
            m.addAction(a)
        mu = mb.addMenu("&Unidades")
        for s in U.SISTEMAS:
            a = QAction("Sistema " + ("Internacional (SI)" if s == "SI" else "Imperial"), self)
            a.triggered.connect(lambda _=False, s=s: self.aplicar_sistema(s))
            mu.addAction(a)
        ma = mb.addMenu("A&yuda")
        a = QAction("Índice de ayuda", self)
        a.triggered.connect(lambda: self.abrir_ayuda("kv_cv"))
        ma.addAction(a)
        a = QAction("Acerca de", self)
        a.triggered.connect(self.acerca)
        ma.addAction(a)

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
        self.abrir_ayuda("kv_cv")

    def _boton_ayuda(self, clave):
        b = QToolButton(text="?")
        b.setToolTip("Ver explicación (F1)")
        b.clicked.connect(lambda: self.abrir_ayuda(clave))
        return b

    def _fila_form(self, form: QFormLayout, etiqueta: str, widget, clave: str):
        widget.setProperty("ayuda", clave)
        h = QHBoxLayout()
        h.addWidget(widget, 1)
        h.addWidget(self._boton_ayuda(clave))
        form.addRow(etiqueta, h)

    # ------------------------------------------------------------ panel datos
    def _panel_datos(self):
        cont = QWidget()
        lay = QVBoxLayout(cont)

        g = QGroupBox("Servicio")
        f = QFormLayout(g)
        self.cb_servicio = QComboBox()
        self.cb_servicio.addItems(["Líquido", "Gas", "Vapor de agua", "Bifásico (líquido + gas o vapor)"])
        self.cb_servicio.currentIndexChanged.connect(self._cambio_servicio)
        self._fila_form(f, "Tipo de servicio", self.cb_servicio, "tipo_fluido")
        self.cb_fluido = QComboBox()
        self.cb_fluido.addItems([USUARIO, *propiedades.FLUIDOS.keys()])
        self.cb_fluido.currentIndexChanged.connect(self._cambio_fluido)
        self._fila_form(f, "Fluido", self.cb_fluido, "fluido")
        self.chk_saturado = QCheckBox("Vapor saturado seco (T1 = temperatura de saturación)")
        f.addRow("", self.chk_saturado)
        self.cb_sistema = QComboBox()
        self.cb_sistema.addItems(["SI", "Imperial"])
        self.cb_sistema.currentTextChanged.connect(self.aplicar_sistema)
        self._fila_form(f, "Sistema de unidades", self.cb_sistema, "sistema_unidades")
        lay.addWidget(g)

        g = QGroupBox("Condiciones de operación")
        grid = QGridLayout(g)
        grid.addWidget(QLabel("<b>Dato</b>"), 0, 0)
        grid.addWidget(QLabel("<b>Unidad</b>"), 0, 2)
        self.chk_caso = []
        for j, c in enumerate(CASOS):
            ch = QCheckBox(c)
            ch.setChecked(c != "Mínimo")
            ch.setProperty("ayuda", "casos")
            grid.addWidget(ch, 0, 3 + j)
            self.chk_caso.append(ch)
        self.filas: dict[str, Fila] = {}
        for i, d in enumerate(FILAS, start=1):
            self.filas[d.clave] = Fila(d, grid, i, self.abrir_ayuda)
        self.btn_prop = QPushButton("Calcular propiedades del fluido")
        self.btn_prop.clicked.connect(self._boton_propiedades)
        grid.addWidget(self.btn_prop, len(FILAS) + 1, 0, 1, 6)
        lay.addWidget(g)

        g = QGroupBox("Válvula y tubería")
        f = QFormLayout(g)
        self.cb_estilo = QComboBox()
        for k, e in ESTILOS.items():
            self.cb_estilo.addItem(e.nombre, k)
        self.cb_estilo.currentIndexChanged.connect(self._cambio_estilo)
        self._fila_form(f, "Estilo", self.cb_estilo, "estilo")
        h = QHBoxLayout()
        self.ed_FL, self.ed_xT, self.ed_Fd = QLineEdit(), QLineEdit(), QLineEdit()
        for nombre, ed, clave in (("FL", self.ed_FL, "FL"), ("xT", self.ed_xT, "xT"), ("Fd", self.ed_Fd, "Fd")):
            ed.setProperty("ayuda", clave)
            ed.setMaximumWidth(70)
            h.addWidget(QLabel(nombre))
            h.addWidget(ed)
            h.addWidget(self._boton_ayuda(clave))
        h.addStretch()
        f.addRow("Factores (típicos)", h)
        self.ed_xFz = QLineEdit(placeholderText="estimado según IEC 60534-8-4")
        self._fila_form(f, "xFz inicio cavitación", self.ed_xFz, "xFz")
        self.cb_caract = QComboBox()
        self.cb_caract.addItem("Isoporcentual", "isoporcentual")
        self.cb_caract.addItem("Lineal", "lineal")
        self.cb_caract.addItem("Apertura rápida", "apertura_rapida")
        self._fila_form(f, "Característica", self.cb_caract, "caracteristica")
        self.cb_tamano = QComboBox()
        self.cb_tamano.addItem("Automático", None)
        for p, dn, _ in TAMANOS:
            self.cb_tamano.addItem(f"{p:g}\"  (DN {dn})", p)
        self._fila_form(f, "Diámetro de válvula", self.cb_tamano, "tamano")
        self.ed_kvnom = QLineEdit(placeholderText="típico del estilo")
        hk = QHBoxLayout()
        hk.addWidget(self.ed_kvnom, 1)
        self.cb_kvnom = QComboBox()
        self.cb_kvnom.addItems(["Cv", "Kv"])
        hk.addWidget(self.cb_kvnom)
        hk.addWidget(self._boton_ayuda("Kv_nominal"))
        self.ed_kvnom.setProperty("ayuda", "Kv_nominal")
        f.addRow("Capacidad nominal", hk)
        self.cb_D1, self.cb_D2 = QComboBox(), QComboBox()
        for cb, clave, et in ((self.cb_D1, "D1", "Tubería de entrada"), (self.cb_D2, "D1", "Tubería de salida")):
            cb.setEditable(True)
            cb.addItem("Igual a la válvula", None)
            for p, dn, di in TAMANOS:
                cb.addItem(f"{p:g}\" cédula 40 (DI {di:.1f} mm)", di)
            cb.setCurrentIndex(0)
            self._fila_form(f, et, cb, clave)
        self.ed_tp = QLineEdit(placeholderText="cédula 40 según el diámetro")
        self._fila_form(f, "Espesor de pared salida [mm]", self.ed_tp, "espesor_pared")
        self.ed_c14e = QLineEdit("100")
        self._fila_form(f, "C de API RP 14E", self.ed_c14e, "C_api14e")
        self.ed_lim_ruido = QLineEdit("85")
        self._fila_form(f, "Límite de ruido [dB(A)]", self.ed_lim_ruido, "limite_ruido")
        lay.addWidget(g)

        g = QGroupBox("Cuerpo: material y clase de presión (ASME B16.34)")
        f = QFormLayout(g)
        self.cb_material = QComboBox()
        for k, m in asme_b16_34.MATERIALES.items():
            self.cb_material.addItem(m.nombre, k)
        self._fila_form(f, "Material", self.cb_material, "material")
        self.cb_clase = QComboBox()
        self.cb_clase.addItem("Automática (mínima que cumple)", None)
        for c in asme_b16_34.CLASES:
            self.cb_clase.addItem(f"Clase {c}", c)
        self._fila_form(f, "Clase", self.cb_clase, "clase_presion")
        self.ed_Pd, self.cb_Pd = QLineEdit(placeholderText="máxima P1 de los casos"), QComboBox()
        self.cb_Pd.addItems(U.unidades_de("presion"))
        self.ed_Td, self.cb_Td = QLineEdit(placeholderText="máxima T1 de los casos"), QComboBox()
        self.cb_Td.addItems(U.unidades_de("temperatura"))
        for et, ed, cb, clave in (("Presión de diseño", self.ed_Pd, self.cb_Pd, "P_diseno"),
                                  ("Temperatura de diseño", self.ed_Td, self.cb_Td, "P_diseno")):
            ed.setProperty("ayuda", clave)
            h = QHBoxLayout()
            h.addWidget(ed, 1)
            h.addWidget(cb)
            h.addWidget(self._boton_ayuda(clave))
            f.addRow(et, h)
        lay.addWidget(g)

        self.btn_calc = QPushButton("Calcular")
        self.btn_calc.setMinimumHeight(40)
        fb = self.btn_calc.font()
        fb.setBold(True)
        fb.setPointSize(fb.pointSize() + 2)
        self.btn_calc.setFont(fb)
        self.btn_calc.clicked.connect(self.calcular)
        lay.addWidget(self.btn_calc)
        lay.addStretch()
        self._cambio_estilo()

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(cont)
        return sc

    # ------------------------------------------------------- panel resultados
    def _panel_resultados(self):
        cont = QWidget()
        lay = QVBoxLayout(cont)
        self.lbl_resumen = QLabel("Sin cálculo.")
        self.lbl_resumen.setWordWrap(True)
        self.lbl_resumen.setFrameShape(QFrame.StyledPanel)
        self.lbl_resumen.setMargin(8)
        lay.addWidget(self.lbl_resumen)
        self.tabs = QTabWidget()

        self.tab_res = QTableWidget()
        self.tab_res.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab_res.verticalHeader().setVisible(False)
        self.tab_res.cellDoubleClicked.connect(self._ayuda_resultado)
        self.tab_res.setToolTip("Doble clic en una fila para ver la explicación de ese valor.")
        self.tabs.addTab(self.tab_res, "Resultados")

        w = QWidget()
        v = QVBoxLayout(w)
        self.lista_alertas = QTreeWidget()
        self.lista_alertas.setHeaderLabels(["Severidad", "Caso", "Fenómeno", "Intensidad"])
        self.lista_alertas.setRootIsDecorated(False)
        self.lista_alertas.currentItemChanged.connect(self._detalle_alerta)
        self.detalle_alerta = QTextBrowser()
        self.detalle_alerta.setOpenLinks(False)
        self.detalle_alerta.anchorClicked.connect(lambda u: self.abrir_ayuda(u.toString()[6:]))
        sp = QSplitter(Qt.Vertical)
        sp.addWidget(self.lista_alertas)
        sp.addWidget(self.detalle_alerta)
        sp.setSizes([260, 340])
        v.addWidget(sp)
        self.tabs.addTab(w, "Alertas")

        self.arbol_memoria = QTreeWidget()
        self.arbol_memoria.setHeaderLabels(["Símbolo", "Descripción", "Valor", "Unidad", "Fórmula", "Referencia"])
        self.tabs.addTab(self.arbol_memoria, "Memoria de cálculo")

        self.tab_tam = QTableWidget()
        self.tab_tam.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab_tam.verticalHeader().setVisible(False)
        self.tabs.addTab(self.tab_tam, "Selección de tamaño")
        lay.addWidget(self.tabs, 1)
        return cont

    # ------------------------------------------------------------- eventos
    def servicio(self) -> str:
        return ["liquido", "gas", "vapor", "bifasico"][self.cb_servicio.currentIndex()]

    def _cambio_servicio(self):
        s = self.servicio()
        for f in self.filas.values():
            f.visible(s in f.d.servicios)
        self.chk_saturado.setVisible(s == "vapor")
        if s == "vapor":
            self.cb_fluido.setCurrentText("Agua / vapor de agua")
        self.cb_fluido.setEnabled(s != "vapor")
        self._cambio_fluido()

    def _cambio_fluido(self):
        manual = self.cb_fluido.currentText() == USUARIO
        self.btn_prop.setEnabled(not manual)
        for f in self.filas.values():
            if f.d.propiedad:
                for e in f.edits:
                    e.setReadOnly(not manual)
                    e.setStyleSheet("" if manual else "background:#f0f0f0;")

    def _cambio_estilo(self):
        e = ESTILOS[self.cb_estilo.currentData()]
        self.ed_FL.setText(f"{e.FL:g}".replace(".", ","))
        self.ed_xT.setText(f"{e.xT:g}".replace(".", ","))
        self.ed_Fd.setText(f"{e.Fd:g}".replace(".", ","))
        self.cb_caract.setCurrentIndex(self.cb_caract.findData(e.caracteristica))
        self.cb_estilo.setToolTip(e.nota or e.nombre)

    def aplicar_sistema(self, sistema: str):
        self.sistema = sistema
        if self.cb_sistema.currentText() != sistema:
            self.cb_sistema.blockSignals(True)
            self.cb_sistema.setCurrentText(sistema)
            self.cb_sistema.blockSignals(False)
        pref = U.SISTEMAS[sistema]
        for f in self.filas.values():
            actual = f.magnitud()
            if f.d.clave in ("caudal", "caudal_g"):
                f.elegir_unidad(pref[actual])
            elif f.d.clave in ("P1", "P2"):
                f.elegir_unidad("bar g" if sistema == "SI" else "psig")
            elif f.d.clave in ("Pv", "Pc"):
                f.elegir_unidad(pref["presion"])
            else:
                f.elegir_unidad(pref[actual])
        self.cb_kvnom.setCurrentText("Kv" if sistema == "SI" else "Cv")
        if not self.ed_Pd.text():
            self.cb_Pd.setCurrentText("bar g" if sistema == "SI" else "psig")
        if not self.ed_Td.text():
            self.cb_Td.setCurrentText("°C" if sistema == "SI" else "°F")
        if self.informe:
            self._mostrar(self.informe)

    # ---------------------------------------------------------- lectura
    def _float(self, ed: QLineEdit, nombre: str, opcional=False) -> float | None:
        try:
            v = leer_numero(ed.text())
        except ValueError:
            raise ValueError(f"El valor «{ed.text()}» de {nombre} no es un número.")
        if v is None and not opcional:
            raise ValueError(f"Falta el dato {nombre}.")
        return v

    def _diametro(self, cb: QComboBox) -> float | None:
        d = cb.currentData()
        if cb.currentIndex() >= 0 and cb.itemText(cb.currentIndex()) == cb.currentText():
            return d
        try:
            return leer_numero(cb.currentText())   # diámetro interior libre en mm
        except ValueError:
            raise ValueError("El diámetro de tubería debe elegirse de la lista o escribirse en mm.")

    def _casos_activos(self):
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
        s = self.servicio()
        F = self.filas
        for j in self._casos_activos():
            P1 = F["P1"].valor_base(j)
            T1 = F["T1"].valor_base(j)
            if s == "bifasico":
                if P1 is None:
                    raise ValueError(f"Caso {CASOS[j]}: ingrese P1 para obtener las propiedades.")
                p = propiedades.bifasico_saturado(fluido, P1)
                F["T1"].poner_base(j, p.T1)
                F["rho_l"].poner_base(j, p.rho_l)
                F["rho_g"].poner_base(j, p.rho_g)
                F["Pv"].poner_base(j, p.Pv)
                F["Pc"].poner_base(j, p.Pc)
                F["gamma"].poner_base(j, p.gamma)
                continue
            sat = s == "vapor" and self.chk_saturado.isChecked()
            if P1 is None or (T1 is None and not sat):
                raise ValueError(f"Caso {CASOS[j]}: ingrese P1 y T1 para obtener las propiedades.")
            if s == "liquido":
                p = propiedades.liquido(fluido, P1, T1)
                F["rho"].poner_base(j, p.rho)
                F["Pv"].poner_base(j, p.Pv)
                F["Pc"].poner_base(j, p.Pc)
                if F["viscosidad"].magnitud() == "viscosidad_cin":
                    F["viscosidad"].poner_base(j, p.nu)
                else:
                    F["viscosidad"].poner_base(j, p.mu)
            else:
                p = propiedades.gas(fluido, P1, T1, saturado=sat)
                if sat:
                    F["T1"].poner_base(j, propiedades.temperatura_saturacion(fluido, P1))
                F["rho"].poner_base(j, p.rho)
                F["M"].poner_base(j, p.M)
                F["gamma"].poner_base(j, p.gamma)
                F["Z"].poner_base(j, p.Z)
                F["mu"].poner_base(j, p.mu)

    def _leer_casos(self) -> list[Caso]:
        s = self.servicio()
        F = self.filas
        casos = []
        activos = self._casos_activos()
        if not activos:
            raise ValueError("Active al menos un caso de operación.")
        fluido = None if self.cb_fluido.currentText() == USUARIO else self.cb_fluido.currentText()
        for j in activos:
            n = CASOS[j]

            def req(clave):
                v = F[clave].valor_base(j)
                if v is None:
                    raise ValueError(f"Caso {n}: falta «{F[clave].d.etiqueta}».")
                return v
            if s == "bifasico":
                estado = Bifasico(P1=req("P1"), P2=req("P2"), T1=req("T1"), W=req("caudal_b"),
                                  xg=req("xg"), rho_l=req("rho_l"), rho_g=req("rho_g"), Pv=req("Pv"),
                                  Pc=req("Pc"), gamma=req("gamma"))
            elif s == "liquido":
                q = req("caudal")
                rho = req("rho")
                visc = req("viscosidad")
                nu = visc if F["viscosidad"].magnitud() == "viscosidad_cin" else visc / rho
                vol = F["caudal"].magnitud() == "caudal_vol"
                estado = Liquido(P1=req("P1"), P2=req("P2"), T1=req("T1"), rho1=rho, Pv=req("Pv"),
                                 Pc=req("Pc"), nu=nu, Q=q if vol else None, W=None if vol else q)
            else:
                q = req("caudal_g")
                masico = F["caudal_g"].magnitud() == "caudal_masico"
                rho = F["rho"].valor_base(j)
                estado = Gas(P1=req("P1"), P2=req("P2"), T1=req("T1"), M=req("M"), gamma=req("gamma"),
                             Z=req("Z"), mu=req("mu"), W=q if masico else None,
                             QN=None if masico else q, rho1=rho)
            casos.append(Caso(n, estado, fluido))
        return casos

    def _leer_seleccion(self) -> Seleccion:
        e = ESTILOS[self.cb_estilo.currentData()]
        kv = self._float(self.ed_kvnom, "capacidad nominal", True)
        if kv is not None and self.cb_kvnom.currentText() == "Cv":
            kv = U.cv_a_kv(kv)
        d = self.cb_tamano.currentData()
        if kv is not None and d is None:
            raise ValueError("Para usar una capacidad nominal fija elija también el diámetro de la válvula.")
        return Seleccion(e, d_pulg=d, Kv_nominal=kv, D1_mm=self._diametro(self.cb_D1),
                         D2_mm=self._diametro(self.cb_D2),
                         FL=self._float(self.ed_FL, "FL"), xT=self._float(self.ed_xT, "xT"),
                         Fd=self._float(self.ed_Fd, "Fd"), xFz=self._float(self.ed_xFz, "xFz", True),
                         C_api14e=self._float(self.ed_c14e, "C de API RP 14E"),
                         tp_mm=self._float(self.ed_tp, "espesor de pared", True),
                         limite_ruido=self._float(self.ed_lim_ruido, "límite de ruido"),
                         material=self.cb_material.currentData(), clase=self.cb_clase.currentData(),
                         P_diseno=self._con_unidad(self.ed_Pd, self.cb_Pd, "presion", "presión de diseño"),
                         T_diseno=self._con_unidad(self.ed_Td, self.cb_Td, "temperatura", "temperatura de diseño"))

    def _con_unidad(self, ed, cb, magnitud, nombre):
        v = self._float(ed, nombre, True)
        return None if v is None else U.a_base(v, magnitud, cb.currentText())

    def calcular(self):
        try:
            if self.cb_fluido.currentText() != USUARIO:
                self.calcular_propiedades()
            sel = self._leer_seleccion()
            casos = self._leer_casos()
            caract = self.cb_caract.currentData()
            if caract != sel.estilo.caracteristica:
                from dataclasses import replace
                sel.estilo = replace(sel.estilo, caracteristica=caract)
            self.informe = dimensionar(casos, sel)
        except ErrorDatos as e:
            self._mostrar_errores(e.alertas)
            return
        except (ValueError, propiedades.ErrorPropiedades, CapacidadInsuficiente) as e:
            QMessageBox.warning(self, "Datos incompletos o inválidos", str(e))
            return
        self._mostrar(self.informe)
        self.statusBar().showMessage("Cálculo terminado.")

    def _mostrar_errores(self, alertas):
        self.lista_alertas.clear()
        for a in alertas:
            it = QTreeWidgetItem([NOMBRE_SEV[a.severidad], "", a.titulo, ""])
            it.setForeground(0, QColor(COLORES[a.severidad]))
            it.setData(0, Qt.UserRole, a)
            self.lista_alertas.addTopLevelItem(it)
        self.tabs.setCurrentIndex(1)
        if alertas:
            self.lista_alertas.setCurrentItem(self.lista_alertas.topLevelItem(0))
        self.lbl_resumen.setText("<b style='color:#7d1f9e'>No se pudo calcular: hay datos inválidos. "
                                 "Vea la pestaña Alertas.</b>")

    # ----------------------------------------------------------- mostrar
    def _u(self, magnitud):
        return U.SISTEMAS[self.sistema][magnitud]

    def _conv(self, v, magnitud):
        if v is None:
            return None
        return U.desde_base(v, magnitud, self._u(magnitud))

    def _filas_resultado(self, inf: Informe):
        """Lista de (clave_ayuda, etiqueta, unidad, [valores por caso])."""
        liquido = isinstance(inf.casos[0].caso.estado, Liquido)
        bifasico = isinstance(inf.casos[0].caso.estado, Bifasico)
        pd, vel = self._u("presion_dif"), self._u("velocidad")
        filas = []

        def fila(clave, etiqueta, unidad, fn):
            vals = []
            for rc in inf.casos:
                try:
                    vals.append(fn(rc))
                except (KeyError, TypeError):
                    vals.append(None)
            filas.append((clave, etiqueta, unidad, vals))
        fila("kv_cv", "Cv requerido", "-", lambda rc: rc.resultado.Cv)
        fila("kv_cv", "Kv requerido", "m³/h", lambda rc: rc.resultado.Kv)
        fila("apertura", "Apertura estimada", "%", lambda rc: rc.apertura * 100)
        fila("tipo_fluido", "Régimen", "", lambda rc: rc.resultado.regimen)
        fila("dPchoked" if liquido else "gas_bloqueado", "Flujo crítico (bloqueado)", "",
             lambda rc: "Sí" if rc.resultado.bloqueado else "No")
        dp = lambda rc: U.desde_base(rc.caso.estado.P1 - rc.caso.estado.P2, "presion_dif", pd)
        fila("dP", "Caída de presión ΔP", pd, dp)
        if bifasico:
            fila("bifasico", "ΔP efectiva fase líquida", pd,
                 lambda rc: U.desde_base(rc.resultado.extra["dPf"], "presion_dif", pd))
            fila("bifasico", "ΔP efectiva fase gaseosa", pd,
                 lambda rc: U.desde_base(rc.resultado.extra["dPg"], "presion_dif", pd))
            fila("Y", "Factor de expansión Y", "-", lambda rc: rc.resultado.extra["Y"])
            fila("bifasico", "Densidad de la mezcla a la salida", self._u("densidad"),
                 lambda rc: self._conv(rc.datos["rho_mezcla_salida"], "densidad"))
        elif liquido:
            fila("dPchoked", "ΔP de flujo crítico", pd,
                 lambda rc: U.desde_base(rc.resultado.extra["dPchoked"], "presion_dif", pd))
            fila("FF", "FF", "-", lambda rc: rc.resultado.extra["FF"])
            fila("FLP", "FLP", "-", lambda rc: rc.resultado.extra["FLP"])
            fila("xF", "xF = ΔP/(P1 − Pv)", "-", lambda rc: rc.datos["xF"])
            fila("xFz", "xFzp1 inicio de cavitación", "-", lambda rc: rc.datos["xFzp1"])
            fila("sigma", "σ = (P1 − Pv)/ΔP", "-", lambda rc: rc.datos["sigma"])
            fila("cavitacion", "Condición", "", lambda rc: rc.datos["regimen"])
            fila("flashing", "Vapor formado a la salida", "%", lambda rc: rc.datos["calidad_salida"] * 100)
        else:
            fila("x", "x = ΔP/P1", "-", lambda rc: rc.resultado.extra["x"])
            fila("xchoked", "xchoked", "-", lambda rc: rc.resultado.extra["xchoked"])
            fila("Y", "Factor de expansión Y", "-", lambda rc: rc.resultado.extra["Y"])
            fila("Fgamma", "Fγ", "-", lambda rc: rc.resultado.extra["Fgamma"])
            fila("xTP", "xTP", "-", lambda rc: rc.resultado.extra["xTP"])
            fila("mach_salida", "Mach a la salida de la válvula", "-", lambda rc: rc.datos["Mach_salida_valvula"])
        if not bifasico:
            fila("ruido", "Ruido LpAe,1m", "dB(A)", lambda rc: rc.datos["ruido_LpAe1m"])
        if not liquido and not bifasico:
            fila("ruido", "Régimen de ruido (IEC 60534-8-3)", "", lambda rc: rc.datos["ruido_regimen"].split(" ")[0])
        fila("FP", "FP", "-", lambda rc: rc.resultado.FP)
        if not bifasico:
            fila("Rev", "Número de Reynolds Rev", "-", lambda rc: rc.resultado.Rev)
            fila("FR", "FR", "-", lambda rc: rc.resultado.FR)
        fila("velocidad_liquido" if liquido else "mach_salida", "Velocidad a la salida de la válvula", vel,
             lambda rc: self._conv(rc.datos["v_salida_valvula"], "velocidad"))
        fila("erosional_api14e", "Velocidad en tubería de salida", vel,
             lambda rc: self._conv(rc.datos["v_tuberia_salida"], "velocidad"))
        fila("erosional_api14e", "Velocidad erosional API RP 14E", vel,
             lambda rc: self._conv(rc.datos["v_erosional_api14e"], "velocidad"))
        return filas

    def _mostrar(self, inf: Informe):
        # Resumen
        peor = max([a.severidad for _, a in inf.todas_las_alertas()] or [Severidad.INFO])
        estado = {Severidad.INFO: ("#2e7d32", "Sin fenómenos que requieran acción."),
                  Severidad.ADVERTENCIA: ("#b07a00", "Hay advertencias para revisar."),
                  Severidad.CRITICA: ("#c0392b", "Hay condiciones críticas: vea la pestaña Alertas."),
                  Severidad.ERROR: ("#7d1f9e", "Hay datos inválidos.")}[peor]
        kvn = inf.Kv_nominal
        estilo = self.cb_estilo.currentText()
        linea_clase = ""
        if inf.clase and inf.rating_barg:
            if self.sistema == "Imperial":
                adm = f"{fmt(U.convertir(inf.rating_barg, 'presion', 'bar g', 'psig'))} psig a {fmt(inf.T_diseno_C * 9 / 5 + 32)} °F"
                dis = f"{fmt(U.convertir(inf.P_diseno_barg, 'presion', 'bar g', 'psig'))} psig"
            else:
                adm = f"{fmt(inf.rating_barg)} bar g a {fmt(inf.T_diseno_C)} °C"
                dis = f"{fmt(inf.P_diseno_barg)} bar g"
            linea_clase = (f"Cuerpo: {_html.escape(self.cb_material.currentText())}, <b>clase {inf.clase}</b> "
                           f"(admite {adm}; diseño {dis})<br>")
        self.lbl_resumen.setText(
            f"<b>Válvula: {inf.d_pulg:g}\" (DN {inf.DN})</b> — {_html.escape(estilo)}<br>"
            f"Capacidad nominal: Cv {fmt(U.kv_a_cv(kvn))} / Kv {fmt(kvn)} · "
            f"Cv máximo requerido: {fmt(max(rc.resultado.Cv for rc in inf.casos))}<br>"
            + linea_clase
            + f"<span style='color:{estado[0]}'><b>{estado[1]}</b></span>")

        # Resultados
        filas = self._filas_resultado(inf)
        t = self.tab_res
        t.clear()
        t.setColumnCount(2 + len(inf.casos))
        t.setRowCount(len(filas))
        t.setHorizontalHeaderLabels(["Magnitud", "Unidad", *[rc.caso.nombre for rc in inf.casos]])
        for i, (clave, et, un, vals) in enumerate(filas):
            it = QTableWidgetItem(et)
            it.setData(Qt.UserRole, clave)
            t.setItem(i, 0, it)
            t.setItem(i, 1, QTableWidgetItem(un))
            for j, v in enumerate(vals):
                txt = v if isinstance(v, str) else fmt(v)
                c = QTableWidgetItem(txt)
                c.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                t.setItem(i, 2 + j, c)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for j in range(len(inf.casos)):
            hh.setSectionResizeMode(2 + j, QHeaderView.Stretch)

        # Alertas
        self.lista_alertas.clear()
        for caso, a in inf.todas_las_alertas():
            inten = ""
            if a.intensidad is not None:
                barras = "█" * int(round(a.intensidad / 10)) + "░" * (10 - int(round(a.intensidad / 10)))
                inten = f"{barras} {a.intensidad:.0f} %" + (f" {a.nivel}" if a.nivel else "")
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

        # Memoria
        self.arbol_memoria.clear()
        for rc in inf.casos:
            raiz = QTreeWidgetItem([f"Caso {rc.caso.nombre}"])
            f = raiz.font(0)
            f.setBold(True)
            raiz.setFont(0, f)
            for p in rc.resultado.memoria.pasos:
                QTreeWidgetItem(raiz, [p.simbolo, p.descripcion, fmt(p.valor, 5), p.unidad, p.formula,
                                       p.referencia])
            self.arbol_memoria.addTopLevelItem(raiz)
            raiz.setExpanded(True)
        for i in range(6):
            self.arbol_memoria.resizeColumnToContents(i)

        # Tamaños
        t = self.tab_tam
        t.clear()
        cols = ["Diámetro", "DN", "Cv nominal típico", "Cv requerido máx.", "Apertura máx. %", ""]
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.setRowCount(len(inf.tabla_tamanos))
        for i, fila_t in enumerate(inf.tabla_tamanos):
            elegido = abs(fila_t["d_pulg"] - inf.d_pulg) < 1e-9
            vals = [f"{fila_t['d_pulg']:g}\"", str(fila_t["DN"]), fmt(U.kv_a_cv(fila_t["Kv_nominal"])),
                    fmt(U.kv_a_cv(fila_t["Kv_max"])) if fila_t["Kv_max"] else "insuficiente",
                    fmt(fila_t["apertura_max"] * 100) if fila_t["apertura_max"] is not None else "—",
                    "◀ seleccionada" if elegido else ""]
            for j, v in enumerate(vals):
                c = QTableWidgetItem(v)
                if elegido:
                    fb = c.font()
                    fb.setBold(True)
                    c.setFont(fb)
                t.setItem(i, j, c)
        t.resizeColumnsToContents()

    def _detalle_alerta(self, it, _=None):
        if it is None:
            return
        a = it.data(0, Qt.UserRole)
        partes = [f"<h3 style='color:{COLORES[a.severidad]}'>{_html.escape(a.titulo)}</h3>",
                  f"<p>{_html.escape(a.mensaje)}</p>"]
        if a.intensidad is not None:
            partes.append(f"<p><b>Intensidad:</b> {a.intensidad:.0f} %"
                          + (f" ({a.nivel})" if a.nivel else "") + "</p>")
        if a.remedios:
            partes.append("<p><b>Posibles soluciones:</b></p><ul>"
                          + "".join(f"<li>{_html.escape(r)}</li>" for r in a.remedios) + "</ul>")
        if a.referencia:
            partes.append(f"<p><i>Referencia: {_html.escape(a.referencia)}</i></p>")
        if ayuda.obtener(a.codigo):
            partes.append(f"<p><a href='ayuda:{a.codigo}'>Ver explicación detallada del fenómeno…</a></p>")
        self.detalle_alerta.setHtml("".join(partes))

    def _ayuda_resultado(self, fila, _col):
        it = self.tab_res.item(fila, 0)
        if it and it.data(Qt.UserRole):
            self.abrir_ayuda(it.data(Qt.UserRole))

    # ------------------------------------------------------------ archivo
    def _estado(self) -> dict:
        return {
            "version": __version__, "sistema": self.sistema,
            "servicio": self.cb_servicio.currentIndex(), "fluido": self.cb_fluido.currentText(),
            "saturado": self.chk_saturado.isChecked(),
            "casos_activos": [c.isChecked() for c in self.chk_caso],
            "filas": {k: {"unidad": f.unidad.currentText(), "valores": [e.text() for e in f.edits]}
                      for k, f in self.filas.items()},
            "estilo": self.cb_estilo.currentData(),
            "FL": self.ed_FL.text(), "xT": self.ed_xT.text(), "Fd": self.ed_Fd.text(),
            "xFz": self.ed_xFz.text(), "caracteristica": self.cb_caract.currentData(),
            "tamano": self.cb_tamano.currentIndex(), "kvnom": self.ed_kvnom.text(),
            "kvnom_unidad": self.cb_kvnom.currentText(),
            "D1": self.cb_D1.currentText(), "D2": self.cb_D2.currentText(), "C14e": self.ed_c14e.text(),
            "tp": self.ed_tp.text(), "lim_ruido": self.ed_lim_ruido.text(),
            "material": self.cb_material.currentData(), "clase": self.cb_clase.currentIndex(),
            "Pd": self.ed_Pd.text(), "Pd_u": self.cb_Pd.currentText(),
            "Td": self.ed_Td.text(), "Td_u": self.cb_Td.currentText(),
        }

    def _cargar(self, s: dict):
        self.aplicar_sistema(s.get("sistema", "SI"))
        self.cb_servicio.setCurrentIndex(s["servicio"])
        self.cb_fluido.setCurrentText(s["fluido"])
        self.chk_saturado.setChecked(s.get("saturado", False))
        for c, v in zip(self.chk_caso, s["casos_activos"]):
            c.setChecked(v)
        self.cb_estilo.setCurrentIndex(self.cb_estilo.findData(s["estilo"]))
        for k, d in s["filas"].items():
            f = self.filas[k]
            f.unidad.blockSignals(True)
            f.unidad.setCurrentText(d["unidad"])
            f._unidad_ant = d["unidad"]
            f.unidad.blockSignals(False)
            for e, v in zip(f.edits, d["valores"]):
                e.setText(v)
        self.ed_FL.setText(s["FL"]); self.ed_xT.setText(s["xT"]); self.ed_Fd.setText(s["Fd"])
        self.ed_xFz.setText(s["xFz"])
        self.cb_caract.setCurrentIndex(self.cb_caract.findData(s["caracteristica"]))
        self.cb_tamano.setCurrentIndex(s["tamano"])
        self.ed_kvnom.setText(s["kvnom"]); self.cb_kvnom.setCurrentText(s["kvnom_unidad"])
        self.cb_D1.setCurrentText(s["D1"]); self.cb_D2.setCurrentText(s["D2"])
        self.ed_c14e.setText(s["C14e"])
        self.ed_tp.setText(s.get("tp", ""))
        self.ed_lim_ruido.setText(s.get("lim_ruido", "85"))
        self.cb_material.setCurrentIndex(max(0, self.cb_material.findData(s.get("material", "WCB"))))
        self.cb_clase.setCurrentIndex(s.get("clase", 0))
        self.ed_Pd.setText(s.get("Pd", "")); self.cb_Pd.setCurrentText(s.get("Pd_u", "bar g"))
        self.ed_Td.setText(s.get("Td", "")); self.cb_Td.setCurrentText(s.get("Td_u", "°C"))

    def nuevo(self):
        for f in self.filas.values():
            for e in f.edits:
                e.clear()
        self.informe = None
        self.lbl_resumen.setText("Sin cálculo.")

    def guardar(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "", "Proyecto de válvula (*.valvula)")
        if ruta:
            if not ruta.endswith(".valvula"):
                ruta += ".valvula"
            with open(ruta, "w", encoding="utf-8") as fh:
                json.dump(self._estado(), fh, ensure_ascii=False, indent=1)

    def abrir(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", "Proyecto de válvula (*.valvula)")
        if ruta:
            with open(ruta, encoding="utf-8") as fh:
                self._cargar(json.load(fh))

    def informe_html(self) -> str:
        inf = self.informe
        if inf is None:
            return ""
        e = _html.escape
        h = [f"<h1>Informe de dimensionamiento de válvula de control</h1>",
             f"<p>{self.lbl_resumen.text()}</p>",
             f"<p>Servicio: {e(self.cb_servicio.currentText())} · Fluido: {e(self.cb_fluido.currentText())}</p>",
             "<h2>Resultados</h2><table border='1' cellspacing='0' cellpadding='3'>",
             "<tr><th>Magnitud</th><th>Unidad</th>" + "".join(f"<th>{e(rc.caso.nombre)}</th>" for rc in inf.casos) + "</tr>"]
        for _, et, un, vals in self._filas_resultado(inf):
            h.append(f"<tr><td>{e(et)}</td><td>{e(un)}</td>" + "".join(
                f"<td align='right'>{e(v if isinstance(v, str) else fmt(v))}</td>" for v in vals) + "</tr>")
        h.append("</table><h2>Alertas</h2>")
        for caso, a in inf.todas_las_alertas():
            inten = f" — intensidad {a.intensidad:.0f} %" + (f" ({a.nivel})" if a.nivel else "") if a.intensidad is not None else ""
            h.append(f"<h3 style='color:{COLORES[a.severidad]}'>[{NOMBRE_SEV[a.severidad]}] {e(caso)}: {e(a.titulo)}{inten}</h3>"
                     f"<p>{e(a.mensaje)}</p>")
            if a.remedios:
                h.append("<ul>" + "".join(f"<li>{e(r)}</li>" for r in a.remedios) + "</ul>")
        h.append("<h2>Memoria de cálculo</h2>")
        for rc in inf.casos:
            h.append(f"<h3>Caso {e(rc.caso.nombre)}</h3><table border='1' cellspacing='0' cellpadding='3'>"
                     "<tr><th>Símbolo</th><th>Descripción</th><th>Valor</th><th>Unidad</th><th>Fórmula</th><th>Referencia</th></tr>")
            for p in rc.resultado.memoria.pasos:
                h.append(f"<tr><td>{e(p.simbolo)}</td><td>{e(p.descripcion)}</td><td align='right'>{fmt(p.valor, 5)}</td>"
                         f"<td>{e(p.unidad)}</td><td>{e(p.formula)}</td><td>{e(p.referencia)}</td></tr>")
            h.append("</table>")
        h.append("<p><i>Factores de válvula: valores típicos genéricos de IEC 60534-2-1 salvo que se indique "
                 "lo contrario. Verificar con los datos certificados de la válvula ofertada.</i></p>")
        return "<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif'>" + "".join(h) + "</body></html>"

    def exportar_html(self):
        if not self.informe:
            QMessageBox.information(self, "Sin cálculo", "Primero realice un cálculo.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar informe", "informe_valvula.html", "HTML (*.html)")
        if ruta:
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write(self.informe_html())

    def exportar_pdf(self, ruta: str | None = None):
        if not self.informe:
            QMessageBox.information(self, "Sin cálculo", "Primero realice un cálculo.")
            return
        if not ruta:
            ruta, _ = QFileDialog.getSaveFileName(self, "Exportar informe", "informe_valvula.pdf", "PDF (*.pdf)")
        if ruta:
            pdf = QPdfWriter(ruta)
            pdf.setPageSize(QPageSize(QPageSize.A4))
            pdf.setResolution(150)
            doc = QTextDocument()
            doc.setHtml(self.informe_html())
            doc.print_(pdf)

    def acerca(self):
        QMessageBox.about(self, "Acerca de",
                          f"<b>Dimensionador de válvulas de control</b> {__version__}<br><br>"
                          "Cálculo según IEC 60534-2-1 / ANSI/ISA-75.01.01, ruido IEC 60534-8-3 y "
                          "IEC 60534-8-4, cavitación ISA-RP75.23 y API RP 14E.<br>Software independiente de fabricantes de válvulas."
                          "<br><br>Propiedades de fluidos: CoolProp (licencia MIT).")
