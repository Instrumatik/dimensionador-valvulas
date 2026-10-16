import pytest

from dimensionador import propiedades as pr
from dimensionador.estilos import ESTILOS, apertura_requerida
from dimensionador.fenomenos import velocidad_erosional_api14e, xFz_tipico
from dimensionador.iec60534_2_1 import Gas, Liquido
from dimensionador.servicio import Caso, Seleccion, dimensionar


def _agua(P1, P2, T, Q):
    p = pr.liquido("Agua / vapor de agua", P1, T)
    return Liquido(Q=Q, P1=P1, P2=P2, T1=T, rho1=p.rho, Pv=p.Pv, Pc=p.Pc, nu=p.nu)


def codigos(informe):
    return {a.codigo for _, a in informe.todas_las_alertas()}


def test_api14e_formula():
    # 100/√(62,4 lb/ft³) = 12,66 ft/s = 3,86 m/s
    assert velocidad_erosional_api14e(999.5) == pytest.approx(12.66 * 0.3048, rel=2e-3)


def test_xfz_rango():
    x = xFz_tipico(100, 0.9, 0.46)
    assert 0.2 < x < 0.9


def test_apertura_caracteristicas():
    assert apertura_requerida(1.0, "isoporcentual", 50) == pytest.approx(1.0)
    assert apertura_requerida(1 / 50, "isoporcentual", 50) == pytest.approx(0.0, abs=1e-12)
    assert apertura_requerida(0.5, "lineal", 50) == pytest.approx((0.5 - 0.02) / 0.98)


def test_sin_cavitacion():
    inf = dimensionar([Caso("Máximo", _agua(500, 450, 300, 50))],
                      Seleccion(ESTILOS["globo_contorneado_iso_abre"]))
    assert "cavitacion" not in codigos(inf) and "flashing" not in codigos(inf)
    assert inf.casos[0].apertura <= 0.85


def test_cavitacion_detectada():
    inf = dimensionar([Caso("Máximo", _agua(1500, 400, 330, 50))],
                      Seleccion(ESTILOS["mariposa_concentrica_70"], D1_mm=154.05, D2_mm=154.05))
    a = [a for _, a in inf.todas_las_alertas() if a.codigo == "cavitacion"]
    assert a and a[0].intensidad > 0 and a[0].remedios


def test_flashing_agua_caliente():
    caso = Caso("Máximo", _agua(1000, 200, 450, 20), fluido="Agua / vapor de agua")
    inf = dimensionar([caso], Seleccion(ESTILOS["angular_contorneado_cierra"], D2_mm=154.05))
    assert "flashing" in codigos(inf)
    assert inf.casos[0].resultado.bloqueado
    assert 0 < inf.casos[0].datos["calidad_salida"] < 0.2


def test_vapor_de_agua_y_seleccion():
    p = pr.gas("Agua / vapor de agua", 1000, 473.15)
    g = Gas(P1=1000, P2=600, T1=473.15, M=p.M, gamma=p.gamma, Z=p.Z, mu=p.mu, W=5000, rho1=p.rho)
    inf = dimensionar([Caso("Normal", g), Caso("Máximo", Gas(**{**g.__dict__, "W": 8000}))],
                      Seleccion(ESTILOS["globo_jaula_4v_fuera"], D1_mm=154.05, D2_mm=202.72))
    assert inf.casos[1].apertura > inf.casos[0].apertura
    assert inf.casos[1].apertura <= 0.85


def test_vapor_saturado():
    p = pr.gas("Agua / vapor de agua", 1000, None, saturado=True)
    assert p.rho == pytest.approx(5.15, rel=0.01)   # vapor saturado a 10 bar a
