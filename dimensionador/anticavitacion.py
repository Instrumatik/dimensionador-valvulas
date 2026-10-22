"""Trims anticavitación por número de etapas (líquidos).

Un trim de N etapas reparte la caída de presión en N restricciones en serie. Se adopta el reparto
de igual relación por etapa (la práctica del diseño de multietapas, ver el manual de selección de
trim, 5.4): cada etapa toma la misma fracción k de la presión disponible sobre Pv,

    (P_salida,i − Pv) = (1 − k)·(P_entrada,i − Pv)   →   k = 1 − ((P2 − Pv)/(P1 − Pv))^(1/N)

de modo que las primeras etapas toman la mayor parte de la caída y la última la menor. Como todas
tienen el mismo Kapp por etapa (= k), la etapa que gobierna la cavitación es cualquiera de ellas; la
última define el ruido (IEC 60534-8-4), porque descarga a la tubería y las anteriores quedan
atenuadas dentro del trim.

Con elementos de etapa iguales, los factores equivalentes de la válvula completa son:
    Kc_eq  = 1 − (1 − Kc_e)^N        (Kapp total al que una etapa llega a Kc_e)
    xFz_eq = 1 − (1 − xFz_e)^N
    FL_eq² = 1 − (1 − FL_e²)^N

Valores genéricos de referencia, no de un fabricante: se reemplazan por los certificados del trim
ofertado (FL, Fd y Kc en la tabla de condiciones de operación).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Elemento de etapa de orificios (cada etapa de un multietapa)
XFZ_ETAPA = 0.50     # inicio de cavitación incipiente por etapa
KC_ETAPA = 0.70      # cavitación constante (daño) por etapa
FL_ETAPA = 0.90
MARGEN = 0.9         # Kapp por etapa ≤ 0,9·Kc_e para aceptar cavitación incipiente


@dataclass(frozen=True)
class TrimAnticavitacion:
    clave: str
    nombre: str
    etapas: int
    FL: float
    Fd: float
    Kc: float
    xFz: float | None    # inicio de cavitación incipiente equivalente (None = típico de IEC 60534-8-4)
    Cd: float | None     # Cv nominal / d² [d en pulgadas]; None = el del trim elegido


def _multietapa(n: int, Cd: float) -> TrimAnticavitacion:
    FL = math.sqrt(min(1 - (1 - FL_ETAPA ** 2) ** n, 0.995))
    return TrimAnticavitacion(f"etapas_{n}", f"Multietapa, {n} etapas", n, round(FL, 3), 0.07,
                              round(1 - (1 - KC_ETAPA) ** n, 3), round(1 - (1 - XFZ_ETAPA) ** n, 3), Cd)


TRIMS: dict[str, TrimAnticavitacion] = {t.clave: t for t in [
    TrimAnticavitacion("estandar", "Estándar (trim elegido, 1 etapa)", 1, 0, 0, 0, None, None),
    TrimAnticavitacion("jaula_1", "Jaula de orificios chicos, 1 etapa", 1, 0.93, 0.10, 0.85, None, 7.0),
    _multietapa(2, 5.0),
    _multietapa(3, 4.0),
    _multietapa(4, 3.5),
    _multietapa(6, 2.8),
]}
ETAPAS_DISPONIBLES = sorted({t.etapas for t in TRIMS.values() if t.clave.startswith("etapas_")})


def k_etapa(P1: float, P2: float, Pv: float, n: int) -> float:
    """Kapp de cada etapa con reparto de igual relación (P en kPa abs; P2 > Pv)."""
    return 1 - ((P2 - Pv) / (P1 - Pv)) ** (1 / n)


def reparto(P1: float, P2: float, Pv: float, n: int) -> list[tuple[float, float, float]]:
    """(P entrada, P salida, ΔP) de cada etapa, de la primera a la última."""
    k = k_etapa(P1, P2, Pv, n)
    out, p = [], P1
    for _ in range(n):
        q = Pv + (1 - k) * (p - Pv)
        out.append((p, q, p - q))
        p = q
    return out


def etapas_para(P1: float, P2: float, Pv: float, k_max: float) -> int:
    """Menor N con Kapp por etapa ≤ k_max."""
    if P2 <= Pv:
        return 0
    return max(1, math.ceil(math.log((P2 - Pv) / (P1 - Pv)) / math.log(1 - k_max) - 1e-9))


def etapas_recomendadas(P1: float, P2: float, Pv: float) -> tuple[int, int]:
    """(N sin cavitación, N mínimo con cavitación incipiente aceptada)."""
    return etapas_para(P1, P2, Pv, XFZ_ETAPA), etapas_para(P1, P2, Pv, MARGEN * KC_ETAPA)


def regimen_etapa(k: float) -> str:
    if k < XFZ_ETAPA:
        return "sin cavitación"
    if k < KC_ETAPA:
        return "cavitación incipiente"
    if k < FL_ETAPA ** 2:
        return "cavitación"
    return "cavitación con bloqueo"


def oferta(n: int) -> int | None:
    """Menor trim de la lista con al menos n etapas (None si ninguno alcanza)."""
    return next((e for e in ETAPAS_DISPONIBLES if e >= n), None)
