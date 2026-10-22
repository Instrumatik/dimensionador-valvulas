"""Conversión de unidades (Sistema Internacional e Imperial).

Internamente el núcleo de cálculo trabaja SIEMPRE en estas unidades base:

    presión absoluta  -> kPa (abs)
    temperatura       -> K
    caudal volumétrico de líquido / caudal real -> m³/h
    caudal másico     -> kg/h
    caudal de gas en condiciones normales -> m³/h normales (0 °C, 101,325 kPa)
    densidad          -> kg/m³
    viscosidad dinámica -> Pa·s
    viscosidad cinemática -> m²/s
    diámetro          -> mm
    velocidad         -> m/s

Las funciones ``a_base`` y ``desde_base`` convierten cualquier unidad
admitida hacia/desde la unidad base de su magnitud. Las presiones
manométricas (barg, psig, kPag) requieren la presión atmosférica local,
que por defecto es 101,325 kPa.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

P_ATM_KPA = 101.325

# Condiciones de referencia para caudal de gas "normal" y "estándar"
T_NORMAL_K = 273.15          # 0 °C, 101,325 kPa  (Nm³/h)
T_ESTANDAR_K = 288.15        # 15 °C, 101,325 kPa (Sm³/h)
T_SCF_K = 288.706            # 60 °F, 14,696 psia (scf)
P_SCF_KPA = 101.325


@dataclass(frozen=True)
class Unidad:
    simbolo: str
    nombre: str
    a_base: Callable[[float], float]
    desde_base: Callable[[float], float]
    manometrica: bool = False


def _lineal(factor: float, offset: float = 0.0):
    """Unidad lineal: base = valor*factor + offset."""
    return (lambda v: v * factor + offset, lambda b: (b - offset) / factor)


def _u(simbolo, nombre, factor, offset=0.0, manometrica=False):
    a, d = _lineal(factor, offset)
    return Unidad(simbolo, nombre, a, d, manometrica)


PSI_KPA = 6.894757293168361
LB_KG = 0.45359237
IN_MM = 25.4
FT_M = 0.3048
GAL_M3 = 3.785411784e-3
BBL_M3 = 0.158987294928
LBF_N = 4.4482216152605

MAGNITUDES: dict[str, dict[str, Unidad]] = {
    "presion": {
        u.simbolo: u
        for u in [
            _u("kPa a", "kilopascal absoluto", 1.0),
            _u("kPa g", "kilopascal manométrico", 1.0, P_ATM_KPA, True),
            _u("bar a", "bar absoluto", 100.0),
            _u("bar g", "bar manométrico", 100.0, P_ATM_KPA, True),
            _u("MPa a", "megapascal absoluto", 1000.0),
            _u("MPa g", "megapascal manométrico", 1000.0, P_ATM_KPA, True),
            _u("psia", "libra por pulgada² absoluta", PSI_KPA),
            _u("psig", "libra por pulgada² manométrica", PSI_KPA, P_ATM_KPA, True),
            _u("kg/cm² a", "kilogramo-fuerza por cm² absoluto", 98.0665),
            _u("kg/cm² g", "kilogramo-fuerza por cm² manométrico", 98.0665, P_ATM_KPA, True),
        ]
    },
    # Diferencias de presión (sin offset atmosférico)
    "presion_dif": {
        u.simbolo: u
        for u in [
            _u("kPa", "kilopascal", 1.0),
            _u("bar", "bar", 100.0),
            _u("MPa", "megapascal", 1000.0),
            _u("psi", "libra por pulgada²", PSI_KPA),
            _u("kg/cm²", "kilogramo-fuerza por cm²", 98.0665),
        ]
    },
    "temperatura": {
        u.simbolo: u
        for u in [
            _u("K", "kelvin", 1.0),
            _u("°C", "grado Celsius", 1.0, 273.15),
            _u("°F", "grado Fahrenheit", 5.0 / 9.0, 273.15 - 32.0 * 5.0 / 9.0),
            _u("°R", "grado Rankine", 5.0 / 9.0),
        ]
    },
    # Diferencia de temperatura (sobrecalentamiento): sin desplazamiento de cero
    "temperatura_dif": {u.simbolo: u for u in [_u("K", "kelvin", 1.0), _u("°C", "grado Celsius", 1.0),
                                               _u("°F", "grado Fahrenheit", 5.0 / 9.0)]},
    "caudal_vol": {
        u.simbolo: u
        for u in [
            _u("m³/h", "metro cúbico por hora", 1.0),
            _u("m³/s", "metro cúbico por segundo", 3600.0),
            _u("L/s", "litro por segundo", 3.6),
            _u("L/min", "litro por minuto", 0.06),
            _u("gpm", "galón US por minuto", GAL_M3 * 60.0),
            _u("bbl/d", "barril por día", BBL_M3 / 24.0),
            _u("ft³/h", "pie cúbico por hora", FT_M ** 3),
        ]
    },
    "caudal_masico": {
        u.simbolo: u
        for u in [
            _u("kg/h", "kilogramo por hora", 1.0),
            _u("kg/s", "kilogramo por segundo", 3600.0),
            _u("t/h", "tonelada por hora", 1000.0),
            _u("lb/h", "libra por hora", LB_KG),
            _u("lb/s", "libra por segundo", LB_KG * 3600.0),
        ]
    },
    # Caudal de gas en condiciones de referencia, base = Nm³/h (0 °C, 101,325 kPa)
    "caudal_gas_std": {
        u.simbolo: u
        for u in [
            _u("Nm³/h", "metro cúbico normal por hora (0 °C; 101,325 kPa)", 1.0),
            _u("Sm³/h", "metro cúbico estándar por hora (15 °C; 101,325 kPa)", T_NORMAL_K / T_ESTANDAR_K),
            _u("scfh", "pie cúbico estándar por hora (60 °F; 14,696 psia)", FT_M ** 3 * T_NORMAL_K / T_SCF_K),
            _u("MMSCFD", "millón de pies cúbicos estándar por día", 1e6 / 24.0 * FT_M ** 3 * T_NORMAL_K / T_SCF_K),
        ]
    },
    "densidad": {
        u.simbolo: u
        for u in [
            _u("kg/m³", "kilogramo por metro cúbico", 1.0),
            _u("g/cm³", "gramo por centímetro cúbico", 1000.0),
            _u("lb/ft³", "libra por pie cúbico", LB_KG / FT_M ** 3),
        ]
    },
    "viscosidad_din": {
        u.simbolo: u
        for u in [
            _u("Pa·s", "pascal segundo", 1.0),
            _u("cP", "centipoise", 1e-3),
            _u("mPa·s", "milipascal segundo", 1e-3),
            _u("lb/(ft·s)", "libra por pie segundo", LB_KG / FT_M),
        ]
    },
    "viscosidad_cin": {
        u.simbolo: u
        for u in [
            _u("m²/s", "metro cuadrado por segundo", 1.0),
            _u("cSt", "centistoke", 1e-6),
            _u("ft²/s", "pie cuadrado por segundo", FT_M ** 2),
        ]
    },
    "longitud": {
        u.simbolo: u
        for u in [
            _u("mm", "milímetro", 1.0),
            _u("cm", "centímetro", 10.0),
            _u("m", "metro", 1000.0),
            _u("in", "pulgada", IN_MM),
        ]
    },
    "carrera": {u.simbolo: u for u in [_u("mm", "milímetro", 1.0), _u("in", "pulgada", IN_MM)]},
    "velocidad": {
        u.simbolo: u
        for u in [
            _u("m/s", "metro por segundo", 1.0),
            _u("ft/s", "pie por segundo", FT_M),
        ]
    },
    # Masa molar o gravedad específica de gas (relativa al aire, M_aire = 28,9647 kg/kmol)
    "masa_molar": {u.simbolo: u for u in [_u("kg/kmol", "kilogramo por kilomol", 1.0),
                                          _u("lb/lbmol", "libra por libra-mol", 1.0),
                                          _u("SG (aire = 1)", "gravedad específica respecto del aire", 28.9647)]},
    "area": {
        u.simbolo: u
        for u in [
            _u("mm²", "milímetro cuadrado", 1.0),
            _u("cm²", "centímetro cuadrado", 100.0),
            _u("in²", "pulgada cuadrada", IN_MM ** 2),
        ]
    },
    "distancia": {u.simbolo: u for u in [_u("m", "metro", 1.0), _u("ft", "pie", FT_M)]},
    "fuerza": {u.simbolo: u for u in [_u("N", "newton", 1.0), _u("kN", "kilonewton", 1000.0),
                                      _u("lbf", "libra fuerza", LBF_N)]},
    "par": {u.simbolo: u for u in [_u("N·m", "newton metro", 1.0), _u("lbf·in", "libra fuerza pulgada", LBF_N * IN_MM / 1000),
                                   _u("lbf·ft", "libra fuerza pie", LBF_N * FT_M)]},
    "adimensional": {u.simbolo: u for u in [_u("-", "adimensional", 1.0)]},
    "fraccion": {u.simbolo: u for u in [_u("%", "porcentaje", 0.01), _u("-", "fracción", 1.0)]},
}

UNIDAD_BASE = {
    "presion": "kPa a",
    "presion_dif": "kPa",
    "temperatura": "K",
    "caudal_vol": "m³/h",
    "caudal_masico": "kg/h",
    "caudal_gas_std": "Nm³/h",
    "densidad": "kg/m³",
    "viscosidad_din": "Pa·s",
    "viscosidad_cin": "m²/s",
    "longitud": "mm",
    "carrera": "mm",
    "velocidad": "m/s",
    "masa_molar": "kg/kmol",
    "area": "mm²",
    "distancia": "m",
    "fuerza": "N",
    "par": "N·m",
    "temperatura_dif": "K",
    "adimensional": "-",
    "fraccion": "-",
}

# Juego de unidades preferido para mostrar en cada sistema
SISTEMAS = {
    "SI": {
        "presion": "bar a", "presion_dif": "bar", "temperatura": "°C",
        "caudal_vol": "m³/h", "caudal_masico": "kg/h", "caudal_gas_std": "Nm³/h",
        "densidad": "kg/m³", "viscosidad_din": "cP", "viscosidad_cin": "cSt",
        "longitud": "mm", "carrera": "mm", "velocidad": "m/s", "masa_molar": "kg/kmol", "adimensional": "-",
        "area": "mm²", "distancia": "m", "temperatura_dif": "°C", "fuerza": "N", "par": "N·m",
        "fraccion": "%",
    },
    "Imperial": {
        "presion": "psia", "presion_dif": "psi", "temperatura": "°F",
        "caudal_vol": "gpm", "caudal_masico": "lb/h", "caudal_gas_std": "scfh",
        "densidad": "lb/ft³", "viscosidad_din": "cP", "viscosidad_cin": "cSt",
        "longitud": "in", "carrera": "in", "velocidad": "ft/s", "masa_molar": "lb/lbmol", "adimensional": "-",
        "area": "in²", "distancia": "ft", "temperatura_dif": "°F", "fuerza": "lbf", "par": "lbf·in",
        "fraccion": "%",
    },
}


class ErrorUnidad(ValueError):
    pass


def _buscar(magnitud: str, simbolo: str) -> Unidad:
    try:
        return MAGNITUDES[magnitud][simbolo]
    except KeyError:
        raise ErrorUnidad(f"Unidad «{simbolo}» no reconocida para la magnitud «{magnitud}».") from None


def a_base(valor: float, magnitud: str, simbolo: str, p_atm_kpa: float = P_ATM_KPA) -> float:
    u = _buscar(magnitud, simbolo)
    if u.manometrica:
        return u.a_base(valor) - P_ATM_KPA + p_atm_kpa
    return u.a_base(valor)


def desde_base(valor: float, magnitud: str, simbolo: str, p_atm_kpa: float = P_ATM_KPA) -> float:
    u = _buscar(magnitud, simbolo)
    if u.manometrica:
        return u.desde_base(valor + P_ATM_KPA - p_atm_kpa)
    return u.desde_base(valor)


def convertir(valor: float, magnitud: str, de: str, a: str, p_atm_kpa: float = P_ATM_KPA) -> float:
    return desde_base(a_base(valor, magnitud, de, p_atm_kpa), magnitud, a, p_atm_kpa)


def unidades_de(magnitud: str) -> list[str]:
    return list(MAGNITUDES[magnitud].keys())


# Relación entre coeficientes: Cv (gpm US, psi) = 1,156 · Kv (m³/h, bar)
CV_POR_KV = 1.0 / 0.865


def kv_a_cv(kv: float) -> float:
    return kv * CV_POR_KV


def cv_a_kv(cv: float) -> float:
    return cv / CV_POR_KV
