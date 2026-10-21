"""Dimensionamiento del actuador (solapa 4), del posicionador (solapa 5) y de los accesorios (solapa 6).

Válvulas de vástago deslizante (globo y ángulo): método de fuerzas.

    Fuerza total = A (desbalance estático) + B (carga de asiento) + C (fricción de empaquetadura)
                   + D (fuerzas adicionales)

* A: la presión del fluido sobre el área desbalanceada del obturador y sobre el vástago. Con el
  obturador que empuja hacia abajo para cerrar (la construcción habitual):

  - desbalanceado, flujo hacia arriba (Up, tiende a abrir):  A = ΔP·A_puerto + P2·A_vástago
  - desbalanceado, flujo hacia abajo (Down, tiende a cerrar): A = −(ΔP·A_puerto − P1·A_vástago)
  - balanceado: A = ΔP·A_desb + P·A_vástago, con A_desb = corona entre el diámetro interior de la
    jaula y la línea de asiento (≈ 0,037·π·d_puerto in²) y P la presión que ve el vástago.

  La fuerza de apertura no lleva carga de asiento (B = 0) y cambia el signo del término de presión.
* B: carga de asiento por clase de cierre (ANSI/FCI 70-2) por pulgada de perímetro del puerto.
* C: fricción de la empaquetadura según tipo, diámetro del vástago y clase de presión.
* D: fuerzas adicionales; con fuelle, su área efectiva reemplaza al área del vástago.

Válvulas rotativas: método de pares.

    Par de arranque  TB = A·ΔP_cierre + B          Par dinámico  TD = C(θ)·ΔP_efectiva

Los factores A, B y C son valores típicos de la industria por estilo y diámetro (no corresponden a
ningún fabricante) y se interpolan en escala logarítmica.

Actuadores: diafragma y resorte, multiresorte, pistón (con y sin resorte), piñón y cremallera,
yugo escocés, eléctrico, electrohidráulico y manual. Para los neumáticos con resorte se calcula el
ajuste de banco (bench set), la constante del resorte, la presión de aire requerida frente al aire
de instrumentos disponible, la carga del vástago y la estabilidad frente al gradiente negativo.

Son tamaños genéricos para la preingeniería: el fabricante del actuador confirma el modelo, el
resorte y el ajuste de banco con sus propias tablas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from .modelos import Alerta, Severidad, _n

LBF_N = 4.4482216152605
IN_MM = 25.4
PSI_KPA = 6.894757293168361
LBFIN_NM = 0.1129848290276167
P_ATM = 101.325

REF_FUERZAS = ("Método de fuerzas A + B + C + D para válvulas de vástago deslizante, práctica de la industria de "
               "válvulas de control; cargas de asiento según ANSI/FCI 70-2 / IEC 60534-4")
REF_PARES = "Método de pares TB = A·ΔP + B y TD = C·ΔPef para válvulas rotativas, práctica de la industria"
REF_ACT = "Práctica de la industria de válvulas de control (dimensionamiento de actuadores)"

TIPOS = ["Diafragma y resorte", "Multiresorte y diafragma", "Pistón doble acción con resorte",
         "Pistón doble acción sin resorte", "Pistón retorno por resorte", "Eléctrico", "Electrohidráulico",
         "Piñón y cremallera (Rack and pinion)", "Yugo escocés", "Manual"]
FALLAS = ["Cierra (FC)", "Abre (FO)", "Última posición (FL)"]
FLUJOS = ["Up", "Down", "Unidireccional", "Bidireccional"]
FC, FO, FL = FALLAS

# Concordancia actuador / válvula: los de cuarto de vuelta solo mueven ejes rotativos y los de vástago
# deslizante (diafragma, pistones) solo vástagos; eléctrico, electrohidráulico y manual existen en las dos versiones.
TIPOS_ROTATIVOS = ("Piñón y cremallera (Rack and pinion)", "Yugo escocés")
TIPOS_LINEALES = ("Diafragma y resorte", "Multiresorte y diafragma", "Pistón doble acción con resorte",
                  "Pistón doble acción sin resorte", "Pistón retorno por resorte")
FLUJOS_LINEALES = ("Up", "Down")
BOLAS_BIDIRECCIONALES = ("bola_paso_completo", "bola_paso_reducido", "bola_trunnion")


def tipos_bloqueados(rotativa: bool) -> dict[str, str]:
    """Tipos de actuador que no corresponden a la válvula, con el motivo."""
    if rotativa:
        return {t: "actuador de vástago deslizante; la válvula elegida es rotativa" for t in TIPOS_LINEALES}
    return {t: "actuador de cuarto de vuelta; la válvula elegida es de vástago deslizante" for t in TIPOS_ROTATIVOS}


def flujos_bloqueados(cuerpo: str, rotativa: bool) -> dict[str, str]:
    """Opciones de Flow que no corresponden al cuerpo: Up/Down solo en globo y ángulo, bidireccional solo en bolas."""
    if not rotativa:
        return {f: "aplica solo a válvulas rotativas" for f in ("Unidireccional", "Bidireccional")}
    b = {f: "aplica solo a válvulas de globo y ángulo" for f in FLUJOS_LINEALES}
    if cuerpo not in BOLAS_BIDIRECCIONALES:
        b["Bidireccional"] = "aplica solo a bola flotante o trunnion"
    return b

MARGEN_LINEAL = 1.10      # margen de diseño sobre la fuerza requerida (vástago deslizante)
MARGEN_ROT = 1.25         # margen sobre el par requerido (rotativas)
MARGEN_ELEC = 1.25        # margen de empuje / par de los actuadores eléctricos y electrohidráulicos
ETA_PISTON = 0.95         # rendimiento por fricción de los sellos del pistón
F_ARO_MAX_N = 360.0
RESORTE_RATIO = 1.45     # par del resorte al comienzo / al final de su carrera (cuarto de vuelta)
P_BANCO_MIN = 3.0         # ajuste de banco inferior mínimo práctico [psig]       # fuerza máxima en el aro del volante (práctica habitual, EN 12570)

# ---------------------------------------------------------------------------------------------- datos


@dataclass
class DatosActuador:
    tipo: str = TIPOS[0]
    falla: str = FC
    volante: bool = False
    P_aire_min: float | None = None     # kPa manométricos
    P_aire_max: float | None = None     # kPa manométricos
    flujo: str = "Up"
    d_vastago_mm: float | None = None   # None = estimado por el diámetro de la válvula
    regulado: bool = True               # el set de aire (solapa 5) limita la alimentación del actuador


SENALES = ["Foundation FieldBus", "4-20mA dc", "4-12mA dc", "12-20mA dc", "3-15 psi", "3-9 psi", "9-15 psi",
           "6-30 psi"]
TIPOS_POS = ["Neumático", "Electroneumático", "Digital-HART", "Foundation FieldBus",
             "Digital-HART con Diagnóstico avanzado", "Foundation FieldBus con Diagnóstico avanzado"]
ACCIONES_POS = ["Directo", "Inverso", "Doble", "Configurable"]
SALIDAS_SET = ["Ajustable 0-30 psi", "Ajustable 0-80 psi", "Otro"]
# Señales neumáticas: presión máxima de la señal [psig]
SENAL_PSI = {"3-15 psi": (3, 15), "3-9 psi": (3, 9), "9-15 psi": (9, 15), "6-30 psi": (6, 30)}
SENAL_MA = ("4-20mA dc", "4-12mA dc", "12-20mA dc")


@dataclass
class DatosPosicionador:
    tag: str = ""
    tipo: str = "Digital-HART"
    senal: str = "4-20mA dc"
    accion: str = "Configurable"
    manometros: bool = True
    set_aire: bool = True
    salida_set: str = "Ajustable 0-80 psi"


ACCION_SOL = ["Desenergiza para cerrar", "Desenergiza para abrir", "Energiza para cerrar", "Energiza para abrir"]
VIAS_SOL = ["2 vías", "3 vías", "4 vías"]
MATERIAL_SOL = ["Latón", "Acero Inoxidable"]
PUERTOS_SOL = ['1/4"', '1/2"', '3/4"']
VOLTAJES_SOL = ["24 Vdc", "110 Vdc", "120 VAC", "220 VAC"]
TIPOS_LIM = ["Mecánico", "Proximidad", "Magnético"]
CONTACTOS_LIM = ["SPST", "SPDT", "DPDT"]
FRECUENCIAS = ["50/60Hz", "50Hz", "60Hz"]
NO_APLICA = "No requerido"


@dataclass
class DatosAccesorios:
    boosters: str = ""
    quick_exhaust: str = ""
    bloqueo: str = ""
    cambio: str = ""
    sol_accion: str = NO_APLICA
    sol_vias: str = "3 vías"
    sol_material: str = "Acero Inoxidable"
    sol_puerto: str = '1/4"'
    sol_voltaje: str = "24 Vdc"
    sol_potencia: str = ""
    lim_tipo: str = NO_APLICA
    lim_contactos: str = "SPDT"
    lim_voltaje: str = ""
    lim_corriente: str = ""
    lim_frecuencia: str = "50/60Hz"

    @property
    def solenoide(self) -> bool:
        return self.sol_accion != NO_APLICA

    @property
    def limites(self) -> bool:
        return self.lim_tipo != NO_APLICA


@dataclass
class Equipo:
    """Actuador, posicionador y accesorios: datos de las solapas 4, 5 y 6."""
    actuador: DatosActuador = field(default_factory=DatosActuador)
    posicionador: DatosPosicionador = field(default_factory=DatosPosicionador)
    accesorios: DatosAccesorios = field(default_factory=DatosAccesorios)


# ---------------------------------------------------------------------------------------- utilidades


def _N(lbf: float) -> str:
    return f"{_n(lbf * LBF_N / 1000, 2)} kN ({_n(lbf, 0)} lbf)" if abs(lbf) * LBF_N >= 1000 else \
        f"{_n(lbf * LBF_N, 0)} N ({_n(lbf, 0)} lbf)"


def _Nm(lbfin: float) -> str:
    return f"{_n(lbfin * LBFIN_NM, 0)} N·m ({_n(lbfin, 0)} lbf·in)"


def _psi(p: float) -> str:
    return f"{_n(p / 14.5037738, 2)} bar g ({_n(p, 1)} psig)"


def _area(a_in2: float) -> str:
    return f"{_n(a_in2 * 6.4516, 0)} cm² ({_n(a_in2, 1)} in²)"


def _in(v: float) -> str:
    return f"{_n(v * IN_MM, 1)} mm ({_n(v, 3)} in)"


def _interp(x: float, xs, ys) -> float:
    """Interpolación lineal con extremos fijos."""
    if x <= xs[0]:
        return ys[0]
    for (a, fa), (b, fb) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if x <= b:
            return fa + (fb - fa) * (x - a) / (b - a)
    return ys[-1]


def _loglog(x: float, xs, ys, exp_bajo: float = 2.0, exp_alto: float | None = None) -> float:
    """Interpolación log-log; fuera de la tabla extrapola con el exponente dado (o el del último tramo)."""
    if x <= xs[0]:
        return ys[0] * (x / xs[0]) ** exp_bajo
    if x >= xs[-1]:
        if exp_alto is None:
            a, b = xs[-2], xs[-1]
            exp_alto = math.log(max(ys[-1], 1e-9) / max(ys[-2], 1e-9)) / math.log(b / a)
            exp_alto = min(max(exp_alto, 1.5), 3.5)
        return ys[-1] * (x / xs[-1]) ** exp_alto
    for a, b, fa, fb in zip(xs, xs[1:], ys, ys[1:]):
        if a <= x <= b:
            if fa <= 0 or fb <= 0:
                return fa + (fb - fa) * (x - a) / (b - a)
            t = math.log(x / a) / math.log(b / a)
            return math.exp(math.log(fa) + t * (math.log(fb) - math.log(fa)))
    return ys[-1]


# ------------------------------------------------------------------------------------ vástago


VASTAGOS_IN = (0.3125, 0.375, 0.5, 0.625, 0.75, 1.0, 1.25, 1.5, 2.0, 2.75)
# Carga máxima admisible en vástagos de inoxidable 316 endurecido por deformación [lbf] a ≤ 38 °C,
# con relaciones longitud / diámetro de hasta 12,5 (pandeo incluido)
CARGA_VASTAGO = {0.3125: 1940, 0.375: 2800, 0.5: 4970, 0.75: 11190, 1.0: 16130, 1.25: 20690, 2.0: 25000}
# Factor de reducción por temperatura [°C]
T_VASTAGO = (38, 93, 149, 204, 260, 316, 371, 427)
F_VASTAGO = (1.0, 0.869, 0.791, 0.714, 0.674, 0.644, 0.614, 0.604)


def vastago_estimado(nps: float, rating: int) -> float:
    """Diámetro de vástago habitual [in] según el diámetro de la válvula y la clase."""
    serie = ((1.0, 0.375), (2.0, 0.5), (4.0, 0.75), (6.0, 1.0), (10.0, 1.25), (99, 2.0))
    i = next(k for k, (n, _) in enumerate(serie) if nps <= n + 1e-9)
    if rating >= 900 and i < len(serie) - 1:
        i += 1
    return serie[i][1]


def carga_admisible_vastago(d_in: float, T_C: float) -> float:
    xs = sorted(CARGA_VASTAGO)
    base = _loglog(d_in, xs, [CARGA_VASTAGO[x] for x in xs], 2.0, 1.0)
    return base * _interp(T_C, T_VASTAGO, F_VASTAGO)


# ------------------------------------------------------------------------- carga de asiento (B)


def carga_asiento(clase: str, dP_psi: float, d_puerto_in: float, blando: bool, balanceado: bool):
    """Carga de asiento B [lbf] y la fórmula aplicada."""
    PC = math.pi * d_puerto_in
    grande = d_puerto_in > 4.375
    n = ["ANSI Clase I", "ANSI Clase II", "ANSI Clase III", "ANSI Clase IV", "ANSI Clase V", "ANSI Clase VI",
         "Tight Shutoff"].index(clase) if clase.startswith(("ANSI", "Tight")) else 3
    if n <= 1:
        return 20 * PC, "20·PC (clase I–II)"
    if n == 2:
        return 40 * PC, "40·PC (clase III)"
    if n == 3:
        if balanceado:
            k = 190 if grande else 150
            return k * PC, f"{k}·PC (clase IV, sello de balanceo)"
        k = 80 if grande else 40
        return k * PC, f"{k}·PC (clase IV, asiento metálico, puerto {'>' if grande else '≤'} 4,375 in)"
    if n == 4:
        if blando:
            return (150 + 0.122 * dP_psi) * PC, "(150 + 0,122·ΔP)·PC (clase V, asiento blando)"
        k = 210 if balanceado else 100
        return (k + 0.122 * dP_psi) * PC, f"({k} + 0,122·ΔP)·PC (clase V, asiento metálico)"
    # clase VI y cierre hermético
    if blando:
        if d_puerto_in < 1.3125:
            return 40 * PC, "40·PC (asiento blando, puerto < 1,3125 in)"
        A, B = 0.0397 * d_puerto_in, 95.0 * d_puerto_in
        return A * dP_psi + B, f"A·ΔP + B con A = {_n(A, 3)} y B = {_n(B, 0)} (asiento de PTFE)"
    if n == 6:
        return (100 + 0.122 * dP_psi) * PC, "(100 + 0,122·ΔP)·PC (cierre hermético metal-metal)"
    return 300 * PC, "300·PC (clase VI metal blando-metal)"


# ------------------------------------------------------------------- fricción de empaquetadura (C)

_VAST = (0.375, 0.5, 0.625, 0.75, 1.0, 1.25, 2.0)
# Grafito simple y PTFE/compuesto por clase de presión (300, 600, 900, 1500, 2500) [lbf]
_GRAFITO = {0.375: (190, 250, 320, 380, 380), 0.5: (230, 320, 410, 500, 590), 0.625: (290, 400, 400, 400, 400),
            0.75: (440, 660, 880, 1100, 1320), 1.0: (610, 850, 1060, 1300, 1540),
            1.25: (800, 1100, 1400, 1700, 2040), 2.0: (1225, 1725, 2250, 2750, 3245)}
_COMPUESTO = {0.375: (95, 125, 160, 190, 190), 0.5: (115, 160, 205, 250, 295), 0.625: (145, 200, 200, 200, 200),
              0.75: (220, 330, 440, 550, 660), 1.0: (305, 425, 530, 650, 770),
              1.25: (400, 550, 700, 850, 1020), 2.0: (613, 862, 1125, 1375, 1623)}
_PTFE_CV = ((0.3125, 60), (0.375, 125), (0.5, 170), (0.625, 210), (0.75, 250), (1.0, 340), (1.25, 425), (2.0, 725))
_GRAFITO_CV = ((0.375, 210), (0.5, 280), (0.625, 380), (0.75, 530), (1.0, 840), (1.25, 1100), (2.0, 1350))
_GRAFITO_HS = ((0.375, 420), (0.5, 1130), (0.75, 2120), (1.0, 3390), (1.25, 4240), (2.0, 6790))
_CLASES = (300, 600, 900, 1500, 2500)


def _por_clase(tabla: dict, d: float, rating: int) -> float:
    j = next((i for i, c in enumerate(_CLASES) if rating <= c), len(_CLASES) - 1)
    f = 0.8 if rating < 300 else 1.0
    return f * _interp(d, _VAST, [tabla[x][j] for x in _VAST])


def friccion_empaquetadura(clave: str | None, d_in: float, rating: int) -> tuple[float, str]:
    """Fricción C [lbf] y la familia usada."""
    k = clave or "ptfe_v"
    if k in ("ptfe_v", "ptfe_trenzado", "ptfe_trenzado_lub", "fuelle"):
        return 100 * d_in, "PTFE simple ≈ 100 lbf por pulgada de vástago" + (" (empaquetadura de respaldo del "
                                                                              "fuelle)" if k == "fuelle" else "")
    if k in ("ptfe_v_doble", "ptfe_v_doble_p", "ptfe_v_doble_vac"):
        return 150 * d_in, "PTFE doble ≈ 150 lbf por pulgada de vástago"
    if k == "ptfe_carbono":
        return _por_clase(_COMPUESTO, d_in, rating), "PTFE con relleno / compuesto, según clase de presión"
    if k == "ptfe_cv":
        return _interp(d_in, *zip(*_PTFE_CV)), "PTFE con carga viva"
    if k == "ptfe_carbono_cv_doble":
        return 1.4 * _interp(d_in, *zip(*_PTFE_CV)), "PTFE/carbono con carga viva, doble juego (1,4 × simple)"
    if k == "ptfe_vidrio_cv":
        return 1.2 * _interp(d_in, *zip(*_PTFE_CV)), "PTFE/vidrio con carga viva (1,2 × PTFE con carga viva)"
    if k == "grafito":
        return _por_clase(_GRAFITO, d_in, rating), "Grafito simple, según clase de presión"
    if k == "grafito_cv":
        return _interp(d_in, *zip(*_GRAFITO_CV)), "Grafito de baja fricción con carga viva"
    if k in ("grafito_hs_718", "grafito_hs_177"):
        return _interp(d_in, *zip(*_GRAFITO_HS)), "Grafito de alta hermeticidad con carga viva"
    return 100 * d_in, "PTFE simple (familia no identificada)"


def area_fuelle(nps: float, d_vast_in: float) -> float:
    """Área efectiva del fuelle de estanqueidad [in²]."""
    if nps <= 2:
        return 0.353
    if nps <= 8:
        return 1.340
    return max(1.340, 1.8 * math.pi * d_vast_in ** 2 / 4)


def gradiente_negativo(balanceado: bool, tiende_a_cerrar: bool, A_desb: float, carrera_in: float,
                       d_puerto_in: float) -> float:
    """Gradiente negativo Kn [(lbf/in)/psi]."""
    if balanceado:
        return min(6.0, 0.12 * d_puerto_in ** 1.5)
    if tiende_a_cerrar:
        return 2 * A_desb / carrera_in
    return 0.0


# --------------------------------------------------------------------------- factores rotativos

# Por familia: NPS -> (A, B, {ángulo: C}). Unidades: TB [lbf·in] con ΔP [psi].
_SEG = {2: (0.15, 80, 0.11, 0.60), 3: (0.10, 280, 0.15, 3.80), 4: (0.10, 380, 1.10, 18.0), 6: (1.80, 500, 1.10, 36.0),
        8: (1.80, 750, 3.80, 60.0), 10: (1.80, 1250, 3.80, 125), 12: (4.00, 3000, 11.0, 143),
        14: (42, 2400, 75, 413), 16: (60, 2800, 105, 578), 18: (60, 2800, 105, 578), 20: (97, 5200, 190, 1044)}
_HP = {3: (0.50, 136, 0.8, 1.8, 8), 4: (0.91, 217, 3.1, 4.7, 25), 6: (1.97, 403, 30, 24, 70),
       8: (4.2, 665, 65, 47, 165), 10: (7.3, 1012, 125, 90, 310), 12: (11.4, 1422, 216, 140, 580)}
_CONC = {2: (0.057, 50, 0.150, 0.240), 3: (0.150, 65, 1.14, 1.67), 4: (0.366, 100, 3.69, 5.19),
         6: (0.800, 100, 17.1, 29.4), 8: (1.79, 140, 42.3, 74.4), 10: (3.93, 232, 69.0, 108),
         12: (5.75, 232, 145, 269), 14: (8.23, 282, 201, 381), 16: (10.7, 282, 311, 639),
         18: (17.2, 396, 419, 794), 20: (21.0, 396, 597, 1200), 24: (36.9, 520, 1060, 2310),
         30: (67.8, 660, 2190, 4980), 36: (96.0, 660, 3990, 10200)}
_EXC = {1: (0.133, 110, 0.38, 0.12), 1.5: (0.306, 220, 0.48, 0.18), 2: (0.507, 250, 0.86, 0.48),
        3: (2.19, 250, 4.2, 1.65), 4: (4.89, 400, 7.2, 4.05), 6: (14.0, 1275, 19.8, 34.8), 8: (30.0, 1275, 45, 32.2)}
_BOLA = {4: (2.4, 800), 6: (3.9, 1030), 8: (13.5, 4100), 10: (20.8, 7140), 12: (22.2, 10300), 16: (47.2, 12000),
         20: (87.4, 25000), 24: (112, 33300)}


@dataclass
class FactoresPar:
    familia: str
    A: float
    B: float
    C: dict            # ángulo [°] -> C
    nota: str = ""

    def C_en(self, ang: float) -> float:
        pts = sorted(self.C.items())
        xs = [0.0] + [a for a, _ in pts]
        ys = [0.0] + [abs(c) for _, c in pts]
        return _interp(ang, xs, ys)


def _tabla(tab: dict, d: float, idx: int, exp_bajo: float) -> float:
    xs = sorted(tab)
    return _loglog(d, xs, [tab[x][idx] for x in xs], exp_bajo)


def factores_par(cuerpo: str, d: float, blando: bool, d_bola: float | None = None) -> FactoresPar:
    """Factores A, B y C(θ) típicos del estilo rotativo para el diámetro nominal d [in]."""
    if cuerpo == "bola_segmentada":
        return FactoresPar("Bola segmentada (corte en V), junta compuesta", _tabla(_SEG, d, 0, 2.0),
                           _tabla(_SEG, d, 1, 2.0), {60: _tabla(_SEG, d, 2, 2.0), 70: _tabla(_SEG, d, 3, 2.0),
                                                     90: _tabla(_SEG, d, 3, 2.0)})
    if cuerpo in ("mariposa_doble", "mariposa_triple"):
        f = FactoresPar("Mariposa de alto rendimiento (excéntrica)", _tabla(_HP, d, 0, 2.5), _tabla(_HP, d, 1, 2.0),
                        {60: _tabla(_HP, d, 2, 3.0), 75: _tabla(_HP, d, 3, 3.0), 90: _tabla(_HP, d, 4, 3.0)})
        if cuerpo == "mariposa_triple":
            f.familia = "Mariposa triple excéntrica, asiento metálico"
            f.B *= 1.5
            f.nota = ("El asiento metálico laminado de la triple excéntrica se cierra por par: se toma 1,5 veces el "
                      "término B de la doble excéntrica. Confirmar el par de asentamiento con el fabricante.")
        return f
    if cuerpo == "mariposa":
        f = FactoresPar("Mariposa concéntrica", _tabla(_CONC, d, 0, 2.5), _tabla(_CONC, d, 1, 2.0),
                        {60: _tabla(_CONC, d, 2, 3.0), 90: _tabla(_CONC, d, 3, 3.0)})
        if blando:
            f.B += 10 * d ** 2.5
            f.familia += " con asiento elastomérico de interferencia"
            f.nota = ("El asiento elastomérico de interferencia agrega par de arranque (≈ 10·d^2,5 lbf·in); con "
                      "elastómeros envejecidos o servicio con sólidos puede duplicarse.")
        return f
    if cuerpo == "tapon_excentrico":
        return FactoresPar("Tapón excéntrico rotativo, asiento metálico", _tabla(_EXC, d, 0, 2.5),
                           _tabla(_EXC, d, 1, 2.0), {60: _tabla(_EXC, d, 2, 2.5), 90: _tabla(_EXC, d, 3, 2.5)})
    # bolas: el par depende del tamaño de la bola
    db = d_bola or d
    A = _loglog(db, sorted(_BOLA), [_BOLA[x][0] for x in sorted(_BOLA)], 3.0)
    B = _loglog(db, sorted(_BOLA), [_BOLA[x][1] for x in sorted(_BOLA)], 2.0)
    fam = "Bola trunnion (muñones), asientos con resorte"
    nota = ""
    if cuerpo in ("bola_paso_completo", "bola_paso_reducido"):
        A *= 1.5
        fam = "Bola flotante"
        nota = ("En la bola flotante la presión carga la bola contra el asiento de aguas abajo: se toma 1,5 veces "
                "el término A de la bola trunnion.")
    return FactoresPar(fam, A, B, {70: 0.15 * db ** 3, 90: 0.045 * db ** 3}, nota)


# ------------------------------------------------------------------------------- series genéricas


@dataclass(frozen=True)
class Tamano:
    nombre: str
    area_in2: float = 0.0        # área efectiva (diafragma o pistón)
    carrera_max_in: float = 99.0
    P_max_psig: float = 150.0    # presión máxima de la carcasa o del cilindro
    brazo_in: float = 0.0        # en cuarto de vuelta: par de doble efecto a 80 psig [lbf·in]
    vastago_area_in2: float = 0.0   # área del vástago del pistón (lado del vástago)


DIAFRAGMA = [Tamano("D-046", 46, 0.75, 50, 1.5), Tamano("D-069", 69, 1.125, 50, 2.0),
             Tamano("D-105", 105, 1.5, 50, 2.5), Tamano("D-156", 156, 2.0, 50, 3.0),
             Tamano("D-220", 220, 3.0, 40, 4.0), Tamano("D-300", 300, 4.0, 40, 5.0),
             Tamano("D-450", 450, 4.0, 40, 6.0)]
MULTIRESORTE = [Tamano("M-035", 35, 0.75, 87, 1.5), Tamano("M-062", 62, 1.125, 87, 2.0),
                Tamano("M-116", 116, 1.5, 87, 2.5), Tamano("M-186", 186, 2.0, 87, 3.0),
                Tamano("M-279", 279, 3.0, 87, 4.0)]
_BORES = (3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 24)
PISTONES = [Tamano(f"P-{b:02d}", math.pi * b ** 2 / 4, 24.0, 150, 0.5 * b, math.pi * (0.25 * b) ** 2 / 4)
            for b in _BORES]
# Piñón y cremallera y yugo escocés: par de doble efecto a 80 psig (5,5 bar) [lbf·in]
RACK = [Tamano(f"R-{i + 1:02d}", 0, P_max_psig=116, brazo_in=t) for i, t in enumerate(
    (90, 180, 350, 700, 1300, 2200, 3500, 5300, 8000, 11500, 17700, 26500, 40000))]
YUGO = [Tamano(f"Y-{i + 1:02d}", 0, P_max_psig=150, brazo_in=t) for i, t in enumerate(
    (2200, 4400, 8900, 17700, 35400, 70800, 141600, 283000, 566000, 1133000))]
ELEC_LIN_KN = (0.6, 1, 1.5, 2.5, 4, 6, 10, 15, 25, 40, 60, 100, 160, 250)
ELEC_ROT_NM = (35, 60, 100, 150, 250, 400, 600, 1000, 1500, 2500, 4000, 6000, 10000, 16000, 25000, 40000)
VOLANTES_MM = (150, 200, 250, 300, 400, 500, 600, 700, 800)


def par_yugo(theta: float) -> float:
    """Factor de par del yugo escocés simétrico (1 en los extremos, 0,5 a 45°)."""
    c = math.cos(math.radians(theta - 45))
    return min(1.0, 0.5 / (c * c))


# ------------------------------------------------------------------------------------- resultados


@dataclass
class ResultadoActuador:
    tipo: str
    falla: str
    rotativa: bool
    seleccion: str = ""
    ok: bool = True
    filas: list = field(default_factory=list)          # (parámetro, valor, clave de ayuda)
    fuerzas: list = field(default_factory=list)        # (componente, valor, fórmula)
    pasos: list = field(default_factory=list)          # (descripción, fórmula, resultado)
    alertas: list = field(default_factory=list)
    P_req_psig: float | None = None    # presión de aire requerida en el actuador
    P_banco: tuple | None = None       # ajuste de banco (inferior, superior) [psig]
    requerido: float = 0.0             # lbf (lineal) o lbf·in (rotativa), con margen
    doble_efecto: bool = False
    resorte: bool = False
    neumatico: bool = False
    area_in2: float = 0.0


@dataclass
class ResultadoPosicionador:
    permitidas: list
    bloqueadas: dict                   # señal -> motivo
    accion_sugerida: str
    set_sugerido: str
    filas: list = field(default_factory=list)
    alertas: list = field(default_factory=list)


@dataclass
class ResultadoAccesorios:
    filas: list = field(default_factory=list)
    alertas: list = field(default_factory=list)


@dataclass
class ResultadoEquipo:
    actuador: ResultadoActuador
    posicionador: ResultadoPosicionador
    accesorios: ResultadoAccesorios
    datos: Equipo

    def todas_las_alertas(self) -> list[tuple[str, Alerta]]:
        return ([("Actuador", a) for a in self.actuador.alertas]
                + [("Posicionador", a) for a in self.posicionador.alertas]
                + [("Accesorios", a) for a in self.accesorios.alertas])


# ---------------------------------------------------------------------------------- servicio


@dataclass
class Servicio:
    """Datos del cálculo (solapas 1, 2 y 3) que necesita el actuador, en unidades inglesas."""
    rotativa: bool
    cuerpo: str
    nps: float
    rating: int
    cierre: str
    P1: float             # psig a cierre
    P2: float
    dP: float             # psi a cierre
    dP_flujo: float       # psi, máxima con caudal
    cierre_supuesto: bool
    T_C: float
    puerto_in: float
    carrera_in: float | None
    rotacion: float | None
    blando: bool
    balanceado: bool
    balance_auto: bool
    empaque: str | None
    empaque_nombre: str
    casos: list           # (nombre, apertura, ΔP [psi], ΔPef [psi])
    trim: str
    compresible: bool


def _g(kPa_abs: float) -> float:
    return (kPa_abs - P_ATM) / PSI_KPA


def servicio_desde(res) -> Servicio:
    geo = res.geometria
    dim, inst = res.dim, res.inst
    casos = dim.casos
    if dim.cierre is not None:
        P1, P2, sup = dim.cierre.P1, dim.cierre.P2, False
    else:
        P1, P2, sup = max(c.P1 for c in casos), P_ATM, True
    dP_fl = max(s["dP"] for s in res.salidas) / PSI_KPA
    mres = getattr(res, "materiales", None)
    blando = inst.cierre in ("ANSI Clase VI", "Tight Shutoff") and inst.cuerpo in ("globo", "angulo")
    empaque, emp_nom = None, "PTFE simple (supuesto: sin selección de materiales)"
    if mres is not None:
        j = getattr(mres, "juego", None)
        if j is not None and getattr(mres, "juego_coincide", False):
            blando = blando or j.juego.blando
        e = getattr(mres, "empaquetadura", None)
        if e is not None and e.elegida is not None:
            empaque, emp_nom = e.elegida.clave, e.elegida.nombre
    if inst.cuerpo == "globo_liner":
        blando = True
    jaula = "jaula" in dim.trim or "multietapa" in dim.trim
    if dim.balanceado is None:
        bal = jaula and res.nps_valvula >= 3 and (P1 - P2) > 1000
        auto = True
    else:
        bal, auto = bool(dim.balanceado), False
    filas = []
    for c, s in zip(casos, res.salidas):
        dp = s["dP"] / PSI_KPA
        filas.append((c.nombre, s["apertura"], dp, min(dp, s.get("dPchoked", s["dP"]) / PSI_KPA)))
    return Servicio(geo.rotativa, inst.cuerpo, res.nps_valvula, inst.rating, inst.cierre, _g(P1), _g(P2),
                    (P1 - P2) / PSI_KPA, dP_fl, sup, res.T_diseno - 273.15, geo.puerto_in, geo.carrera_in,
                    geo.rotacion_grados, blando, bal, auto, empaque, emp_nom, filas, dim.trim, dim.compresible)


# --------------------------------------------------------------------------- fuerzas (lineal)


@dataclass
class Fuerzas:
    A: float
    A_ab: float
    B: float
    C: float
    D: float
    cierre: float         # A + B + C + D
    apertura: float       # fuerza para abrir
    d_vast: float
    A_vast: float
    A_puerto: float
    A_desb: float
    Kn: float
    tiende_a_cerrar: bool
    textos: dict


def fuerzas_lineales(sv: Servicio, act: DatosActuador) -> Fuerzas:
    d = sv.puerto_in
    PC = math.pi * d
    A_p = math.pi * d * d / 4
    d_v = act.d_vastago_mm / IN_MM if act.d_vastago_mm else vastago_estimado(sv.nps, sv.rating)
    fuelle = sv.empaque == "fuelle"
    A_v = area_fuelle(sv.nps, d_v) if fuelle else math.pi * d_v ** 2 / 4
    up = act.flujo == "Up"
    P1, P2, dP = max(sv.P1, 0.0), max(sv.P2, 0.0), max(sv.dP, 0.0)
    t = {}
    if sv.balanceado:
        A_u = 0.037 * PC
        Pv = P1 if up else P2
        A = dP * A_u + Pv * A_v
        A_ab = max(0.0, dP * A_u)
        t["A"] = (f"ΔP·A_desb + {'P1' if up else 'P2'}·A_vástago = {_n(dP, 1)}·{_n(A_u, 3)} + {_n(Pv, 1)}·"
                  f"{_n(A_v, 3)}")
        t["A_ab"] = f"ΔP·A_desb = {_n(dP, 1)}·{_n(A_u, 3)}"
        cierra = False
    else:
        A_u = A_p
        if up:
            A = dP * A_p + P2 * A_v
            A_ab = 0.0
            t["A"] = f"ΔP·A_puerto + P2·A_vástago = {_n(dP, 1)}·{_n(A_p, 3)} + {_n(P2, 1)}·{_n(A_v, 3)}"
            t["A_ab"] = "0 (el fluido ayuda a abrir)"
            cierra = False
        else:
            A = -(dP * A_p - P1 * A_v)
            A_ab = max(0.0, dP * A_p - P1 * A_v)
            t["A"] = f"−(ΔP·A_puerto − P1·A_vástago) = −({_n(dP, 1)}·{_n(A_p, 3)} − {_n(P1, 1)}·{_n(A_v, 3)})"
            t["A_ab"] = f"ΔP·A_puerto − P1·A_vástago = {_n(dP, 1)}·{_n(A_p, 3)} − {_n(P1, 1)}·{_n(A_v, 3)}"
            cierra = True
    B, t["B"] = carga_asiento(sv.cierre, dP, d, sv.blando, sv.balanceado)
    C, t["C"] = friccion_empaquetadura(sv.empaque, d_v, sv.rating)
    D = 0.0
    t["D"] = "0 (sin fuerzas adicionales declaradas)" + ("; el fuelle reemplaza al área del vástago" if fuelle else "")
    F_c = max(A + B + C + D, C)
    F_a = A_ab + C + D
    Kn = gradiente_negativo(sv.balanceado, cierra, A_u, sv.carrera_in or 1.0, d)
    return Fuerzas(A, A_ab, B, C, D, F_c, F_a, d_v, A_v, A_p, A_u, Kn, cierra, t)


# --------------------------------------------------------------------- dimensionamiento neumático


def _banco(F_c: float, F_a: float, F_fric: float, L: float, area: float, Pd: float, falla: str,
           span_min: float) -> tuple | None:
    """Ajuste de banco (Pbl, Pbu) [psig] de un actuador de resorte; None si no alcanza.

    F_c: fuerza (con margen) que debe dar el actuador en el asiento; F_a: fuerza para abrir; F_fric: la parte
    de fricción (lo que el resorte debe vencer para llegar a la carrera total); Pd: presión disponible.
    """
    if falla == FO:   # el aire cierra; el resorte abre
        Pbl_min = max(F_fric / area, P_BANCO_MIN)
        Pbu_max = Pd - F_c / area
        Pbu_min = F_a / area
        Pbl = math.ceil(Pbl_min * 2) / 2
        Pbu = max(Pbl + span_min, Pbu_min)
        if Pbu > Pbu_max + 1e-9:
            return None
        r = math.ceil(Pbu * 2) / 2
        return Pbl, r if r <= Pbu_max else Pbu
    # FC y FL: el resorte cierra; el aire abre
    Pbl_min = max(F_c / area, P_BANCO_MIN)
    Pbu_max = Pd - F_a / area
    Pbl = math.ceil(Pbl_min * 2) / 2
    Pbu = Pbl + span_min
    if Pbu > Pbu_max + 1e-9:
        return None
    r = math.ceil(Pbu * 2) / 2
    return Pbl, r if r <= Pbu_max else Pbu


def _req_aire(Pbl, Pbu, F_c, F_a, area, falla) -> float:
    return Pbu + (F_c if falla == FO else F_a) / area


def _aire(act: DatosActuador):
    pmin = None if act.P_aire_min is None else act.P_aire_min / PSI_KPA
    pmax = None if act.P_aire_max is None else act.P_aire_max / PSI_KPA
    return pmin, pmax


# ------------------------------------------------------------------------------ evaluación lineal


def _resorte_lineal(r: ResultadoActuador, sv, act, fz: Fuerzas, serie, nombre_tipo, span_fijo=None,
                    piston_doble=False):
    pmin, pmax = _aire(act)
    L = sv.carrera_in
    F_c = fz.cierre * MARGEN_LINEAL
    F_a = fz.apertura * MARGEN_LINEAL
    r.requerido = max(F_c, F_a)
    elegido = None
    for t in serie:
        if L > t.carrera_max_in + 1e-9:
            continue
        Pd = min(pmin, t.P_max_psig)
        area = t.area_in2
        if piston_doble:
            area_ab = t.area_in2 - t.vastago_area_in2
            # el resorte solo lleva a la posición de falla; el aire actúa en ambos sentidos
            if act.falla == FO:
                Fs_min = F_a                      # resorte abre: fuerza en el asiento = apertura
            else:
                Fs_min = F_c
            Ks = 5.0 * area_ab / L               # ajuste de banco ≥ 5 psi
            Fs_max = Fs_min + Ks * L
            if act.falla == FO:
                ok = ETA_PISTON * Pd * area >= F_c + Fs_max and ETA_PISTON * Pd * area_ab >= 0
            else:
                ok = ETA_PISTON * Pd * area_ab >= F_a + Fs_max
            if ok:
                elegido = (t, Pd, Fs_min, Fs_max, Ks)
                break
            continue
        span = span_fijo if span_fijo is not None else max(3.0, Pd / 3)
        span = max(span, fz.Kn * sv.dP_flujo * L / area)
        b = _banco(F_c, F_a, fz.C + fz.D, L, area * (ETA_PISTON if t in PISTONES else 1.0), Pd, act.falla, span)
        if b is not None:
            elegido = (t, Pd, *b)
            break
    if elegido is None:
        r.ok = False
        r.seleccion = f"{nombre_tipo}: ningún tamaño de la serie genérica alcanza con el aire disponible"
        mayor = serie[-1]
        r.alertas.append(Alerta(
            "act_no_alcanza", Severidad.CRITICA, "El actuador no alcanza la fuerza requerida",
            f"Con aire mínimo de {_psi(pmin)} ningún {nombre_tipo.lower()} de la serie genérica (hasta "
            f"{_area(mayor.area_in2)}) da {_N(F_c)} para cerrar y {_N(F_a)} para abrir con carrera "
            f"{_in(L)}.",
            remedios=["Aumentar la presión mínima del aire de instrumentos o usar un amplificador (booster).",
                      "Usar un trim balanceado para bajar la fuerza de desbalance.",
                      "Pasar a un actuador de pistón o electrohidráulico.",
                      "Revisar la clase de cierre: una clase menor baja la carga de asiento."],
            referencia=REF_ACT))
        return
    if piston_doble:
        t, Pd, Fs_min, Fs_max, Ks = elegido
        area_ab = t.area_in2 - t.vastago_area_in2
        bench = Ks * L / area_ab
        r.P_banco = (Fs_min / area_ab, Fs_min / area_ab + bench)
        P_req = (F_c + Fs_max) / (ETA_PISTON * t.area_in2) if act.falla == FO else \
            (F_a + Fs_max) / (ETA_PISTON * area_ab)
        r.P_req_psig = P_req
        r.area_in2 = t.area_in2
        r.seleccion = (f"{nombre_tipo} {t.nombre}: cilindro de {_in(math.sqrt(4 * t.area_in2 / math.pi))} de "
                       f"diámetro, área {_area(t.area_in2)}")
        r.filas += [("Tamaño (serie genérica)", r.seleccion, "act_tamano"),
                    ("Fuerza del resorte en la posición de falla", _N(Fs_min), "act_resorte"),
                    ("Constante del resorte", f"{_n(Ks * LBF_N / IN_MM, 1)} N/mm ({_n(Ks, 0)} lbf/in)",
                     "act_resorte"),
                    ("Ajuste de banco del resorte", f"{_n(bench, 1)} psi (≥ 5 psi)", "act_banco"),
                    ("Presión de aire requerida", _psi(P_req), "act_P_req"),
                    ("Empuje de cierre con aire mínimo",
                     _N(ETA_PISTON * Pd * t.area_in2 + (Fs_min if act.falla != FO else -Fs_max)), "act_empuje"),
                    ("Empuje de apertura con aire mínimo",
                     _N(ETA_PISTON * Pd * area_ab - (Fs_max if act.falla != FO else -Fs_min)), "act_empuje")]
        _verif_aire(r, pmin, pmax, P_req, t.P_max_psig, act.regulado)
        P_al = _P_alimentacion(pmin, pmax, t.P_max_psig, P_req, act.regulado)
        _verif_vastago(r, sv, fz, ETA_PISTON * P_al * t.area_in2 + (Fs_min if act.falla != FO else -Fs_max))
        r.pasos += [("Fuerza del resorte de falla", "F_resorte ≥ fuerza en la posición de falla × margen",
                     _N(Fs_min)),
                    ("Constante mínima del resorte", "Ks = 5 psi × (A_pistón − A_vástago) / carrera",
                     f"{_n(Ks, 0)} lbf/in"),
                    ("Presión requerida", "P = (F + F_resorte máx) / (η·A)", _psi(P_req))]
        return
    t, Pd, Pbl, Pbu = elegido
    area = t.area_in2 * (ETA_PISTON if t in PISTONES else 1.0)
    Ks = (Pbu - Pbl) * area / L
    P_req = _req_aire(Pbl, Pbu, F_c, F_a, area, act.falla)
    r.P_banco, r.P_req_psig, r.area_in2 = (Pbl, Pbu), P_req, t.area_in2
    r.seleccion = f"{nombre_tipo} {t.nombre}: área efectiva {_area(t.area_in2)}, carrera máxima {_in(t.carrera_max_in)}"
    if act.falla == FO:
        emp_c = Pd * area - Pbu * area
        emp_a = Pbl * area
        accion = "Aire para cerrar (resorte abre): actuador de acción directa"
    else:
        emp_c = Pbl * area
        emp_a = Pd * area - Pbu * area
        accion = "Aire para abrir (resorte cierra): actuador de acción inversa"
    r.filas += [("Tamaño (serie genérica)", r.seleccion, "act_tamano"),
                ("Acción del actuador", accion, "act_falla"),
                ("Ajuste de banco (bench set)", f"{_n(Pbl, 1)} – {_n(Pbu, 1)} psig "
                 f"({_n(Pbl / 14.5038, 2)} – {_n(Pbu / 14.5038, 2)} bar g)", "act_banco"),
                ("Constante del resorte", f"{_n(Ks * LBF_N / IN_MM, 1)} N/mm ({_n(Ks, 0)} lbf/in)", "act_resorte"),
                ("Compresión inicial del resorte", _in(Pbl * area / Ks), "act_resorte"),
                ("Carga máxima del resorte", _N(Pbu * area), "act_resorte"),
                ("Presión de aire requerida en el actuador", _psi(P_req), "act_P_req"),
                ("Empuje de cierre disponible", _N(emp_c), "act_empuje"),
                ("Empuje de apertura disponible", _N(emp_a), "act_empuje"),
                ("Margen de presión con aire mínimo", _psi(Pd - P_req), "act_P_req")]
    r.pasos += [("Ajuste de banco inferior", ("Pbl = F_apertura·m / A (el resorte abre)" if act.falla == FO else
                                              "Pbl = F_cierre·m / A (el resorte asienta)"), f"{_n(Pbl, 1)} psig"),
                ("Ajuste de banco superior", "Pbu = Pbl + rango (≥ ⅓ del rango de operación, ≥ Kn·ΔP·L/A)",
                 f"{_n(Pbu, 1)} psig"),
                ("Constante del resorte", "Ks = (Pbu − Pbl)·A / L", f"{_n(Ks, 0)} lbf/in"),
                ("Presión de aire requerida", ("P = Pbu + F_cierre·m / A" if act.falla == FO else
                                               "P = Pbu + F_apertura·m / A"), _psi(P_req))]
    # estabilidad (gradiente negativo)
    Ks_min = fz.Kn * sv.dP_flujo
    if Ks_min > 0:
        r.filas.append(("Constante mínima por gradiente negativo", f"{_n(Ks_min, 0)} lbf/in (Kn = "
                        f"{_n(fz.Kn, 2)} in, ΔP con caudal {_n(sv.dP_flujo, 0)} psi)", "act_gradiente"))
        if Ks < Ks_min * 0.999:
            r.alertas.append(Alerta(
                "act_gradiente", Severidad.ADVERTENCIA, "Resorte blando frente al gradiente negativo",
                f"La constante del resorte ({_n(Ks, 0)} lbf/in) es menor que Kn·ΔP = {_n(Ks_min, 0)} lbf/in: cerca "
                "del asiento la fuerza del fluido crece más rápido que la del resorte y el obturador puede "
                "inestabilizarse (golpeteo contra el asiento).",
                remedios=["Elegir un resorte más rígido (rango de banco más amplio) o más presión de aire.",
                          "El posicionador y el efecto de resorte del aire ayudan, pero no reemplazan el chequeo."],
                referencia=REF_ACT))
    if act.falla == FL:
        r.alertas.append(Alerta(
            "act_fl_resorte", Severidad.ADVERTENCIA, "Última posición con actuador de resorte",
            f"Un {nombre_tipo.lower()} vuelve a la posición del resorte al perder aire. Para mantener la última "
            "posición se necesita una válvula de bloqueo neumático (lock-up) que atrape el aire. Se dimensionó "
            "como falla cierra.", remedios=["Declarar la válvula de bloqueo neumático en 6-Accesorios."],
            referencia=REF_ACT))
    _verif_aire(r, pmin, pmax, P_req, t.P_max_psig, act.regulado)
    # carga del vástago en el asiento: el resorte (falla cierra) o el aire máximo menos el resorte (falla abre)
    P_al = _P_alimentacion(pmin, pmax, t.P_max_psig, P_req, act.regulado)
    _verif_vastago(r, sv, fz, (P_al - Pbu) * area if act.falla == FO else Pbl * area)
    if act.volante:
        F_hw = Pbu * area + (fz.cierre if act.falla == FO else fz.apertura)
        r.filas.append(("Empuje requerido del volante", _N(F_hw), "act_volante"))
        _volante(r, F_hw * 0.25 / (2 * math.pi * 0.30), "lbfin")   # tornillo de 1/4 in de avance, η 0,30


def _verif_aire(r: ResultadoActuador, pmin, pmax, P_req, P_lim, regulado: bool = False):
    if P_req > pmin + 1e-6:
        r.ok = False
        r.alertas.append(Alerta(
            "act_aire_insuficiente", Severidad.CRITICA, "Aire de instrumentos insuficiente",
            f"El actuador necesita {_psi(P_req)} y el aire mínimo disponible es {_psi(pmin)}.",
            remedios=["Elegir un actuador más grande.", "Subir la presión mínima garantizada del aire."],
            referencia=REF_ACT))
    if pmax is not None and pmax > P_lim + 1e-6:
        r.alertas.append(Alerta(
            "act_presion_carcasa", Severidad.INFO if regulado else Severidad.ADVERTENCIA,
            "Aire máximo sobre el límite del actuador",
            f"El aire máximo ({_psi(pmax)}) supera la presión máxima del actuador ({_psi(P_lim)}): "
            + ("el set de aire de la solapa 5 debe regularse por debajo de ese límite." if regulado else
               "se requiere un regulador (set de aire) que limite la alimentación."),
            remedios=[f"Regular la alimentación entre {_psi(P_req)} y {_psi(P_lim)} con el set de aire "
                      "(solapa 5)."], referencia=REF_ACT))


def _P_alimentacion(pmin, pmax, P_lim, P_req, regulado: bool) -> float:
    """Presión máxima que puede llegar al actuador: la del regulador (set de aire) o la de la red."""
    red = min(pmax if pmax is not None else pmin, P_lim)
    if regulado:
        return min(red, max(P_req * 1.10, P_req + 2.0))
    return red


def _verif_vastago(r: ResultadoActuador, sv: Servicio, fz: Fuerzas, F_max: float):
    adm = carga_admisible_vastago(fz.d_vast, sv.T_C)
    r.filas.append(("Carga del vástago en el asiento / admisible", f"{_N(F_max)} / {_N(adm)} (316 endurecido, "
                    f"{_n(sv.T_C, 0)} °C)", "act_vastago"))
    if F_max > adm:
        r.alertas.append(Alerta(
            "act_vastago", Severidad.CRITICA, "Carga del vástago excesiva (pandeo)",
            f"El actuador puede aplicar {_N(F_max)} y el vástago de {_in(fz.d_vast)} admite {_N(adm)} a "
            f"{_n(sv.T_C, 0)} °C.",
            remedios=["Usar un vástago de mayor diámetro o de mayor resistencia (17-4PH, S20910).",
                      "Limitar la presión de alimentación con un regulador.", "Elegir un actuador más chico."],
            referencia=REF_ACT))


def _volante(r: ResultadoActuador, T_lbfin: float, _u=""):
    """Diámetro de volante para no superar la fuerza de aro admisible; si no alcanza, reductor."""
    T_Nm = T_lbfin * LBFIN_NM
    for D in VOLANTES_MM:
        F = T_Nm / (D / 2000)
        if F <= F_ARO_MAX_N:
            r.filas.append(("Volante sugerido", f"Ø {D} mm, fuerza en el aro {_n(F, 0)} N (≤ {_n(F_ARO_MAX_N, 0)} N)",
                            "act_volante"))
            return
    i = math.ceil(T_Nm / (F_ARO_MAX_N * 0.3 * 0.6))     # reductor η 0,6 con volante Ø 600 mm
    r.filas.append(("Volante sugerido", f"Ø 600 mm con reductor de relación ≥ {i}:1 (par {_n(T_Nm, 0)} N·m)",
                    "act_volante"))


def _electrico(r: ResultadoActuador, act, req: float, rotativa: bool, sv=None, fz=None):
    eh = act.tipo == "Electrohidráulico"
    if rotativa:
        T = req * LBFIN_NM * MARGEN_ELEC / MARGEN_ROT
        tam = next((t for t in ELEC_ROT_NM if t >= T), None)
        r.seleccion = (f"{act.tipo}: par nominal {_n(tam, 0)} N·m" if tam else
                       f"{act.tipo}: par requerido {_n(T, 0)} N·m (fuera de la serie genérica)")
        r.filas += [("Par requerido con margen 1,25", f"{_n(T, 0)} N·m", "act_requerido"),
                    ("Tamaño (serie genérica)", r.seleccion, "act_tamano")]
    else:
        F = req * LBF_N / 1000 * MARGEN_ELEC / MARGEN_LINEAL
        tam = next((t for t in ELEC_LIN_KN if t >= F), None)
        r.seleccion = (f"{act.tipo}: empuje nominal {_n(tam, 1)} kN" if tam else
                       f"{act.tipo}: empuje requerido {_n(F, 1)} kN (fuera de la serie genérica)")
        r.filas += [("Empuje requerido con margen 1,25", f"{_n(F, 2)} kN", "act_requerido"),
                    ("Tamaño (serie genérica)", r.seleccion, "act_tamano")]
        if tam and fz is not None:
            _verif_vastago(r, sv, fz, tam * 1000 / LBF_N)
            r.filas.append(("Límite de empuje", "Ajustar el limitador de empuje del actuador por debajo de la "
                            "carga admisible del vástago", "act_vastago"))
    if tam is None:
        r.ok = False
        r.alertas.append(Alerta("act_no_alcanza", Severidad.CRITICA, "Fuera de la serie genérica",
                                "El requerimiento supera la serie genérica de actuadores eléctricos.",
                                remedios=["Consultar actuadores especiales o electrohidráulicos."],
                                referencia=REF_ACT))
    if act.falla != FL and not eh:
        r.alertas.append(Alerta(
            "act_falla_electrico", Severidad.ADVERTENCIA, "Posición de falla con actuador eléctrico",
            f"Un actuador eléctrico queda en la última posición al perder energía. Para «{act.falla}» se "
            "necesita un actuador con resorte de seguridad o reserva de energía (batería o supercapacitor).",
            remedios=["Especificar módulo de falla segura (resorte o reserva de energía).",
                      "O cambiar el modo de falla a Última posición (FL) si el proceso lo admite."],
            referencia=REF_ACT))
    r.filas.append(("Comportamiento ante falla", {FL: "Queda en la última posición", FC: "Cierra (con módulo de "
                    "falla segura)", FO: "Abre (con módulo de falla segura)"}[act.falla] if not eh else
                    {FL: "Queda en la última posición (bloqueo hidráulico)", FC: "Cierra con el resorte del "
                     "cilindro hidráulico", FO: "Abre con el resorte del cilindro hidráulico"}[act.falla],
                    "act_falla"))


def _manual(r: ResultadoActuador, act, req: float, rotativa: bool):
    if act.falla != FL:
        r.alertas.append(Alerta("act_manual_falla", Severidad.ADVERTENCIA, "Actuador manual sin posición de falla",
                                "Un actuador manual queda donde lo deja el operador: no tiene posición de falla "
                                f"«{act.falla}».", remedios=["Cambiar el modo de falla a Última posición (FL)."],
                                referencia=REF_ACT))
    T = req if rotativa else req * 0.25 / (2 * math.pi * 0.30)
    r.seleccion = "Manual: volante" + ("" if rotativa else " con tornillo de avance")
    r.filas.append(("Par en el volante", _Nm(T), "act_volante"))
    _volante(r, T)


# ------------------------------------------------------------------------------------- rotativas


def pares_rotativos(sv: Servicio, act: DatosActuador):
    """Pares de arranque y dinámico [lbf·in] con sus factores."""
    d_bola = None
    if sv.cuerpo == "bola_paso_reducido" or ("reducido" in sv.trim):
        d_bola = sv.puerto_in / 0.95
    f = factores_par(sv.cuerpo, sv.nps, sv.blando, d_bola)
    dP = max(sv.dP, 0.0)
    TB = f.A * dP + f.B
    TD, caso_TD = 0.0, ""
    rot = sv.rotacion or 90.0
    for nombre, h, dp, dpef in sv.casos:
        ang = h * rot
        td = f.C_en(ang) * dpef
        if td > TD:
            TD, caso_TD = td, f"{nombre} ({_n(ang, 0)}°, ΔPef {_n(dpef, 1)} psi)"
    return f, TB, TD, caso_TD


def _rotativo(r: ResultadoActuador, sv: Servicio, act: DatosActuador):
    f, TB, TD, caso = pares_rotativos(sv, act)
    req_b = TB * MARGEN_ROT
    req_d = TD * MARGEN_ROT
    r.requerido = max(req_b, req_d)
    r.fuerzas += [("A (factor de presión)", f"{_n(f.A, 3)} lbf·in/psi", f.familia),
                  ("B (fricción de asientos, cojinetes y empaquetadura)", _Nm(f.B), ""),
                  ("TB, par de arranque", _Nm(TB), f"A·ΔP_cierre + B = {_n(f.A, 3)}·{_n(sv.dP, 1)} + {_n(f.B, 0)}"),
                  ("TD, par dinámico máximo", _Nm(TD), f"C(θ)·ΔPef, caso {caso}" if caso else "C(θ)·ΔPef"),
                  ("Par requerido con margen 1,25", _Nm(r.requerido), "máx(TB, TD) × 1,25")]
    r.pasos += [("Par de arranque", "TB = A·ΔP_cierre + B", _Nm(TB)),
                ("Par dinámico", "TD = C(θ)·ΔPef (ΔPef = mín(ΔP, ΔP bloqueada))", _Nm(TD)),
                ("Par requerido", "T = máx(TB, TD) × 1,25", _Nm(r.requerido))]
    if f.nota:
        r.alertas.append(Alerta("act_factores_par", Severidad.INFO, "Factores de par estimados", f.nota,
                                referencia=REF_PARES))
    tipo = act.tipo
    pmin, pmax = _aire(act)
    rot = sv.rotacion or 90.0
    if tipo in ("Eléctrico", "Electrohidráulico"):
        _electrico(r, act, r.requerido, True)
        return
    if tipo == "Manual":
        _manual(r, act, r.requerido, True)
        return
    _cuarto_vuelta(r, act, TB, TD, pmin, pmax, tipo == "Yugo escocés", rot)  # los lineales se bloquean antes


def _cuarto_vuelta(r, act, TB, TD, pmin, pmax, yugo: bool, rot: float):
    serie = YUGO if yugo else RACK
    req_b, req_d = TB * MARGEN_ROT, TD * MARGEN_ROT
    nombre = "Yugo escocés" if yugo else "Piñón y cremallera"
    resorte = act.falla != FL
    # factor de forma del par en la zona de mayor par dinámico (≈ 70°) y en los extremos
    f_run = par_yugo(min(70.0, rot)) if yugo else 1.0
    f_mid = 0.5 if yugo else 1.0
    elegido = None
    for t in serie:
        Pd = min(pmin, t.P_max_psig)
        T_aire = t.brazo_in * Pd / 80.0           # par de doble efecto, proporcional a la presión
        if not resorte:
            if T_aire >= req_b and T_aire * f_run >= req_d and T_aire * f_mid >= 0.5 * req_d:
                elegido = (t, Pd, T_aire, None, None)
                break
            continue
        # el resorte asienta al final de su carrera y debe vencer el par dinámico al comenzarla
        Tse = max(req_b, req_d / (RESORTE_RATIO * f_run))
        Tss = Tse * RESORTE_RATIO
        ok = (T_aire - Tse >= req_b and (T_aire - Tss) * f_run >= req_d and Tss * f_run >= req_d)
        if ok:
            elegido = (t, Pd, T_aire, Tse, Tss)
            break
    if elegido is None:
        r.ok = False
        r.seleccion = f"{nombre}: ningún tamaño de la serie genérica alcanza"
        r.alertas.append(Alerta("act_no_alcanza", Severidad.CRITICA, "El actuador no alcanza el par requerido",
                                f"Ningún actuador de {nombre.lower()} de la serie genérica da {_Nm(max(req_b, req_d))} "
                                f"con aire mínimo de {_psi(pmin)}.",
                                remedios=["Subir la presión mínima del aire.", "Usar un actuador electrohidráulico."],
                                referencia=REF_ACT))
        return
    t, Pd, T_aire, Tse, Tss = elegido
    r.seleccion = (f"{nombre} {t.nombre} {'con retorno por resorte' if resorte else 'de doble efecto'}: "
                   f"{_Nm(t.brazo_in)} a 5,5 bar")
    r.doble_efecto = not resorte
    r.resorte = resorte
    r.filas += [("Tamaño (serie genérica)", r.seleccion, "act_tamano"),
                ("Par de aire con aire mínimo" + (" (extremos)" if yugo else ""), _Nm(T_aire), "act_empuje")]
    if yugo:
        r.filas.append(("Par de aire en la zona media (45°)", _Nm(T_aire * f_mid), "act_empuje"))
    if resorte:
        r.filas += [("Par del resorte al final (posición de falla)", _Nm(Tse), "act_resorte"),
                    ("Par del resorte al comienzo", _Nm(Tss), "act_resorte"),
                    ("Par de aire al comienzo / al final", f"{_Nm(T_aire - Tse)} / {_Nm(T_aire - Tss)}", "act_empuje")]
        P_req = 80.0 * max(Tse + req_b, Tss + req_d / f_run) / t.brazo_in
    else:
        P_req = 80.0 * max(req_b, req_d / f_run) / t.brazo_in
    r.P_req_psig = P_req
    r.filas.append(("Presión de aire requerida", _psi(P_req), "act_P_req"))
    _verif_aire(r, pmin, pmax, P_req, t.P_max_psig, act.regulado)
    if act.volante:
        r.filas.append(("Mando manual", f"Reductor de volante para {_Nm(max(req_b, req_d))}", "act_volante"))
        _volante(r, max(req_b, req_d))


# ---------------------------------------------------------------------------------------- general

def evaluar_actuador(sv: Servicio, act: DatosActuador) -> ResultadoActuador:
    r = ResultadoActuador(act.tipo, act.falla, sv.rotativa)
    r.neumatico = act.tipo not in ("Eléctrico", "Electrohidráulico", "Manual")
    r.resorte = act.tipo in ("Diafragma y resorte", "Multiresorte y diafragma", "Pistón doble acción con resorte",
                             "Pistón retorno por resorte")
    r.doble_efecto = act.tipo in ("Pistón doble acción con resorte", "Pistón doble acción sin resorte")
    pmin, pmax = _aire(act)
    if r.neumatico and pmin is None:
        r.ok = False
        r.seleccion = "Falta el aire de instrumentos mínimo"
        r.alertas.append(Alerta("act_sin_aire", Severidad.ADVERTENCIA, "Falta el aire de instrumentos",
                                "Para dimensionar un actuador neumático cargue la presión mínima (y máxima) del aire "
                                "de instrumentos disponible en 4-Actuador.", referencia=REF_ACT))
        return r
    if pmin is not None and pmax is not None and pmax < pmin:
        r.alertas.append(Alerta("act_aire_rango", Severidad.ADVERTENCIA, "Aire máximo menor que el mínimo",
                                "La presión máxima del aire de instrumentos es menor que la mínima; se usó la mínima "
                                "para todos los chequeos."))
        pmax = pmin
    if sv.cierre_supuesto:
        r.alertas.append(Alerta(
            "act_cierre_supuesto", Severidad.INFO, "ΔP de cierre supuesta",
            f"No se cargó el caso Tight Shutoff: se supuso cierre contra la presión de entrada máxima "
            f"({_n(sv.P1, 1)} psig) con la salida a presión atmosférica (criterio conservador).",
            remedios=["Cargar el caso Tight Shutoff en 2-Cálculos Válvula con las presiones reales de cierre."],
            referencia=REF_FUERZAS))
    if act.tipo in tipos_bloqueados(sv.rotativa):
        r.ok = False
        if sv.rotativa:
            r.seleccion = "Actuador de vástago deslizante en válvula rotativa"
            txt = (f"Un actuador de {act.tipo.lower()} mueve un vástago lineal: no corresponde a una válvula "
                   "rotativa (mariposa, bola, tapón excéntrico).")
            rem = ["Elegir piñón y cremallera, yugo escocés, eléctrico, electrohidráulico o manual."]
        else:
            r.seleccion = "Actuador rotativo en válvula de vástago deslizante"
            txt = (f"Un actuador de {act.tipo.lower()} es de cuarto de vuelta: no mueve el vástago de una "
                   "válvula de globo o ángulo.")
            rem = ["Elegir diafragma y resorte, pistón, eléctrico lineal o electrohidráulico."]
        r.alertas.append(Alerta("act_incompatible", Severidad.CRITICA, "Actuador incompatible con la válvula", txt,
                                remedios=rem, referencia=REF_ACT))
        return r
    bloq = flujos_bloqueados(sv.cuerpo, sv.rotativa)
    if act.flujo in bloq:
        usado = ("Down" if ("cierra" in sv.trim or "dentro" in sv.trim) else "Up") if not sv.rotativa \
            else "Unidireccional"
        r.alertas.append(Alerta("act_flujo_valvula", Severidad.ADVERTENCIA, "Flow no corresponde a la válvula",
                                f"Se eligió «{act.flujo}», que {bloq[act.flujo]}. Se calculó con «{usado}».",
                                remedios=["Elegir en Flow una opción habilitada para esta válvula."],
                                referencia=REF_ACT))
        act = replace(act, flujo=usado)
    if sv.rotativa:
        r.filas.append(("Método", "Pares de arranque y dinámico de válvula rotativa", "act_metodo"))
        r.filas.append(("Flow (sentido del flujo)", "Bidireccional: cierra con presión desde cualquier lado; el par de "
                        "arranque se toma con la ΔP de cierre máxima en el sentido más desfavorable"
                        if act.flujo == "Bidireccional" else "Unidireccional: cierra con presión en el sentido "
                        "marcado en el cuerpo", "act_flujo"))
        _rotativo(r, sv, act)
    else:
        _lineal(r, sv, act)
    return r


def _lineal(r: ResultadoActuador, sv: Servicio, act: DatosActuador):
    fz = fuerzas_lineales(sv, act)
    r.filas.append(("Método", "Fuerzas A + B + C + D de válvula de vástago deslizante", "act_metodo"))
    t = fz.textos
    r.fuerzas += [("A, desbalance estático (cierre)", _N(fz.A), t["A"]),
                  ("B, carga de asiento", _N(fz.B), t["B"] + f"; PC = π·{_n(sv.puerto_in, 3)} in"),
                  ("C, fricción de empaquetadura", _N(fz.C), t["C"] + f"; vástago {_in(fz.d_vast)}"),
                  ("D, fuerzas adicionales", _N(fz.D), t["D"]),
                  ("Fuerza de cierre A + B + C + D", _N(fz.cierre), ""),
                  ("Fuerza de apertura", _N(fz.apertura), "Término de presión que retiene + C + D (B = 0): "
                   + t["A_ab"])]
    r.filas += [("Obturador", ("Balanceado" if sv.balanceado else "Desbalanceado")
                 + (" (supuesto por el programa)" if sv.balance_auto else ""), "act_obturador"),
                ("Flujo / efecto de la presión", f"{act.flujo}: " + (
                    "obturador balanceado, la presión actúa sobre la corona del sello de balanceo"
                    if sv.balanceado else f"la presión tiende a {'cerrar' if fz.tiende_a_cerrar else 'abrir'}"),
                 "act_flujo"),
                ("Diámetro del vástago", _in(fz.d_vast) + (" (dato)" if act.d_vastago_mm else " (estimado)"),
                 "act_vastago"),
                ("Empaquetadura considerada", sv.empaque_nombre, "act_friccion"),
                ("Carrera nominal", _in(sv.carrera_in), "carrera_nominal")]
    r.pasos += [("Área del puerto", "A_puerto = π·d²/4", f"{_n(fz.A_puerto, 3)} in²"),
                ("Área del vástago" + (" (fuelle)" if sv.empaque == "fuelle" else ""), "A_vástago = π·d_v²/4",
                 f"{_n(fz.A_vast, 3)} in²"),
                ("Desbalance estático", t["A"], _N(fz.A)),
                ("Carga de asiento", t["B"], _N(fz.B)),
                ("Fricción de empaquetadura", t["C"], _N(fz.C)),
                ("Fuerza de cierre", "F = A + B + C + D", _N(fz.cierre)),
                ("Fuerza de apertura", "F = A_apertura + C + D", _N(fz.apertura)),
                ("Fuerza requerida con margen", f"F × {_n(MARGEN_LINEAL, 2)}", _N(max(fz.cierre, fz.apertura)
                                                                                   * MARGEN_LINEAL))]
    _alertas_fuerza(r, sv, act, fz)
    tipo = act.tipo
    if tipo == "Diafragma y resorte":
        _resorte_lineal(r, sv, act, fz, DIAFRAGMA, "Diafragma y resorte")
    elif tipo == "Multiresorte y diafragma":
        _resorte_lineal(r, sv, act, fz, MULTIRESORTE, "Multiresorte y diafragma")
    elif tipo == "Pistón retorno por resorte":
        _resorte_lineal(r, sv, act, fz, PISTONES, "Pistón con retorno por resorte", span_fijo=5.0)
    elif tipo == "Pistón doble acción con resorte":
        _resorte_lineal(r, sv, act, fz, PISTONES, "Pistón de doble acción con resorte", piston_doble=True)
    elif tipo == "Pistón doble acción sin resorte":
        _piston_doble(r, sv, act, fz)
    elif tipo in ("Eléctrico", "Electrohidráulico"):
        r.requerido = max(fz.cierre, fz.apertura) * MARGEN_LINEAL
        _electrico(r, act, r.requerido, False, sv, fz)
    elif tipo == "Manual":
        r.requerido = max(fz.cierre, fz.apertura) * MARGEN_LINEAL
        _manual(r, act, r.requerido, False)


def _piston_doble(r, sv, act, fz):
    pmin, pmax = _aire(act)
    F_c, F_a = fz.cierre * MARGEN_LINEAL, fz.apertura * MARGEN_LINEAL
    r.requerido = max(F_c, F_a)
    for t in PISTONES:
        Pd = min(pmin, t.P_max_psig)
        a_ab = t.area_in2 - t.vastago_area_in2
        if ETA_PISTON * Pd * t.area_in2 >= F_c and ETA_PISTON * Pd * a_ab >= F_a:
            break
    else:
        r.ok = False
        r.seleccion = "Pistón de doble acción: ningún tamaño alcanza"
        r.alertas.append(Alerta("act_no_alcanza", Severidad.CRITICA, "El actuador no alcanza la fuerza requerida",
                                f"Ningún pistón de la serie genérica da {_N(F_c)} con aire de {_psi(pmin)}.",
                                referencia=REF_ACT))
        return
    P_req = max(F_c / (ETA_PISTON * t.area_in2), F_a / (ETA_PISTON * a_ab))
    r.P_req_psig, r.area_in2 = P_req, t.area_in2
    r.seleccion = (f"Pistón de doble acción sin resorte {t.nombre}: cilindro de "
                   f"{_in(math.sqrt(4 * t.area_in2 / math.pi))}, área {_area(t.area_in2)}")
    r.filas += [("Tamaño (serie genérica)", r.seleccion, "act_tamano"),
                ("Empuje de cierre con aire mínimo", _N(ETA_PISTON * Pd * t.area_in2), "act_empuje"),
                ("Empuje de apertura con aire mínimo", _N(ETA_PISTON * Pd * a_ab), "act_empuje"),
                ("Presión de aire requerida", _psi(P_req), "act_P_req")]
    r.pasos.append(("Presión requerida", "P = máx(F_cierre / (η·A), F_apertura / (η·(A − A_vástago)))",
                    _psi(P_req)))
    _verif_aire(r, pmin, pmax, P_req, t.P_max_psig, act.regulado)
    _verif_vastago(r, sv, fz, ETA_PISTON * _P_alimentacion(pmin, pmax, t.P_max_psig, P_req, act.regulado)
                   * t.area_in2)
    if act.volante:
        r.filas.append(("Empuje requerido del volante", _N(max(fz.cierre, fz.apertura)), "act_volante"))
        _volante(r, max(fz.cierre, fz.apertura) * 0.25 / (2 * math.pi * 0.30))


def _alertas_fuerza(r, sv: Servicio, act: DatosActuador, fz: Fuerzas):
    trim_cierra = "cierra" in sv.trim or "dentro" in sv.trim
    if (act.flujo == "Down") != trim_cierra and not sv.rotativa:
        r.alertas.append(Alerta(
            "act_flujo_trim", Severidad.ADVERTENCIA, "Sentido del flujo distinto del trim",
            f"Se eligió flujo {act.flujo} pero el trim de la solapa 2 es de flujo que tiende a "
            f"{'cerrar (Down)' if trim_cierra else 'abrir (Up)'}. El sentido cambia FL, xT y la fuerza del actuador.",
            remedios=["Elegir el mismo sentido en las dos solapas."], referencia=REF_FUERZAS))
    if sv.blando and sv.dP > 1440:
        r.alertas.append(Alerta("act_asiento_blando_dp", Severidad.CRITICA, "ΔP de cierre sobre el límite del PTFE",
                                f"El asiento blando de PTFE admite hasta 1440 psi (99 bar) de ΔP de cierre; la "
                                f"ΔP de cierre es {_n(sv.dP, 0)} psi.",
                                remedios=["Usar asiento metálico clase V."], referencia=REF_FUERZAS))
    if sv.cierre == "ANSI Clase V" and not sv.blando:
        r.alertas.append(Alerta("act_clase_v", Severidad.INFO, "Vida del cierre clase V",
                                "Con asiento metálico clase V, una carga de asiento de unas 800 lbf por pulgada de "
                                "perímetro del puerto prolonga la vida del cierre (a costa de un actuador mayor).",
                                referencia=REF_FUERZAS))
    if sv.balanceado and sv.cierre in ("ANSI Clase V", "ANSI Clase VI", "Tight Shutoff"):
        r.alertas.append(Alerta("act_balance_cierre", Severidad.INFO, "Sello de balanceo y cierre alto",
                                "Con obturador balanceado y clase V o superior el sello de balanceo también debe "
                                "cerrar: se usó la carga de asiento del sello (mayor). Verificar con el fabricante.",
                                referencia=REF_FUERZAS))
    if sv.balance_auto and sv.balanceado:
        r.alertas.append(Alerta("act_balance_supuesto", Severidad.INFO, "Obturador balanceado supuesto",
                                "No se indicó el balanceo en 2-Cálculos Válvula: con trim de jaula, ΔP de cierre "
                                "mayor que 10 bar y válvula de 3\" o más se supuso balanceado.",
                                referencia=REF_FUERZAS))


# ------------------------------------------------------------------------------------ posicionador


def _familia_senal(tipo: str) -> tuple:
    if tipo == "Neumático":
        return tuple(SENAL_PSI)
    if tipo.startswith("Foundation"):
        return ("Foundation FieldBus",)
    return SENAL_MA


def evaluar_posicionador(pos: DatosPosicionador, act: DatosActuador, ra: ResultadoActuador) -> ResultadoPosicionador:
    al: list[Alerta] = []
    bloq: dict[str, str] = {}
    familia = _familia_senal(pos.tipo)
    for s in SENALES:
        if s not in familia:
            bloq[s] = f"no corresponde a un posicionador {pos.tipo.lower()}"
    P_req = ra.P_req_psig
    if P_req is not None:
        for s, (lo, hi) in SENAL_PSI.items():
            if s in bloq:
                continue
            if hi < P_req - 1e-6:
                bloq[s] = f"su máximo ({hi} psi) no alcanza los {_n(P_req, 1)} psi que necesita el actuador"
            elif ra.P_banco and hi < ra.P_banco[1] - 1e-6:
                bloq[s] = f"no cubre el ajuste de banco superior ({_n(ra.P_banco[1], 1)} psi)"
    if not ra.neumatico:
        for s in SENAL_PSI:
            bloq.setdefault(s, "el actuador no es neumático")
    permitidas = [s for s in SENALES if s not in bloq]
    if pos.senal in bloq:
        al.append(Alerta("pos_senal_bloqueada", Severidad.CRITICA if pos.senal in SENAL_PSI else
                         Severidad.ADVERTENCIA, "Señal de entrada no apta",
                         f"La señal «{pos.senal}» quedó bloqueada: {bloq[pos.senal]}.",
                         remedios=["Elegir una de las señales habilitadas: " + ", ".join(permitidas) + "."
                                   if permitidas else "Revisar el tipo de posicionador y el actuador."],
                         referencia=REF_ACT))
    # acción sugerida
    if pos.tipo != "Neumático" and pos.tipo != "Electroneumático":
        sug = "Configurable"
    elif ra.doble_efecto or act.tipo == "Pistón doble acción sin resorte":
        sug = "Doble"
    else:
        sug = "Directo" if act.falla != FO else "Inverso"
    if ra.doble_efecto and pos.accion not in ("Doble", "Configurable"):
        al.append(Alerta("pos_accion", Severidad.ADVERTENCIA, "Acción del posicionador incompatible",
                         "Un actuador de doble efecto necesita un posicionador de acción doble (dos salidas).",
                         remedios=["Elegir acción «Doble»."], referencia=REF_ACT))
    elif not ra.doble_efecto and pos.accion == "Doble" and ra.neumatico:
        al.append(Alerta("pos_accion", Severidad.INFO, "Posicionador doble en actuador de simple efecto",
                         "La salida doble no se usa en un actuador de simple efecto: tape una salida o use acción "
                         "directa o inversa."))
    elif pos.accion in ("Directo", "Inverso") and sug in ("Directo", "Inverso") and pos.accion != sug:
        al.append(Alerta("pos_accion", Severidad.INFO, "Acción del posicionador",
                         f"Con falla {act.falla} y señal creciente para abrir, la acción habitual es «{sug}». Verifique "
                         "la convención de la señal del sistema de control.", referencia=REF_ACT))
    # set de aire
    set_sug = "Otro"
    if P_req is not None:
        set_sug = "Ajustable 0-30 psi" if P_req <= 27 else "Ajustable 0-80 psi" if P_req <= 75 else "Otro"
    filas = [("Tag", pos.tag or "—", "pos_tag"), ("Tipo", pos.tipo, "pos_tipo"),
             ("Señal de entrada", pos.senal, "pos_senal"), ("Acción", pos.accion, "pos_accion"),
             ("Manómetros", "Sí" if pos.manometros else "No", "pos_manometros"),
             ("Set de aire de instrumentos", "Sí" if pos.set_aire else "No", "pos_set")]
    if pos.set_aire:
        filas.append(("Salida del set de aire", pos.salida_set, "pos_set"))
        rango = {"Ajustable 0-30 psi": 30, "Ajustable 0-80 psi": 80}.get(pos.salida_set)
        if rango and P_req is not None and rango < P_req:
            al.append(Alerta("pos_set_rango", Severidad.CRITICA, "Rango del set de aire insuficiente",
                             f"El set de aire regula hasta {rango} psi y el actuador necesita {_n(P_req, 1)} psi.",
                             remedios=[f"Elegir «{set_sug}»."], referencia=REF_ACT))
        elif rango == 80 and P_req is not None and P_req <= 27:
            al.append(Alerta("pos_set_rango", Severidad.INFO, "Set de aire de rango amplio",
                             "El actuador trabaja por debajo de 30 psi: un set de 0-30 psi regula con más precisión y "
                             "protege la carcasa del diafragma.", remedios=["Elegir «Ajustable 0-30 psi»."]))
    elif ra.neumatico:
        al.append(Alerta("pos_sin_set", Severidad.ADVERTENCIA, "Sin set de aire",
                         "Sin filtro-regulador el posicionador y el actuador reciben el aire sin filtrar ni regular.",
                         remedios=[f"Agregar set de aire «{set_sug}»."], referencia=REF_ACT))
    if pos.tipo in ("Neumático",) and act.tipo in ("Eléctrico", "Electrohidráulico", "Manual"):
        al.append(Alerta("pos_tipo", Severidad.ADVERTENCIA, "Posicionador neumático en actuador no neumático",
                         f"Un posicionador neumático no aplica a un actuador {act.tipo.lower()}."))
    filas.append(("Señales habilitadas", ", ".join(permitidas) or "ninguna", "pos_senal"))
    return ResultadoPosicionador(permitidas, bloq, sug, set_sug, filas, al)


# -------------------------------------------------------------------------------------- accesorios


def evaluar_accesorios(acc: DatosAccesorios, act: DatosActuador, ra: ResultadoActuador, sv: Servicio,
                       agrio: bool = False) -> ResultadoAccesorios:
    al: list[Alerta] = []
    filas = []
    for k, et in (("boosters", "Boosters (amplificadores de volumen)"), ("quick_exhaust", "Quick exhaust (escape "
                  "rápido)"), ("bloqueo", "Válvulas de bloqueo neumático"), ("cambio", "Válvula de cambio "
                                                                               "(switching valve)")):
        v = getattr(acc, k).strip()
        if v:
            filas.append((et, v, "acc_" + k))
    if acc.solenoide:
        t = f"{acc.sol_accion}, {acc.sol_vias}, {acc.sol_material}, puertos {acc.sol_puerto}, {acc.sol_voltaje}"
        if acc.sol_potencia.strip():
            t += f", {acc.sol_potencia.strip()}"
        filas.append(("Válvula solenoide", t, "acc_solenoide"))
        cierra = "cerrar" in acc.sol_accion
        if act.falla in (FC, FO) and ra.neumatico:
            seguro = cierra == (act.falla == FC)
            if acc.sol_accion.startswith("Desenergiza") and not seguro:
                al.append(Alerta("acc_sol_falla", Severidad.CRITICA, "Solenoide contraria a la posición de falla",
                                 f"La solenoide «{acc.sol_accion}» ventea el actuador al desenergizarse y la válvula va "
                                 f"a su posición de falla ({act.falla}): no puede llevarla a la posición opuesta.",
                                 remedios=["Elegir «Desenergiza para " + ("cerrar" if act.falla == FC else "abrir")
                                           + "» o cambiar el modo de falla."], referencia=REF_ACT))
            if acc.sol_accion.startswith("Energiza"):
                al.append(Alerta("acc_sol_energiza", Severidad.ADVERTENCIA, "Solenoide energiza para actuar",
                                 "Con «energiza para actuar» un corte de energía no lleva la válvula a la posición "
                                 "segura: la función de seguridad depende de la alimentación eléctrica.",
                                 remedios=["Preferir «desenergiza para actuar» (a prueba de fallas)."],
                                 referencia="IEC 61508 / IEC 61511 (principio de falla segura)"))
        if ra.doble_efecto and acc.sol_vias != "4 vías":
            al.append(Alerta("acc_sol_vias", Severidad.ADVERTENCIA, "Vías de la solenoide",
                             "Un actuador de doble efecto se comanda con solenoide de 4 vías (5/2): presuriza un lado y "
                             "ventea el otro.", remedios=["Elegir 4 vías."], referencia=REF_ACT))
        elif not ra.doble_efecto and ra.neumatico and acc.sol_vias != "3 vías":
            al.append(Alerta("acc_sol_vias", Severidad.ADVERTENCIA, "Vías de la solenoide",
                             "Un actuador de simple efecto (resorte) se ventea con solenoide de 3 vías (3/2); la de 2 "
                             "vías no ventea y la de 4 vías es para doble efecto.", remedios=["Elegir 3 vías."],
                             referencia=REF_ACT))
        if acc.sol_material == "Latón" and agrio:
            al.append(Alerta("acc_sol_material", Severidad.ADVERTENCIA, "Solenoide de latón en ambiente agrio",
                             "El latón se corroe con H₂S y amoníaco del ambiente.",
                             remedios=["Usar solenoide de acero inoxidable."]))
        if ra.area_in2 >= 220 and acc.sol_puerto == '1/4"':
            al.append(Alerta("acc_sol_puerto", Severidad.INFO, "Puerto de solenoide chico para el actuador",
                             f"Con un actuador de {_area(ra.area_in2)} una solenoide de 1/4\" ventea lento.",
                             remedios=["Usar puerto 1/2\" o agregar un escape rápido (quick exhaust)."]))
    if acc.limites:
        t = f"{acc.lim_tipo}, contactos {acc.lim_contactos}"
        if acc.lim_voltaje.strip():
            t += f", {acc.lim_voltaje.strip()}"
        if acc.lim_corriente.strip():
            t += f", {acc.lim_corriente.strip()}"
        if "AC" in acc.lim_voltaje.upper() or not acc.lim_voltaje.strip():
            t += f", {acc.lim_frecuencia}"
        filas.append(("Límites de carrera", t, "acc_limites"))
    if act.falla == FL and ra.resorte and not acc.bloqueo.strip():
        al.append(Alerta("acc_lockup", Severidad.ADVERTENCIA, "Falta la válvula de bloqueo neumático",
                         "La falla en última posición con actuador de resorte requiere una válvula de bloqueo "
                         "(lock-up) que atrape el aire del actuador.",
                         remedios=["Completar «Válvulas de bloqueo neumático» en 6-Accesorios."], referencia=REF_ACT))
    if act.falla in (FC, FO) and act.tipo == "Pistón doble acción sin resorte" and not acc.cambio.strip():
        al.append(Alerta("acc_switching", Severidad.ADVERTENCIA, "Falta tanque de reserva y válvula de cambio",
                         f"Un pistón de doble acción sin resorte no tiene posición de falla propia. Para «{act.falla}» "
                         "necesita un tanque de volumen y una válvula de cambio (switching valve) que lo descargue "
                         "sobre el lado correcto al perder el aire.",
                         remedios=["Completar «Válvula de cambio» en 6-Accesorios y dimensionar el tanque."],
                         referencia=REF_ACT))
    return ResultadoAccesorios(filas, al)


def evaluar(res, eq: Equipo) -> ResultadoEquipo:
    sv = servicio_desde(res)
    eq.actuador.regulado = eq.posicionador.set_aire
    ra = evaluar_actuador(sv, eq.actuador)
    rp = evaluar_posicionador(eq.posicionador, eq.actuador, ra)
    agrio = bool(getattr(getattr(res, "materiales", None), "agrio", False))
    rc = evaluar_accesorios(eq.accesorios, eq.actuador, ra, sv, agrio)
    return ResultadoEquipo(ra, rp, rc, eq)
