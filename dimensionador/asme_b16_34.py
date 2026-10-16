"""Clases de presión-temperatura ASME B16.34 (clase estándar) y materiales ASTM.

Los valores de las tablas son presiones de trabajo máximas en bar
manométricos para válvulas de clase estándar. Deben verificarse contra la
edición vigente de ASME B16.34 que use el proyecto; el archivo de datos es
editable para actualizarlos.

Grupos incluidos:
  1.1  Acero al carbono: ASTM A216 WCB (fundición), A105 (forja), A350 LF2*, A515 70, A516 70
  2.2  Acero inoxidable 316: ASTM A351 CF8M y CF3M (fundición), A182 F316 (forja)
"""
from __future__ import annotations

from dataclasses import dataclass

from .modelos import Alerta, Severidad, _n

TEMPERATURAS_C = [38, 50, 100, 150, 200, 250, 300, 325, 350, 375, 400, 425, 450, 475, 500, 538]
CLASES = [150, 300, 600, 900, 1500, 2500]

TABLAS = {
    "1.1": {
        150: [19.6, 19.2, 17.7, 15.8, 13.8, 12.1, 10.2, 9.3, 8.4, 7.4, 6.5, 5.5, 4.6, 3.7, 2.8, 1.4],
        300: [51.1, 50.1, 46.6, 45.1, 43.8, 41.9, 39.8, 38.7, 37.6, 36.4, 34.7, 28.8, 23.0, 17.4, 11.8, 5.9],
        600: [102.1, 100.2, 93.2, 90.2, 87.6, 83.9, 79.6, 77.4, 75.1, 72.7, 69.4, 57.5, 46.0, 34.9, 23.5, 11.8],
        900: [153.2, 150.4, 139.8, 135.2, 131.4, 125.8, 119.5, 116.1, 112.7, 109.1, 104.2, 86.3, 69.0, 52.3, 35.3, 17.7],
        1500: [255.3, 250.6, 233.0, 225.4, 219.0, 209.7, 199.1, 193.6, 187.8, 181.8, 173.6, 143.8, 115.0, 87.2, 58.8, 29.5],
        2500: [425.5, 417.7, 388.3, 375.6, 365.0, 349.5, 331.8, 322.6, 313.0, 303.1, 289.3, 239.7, 191.7, 145.3, 97.9, 49.2],
    },
    "2.2": {
        150: [19.0, 18.4, 16.2, 14.8, 13.7, 12.1, 10.2, 9.3, 8.4, 7.4, 6.5, 5.5, 4.6, 3.7, 2.8, 1.4],
        300: [49.6, 48.1, 42.2, 38.5, 35.7, 33.4, 31.6, 30.9, 30.3, 29.9, 29.4, 29.1, 28.8, 28.7, 28.2, 25.2],
        600: [99.3, 96.2, 84.4, 77.0, 71.3, 66.8, 63.2, 61.8, 60.7, 59.8, 58.9, 58.3, 57.7, 57.3, 56.5, 50.0],
        900: [148.9, 144.3, 126.6, 115.5, 107.0, 100.1, 94.9, 92.7, 91.0, 89.6, 88.3, 87.4, 86.6, 85.9, 84.7, 75.2],
        1500: [248.2, 240.6, 211.0, 192.5, 178.3, 166.9, 158.1, 154.4, 151.6, 149.4, 147.2, 145.7, 144.3, 143.2, 140.9, 125.5],
        2500: [413.7, 400.9, 351.6, 320.8, 297.2, 278.1, 263.5, 257.4, 252.7, 249.0, 245.3, 242.9, 240.5, 238.7, 235.0, 208.9],
    },
}


@dataclass(frozen=True)
class Material:
    clave: str
    nombre: str
    grupo: str
    T_min_C: float      # temperatura mínima de uso sin requisitos adicionales
    T_max_C: float      # máximo de la tabla incluida
    nota: str = ""


MATERIALES = {m.clave: m for m in [
    Material("WCB", "ASTM A216 WCB (acero al carbono fundido)", "1.1", -29, 538,
             "Uso prolongado por encima de 425 °C: riesgo de grafitización."),
    Material("A105", "ASTM A105 (acero al carbono forjado)", "1.1", -29, 538,
             "Uso prolongado por encima de 425 °C: riesgo de grafitización."),
    Material("CF8M", "ASTM A351 CF8M (inoxidable 316 fundido)", "2.2", -196, 538),
    Material("F316", "ASTM A182 F316 (inoxidable 316 forjado)", "2.2", -196, 538),
]}


def rating(grupo: str, clase: int, T_C: float) -> float | None:
    """Presión máxima de trabajo [bar g] a la temperatura dada (interpolación lineal)."""
    fila = TABLAS[grupo][clase]
    if T_C <= TEMPERATURAS_C[0]:
        return fila[0]
    if T_C > TEMPERATURAS_C[-1]:
        return None
    for (t0, p0), (t1, p1) in zip(zip(TEMPERATURAS_C, fila), zip(TEMPERATURAS_C[1:], fila[1:])):
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
    if m.grupo == "1.1" and T_max_C > 425:
        alertas.append(Alerta(
            "grafitizacion", Severidad.ADVERTENCIA, "Riesgo de grafitización del acero al carbono",
            "Con exposición prolongada por encima de 425 °C la fase carburo del acero al carbono puede "
            "convertirse en grafito y perder resistencia.",
            remedios=["Para servicio continuo a esta temperatura especificar ASTM A217 WC6 o WC9."],
            referencia="ASME B16.34, notas de la Tabla 2-1.1"))
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
