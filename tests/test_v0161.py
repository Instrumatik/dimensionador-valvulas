"""v0.16.1: verificación rápida de material (galling con la biblioteca y mecanismos de deterioro)."""
import os

import pytest

from dimensionador import ayuda, materiales as MT, verificacion_material as VM


def _mec(clave, T=60):
    return {f.codigo: f for f in VM.mecanismos(MT.MATERIALES[clave], T)}


def test_todos_los_materiales_se_evaluan():
    for m in MT.MATERIALES.values():
        filas = VM.mecanismos(m, 60)
        assert len(filas) == 23 and all(f.nivel in "ABCD?-" and f.explicacion for f in filas), m.clave
        assert VM.resumen_galling(m, VM.galling(m, 60))


def test_316_frente_a_superduplex():
    a, b = _mec("CF8M"), _mec("CD3MWCuN")
    assert a["M02"].nivel == "B" and b["M02"].nivel == "A"
    assert a["M03"].nivel in "CD" and b["M03"].nivel == "A"
    assert "22 HRC" in a["M04"].limite
    assert _mec("CF8M", 25)["M03"].nivel == "A"


def test_acero_al_carbono_y_temperatura():
    w = _mec("WCB")
    assert w["M06"].nivel in "CD" and w["M03"].nivel == "A" and w["M05"].nivel == "A"
    assert "230 °C" in w["M30"].limite
    assert _mec("WCB", 600)["M21"].nivel == "D"


def test_polimeros_no_aplica():
    e = _mec("EPDM")
    assert e["M04"].nivel == "-" and e["M33"].nivel == "D" and e["M33"].resultado == "No resiste"


def test_galling_316_y_stellite():
    g = {f.material.clave: f.nivel for f in VM.galling(MT.MATERIALES["CF8M"], 60)}
    assert g["316"] == "ALTO" and g["316_ST6"] == "BAJO"
    assert all(f.nivel == "BAJO" for f in VM.galling(MT.MATERIALES["ST6"], 60))
    assert len(VM.galling(MT.MATERIALES["CF8M"], 60, todos=True)) == len(MT.MATERIALES)


def test_ayuda():
    assert ayuda.obtener("verificacion_material")


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_ventana(app):
    from dimensionador.gui import herramientas as GH
    assert "verif_material" in GH.VENTANAS and "verif_material" in dict(GH.HERRAMIENTAS)
    d = GH.VerificacionMaterial(None, "CF8M")
    assert d.t_mec.rowCount() == 23 and d.t_gall.rowCount() > 10
    d.cb_nivel.setCurrentIndex(1)
    assert all(d.t_gall.item(i, 3).text() == "ALTO" for i in range(d.t_gall.rowCount()))
    d.ed_T.setText("abc"); d._mostrar()
    assert d.msg.text()
