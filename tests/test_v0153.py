"""v0.15.3: bola de paso con orificio en V (V-port), distinta de la bola segmentada."""
import json
import os
from pathlib import Path

import pytest

from dimensionador import actuadores as A, geometria as G, herramientas as H
from dimensionador.estilos import CUERPOS, ESTILOS, KC_TIPICO, NOMBRE_CORTO

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
KIT = Path(__file__).resolve().parents[1] / "kit_workshop" / "casos"


def test_estilos_vport():
    c = CUERPOS["bola_vport"]
    assert c.rotativa and c.trims == ("bola_vport_v90", "bola_vport_v60", "bola_vport_v30")
    for t in c.trims:
        e = ESTILOS[t]
        assert e.caracteristica == "isoporcentual" and t in KC_TIPICO and t in NOMBRE_CORTO
        assert G.rotacion(t) == 90
    for ang in ("90", "60", "30"):                # misma V: menos capacidad, más FL y xT que la segmentada
        seg = ESTILOS["bola_segmentada" if ang == "90" else f"bola_segmentada_v{ang}"]
        vp = ESTILOS[f"bola_vport_v{ang}"]
        assert vp.Cd < seg.Cd and vp.FL > seg.FL and vp.xT > seg.xT
    assert ESTILOS["bola_vport_v30"].Cd < ESTILOS["bola_vport_v60"].Cd < ESTILOS["bola_vport_v90"].Cd
    assert "bola_vport" not in A.BOLAS_BIDIRECCIONALES
    assert {f.clave for f in H.factores_valvula() if f.cuerpo == c.nombre} == set(c.trims)


def test_par_flotante_y_munones():
    chica, grande = A.factores_par("bola_vport", 4, True), A.factores_par("bola_vport", 12, True)
    assert "flotante" in chica.familia and "muñones" in grande.familia
    assert chica.A == pytest.approx(1.5 * A.factores_par("bola_trunnion", 4, True).A)


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_calculo_completo_con_vport(app, tmp_path):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w._cargar(json.load(open(KIT / "Caso_A_baja_agua_enfriamiento_mariposa.valvula", encoding="utf-8")))
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("bola_vport"))
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("bola_vport_v60"))
    assert [w.cb_trim.itemData(i) for i in range(w.cb_trim.count())] == list(CUERPOS["bola_vport"].trims)
    w.calcular()
    assert w.res is not None and w.res.equipo.actuador.seleccion
    ruta = tmp_path / "vport.docx"
    w.exportar_word("hoja_datos", str(ruta))
    assert ruta.exists()
