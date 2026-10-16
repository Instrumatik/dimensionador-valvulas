"""Estilos genéricos de válvula y sus factores típicos.

NEUTRALIDAD DE MARCA: estos valores NO corresponden a ningún fabricante.
FL, xT y Fd son los valores típicos a carrera nominal publicados en la
Tabla 2 (Anexo) de IEC 60534-2-1:2011. El coeficiente específico ``Cd``
(Kv nominal / d², con d en pulgadas, pasado a Cv) es un valor
representativo del estilo, útil para preseleccionar el tamaño. El usuario
debe reemplazarlos por los datos certificados de la válvula ofertada
cuando los tenga (ver ayuda «estilo_valvula»).
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class EstiloValvula:
    clave: str
    nombre: str
    familia: str            # «globo», «angular», «rotativa»
    FL: float
    xT: float
    Fd: float
    Cd: float               # Cv nominal / d² [d en pulgadas], valor típico
    caracteristica: str     # «isoporcentual», «lineal», «apertura_rapida»
    rangeabilidad: float    # relación R para la característica inherente
    nota: str = ""


ESTILOS: dict[str, EstiloValvula] = {e.clave: e for e in [
    EstiloValvula("globo_contorneado_lineal_abre", "Globo, obturador contorneado, lineal, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 12.0, "lineal", 50),
    EstiloValvula("globo_contorneado_lineal_cierra", "Globo, obturador contorneado, lineal, flujo tiende a cerrar",
                  "globo", 0.80, 0.55, 1.00, 12.0, "lineal", 50),
    EstiloValvula("globo_contorneado_iso_abre", "Globo, obturador contorneado, isoporcentual, flujo tiende a abrir",
                  "globo", 0.90, 0.75, 0.46, 11.0, "isoporcentual", 50),
    EstiloValvula("globo_contorneado_iso_cierra", "Globo, obturador contorneado, isoporcentual, flujo tiende a cerrar",
                  "globo", 0.80, 0.70, 1.00, 11.0, "isoporcentual", 50),
    EstiloValvula("globo_jaula_4v_fuera", "Globo, jaula caracterizada 4 ventanas, flujo hacia afuera",
                  "globo", 0.90, 0.75, 0.41, 14.0, "isoporcentual", 50),
    EstiloValvula("globo_jaula_4v_dentro", "Globo, jaula caracterizada 4 ventanas, flujo hacia adentro",
                  "globo", 0.85, 0.70, 0.41, 14.0, "isoporcentual", 50),
    EstiloValvula("globo_jaula_60_orificios", "Globo, jaula de 60 orificios (baja cavitación / bajo ruido)",
                  "globo", 0.90, 0.68, 0.13, 7.0, "lineal", 30,
                  "Jaula perforada para reducir ruido y retrasar la cavitación."),
    EstiloValvula("globo_jaula_120_orificios", "Globo, jaula de 120 orificios (baja cavitación / bajo ruido)",
                  "globo", 0.90, 0.68, 0.09, 7.0, "lineal", 30),
    EstiloValvula("globo_multietapa", "Globo, internos multietapa (anticavitación severa)",
                  "globo", 0.97, 0.81, 0.07, 3.5, "lineal", 30,
                  "Divide la caída de presión en varias etapas."),
    EstiloValvula("angular_contorneado_abre", "Angular, obturador contorneado, flujo tiende a abrir",
                  "angular", 0.90, 0.72, 0.46, 12.0, "lineal", 50),
    EstiloValvula("angular_contorneado_cierra", "Angular, obturador contorneado, flujo tiende a cerrar",
                  "angular", 0.80, 0.65, 1.00, 12.0, "lineal", 50,
                  "Configuración habitual para servicios con flashing."),
    EstiloValvula("angular_venturi", "Angular, tipo Venturi", "angular", 0.50, 0.20, 1.00, 18.0, "lineal", 30),
    EstiloValvula("rotativa_obturador_excentrico_abre", "Rotativa, obturador esférico excéntrico, flujo tiende a abrir",
                  "rotativa", 0.85, 0.60, 0.42, 14.0, "lineal", 100),
    EstiloValvula("rotativa_obturador_excentrico_cierra", "Rotativa, obturador esférico excéntrico, flujo tiende a cerrar",
                  "rotativa", 0.68, 0.40, 0.42, 14.0, "lineal", 100),
    EstiloValvula("mariposa_concentrica_60", "Mariposa concéntrica, apertura máxima 60°",
                  "rotativa", 0.70, 0.42, 0.50, 20.0, "isoporcentual", 20),
    EstiloValvula("mariposa_concentrica_70", "Mariposa concéntrica, apertura máxima 70°",
                  "rotativa", 0.62, 0.35, 0.57, 30.0, "isoporcentual", 20),
    EstiloValvula("mariposa_alto_rendimiento_90", "Mariposa de alto rendimiento (doble excéntrica), 90°",
                  "rotativa", 0.67, 0.35, 0.57, 35.0, "isoporcentual", 30),
    EstiloValvula("bola_segmentada", "Bola segmentada (V-notch)", "rotativa", 0.60, 0.30, 0.98, 25.0,
                  "isoporcentual", 100),
    EstiloValvula("bola_paso_total_70", "Bola de paso total, apertura 70°", "rotativa", 0.74, 0.42, 0.99, 30.0,
                  "isoporcentual", 50),
    EstiloValvula("globo_liner_contorneado", "Globo con liner, obturador contorneado, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 10.0, "isoporcentual", 30,
                  "Cuerpo revestido (PFA/PTFE): IEC no publica factores propios; se adoptan los del "
                  "globo contorneado."),
    EstiloValvula("angular_jaula_abre", "Angular, jaula, flujo tiende a abrir",
                  "angular", 0.85, 0.65, 0.41, 12.0, "lineal", 50),
    EstiloValvula("mariposa_triple_90", "Mariposa triple excéntrica, 90°",
                  "rotativa", 0.67, 0.35, 0.57, 30.0, "isoporcentual", 30,
                  "IEC no publica factores propios de la triple excéntrica: se adoptan los del disco "
                  "excéntrico (doble excéntrica)."),
]}


# ---------------------------------------------------------------------------
# Estilos de cuerpo de la versión 2 y los internos (trims) compatibles con cada uno.
# Las claves de «trims» son estilos de ESTILOS (factores típicos de IEC 60534-2-1).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Cuerpo:
    clave: str
    nombre: str
    trims: tuple            # claves de ESTILOS
    nps_min: float
    nps_max: float
    rotativa: bool
    guia: str               # tipo de guía habitual del obturador
    An: float               # coeficiente acústico de IEC 60534-8-4


CUERPOS: dict[str, Cuerpo] = {c.clave: c for c in [
    Cuerpo("globo", "Globo", ("globo_contorneado_iso_abre", "globo_contorneado_lineal_abre",
                              "globo_contorneado_iso_cierra", "globo_jaula_4v_fuera",
                              "globo_jaula_4v_dentro", "globo_jaula_60_orificios",
                              "globo_jaula_120_orificios", "globo_multietapa"),
           0.5, 24, False, "Guiado superior / por jaula", -4.6),
    Cuerpo("globo_liner", "Globo con liner", ("globo_liner_contorneado",), 0.5, 12, False,
           "Guiado superior (vástago con fuelle o empaquetadura PTFE)", -4.6),
    Cuerpo("angulo", "Ángulo", ("angular_contorneado_abre", "angular_contorneado_cierra",
                                "angular_jaula_abre", "angular_venturi"),
           0.5, 16, False, "Guiado superior / por jaula", -4.6),
    Cuerpo("bola", "Bola", ("bola_segmentada", "bola_paso_total_70"), 1, 36, True,
           "Eje guiado por cojinetes", -4.3),
    Cuerpo("mariposa", "Mariposa", ("mariposa_concentrica_60", "mariposa_concentrica_70"), 2, 60, True,
           "Eje guiado por cojinetes", -4.3),
    Cuerpo("mariposa_doble", "Mariposa doble excentricidad", ("mariposa_alto_rendimiento_90",), 2, 48,
           True, "Eje guiado por cojinetes", -4.3),
    Cuerpo("mariposa_triple", "Mariposa triple excentricidad", ("mariposa_triple_90",), 3, 60, True,
           "Eje guiado por cojinetes", -4.3),
]}

# Grado de anticavitación de cada trim: 0 estándar, 1 etapa simple de orificios, 2 multietapa
ANTICAVITACION = {"globo_jaula_60_orificios": 1, "globo_jaula_120_orificios": 1, "globo_multietapa": 2}

# Diámetros nominales (pulgada, DN mm) y diámetro interior de tubería
# cédula 40 según ASME B36.10M (mm).
TAMANOS = [
    # (pulgadas, DN, DI cédula 40 [mm])
    (0.5, 15, 15.80), (0.75, 20, 20.93), (1.0, 25, 26.64), (1.5, 40, 40.89),
    (2.0, 50, 52.50), (3.0, 80, 77.92), (4.0, 100, 102.26), (6.0, 150, 154.05),
    (8.0, 200, 202.72), (10.0, 250, 254.51), (12.0, 300, 303.23), (14.0, 350, 333.34),
    (16.0, 400, 381.00), (18.0, 450, 428.66), (20.0, 500, 477.82), (24.0, 600, 574.64),
    (30.0, 750, None), (36.0, 900, None), (42.0, 1050, None), (48.0, 1200, None),
]


def kv_nominal(estilo: EstiloValvula, d_pulg: float) -> float:
    """Kv nominal típico del estilo para un diámetro dado."""
    return estilo.Cd * d_pulg ** 2 * 0.865


def apertura_requerida(phi: float, caracteristica: str, R: float) -> float:
    """Carrera relativa h (0–1) para la capacidad relativa φ = C/Cnominal.

    Característica inherente ideal:
      lineal:          φ = 1/R + (1 − 1/R)·h
      isoporcentual:   φ = R^(h − 1)
      apertura rápida: φ = √h
    """
    if phi <= 0:
        return 0.0
    if caracteristica == "lineal":
        h = (phi - 1 / R) / (1 - 1 / R)
    elif caracteristica == "isoporcentual":
        h = 1 + math.log(phi) / math.log(R)
    else:
        h = phi ** 2
    return max(h, 0.0)


# Espesor de pared cédula 40 (ASME B36.10M) [mm], indexado por diámetro interior
ESPESOR_SCH40 = {15.80: 2.77, 20.93: 2.87, 26.64: 3.38, 40.89: 3.68, 52.50: 3.91, 77.92: 5.49,
                 102.26: 6.02, 154.05: 7.11, 202.72: 8.18, 254.51: 9.27, 303.23: 10.31,
                 333.34: 11.13, 381.00: 12.70, 428.66: 14.27, 477.82: 15.09, 574.64: 17.48}


def espesor_pared(Di_mm: float) -> float:
    """Espesor de pared cédula 40 para el DI dado (interpolado si no coincide)."""
    claves = sorted(ESPESOR_SCH40)
    if Di_mm <= claves[0]:
        return ESPESOR_SCH40[claves[0]]
    if Di_mm >= claves[-1]:
        return ESPESOR_SCH40[claves[-1]]
    for a, b in zip(claves, claves[1:]):
        if a <= Di_mm <= b:
            return ESPESOR_SCH40[a] + (ESPESOR_SCH40[b] - ESPESOR_SCH40[a]) * (Di_mm - a) / (b - a)

# Coeficiente de cavitación incipiente Kc típico de cada trim (ΔP de inicio / (P1 − Pv)).
# Valores genéricos de referencia de la práctica de la industria (ISA-RP75.23 usa el índice
# equivalente σi = 1/Kc); no corresponden a ningún fabricante. Deben reemplazarse por el Kc
# certificado del trim ofertado.
KC_TIPICO = {
    "globo_contorneado_iso_abre": 0.65, "globo_contorneado_lineal_abre": 0.65,
    "globo_contorneado_iso_cierra": 0.55, "globo_contorneado_lineal_cierra": 0.55,
    "globo_jaula_4v_fuera": 0.70, "globo_jaula_4v_dentro": 0.65,
    "globo_jaula_60_orificios": 0.80, "globo_jaula_120_orificios": 0.85, "globo_multietapa": 0.95,
    "globo_liner_contorneado": 0.60,
    "angular_contorneado_abre": 0.65, "angular_contorneado_cierra": 0.55, "angular_jaula_abre": 0.65,
    "angular_venturi": 0.20,
    "bola_segmentada": 0.25, "bola_paso_total_70": 0.30,
    "mariposa_concentrica_60": 0.35, "mariposa_concentrica_70": 0.30,
    "mariposa_alto_rendimiento_90": 0.35, "mariposa_triple_90": 0.35,
    "rotativa_obturador_excentrico_abre": 0.50, "rotativa_obturador_excentrico_cierra": 0.35,
}
