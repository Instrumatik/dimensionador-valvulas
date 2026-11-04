"""v0.16.0: fluidos de refinería, mejoradores, servicios y químicos; bola segmentada parabólica."""
import os

import pytest

from dimensionador import ayuda, empaquetaduras as EM, estilos as E, fluido_servicio as FS
from dimensionador import fluidos_proceso as FP, herramientas as H, propiedades as P, quimica as Q
from dimensionador import seleccion_materiales as SM
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular

pytestmark = pytest.mark.skipif(not P.DISPONIBLE, reason="requiere CoolProp")


def test_catalogo_completo():
    assert len(FP.CATALOGO) >= 37
    for f in FP.CATALOGO.values():
        assert f.grupo in FP.GRUPOS and f.presentaciones and f.ingles
    assert FP.presentaciones("Crudo comercial")[0] == "8 °API" and FP.presentaciones("Crudo comercial")[-1] == "27 °API"
    for n in ("Agua agria", "Agua agria despojada", "Aguas servidas / residuales", "Agua aceitosa",
              "Agua de enfriamiento (circuito de torre)", "Agua de servicio"):
        assert any(n in v for v in FS.variantes("liquido", FS.AGUA)), n


def test_propiedades_de_quimicos():
    def sg(n, p, T=293.15):
        return FP.liquido(n, p, 500, T).SG
    assert sg("Ácido sulfúrico", "98 %") == pytest.approx(1.83, abs=0.02)
    assert sg("Hidróxido de sodio (soda cáustica)", "50 %") == pytest.approx(1.52, abs=0.02)
    assert sg("Ácido fosfórico", "85 %", 298.15) == pytest.approx(1.68, abs=0.03)
    assert sg("Monoetilenglicol (MEG)", "MEG 50 % en agua") == pytest.approx(1.07, abs=0.01)
    teg = FP.liquido("Trietilenglicol (TEG)", "TEG pobre 99,5 % (deshidratación de gas)", 500, 313.15)
    assert 1.10 < teg.SG < 1.13 and 0.020 < teg.mu < 0.035
    with pytest.raises(ValueError):
        FP.liquido("Azufre líquido", "Azufre líquido desgasificado (H₂S < 10 ppm)", 500, 373.15)


def test_crudo_y_datos_de_laboratorio():
    r = FP.liquido("Crudo comercial", "16 °API", 500, 288.71)
    assert r.SG == pytest.approx(141.5 / (131.5 + 16), abs=0.003)
    base = FP.liquido("Crudo comercial", "16 °API", 500, 323.15).mu
    lab = FP.liquido("Crudo comercial", "16 °API", 500, 323.15, "API 16; ν 1000 cSt a 50 °C; ν 100 cSt a 100 °C")
    assert lab.nu_cSt == pytest.approx(1000, rel=0.02) and lab.mu != pytest.approx(base, rel=0.05)
    # más pesado → más denso y más viscoso
    assert FP.liquido("Crudo comercial", "10 °API", 500, 333.15).mu > FP.liquido("Crudo comercial", "25 °API", 500,
                                                                                  333.15).mu


def test_gases_de_proceso():
    g = P.gas("Gas de síntesis (syngas)", 2000, 313.15, P.composicion_tipica("Gas de síntesis (syngas)"))
    assert 8 < g.M < 25 and 0.9 < g.Z < 1.1
    assert FP.es_toxico("Gas ácido — Gas ácido de regeneradora de aminas") or FP.es_toxico("Gas ácido")


def _dim(fluido, pres, T, datos="", P1=1500, P2=900):
    r = FP.liquido(fluido, pres, P1, T, datos or None)
    c = CasoLiquido("Máximo", 100, None, P1, P2, T, r.SG, r.mu, r.Pv, FL=0.9, Fd=0.46)
    return Dimensionamiento([c], r.Pc, "globo_contorneado_iso_abre", nps_valvula=4, fluido=fluido, variante=pres,
                            datos_fluido=datos)


def _mat(dim):
    return calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4), dim, SM.ServicioMateriales())


def test_materiales_residuo_caliente():
    res = _mat(_dim("Hidrocarburos pesados", "Residuo atmosférico (12 °API)", 613.15, "API 12; S 3,5 %; TAN 2"))
    cod = {m.codigo for m in res.materiales.mecanismos}
    assert {"M30", "M31", "M33"} <= cod
    assert res.materiales.cuerpo.clave != "WCB"
    assert any(a.codigo == "fp_propiedades_estimadas" for _, a in res.alertas)


def test_agentes_nuevos_y_reglas():
    hc = Q.normalizar(Q.AgenteServicio("hidrocarburos", "% p/p", 100, "Líquida"), 101.3, 0.9)
    from dimensionador import materiales as MT
    epdm = next(m for m in MT.MATERIALES.values() if "epdm" in m.quimica)
    assert Q.evaluar(epdm, hc, 40, False).nivel == "D"
    tan = Q.normalizar(Q.AgenteServicio("tan", "mg KOH/g", 2.5, "Líquida"), 101.3, 0.9)
    assert Q.evaluar(MT.MATERIALES["WCB"], tan, 320, False).nivel == "D"
    assert Q.evaluar(MT.MATERIALES["WCB"], tan, 150, False).nivel == "A"


def test_alertas_de_solidificacion():
    al = FP.alertas("Hidróxido de sodio (soda cáustica)", "50 %", "", [278.15], "liquido")
    assert any(a.codigo == "fp_solidifica" for a in al)
    al = FP.alertas("Amina rica", "MDEA 45 %", "", [323.15], "liquido")
    assert any(a.codigo == "fp_desgasificacion" for a in al)


def test_ayuda_completa():
    for k in ("fluidos_proceso", "caracterizacion_fluido", "fp_solidifica", "fp_temperatura_alta",
              "fp_desgasificacion", "fp_polimero_corte", "fp_propiedades_estimadas", "agente_hidrocarburos",
              "agente_glicoles", "agente_azufre_hc", "agente_tan"):
        assert ayuda.obtener(k), k
    assert "M33" in ayuda.obtener("mecanismos_falla").texto
    assert "Crudo comercial" in ayuda.obtener("fluidos_proceso").texto


def test_tabla_de_fluidos_incluye_proceso():
    filas = H.filas_proceso()
    assert any(f.fluido.startswith("Ácido sulfúrico") for f in filas)
    assert all(f.SG_liq and f.SG_liq > 0.5 for f in filas)


def test_bola_segmentada_parabolica():
    e = E.ESTILOS["bola_segmentada_parabolica"]
    assert "bola_segmentada_parabolica" in E.CUERPOS["bola_segmentada"].trims
    assert e.caracteristica == "parabolica" and e.FL > E.ESTILOS["bola_segmentada"].FL
    assert E.NOMBRE_CORTO["bola_segmentada_parabolica"] == "Perfil parabólico"
    # a mitad de caudal abre más que la isoporcentual y menos que la lineal
    h_par = E.apertura_requerida(0.5, "parabolica", 100)
    assert E.apertura_requerida(0.5, "lineal", 100) < h_par < E.apertura_requerida(0.5, "isoporcentual", 100) or \
        E.apertura_requerida(0.5, "isoporcentual", 100) < h_par


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_solapa_2_con_fluido_de_proceso(app):
    from dimensionador.gui import ventana as V
    w = V.VentanaPrincipal()
    w.cb_fluido.setCurrentText("Ácido sulfúrico")
    app.processEvents()
    w.cb_variante.setCurrentText("98 %")
    app.processEvents()
    assert w.ed_comp_gn.isVisibleTo(w) or w.ed_comp_gn.text()
    assert w.fila_variante[1].property("ayuda") == "fluidos_proceso"
