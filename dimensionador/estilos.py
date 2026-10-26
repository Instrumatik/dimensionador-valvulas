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


# Nombres de versiones anteriores, para abrir proyectos guardados con ellos
NOMBRES_ANTERIORES = {
    "Globo, jaula caracterizada 4 ventanas, flujo hacia afuera": "globo_jaula_4v_fuera",
    "Globo, jaula caracterizada 4 ventanas, flujo hacia adentro": "globo_jaula_4v_dentro",
    "Bola segmentada (V-notch)": "bola_segmentada",
    "Bola": "bola_trunnion",
}


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
    familia_cv: str = ""    # familia de capacidad.PLENO (vástago ascendente); "" = Cv = Cd·d²
    factor_cv: float = 1.0  # multiplicador del Cv de la familia (p. ej. número de etapas)


_NOTA_DOBLE_GUIA = ("Diseño de válvula de globo en el que el obturador o el vástago se apoya y se alinea en dos "
                    "puntos de guiado separados, ubicados en la parte superior del conjunto, por encima de la "
                    "corriente del fluido. Los factores son los del obturador contorneado de IEC 60534-2-1; la "
                    "característica la define el perfil del obturador.")

ESTILOS: dict[str, EstiloValvula] = {e.clave: e for e in [
    # --- claves de v0.11.0 y anteriores (característica en la clave): se conservan para abrir proyectos
    # guardados; el programa las convierte a las de abajo (CLAVES_ANTERIORES)
    EstiloValvula("globo_contorneado_lineal_abre", "Globo, obturador contorneado, lineal, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 12.0, "lineal", 50, familia_cv="contorneado"),
    EstiloValvula("globo_contorneado_lineal_cierra", "Globo, obturador contorneado, lineal, flujo tiende a cerrar",
                  "globo", 0.80, 0.55, 1.00, 12.0, "lineal", 50, familia_cv="contorneado"),
    EstiloValvula("globo_contorneado_iso_abre", "Globo, obturador contorneado, isoporcentual, flujo tiende a abrir",
                  "globo", 0.90, 0.75, 0.46, 11.0, "isoporcentual", 50, familia_cv="contorneado"),
    EstiloValvula("globo_contorneado_iso_cierra", "Globo, obturador contorneado, isoporcentual, flujo tiende a cerrar",
                  "globo", 0.80, 0.70, 1.00, 11.0, "isoporcentual", 50, familia_cv="contorneado"),
    EstiloValvula("globo_doble_guia_superior",
                  "Globo, doble guía de vástago superior, obturador contorneado, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 12.0, "isoporcentual", 50, _NOTA_DOBLE_GUIA, familia_cv="contorneado"),
    # --- v0.12.0: el estilo de trim es la geometría; el sentido del flujo va en la clave y la característica
    # (lineal, isoporcentual, apertura rápida) se elige aparte
    EstiloValvula("globo_contorneado_abre", "Globo, obturador contorneado, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 12.0, "isoporcentual", 50, familia_cv="contorneado"),
    EstiloValvula("globo_contorneado_cierra", "Globo, obturador contorneado, flujo tiende a cerrar",
                  "globo", 0.80, 0.55, 1.00, 12.0, "isoporcentual", 50, familia_cv="contorneado"),
    EstiloValvula("globo_doble_guia_abre",
                  "Globo, doble guía de vástago superior, obturador contorneado, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 12.0, "isoporcentual", 50, _NOTA_DOBLE_GUIA, familia_cv="contorneado"),
    EstiloValvula("globo_doble_guia_cierra",
                  "Globo, doble guía de vástago superior, obturador contorneado, flujo tiende a cerrar",
                  "globo", 0.80, 0.55, 1.00, 12.0, "isoporcentual", 50, _NOTA_DOBLE_GUIA, familia_cv="contorneado"),
    EstiloValvula("globo_jaula_4v_fuera",
                  "Globo, jaula caracterizada 4 ventanas, flujo de adentro hacia afuera de la jaula (tiende a abrir)",
                  "globo", 0.90, 0.75, 0.41, 14.0, "isoporcentual", 50,
                  "El fluido entra por debajo del asiento, sube por el interior de la jaula y sale por las "
                  "ventanas hacia el cuerpo (flujo bajo el obturador, tiende a abrir). Es la dirección "
                  "habitual en líquidos y gases.", familia_cv="jaula"),
    EstiloValvula("globo_jaula_4v_dentro",
                  "Globo, jaula caracterizada 4 ventanas, flujo de afuera hacia adentro de la jaula (tiende a cerrar)",
                  "globo", 0.85, 0.70, 0.41, 14.0, "isoporcentual", 50,
                  "El fluido rodea la jaula, entra por las ventanas y baja a través del asiento (flujo "
                  "sobre el obturador, tiende a cerrar). Se usa para alejar la cavitación o el flashing "
                  "del asiento y en algunos trims de bajo ruido.", familia_cv="jaula"),
    EstiloValvula("globo_jaula_60_orificios", "Globo, jaula de 60 orificios (baja cavitación / bajo ruido), flujo "
                  "tiende a abrir", "globo", 0.90, 0.68, 0.13, 7.0, "lineal", 15,
                  "Jaula perforada para reducir ruido y retrasar la cavitación. Con flujo de adentro hacia "
                  "afuera es la disposición habitual de bajo ruido en gases.", familia_cv="orificios"),
    EstiloValvula("globo_jaula_60_orificios_cierra", "Globo, jaula de 60 orificios (baja cavitación / bajo ruido), "
                  "flujo tiende a cerrar", "globo", 0.90, 0.68, 0.13, 7.0, "lineal", 15,
                  "Flujo de afuera hacia adentro de la jaula: los chorros chocan en el centro, lejos de las "
                  "paredes; es la disposición habitual anticavitación en líquidos. IEC 60534-2-1 publica los "
                  "mismos factores para los dos sentidos.", familia_cv="orificios"),
    EstiloValvula("globo_jaula_120_orificios", "Globo, jaula de 120 orificios (baja cavitación / bajo ruido), flujo "
                  "tiende a abrir", "globo", 0.90, 0.68, 0.09, 7.0, "lineal", 15, familia_cv="orificios"),
    EstiloValvula("globo_jaula_120_orificios_cierra", "Globo, jaula de 120 orificios (baja cavitación / bajo ruido), "
                  "flujo tiende a cerrar", "globo", 0.90, 0.68, 0.09, 7.0, "lineal", 15, familia_cv="orificios"),
    EstiloValvula("globo_multietapa", "Globo, internos multietapa (anticavitación severa), flujo tiende a abrir",
                  "globo", 0.97, 0.81, 0.07, 3.5, "lineal", 33,
                  "Divide la caída de presión en varias etapas.", familia_cv="multietapa"),
    EstiloValvula("globo_multietapa_cierra", "Globo, internos multietapa (anticavitación severa), flujo tiende a "
                  "cerrar", "globo", 0.97, 0.81, 0.07, 3.5, "lineal", 33,
                  "Divide la caída de presión en varias etapas; con flujo hacia adentro la última etapa "
                  "descarga en el centro del trim (disposición habitual anticavitación).", familia_cv="multietapa"),
    EstiloValvula("angular_contorneado_abre", "Angular, obturador contorneado, flujo tiende a abrir",
                  "angular", 0.90, 0.72, 0.46, 12.0, "lineal", 50, familia_cv="contorneado"),
    EstiloValvula("angular_contorneado_cierra", "Angular, obturador contorneado, flujo tiende a cerrar",
                  "angular", 0.80, 0.65, 1.00, 12.0, "lineal", 50,
                  "Configuración habitual para servicios con flashing.", familia_cv="contorneado"),
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
    EstiloValvula("bola_segmentada", "Bola segmentada, corte en V de 90° (V-notch)", "rotativa", 0.60, 0.30,
                  0.98, 25.0, "isoporcentual", 100,
                  "Factores de IEC 60534-2-1, Tabla 2 (bola segmentada). El borde en V corta fibras y sólidos."),
    EstiloValvula("bola_paso_total_70", "Bola de paso total, apertura 70°", "rotativa", 0.74, 0.42, 0.99, 30.0,
                  "isoporcentual", 50),
    # --- bola (v0.8.0). Las de 90° y paso reducido y las V de 60°/30° no figuran en la Tabla 2 de
    # IEC 60534-2-1: se estiman a partir de las de bola de paso total 70° y segmentada.
    EstiloValvula("bola_paso_completo_90", "Bola de paso completo, apertura 90°", "rotativa", 0.55, 0.20, 0.99,
                  45.0, "isoporcentual", 30,
                  "A 90° la bola casi no restringe: FL y xT muy bajos (mucha recuperación de presión) y mayor "
                  "tendencia a cavitar. Valores estimados (IEC solo publica la bola a 70°); para control se "
                  "prefiere limitar la carrera a 70°."),
    EstiloValvula("bola_paso_reducido_70", "Bola de paso reducido, apertura 70°", "rotativa", 0.80, 0.50, 0.99,
                  14.0, "isoporcentual", 50,
                  "El orificio de la bola es una o dos medidas menor que la conexión: menos capacidad, algo "
                  "más de FL y xT que el paso completo. Valores estimados."),
    EstiloValvula("bola_paso_reducido_90", "Bola de paso reducido, apertura 90°", "rotativa", 0.68, 0.33, 0.99,
                  20.0, "isoporcentual", 30, "Valores estimados a partir de la bola de paso completo."),
    EstiloValvula("bola_segmentada_v60", "Bola segmentada, corte en V de 60°", "rotativa", 0.65, 0.36, 0.98, 17.0,
                  "isoporcentual", 150,
                  "V más cerrada: menos capacidad, más rangeabilidad y mejor control a bajo caudal. Valores "
                  "estimados a partir de la bola segmentada de IEC."),
    EstiloValvula("bola_segmentada_v30", "Bola segmentada, corte en V de 30°", "rotativa", 0.72, 0.45, 0.98, 9.0,
                  "isoporcentual", 200,
                  "V estrecha para caudales bajos y fluidos fibrosos o con sólidos. Valores estimados."),
    EstiloValvula("globo_liner_contorneado", "Globo con liner, obturador contorneado, flujo tiende a abrir",
                  "globo", 0.90, 0.72, 0.46, 10.0, "isoporcentual", 30,
                  "Cuerpo revestido (PFA/PTFE): IEC no publica factores propios; se adoptan los del "
                  "globo contorneado. El revestimiento reduce el paso: Cv de 0,85 veces el contorneado.",
                  familia_cv="contorneado", factor_cv=0.85),
    EstiloValvula("angular_jaula_abre", "Angular, jaula, flujo tiende a abrir",
                  "angular", 0.85, 0.65, 0.41, 12.0, "lineal", 50, familia_cv="jaula"),
    EstiloValvula("angular_jaula_cierra", "Angular, jaula, flujo tiende a cerrar",
                  "angular", 0.80, 0.60, 0.41, 12.0, "lineal", 50,
                  "Factores estimados a partir del angular de jaula con flujo que tiende a abrir y de la "
                  "diferencia entre sentidos del obturador contorneado.", familia_cv="jaula"),
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
    Cuerpo("globo", "Globo", ("globo_contorneado_abre", "globo_contorneado_cierra", "globo_doble_guia_abre",
                              "globo_doble_guia_cierra", "globo_jaula_4v_fuera", "globo_jaula_4v_dentro",
                              "globo_jaula_60_orificios", "globo_jaula_60_orificios_cierra",
                              "globo_jaula_120_orificios", "globo_jaula_120_orificios_cierra",
                              "globo_multietapa", "globo_multietapa_cierra"),
           0.5, 24, False, "Guiado superior / por jaula", -4.6),
    Cuerpo("globo_liner", "Globo con liner", ("globo_liner_contorneado",), 0.5, 12, False,
           "Guiado superior (vástago con fuelle o empaquetadura PTFE)", -4.6),
    Cuerpo("angulo", "Ángulo", ("angular_contorneado_abre", "angular_contorneado_cierra",
                                "angular_jaula_abre", "angular_jaula_cierra", "angular_venturi"),
           0.5, 16, False, "Guiado superior / por jaula", -4.6),
    Cuerpo("bola_paso_completo", "Bola de paso completo (flotante)", ("bola_paso_total_70", "bola_paso_completo_90"),
           0.5, 8, True, "Bola flotante apoyada en los asientos; eje guiado por buje", -4.3),
    Cuerpo("bola_paso_reducido", "Bola de paso reducido (flotante)", ("bola_paso_reducido_70", "bola_paso_reducido_90"),
           0.5, 8, True, "Bola flotante apoyada en los asientos; eje guiado por buje", -4.3),
    Cuerpo("bola_trunnion", "Bola trunnion / Bola-T (montada en muñones)", ("bola_paso_total_70", "bola_paso_completo_90",
                                                                 "bola_paso_reducido_70", "bola_paso_reducido_90",
                                                                 "bola_segmentada"),
           2, 48, True, "Bola fija en muñones superior e inferior con cojinetes; asientos con resorte", -4.3),
    Cuerpo("bola_segmentada", "Bola segmentada (corte en V)", ("bola_segmentada", "bola_segmentada_v60",
                                                               "bola_segmentada_v30"),
           1, 24, True, "Segmento guiado por eje pasante con cojinetes", -4.3),
    Cuerpo("tapon_excentrico", "Tapón excéntrico rotativo", ("rotativa_obturador_excentrico_abre",
                                                             "rotativa_obturador_excentrico_cierra"),
           1, 12, True, "Tapón esférico en brazo flexible excéntrico; eje con cojinetes", -4.3),
    Cuerpo("mariposa", "Mariposa", ("mariposa_concentrica_60", "mariposa_concentrica_70"), 2, 60, True,
           "Eje guiado por cojinetes", -4.3),
    Cuerpo("mariposa_doble", "Mariposa doble excentricidad", ("mariposa_alto_rendimiento_90",), 2, 48,
           True, "Eje guiado por cojinetes", -4.3),
    Cuerpo("mariposa_triple", "Mariposa triple excentricidad", ("mariposa_triple_90",), 3, 60, True,
           "Eje guiado por cojinetes", -4.3),
]}

# Grado de anticavitación de cada trim: 0 estándar, 1 etapa simple de orificios, 2 multietapa
ANTICAVITACION = {"globo_jaula_60_orificios": 1, "globo_jaula_120_orificios": 1, "globo_multietapa": 2,
                  "globo_jaula_60_orificios_cierra": 1, "globo_jaula_120_orificios_cierra": 1,
                  "globo_multietapa_cierra": 2}

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
    """Kv nominal típico del estilo para un diámetro dado.

    Vástago ascendente: Cv del trim pleno de su familia (``capacidad``, mediana de datos publicados de
    fabricantes) con la característica del estilo. Rotativas y Venturi: Cd·d²."""
    if estilo.familia_cv:
        from . import capacidad
        return capacidad.pleno(estilo.familia_cv, d_pulg, estilo.caracteristica).Cv * estilo.factor_cv * 0.865
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

# Coeficiente de cavitación Kc típico de cada trim: ΔP/(P1 − Pv) a partir del cual la cavitación es
# sostenida y puede dañar (régimen constante σc = 1/Kc de ISA-RP75.23, criterio de ΔPcav de los
# fabricantes). La cavitación incipiente (ruido) se evalúa aparte con xFz de IEC 60534-8-4.
# Valores genéricos de referencia; no corresponden a ningún fabricante. Deben reemplazarse por el
# Kc certificado del trim ofertado.
KC_TIPICO = {
    "globo_contorneado_iso_abre": 0.65, "globo_contorneado_lineal_abre": 0.65,
    "globo_contorneado_iso_cierra": 0.55, "globo_contorneado_lineal_cierra": 0.55,
    "globo_jaula_4v_fuera": 0.70, "globo_jaula_4v_dentro": 0.65,
    "globo_jaula_60_orificios": 0.80, "globo_jaula_120_orificios": 0.85, "globo_multietapa": 0.95,
    "globo_liner_contorneado": 0.60, "globo_doble_guia_superior": 0.65,
    "globo_contorneado_abre": 0.65, "globo_contorneado_cierra": 0.55, "globo_doble_guia_abre": 0.65,
    "globo_doble_guia_cierra": 0.55, "globo_jaula_60_orificios_cierra": 0.85, "globo_jaula_120_orificios_cierra": 0.90,
    "globo_multietapa_cierra": 0.95, "angular_jaula_cierra": 0.60,
    "angular_contorneado_abre": 0.65, "angular_contorneado_cierra": 0.55, "angular_jaula_abre": 0.65,
    "angular_venturi": 0.20,
    "bola_segmentada": 0.25, "bola_paso_total_70": 0.30, "bola_paso_completo_90": 0.20,
    "bola_paso_reducido_70": 0.40, "bola_paso_reducido_90": 0.30, "bola_segmentada_v60": 0.30,
    "bola_segmentada_v30": 0.35,
    "mariposa_concentrica_60": 0.35, "mariposa_concentrica_70": 0.30,
    "mariposa_alto_rendimiento_90": 0.35, "mariposa_triple_90": 0.35,
    "rotativa_obturador_excentrico_abre": 0.50, "rotativa_obturador_excentrico_cierra": 0.35,
}

# Claves de versiones anteriores que llevaban la característica en el nombre: (clave nueva, característica)
CLAVES_ANTERIORES = {
    "globo_contorneado_lineal_abre": ("globo_contorneado_abre", "lineal"),
    "globo_contorneado_lineal_cierra": ("globo_contorneado_cierra", "lineal"),
    "globo_contorneado_iso_abre": ("globo_contorneado_abre", "isoporcentual"),
    "globo_contorneado_iso_cierra": ("globo_contorneado_cierra", "isoporcentual"),
    "globo_doble_guia_superior": ("globo_doble_guia_abre", None),
}

# Factores (FL, xT, Fd) de IEC 60534-2-1, Tabla 2, que cambian con la característica; el resto de los
# estilos tiene los mismos para lineal, isoporcentual y apertura rápida.
FACTORES_CARACTERISTICA = {
    ("globo_contorneado_abre", "lineal"): (0.90, 0.72, 0.46),
    ("globo_contorneado_abre", "isoporcentual"): (0.90, 0.75, 0.46),
    ("globo_contorneado_cierra", "lineal"): (0.80, 0.55, 1.00),
    ("globo_contorneado_cierra", "isoporcentual"): (0.80, 0.70, 1.00),
    ("globo_doble_guia_abre", "lineal"): (0.90, 0.72, 0.46),
    ("globo_doble_guia_abre", "isoporcentual"): (0.90, 0.75, 0.46),
    ("globo_doble_guia_cierra", "lineal"): (0.80, 0.55, 1.00),
    ("globo_doble_guia_cierra", "isoporcentual"): (0.80, 0.70, 1.00),
}


def factores(clave: str, caracteristica: str) -> tuple[float, float, float]:
    """FL, xT y Fd típicos del estilo con la característica elegida."""
    e = ESTILOS[clave]
    return FACTORES_CARACTERISTICA.get((clave, caracteristica), (e.FL, e.xT, e.Fd))


def estilo_con(clave: str, caracteristica: str) -> EstiloValvula:
    """Estilo con la característica y los factores que le corresponden."""
    from dataclasses import replace
    FL, xT, Fd = factores(clave, caracteristica)
    return replace(ESTILOS[clave], caracteristica=caracteristica, FL=FL, xT=xT, Fd=Fd)


# Estilo de trim (geometría) y sentido del flujo de cada clave; la solapa 2 los elige por separado.
SENTIDOS = {"abre": "Flujo tiende a abrir (Up)", "cierra": "Flujo tiende a cerrar (Down)", "": "No aplica"}
GEOMETRIA = {
    "globo_contorneado_abre": ("contorneado", "abre"), "globo_contorneado_cierra": ("contorneado", "cierra"),
    "globo_doble_guia_abre": ("doble_guia", "abre"), "globo_doble_guia_cierra": ("doble_guia", "cierra"),
    "globo_jaula_4v_fuera": ("jaula_4v", "abre"), "globo_jaula_4v_dentro": ("jaula_4v", "cierra"),
    "globo_jaula_60_orificios": ("jaula_60", "abre"), "globo_jaula_60_orificios_cierra": ("jaula_60", "cierra"),
    "globo_jaula_120_orificios": ("jaula_120", "abre"), "globo_jaula_120_orificios_cierra": ("jaula_120", "cierra"),
    "globo_multietapa": ("multietapa", "abre"), "globo_multietapa_cierra": ("multietapa", "cierra"),
    "globo_liner_contorneado": ("liner_contorneado", "abre"),
    "angular_contorneado_abre": ("contorneado", "abre"), "angular_contorneado_cierra": ("contorneado", "cierra"),
    "angular_jaula_abre": ("jaula", "abre"), "angular_jaula_cierra": ("jaula", "cierra"),
    "angular_venturi": ("venturi", "cierra"),
    "rotativa_obturador_excentrico_abre": ("excentrico", "abre"),
    "rotativa_obturador_excentrico_cierra": ("excentrico", "cierra"),
}
NOMBRE_GEOMETRIA = {
    "contorneado": "Obturador contorneado", "doble_guia": "Doble guía de vástago - superior",
    "jaula_4v": "Jaula caracterizada 4 ventanas", "jaula_60": "Jaula de 60 orificios (baja cavitación / ruido)",
    "jaula_120": "Jaula de 120 orificios (baja cavitación / ruido)", "multietapa": "Multietapa (anticavitación severa)",
    "liner_contorneado": "Liner, obturador contorneado", "jaula": "Jaula", "venturi": "Venturi",
    "excentrico": "Obturador excéntrico",
}


def geometria_sentido(clave: str) -> tuple[str, str]:
    """(estilo de trim, sentido) de una clave; las rotativas sin sentido devuelven (clave, "")."""
    clave = CLAVES_ANTERIORES.get(clave, (clave,))[0]
    return GEOMETRIA.get(clave, (clave, ""))


def geometrias(cuerpo: str) -> list[str]:
    """Estilos de trim (geometrías) del cuerpo, en el orden de sus trims."""
    out = []
    for k in CUERPOS[cuerpo].trims:
        g = geometria_sentido(k)[0]
        if g not in out:
            out.append(g)
    return out


def sentidos(cuerpo: str, geometria: str) -> list[str]:
    """Sentidos de flujo disponibles para un estilo de trim del cuerpo ([""] si no aplica)."""
    return [geometria_sentido(k)[1] for k in CUERPOS[cuerpo].trims if geometria_sentido(k)[0] == geometria]


def clave_trim(cuerpo: str, geometria: str, sentido: str) -> str:
    """Clave de ESTILOS para el estilo de trim y el sentido elegidos (el primero disponible si no está)."""
    ks = [k for k in CUERPOS[cuerpo].trims if geometria_sentido(k)[0] == geometria]
    return next((k for k in ks if geometria_sentido(k)[1] == sentido), ks[0] if ks else CUERPOS[cuerpo].trims[0])


def nombre_geometria(g: str) -> str:
    if g in NOMBRE_GEOMETRIA:
        return NOMBRE_GEOMETRIA[g]
    return NOMBRE_CORTO.get(g, ESTILOS[g].nombre if g in ESTILOS else g)


# Nombre corto para el desplegable de la solapa 2 (el cuerpo ya se elige en 1-Sistema); el nombre completo
# queda en la ayuda emergente, la ayuda «Ver» y los documentos.
NOMBRE_CORTO = {
    "globo_contorneado_lineal_abre": "Contorneado lineal · flujo abre",
    "globo_contorneado_lineal_cierra": "Contorneado lineal · flujo cierra",
    "globo_contorneado_iso_abre": "Contorneado isoporcentual · flujo abre",
    "globo_contorneado_iso_cierra": "Contorneado isoporcentual · flujo cierra",
    "globo_doble_guia_superior": "Doble guía de vástago - superior · flujo abre",
    "globo_contorneado_abre": "Contorneado · flujo abre", "globo_contorneado_cierra": "Contorneado · flujo cierra",
    "globo_doble_guia_abre": "Doble guía de vástago - superior · flujo abre",
    "globo_doble_guia_cierra": "Doble guía de vástago - superior · flujo cierra",
    "globo_jaula_60_orificios_cierra": "Jaula 60 orificios · flujo cierra",
    "globo_jaula_120_orificios_cierra": "Jaula 120 orificios · flujo cierra",
    "globo_multietapa_cierra": "Multietapa · flujo cierra", "angular_jaula_cierra": "Jaula · flujo cierra",
    "globo_jaula_4v_fuera": "Jaula 4 ventanas · flujo abre",
    "globo_jaula_4v_dentro": "Jaula 4 ventanas · flujo cierra",
    "globo_jaula_60_orificios": "Jaula 60 orificios (baja cavitación)",
    "globo_jaula_120_orificios": "Jaula 120 orificios (baja cavitación)",
    "globo_multietapa": "Multietapa (anticavitación severa)",
    "angular_contorneado_abre": "Contorneado · flujo abre",
    "angular_contorneado_cierra": "Contorneado · flujo cierra",
    "angular_venturi": "Venturi",
    "angular_jaula_abre": "Jaula · flujo abre",
    "rotativa_obturador_excentrico_abre": "Obturador excéntrico · flujo abre",
    "rotativa_obturador_excentrico_cierra": "Obturador excéntrico · flujo cierra",
    "mariposa_concentrica_60": "Concéntrica · 60°",
    "mariposa_concentrica_70": "Concéntrica · 70°",
    "mariposa_alto_rendimiento_90": "Doble excéntrica · 90°",
    "mariposa_triple_90": "Triple excéntrica · 90°",
    "bola_segmentada": "Corte en V de 90°",
    "bola_segmentada_v60": "Corte en V de 60°",
    "bola_segmentada_v30": "Corte en V de 30°",
    "bola_paso_total_70": "Paso total · 70°",
    "bola_paso_completo_90": "Paso completo · 90°",
    "bola_paso_reducido_70": "Paso reducido · 70°",
    "bola_paso_reducido_90": "Paso reducido · 90°",
    "globo_liner_contorneado": "Liner, contorneado · flujo abre",
}
