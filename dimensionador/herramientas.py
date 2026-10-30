"""Herramientas rápidas de la barra del encabezado (sin interfaz gráfica, para poder probarlas).

Conversor de unidades, propiedades de fluidos en un punto y en saturación, tablas de tubería,
presión-temperatura por clase y calculadoras cortas. Reutilizan los mismos módulos que el cálculo de la
válvula (``unidades``, ``propiedades``, ``tuberias``, ``asme_b16_34``), así que sus resultados coinciden con
los del programa. Ninguna toca el proyecto abierto.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import asme_b16_34 as B, propiedades as P, tuberias as T, unidades as U

# ----------------------------------------------------------------------------- conversor de unidades
# Kv es la base: Cv = Kv / 0,865
_COEF = {"Kv": U.Unidad("Kv", "coeficiente de caudal métrico (m³/h con 1 bar)", lambda v: v, lambda b: b),
         "Cv": U.Unidad("Cv", "coeficiente de caudal US (gpm con 1 psi)", U.cv_a_kv, U.kv_a_cv)}

# (clave, nombre) en el orden del desplegable
MAGNITUDES = (
    ("presion", "Presión (absoluta y manométrica)"),
    ("presion_dif", "Diferencia de presión"),
    ("temperatura", "Temperatura"),
    ("temperatura_dif", "Diferencia de temperatura"),
    ("caudal_vol", "Caudal volumétrico"),
    ("caudal_masico", "Caudal másico"),
    ("caudal_gas_std", "Caudal de gas en condiciones de referencia"),
    ("coeficiente", "Coeficiente de caudal (Cv / Kv)"),
    ("densidad", "Densidad"),
    ("viscosidad_din", "Viscosidad dinámica"),
    ("viscosidad_cin", "Viscosidad cinemática"),
    ("longitud", "Longitud (diámetros, espesores)"),
    ("distancia", "Distancia"),
    ("area", "Área"),
    ("velocidad", "Velocidad"),
    ("fuerza", "Fuerza"),
    ("par", "Par (torque)"),
    ("masa_molar", "Masa molar / gravedad específica de gas"),
)


def unidades(magnitud: str) -> dict[str, U.Unidad]:
    return _COEF if magnitud == "coeficiente" else U.MAGNITUDES[magnitud]


def convertir(valor: float, magnitud: str, de: str, a: str, p_atm_kpa: float = U.P_ATM_KPA) -> float:
    if magnitud != "coeficiente":
        return U.convertir(valor, magnitud, de, a, p_atm_kpa)
    return _COEF[a].desde_base(_COEF[de].a_base(valor))


def convertir_todas(valor: float, magnitud: str, de: str,
                    p_atm_kpa: float = U.P_ATM_KPA) -> list[tuple[str, str, float]]:
    """El valor expresado en todas las unidades de la magnitud: (símbolo, nombre, valor)."""
    return [(s, u.nombre, convertir(valor, magnitud, de, s, p_atm_kpa)) for s, u in unidades(magnitud).items()]


def p_atm_altitud(z_m: float) -> float:
    """Presión atmosférica [kPa] a la altitud dada (atmósfera estándar ISA, válida hasta 11 km)."""
    return U.P_ATM_KPA * (1 - 2.25577e-5 * z_m) ** 5.25588


# ----------------------------------------------------------------------------- propiedades de fluidos
@dataclass
class Propiedad:
    nombre: str
    valor: float | str | None
    magnitud: str = ""        # magnitud de ``unidades`` para convertir; "" = texto o unidad fija
    unidad: str = ""          # unidad fija cuando no hay magnitud


FASES = {"liquid": "Líquido", "gas": "Gas", "supercritical": "Supercrítico",
         "supercritical_gas": "Supercrítico (tipo gas)", "supercritical_liquid": "Supercrítico (tipo líquido)",
         "twophase": "Bifásico", "critical_point": "Punto crítico"}


def _cp(clave, *args):
    try:
        v = P.CP.PropsSI(clave, *args)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def propiedades_punto(fluido: str, P_kPa: float, T_K: float, composicion: dict | None = None) -> list[Propiedad]:
    """Propiedades termofísicas del fluido a P y T (CoolProp, la misma biblioteca del cálculo)."""
    n = P._cp_nombre(fluido, composicion)
    a = ("T", T_K, "P", P_kPa * 1000, n)
    try:
        fase = P.CP.PhaseSI(*a)
    except Exception as e:
        raise P.ErrorPropiedades(f"No se pudieron obtener las propiedades de {fluido} a esas condiciones: {e}") from None
    rho = _cp("D", *a)
    mu = _cp("V", *a)
    cp, cv, c = _cp("C", *a), _cp("O", *a), _cp("A", *a)
    M = _cp("M", *a)
    mezcla = "&" in n          # en mezclas CoolProp no da punto crítico ni saturación en forma confiable (y tarda)
    Tc, Pc = (None, None) if mezcla else (_cp("Tcrit", n), _cp("Pcrit", n))
    Pv = _cp("P", "T", T_K, "Q", 0, n) if Tc and T_K < Tc else None
    Tsat = _cp("T", "P", P_kPa * 1000, "Q", 0, n) if Pc and P_kPa * 1000 < Pc else None
    kappa = rho * c ** 2 / (P_kPa * 1000) if rho and c else None
    filas = [
        Propiedad("Fase", FASES.get(fase, fase)),
        Propiedad("Densidad", rho, "densidad"),
        Propiedad("Viscosidad dinámica", mu, "viscosidad_din"),
        Propiedad("Viscosidad cinemática", mu / rho if mu and rho else None, "viscosidad_cin"),
        Propiedad("Masa molar", M * 1000 if M else None, "masa_molar"),
        Propiedad("Factor de compresibilidad Z", _cp("Z", *a), unidad="-"),
        Propiedad("Calor específico cp", cp / 1000 if cp else None, unidad="kJ/(kg·K)"),
        Propiedad("Calor específico cv", cv / 1000 if cv else None, unidad="kJ/(kg·K)"),
        Propiedad("Relación cp/cv", cp / cv if cp and cv else None, unidad="-"),
        Propiedad("Exponente isoentrópico κ (gas real)", kappa if fase not in ("liquid", "twophase") else None, unidad="-"),
        Propiedad("Velocidad del sonido", c, "velocidad"),
        Propiedad("Entalpía específica", _cp("H", *a) / 1000 if _cp("H", *a) is not None else None, unidad="kJ/kg"),
        Propiedad("Entropía específica", _cp("S", *a) / 1000 if _cp("S", *a) is not None else None, unidad="kJ/(kg·K)"),
        Propiedad("Presión de vapor a T", Pv / 1000 if Pv else None, "presion"),
        Propiedad("Temperatura de saturación a P", Tsat, "temperatura"),
        Propiedad("Presión crítica", Pc / 1000 if Pc else None, "presion"),
        Propiedad("Temperatura crítica", Tc, "temperatura"),
    ]
    return [f for f in filas if f.valor is not None]


def saturacion(fluido: str, P_kPa: float | None = None, T_K: float | None = None) -> list[Propiedad]:
    """Líquido y vapor saturados a la presión o a la temperatura dada (tabla de vapor para el agua)."""
    n = P._cp_nombre(fluido)
    if (P_kPa is None) == (T_K is None):
        raise ValueError("Indique la presión o la temperatura de saturación, una sola.")
    base = ("P", P_kPa * 1000) if P_kPa is not None else ("T", T_K)
    Ts = _cp("T", *base, "Q", 0, n)
    Ps = _cp("P", *base, "Q", 0, n)
    if Ts is None or Ps is None:
        raise P.ErrorPropiedades(f"{fluido} no tiene saturación a esas condiciones (por encima del punto crítico "
                                 "o por debajo del punto triple).")
    v = lambda k, q: _cp(k, *base, "Q", q, n)
    hf, hg = v("H", 0), v("H", 1)
    return [
        Propiedad("Temperatura de saturación", Ts, "temperatura"),
        Propiedad("Presión de saturación", Ps / 1000, "presion"),
        Propiedad("Densidad del líquido", v("D", 0), "densidad"),
        Propiedad("Densidad del vapor", v("D", 1), "densidad"),
        Propiedad("Volumen específico del vapor", 1 / v("D", 1), unidad="m³/kg"),
        Propiedad("Entalpía del líquido hf", hf / 1000, unidad="kJ/kg"),
        Propiedad("Entalpía del vapor hg", hg / 1000, unidad="kJ/kg"),
        Propiedad("Calor latente hfg", (hg - hf) / 1000, unidad="kJ/kg"),
        Propiedad("Entropía del líquido sf", v("S", 0) / 1000, unidad="kJ/(kg·K)"),
        Propiedad("Entropía del vapor sg", v("S", 1) / 1000, unidad="kJ/(kg·K)"),
        Propiedad("Viscosidad del líquido", v("V", 0), "viscosidad_din"),
        Propiedad("Viscosidad del vapor", v("V", 1), "viscosidad_din"),
    ]


# ----------------------------------------------------------------------------- tuberías
RHO_ACERO = 7850.0     # kg/m³, para el peso por metro


@dataclass
class FilaTuberia:
    cedula: str
    OD_mm: float
    espesor_mm: float
    DI_mm: float
    area_mm2: float
    peso_kg_m: float


def tabla_tuberia(nps: float) -> list[FilaTuberia]:
    """Todas las cédulas que la norma define para el diámetro, con DI, área y peso del caño vacío."""
    od = T.OD_MM[nps]
    filas = []
    for c in T.cedulas_de(nps):
        e = T.espesor(nps, c)
        di = od - 2 * e
        filas.append(FilaTuberia(c, od, e, di, math.pi / 4 * di ** 2,
                                 math.pi * (od - e) * e * 1e-6 * RHO_ACERO))
    return filas


def velocidad(Q_m3h: float, DI_mm: float) -> float:
    """Velocidad media [m/s] del caudal volumétrico real en el diámetro interior dado."""
    return Q_m3h / 3600 / (math.pi / 4 * (DI_mm / 1000) ** 2)


def diametro_para_velocidad(Q_m3h: float, v_ms: float) -> float:
    """Diámetro interior [mm] que da la velocidad pedida."""
    return math.sqrt(Q_m3h / 3600 / v_ms * 4 / math.pi) * 1000


def nps_para_velocidad(Q_m3h: float, v_max_ms: float, cedula: str = "40") -> tuple[float, str, float] | None:
    """El menor diámetro nominal cuya velocidad no supera v_max: (NPS, cédula usada, velocidad)."""
    for nps in T.NPS:
        c = T.cedula_para(nps, cedula)
        if c is None:
            continue
        v = velocidad(Q_m3h, T.diametro_interior(nps, c))
        if v <= v_max_ms:
            return nps, c, v
    return None


# Velocidades orientativas en tubería (práctica habitual de diseño; no son límites de norma)
VELOCIDADES_TIPICAS = (
    ("Agua y líquidos poco viscosos, descarga de bomba", "1,5 – 3 m/s"),
    ("Succión de bombas", "0,6 – 1,5 m/s"),
    ("Líquidos viscosos", "0,5 – 1,5 m/s"),
    ("Gases y aire comprimido", "10 – 20 m/s"),
    ("Vapor saturado", "20 – 35 m/s"),
    ("Vapor sobrecalentado", "30 – 50 m/s"),
    ("Salida de válvula de control, líquido", "≤ 9 m/s (con cavitación ≤ 4,5 m/s)"),
    ("Salida de válvula de control, gas o vapor", "≤ 0,3 Mach (ruido)"),
)


# ----------------------------------------------------------------------------- presión-temperatura
def tabla_rating(grupo: str) -> tuple[list[float], dict[int, list[float]]]:
    """Temperaturas [°C] y presión máxima de trabajo [bar g] por clase del grupo de materiales."""
    ts, tabla = B.GRUPOS[grupo]
    return list(ts), {c: list(tabla[c]) for c in B.CLASES}


# ----------------------------------------------------------------------------- calculadoras
def ff(Pv_kPa: float, Pc_kPa: float) -> float:
    """Factor de relación de presión crítica del líquido FF = 0,96 − 0,28·√(Pv/Pc) (IEC 60534-2-1)."""
    return 0.96 - 0.28 * math.sqrt(Pv_kPa / Pc_kPa)


def dp_bloqueado(P1_kPa: float, Pv_kPa: float, Pc_kPa: float, FL: float) -> tuple[float, float]:
    """ΔP a partir de la cual el líquido queda bloqueado: ΔPmax = FL²·(P1 − FF·Pv). Devuelve (FF, ΔPmax kPa)."""
    f = ff(Pv_kPa, Pc_kPa)
    return f, FL ** 2 * (P1_kPa - f * Pv_kPa)


def dp_bloqueado_gas(P1_kPa: float, xT: float, gamma: float) -> float:
    """ΔP de flujo bloqueado de un gas: ΔPmax = Fγ·xT·P1, con Fγ = γ/1,40."""
    return gamma / 1.40 * xT * P1_kPa


def caudal_gas_real(Q_N_m3h: float, P_kPa: float, T_K: float, Z: float = 1.0) -> float:
    """Caudal real [m³/h] a P y T de un caudal normal [Nm³/h] (0 °C; 101,325 kPa)."""
    return Q_N_m3h * U.P_ATM_KPA / P_kPa * T_K / U.T_NORMAL_K * Z


def caudal_gas_normal(Q_m3h: float, P_kPa: float, T_K: float, Z: float = 1.0) -> float:
    return Q_m3h / caudal_gas_real(1.0, P_kPa, T_K, Z)


V_MOLAR_NORMAL = 22.414   # m³/kmol a 0 °C y 101,325 kPa


def masico_desde_normal(Q_N_m3h: float, M: float) -> float:
    """Caudal másico [kg/h] de un caudal normal [Nm³/h] con masa molar M [kg/kmol]."""
    return Q_N_m3h * M / V_MOLAR_NORMAL


def reynolds(v_ms: float, DI_mm: float, nu_m2s: float) -> float:
    return v_ms * DI_mm / 1000 / nu_m2s


def mach(v_ms: float, c_ms: float) -> float:
    return v_ms / c_ms


# ----------------------------------------------------------------------------- enlaces de referencia
# (nombre, url): lista inicial; el usuario la edita y se guarda en su configuración
ENLACES = (
    ("LME · precios de níquel, cobre y cobalto", "https://www.lme.com"),
    ("Outokumpu · recargos por aleación del inoxidable", "https://www.outokumpu.com"),
    ("Acerinox · extras de aleación", "https://www.acerinox.com"),
    ("NIST Chemistry WebBook · propiedades de fluidos", "https://webbook.nist.gov/chemistry/fluid/"),
    ("CoolProp · documentación de propiedades", "https://coolprop.org"),
    ("NACE / AMPP · corrosión y servicio agrio", "https://www.ampp.org"),
    ("ISA · normas de instrumentación", "https://www.isa.org"),
    ("IEC Webstore · IEC 60534", "https://webstore.iec.ch"),
    ("ASME · normas B16 y B36", "https://www.asme.org"),
)
