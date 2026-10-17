"""Selección orientativa de trim a partir de Kapp, Kc y FL²."""
import math

from dimensionador import seleccion_trim as ST
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular

PV = 198.7   # agua a 120 °C, kPa a


def _sel(P1, P2, Kc=0.65):
    c = CasoLiquido("Máximo", 50, None, P1, P2, 393.15, 0.943, 2.3e-4, PV, FL=0.9, Fd=0.46, Kc=Kc)
    res = calcular(Identificacion(), Instalacion(nps_entrada=3, nps_salida=3),
                   Dimensionamiento([c], 22064, "globo_contorneado_iso_abre", nps_valvula=3))
    return ST.seleccionar(res)


def test_sin_cavitacion_conserva_el_trim():
    sel = _sel(3100, 2100)          # Kapp ≈ 0,34
    assert sel.etapas == 1 and "contorneado" in sel.trim


def test_cavitacion_moderada_elige_jaula():
    sel = _sel(3100, 1100)          # Kapp ≈ 0,69 → Kc ≥ 0,77
    assert sel.etapas == 1 and "60 orificios" in sel.trim


def test_bloqueado_pide_multietapa_con_etapas():
    sel = _sel(3100, 300)           # Kapp ≈ 0,97
    esperado = math.ceil(math.log((300 - PV) / (3100 - PV)) / math.log(0.5))
    assert "multietapa" in sel.trim and sel.etapas == esperado
    assert any("placa de restricción" in a for a in sel.complementos)


def test_flashing():
    sel = _sel(3100, 150)
    assert "flashing" in sel.trim and "carburo" in sel.materiales
