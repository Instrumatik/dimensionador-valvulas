"""v0.14.1: 422, resortes, juntas, O-rings, XTREME, búsqueda sin tildes y ajustes de rotativas."""
import json
import os
from pathlib import Path

import pytest

from dimensionador import materiales as MT, pernos as PE

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
KIT = Path(__file__).resolve().parents[1] / "kit_workshop" / "casos"


def test_materiales_v0141():
    assert {"obturador", "guia", "jaula"} <= MT.MATERIALES["422"].componentes
    assert "resorte" in MT.MATERIALES["301"].componentes and "oring" in MT.MATERIALES["EPDM"].componentes
    assert "junta" in MT.MATERIALES["RPTFE"].componentes and "junta" in MT.MATERIALES["GRAF"].componentes
    assert "asiento" in MT.MATERIALES["XTREME"].componentes
    assert {m.clave for m in MT.buscar("Duplex SS")} >= {"CD3MN", "F51", "2205"}
    assert {m.clave for m in MT.buscar("superduplex")} >= {"CD3MWCuN", "F55", "S32760"}


def test_alertas_de_piezas():
    j, o, r = PE.JUNTAS["ptfe_relleno"], PE.ORINGS["epdm"], PE.RESORTES["301"]
    al = PE.alertas_piezas(j, o, r, 400, 20, True, [("EPDM", "D")])
    assert {a.codigo for a in al} >= {"junta_bonete_temperatura", "orings_temperatura", "orings_quimica",
                                       "resortes_temperatura", "resortes_nace"}
    assert PE.alertas_piezas(PE.JUNTAS["grafito"], PE.ORINGS["estandar"], PE.RESORTES["x750"], 300, 20, True, []) == []


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_desplegables_mismo_ancho_y_descripcion(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    anchos = {cb.width() for cb in w.cb_pernos.values()} | {w.cb_cierre.width()}
    assert len(anchos) == 1
    cb = w.cb_pernos["pernos_bonete"]
    cb.setCurrentIndex(cb.findData("b8m2_8m"))
    assert cb.toolTip().startswith("SA-193 B8M endurecido") and "ASTM A193" in cb.toolTip()


def test_piezas_en_hoja_de_datos(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w._cargar(json.loads((KIT / "Caso_B_media_vapor_sobrecalentado.valvula").read_text(encoding="utf-8")))
    for k, v in (("junta_bonete", "grafito"), ("orings", "epdm"), ("resortes", "301")):
        w.cb_pernos[k].setCurrentIndex(w.cb_pernos[k].findData(v))
    w.calcular()
    h = w.vistas["hoja_datos"].toPlainText()
    assert "Grafito flexible (Grafoil)" in h and "EPDM" in h and "Inoxidable 301 (301 SS)" in h
    w2 = VentanaPrincipal()
    w2._cargar(w._estado())
    assert w2.cb_pernos["resortes"].currentData() == "301"


def test_rotativa_etiquetas_y_disco_incoherente(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w._cargar(json.loads((KIT / "Caso_A_baja_agua_enfriamiento_mariposa.valvula").read_text(encoding="utf-8")))
    assert w.f_puerto.lbl.text().startswith("Diámetro del disco") and not w.f_carrera.edits[0].isEnabled()
    w.f_puerto.elegir("mm", convertir=False)
    w.f_puerto.edits[0].setText("20")
    w.calcular()
    assert "coherencia_disco" in {a.codigo for _, a in w.res.alertas}
    w.f_puerto.edits[0].setText("")
    w.calcular()
    assert "coherencia_disco" not in {a.codigo for _, a in w.res.alertas}
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("globo"))
    assert w.f_puerto.lbl.text().startswith("Tamaño del trim") and w.f_carrera.edits[0].isEnabled()
