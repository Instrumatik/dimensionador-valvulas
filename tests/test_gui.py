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
