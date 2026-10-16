"""Prueba de humo de la interfaz (se omite si no hay PySide6 o librerías gráficas)."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_calculo_desde_la_interfaz(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w.cb_fluido.setCurrentText("Agua / vapor de agua")
    for k, v in {"caudal": "90", "P1": "22", "P2": "7", "T1": "127"}.items():
        w.filas[k].edits[2].setText(v)
    w.chk_caso[1].setChecked(False)
    w.calcular()
    assert w.informe is not None
    assert w.informe.casos[0].resultado.Cv > 0
    assert w.lista_alertas.topLevelItemCount() > 0
    # Cambio de sistema de unidades: los valores se convierten, el resultado no cambia
    cv = w.informe.casos[0].resultado.Cv
    w.aplicar_sistema("Imperial")
    w.calcular()
    assert w.informe.casos[0].resultado.Cv == pytest.approx(cv, rel=1e-4)
