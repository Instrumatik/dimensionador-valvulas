"""v0.13.4: tabla ASME B36.10M / B36.19M completa y área de salida de la válvula automática o manual."""
import json
import math
import os
from pathlib import Path

import pytest

from dimensionador import tuberias as TB

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
KIT = Path(__file__).resolve().parents[1] / "kit_workshop" / "casos"


def test_tabla_completa():
    for n in (0.375, 3.5, 22, 34, 38, 46, 64, 72, 80):
        assert n in TB.NPS and TB.cedulas_de(n)
    assert TB.NPS[0] == 0.125 and TB.NPS[-1] == 80
    # Valores de control de la norma
    assert TB.espesor(2, "XS") == 5.54 and TB.espesor(2, "160") == 8.74
    assert TB.espesor(3.5, "40") == 5.74 and TB.espesor(22, "30") == 12.70
    assert TB.espesor(1, "30") == 2.90 and TB.espesor(16, "40S") == 9.53
    for n in TB.NPS:
        for c in TB.cedulas_de(n):
            assert 0 < TB.diametro_interior(n, c) < TB.OD_MM[n]
    assert TB.area_interior(3, "80") == pytest.approx(math.pi / 4 * 73.66 ** 2)


def test_cedula_inexistente_usa_std():
    assert TB.salida_valvula(3, "20") == (pytest.approx(TB.area_interior(3, "STD")), "STD")
    assert TB.salida_valvula(3, "80")[1] == "80"


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _caso_b(w):
    w._cargar(json.loads((KIT / "Caso_B_media_vapor_sobrecalentado.valvula").read_text(encoding="utf-8")))


def test_area_automatica_y_manual(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _caso_b(w)
    assert w.cb_area_modo.currentData() == "auto" and w.f_area.edits[0].isReadOnly()
    w.calcular()
    s = w.res.salidas[0]
    d = w.res.nps_valvula
    assert s["A_salida"] == pytest.approx(TB.area_interior(d, w.cb_sch["salida"].currentText()))
    assert "Automática" in s["origen_area"] and w.f_area.edits[0].text()
    assert "Automática" in w.vistas["hoja_datos"].toPlainText()
    # Manual: la celda se edita y el área ingresada gobierna el cálculo
    w.cb_area_modo.setCurrentIndex(w.cb_area_modo.findData("manual"))
    assert not w.f_area.edits[0].isReadOnly()
    w.f_area.elegir("mm²", convertir=False)
    w.f_area.edits[0].setText("4000")
    w.calcular()
    assert w.res.salidas[0]["A_salida"] == pytest.approx(4000) and "Manual" in w.res.salidas[0]["origen_area"]
    est = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(est)
    assert w2.cb_area_modo.currentData() == "manual"


def test_liquido_usa_area_de_tabla(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w._cargar(json.loads((KIT / "Caso_C_alta_agua_producida_agria.valvula").read_text(encoding="utf-8")))
    assert not w.f_area.lbl.isHidden()
    w.calcular()
    s = w.res.salidas[-1]
    A = TB.area_interior(w.res.nps_valvula, w.cb_sch["salida"].currentText()) * 1e-6
    assert s["v_valvula"] == pytest.approx(s["Q"] / 3600 / A, rel=1e-6)


def test_proyecto_anterior_con_area_queda_manual(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    s = json.loads((KIT / "Caso_B_media_vapor_sobrecalentado.valvula").read_text(encoding="utf-8"))
    s["campos"].pop("area_modo", None)
    s["filas"]["area_salida"]["valores"] = ["4500"]
    w = VentanaPrincipal()
    w._cargar(s)
    assert w.cb_area_modo.currentData() == "manual" and w.f_area.edits[0].text() == "4500"
