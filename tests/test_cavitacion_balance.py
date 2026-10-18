"""Cavitación incipiente (xFz) frente a Kc, y obturador balanceado o desbalanceado."""
import pytest

from dimensionador.estilos import ESTILOS, NOMBRES_ANTERIORES
from dimensionador.proyecto import (CasoCierre, CasoLiquido, Dimensionamiento, Identificacion,
                                    Instalacion, calcular, fuerza_desbalance)


def _calc(Kc=0.65, balanceado=None, cierre="ANSI Clase IV", trim="globo_contorneado_iso_abre",
          P2=550, dP_cierre=None, cuerpo="globo"):
    c = CasoLiquido("Máximo", 180, None, 1100, P2, 313.15, 0.992, 6.5e-4, 7.4, FL=0.9, Fd=0.46, Kc=Kc)
    ci = CasoCierre("Tight Shutoff", 101.325 + dP_cierre, 101.325) if dP_cierre else None
    dim = Dimensionamiento([c], 22064, trim, nps_valvula=4, cierre=ci, balanceado=balanceado)
    return calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6, cierre=cierre, cuerpo=cuerpo), dim)


def _codigos(r):
    return {a.codigo for _, a in r.alertas}


def test_incipiente_sin_alerta_de_cavitacion():
    r = _calc()
    s = r.salidas[0]
    assert s["xFzp1"] < s["Kapp"] < s["Kc"]
    assert s["condicion"] == "cavitación incipiente"
    assert "cavitacion_incipiente" in _codigos(r) and "cavitacion" not in _codigos(r)
    assert s["dPinc"] == pytest.approx(s["xFzp1"] * (1100 - 7.4))


def test_ruido_usa_el_kc_del_trim():
    con_kc, sin_kc = _calc(), _calc(Kc=None)
    assert sin_kc.salidas[0]["Kc_estimado"] and not con_kc.salidas[0]["Kc_estimado"]
    # con Kc el ruido no suma cavitación por debajo de Kc; sin Kc usa el xFz típico (conservador)
    assert sin_kc.salidas[0]["Lp"] - con_kc.salidas[0]["Lp"] > 15


def test_kc_superado_da_alerta_de_cavitacion():
    r = _calc(Kc=0.4)
    assert "cavitacion" in _codigos(r) and "cavitacion_incipiente" not in _codigos(r)


def test_multietapa_sin_xfz_usa_kc():
    r = _calc(Kc=0.95, trim="globo_multietapa")
    assert r.salidas[0]["xFzp1"] == pytest.approx(r.salidas[0]["Kc"])


def test_desbalanceado_con_dp_alta():
    r = _calc(balanceado=False, dP_cierre=2000)
    assert "desbalance_fuerza" in _codigos(r)
    assert fuerza_desbalance(2000, 4) == pytest.approx(2e6 * 3.14159265 / 4 * 0.1016 ** 2, rel=1e-6)
    assert "desbalanceado (elegido)" in dict(r.recomendaciones)["Tipo de guía y obturador"]


def test_balanceado_avisos():
    r = _calc(balanceado=True, cierre="ANSI Clase V")
    assert {"balance_sin_jaula", "balance_cierre"} <= _codigos(r)
    r = _calc(balanceado=True, trim="globo_jaula_4v_fuera")
    assert not {"balance_sin_jaula", "balance_cierre", "desbalance_fuerza"} & _codigos(r)


def test_nombres_anteriores_de_la_jaula():
    for viejo, clave in NOMBRES_ANTERIORES.items():
        assert clave in ESTILOS and ESTILOS[clave].nombre != viejo
    assert "de adentro hacia afuera" in ESTILOS["globo_jaula_4v_fuera"].nombre
