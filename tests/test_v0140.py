"""v0.14.0: pernos y tuercas, 304 / F304 / 316 nitrurado, diafragma rotativo con palanca y sentido de instalación
de las mariposas excéntricas."""
import json
import os
from pathlib import Path

import pytest

from dimensionador import actuadores as A, ayuda, materiales as MT, pernos as PE

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
KIT = Path(__file__).resolve().parents[1] / "kit_workshop" / "casos"


def test_materiales_nuevos_en_biblioteca():
    for k, comp in (("304", "obturador"), ("304", "vastago"), ("F304", "cuerpo"), ("316_NIT", "guia"),
                    ("316_NIT", "vastago")):
        assert comp in MT.MATERIALES[k].componentes
    assert MT.MATERIALES["F304"].grupo == "2.1"
    assert any("No es la opción recomendada" in n for n in MT.MATERIALES["304"].notas)
    for o in list(PE.CUERPO_BONETE.values()) + list(PE.PRENSAEMPAQUES.values()):
        for _, m in o.piezas:
            assert "pernos" in m.componentes
    assert ("Componentes", "Pernos, espárragos y tuercas") in MT.ficha(MT.MATERIALES["B7M"])


def test_opciones_y_alertas_de_pernos():
    assert len(PE.CUERPO_BONETE) == 23 and len(PE.PRENSAEMPAQUES) == 13
    b7 = PE.CUERPO_BONETE["b7_2h"]
    assert PE.alertas(b7, PE.PRENSAEMPAQUES["estandar"], 200, 20, False) == []
    al = PE.alertas(b7, PE.PRENSAEMPAQUES["estandar"], 500, 20, True)
    assert {a.codigo for a in al} == {"pernos_bonete_temperatura", "pernos_bonete_nace"}
    assert PE.alertas(PE.CUERPO_BONETE["b7m_2hm"], PE.PRENSAEMPAQUES["b7m_2hm"], 200, 20, True) == []
    assert PE.nace_ok(PE.CUERPO_BONETE["estandar"]) is None
    assert PE.opcion(PE.CUERPO_BONETE, "SA-193 B7 espárragos / tuercas 2H") is b7


def test_galling_nitrurado():
    from dimensionador.seleccion_materiales import riesgo_galling
    assert riesgo_galling(MT.MATERIALES["316_NIT"], MT.MATERIALES["316"], 100)[0] == "BAJO"


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _caso(w, nombre):
    w._cargar(json.loads((KIT / f"{nombre}.valvula").read_text(encoding="utf-8")))


def test_pernos_en_pantalla_documentos_y_proyecto(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _caso(w, "Caso_C_alta_agua_producida_agria")
    w.cb_pernos["pernos_bonete"].setCurrentIndex(w.cb_pernos["pernos_bonete"].findData("b7_2h"))
    w.cb_pernos["pernos_prensa"].setCurrentIndex(w.cb_pernos["pernos_prensa"].findData("b7m_2hm"))
    w.calcular()
    assert "pernos_bonete_nace" in {a.codigo for _, a in w.res.alertas}
    h = w.vistas["hoja_datos"].toPlainText()
    assert "SA-193 B7 espárragos / tuercas 2H" in h and "SA-193 B7M espárragos / tuercas 2HM, NACE" in h
    w2 = VentanaPrincipal()
    w2._cargar(w._estado())
    assert w2.cb_pernos["pernos_prensa"].currentData() == "b7m_2hm"


def test_sentido_de_instalacion_mariposa_excentrica(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _caso(w, "Caso_A_baja_agua_enfriamiento_mariposa")
    assert w.cb_cuerpo.currentData() in ("mariposa_doble", "mariposa_triple")
    assert w.cb_sentido.isEnabled() and w.cb_sentido.count() == 2
    w.calcular()
    cv = w.res.salidas[0]["Cv"]
    assert "Flow to open" in w.vistas["hoja_datos"].toPlainText()
    w.cb_sentido.setCurrentIndex(w.cb_sentido.findData("cierra"))
    w.calcular()
    assert w.res.salidas[0]["Cv"] == pytest.approx(cv) and "Flow to close" in w.vistas["hoja_datos"].toPlainText()
    w.cb_cuerpo.setCurrentIndex(w.cb_cuerpo.findData("mariposa"))
    assert w.cb_sentido.currentText() == "No aplica" and not w.cb_sentido.isEnabled()


@pytest.mark.parametrize("falla", [A.FC, A.FO])
def test_diafragma_rotativo_con_palanca(app, falla):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    _caso(w, "Caso_A_baja_agua_enfriamiento_mariposa")
    w.eq_w["act_tipo"].setCurrentText(A.PALANCA)
    w.eq_w["act_falla"].setCurrentText(falla)
    w.calcular()
    a = w.res.equipo.actuador
    assert a.ok and a.seleccion.startswith(A.PALANCA) and a.resorte and a.P_banco
    assert a.P_req_psig <= a.P_disp_psig + 1e-9
    assert "act_incompatible" not in {x.codigo for x in a.alertas}
    assert A.par_palanca(45) == pytest.approx(1) and A.par_palanca(0) == pytest.approx(0.7071, abs=1e-4)
    assert A.carrera_palanca(0) == 0 and A.carrera_palanca(90) == pytest.approx(1)


def test_palanca_bloqueada_en_globo():
    assert A.PALANCA in A.tipos_bloqueados(False) and A.PALANCA not in A.tipos_bloqueados(True)


def test_ayuda_nombres_de_mariposas():
    h = ayuda.html("estilo_cuerpo")
    assert "disco excéntrico con offset" in h and "High Performance Butterfly" in h and "fabricante" in h
