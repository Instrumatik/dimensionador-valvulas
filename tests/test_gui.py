"""Prueba de la interfaz de la versión 2 (líquidos) en modo sin pantalla."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _cargar(w):
    w.cb_nps["entrada"].setCurrentText('6"')
    w.cb_nps["salida"].setCurrentText('6"')
    w.ed_ident["tag"].setText("FV-101")
    F = w.filas
    for j, (q, p1, p2) in enumerate([(60, 10, 6), (250, 9, 3), (360, 8, 1.2)]):
        F["caudal"].edits[j].setText(str(q))
        F["P1"].edits[j].setText(str(p1))
        F["P2"].edits[j].setText(str(p2))
        F["T1"].edits[j].setText("90")


def test_calculo_y_entregables(app, tmp_path):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    w.calcular()
    assert w.res is not None
    assert w.res.nps_valvula == 6
    cv = [c.text() for c in w.salidas["Cv"].celdas]
    assert all(cv[:3]) and cv[2].startswith("157") and cv[3] == cv[4] == ""
    assert w.salidas["dP"].lbl_unidad.text() == "bar"
    assert "Memoria de cálculo" in w.vistas["memoria"].toPlainText()
    ruta = w.exportar_word("todos", str(tmp_path / "todos.docx"))
    assert os.path.getsize(ruta) > 20000
    doc = w.documento_impresion("todos")
    assert "Informe técnico" in doc.toPlainText()
    # Cambio global de unidades: resultados y documentos en imperial
    w.aplicar_sistema("Imperial")
    assert w.salidas["dP"].lbl_unidad.text() == "psi"
    assert w.salidas["dP"].celdas[0].text().startswith("58")
    assert "psig" in w.vistas["hoja_datos"].toPlainText()
    # Guardar y abrir el proyecto
    estado = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(estado)
    w2.calcular()
    assert w2.res.salidas[2]["Cv"] == pytest.approx(w.res.salidas[2]["Cv"], rel=1e-6)


def test_cedulas_por_diametro(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w.cb_nps["entrada"].setCurrentText('48"')
    items = [w.cb_sch["entrada"].itemText(i) for i in range(w.cb_sch["entrada"].count())]
    assert items == ["STD", "XS"]


def test_rueda_no_cambia_listas(app):
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QWheelEvent
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    cb = w.cb_trim
    antes = cb.currentIndex()
    ev = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0), QPoint(0, -120), Qt.NoButton,
                     Qt.NoModifier, Qt.NoScrollPhase, False)
    QtWidgets.QApplication.sendEvent(cb, ev)
    assert cb.currentIndex() == antes


def test_casos_nuevos_y_panel(app):
    from dimensionador.gui.ventana import CIERRE, VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    # FL por caso, distinto en el mínimo
    w.filas["FL"].edits[0].setText("0,75")
    # Tight Shutoff y Transitorio
    w.filas["P1"].edits[CIERRE].setText("12")
    w.filas["P2"].edits[CIERRE].setText("0")
    for k, v in (("caudal", "400"), ("P1", "8"), ("P2", "1"), ("T1", "90")):
        w.filas[k].edits[4].setText(v)
    w.calcular()
    assert w.res is not None and w.res.dim.cierre is not None
    assert w.res.salidas[0]["FL"] == pytest.approx(0.75)
    assert w.salidas["dP"].celdas[CIERRE].text().startswith("12")
    assert w.salidas["Cv"].celdas[CIERRE].text() == ""
    assert w.salidas["Cv"].celdas[4].text()
    assert "Kc" not in w.salidas
    # Caudal contrario en resultados
    assert w.salidas["caudal_otro"].lbl.text() == "Flujo másico"
    assert w.salidas["caudal_otro"].celdas[1].text()
    # Cambiar a másico convierte en lugar de borrar
    q = w.filas["caudal"].edits[1].text()
    w.cb_tipo_caudal.setCurrentIndex(1)
    assert w.filas["caudal"].edits[1].text() not in ("", q)
    # Panel de información
    w.tabs.setCurrentIndex(1)
    w.abrir_ayuda("FL")
    panel = w.paneles[1]
    assert panel.texto.toPlainText()
    ancho = panel.width()
    panel.limpiar()
    assert panel.texto.toPlainText() == "" and panel.width() == ancho


def test_fecha_con_calendario(app):
    from PySide6.QtCore import QDate
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    f = w.ed_ident["fecha"]
    f.setDate(QDate(2026, 3, 5))
    assert f.text() == "05/03/2026"
    estado = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(estado)
    assert w2.ed_ident["fecha"].date() == QDate(2026, 3, 5)
    assert f.lineEdit().isReadOnly()


def _tipo(w, clave):
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData(clave))


def test_gas_definido_por_usuario(app, tmp_path):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _tipo(w, "gas")
    assert w.filas["SG"].lbl.isHidden() and not w.filas["Z1"].lbl.isHidden()
    assert w.filas["xT"].edits[1].text()            # xT típico del trim
    w.cb_fluido.setCurrentText("Definido por el usuario")
    w.cb_nps["entrada"].setCurrentText('4"')
    w.cb_nps["salida"].setCurrentText('4"')
    w.cb_tamano.setCurrentIndex(w.cb_tamano.findData(4))
    w.cb_tipo_caudal.setCurrentIndex(0)             # volumétrico estándar
    F = w.filas
    assert F["caudal"].magnitud() == "caudal_gas_std"
    for k, v in (("caudal", "3800"), ("P1", "6,8"), ("P2", "3,1"), ("T1", "160"), ("M", "44,01"),
                 ("mu", "0,0159"), ("gamma", "1,30"), ("Z1", "0,988"), ("xT", "0,60"), ("FL", "0,85"),
                 ("Fd", "0,42")):
        F[k].edits[1].setText(v)
    F["P1"].elegir("bar a", convertir=False)
    F["P2"].elegir("bar a", convertir=False)
    w.calcular()
    assert w.res is not None and w.res.dim.tipo == "gas"
    assert w.res.salidas[0]["Kv"] == pytest.approx(62.7, rel=3e-3)    # IEC 60534-2-1, ejemplo 3
    assert w.salidas["caudal_otro"].lbl.text() == "Flujo másico"
    assert w.salidas["Y"].celdas[1].text().startswith("0,674")
    assert w.salidas["Lp_g"].celdas[1].text() and w.salidas["Ma2"].celdas[1].text()
    assert w.salidas["nivel_trim"].celdas[1].text()
    # Pasar a másico convierte con la densidad normal
    w.cb_tipo_caudal.setCurrentIndex(1)
    assert F["caudal"].magnitud() == "caudal_masico"
    assert float(F["caudal"].edits[1].text().replace(",", ".")) == pytest.approx(7461.3, rel=1e-3)
    ruta = w.exportar_word("todos", str(tmp_path / "gas.docx"))
    import docx
    texto = "\n".join(c.text for t in docx.Document(ruta).tables for r in t.rows for c in r.cells)
    assert "Factor de expansión Y" in texto and "Ruido de la válvula LpA a Rn" in texto
    assert "Kapp" not in texto
    # Guardar y abrir conserva el tipo de fluido
    w2 = VentanaPrincipal()
    w2._cargar(w._estado())
    assert w2.tipo() == "gas"
    w2.calcular()
    assert w2.res.salidas[0]["Kv"] == pytest.approx(w.res.salidas[0]["Kv"], rel=1e-6)


def test_steam_y_vuelta_a_liquido(app):
    pytest.importorskip("CoolProp")
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _tipo(w, "steam")
    assert not w.cb_tipo_caudal.isEnabled() and w.filas["caudal"].magnitud() == "caudal_masico"
    F = w.filas
    for j, (W, p1, p2, t1) in enumerate([(5000, 10, 6, ""), (12000, 10, 5, "250")]):
        F["caudal"].edits[j].setText(str(W))
        F["P1"].edits[j].setText(str(p1))
        F["P2"].edits[j].setText(str(p2))
        F["T1"].edits[j].setText(t1)
    w.calcular()
    assert w.res is not None and w.res.dim.tipo == "steam"
    assert "sat." in w.salidas["tipo_calculo"].celdas[0].text()
    assert w.salidas["sobrecalentamiento2"].celdas[0].text()
    assert w.salidas["caudal_otro"].lbl.text().startswith("Caudal volumétrico real")
    assert "IAPWS" in w.vistas["memoria"].toPlainText()
    _tipo(w, "liquido")
    assert w.res is None and not w.filas["Kc"].lbl.isHidden() and w.filas["xT"].lbl.isHidden()


def test_solapa_materiales(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    # el fluido se define una sola vez, en 2-Cálculos Válvula
    assert not {"fluido", "familia_fluido", "fase", "acuosa"} & set(w.mat_cb)
    assert w.fila_variante[2].isVisibleTo(w) or not w.isVisible()
    w.cb_variante.setCurrentText("Agua de mar")
    assert w.cb_agua_libre.currentText() == "Sí" and not w.cb_agua_libre.isEnabled()
    assert "salinidad 3,5" in w.lbl_salinidad.text()
    fam, ag, un, ed, fa = w.mat_agentes[0]
    fam.setCurrentText("Halogenuros / sales")
    assert ag.currentData() == "cloruros"
    ed.setText("25000")
    modo, sel = w.mat_comp["vastago"][1], w.mat_comp["vastago"][2]
    modo.setCurrentText("MANUAL")
    assert sel.isEnabled()
    sel.setCurrentIndex(sel.findData("316"))
    w.calcular()
    m = w.res.materiales
    assert m is not None and m.componentes["vastago"].modo == "MANUAL"
    assert m.servicio.fluido == "Agua de mar" and m.servicio.acuosa == "Sí"
    assert w.res.dim.salinidad_pct == pytest.approx(1.648 * 25000 / 1e4 / (1 + 0.0073 * 4.12), rel=0.01)
    assert float(w.filas["SG"].edits[0].text().replace(",", ".")) > 0.99   # agua pura a 90 °C: 0,965
    assert "Agua de mar" in w.mat_lbl_fluido.text()
    assert "Recomendado" in w.mat_comp["cuerpo"][4].text()
    assert "Selección de materiales" in w.vistas["informe_tecnico"].toPlainText()
    estado = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(estado)
    assert w2.cb_variante.currentText() == "Agua de mar"
    assert w2.mat_agentes[0][3].text() == "25000"
    assert w2.mat_comp["vastago"][1].currentText() == "MANUAL"
    assert w2.mat_comp["vastago"][2].currentData() == "316"
    assert w2._servicio_materiales().agentes[0].clave == ag.currentData()


def test_empaquetadura_y_bola_trunnion(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("bola_trunnion"))
    assert w.cb_trim.findData("bola_paso_completo_90") >= 0
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("bola_paso_completo_90"))
    w.calcular()
    e = w.res.materiales.empaquetadura
    assert e is not None and "prensaestopas" in e.bonete
    assert "Recomendada" in w.mat_emp[4].text() and e.bonete in w.mat_lbl_bonete.text()
    modo, sel = w.mat_emp[1], w.mat_emp[2]
    modo.setCurrentText("MANUAL")
    sel.setCurrentIndex(sel.findData("grafito"))
    w.calcular()
    assert w.res.materiales.empaquetadura.elegida.clave == "grafito"
    assert "Empaquetadura" in w.vistas["hoja_datos"].toPlainText()
    w2 = VentanaPrincipal()
    w2._cargar(w._estado())
    assert w2.cb_cuerpo.currentData() == "bola_trunnion"
    assert w2.cb_trim.currentData() == "bola_paso_completo_90"
    assert w2.mat_emp[1].currentText() == "MANUAL" and w2.mat_emp[2].currentData() == "grafito"
    # proyecto anterior a 0.8.0 con estilo «Bola»
    est = w._estado()
    est["campos"]["cuerpo"] = "Bola"
    est["campos"]["trim"] = "Bola segmentada (V-notch)"
    w3 = VentanaPrincipal()
    w3._cargar(est)
    assert w3.cb_cuerpo.currentData() == "bola_trunnion" and w3.cb_trim.currentData() == "bola_segmentada"


def test_gas_seco_y_proyecto_070(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData("gas"))
    w.cb_fluido.setCurrentText("Nitrógeno")
    assert w.cb_agua_libre.isEnabled() and w.cb_agua_libre.currentText() == "No"
    assert not w.mat_ed_pH.isEnabled()
    w.cb_fluido.setCurrentText("Definido por el usuario")
    assert "Gas natural" in [w.cb_variante.itemText(i) for i in range(w.cb_variante.count())]
    # proyecto guardado con la versión 0.7.0: el fluido de 3-Materiales pasa a la solapa 2
    w2 = VentanaPrincipal()
    estado = w2._estado()
    estado["campos"].pop("variante")
    estado["campos"].pop("agua_libre")
    estado["campos"]["mat_fluido"] = "Agua producida"
    estado["campos"]["mat_familia_fluido"] = "Agua"
    w2._cargar(estado)
    assert w2.cb_variante.currentText() == "Agua producida (yacimiento)"


def test_trim_carrera_y_juego_v082(app, tmp_path):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    w.calcular()
    c0 = w.salidas["carrera"].celdas[0].text()
    assert w.cb_carrera.currentText() == "mm" and c0 and "mm" not in c0      # un solo valor, unidad aparte
    w.cb_carrera.setCurrentText("in")
    assert float(w.salidas["carrera"].celdas[0].text().replace(",", ".")) == pytest.approx(
        float(c0.replace(".", "").replace(",", ".")) / 25.4, rel=0.01)
    assert " in" in w.vistas["hoja_datos"].toPlainText()
    w.cb_carrera.setCurrentText("mm")
    assert "Carrera nominal" in w.lbl_resumen.text() and "estimad" in w.lbl_geo.text()
    # puerto y carrera certificados, en pulgadas
    w.f_puerto.elegir("in", convertir=False)
    w.f_puerto.edits[0].setText("5,375")
    w.f_carrera.elegir("in", convertir=False)
    w.f_carrera.edits[0].setText("3")
    # juego de internos elegido
    i = w.mat_juego.findData("N25-T12")
    w.mat_juego.setCurrentIndex(i)
    assert not w.mat_comp["obturador"][1].isEnabled()
    w.calcular()
    g = w.res.geometria
    assert g.puerto_certificado and g.texto_puerto.startswith("5 3/8 in")
    assert w.res.materiales.juego_usuario == "N25-T12"
    assert "N25-T12" in w.mat_lbl_juego.text()
    # se guarda y se vuelve a abrir
    s = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(s)
    assert w2.mat_juego.currentData() == "N25-T12" and w2.f_carrera.edits[0].text() == "3"
    # el texto guía de la concentración sigue a la unidad
    fam, ag, un, ed, fa = w2.mat_agentes[0]
    fam.setCurrentText("Gases ácidos / reactivos")
    un.setCurrentText("% p/p")
    assert ed.placeholderText() == "en % p/p"
    un.setCurrentText("ppmv")
    assert ed.placeholderText() == "en ppmv"


def test_solapas_equipo(app, tmp_path):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    E = w.eq_w
    E["act_falla"].setCurrentIndex(E["act_falla"].findText("Abre (FO)") if E["act_falla"].findText("Abre (FO)") >= 0 else 0)
    E["pos_tag"].setText("ZY-101")
    E["acc_quick_exhaust"].setText("1 unidad 1/2 NPT")
    w.calcular()
    eq = w.res.equipo
    assert eq is not None and eq.actuador.seleccion
    texto = w.vistas["hoja_datos"].toPlainText()
    assert "Actuador" in texto and "ZY-101" in texto and "1 unidad 1/2 NPT" in texto
    assert "Boosters" not in texto                        # celda vacía: no figura en los entregables
    assert "Actuador" in w.vistas["memoria"].toPlainText()
    estado = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(estado)
    assert {k: (x.currentText() if hasattr(x, "currentText") else x.text()) for k, x in w2.eq_w.items()} == estado["equipo"]
    w2.calcular()
    assert w2.res.equipo.actuador.seleccion == eq.actuador.seleccion


def test_concordancia_actuador_valvula(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    E = w.eq_w

    def habilitadas(cb):
        return [cb.itemText(i) for i in range(cb.count()) if cb.model().item(i).isEnabled()]

    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("globo"))
    assert "Yugo escocés" not in habilitadas(E["act_tipo"]) and "Diafragma y resorte" in habilitadas(E["act_tipo"])
    assert habilitadas(E["act_flujo"]) == ["Up", "Down"]
    E["act_tipo"].setCurrentText("Pistón retorno por resorte")
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("mariposa"))
    assert E["act_tipo"].currentText() == "Piñón y cremallera (Rack and pinion)"
    assert E["act_tipo"].count() == 10 and "Diafragma y resorte" not in habilitadas(E["act_tipo"])
    assert habilitadas(E["act_flujo"]) == ["Unidireccional"] and E["act_flujo"].currentText() == "Unidireccional"
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("bola_trunnion"))
    assert habilitadas(E["act_flujo"]) == ["Unidireccional", "Bidireccional"]
    E["act_flujo"].setCurrentText("Bidireccional")
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("angulo"))
    from dimensionador.actuadores import TIPOS_ROTATIVOS
    assert E["act_flujo"].currentText() in ("Up", "Down")
    assert E["act_tipo"].currentText() not in TIPOS_ROTATIVOS


def test_trim_reducido_en_pantalla_y_documentos(app, tmp_path):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    w.cb_tamano.setCurrentIndex(w.cb_tamano.findData(6))
    w.calcular()
    cv_full = w.res.Cv_nominal
    w.f_puerto.elegir("in", convertir=False)
    w.f_puerto.edits[0].setText("3")
    w.ed_cv_red.setText("200")
    w.calcular()
    tr = w.res.trim_reducido
    assert tr is not None and tr.Cv_certificado and w.res.Cv_nominal == pytest.approx(200)
    assert tr.Cv_tipico == pytest.approx(cv_full)
    assert "trim reducido" in w.lbl_geo.text()
    assert "Trim reducido: tamaño del puerto" in w.vistas["hoja_datos"].toPlainText()
    assert os.path.getsize(w.exportar_word("todos", str(tmp_path / "red.docx"))) > 20000
    w2 = VentanaPrincipal()
    w2._cargar(w._estado())
    assert w2.ed_cv_red.text() == "200"


def test_buscador_encabezado(app):
    from dimensionador.gui.buscador import normalizar
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    b = w.buscador
    assert normalizar("Cavitación") == "cavitacion"
    assert b.buscar("c") == []
    res = b.buscar("cavitacion")
    textos = [r.texto for r in res]
    assert any(t.startswith("Dato · 2-Cálculos Válvula") for t in textos)
    assert any(t.startswith("Ayuda · ") for t in textos)
    assert any(r.texto.startswith("Opción · 3-Materiales") for r in b.buscar("ptfe"))
    assert b.buscar("zzzqqq") == []
    # Ir a un dato cambia de solapa y muestra su explicación en el panel
    dato = next(r for r in b.buscar("diametro del vastago") if r.texto.startswith("Dato"))
    b.ir(dato)
    app.processEvents()
    assert w.tabs.currentIndex() == 3
    assert w.paneles[3].texto.toPlainText()


def test_trim_anticavitacion_por_etapas(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    for j, p2 in enumerate(("1,5", "1,5", "1,2")):
        w.filas["P2"].edits[j].setText(p2)
    w.calcular()
    assert w.salidas["etapas_txt"].celdas[0].text()
    assert w.salidas["k_etapa"].celdas[0].text() in ("", "—")
    w.cb_anticav.setCurrentIndex(w.cb_anticav.findData("etapas_3"))
    assert w.filas["Kc"].edits[0].text() == "0,973"
    w.calcular()
    assert w.res.dim.anticav == "etapas_3"
    assert w.salidas["k_etapa"].celdas[0].text() not in ("", "—")
    assert "Multietapa, 3 etapas" in w.vistas["hoja_datos"].toPlainText()
    assert "Kapp por etapa" in w.vistas["memoria"].toPlainText()
    w.cb_anticav.setCurrentIndex(0)
    assert w.filas["Kc"].edits[0].text() != "0,973"
    # En un cuerpo rotativo solo queda el estándar
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("mariposa"))
    it = w.cb_anticav.model().item(w.cb_anticav.findData("etapas_2"))
    assert not it.isEnabled()


def test_actuador_certificado_en_pantalla(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    E = w.eq_w
    assert w.g_cert.isHidden()
    w.calcular()
    auto = w.res.equipo.actuador
    assert auto.ok
    E["act_modo"].setCurrentText("MANUAL")
    assert not w.g_cert.isHidden()
    assert not w.f_cert["cert_area_in2"].edits[0].isHidden()
    assert w.f_cert["cert_par_aire_lbfin"].edits[0].isHidden()
    w.calcular()
    assert "act_cert_faltan" in {a.codigo for a in w.res.equipo.actuador.alertas}
    F = w.f_cert
    F["cert_area_in2"].elegir("in²", False)
    F["cert_area_in2"].edits[0].setText(str(auto.area_in2).replace(".", ","))
    F["cert_banco_psig"].elegir("psig", False)
    for j, v in enumerate(auto.P_banco):
        F["cert_banco_psig"].edits[j].setText(f"{v:g}".replace(".", ","))
    F["cert_carrera_in"].elegir("in", False)
    F["cert_carrera_in"].edits[0].setText("4")
    F["cert_pmax_psig"].elegir("psig", False)
    F["cert_pmax_psig"].edits[0].setText("50")
    w.f_friccion.elegir("lbf", False)
    w.f_friccion.edits[0].setText("40")
    w.calcular()
    ra = w.res.equipo.actuador
    assert ra.ok, [a.mensaje for a in ra.alertas]
    assert "certificado" in ra.seleccion
    assert "certificada" in ra.fuerzas[2][2]
    assert "certificado" in w.vistas["hoja_datos"].toPlainText()
    estado = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(estado)
    w2.calcular()
    assert w2.res.equipo.actuador.seleccion == ra.seleccion


def test_datos_para_verificacion_externa(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _cargar(w)
    assert w.g_ext.isHidden()
    w.bt_ext.setChecked(True)
    assert not w.g_ext.isHidden()
    w.calcular()
    ra = w.res.equipo.actuador
    campos = [w.tb_ext.item(i, 0).text() for i in range(w.tb_ext.rowCount())]
    assert campos[:3] == ["Operating Range", "Pa", "Pb"] and "Seat Load Force" in campos
    w._ext_copiar()
    assert QtWidgets.QApplication.clipboard().text().startswith("Operating Range\t")
    w._ext_ayuda(campos.index("Port Diameter"))
    w.ed_ext["area"].setText(f"{ra.area_in2:g}")
    w.ed_ext["empuje"].setText(f"{max(ra.terminos['cierre'], ra.terminos['apertura']) * 1.5:.0f}")
    w._ext_comparar()
    txt = w.vista_ext.toPlainText()
    assert "Fuerza requerida" in txt and "Seat Load Force" in txt
    w._eq_nuevo()
    assert w.tb_ext.rowCount() == 0
