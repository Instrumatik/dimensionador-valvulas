"""Clases de presión-temperatura ASME B16.34 (clase estándar) por grupo de material.

Los valores (``datos_b16_34.py``) son presiones de trabajo máximas en bar
manométricos para válvulas de clase estándar, edición 2017, para los 49
grupos de materiales de la norma. Deben verificarse contra la edición
vigente que use el proyecto.

Los materiales y sus límites de temperatura propios están en ``materiales.py``.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import datos_b16_34 as D
from .modelos import Alerta, Severidad, _n

CLASES = D.CLASES
GRUPOS = D.GRUPOS
DESCRIPCION = D.DESCRIPCION
T_BRIDADAS_C = 538          # las válvulas bridadas terminan su rating en 538 °C
TEMPERATURAS_C = GRUPOS["1.1"][0]


def temperaturas(grupo: str) -> list[float]:
    return GRUPOS[grupo][0]


def T_max_tabla(grupo: str) -> float:
    return GRUPOS[grupo][0][-1]


@dataclass(frozen=True)
class Material:
    clave: str
    nombre: str
    grupo: str
    T_min_C: float      # temperatura mínima de uso sin requisitos adicionales
    T_max_C: float      # máximo admitido para el material (norma o práctica)
    nota: str = ""


def _materiales():
    from . import materiales as M
    return {k: Material(k, m.nombre, m.grupo, m.T_min_C, m.T_max_C, m.notas[0] if m.notas else "")
            for k, m in M.MATERIALES.items() if m.grupo}


MATERIALES = _materiales()


def rating(grupo: str, clase: int, T_C: float) -> float | None:
    """Presión máxima de trabajo [bar g] a la temperatura dada (interpolación lineal)."""
    ts, tabla = GRUPOS[grupo]
    fila = tabla[clase]
    if T_C <= ts[0]:
        return fila[0]
    if T_C > ts[-1]:
        return None
    for (t0, p0), (t1, p1) in zip(zip(ts, fila), zip(ts[1:], fila[1:])):
        if t0 <= T_C <= t1:
            return p0 + (p1 - p0) * (T_C - t0) / (t1 - t0)
    return None


def clase_minima(grupo: str, P_barg: float, T_C: float) -> int | None:
    for c in CLASES:
        r = rating(grupo, c, T_C)
        if r is not None and r >= P_barg:
            return c
    return None


def verificar(material: str, clase: int | None, P_barg: float, T_max_C: float,
              T_min_C: float) -> tuple[int | None, float | None, list[Alerta]]:
    """Verifica (o propone) la clase de presión para la presión y temperaturas de diseño."""
    m = MATERIALES[material]
    alertas: list[Alerta] = []
    ref = "ASME B16.34 (clase estándar), Tabla 2-" + m.grupo
    if T_min_C < m.T_min_C:
        alertas.append(Alerta(
            "material_baja_temperatura", Severidad.CRITICA, "Material no apto para la temperatura mínima",
            f"{m.nombre} se usa sin requisitos adicionales hasta {_n(m.T_min_C, 0)} °C y el servicio llega "
            f"a {_n(T_min_C, 0)} °C. Riesgo de fractura frágil.",
            remedios=["Usar acero al carbono para baja temperatura con ensayo de impacto (ASTM A352 LCC o "
                      "LCB en fundición, ASTM A350 LF2 en forja) o acero inoxidable (A351 CF8M)."],
            referencia="ASME B16.34 / ASME B31.3"))
    if T_max_C > m.T_max_C:
        alertas.append(Alerta(
            "material_alta_temperatura", Severidad.CRITICA, "Temperatura fuera de la tabla del material",
            f"La temperatura de diseño ({_n(T_max_C, 0)} °C) supera el rango incluido para {m.nombre} "
            f"({_n(m.T_max_C, 0)} °C).",
            remedios=["Usar aceros aleados al cromo-molibdeno (ASTM A217 WC6 o WC9) o inoxidables, según "
                      "la tabla de ASME B16.34 correspondiente."], referencia=ref))
        return clase, None, alertas
    if m.grupo in ("1.1", "1.2", "1.3", "1.4") and T_max_C > 425:
        alertas.append(Alerta(
            "grafitizacion", Severidad.ADVERTENCIA, "Riesgo de grafitización del acero al carbono",
            "Con exposición prolongada por encima de 425 °C la fase carburo del acero al carbono puede "
            "convertirse en grafito y perder resistencia.",
            remedios=["Para servicio continuo a esta temperatura especificar ASTM A217 WC6 o WC9."],
            referencia="ASME B16.34, notas de la Tabla 2-" + m.grupo))
    if clase is None:
        clase = clase_minima(m.grupo, P_barg, T_max_C)
        if clase is None:
            alertas.append(Alerta("clase_insuficiente", Severidad.CRITICA, "Ninguna clase estándar alcanza",
                                  f"La presión de diseño {_n(P_barg, 1)} bar g a {_n(T_max_C, 0)} °C supera la "
                                  "clase 2500.", referencia=ref))
            return None, None, alertas
    r = rating(m.grupo, clase, T_max_C)
    if r is not None and P_barg > r:
        alertas.append(Alerta(
            "clase_insuficiente", Severidad.CRITICA, f"Clase {clase} insuficiente",
            f"A {_n(T_max_C, 0)} °C la clase {clase} de {m.nombre} admite {_n(r, 1)} bar g y la presión de "
            f"diseño es {_n(P_barg, 1)} bar g.",
            remedios=[f"Usar clase {clase_minima(m.grupo, P_barg, T_max_C) or 'superior'}."], referencia=ref))
    return clase, r, alertas
