"""Validación del ruido contra los ejemplos resueltos de IEC 60534-8-3 y 8-4.

Valores de referencia: ejemplos de las normas según los reproduce la
biblioteca «fluids» (que informa coincidencia con todos los decimales dados).
"""
import pytest

from dimensionador.ruido import ruido_gas, ruido_liquido

KV90 = 90 * 0.865


@pytest.mark.parametrize("m,P2,Cv,d,Di,esperado", [
    (2.22, 720, 90, 0.1, 0.2031, 91.67631681476502),
    (2.29, 690, 90, 0.1, 0.2031, 92.80027236454005),
    (2.59, 480, 90, 0.1, 0.2031, 97.65988432967984),
    (1.18, 420, 40, 0.2031, 0.2031, 94.16189978031449),
    (1.19, 50, 40, 0.2031, 0.2031, 97.48317214321824),
    (0.89, 50, 30, 0.1, 0.15, 93.38835049261132),
])
def test_ruido_gas_iec_60534_8_3(m, P2, Cv, d, Di, esperado):
    r = ruido_gas(m, 1000, P2, 450, 5.3, 1.22, 19.8, Cv * 0.865, d, Di, 0.008, 0.2959450058448346,
                  0.792 / 0.98, rho_pared=8000.0, c_aire=343.0, An=-3.8, Stp=0.2)
    assert r["LpAe1m"] == pytest.approx(esperado, abs=0.01)


@pytest.mark.parametrize("m,P2,xFz,esperado", [
    (30, 800, None, 65.47210071692108),
    (40, 650, None, 81.58199982219298),
    (40, 650, 0.254340899267 + 0.1, 69.93930269695811),
])
def test_ruido_liquido_iec_60534_8_4(m, P2, xFz, esperado):
    r = ruido_liquido(m, 1000, P2, 2.32, 997.0, 1400.0, KV90, 0.1, 0.1071, 0.0036, 0.92, 0.42,
                      rho_aire=1.293, xFz=xFz, An=-4.6)
    assert r["LpAe1m"] == pytest.approx(esperado, abs=0.01)
