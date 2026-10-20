"""Solapa 3-Materiales: datos del servicio, agentes químicos y material de cada componente."""
from __future__ import annotations

import html as _html

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QPushButton, QTextBrowser, QVBoxLayout, QWidget)

from .. import empaquetaduras as EM, juegos_trim as JT, materiales as MT, quimica as Q, seleccion_materiales as SM
from ..modelos import Severidad

N_AGENTES = 6
SERVICIO = [  # clave de campo, etiqueta, opciones, ayuda, valor inicial
    ("industria", "Industria / proceso", SM.INDUSTRIAS, "mat_industria", "Otra"),
    ("composicion", "Estado de la composición", SM.COMPOSICION, "mat_composicion", "Parcialmente conocida"),
    ("regimen", "Régimen operativo", SM.REGIMEN, "mat_regimen", "Continuo"),
    ("medio", "Medio esperado", SM.MEDIO, "mat_medio", "Por evaluar"),
    ("norma_agrio", "Norma de servicio agrio", SM.NORMA_AGRIO, "mat_norma_agrio", "Por determinar"),
    ("solidos", "Sólidos", SM.SOLIDOS, "mat_solidos", "Ausentes confirmados"),
]
AYUDA_COMP = {k: "comp_" + k for k in MT.COMPONENTES}
SIN_AGENTE = "—"
COLOR_SEV = {Severidad.INFO: "#2f6fb0", Severidad.ADVERTENCIA: "#d9771e", Severidad.CRITICA: "#c0392b",
             Severidad.ERROR: "#7d1f9e"}
POR_COMPONENTE = "Por componente (modo de cada pieza)"
AVISO_MANUAL = ("Selección MANUAL: no recomendada. La responsabilidad por la aptitud del material queda fuera "
                "del alcance del programa.")


class SolapaMateriales:
    """Mezcla para VentanaPrincipal (usa sus ayudantes _registrar, _fila, abrir_ayuda)."""

    def _tab_materiales(self) -> QWidget:
        from .ventana import ACENTO, AZUL, Combo, boton_ir, titulo_seccion
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.addWidget(titulo_seccion("SELECCIÓN DE MATERIALES", AZUL))
        nota = QLabel("El fluido se define una sola vez, en 2-Cálculos Válvula. Aquí se agregan solo los datos "
                      "complementarios para elegir materiales (industria, agentes químicos, sólidos, pH, norma de "
                      "servicio agrio). Temperaturas, presiones, cavitación y flashing se toman del cálculo. Use "
                      "«Ver» o F1 para la explicación de cada dato.")
        nota.setWordWrap(True)
        nota.setStyleSheet("color:#55606d;font-style:italic;padding:4px")
        lay.addWidget(nota)

        # ---- fluido heredado de la solapa 2
        g = QGroupBox("Fluido (definido en 2-Cálculos Válvula)")
        h = QHBoxLayout(g)
        self.mat_lbl_fluido = QLabel("")
        self.mat_lbl_fluido.setWordWrap(True)
        self.mat_lbl_fluido.setTextFormat(Qt.RichText)
        self.mat_lbl_fluido.setStyleSheet("background:#eef2f6;border:1px solid #c9d3de;padding:6px")
        h.addWidget(self.mat_lbl_fluido, 1)
        h.addWidget(boton_ir(self.abrir_ayuda, "mat_fluido_heredado"))
        ir = QPushButton("Cambiar en 2-Cálculos Válvula")
        ir.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        h.addWidget(ir)
        lay.addWidget(g)

        # ---- servicio
        g = QGroupBox("Datos complementarios del servicio")
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
        self.mat_lbl_pH_nota = QLabel("")
        self.mat_lbl_pH_nota.setStyleSheet(f"color:{ACENTO};font-size:8pt")
        grid.addWidget(self.mat_lbl_pH_nota, r, 3)
        self.mat_lbl_solidos = QLabel("")
        self.mat_lbl_solidos.setStyleSheet(f"color:{ACENTO};font-size:8pt")
        grid.addWidget(self.mat_lbl_solidos, [x[0] for x in SERVICIO].index("solidos"), 3)
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
            # los cloruros informados corrigen las propiedades de las aguas salinas (solapa 2)
            ag.currentIndexChanged.connect(lambda *_: self._cambio_variante())
            ed.editingFinished.connect(self._cambio_variante)
            un.currentIndexChanged.connect(lambda *_: self._cambio_variante())
            un.currentIndexChanged.connect(lambda _=None, i=i: self._mat_guia_unidad(i))
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
        lbl = QLabel("Juego de internos")
        lbl.setStyleSheet("font-weight:600")
        self.mat_juego = self._registrar("mat_juego", Combo(), "juego_trim")
        self.mat_juego.addItem(POR_COMPONENTE, "")
        for j in JT.JUEGOS.values():
            self.mat_juego.addItem(j.texto, j.clave)
        self.mat_juego.setFixedWidth(560)
        self.mat_juego.setToolTip("Elija un juego estándar para fijar asiento, jaula y obturador juntos; el programa "
                                  "verifica su aptitud. «Por componente» deja que cada pieza use su modo.")
        self.mat_lbl_juego = QLabel("Juego estándar: se calcula con «Calcular».")
        self.mat_lbl_juego.setWordWrap(True)
        self.mat_lbl_juego.setStyleSheet("color:#2f6fb0;font-size:8pt;padding-bottom:4px")
        grid.addWidget(lbl, r, 0)
        grid.addWidget(boton_ir(self.abrir_ayuda, "juego_trim"), r, 1)
        grid.addWidget(self.mat_juego, r, 2, 1, 3)
        grid.addWidget(self.mat_lbl_juego, r + 1, 2, 1, 4)
        self.mat_juego.currentIndexChanged.connect(self._mat_cambio_juego)
        r += 2
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

        # ---- empaquetadura y bonete
        g = QGroupBox("Empaquetadura y bonete")
        grid = QGridLayout(g)
        lbl = QLabel("Empaquetadura del vástago")
        lbl.setStyleSheet("font-weight:600")
        modo = self._registrar("mat_modo_empaquetadura", Combo(), "mat_modo")
        modo.addItems(SM.MODOS)
        modo.setFixedWidth(130)
        sel = self._registrar("mat_sel_empaquetadura", Combo(), "empaquetadura")
        for e in EM.EMPAQUETADURAS.values():
            sel.addItem(e.nombre, e.clave)
        sel.setFixedWidth(430)
        sel.setEnabled(False)
        an = QPushButton("Análisis…")
        an.setToolTip("Ver la justificación de la empaquetadura y del bonete")
        an.clicked.connect(self._emp_analisis)
        rec = QLabel("Recomendación: se calcula con «Calcular».")
        rec.setWordWrap(True)
        rec.setStyleSheet("color:#2f6fb0;font-size:8pt;padding-bottom:4px")
        grid.addWidget(lbl, 0, 0)
        grid.addWidget(boton_ir(self.abrir_ayuda, "empaquetadura"), 0, 1)
        grid.addWidget(modo, 0, 2)
        grid.addWidget(sel, 0, 3)
        grid.addWidget(an, 0, 4)
        grid.addWidget(rec, 1, 3, 1, 3)
        self.mat_lbl_bonete = QLabel("Bonete: se calcula con «Calcular».")
        self.mat_lbl_bonete.setWordWrap(True)
        lb = QLabel("Tipo de bonete")
        lb.setStyleSheet("font-weight:600")
        grid.addWidget(lb, 2, 0)
        grid.addWidget(boton_ir(self.abrir_ayuda, "tipo_bonete"), 2, 1)
        grid.addWidget(self.mat_lbl_bonete, 2, 2, 1, 4)
        grid.setColumnStretch(5, 1)
        modo.currentTextChanged.connect(self._emp_cambio_modo)
        self.mat_emp = (lbl, modo, sel, an, rec)
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
    def _mat_fluido_heredado(self):
        """Muestra lo que la solapa 2 define del fluido y bloquea los datos que de él dependen."""
        if not hasattr(self, "mat_lbl_fluido"):
            return
        from .. import fluido_servicio as FS
        t, fl, var = self.tipo(), self._fluido_actual(), self.cb_variante.currentText()
        agua = self.cb_agua_libre.currentText()
        salidas = self.res.salidas if self.res is not None and self.res.dim.tipo == t else None
        fm = FS.para_materiales(t, None if fl == FS.USUARIO else fl, var,
                                FS.agua_libre_sugerida(t, fl, var) if agua == FS.AUTO_AGUA else agua, salidas,
                                bool(self.res and self.res.materiales and self.res.materiales.ctx.flashing))
        partes = [f"<b>{_html.escape(fm.descripcion)}</b>", f"Tipo: {_html.escape(self.cb_tipo_fluido.currentText())}",
                  f"Familia: {_html.escape(fm.familia)}", f"Fase: {_html.escape(fm.fase)}",
                  f"Agua libre: {_html.escape(fm.acuosa)}"]
        if self.res is not None and self.res.materiales is not None:
            c = self.res.materiales.ctx
            partes += [f"T {c.T_min_C:.0f} a {c.T_max_C:.0f} °C", f"P diseño {c.P_barg:.1f} bar g".replace(".", ","),
                       f"cavitación {c.severidad_cav}" + (" · flashing" if c.flashing else "")]
        self.mat_lbl_fluido.setText(" · ".join(partes))
        seco = fm.acuosa == "No"
        self.mat_ed_pH.setEnabled(not seco)
        self.mat_lbl_pH_nota.setText("Sin agua libre: el pH no se usa." if seco else "")
        sol = self.mat_cb["solidos"]
        if fm.familia == "Slurry":
            sol.setCurrentText("Presentes")
            sol.setEnabled(False)
            self.mat_lbl_solidos.setText("Slurry: sólidos presentes (lo define el fluido).")
        else:
            sol.setEnabled(True)
            self.mat_lbl_solidos.setText("")

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
        self._mat_guia_unidad(i)

    def _mat_guia_unidad(self, i):
        fam, ag, un, ed, fa = self.mat_agentes[i]
        if ag.currentData():
            ed.setPlaceholderText(f"en {un.currentText()}")

    def _mat_cambio_juego(self, *_):
        clave = self.mat_juego.currentData()
        for k in ("asiento", "jaula", "obturador"):
            lbl, modo, sel, an, rec = self.mat_comp[k]
            modo.setEnabled(not clave)
            if clave:
                j = sel.findData(JT.JUEGOS[clave].piezas()[k])
                if j >= 0:
                    sel.setCurrentIndex(j)
                sel.setEnabled(False)
        if not clave:
            self._mat_nombres_componentes()

    def _mat_texto_juego(self):
        m = self.res.materiales
        if not m.juegos:
            self.mat_lbl_juego.setText("No aplica a válvulas rotativas (el programa no usa juegos de internos en "
                                       "bola, mariposa ni tapón excéntrico).")
            return
        aptos = [v.juego.clave for v in sorted(m.juegos, key=lambda v: v.puntaje) if v.ok]
        t = f"<b>{_html.escape(m.juego_texto)}</b>"
        if m.juego_usuario and m.juego and not m.juego.ok:
            t += ("<br><span style='color:#c0392b'><b>No apto:</b> "
                  + _html.escape(" ".join(m.juego.motivos)[:300]) + "</span>")
        t += "<br>Juegos estándar aptos: " + (", ".join(aptos) if aptos else "ninguno")
        self.mat_lbl_juego.setText(t)

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

    def _emp_cambio_modo(self, *_):
        lbl, modo, sel, an, rec = self.mat_emp
        manual = modo.currentText() == "MANUAL"
        sel.setEnabled(manual)
        sel.setStyleSheet("QComboBox{border:2px solid #c0392b}" if manual else "")
        rec.setStyleSheet(f"color:{'#c0392b' if manual else '#2f6fb0'};font-size:8pt;padding-bottom:4px")
        if manual:
            self.statusBar().showMessage(AVISO_MANUAL)
        if getattr(self, "res", None) is not None and self.res.materiales is not None:
            self._emp_texto()

    def _emp_texto(self):
        e = self.res.materiales.empaquetadura
        lbl, modo, sel, an, rec = self.mat_emp
        if e is None:
            return
        t = (f"Recomendada: <b>{_html.escape(e.recomendada.nombre)}</b> · emisión requerida {_html.escape(e.emision_req)}"
             if e.recomendada else "<b>Sin empaquetadura apta en la biblioteca</b>")
        if e.elegida is not None:
            t += (f"<br>Tipo: {_html.escape(e.elegida.tipo)} · carga viva: {'sí' if e.elegida.carga_viva else 'no'} · "
                  f"{_html.escape(e.elegida.guia_temperatura)}")
        if modo.currentText() == "MANUAL":
            t += "<br><span style='color:#c0392b'>" + _html.escape(AVISO_MANUAL) + "</span>"
            al = [a for a in e.alertas if a.codigo == "empaque_incompatible"]
            if al:
                t += "<br><span style='color:#c0392b'><b>No apta:</b> " + _html.escape(al[0].mensaje[:300]) + "</span>"
        rec.setText(t)
        self.mat_lbl_bonete.setText(f"<b>{_html.escape(e.bonete)}</b><br><span style='color:#55606d;font-size:8pt'>"
                                    f"{_html.escape(e.bonete_motivo)}</span>")

    def _emp_analisis(self):
        if self.res is None or self.res.materiales is None:
            self.calcular()
            if self.res is None or self.res.materiales is None:
                return
        d = QDialog(self)
        d.setWindowTitle("Análisis de empaquetadura y bonete")
        d.resize(900, 700)
        v = QVBoxLayout(d)
        t = QTextBrowser()
        t.setOpenLinks(False)
        t.anchorClicked.connect(lambda u: self.abrir_ayuda(u.toString()[6:]))
        t.setHtml(html_empaquetadura(self.res.materiales.empaquetadura))
        v.addWidget(t)
        b = QPushButton("Cerrar")
        b.clicked.connect(d.accept)
        v.addWidget(b, 0, Qt.AlignRight)
        d.exec()

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
            fijo = bool(self.mat_juego.currentData()) and c in ("asiento", "jaula", "obturador")
            for w in (modo, sel, an):
                w.setEnabled(aplica if w is not sel else aplica and modo.currentText() == "MANUAL" and not fijo)
            if fijo:
                modo.setEnabled(False)
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
        for lbl, modo, sel, an, rec in list(self.mat_comp.values()) + [self.mat_emp]:
            modo.setCurrentText("AUTOMÁTICO")
            rec.setText("Recomendación: se calcula con «Calcular».")
        self.mat_lbl_bonete.setText("Bonete: se calcula con «Calcular».")
        self.mat_juego.setCurrentIndex(0)
        self.mat_lbl_juego.setText("Juego estándar: se calcula con «Calcular».")
        self.mat_resumen.setHtml("<p style='color:#55606d'>Todavía no hay cálculo.</p>")

    def _mat_estado(self) -> dict:
        """Estado de la solapa para guardar el proyecto."""
        return {"servicio": {k: cb.currentText() for k, cb in self.mat_cb.items()},
                "pH": self.mat_ed_pH.text(),
                "agentes": [{"familia": fam.currentText(), "agente": ag.currentData(), "unidad": un.currentText(),
                             "concentracion": ed.text(), "fase": fa.currentText()}
                            for fam, ag, un, ed, fa in self.mat_agentes],
                "componentes": {k: {"modo": c[1].currentText(), "material": c[2].currentData()}
                                for k, c in self.mat_comp.items()},
                "empaquetadura": {"modo": self.mat_emp[1].currentText(), "clave": self.mat_emp[2].currentData()},
                "juego_trim": self.mat_juego.currentData() or ""}

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
        x = d.get("empaquetadura", {})
        j = self.mat_emp[2].findData(x.get("clave"))
        if j >= 0:
            self.mat_emp[2].setCurrentIndex(j)
        self.mat_emp[1].setCurrentText(x.get("modo", "AUTOMÁTICO"))
        self._mat_nombres_componentes()
        j = self.mat_juego.findData(d.get("juego_trim", ""))
        self.mat_juego.setCurrentIndex(max(0, j))
        self._mat_cambio_juego()

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
        modos["empaquetadura"] = self.mat_emp[1].currentText()
        if modos["empaquetadura"] == "MANUAL":
            manual["empaquetadura"] = self.mat_emp[2].currentData()
        return SM.ServicioMateriales(pH=pH, agentes=agentes, modos=modos, manual=manual,
                                     juego_trim=self.mat_juego.currentData() or "", **v)

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
            fijo = bool(self.mat_juego.currentData()) and k in ("asiento", "jaula", "obturador")
            if (modo.currentText() != "MANUAL" or fijo) and rc.elegido:
                i = sel.findData(rc.elegido.clave)
                if i >= 0:
                    sel.setCurrentIndex(i)
            sel.setEnabled(aplica and modo.currentText() == "MANUAL" and not fijo)
            if fijo:
                modo.setEnabled(False)
            self._mat_texto_recomendacion(k)
        e = m.empaquetadura
        if e is not None and e.elegida is not None and self.mat_emp[1].currentText() != "MANUAL":
            i = self.mat_emp[2].findData(e.elegida.clave)
            if i >= 0:
                self.mat_emp[2].setCurrentIndex(i)
        self._emp_texto()
        self._mat_texto_juego()
        self.mat_resumen.setHtml(html_resumen(m))
        self._mat_fluido_heredado()

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
    sv = m.servicio
    p = [f"<p><b>Fluido</b> (solapa 2): {_e(sv.fluido)} · familia {_e(sv.familia_fluido)} · fase {_e(sv.fase)} · "
         f"agua libre {_e(sv.acuosa)}</p>",
         f"<p><b>Temperatura</b> {ctx.T_min_C:.0f} a {ctx.T_max_C:.0f} °C · <b>Presión de diseño</b> "
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
    if m.juegos:
        aptos = [v.juego.texto for v in sorted(m.juegos, key=lambda v: v.puntaje) if v.ok]
        p.append(f"<p><b>Juego de internos</b> (<a href='ayuda:juego_trim'>ayuda</a>): {_e(m.juego_texto)}"
                 + (f". {_e(m.juego.juego.aplicacion)}" if m.juego and m.juego.juego.aplicacion else "")
                 + "<br><span style='color:#55606d'>Aptos para este servicio: "
                 + (_e("; ".join(aptos)) if aptos else "ninguno") + "</span></p>")
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
    e = m.empaquetadura
    if e is not None:
        p.append("<h4>Empaquetadura y bonete <a href='ayuda:empaquetadura'>(ayuda)</a></h4>"
                 f"<p><b>Empaquetadura:</b> {_e(e.texto)} ({_e(e.modo)})"
                 + (f" · {_e(e.elegida.tipo)} · carga viva {'sí' if e.elegida.carga_viva else 'no'} · "
                    f"{_e(e.elegida.guia_temperatura)}" if e.elegida else "")
                 + f" · <b>Bonete:</b> {_e(e.bonete)} · "
                 f"<b>Emisión requerida:</b> {_e(e.emision_req)}</p>"
                 + "".join(f"<p style='color:#55606d'>• {_e(n)}</p>" for n in e.notas))
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


def html_empaquetadura(e: EM.ResultadoEmpaquetadura) -> str:
    p = ["<h2 style='color:#3d5a80'>Empaquetadura y bonete</h2>",
         f"<p><b>Modo:</b> {_e(e.modo)} · <b>Recomendada:</b> "
         f"{_e(e.recomendada.nombre) if e.recomendada else 'sin empaquetadura apta'} · <b>Elegida:</b> "
         f"{_e(e.texto)}</p>"]
    if e.modo == "MANUAL":
        p.append(f"<p style='color:#c0392b'><b>{_e(AVISO_MANUAL)}</b></p>")
    p.append(f"<p><b>Bonete:</b> {_e(e.bonete)}. {_e(e.bonete_motivo)} <a href='ayuda:tipo_bonete'>(ayuda)</a></p>")
    p.append(f"<p><b>Emisión fugitiva requerida:</b> {_e(e.emision_req)}. {_e(e.emision_motivo)} "
             "<a href='ayuda:emision_fugitiva'>(ayuda)</a></p>")
    if e.elegida is not None:
        x = e.elegida
        p.append(f"<p><b>Tipo:</b> {_e(x.tipo)} · <b>Carga viva:</b> {'sí' if x.carga_viva else 'no'} · "
                 f"<b>Guía de temperatura:</b> {_e(x.guia_temperatura)}</p>")
    p.append("<h4>Catálogo de empaquetaduras</h4><table width='100%' cellspacing='0' cellpadding='3' border='1' "
             "style='border-collapse:collapse'><tr bgcolor='#dde5ee'><th>Empaquetadura</th><th>Carga viva</th>"
             "<th>Guía de temperatura</th><th>Tipo</th></tr>" + "".join(
                 f"<tr><td>{_e(x.nombre)}</td><td>{'Sí' if x.carga_viva else 'No'}</td>"
                 f"<td>{_e(x.guia_temperatura)}</td><td>{_e(x.tipo)}</td></tr>" for x in EM.EMPAQUETADURAS.values())
             + "</table>")
    if e.justificacion:
        p.append("<h4>Justificación</h4><ul>" + "".join(f"<li>{_e(x)}</li>" for x in e.justificacion) + "</ul>")
    if e.notas:
        p.append("<h4>Notas de instalación</h4><ul>" + "".join(f"<li>{_e(x)}</li>" for x in e.notas) + "</ul>")
    if e.alternativas:
        p.append("<h4>Alternativas aptas</h4><ul>" + "".join(f"<li>{_e(a.nombre)} — {_e(b)}</li>"
                                                            for a, b in e.alternativas) + "</ul>")
    if e.descartadas:
        p.append("<h4>Descartadas y motivo</h4><ul>" + "".join(f"<li><b>{_e(a.nombre)}</b>: {_e(b)}</li>"
                                                              for a, b in e.descartadas) + "</ul>")
    p.append("<h4>Alertas</h4>" + _alertas_html(e.alertas))
    p.append("<p style='color:#55606d;font-size:8pt'>Valores genéricos de catálogo. Verificar con la hoja técnica "
             "de la empaquetadura ofertada y su certificado de emisión.</p>")
    return "".join(p)
