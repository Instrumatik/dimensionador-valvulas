"""Validación contra los ejemplos resueltos del Anexo de IEC 60534-2-1:2011."""
import math

import pytest

from dimensionador.iec60534_2_1 import (Gas, Liquido, Valvula, caudal_gas, caudal_liquido,
                                        dimensionar_gas, dimensionar_liquido)
from dimensionador.modelos import ErrorDatos

AGUA_90C = dict(P1=680, P2=220, T1=363, rho1=0.965 * 999.1, Pv=70.1, Pc=22120, nu=3.26e-7)


def test_ejemplo1_liquido_turbulento_no_critico():
    # Globo, obturador parabólico, flujo tiende a abrir: FL=0,90 Fd=0,46, DN150
    r = dimensionar_liquido(Liquido(Q=360, **AGUA_90C), Valvula(FL=0.90, xT=0.75, Fd=0.46, d_mm=150))
    assert r.extra["FF"] == pytest.approx(0.944, abs=5e-4)
    assert r.extra["dPchoked"] == pytest.approx(497, rel=2e-3)
    assert not r.bloqueado
    assert r.Kv == pytest.approx(165, rel=3e-3)
    assert r.Rev == pytest.approx(2.967e6, rel=3e-3)
    assert r.regimen == "turbulento"


def test_ejemplo2_liquido_critico():
    # Bola segmentada: FL=0,60 Fd=0,98, DN100
    r = dimensionar_liquido(Liquido(Q=360, **AGUA_90C), Valvula(FL=0.60, xT=0.30, Fd=0.98, d_mm=100))
    assert r.bloqueado
    assert r.Kv == pytest.approx(238, rel=3e-3)


def test_ejemplo3_gas_no_critico():
    # CO2, válvula rotativa de obturador excéntrico: FL=0,85 xT=0,60 Fd=0,42, DN100
    g = Gas(P1=680, P2=310, T1=433, M=44.01, gamma=1.30, Z=0.988, mu=1.59e-5, QN=3800)
    r = dimensionar_gas(g, Valvula(FL=0.85, xT=0.60, Fd=0.42, d_mm=100))
    assert r.extra["Fgamma"] == pytest.approx(0.929, abs=5e-4)
    assert r.extra["x"] == pytest.approx(0.544, abs=5e-4)
    assert r.extra["xchoked"] == pytest.approx(0.557, abs=5e-4)
    assert r.extra["Y"] == pytest.approx(0.674, abs=1e-3)
    assert not r.bloqueado
    assert r.Kv == pytest.approx(62.7, rel=3e-3)


def test_gas_critico_usa_Y_0667():
    g = Gas(P1=680, P2=150, T1=433, M=44.01, gamma=1.30, Z=0.988, mu=1.59e-5, QN=3800)
    r = dimensionar_gas(g, Valvula(FL=0.85, xT=0.60, Fd=0.42, d_mm=100))
    assert r.bloqueado
    assert r.extra["Y"] == pytest.approx(2 / 3, abs=1e-9)


def test_reductores_aumentan_kv_y_consistencia_inversa():
    f = Liquido(Q=360, **AGUA_90C)
    sin = dimensionar_liquido(f, Valvula(FL=0.9, xT=0.75, Fd=0.46, d_mm=100))
    v = Valvula(FL=0.9, xT=0.75, Fd=0.46, d_mm=100, D1_mm=150, D2_mm=150)
    con = dimensionar_liquido(f, v)
    assert con.FP < 1 and con.Kv > sin.Kv
    # El caudal que pasa el Kv calculado debe ser el caudal de diseño
    assert caudal_liquido(con.Kv, f, v) == pytest.approx(360, rel=1e-6)


def test_gas_reductores_inverso():
    g = Gas(P1=680, P2=310, T1=433, M=44.01, gamma=1.30, Z=0.988, mu=1.59e-5, W=7000)
    v = Valvula(FL=0.85, xT=0.60, Fd=0.42, d_mm=80, D1_mm=150, D2_mm=150)
    r = dimensionar_gas(g, v)
    assert r.FP < 1
    assert caudal_gas(r.Kv, g, v) == pytest.approx(7000, rel=1e-6)


def test_liquido_viscoso_no_turbulento():
    # Aceite muy viscoso, caudal bajo: debe resultar FR < 1 y Kv mayor que el turbulento
    f = Liquido(Q=2.0, P1=500, P2=400, T1=300, rho1=900, Pv=1, Pc=2000, nu=5e-3)
    r = dimensionar_liquido(f, Valvula(FL=0.9, xT=0.7, Fd=0.46, d_mm=80))
    assert r.Rev < 10000
    assert r.FR < 1
    turb = 2.0 / 0.1 * math.sqrt(900 / 999.1 / 100)
    assert r.Kv == pytest.approx(turb / r.FR, rel=1e-6)


def test_datos_invalidos():
    with pytest.raises(ErrorDatos) as e:
        dimensionar_liquido(Liquido(Q=10, P1=300, P2=400, T1=300, rho1=1000, Pv=3, Pc=22000, nu=1e-6),
                            Valvula(FL=0.9, xT=0.7, Fd=0.46, d_mm=50))
    assert any(a.codigo == "dato_dp" for a in e.value.alertas)


def test_bifasico_limites():
    from dimensionador.iec60534_2_1 import Bifasico, dimensionar_bifasico
    v = Valvula(FL=0.9, xT=0.72, Fd=0.46, d_mm=100)
    base = dict(P1=1000, P2=600, T1=453, W=20000, rho_l=887, rho_g=5.15, Pv=1000 * 0.999, Pc=22064, gamma=1.3)
    # Con fracción de gas muy chica tiende al resultado de líquido; con casi 1 al de gas
    casi_liq = dimensionar_bifasico(Bifasico(xg=1e-6, **base), v)
    liq = dimensionar_liquido(Liquido(W=20000, P1=1000, P2=600, T1=453, rho1=887, Pv=999, Pc=22064, nu=1.7e-7), v)
    assert casi_liq.Kv == pytest.approx(liq.Kv, rel=1e-3)
    casi_gas = dimensionar_bifasico(Bifasico(xg=1 - 1e-6, **base), v)
    gas = dimensionar_gas(Gas(W=20000, P1=1000, P2=600, T1=453, M=18.015, gamma=1.3, Z=1, mu=1.5e-5, rho1=5.15), v)
    assert casi_gas.Kv == pytest.approx(gas.Kv, rel=1e-3)
    medio = dimensionar_bifasico(Bifasico(xg=0.1, **base), v)
    assert liq.Kv < medio.Kv < gas.Kv
