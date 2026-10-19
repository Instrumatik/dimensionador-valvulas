"""Solapa 3-Materiales: datos del servicio, agentes químicos y material de cada componente."""
from __future__ import annotations

import html as _html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QTextBrowser, QVBoxLayout, QWidget)

from .. import materiales as MT, quimica as Q, seleccion_materiales as SM
from ..modelos import Severidad

N_AGENTES = 6
SERVICIO = [  # clave de campo, etiqueta, opciones, ayuda, valor inicial
    ("industria", "Industria / proceso", SM.INDUSTRIAS, "mat_industria", "Otra"),
    ("familia_fluido", "Familia de fluido", SM.FAMILIAS_FLUIDO, "mat_familia_fluido", "Agua"),
    ("fluido", "Fluido principal", SM.FLUIDOS, "mat_fluido", "Agua industrial"),
    ("fase", "Fase principal", SM.FASES, "mat_fase", "Líquido"),
    ("composicion", "Estado de la composición", SM.COMPOSICION, "mat_composicion", "Parcialmente conocida"),
    ("acuosa", "Fase acuosa presente", SM.ACUOSA, "mat_acuosa", "Sí"),
    ("regimen", "Régimen operativo", SM.REGIMEN, "mat_regimen", "Continuo"),
    ("medio", "Medio esperado", SM.MEDIO, "mat_medio", "Por evaluar"),
    ("norma_agrio", "Norma de servicio agrio", SM.NORMA_AGRIO, "mat_norma_agrio", "Por determinar"),
    ("solidos", "Sólidos", SM.SOLIDOS, "mat_solidos", "Ausentes confirmados"),
]
AYUDA_COMP = {k: "comp_" + k for k in MT.COMPONENTES}
SIN_AGENTE = "—"
COLOR_SEV = {Severidad.INFO: "#2f6fb0", Severidad.ADVERTENCIA: "#d9771e", Severidad.CRITICA: "#c0392b",
             Severidad.ERROR: "#7d1f9e"}
AVISO_MANUAL = ("Selección MANUAL: no recomendada. La responsabilidad por la aptitud del material queda fuera "
                "del alcance del programa.")


class SolapaMateriales:
    """Mezcla para VentanaPrincipal (usa sus ayudantes _registrar, _fila, abrir_ayuda)."""

    def _tab_materiales(self) -> QWidget:
        from .ventana import ACENTO, AZUL, Combo, boton_ir, titulo_seccion
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("SELECCIÓN DE MATERIALES", AZUL))
        nota = QLabel("Con pocos datos del servicio el programa propone el material de cada componente. Toma "
                      "temperaturas, presión de diseño, rating, cavitación, flashing y caída de presión de las "
                      "solapas 1 y 2. Use «Ver» o F1 para la explicación de cada dato.")
        nota.setWordWrap(True)
        nota.setStyleSheet("color:#55606d;font-style:italic;padding:4px")
        lay.addWidget(nota)

        # ---- servicio
        g = QGroupBox("Servicio y fluido")
        grid = QGridLayout(g)
        self.mat_cb: dict[str, Combo] = {}
        for r, (k, et, ops, ay, ini) in enumerate(SERVICIO):
            cb = self._registrar("mat_" + k, Combo())
            cb.addItems(ops)
            cb.setCurrentText(ini)
            self.mat_cb[k] = cb
            self._fila(grid, r, et, cb, ay, ancho=300)
        r = len(SERVICIO)
        self.mat_lbl_norma = QLabel("")
        self.mat_lbl_norma.setStyleSheet(f"color:{ACENTO};font-size:8pt")
        self.mat_lbl_norma.setWordWrap(True)
        grid.addWidget(self.mat_lbl_norma, SERVICIO.index(next(s for s in SERVICIO if s[0] == "norma_agrio")), 3)
        self.mat_ed_pH = self._registrar("mat_pH", QLineEdit())
        self.mat_ed_pH.setPlaceholderText("opcional")
        self._fila(grid, r, "pH de la fase acuosa", self.mat_ed_pH, "mat_pH", ancho=104)
        grid.setColumnStretch(4, 1)
        self.mat_cb["industria"].currentTextChanged.connect(self._mat_norma_sugerida)
        self._mat_norma_sugerida()
        lay.addWidget(g)

        # ---- agentes
        g = QGroupBox("Agentes químicos (contaminantes o componentes del fluido)")
        grid = QGridLayout(g)
        cab = [("Familia química", "familia_quimica"), ("Agente / especie", "agente"),
               ("Unidad química", "unidad_quimica"), ("Concentración", "concentracion_agente"),
               ("Fase del agente", "fase_agente")]
        for j, (t, ay) in enumerate(cab):
            h = QHBoxLayout()
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(QLabel(f"<b>{t}</b>"))
            h.addWidget(boton_ir(self.abrir_ayuda, ay))
            h.addStretch()
            w = QWidget()
            w.setLayout(h)
            grid.addWidget(w, 0, j + 1)
        self.mat_agentes = []
        for i in range(N_AGENTES):
            grid.addWidget(QLabel(f"{i + 1}"), i + 1, 0)
            fam = self._registrar(f"mat_ag{i}_familia", Combo(), "familia_quimica")
            fam.addItems([SIN_AGENTE] + Q.FAMILIAS)
            ag = self._registrar(f"mat_ag{i}_agente", Combo(), "agente")
            un = self._registrar(f"mat_ag{i}_unidad", Combo(), "unidad_quimica")
            un.addItems(Q.UNIDADES)
            ed = self._registrar(f"mat_ag{i}_conc", QLineEdit(), "concentracion_agente")
            ed.setPlaceholderText("ingresar valor")
            fa = self._registrar(f"mat_ag{i}_fase", Combo(), "fase_agente")
            fa.addItems(Q.FASES)
            fa.setCurrentText("Desconocida")
            ver = QPushButton("Ver agente")
            ver.setStyleSheet("QPushButton{padding:1px 4px;color:#0d3b66;font-size:8pt}")
            ver.setFocusPolicy(Qt.NoFocus)
            ver.setToolTip("Explicación del agente elegido: qué es, dónde aparece, cómo se confirma y sus umbrales")
            fam.setFixedWidth(190)
            ag.setFixedWidth(230)
            un.setFixedWidth(120)
            ed.setFixedWidth(110)
            fa.setFixedWidth(140)
            for j, w in enumerate((fam, ag, un, ed, fa, ver)):
                grid.addWidget(w, i + 1, j + 1)
            fam.currentTextChanged.connect(lambda _=None, i=i: self._mat_cambio_familia(i))
            ag.currentIndexChanged.connect(lambda _=None, i=i: self._mat_cambio_agente(i))
            ver.clicked.connect(lambda _=False, i=i: self._mat_ver_agente(i))
            self.mat_agentes.append((fam, ag, un, ed, fa))
            self._mat_cambio_familia(i)
        grid.setColumnStretch(8, 1)
        lay.addWidget(g)

        # ---- componentes
        g = QGroupBox("Material por componente")
        grid = QGridLayout(g)
        self.mat_comp = {}
        r = 0
        h = QHBoxLayout()
        h.addWidget(QLabel("<b>Modo</b>"))
        h.addWidget(boton_ir(self.abrir_ayuda, "mat_modo"))
        h.addStretch()
        w = QWidget()
        w.setLayout(h)
        grid.addWidget(w, r, 2)
        grid.addWidget(QLabel("<b>Material</b>"), r, 3)
        r += 1
        for k, nombre in MT.COMPONENTES.items():
            lbl = QLabel(nombre)
            lbl.setStyleSheet("font-weight:600")
            modo = self._registrar(f"mat_modo_{k}", Combo(), "mat_modo")
            modo.addItems(SM.MODOS)
            modo.setFixedWidth(130)
            sel = self._registrar(f"mat_sel_{k}", Combo(), AYUDA_COMP[k])
            for m in MT.para_componente(k):
                if not m.blando:
                    sel.addItem(m.nombre, m.clave)
            sel.setFixedWidth(430)
            sel.setEnabled(False)
            an = QPushButton("Análisis…")
            an.setToolTip("Ver el análisis y la justificación de la recomendación")
            an.clicked.connect(lambda _=False, k=k: self._mat_analisis(k))
            rec = QLabel("Recomendación: se calcula con «Calcular».")
            rec.setWordWrap(True)
            rec.setStyleSheet("color:#2f6fb0;font-size:8pt;padding-bottom:4px")
            grid.addWidget(lbl, r, 0)
            grid.addWidget(boton_ir(self.abrir_ayuda, AYUDA_COMP[k]), r, 1)
            grid.addWidget(modo, r, 2)
            grid.addWidget(sel, r, 3)
            grid.addWidget(an, r, 4)
            grid.addWidget(rec, r + 1, 3, 1, 3)
            modo.currentTextChanged.connect(lambda _=None, k=k: self._mat_cambio_modo(k))
            self.mat_comp[k] = (lbl, modo, sel, an, rec)
            r += 2
        grid.setColumnStretch(5, 1)
        lay.addWidget(g)

        h = QHBoxLayout()
        b = QPushButton("Calcular")
        b.setStyleSheet("QPushButton{background:#f5b700;color:#0d3b66;font-weight:800;padding:5px 16px}")
        b.clicked.connect(self.calcular)
        bl = QPushButton("Biblioteca de materiales…")
        bl.setProperty("ayuda", "mat_biblioteca")
        bl.clicked.connect(self.biblioteca_materiales)
        h.addWidget(b)
        h.addWidget(bl)
        h.addWidget(boton_ir(self.abrir_ayuda, "mat_biblioteca"))
        h.addStretch()
        lay.addLayout(h)

        lay.addWidget(titulo_seccion("ANÁLISIS DE MATERIALES", ACENTO))
        self.mat_resumen = QTextBrowser()
        self.mat_resumen.setOpenLinks(False)
        self.mat_resumen.anchorClicked.connect(lambda u: self.abrir_ayuda(u.toString()[6:]))
        self.mat_resumen.setMinimumHeight(420)
        self.mat_resumen.setHtml("<p style='color:#55606d'>Todavía no hay cálculo.</p>")
        lay.addWidget(self.mat_resumen)
        return self._scroll(cont)

    # ------------------------------------------------------------ eventos
    def _mat_norma_sugerida(self):
        ind = self.mat_cb["industria"].currentText()
        n, motivo = SM._norma(SM.ServicioMateriales(industria=ind), True)
        self.mat_lbl_norma.setText(f"Recomendada si hay H₂S: {n}")
        self.mat_lbl_norma.setToolTip(motivo)

    def _mat_cambio_familia(self, i):
        fam, ag, un, ed, fa = self.mat_agentes[i]
        actual = ag.currentData()
        ag.blockSignals(True)
        ag.clear()
        f = fam.currentText()
        if f == SIN_AGENTE:
            ag.addItem(SIN_AGENTE, None)
        else:
            for a in Q.por_familia(f):
                ag.addItem(f"{a.formula} — {a.nombre}" if a.formula != "—" else a.nombre, a.clave)
        j = ag.findData(actual)
        ag.setCurrentIndex(max(0, j))
        ag.blockSignals(False)
        for w in (ag, un, ed, fa):
            w.setEnabled(f != SIN_AGENTE)
        self._mat_cambio_agente(i, sugerir=j < 0)

    def _mat_cambio_agente(self, i, sugerir=True):
        fam, ag, un, ed, fa = self.mat_agentes[i]
        clave = ag.currentData()
        if clave and sugerir:
            a = Q.AGENTES[clave]
            un.setCurrentText(a.unidad_sugerida)
            if a.base == "kPa" and fa.currentText() == "Desconocida":
                fa.setCurrentText("Gas / vapor")
            elif a.base != "kPa" and fa.currentText() == "Desconocida":
                fa.setCurrentText("Acuosa")
        if clave:
            ed.setPlaceholderText(f"en {un.currentText()}")

    def _mat_ver_agente(self, i):
        clave = self.mat_agentes[i][1].currentData()
        self.abrir_ayuda("agente_" + clave if clave else "agente")

    def _mat_cambio_modo(self, k):
        lbl, modo, sel, an, rec = self.mat_comp[k]
        manual = modo.currentText() == "MANUAL"
        sel.setEnabled(manual)
        sel.setStyleSheet("QComboBox{border:2px solid #c0392b}" if manual else "")
        if manual:
            rec.setStyleSheet("color:#c0392b;font-size:8pt;padding-bottom:4px")
            self.statusBar().showMessage(AVISO_MANUAL)
        else:
            rec.setStyleSheet("color:#2f6fb0;font-size:8pt;padding-bottom:4px")
        if hasattr(self, "res") and self.res is not None and self.res.materiales is not None:
            self._mat_texto_recomendacion(k)

    def _mat_nombres_componentes(self):
        if not hasattr(self, "mat_comp"):
            return
        rot = self.cuerpo().rotativa
        nombres = MT.COMPONENTES_ROTATIVA if rot else MT.COMPONENTES
        k = self.cb_trim.currentData() or ""
        jaula = "jaula" in k or "multietapa" in k
        for c, (lbl, modo, sel, an, rec) in self.mat_comp.items():
            lbl.setText(nombres[c])
            aplica = (c != "jaula" or jaula) and (c != "guia" or not jaula)
            for w in (modo, sel, an):
                w.setEnabled(aplica if w is not sel else aplica and modo.currentText() == "MANUAL")
            if not aplica:
                rec.setText("No aplica con el trim elegido" + (" (sin jaula)." if c == "jaula" else
                                                               " (el obturador se guía en la jaula)."))

    def _mat_nuevo(self):
        for k, et, ops, ay, ini in SERVICIO:
            self.mat_cb[k].setCurrentText(ini)
        self.mat_ed_pH.clear()
        for fam, ag, un, ed, fa in self.mat_agentes:
            fam.setCurrentText(SIN_AGENTE)
            ed.clear()
            fa.setCurrentText("Desconocida")
        for lbl, modo, sel, an, rec in self.mat_comp.values():
            modo.setCurrentText("AUTOMÁTICO")
            rec.setText("Recomendación: se calcula con «Calcular».")
        self.mat_resumen.setHtml("<p style='color:#55606d'>Todavía no hay cálculo.</p>")

    def _mat_estado(self) -> dict:
        """Estado de la solapa para guardar el proyecto."""
        return {"servicio": {k: cb.currentText() for k, cb in self.mat_cb.items()},
                "pH": self.mat_ed_pH.text(),
                "agentes": [{"familia": fam.currentText(), "agente": ag.currentData(), "unidad": un.currentText(),
                             "concentracion": ed.text(), "fase": fa.currentText()}
                            for fam, ag, un, ed, fa in self.mat_agentes],
                "componentes": {k: {"modo": c[1].currentText(), "material": c[2].currentData()}
                                for k, c in self.mat_comp.items()}}

    def _mat_cargar(self, d: dict):
        self._mat_nuevo()
        for k, v in d.get("servicio", {}).items():
            cb = self.mat_cb.get(k)
            if cb is not None and cb.findText(v) >= 0:
                cb.setCurrentText(v)
        self.mat_ed_pH.setText(d.get("pH", ""))
        for (fam, ag, un, ed, fa), x in zip(self.mat_agentes, d.get("agentes", [])):
            if fam.findText(x.get("familia", "")) < 0:
                continue
            fam.setCurrentText(x["familia"])
            j = ag.findData(x.get("agente"))
            if j >= 0:
                ag.setCurrentIndex(j)
            if un.findText(x.get("unidad", "")) >= 0:
                un.setCurrentText(x["unidad"])
            if fa.findText(x.get("fase", "")) >= 0:
                fa.setCurrentText(x["fase"])
            ed.setText(x.get("concentracion", ""))
        for k, x in d.get("componentes", {}).items():
            c = self.mat_comp.get(k)
            if c is None:
                continue
            j = c[2].findData(x.get("material"))
            if j >= 0:
                c[2].setCurrentIndex(j)
            c[1].setCurrentText(x.get("modo", "AUTOMÁTICO"))
        self._mat_nombres_componentes()

    # ------------------------------------------------------------ lectura
    def _servicio_materiales(self) -> SM.ServicioMateriales:
        from .ventana import leer_numero
        v = {k: cb.currentText() for k, cb in self.mat_cb.items()}
        agentes = []
        for i, (fam, ag, un, ed, fa) in enumerate(self.mat_agentes):
            if fam.currentText() == SIN_AGENTE or not ag.currentData():
                continue
            txt = ed.text().strip()
            c = leer_numero(txt) if txt else None
            if txt and c is None:
                raise ValueError(f"Agente {i + 1}: la concentración «{txt}» no es un número.")
            agentes.append(Q.AgenteServicio(ag.currentData(), un.currentText(), c, fa.currentText()))
        pH_t = self.mat_ed_pH.text().strip()
        pH = leer_numero(pH_t) if pH_t else None
        if pH_t and (pH is None or not 0 <= pH <= 14):
            raise ValueError("El pH debe ser un número entre 0 y 14.")
        modos = {k: c[1].currentText() for k, c in self.mat_comp.items()}
        manual = {k: c[2].currentData() for k, c in self.mat_comp.items() if c[1].currentText() == "MANUAL"}
        return SM.ServicioMateriales(pH=pH, agentes=agentes, modos=modos, manual=manual, **v)

    # ------------------------------------------------------------ resultados
    def _mat_texto_recomendacion(self, k):
        m = self.res.materiales
        rc = m.componentes[k]
        lbl, modo, sel, an, rec = self.mat_comp[k]
        if not rc.aplica:
            rec.setText("No aplica: " + (rc.justificacion[0] if rc.justificacion else "no corresponde a este trim."))
            return
        r = rc.recomendado
        t = f"Recomendado: <b>{_html.escape(r.nombre)}</b>" if r else "<b>Sin material apto en la biblioteca</b>"
        if rc.dureza_req_HRC:
            t += f" · dureza mínima {rc.dureza_req_HRC:.0f} HRC"
        if k == "asiento" and rc.inserto:
            t += f" · inserto blando {_html.escape(rc.inserto.nombre.split(' (')[0])}"
        if modo.currentText() == "MANUAL":
            t += "<br><span style='color:#c0392b'>" + _html.escape(AVISO_MANUAL) + "</span>"
            al = [a for a in rc.alertas if a.codigo == "mat_incompatible"]
            if al:
                t += "<br><span style='color:#c0392b'><b>No apto:</b> " + _html.escape(al[0].mensaje[:300]) + "</span>"
        rec.setText(t)

    def _mostrar_materiales(self):
        m = self.res.materiales if self.res is not None else None
        if m is None:
            return
        for k, (lbl, modo, sel, an, rec) in self.mat_comp.items():
            rc = m.componentes[k]
            lbl.setText(rc.nombre)
            aplica = rc.aplica
            modo.setEnabled(aplica)
            an.setEnabled(aplica)
            if modo.currentText() != "MANUAL" and rc.elegido:
                i = sel.findData(rc.elegido.clave)
                if i >= 0:
                    sel.setCurrentIndex(i)
            sel.setEnabled(aplica and modo.currentText() == "MANUAL")
            self._mat_texto_recomendacion(k)
        self.mat_resumen.setHtml(html_resumen(m))

    def _mat_analisis(self, k):
        if self.res is None or self.res.materiales is None:
            self.calcular()
            if self.res is None or self.res.materiales is None:
                return
        rc = self.res.materiales.componentes[k]
        d = QDialog(self)
        d.setWindowTitle(f"Análisis de material — {rc.nombre}")
        d.resize(900, 700)
        v = QVBoxLayout(d)
        t = QTextBrowser()
        t.setOpenLinks(False)
        t.anchorClicked.connect(lambda u: self.abrir_ayuda(u.toString()[6:]))
        t.setHtml(html_componente(self.res.materiales, k))
        v.addWidget(t)
        b = QPushButton("Cerrar")
        b.clicked.connect(d.accept)
        v.addWidget(b, 0, Qt.AlignRight)
        d.exec()

    def biblioteca_materiales(self):
        d = QDialog(self)
        d.setWindowTitle("Biblioteca de materiales")
        d.resize(1150, 740)
        h = QHBoxLayout(d)
        izq = QVBoxLayout()
        buscar = QLineEdit(placeholderText="Buscar por nombre, UNS, ASTM o familia…")
        lista = QListWidget()
        izq.addWidget(buscar)
        izq.addWidget(lista)
        w = QWidget()
        w.setLayout(izq)
        w.setMaximumWidth(420)
        texto = QTextBrowser()
        h.addWidget(w)
        h.addWidget(texto, 1)

        def llenar(f=""):
            lista.clear()
            for mm in sorted(MT.buscar(f), key=lambda x: (x.familia, x.nombre)):
                it = QListWidgetItem(mm.nombre)
                it.setData(Qt.UserRole, mm.clave)
                lista.addItem(it)
        buscar.textChanged.connect(llenar)
        lista.currentItemChanged.connect(
            lambda it, _: it and texto.setHtml(html_ficha(MT.MATERIALES[it.data(Qt.UserRole)])))
        llenar()
        lista.setCurrentRow(0)
        d.exec()


# ---------------------------------------------------------------------------
# HTML de resultados
# ---------------------------------------------------------------------------
def _e(t) -> str:
    return _html.escape(str(t))


def html_ficha(m: MT.Material) -> str:
    filas = "".join(f"<tr><td bgcolor='#eef2f6' width='32%'><b>{_e(a)}</b></td><td>{_e(b)}</td></tr>"
                    for a, b in MT.ficha(m))
    return (f"<h2 style='color:#3d5a80'>{_e(m.nombre)}</h2>"
            f"<table width='100%' cellspacing='0' cellpadding='4' border='1' style='border-collapse:collapse'>"
            f"{filas}</table><p style='color:#55606d;font-size:8pt'>Valores típicos u orientativos. La aptitud final "
            "requiere el certificado del material (MTR) y la confirmación del fabricante.</p>")


def _alertas_html(alertas) -> str:
    if not alertas:
        return "<p>Sin alertas de materiales.</p>"
    out = []
    for a in alertas:
        c = COLOR_SEV[a.severidad]
        rem = "".join(f"<li>{_e(r)}</li>" for r in a.remedios)
        out.append(f"<p style='margin:4px 0'><b style='color:{c}'>{_e(a.titulo)}</b> — {_e(a.mensaje)}"
                   f" <a href='ayuda:{a.codigo}'>(ayuda)</a></p>" + (f"<ul style='margin:0'>{rem}</ul>" if rem else ""))
    return "".join(out)


def html_resumen(m: SM.ResultadoMateriales) -> str:
    ctx = m.ctx
    p = [f"<p><b>Temperatura</b> {ctx.T_min_C:.0f} a {ctx.T_max_C:.0f} °C · <b>Presión de diseño</b> "
         f"{ctx.P_barg:.1f} bar g · <b>Rating</b> CL{ctx.clase} · <b>Cavitación</b> {ctx.severidad_cav}"
         + (" · <b>flashing</b>" if ctx.flashing else "") + f" · <b>ΔP máx.</b> {ctx.dP_max_kPa / 100:.1f} bar</p>",
         f"<p><b>Medio detectado:</b> {_e(m.medio_detectado)} (<a href='ayuda:mat_medio'>ayuda</a>) · "
         f"<b>Servicio agrio:</b> {'sí' if m.agrio else 'no'}"
         + (f" (pH₂S = {m.pH2S_kPa:.2f} kPa)" if m.pH2S_kPa is not None else "")
         + f" · <b>Norma:</b> {_e(m.norma)} — {_e(m.norma_motivo)}</p>",
         f"<p><b>Dureza de internos:</b> {_e(m.dureza_motivo)} (<a href='ayuda:cavitacion_dureza'>ayuda</a>)</p>"]
    filas = "".join(f"<tr><td><b>{_e(c.nombre)}</b></td><td>{_e(c.modo)}</td><td>{_e(c.texto)}</td>"
                    f"<td>{_e(c.elegido.dureza_txt) if c.elegido else '—'}</td></tr>"
                    for c in m.componentes.values())
    p.append("<table width='100%' cellspacing='0' cellpadding='4' border='1' style='border-collapse:collapse'>"
             "<tr bgcolor='#dde5ee'><th>Componente</th><th>Modo</th><th>Material</th><th>Dureza</th></tr>"
             f"{filas}</table>")
    if m.galling:
        g = "".join(f"<tr><td>{_e(x.par)}</td><td>{_e(x.a)} / {_e(x.b)}</td><td>{_e(x.nivel)}</td>"
                    f"<td>{_e(x.motivo)}</td></tr>" for x in m.galling)
        p.append("<h4>Parejas en contacto (galling) <a href='ayuda:galling'>(ayuda)</a></h4>"
                 "<table width='100%' cellspacing='0' cellpadding='4' border='1' style='border-collapse:collapse'>"
                 "<tr bgcolor='#dde5ee'><th>Pareja</th><th>Materiales</th><th>Riesgo</th><th>Motivo</th></tr>"
                 f"{g}</table>")
    if m.mecanismos:
        g = "".join(f"<tr><td>{_e(x.codigo)}</td><td>{_e(x.nombre)}</td><td>{_e(x.estado)}</td>"
                    f"<td>{_e(x.motivo)}</td></tr>" for x in m.mecanismos)
        p.append("<h4>Mecanismos de deterioro <a href='ayuda:mecanismos_falla'>(ayuda)</a></h4>"
                 "<table width='100%' cellspacing='0' cellpadding='4' border='1' style='border-collapse:collapse'>"
                 "<tr bgcolor='#dde5ee'><th>ID</th><th>Mecanismo</th><th>Estado</th><th>Motivo</th></tr>"
                 f"{g}</table>")
    if m.agentes:
        g = "".join(f"<tr><td>{_e(n.agente.formula)} — {_e(n.agente.nombre)}</td><td>{_e(n.texto())}</td>"
                    f"<td>{_e(' '.join(n.notas))}</td></tr>" for n in m.agentes)
        p.append("<h4>Agentes evaluados</h4><table width='100%' cellspacing='0' cellpadding='4' border='1' "
                 "style='border-collapse:collapse'><tr bgcolor='#dde5ee'><th>Agente</th><th>Valor normalizado</th>"
                 f"<th>Nota</th></tr>{g}</table>")
    for n in m.notas:
        p.append(f"<p style='color:#55606d'>• {_e(n)}</p>")
    p.append("<h4>Alertas</h4>" + _alertas_html(m.todas_las_alertas()))
    p.append("<p style='color:#55606d;font-size:8pt'>Preselección de ingeniería: no reemplaza la aprobación del "
             "fabricante ni del especialista en corrosión del proyecto.</p>")
    return "".join(p)


def html_componente(m: SM.ResultadoMateriales, k: str) -> str:
    rc = m.componentes[k]
    p = [f"<h2 style='color:#3d5a80'>{_e(rc.nombre)}</h2>"]
    if not rc.aplica:
        return "".join(p) + "<p>No aplica con el trim elegido.</p>"
    p.append(f"<p><b>Modo:</b> {_e(rc.modo)} · <b>Recomendado:</b> "
             f"{_e(rc.recomendado.nombre) if rc.recomendado else 'sin material apto'} · <b>Elegido:</b> "
             f"{_e(rc.texto)}</p>")
    if rc.modo == "MANUAL":
        p.append(f"<p style='color:#c0392b'><b>{_e(AVISO_MANUAL)}</b></p>")
    p.append("<h4>Justificación</h4><ul>" + "".join(f"<li>{_e(x.strip(' ·'))}</li>" for x in rc.justificacion) + "</ul>")
    if rc.alternativas:
        p.append("<h4>Alternativas aptas</h4><ul>" + "".join(f"<li>{_e(a.nombre)} — {_e(b)}</li>"
                                                            for a, b in rc.alternativas) + "</ul>")
    if rc.descartados:
        vistos = set()
        items = []
        for a, b in rc.descartados:
            if a.clave in vistos:
                continue
            vistos.add(a.clave)
            items.append(f"<li><b>{_e(a.nombre)}</b>: {_e(b)}</li>")
        p.append("<h4>Materiales descartados y motivo</h4><ul>" + "".join(items[:25]) + "</ul>")
    gall = [g for g in m.galling if rc.elegido and rc.elegido.clave in (g.a, g.b)]
    if gall:
        p.append("<h4>Galling con las piezas en contacto</h4><ul>" + "".join(
            f"<li>{_e(g.par)}: <b>{_e(g.nivel)}</b> — {_e(g.motivo)} {_e(g.remedio)}</li>" for g in gall) + "</ul>")
    p.append("<h4>Alertas del componente</h4>" + _alertas_html(rc.alertas))
    if rc.elegido:
        p.append(html_ficha(rc.elegido))
    return "".join(p)
