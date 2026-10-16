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
    assert all(cv) and cv[2].startswith("157")
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
