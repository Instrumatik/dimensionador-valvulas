"""v0.15.2: factores típicos de válvula, SG y tabla de fluidos en la barra de herramientas."""
import os

import pytest

from dimensionador import estilos as E, herramientas as H, propiedades as P, trims as TR

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_factores_de_todos_los_estilos_en_uso():
    filas = H.factores_valvula()
    claves = {f.clave for f in filas}
    deslizantes = {k for k in TR.claves_en_uso() if E.ESTILOS[k].familia != "rotativa"}
    rotativas = {k for c, cu in E.CUERPOS.items() if not TR.deslizante(c) for k in cu.trims}
    assert rotativas <= claves and {f.clave for f in filas if f.clave in deslizantes}
    cuerpos = {f.cuerpo for f in filas}
    assert {"Globo", "Ángulo", "Mariposa", "Mariposa triple excentricidad", "Bola segmentada (corte en V)"} <= cuerpos
    for f in filas:                              # los mismos factores que usa 2-Cálculos
        st = E.ESTILOS[f.clave]
        assert (f.FL, f.xT, f.Fd, f.Kc) == (st.FL, st.xT, st.Fd, E.KC_TIPICO.get(f.clave))
        assert 0 < f.FL <= 1 and 0 < f.xT <= 1
    assert H.factores_anticavitacion() and H.factores_antiruido()


@pytest.mark.skipif(not P.DISPONIBLE, reason="sin CoolProp")
def test_sg_y_tabla_de_fluidos():
    agua = {p.nombre: p.valor for p in H.propiedades_punto("Agua / vapor de agua", 101.325, 288.15)}
    assert agua["Gravedad específica SG (agua a 15 °C = 1)"] == pytest.approx(1.0, abs=1e-3)
    co2 = {p.nombre: p.valor for p in H.propiedades_punto("Dióxido de carbono", 101.325, 300)}
    assert co2["Gravedad específica del gas SG (aire = 1)"] == pytest.approx(44.01 / 28.9647, rel=1e-3)
    t = {f.fluido: f for f in H.tabla_fluidos()}
    assert set(t) == set(P.FLUIDOS)
    a = t["Agua / vapor de agua"]
    assert a.Tc - 273.15 == pytest.approx(373.9, abs=0.1) and a.Pc == pytest.approx(22064, abs=1)
    assert a.Teb - 273.15 == pytest.approx(99.97, abs=0.05) and a.SG_liq == pytest.approx(1.0, abs=1e-3)
    assert t["Propano"].M == pytest.approx(44.1, abs=0.01) and t["Propano"].Pv is not None
    assert t["Helio"].Pv is None and t["Aire"].k == pytest.approx(1.40, abs=0.01)


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_ventanas(app):
    from dimensionador.gui import herramientas as GH
    f = GH.Factores()
    total = f.tabla.rowCount()
    f.cb_cuerpo.setCurrentText("Mariposa")
    assert 0 < f.tabla.rowCount() < total and f.tabs.count() == 3
    assert "factores" in GH.VENTANAS and "factores" in dict(GH.HERRAMIENTAS)
    if P.DISPONIBLE:
        fl = GH.Fluidos()
        assert fl.tabs.count() == 2
        fl.tabla_fluidos.cargar()
        assert fl.tabla_fluidos.tabla.rowCount() == len(P.FLUIDOS)
