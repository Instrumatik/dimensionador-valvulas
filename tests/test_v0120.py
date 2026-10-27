"""v0.12.0: tabla de capacidad (Cv, puerto y carrera), estilo/sentido/característica y coherencia."""
import os
from dataclasses import replace

import pytest

from dimensionador import capacidad as CAP, quimica, seleccion_materiales as SM
from dimensionador.estilos import CLAVES_ANTERIORES, CUERPOS, ESTILOS, geometria_sentido, kv_nominal
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_tabla_de_capacidad_pleno():
    assert CAP.pleno("jaula", 6).Cv == pytest.approx(394, rel=0.02)
    assert CAP.pleno("jaula", 8).Cv == pytest.approx(585, rel=0.02)
    assert CAP.pleno("contorneado", 8).Cv == pytest.approx(640, rel=0.02)
    assert CAP.pleno("orificios", 3).Cv == pytest.approx(95, rel=0.03)
    assert CAP.pleno("multietapa", 3).Cv == pytest.approx(70, rel=0.03)
    # característica: el Cv cambia según la familia; el sentido de flujo no cambia el Cv
    assert CAP.pleno("contorneado", 4, "isoporcentual").Cv == pytest.approx(CAP.pleno("contorneado", 4).Cv)
    assert CAP.pleno("jaula", 4, "isoporcentual").Cv == pytest.approx(0.89 * CAP.pleno("jaula", 4).Cv, rel=0.01)
    # interpolación monótona entre tamaños
    cvs = [CAP.pleno("jaula", n).Cv for n in (2, 3, 4, 6, 8, 10)]
    assert cvs == sorted(cvs)


def test_trim_reducido_modelo_en_serie():
    # Ejemplo de Andrea: jaula de 3" con puerto 2 5/16" y carrera 1 1/8"
    cv = CAP.cv_geometria("jaula", 3, 2.3125, 1.125)
    assert cv == pytest.approx(66.8, rel=0.03)
    co = CAP.coherencia("jaula", 3, "lineal", 2.3125, 1.125, 102)
    assert not co.coherente and co.dentro_de_banda          # +53 %, pero dentro de la dispersión
    assert CAP.coherencia("jaula", 3, "lineal", 2.3125, 1.125, 250).dentro_de_banda is False
    # el Cv del reducido nunca supera el del pleno y el puerto para un Cv es la inversa
    assert CAP.cv_geometria("jaula", 3, 3.4375, 3.0) <= CAP.pleno("jaula", 3).Cv * 1.001
    assert CAP.cv_geometria("contorneado", 4, CAP.puerto_para_cv("contorneado", 4, 80)) == pytest.approx(80, rel=0.05)


def test_kv_nominal_usa_la_tabla():
    e = ESTILOS["globo_jaula_4v_fuera"]
    assert e.familia_cv == "jaula"
    car = e.caracteristica
    assert kv_nominal(e, 6) / 0.865 == pytest.approx(CAP.pleno("jaula", 6, car).Cv, rel=0.01)
    assert kv_nominal(ESTILOS["globo_contorneado_abre"], 8) / 0.865 == pytest.approx(
        CAP.pleno("contorneado", 8, ESTILOS["globo_contorneado_abre"].caracteristica).Cv, rel=0.01)


def test_claves_anteriores_se_migran():
    for vieja, (nueva, car) in CLAVES_ANTERIORES.items():
        d = Dimensionamiento([], 22120, vieja, caracteristica="apertura_rapida")
        nueva = nueva.replace("doble_guia", "contorneado")      # v0.13.0: la doble guía es una guía
        assert d.trim == nueva and (car is None or d.caracteristica == car)
    assert geometria_sentido("globo_jaula_4v_dentro") == ("jaula_4v", "cierra")
    assert Dimensionamiento([], 22120, "globo_jaula_4v_fuera").sentido == "abre"
    for c in CUERPOS.values():
        assert all(k in ESTILOS for k in c.trims)


def _caso(Q=60):
    return CasoLiquido("Máximo", Q, None, 680, 220, 363, 0.965, 3.26e-7 * 0.965 * 999.1, 70.1)


def test_alerta_de_coherencia():
    ident, inst = Identificacion(), Instalacion(nps_entrada=3, nps_salida=3)
    dim = Dimensionamiento([_caso()], 22120, "globo_jaula_4v_fuera", nps_valvula=3, caracteristica="lineal",
                           puerto_mm=2.3125 * 25.4, carrera_mm=1.125 * 25.4)
    sin = calcular(ident, inst, dim)
    assert not any(a.codigo == "coherencia_trim" for _, a in sin.alertas)
    info = calcular(ident, inst, replace(dim, Cv_reducido_cert=102))
    al = [a for _, a in info.alertas if a.codigo == "coherencia_trim"]
    assert al and al[0].severidad.name == "INFO"
    adv = calcular(ident, inst, replace(dim, Cv_reducido_cert=20))
    al = [a for _, a in adv.alertas if a.codigo == "coherencia_trim"]
    assert al and al[0].severidad.name == "ADVERTENCIA"


def test_geometria_ligada_al_cv():
    ident, inst = Identificacion(), Instalacion(nps_entrada=3, nps_salida=3)
    dim = Dimensionamiento([_caso()], 22120, "globo_jaula_4v_fuera", nps_valvula=3, caracteristica="lineal")
    pl = calcular(ident, inst, dim)
    assert pl.geometria.puerto_in == pytest.approx(CAP.pleno("jaula", 3).puerto_in, abs=1 / 16)
    red = calcular(ident, inst, replace(dim, Cv_nominal=67))
    assert red.geometria.reducido and red.geometria.puerto_in < pl.geometria.puerto_in


def test_sin_cavitacion_es_ninguna():
    assert SM.severidad_cavitacion({"condicion": "Sin cavitación"}) == "ninguna"
    assert SM.severidad_cavitacion({"condicion": "Sin cavitación", "Kapp": 0.2, "FL": 0.9, "Kc": 0.6,
                                    "xFzp1": 0.5}) == "ninguna"


def test_cloruros_sobre_100C_en_austeniticos():
    for m in ("ss304", "ss316", "ss317"):
        assert quimica.nivel_regla("cloruros", m, 30, 80, True) == "A"
        assert quimica.nivel_regla("cloruros", m, 30, 150, True) == "B"


def test_temperatura_de_corrosion_es_la_de_operacion():
    ctx = SM.Contexto.__new__(SM.Contexto)
    ctx.T_max_C, ctx.T_op_C = 300.0, 90.0
    assert ctx.T_corr == 90.0
    ctx.T_op_C = None
    assert ctx.T_corr == 300.0


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_gui_sentido_y_flow(app):
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    w.show()
    w.cb_tipo_trim.setCurrentIndex(w.cb_tipo_trim.findData("jaula"))
    w.cb_trim.setCurrentIndex(w.cb_trim.findData("jaula_4v"))
    w.cb_sentido.setCurrentIndex(w.cb_sentido.findData("cierra"))
    assert w.trim_clave() == "globo_jaula_4v_dentro"
    w._act_concordancia()
    fl = w.eq_w["act_flujo"]
    assert not fl.isEnabled() and "Down" in fl.currentText()
    w.cb_caract.setCurrentIndex(w.cb_caract.findData("apertura_rapida"))
    assert w.cb_caract.isEnabled()
    est = w._estado()
    w2 = VentanaPrincipal()
    w2._cargar(est)
    assert w2.trim_clave() == "globo_jaula_4v_dentro"
