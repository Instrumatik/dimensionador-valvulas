"""Solapas 4-Actuador, 5-Posicionador y 6-Accesorios: datos simples, cálculo completo en ``actuadores``."""
from __future__ import annotations

import html as _html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QTextBrowser,
                               QVBoxLayout, QWidget)

from .. import actuadores as A
from . import botones
from ..estilos import ESTILOS
from ..modelos import Severidad

SI_NO = ["Sí", "No"]
COLOR_SEV = {Severidad.INFO: "#2f6fb0", Severidad.ADVERTENCIA: "#d9771e", Severidad.CRITICA: "#c0392b",
             Severidad.ERROR: "#7d1f9e"}
NOTA = "color:#55606d;font-style:italic;padding:4px"


def _bloquear_items(cb, bloqueadas: dict, dejar_actual=False):
    """Deja visibles todas las opciones pero deshabilita las bloqueadas, con el motivo como ayuda emergente."""
    m = cb.model()
    for i in range(cb.count()):
        s = cb.itemText(i)
        it = m.item(i)
        if it is None:
            continue
        it.setEnabled(s not in bloqueadas or (dejar_actual and s == cb.currentText()))
        cb.setItemData(i, f"Bloqueada: {bloqueadas[s]}." if s in bloqueadas else "", Qt.ToolTipRole)


def _vista() -> QTextBrowser:
    v = QTextBrowser()
    v.setOpenExternalLinks(False)
    v.setMinimumHeight(260)
    v.setStyleSheet("QTextBrowser{background:white;border:1px solid #c9d3de}")
    return v


def _tabla(filas, cab=None) -> str:
    h = "<table cellspacing=0 cellpadding=4 style='border-collapse:collapse;width:100%'>"
    if cab:
        h += "<tr>" + "".join(f"<th style='background:#dde5ee;text-align:left'>{_html.escape(c)}</th>"
                              for c in cab) + "</tr>"
    for i, f in enumerate(filas):
        fondo = "#f6f8fa" if i % 2 else "white"
        h += f"<tr style='background:{fondo}'>" + "".join(
            f"<td style='border-bottom:1px solid #e3e8ee'>{'<b>' if j == 0 else ''}{_html.escape(str(c))}"
            f"{'</b>' if j == 0 else ''}</td>" for j, c in enumerate(f)) + "</tr>"
    return h + "</table>"


def _alertas(alertas) -> str:
    if not alertas:
        return "<p style='color:#2e7d32'><b>Sin alertas.</b></p>"
    h = ""
    for a in sorted(alertas, key=lambda a: -a.severidad):
        h += (f"<p style='margin:4px 0'><b style='color:{COLOR_SEV[a.severidad]}'>{_html.escape(a.titulo)}</b><br>"
              f"{_html.escape(a.mensaje)}</p>")
        if a.remedios:
            h += "<ul style='margin-top:0'>" + "".join(f"<li>{_html.escape(r)}</li>" for r in a.remedios) + "</ul>"
    return h


class SolapaEquipo:
    """Mezcla para VentanaPrincipal (usa _registrar, _fila, abrir_ayuda y calcular)."""

    def _grupo(self, titulo, filas, ancho=300) -> QGroupBox:
        from .ventana import Combo
        g = QGroupBox(titulo)
        grid = QGridLayout(g)
        for r, (nombre, et, ops, ayuda, ini) in enumerate(filas):
            if ops is None:
                w = self._registrar(nombre, QLineEdit())
                w.setPlaceholderText(ini or "")
            else:
                w = self._registrar(nombre, Combo())
                w.addItems(ops)
                w.setCurrentText(ini)
            self._fila(grid, r, et, w, ayuda, ancho=ancho)
            self.eq_w[nombre] = w
        grid.setColumnStretch(4, 1)
        return g

    def _boton_calcular(self, lay):
        h = QHBoxLayout()
        b = QPushButton("Calcular")
        botones.calcular(b, "amarillo", "5px 18px")
        b.clicked.connect(lambda: self.calcular())
        h.addWidget(b)
        h.addStretch()
        lay.addLayout(h)

    # ------------------------------------------------------------------ 4-Actuador
    def _tab_actuador(self) -> QWidget:
        from .ventana import AZUL, FilaUnidad, titulo_seccion
        self.eq_w = {}
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("DIMENSIONAMIENTO DEL ACTUADOR", AZUL))
        nota = QLabel("Presiones de cierre, ΔP con caudal, clase de cierre, puerto, carrera, balanceo, empaquetadura y "
                      "temperatura se toman de las solapas 1, 2 y 3. Aquí solo se elige el actuador y se carga el aire "
                      "de instrumentos disponible. El programa calcula fuerzas o pares, resorte, ajuste de banco, "
                      "presión de aire requerida, carga del vástago y estabilidad.")
        nota.setWordWrap(True)
        nota.setStyleSheet(NOTA)
        lay.addWidget(nota)
        g = self._grupo("Actuador", [
            ("act_modo", "Modo", A.MODOS_ACT, "act_modo", "AUTOMÁTICO"),
            ("act_tipo", "Tipo", A.TIPOS, "act_tipo", A.TIPOS[0]),
            ("act_falla", "Modo de falla", A.FALLAS, "act_falla", A.FC),
            ("act_volante", "Volante", SI_NO, "act_volante", "No"),
            ("act_flujo", "Flow (sentido del flujo)", A.FLUJOS, "act_flujo", "Up"),
            ("act_rango", "Operating Range (rango de operación)", A.RANGOS_LISTA, "ext_rango", A.RANGO_AUTO),
        ])
        grid = g.layout()
        r = grid.rowCount()
        grid.addWidget(QLabel("<b>Mín.</b>"), r, 3)
        grid.addWidget(QLabel("<b>Máx.</b>"), r, 4)
        self.f_aire = FilaUnidad("aire_instrumentos", "Aire de instrumentos disponible", ("presion",), grid, r + 1,
                                 self.abrir_ayuda, n=2, ayuda_clave="act_aire")
        self.f_vastago = FilaUnidad("d_vastago", "Diámetro del vástago", ("longitud",), grid, r + 2, self.abrir_ayuda,
                                    n=1, ayuda_clave="act_vastago")
        self.f_vastago.edits[0].setPlaceholderText("estimado")
        self.f_friccion = FilaUnidad("friccion_cert", "Fricción certificada de la empaquetadura", ("fuerza",), grid,
                                     r + 3, self.abrir_ayuda, n=1, ayuda_clave="act_friccion_cert")
        self.f_friccion.edits[0].setPlaceholderText("estimada")
        self.f_rango = FilaUnidad("rango_pa_pb", "Pa / Pb del rango (Optimized)", ("presion",), grid, r + 4,
                                  self.abrir_ayuda, n=2, ayuda_clave="ext_rango")
        self.f_rango.elegir("psig", False)
        self.f_rango.edits[0].setPlaceholderText("Pa")
        self.f_rango.edits[1].setPlaceholderText("Pb")
        self.eq_w["act_rango"].currentTextChanged.connect(self._act_rango_visible)
        self.f_friccion.edits[0].setToolTip("En blanco: fricción típica de la empaquetadura de 3-Materiales. Con dato, "
                                            "reemplaza el término C de la fuerza (válvulas de vástago deslizante).")
        self.lbl_act_tipo = QLabel("")
        self.lbl_act_tipo.setWordWrap(True)
        self.lbl_act_tipo.setStyleSheet("color:#2f6fb0;font-size:8pt")
        grid.addWidget(self.lbl_act_tipo, 1, 3, 1, 3)
        lay.addWidget(g)
        # Datos certificados (modo MANUAL): solo se muestran los que pide el tipo de actuador
        self.g_cert = QGroupBox("Datos certificados del actuador (modo MANUAL: fabricante o cliente)")
        gc = QGridLayout(self.g_cert)
        gc.addWidget(QLabel("<b>Dato</b>"), 0, 0)
        gc.addWidget(QLabel("<b>Unidad</b>"), 0, 2)
        self.f_cert = {}
        for i, (k, et, mags, n, cab) in enumerate((
                ("cert_area_in2", "Área efectiva", ("area",), 1, ""),
                ("cert_banco_psig", "Ajuste de banco (bench set)", ("presion",), 2, "Inferior / superior"),
                ("cert_carrera_in", "Carrera nominal del actuador", ("longitud",), 1, ""),
                ("cert_pmax_psig", "Presión máxima del actuador", ("presion",), 1, ""),
                ("cert_par_aire_lbfin", "Par de aire (doble efecto)", ("par",), 1, ""),
                ("cert_p_par_psig", "Presión a la que se da el par de aire", ("presion",), 1, ""),
                ("cert_par_resorte_lbfin", "Par del resorte", ("par",), 2, "Comienzo / final"),
                ("cert_nominal", "Empuje o par nominal", ("fuerza", "par"), 1, ""))):
            f = FilaUnidad(k, et, mags, gc, i + 1, self.abrir_ayuda, n=n, ayuda_clave="act_certificado")
            nota_c = QLabel(cab)
            nota_c.setStyleSheet("color:#555")
            gc.addWidget(nota_c, i + 1, 5)
            f.extra = [nota_c]
            self.f_cert[k] = f
        self.f_cert["cert_banco_psig"].elegir("psig", False)
        self.f_cert["cert_pmax_psig"].elegir("psig", False)
        self.f_cert["cert_p_par_psig"].elegir("psig", False)
        gc.setColumnStretch(6, 1)
        lay.addWidget(self.g_cert)
        for k in ("act_modo", "act_tipo", "act_falla"):
            self.eq_w[k].currentTextChanged.connect(self._act_cert_visibles)
        self.eq_w["act_tipo"].currentTextChanged.connect(self._act_cambio_tipo)
        self._boton_calcular(lay)
        self.vista_act = _vista()
        lay.addWidget(self.vista_act, 1)
        self._seccion_externa(lay)
        self._act_cambio_tipo()
        self._act_cert_visibles()
        self._act_rango_visible()
        return self._scroll(cont)

    def _act_rango_visible(self, *_):
        opt = self.eq_w["act_rango"].currentText() == A.RANGO_OPT
        for w in self.f_rango.widgets():
            w.setVisible(opt)

    def _act_rango(self) -> dict:
        """rango y rango_nombre para A.DatosActuador (Pa y Pb en psig)."""
        op = self.eq_w["act_rango"].currentText()
        pa_pb = None
        if op == A.RANGO_OPT:
            vals = [self.f_rango.valor_base(j) for j in (0, 1)]
            if any(v is None for v in vals):
                raise ValueError("Operating Range «Optimized»: cargue Pa y Pb.")
            pa_pb = tuple((v - 101.325) / A.PSI_KPA for v in vals)
            if pa_pb[0] < 0 or pa_pb[1] <= pa_pb[0]:
                raise ValueError("Operating Range «Optimized»: Pb debe ser mayor que Pa y Pa no negativa (psig).")
        rango, nombre = A.rango_elegido(op, pa_pb)
        return {"rango": rango, "rango_nombre": nombre}

    # ---------------------------------------------- datos para verificación con software de fabricante
    def _seccion_externa(self, lay):
        self.bt_ext = QPushButton("▸ Datos para verificación con software de fabricante")
        self.bt_ext.setCheckable(True)
        self.bt_ext.setStyleSheet("QPushButton{text-align:left;border:none;color:#1f4e79;font-weight:bold;padding:4px}")
        self.bt_ext.setToolTip("Los datos de las solapas 1, 2 y 3 en el formato que piden las herramientas de "
                               "actuadores de los fabricantes, y la comparación con lo que devuelven.")
        lay.addWidget(self.bt_ext)
        self.g_ext = QWidget()
        le = QVBoxLayout(self.g_ext)
        le.setContentsMargins(0, 0, 0, 0)
        nota = QLabel("Cargue estos datos en la herramienta de actuadores del fabricante, en el mismo orden y "
                      "unidades. Haga clic en una fila para ver qué es el dato y cómo lo obtuvo N25.")
        nota.setWordWrap(True)
        nota.setStyleSheet(NOTA)
        le.addWidget(nota)
        self.tb_ext = QTableWidget(0, 4)
        self.tb_ext.setHorizontalHeaderLabels(["Campo", "Valor", "Unidad", "Dato y cómo lo obtuvo N25"])
        self.tb_ext.verticalHeader().setVisible(False)
        self.tb_ext.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tb_ext.setSelectionBehavior(QAbstractItemView.SelectRows)
        hh = self.tb_ext.horizontalHeader()
        for c in range(3):
            hh.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        hh.setStretchLastSection(True)
        self.tb_ext.setMinimumHeight(260)
        self.tb_ext.setProperty("ayuda", "ext_verificacion")
        self.tb_ext.cellClicked.connect(self._ext_ayuda)
        le.addWidget(self.tb_ext)
        h = QHBoxLayout()
        self.bt_ext_copiar = QPushButton("Copiar datos")
        self.bt_ext_copiar.setToolTip("Copia campo, valor y unidad, separados por tabulaciones.")
        self.bt_ext_copiar.clicked.connect(self._ext_copiar)
        h.addWidget(self.bt_ext_copiar)
        b = QPushButton("Ver guía")
        b.clicked.connect(lambda: self.abrir_ayuda("guia_verificacion_externa"))
        h.addWidget(b)
        h.addStretch()
        le.addLayout(h)
        gc = QGroupBox("Comparar con lo que devuelve el software del fabricante")
        grid = QGridLayout(gc)
        self.ed_ext = {}
        for i, (k, et, ph) in enumerate((("area", "Área efectiva [in²]", ""),
                                         ("banco_inf", "Ajuste de banco inferior [psig]", ""),
                                         ("banco_sup", "Ajuste de banco superior [psig]", ""),
                                         ("empuje", "Fuerza requerida por la válvula [lbf]", "sin margen"))):
            grid.addWidget(QLabel(et), i, 0)
            e = QLineEdit()
            e.setPlaceholderText(ph)
            e.setFixedWidth(110)
            e.setProperty("ayuda", "ext_comparacion")
            grid.addWidget(e, i, 1)
            self.ed_ext[k] = e
        bc = QPushButton("Comparar")
        bc.clicked.connect(self._ext_comparar)
        grid.addWidget(bc, 4, 1)
        grid.setColumnStretch(2, 1)
        le.addWidget(gc)
        self.vista_ext = _vista()
        self.vista_ext.setMinimumHeight(140)
        le.addWidget(self.vista_ext)
        self.g_ext.setVisible(False)
        lay.addWidget(self.g_ext)
        self.bt_ext.toggled.connect(self._ext_mostrar)

    def _ext_mostrar(self, on: bool):
        self.g_ext.setVisible(on)
        self.bt_ext.setText(("▾ " if on else "▸ ") + "Datos para verificación con software de fabricante")

    def _ext_filas(self) -> list:
        eq = getattr(self.res, "equipo", None) if self.res is not None else None
        return eq.actuador.externos if eq is not None else []

    def _ext_llenar(self):
        filas = self._ext_filas()
        self.tb_ext.setRowCount(len(filas))
        for i, (campo, nombre, valor, unidad, _clave, origen) in enumerate(filas):
            for j, t in enumerate((campo, valor, unidad, f"{nombre}: {origen}")):
                it = QTableWidgetItem(t)
                if j == 1:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tb_ext.setItem(i, j, it)
        self.tb_ext.resizeRowsToContents()
        if not filas:
            self.vista_ext.setHtml("<p style='color:#55606d'>Solo para válvulas de vástago deslizante; se completa "
                                   "con «Calcular».</p>")
        else:
            self.vista_ext.clear()

    def _ext_ayuda(self, fila: int, _col: int = 0):
        filas = self._ext_filas()
        if 0 <= fila < len(filas):
            self.abrir_ayuda(filas[fila][4])

    def _ext_copiar(self):
        txt = "\n".join(f"{c}\t{v}\t{u}" for c, _n, v, u, _k, _o in self._ext_filas())
        QApplication.clipboard().setText(txt)

    def _ext_comparar(self):
        eq = getattr(self.res, "equipo", None) if self.res is not None else None
        if eq is None or not eq.actuador.terminos:
            self.vista_ext.setHtml("<p style='color:#c0392b'>Primero calcule una válvula de vástago deslizante.</p>")
            return
        val = {}
        for k, e in self.ed_ext.items():
            t = e.text().strip().replace(",", ".")
            try:
                val[k] = float(t) if t else None
            except ValueError:
                self.vista_ext.setHtml(f"<p style='color:#c0392b'>Valor no numérico: {_html.escape(e.text())}</p>")
                return
        banco = (val["banco_inf"], val["banco_sup"]) if None not in (val["banco_inf"], val["banco_sup"]) else None
        filas = A.comparar_externo(eq.actuador, val["area"], banco, val["empuje"])
        if not filas:
            self.vista_ext.setHtml("<p style='color:#55606d'>Cargue al menos el área efectiva o la fuerza requerida "
                                   "que informa el software del fabricante.</p>")
            return
        self.vista_ext.setHtml(_tabla(filas, ["Dato", "N25", "Fabricante", "Diferencia", "Lectura"]))

    def _act_cert_visibles(self, *_):
        """En MANUAL muestra los datos certificados que necesita el tipo de actuador elegido."""
        if not hasattr(self, "g_cert"):
            return
        manual = self.eq_w["act_modo"].currentText() == "MANUAL"
        self.g_cert.setVisible(manual)
        rot = self.cuerpo().rotativa if hasattr(self, "cb_cuerpo") and self.cb_cuerpo.currentData() else False
        pide = A.datos_certificados(self.eq_w["act_tipo"].currentText(), self.eq_w["act_falla"].currentText(), rot)
        for k, f in self.f_cert.items():
            for w in f.widgets() + f.extra:
                w.setVisible(manual and k in pide)
        for w in self.f_friccion.widgets():
            w.setEnabled(not rot)
        f = self.f_cert["cert_nominal"]
        if f.magnitud() != ("par" if rot else "fuerza"):
            from .. import unidades as U
            f.elegir(U.SISTEMAS[getattr(self, "sistema", "SI")]["par" if rot else "fuerza"], False)

    def _act_cert_datos(self) -> dict:
        """Datos certificados en unidades inglesas para A.DatosActuador (solo los del tipo elegido)."""
        if self.eq_w["act_modo"].currentText() != "MANUAL":
            return {}
        rot = self.cuerpo().rotativa
        pide = A.datos_certificados(self.eq_w["act_tipo"].currentText(), self.eq_w["act_falla"].currentText(), rot)
        conv = {"area": lambda v: v / 25.4 ** 2, "presion": lambda v: (v - 101.325) / A.PSI_KPA,
                "longitud": lambda v: v / 25.4, "fuerza": lambda v: v / A.LBF_N, "par": lambda v: v / A.LBFIN_NM}
        out = {"modo": "MANUAL"}
        for k in pide:
            f = self.f_cert[k]
            vals = [f.valor_base(j) for j in range(len(f.edits))]
            if any(v is None for v in vals):
                out[k] = None
                continue
            vals = [conv[f.magnitud()](v) for v in vals]
            if any(v <= 0 for v in vals) and k != "cert_banco_psig":
                raise ValueError(f"«{f.lbl.text()}» debe ser mayor que cero.")
            out[k] = tuple(vals) if len(vals) > 1 else vals[0]
        f = self.f_cert["cert_nominal"]
        if "cert_nominal" in pide and out.get("cert_nominal") is not None and (f.magnitud() == "par") != rot:
            raise ValueError("Empuje o par nominal: use una unidad de fuerza en válvulas lineales y de par en "
                             "rotativas.")
        return out

    def _act_cambio_tipo(self, *_):
        t = self.eq_w["act_tipo"].currentText()
        neum = t not in ("Eléctrico", "Electrohidráulico", "Manual")
        for e in self.f_aire.edits:
            e.setEnabled(neum)
        self.f_aire.unidad.setEnabled(neum)
        txt = {"Diafragma y resorte": "Simple efecto, resorte de falla; hasta unos 3,4 bar en la carcasa.",
               "Multiresorte y diafragma": "Varios resortes cortos: compacto, admite hasta unos 6 bar.",
               "Pistón doble acción con resorte": "Aire a ambos lados y resorte que lleva a la falla.",
               "Pistón doble acción sin resorte": "Gran empuje; la falla requiere tanque y válvula de cambio.",
               "Pistón retorno por resorte": "Aire de un lado, resorte del otro; hasta unos 10 bar.",
               "Eléctrico": "Queda en la última posición si no lleva módulo de falla segura.",
               "Electrohidráulico": "Gran empuje o par con falla por resorte hidráulico.",
               "Piñón y cremallera (Rack and pinion)": "Cuarto de vuelta, par constante en todo el recorrido.",
               "Yugo escocés": "Cuarto de vuelta, par máximo en los extremos (arranque y asiento).",
               "Manual": "Volante o reductor; sin posición de falla."}[t]
        self.lbl_act_tipo.setText(txt)

    # ------------------------------------------------------------- 5-Posicionador
    def _tab_posicionador(self) -> QWidget:
        from .ventana import AZUL, titulo_seccion
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("POSICIONADOR", AZUL))
        nota = QLabel("Las señales que no alcanzan la presión que necesita el actuador, o que no corresponden al tipo "
                      "de posicionador, quedan bloqueadas después de «Calcular» y el motivo se muestra al pasar el "
                      "mouse sobre ellas.")
        nota.setWordWrap(True)
        nota.setStyleSheet(NOTA)
        lay.addWidget(nota)
        lay.addWidget(self._grupo("Posicionador", [
            ("pos_tag", "Tag", None, "pos_tag", "p. ej. ZY-101"),
            ("pos_tipo", "Tipo", A.TIPOS_POS, "pos_tipo", "Digital-HART"),
            ("pos_senal", "Señal de entrada", A.SENALES, "pos_senal", "4-20mA dc"),
            ("pos_accion", "Acción", A.ACCIONES_POS, "pos_accion", "Configurable"),
            ("pos_manometros", "Manómetros", SI_NO, "pos_manometros", "Sí"),
            ("pos_set", "Set de aire de instrumentos", SI_NO, "pos_set", "Sí"),
            ("pos_salida_set", "Salida set de aire", A.SALIDAS_SET, "pos_set", "Ajustable 0-80 psi"),
        ]))
        self.eq_w["pos_tipo"].currentTextChanged.connect(self._pos_cambio_tipo)
        self.eq_w["pos_set"].currentTextChanged.connect(
            lambda t: self.eq_w["pos_salida_set"].setEnabled(t == "Sí"))
        self._boton_calcular(lay)
        self.vista_pos = _vista()
        lay.addWidget(self.vista_pos, 1)
        return self._scroll(cont)

    def _pos_cambio_tipo(self, *_):
        """Al cambiar el tipo, pasa a una señal de su familia si la elegida no corresponde."""
        tipo = self.eq_w["pos_tipo"].currentText()
        fam = A._familia_senal(tipo)
        cb = self.eq_w["pos_senal"]
        if cb.currentText() not in fam:
            cb.setCurrentText(fam[0])
        if tipo not in ("Neumático", "Electroneumático") and self.eq_w["pos_accion"].currentText() != "Doble":
            self.eq_w["pos_accion"].setCurrentText("Configurable")

    def _pos_bloquear(self, bloqueadas: dict):
        _bloquear_items(self.eq_w["pos_senal"], bloqueadas, dejar_actual=True)

    def _act_concordancia(self):
        """Bloquea los actuadores y las opciones de Flow que no corresponden a la válvula de 1-Sistema."""
        if not hasattr(self, "eq_w") or not hasattr(self, "cb_cuerpo") or self.cb_cuerpo.currentData() is None:
            return
        c = self.cuerpo()
        tipo, flujo = self.eq_w["act_tipo"], self.eq_w["act_flujo"]
        _bloquear_items(tipo, A.tipos_bloqueados(c.rotativa))
        if tipo.currentText() in A.tipos_bloqueados(c.rotativa):
            tipo.setCurrentText("Piñón y cremallera (Rack and pinion)" if c.rotativa else A.TIPOS[0])
        _bloquear_items(flujo, A.flujos_bloqueados(c.clave, c.rotativa))
        if flujo.currentText() in A.flujos_bloqueados(c.clave, c.rotativa):
            if c.rotativa:
                flujo.setCurrentText("Unidireccional")
            else:
                self._act_flujo_desde_trim(self.trim_clave())
        if not c.rotativa:   # en vástago ascendente el sentido se elige una sola vez, en la solapa 2
            self._act_flujo_desde_trim(self.trim_clave())
        flujo.setEnabled(c.rotativa)
        flujo.setToolTip("Unidireccional o bidireccional según el cierre de la válvula rotativa." if c.rotativa else
                         "Se toma de «Sentido de flujo» de la solapa 2 (Up: tiende a abrir; Down: tiende a cerrar).")
        self._act_cert_visibles()

    # -------------------------------------------------------------- 6-Accesorios
    def _tab_accesorios(self) -> QWidget:
        from .ventana import AZUL, titulo_seccion
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("ACCESORIOS", AZUL))
        nota = QLabel("Las celdas de texto que quedan vacías no aparecen en los documentos entregables. Elija «No "
                      "requerido» en solenoide o límites de carrera si la válvula no los lleva.")
        nota.setWordWrap(True)
        nota.setStyleSheet(NOTA)
        lay.addWidget(nota)
        lay.addWidget(self._grupo("Accesorios neumáticos", [
            ("acc_boosters", "Boosters", None, "acc_boosters", "vacío = no se incluye"),
            ("acc_quick_exhaust", "Quick Exhaust", None, "acc_quick_exhaust", "vacío = no se incluye"),
            ("acc_bloqueo", "Válvulas de bloqueo neumático", None, "acc_bloqueo", "vacío = no se incluye"),
            ("acc_cambio", "Válvula de cambio (switching valve)", None, "acc_cambio", "vacío = no se incluye"),
        ], ancho=420))
        lay.addWidget(self._grupo("Válvulas solenoides", [
            ("acc_sol_accion", "Tipo de acción", [A.NO_APLICA] + A.ACCION_SOL, "acc_solenoide", A.NO_APLICA),
            ("acc_sol_vias", "Tipo de cambio (pasajes)", A.VIAS_SOL, "acc_solenoide", "3 vías"),
            ("acc_sol_material", "Material", A.MATERIAL_SOL, "acc_solenoide", "Acero Inoxidable"),
            ("acc_sol_puerto", "Tamaño de puertos", A.PUERTOS_SOL, "acc_solenoide", '1/4"'),
            ("acc_sol_voltaje", "Voltaje", A.VOLTAJES_SOL, "acc_solenoide", "24 Vdc"),
            ("acc_sol_potencia", "Potencia", None, "acc_solenoide", "vacío = no se incluye"),
        ]))
        lay.addWidget(self._grupo("Límites de carrera", [
            ("acc_lim_tipo", "Tipo", [A.NO_APLICA] + A.TIPOS_LIM, "acc_limites", A.NO_APLICA),
            ("acc_lim_contactos", "Contactos", A.CONTACTOS_LIM, "acc_limites", "SPDT"),
            ("acc_lim_voltaje", "Voltaje", None, "acc_limites", "vacío = no se incluye"),
            ("acc_lim_corriente", "Corriente", None, "acc_limites", "vacío = no se incluye"),
            ("acc_lim_frecuencia", "Frecuencia", A.FRECUENCIAS, "acc_limites", "50/60Hz"),
        ]))
        for k, hijos in (("acc_sol_accion", ("acc_sol_vias", "acc_sol_material", "acc_sol_puerto", "acc_sol_voltaje",
                                             "acc_sol_potencia")),
                         ("acc_lim_tipo", ("acc_lim_contactos", "acc_lim_voltaje", "acc_lim_corriente",
                                           "acc_lim_frecuencia"))):
            self.eq_w[k].currentTextChanged.connect(
                lambda t, hijos=hijos: [self.eq_w[h].setEnabled(t != A.NO_APLICA) for h in hijos])
            for h in hijos:
                self.eq_w[h].setEnabled(False)
        self._boton_calcular(lay)
        self.vista_acc = _vista()
        lay.addWidget(self.vista_acc, 1)
        return self._scroll(cont)

    # ------------------------------------------------------------------ datos
    def _equipo_datos(self) -> A.Equipo:
        w = self.eq_w
        t = lambda k: w[k].currentText() if hasattr(w[k], "currentText") else w[k].text().strip()  # noqa: E731
        pa = [self.f_aire.valor_base(j) for j in (0, 1)]
        pa = [None if v is None else v - 101.325 for v in pa]
        if pa[0] is not None and pa[0] <= 0 and t("act_tipo") not in ("Eléctrico", "Electrohidráulico", "Manual"):
            raise ValueError("El aire de instrumentos mínimo debe ser mayor que cero (presión manométrica).")
        dv = self.f_vastago.valor_base(0)
        if dv is not None and dv <= 0:
            raise ValueError("El diámetro del vástago debe ser mayor que cero.")
        fr = self.f_friccion.valor_base(0)
        if fr is not None and fr <= 0:
            raise ValueError("La fricción certificada de la empaquetadura debe ser mayor que cero.")
        act = A.DatosActuador(t("act_tipo"), t("act_falla"), t("act_volante") == "Sí", pa[0], pa[1],
                              t("act_flujo"), dv, friccion_cert_lbf=None if fr is None else fr / A.LBF_N,
                              **self._act_cert_datos(), **self._act_rango())
        pos = A.DatosPosicionador(t("pos_tag"), t("pos_tipo"), t("pos_senal"), t("pos_accion"),
                                  t("pos_manometros") == "Sí", t("pos_set") == "Sí", t("pos_salida_set"))
        acc = A.DatosAccesorios(t("acc_boosters"), t("acc_quick_exhaust"), t("acc_bloqueo"), t("acc_cambio"),
                                t("acc_sol_accion"), t("acc_sol_vias"), t("acc_sol_material"), t("acc_sol_puerto"),
                                t("acc_sol_voltaje"), t("acc_sol_potencia"), t("acc_lim_tipo"),
                                t("acc_lim_contactos"), t("acc_lim_voltaje"), t("acc_lim_corriente"),
                                t("acc_lim_frecuencia"))
        return A.Equipo(act, pos, acc)

    def _act_flujo_desde_trim(self, trim: str):
        if hasattr(self, "eq_w") and "act_flujo" in self.eq_w and trim and not ESTILOS[trim].familia == "rotativa":
            from ..estilos import geometria_sentido
            self.eq_w["act_flujo"].setCurrentText("Down" if geometria_sentido(trim)[1] == "cierra" else "Up")

    def _eq_aire_inicial(self):
        """Aire de instrumentos típico de planta (4 a 7 bar g) para que el primer cálculo tenga resultado."""
        for j, v in enumerate((4.0, 7.0)):
            self.f_aire.poner_base(j, v * 100 + 101.325)

    def _eq_nuevo(self):
        defaults = {"act_modo": "AUTOMÁTICO", "act_tipo": A.TIPOS[0], "act_falla": A.FC, "act_volante": "No", "pos_tipo": "Digital-HART",
                    "pos_senal": "4-20mA dc", "pos_accion": "Configurable", "pos_manometros": "Sí", "pos_set": "Sí",
                    "pos_salida_set": "Ajustable 0-80 psi", "acc_sol_accion": A.NO_APLICA, "acc_sol_vias": "3 vías",
                    "acc_sol_material": "Acero Inoxidable", "acc_sol_puerto": '1/4"', "acc_sol_voltaje": "24 Vdc",
                    "acc_lim_tipo": A.NO_APLICA, "acc_lim_contactos": "SPDT", "acc_lim_frecuencia": "50/60Hz"}
        for k, w in self.eq_w.items():
            if k in defaults:
                w.setCurrentText(defaults[k])
            elif isinstance(w, QLineEdit):
                w.clear()
        self.f_vastago.edits[0].clear()
        self.f_friccion.edits[0].clear()
        for e in self.f_rango.edits:
            e.clear()
        for f in self.f_cert.values():
            for e in f.edits:
                e.clear()
        self._eq_aire_inicial()
        self._pos_bloquear({})
        self._act_concordancia()
        for v in (self.vista_act, self.vista_pos, self.vista_acc):
            v.setHtml("<p style='color:#55606d'>Se calcula con «Calcular».</p>")
        self.tb_ext.setRowCount(0)
        for e in self.ed_ext.values():
            e.clear()
        self.vista_ext.clear()

    # --------------------------------------------------------------- mostrar
    def _mostrar_equipo(self):
        eq = getattr(self.res, "equipo", None) if self.res is not None else None
        if eq is None:
            for v in (self.vista_act, self.vista_pos, self.vista_acc):
                v.setHtml("<p style='color:#55606d'>Se calcula con «Calcular».</p>")
            self._ext_llenar()
            return
        ra, rp, rc = eq.actuador, eq.posicionador, eq.accesorios
        color = "#2e7d32" if ra.ok else "#c0392b"
        h = (f"<h3 style='color:{color};margin:2px 0'>{'Actuador apto' if ra.ok else 'El actuador NO cumple'}: "
             f"{_html.escape(ra.seleccion or '—')}</h3>")
        if ra.fuerzas:
            h += "<h4>" + ("Pares de la válvula" if ra.rotativa else "Fuerzas de la válvula (A + B + C + D)") + "</h4>"
            h += _tabla(ra.fuerzas, ["Componente", "Valor", "Fórmula / base"])
        h += "<h4>Resultados</h4>" + _tabla([(f, v) for f, v, _ in ra.filas], ["Parámetro", "Valor"])
        if ra.pasos:
            h += "<h4>Memoria del cálculo</h4>" + _tabla(ra.pasos, ["Paso", "Ecuación", "Resultado"])
        h += "<h4>Alertas del actuador</h4>" + _alertas(ra.alertas)
        h += ("<p style='color:#55606d;font-size:8pt'>Tamaños de series genéricas (no corresponden a ningún "
              "fabricante). El fabricante confirma modelo, resorte y ajuste de banco.</p>")
        self.vista_act.setHtml(h)
        self._ext_llenar()
        self._pos_bloquear(rp.bloqueadas)
        hp = "<h4>Posicionador</h4>" + _tabla([(f, v) for f, v, _ in rp.filas], ["Dato", "Valor"])
        hp += (f"<p>Acción sugerida: <b>{_html.escape(rp.accion_sugerida)}</b> · Set de aire sugerido: "
               f"<b>{_html.escape(rp.set_sugerido)}</b>"
               + (f" · Presión requerida por el actuador: <b>{A._psi(ra.P_req_psig)}</b>"
                  if ra.P_req_psig is not None else "") + "</p>")
        if rp.bloqueadas:
            hp += "<h4>Señales bloqueadas</h4><ul>" + "".join(
                f"<li><b>{_html.escape(s)}</b>: {_html.escape(m)}.</li>" for s, m in rp.bloqueadas.items()) + "</ul>"
        hp += "<h4>Alertas del posicionador</h4>" + _alertas(rp.alertas)
        self.vista_pos.setHtml(hp)
        ha = "<h4>Accesorios que se incluyen en los documentos</h4>"
        ha += _tabla([(f, v) for f, v, _ in rc.filas], ["Accesorio", "Especificación"]) if rc.filas else \
            "<p>Ninguno.</p>"
        ha += "<h4>Alertas de accesorios</h4>" + _alertas(rc.alertas)
        self.vista_acc.setHtml(ha)
