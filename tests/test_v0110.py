"""Versión 0.11.0: gas natural con composición, doble guía superior, característica fijada por el trim."""
import os

import pytest

from dimensionador import compresible as CG, propiedades
from dimensionador.estilos import CUERPOS, ESTILOS
from dimensionador.iec60534_2_1 import Gas, Valvula, dimensionar_gas
from dimensionador.proyecto import Dimensionamiento

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_composicion_se_lee_y_normaliza():
    c = propiedades.leer_composicion("Metano 89; etano 5,5; Propano 2; Nitrógeno 1,5; Dióxido de carbono 1")
    assert sum(c.values()) == pytest.approx(100) and c["Metano"] == pytest.approx(89 / 99 * 100)
    assert propiedades.leer_composicion("") == propiedades.GN_TIPICO
    with pytest.raises(propiedades.ErrorPropiedades):
        propiedades.leer_composicion("Metano 90; Kriptonita 10")
    with pytest.raises(propiedades.ErrorPropiedades):
        propiedades.leer_composicion("Metano 50")


def test_gas_natural_calcula_t2_y_z2():
    e = CG.resolver_estado(CG.CasoGas("Normal", 1.0, None, 7000, 2000, 300.15), "gas", "Gas natural")
    assert e.Z1 == pytest.approx(0.858, abs=0.005) and e.Z2 == pytest.approx(0.942, abs=0.005)
    assert e.T2 - 273.15 == pytest.approx(1.7, abs=0.5)
    assert 17.5 < e.M < 18.5 and 1.0e-5 < e.mu < 1.6e-5
    metano = CG.resolver_estado(CG.CasoGas("Normal", 1.0, None, 7000, 2000, 300.15), "gas", "Metano")
    assert metano.T2 > e.T2                      # los pesados enfrían más en la expansión
    pesado = CG.resolver_estado(CG.CasoGas("Normal", 1.0, None, 7000, 2000, 300.15), "gas", "Gas natural",
                                {"Metano": 80, "Etano": 12, "Propano": 8})
    assert pesado.M > e.M and pesado.Z1 < e.Z1


def test_rev_de_gas_usa_caudal_real():
    g = Gas(P1=680, P2=310, T1=433, M=44.01, gamma=1.30, Z=0.988, mu=1.59e-5, QN=3800)
    r = dimensionar_gas(g, Valvula(FL=0.85, xT=0.60, Fd=0.42, d_mm=100))
    Q, nu = r.memoria.valor("Q"), r.memoria.valor("ν")
    assert Q == pytest.approx(r.extra["W"] / r.extra["rho1"]) and nu == pytest.approx(1.59e-5 / r.extra["rho1"])


def test_doble_guia_superior_y_caracteristica_fija():
    # v0.12.0: la doble guía tiene los dos sentidos de flujo y la clave de v0.11.0 se convierte
    e = ESTILOS["globo_doble_guia_abre"]
    assert e.FL == 0.90 and e.xT == 0.72 and "globo_doble_guia_cierra" in CUERPOS["globo"].trims
    assert "dos puntos de guiado" in e.nota
    assert Dimensionamiento([], 22120, "globo_doble_guia_superior").trim == "globo_doble_guia_abre"
    d = Dimensionamiento([], 22120, "globo_contorneado_iso_abre", caracteristica="lineal")
    assert d.caracteristica == "isoporcentual"
    d = Dimensionamiento([], 22120, "globo_jaula_4v_fuera", caracteristica="lineal")
    assert d.caracteristica == "lineal"


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_gui_gas_natural_y_caracteristica(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w.show()
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("contorneado"))   # v0.12.0: característica libre
    assert w.cb_caract.isEnabled()
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("doble_guia"))
    assert w.cb_caract.isEnabled() and w.trim_clave() == "globo_doble_guia_abre"
    assert w.cb_trim.currentText() == "Doble guía de vástago - superior"
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData("gas"))
    assert w.ed_comp_gn.isHidden()
    w.cb_fluido.setCurrentText("Gas natural")
    assert not w.ed_comp_gn.isHidden() and "kg/kmol" in w.lbl_comp_gn.text()
    F = w.filas
    F["caudal"].edits[1].setText("20000")
    F["P1"].elegir("bar a", convertir=False)
    F["P2"].elegir("bar a", convertir=False)
    F["P1"].edits[1].setText("70")
    F["P2"].edits[1].setText("20")
    F["T1"].edits[1].setText("27")
    w.calcular_propiedades()
    assert F["Z1"].edits[1].text().startswith("0,85") or F["Z1"].edits[1].text().startswith("0,86")
    est = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(est)
    assert w2.ed_comp_gn.text() == w.ed_comp_gn.text()
