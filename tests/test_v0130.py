"""v0.13.0 y v0.13.1: trims sin jaula / con jaula, guía, config dinámica de la jaula y multietapa para gas."""
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
    assert T.obturadores("globo", "puerto") == ["vport"]
    assert "disco_plano" not in T.ELEMENTOS and "jaula_retencion" not in T.ELEMENTOS
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
    assert "apertura_rapida" in T.ELEMENTOS["jaula_4v"].caracteristicas


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
    # Sin jaula: guía y tipo de obturador visibles, jaula y config dinámica ocultas
    assert w.cb_tipo_trim.currentText() == "Sin jaula" and not w.fila_guia[0].isHidden()
    assert w.fila_nivel[0].isHidden() and w.fila_jaula[0].isHidden() and w.lbl_trim.text() == "Tipo de obturador"
    w.cb_guia.setCurrentIndex(w.cb_guia.findData("puerto"))
    assert [w.cb_trim.itemData(i) for i in range(w.cb_trim.count())] == ["vport"]
    # Con jaula: obturador cilíndrico fijo; con jaula estándar la config dinámica queda bloqueada
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData("gas"))
    w.cb_tipo_trim.setCurrentIndex(w.cb_tipo_trim.findData("jaula"))
    assert w.fila_guia[0].isHidden() and w.cb_trim.currentText() == "Cilíndrico" and not w.cb_trim.isEnabled()
    assert [w.cb_jaula.itemData(i) for i in range(w.cb_jaula.count())] == ["estandar", "antiruido"]
    assert not w.cb_nivel.isEnabled() and w.trim_clave() == "globo_jaula_4v_fuera"
    # Antiruido: todas las construcciones y niveles, de la más simple a la más compleja
    w.cb_jaula.setCurrentIndex(w.cb_jaula.findData("antiruido"))
    datos = [w.cb_nivel.itemData(i) for i in range(w.cb_nivel.count())]
    assert w.cb_nivel.isEnabled() and datos[0] == "jaula_multiorificio|multiorificio_1"
    assert datos[-1] == "jaula_discos|discos_10" and len(datos) == 10
    w.cb_nivel.setCurrentIndex(w.cb_nivel.findData("jaula_multietapa_gas|multietapa_3"))
    assert w.trim_especial() == ("estandar", "multietapa_3")
    assert w.filas["xT"].edits[0].text() == "0,967"
    # Con líquido: anticavitación en lugar de antiruido
    w.cb_tipo_fluido.setCurrentIndex(w.cb_tipo_fluido.findData("liquido"))
    assert w.cb_jaula.findData("antiruido") < 0 and w.cb_jaula.findData("anticav") >= 0
    w.cb_jaula.setCurrentIndex(w.cb_jaula.findData("anticav"))
    datos = [w.cb_nivel.itemData(i) for i in range(w.cb_nivel.count())]
    assert datos[:3] == ["jaula_anticav|jaula_1", "jaula_anticav|etapas_2", "jaula_pasajes|pasajes_2"]


def test_gui_proyecto_v012_se_migra(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    s = json.loads((KIT / "Caso_C_alta_agua_producida_agria.valvula").read_text(encoding="utf-8"))
    s["campos"].pop("tipo_trim", None)
    s["campos"]["trim"] = "Multietapa (anticavitación severa)"     # como lo guardaba v0.12
    s["campos"]["anticav"] = "Multietapa, 4 etapas"
    w = VentanaPrincipal()
    w._cargar(s)
    assert w.cb_tipo_trim.currentData() == "jaula" and w.cb_jaula.currentData() == "anticav"
    assert w.cb_nivel.currentData() == "jaula_anticav|etapas_4" and w.trim_especial() == ("etapas_4", "estandar")
    est = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(est)
    assert w2.trim_clave() == w.trim_clave() and w2.cb_nivel.currentData() == "jaula_anticav|etapas_4"


def test_gui_proyecto_v0130_se_migra(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    s = json.loads((KIT / "Caso_C_alta_agua_producida_agria.valvula").read_text(encoding="utf-8"))
    c = s["campos"]
    for k in ("jaula",):
        c.pop(k, None)
    c.update(tipo_trim="Guiado por jaula", trim="Jaula anticavitación",
             nivel="3 etapas – sin cavitación hasta Kapp 0,875")
    w = VentanaPrincipal()
    w._cargar(s)
    assert w.cb_tipo_trim.currentText() == "Con jaula" and w.cb_nivel.currentData() == "jaula_anticav|etapas_3"
    c.update(tipo_trim="Guiado por obturador", guia="Por el puerto (port guided)", trim="Obturador de disco plano")
    w._cargar(s)
    assert w.cb_tipo_trim.currentText() == "Sin jaula" and w.cb_trim.currentData() == "contorneado"


def test_textos_cortos_de_config_dinamica(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    assert T.texto_config("jaula_anticav", "etapas_3", True) == "Jaula perforada, 3 etapas – s/cav hasta Kapp 0,875"
    assert T.texto_config("jaula_multietapa_gas", "multietapa_3", False) == \
        "Multietapa multiorificio, 3 etapas – at 20 a 30 dB(A)"
    assert "atenuación típica" in T.texto_config("jaula_multiorificio", "multiorificio_2", False, completo=True)
    w = VentanaPrincipal()
    w.cb_tipo_trim.setCurrentIndex(w.cb_tipo_trim.findData("jaula"))
    w.cb_jaula.setCurrentIndex(w.cb_jaula.findData("anticav"))
    assert w.cb_nivel.width() == w.cb_sentido.width()
    fm = w.cb_nivel.fontMetrics()
    assert all(fm.horizontalAdvance(w.cb_nivel.itemText(i)) < w.cb_nivel.width() - 25 for i in range(w.cb_nivel.count()))
    # Proyecto guardado con la redacción de v0.13.1
    assert T.config_desde_texto("globo", True, "Pasajes grandes (sólidos), 4 etapas – sin cavitación hasta Kapp 0,938") \
        == ("jaula_pasajes", "pasajes_4")
    assert T.config_desde_texto("globo", False, "Multiorificio, nivel 2 (≈ 200 orificios) – atenuación típica 10 a "
                                "15 dB(A)") == ("jaula_multiorificio", "multiorificio_2")
