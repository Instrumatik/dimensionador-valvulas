"""v0.13.0: trims ordenados por tipo (obturador / jaula), guía, niveles individuales y multietapa para gas."""
import json
import os
from pathlib import Path

import pytest

from dimensionador import anticavitacion as AC, compresible as CG, trims as T
from dimensionador.estilos import ESTILOS, apertura_requerida
from dimensionador.proyecto import (CasoGas, Dimensionamiento, Identificacion, Instalacion, RuidoAerodinamico,
                                    calcular, caudal_relativo)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
KIT = Path(__file__).resolve().parents[1] / "kit_workshop" / "casos"


def test_jaulas_segun_fluido_y_niveles_individuales():
    liq = T.elementos("globo", "jaula", True)
    gas = T.elementos("globo", "jaula", False)
    assert "jaula_anticav" in liq and "jaula_multiorificio" not in liq and "jaula_multietapa_gas" not in liq
    assert "jaula_multiorificio" in gas and "jaula_multietapa_gas" in gas and "jaula_anticav" not in gas
    assert T.niveles("jaula_anticav", True) == ["jaula_1", "etapas_2", "etapas_3", "etapas_4", "etapas_6"]
    assert T.niveles("jaula_multietapa_gas", False) == ["multietapa_2", "multietapa_3", "multietapa_4"]
    # Cada nivel muestra lo que mitiga
    assert "Kapp 0,875" in T.texto_nivel("etapas_3", True)
    assert "dB(A)" in T.texto_nivel("multiorificio_2", False)


def test_guia_filtra_obturadores():
    assert T.obturadores("globo", "puerto") == ["vport", "disco_plano"]
    assert T.obturadores("globo", "bonete") == ["microcaudal", "contorneado"]
    assert "puerto" not in T.guias("angulo")
    for c in T.POR_CUERPO:
        for e in T.POR_CUERPO[c]:
            for sd in T.sentidos(c, e):
                for nv in [""] + T.niveles(e, True) + T.niveles(e, False):
                    assert T.clave_estilo(c, e, sd, nv) in ESTILOS


def _gas(nivel: str, trim: str):
    t = CG.TRIMS_RUIDO[nivel]
    c = CasoGas("d2", 60000, None, 5000, 1000, 288.15, M=17.4, mu=1.1e-5, gamma=1.3, Z1=0.95,
                xT=CG.xT_etapas(t.etapas) if t.etapas > 1 else 0.75, FL=0.9, Fd=t.Fd or 0.41, Z2=0.95)
    inst = Instalacion(nps_entrada=6, nps_salida=10, ruido_permitido=85, rating=600)
    return calcular(Identificacion(), inst, Dimensionamiento([c], None, trim, nps_valvula=6, tipo="gas",
                                                              ruido=RuidoAerodinamico(nivel)))


def test_multietapa_multiorificio_gas():
    base = _gas("estandar", "globo_jaula_4v_fuera").salidas[0]
    me = [_gas(f"multietapa_{n}", "globo_jaula_multietapa_gas_abre") for n in (2, 3, 4)]
    Lp = [r.salidas[0]["Lp"] for r in me]
    assert Lp[0] < base["Lp"] - 10 and Lp[0] > Lp[1] > Lp[2]
    # Más etapas: xT mayor (se estrangula la última) y menos Cv por pulgada
    assert CG.xT_etapas(2) == pytest.approx(0.898, abs=1e-3) and CG.xT_etapas(4) > CG.xT_etapas(3)
    assert me[0].Cv_nominal > me[1].Cv_nominal > me[2].Cv_nominal
    # El ladder de nivel requerido sigue con multietapa y discos apilados
    assert base["nivel_trim"] == "Silenciador o difusor"


def test_guia_por_puerto_avisa_con_dp_alta():
    c = CasoGas("d", 60000, None, 5000, 1000, 288.15, M=17.4, mu=1.1e-5, gamma=1.3, Z1=0.95, xT=0.75, FL=0.9,
                Fd=0.29)
    r = calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=10, rating=600),
                 Dimensionamiento([c], None, "globo_vport_abre", nps_valvula=6, tipo="gas", guia="puerto"))
    assert any(a.codigo == "guia_puerto" for _, a in r.alertas)
    assert "por el puerto" in dict(r.recomendaciones)["Tipo de guía y obturador"]


def test_parabolica_modificada():
    R = 50
    for h in (0.2, 0.5, 0.9):
        phi = caudal_relativo(h, "parabolica", R)
        assert caudal_relativo(h, "isoporcentual", R) < phi < caudal_relativo(h, "lineal", R)
        assert apertura_requerida(phi, "parabolica", R) == pytest.approx(h)
    assert "parabolica" in T.ELEMENTOS["contorneado"].caracteristicas
    assert T.ELEMENTOS["disco_plano"].caracteristicas == ("apertura_rapida",)


def test_microcaudal_limitado_a_2_pulgadas():
    from dimensionador.estilos import CUERPOS
    from dimensionador.proyecto import _tamanos
    assert max(_tamanos(CUERPOS["globo"], ESTILOS["globo_microcaudal_abre"])) == 2.0


def test_migracion_de_claves_viejas():
    el = T.desde_claves("globo", "globo_multietapa", liquido=True)
    assert (el.elemento, el.nivel) == ("jaula_anticav", "etapas_3")
    el = T.desde_claves("globo", "globo_jaula_120_orificios", liquido=False)
    assert (el.elemento, el.nivel) == ("jaula_multiorificio", "multiorificio_1")
    el = T.desde_claves("globo", "globo_jaula_4v_dentro", anticav="etapas_4")
    assert (el.elemento, el.sentido, el.nivel) == ("jaula_anticav", "cierra", "etapas_4")
    assert AC.TRIMS["discos_8"].etapas == 8 and AC.TRIMS["pasajes_2"].Fd == 0.25


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_gui_desplegables_dependientes(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w.show()
    # Guiado por obturador: guía visible, jaulas especiales y nivel ocultos
    assert w.cb_tipo_trim.currentData() == "obturador" and not w.fila_guia[0].isHidden()
    assert w.fila_nivel[0].isHidden()
    w.cb_guia.setCurrentIndex(w.cb_guia.findData("puerto"))
    assert [w.cb_trim.itemData(i) for i in range(w.cb_trim.count())] == ["vport", "disco_plano"]
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("disco_plano"))
    assert w.cb_caract.currentData() == "apertura_rapida" and not w.cb_caract.isEnabled()
    # Guiado por jaula con gas: jaulas de bajo ruido y niveles individuales
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData("gas"))
    w.cb_tipo_trim.setCurrentIndex(w.cb_tipo_trim.findData("jaula"))
    assert w.fila_guia[0].isHidden() and w.cb_trim.findData("jaula_anticav") < 0
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("jaula_multietapa_gas"))
    assert not w.fila_nivel[0].isHidden() and w.cb_nivel.count() == 3
    w.cb_nivel.setCurrentIndex(w.cb_nivel.findData("multietapa_3"))
    assert w.trim_especial() == ("estandar", "multietapa_3")
    assert w.filas["xT"].edits[0].text() == "0,967"
    # Con líquido la misma jaula no está: pasa a las de anticavitación
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData("liquido"))
    assert w.cb_trim.findData("jaula_multietapa_gas") < 0 and w.cb_trim.findData("jaula_anticav") >= 0


def test_gui_proyecto_v012_se_migra(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    s = json.loads((KIT / "Caso_C_alta_agua_producida_agria.valvula").read_text(encoding="utf-8"))
    s["campos"].pop("tipo_trim", None)
    s["campos"]["trim"] = "Multietapa (anticavitación severa)"     # como lo guardaba v0.12
    s["campos"]["anticav"] = "Multietapa, 4 etapas"
    w = VentanaPrincipal()
    w._cargar(s)
    assert w.cb_tipo_trim.currentData() == "jaula" and w.cb_trim.currentData() == "jaula_anticav"
    assert w.cb_nivel.currentData() == "etapas_4" and w.trim_especial() == ("etapas_4", "estandar")
    est = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(est)
    assert w2.trim_clave() == w.trim_clave() and w2.cb_nivel.currentData() == "etapas_4"
