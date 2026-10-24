"""Fluidos compresibles en el flujo de la versión 2: gas, vapor y vapor de agua (steam).

* Dimensionamiento: IEC 60534-2-1:2011 / ANSI/ISA-75.01.01, cláusulas 6, 7 y 9
  (ecuación de caudal másico con factor de expansión Y, xT, Fγ, FP y xTP).
* Ruido aerodinámico: IEC 60534-8-3:2010, separado en ruido del trim y ruido de la
  salida de la válvula, y referido a 1 m y a la distancia Rn de la pared de la tubería.
* Vapor de agua: propiedades IAPWS-95 (CoolProp); la temperatura de salida se obtiene
  por expansión isoentálpica (estrangulamiento).

Todas las magnitudes en unidades base: kPa abs, K, kg/h, Nm³/h, kg/m³, Pa·s, mm, mm², m/s.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import propiedades, ruido
from .iec60534_2_1 import P_N, R_UNIV, T_N, Gas
from .modelos import _n, Alerta, ErrorDatos, Severidad

M_AIRE = 28.9647               # kg/kmol, para la gravedad específica de gases
AGUA = "Agua / vapor de agua"
TIPOS = {"liquido": "Líquido", "gas": "Gas", "vapor": "Vapor", "steam": "Vapor de agua (steam)"}
REF_SIZ = "IEC 60534-2-1:2011"

# Trims para ruido aerodinámico. Para una jaula de No orificios iguales IEC 60534-2-1
# (Anexo A) da Fd = dH/do = 1/√No; con ese Fd, IEC 60534-8-3 reduce el diámetro del
# chorro y desplaza el ruido a frecuencias altas, que la tubería atenúa más.
TRIMS_RUIDO = {
    "estandar": ("Estándar (pasaje único)", None),
    "multiorificio_1": ("Jaula multiorificio, nivel 1 (≈ 50 orificios)", 1 / math.sqrt(50)),
    "multiorificio_2": ("Jaula multiorificio, nivel 2 (≈ 200 orificios)", 1 / math.sqrt(200)),
    "multiorificio_3": ("Jaula multiorificio, nivel 3 (≈ 800 orificios)", 1 / math.sqrt(800)),
}
NIVEL_CORTO = {"estandar": "No requerido", "multiorificio_1": "Nivel 1", "multiorificio_2": "Nivel 2",
               "multiorificio_3": "Nivel 3"}
MACH_SALIDA_VALVULA = 0.3      # límite habitual de diseño en la salida de la válvula (ruido)
MACH_TUBERIA = 0.3


@dataclass
class CasoGas:
    """Caso de operación con gas, vapor o vapor de agua."""
    nombre: str
    W: float | None            # kg/h
    QN: float | None           # Nm³/h (0 °C; 101,325 kPa)
    P1: float                  # kPa abs
    P2: float
    T1: float | None           # K; None solo en steam = vapor saturado seco
    M: float | None = None     # kg/kmol (gas y vapor)
    mu: float | None = None    # Pa·s
    gamma: float | None = None
    Z1: float | None = None    # gas
    rho1: float | None = None  # vapor (dato); calculada en gas y steam
    xT: float = 0.72
    FL: float = 0.9
    Fd: float = 0.46
    T2: float | None = None    # K; None = isoentálpica (fluido conocido) o T1
    Z2: float | None = None    # gas; None = de la biblioteca o Z1
    rho2: float | None = None  # vapor; None = de la biblioteca o ρ1·P2/P1·T1/T2
    criterio: bool = True


@dataclass
class RuidoAerodinamico:
    trim: str = "estandar"             # clave de TRIMS_RUIDO
    Rn: float = 1.0                    # m, distancia desde la pared de la tubería
    area_salida: float | None = None   # mm²; None = área del diámetro nominal de la válvula


@dataclass
class Estado:
    """Propiedades resueltas de un caso (dato del usuario, biblioteca o norma)."""
    M: float
    mu: float
    gamma: float
    Z1: float
    rho1: float
    T1: float
    T2: float
    Z2: float
    rho2: float
    saturado: bool = False
    sobrecalentamiento2: float | None = None   # K sobre la saturación a P2 (steam)
    origen: str = ""


def _err(caso, codigo, titulo, texto):
    return Alerta(codigo, Severidad.ERROR, titulo, f"Caso {caso}: {texto}")


def resolver_estado(c: CasoGas, tipo: str, fluido: str | None, composicion: dict | None = None) -> Estado:
    """Completa las propiedades de un caso. Los datos del usuario tienen prioridad."""
    errores = []
    if c.P2 >= c.P1:
        raise ErrorDatos([_err(c.nombre, "dato_dp", "Presiones inválidas",
                               "la presión de salida debe ser menor que la de entrada.")])
    if tipo == "steam":
        return _estado_steam(c)
    biblio = fluido if fluido and fluido in propiedades.FLUIDOS else None
    p1 = None
    if biblio and c.T1 is not None and None in (c.M, c.mu, c.gamma, c.Z1 if tipo == "gas" else c.rho1):
        try:
            p1 = propiedades.gas(biblio, c.P1, c.T1, composicion=composicion)
        except propiedades.ErrorPropiedades as e:
            raise ErrorDatos([_err(c.nombre, "dato_propiedades", "Propiedades del fluido", str(e))]) from None
    M = c.M or (p1.M if p1 else None)
    mu = c.mu or (p1.mu if p1 else None)
    gamma = c.gamma or (p1.gamma if p1 else None)
    if c.T1 is None:
        errores.append(_err(c.nombre, "dato_t1", "Falta la temperatura", "ingrese la temperatura de entrada."))
    for v, nombre in ((M, "la masa molar o gravedad específica"), (mu, "la viscosidad"),
                      (gamma, "la relación de calores específicos γ")):
        if v is None:
            errores.append(_err(c.nombre, "dato_faltante", "Dato faltante", f"falta {nombre}."))
    if tipo == "gas":
        Z1 = c.Z1 or (p1.Z if p1 else None)
        if Z1 is None:
            errores.append(_err(c.nombre, "dato_faltante", "Dato faltante", "falta el factor de compresibilidad Z1."))
        rho1 = None
    else:
        rho1 = c.rho1 or (p1.rho if p1 else None)
        if rho1 is None:
            errores.append(_err(c.nombre, "dato_faltante", "Dato faltante", "falta la densidad de entrada ρ1."))
        Z1 = None
    if errores:
        raise ErrorDatos(errores)
    T1 = c.T1
    if tipo == "gas":
        rho1 = c.P1 * M / (Z1 * R_UNIV * T1)
    else:
        Z1 = c.P1 * M / (rho1 * R_UNIV * T1)
    # Condición de salida (ruido y velocidades)
    T2, Z2, rho2, origen = c.T2, c.Z2, c.rho2, "dato del usuario"
    if biblio and (T2 is None or (Z2 is None and tipo == "gas") or (rho2 is None and tipo == "vapor")):
        try:
            CP = propiedades.CP
            n = propiedades._cp_nombre(biblio, composicion)
            h1 = CP.PropsSI("H", "T", T1, "P", c.P1 * 1000, n)
            T2c = CP.PropsSI("T", "H", h1, "P", c.P2 * 1000, n) if T2 is None else T2
            T2 = T2c
            Z2 = Z2 or CP.PropsSI("Z", "T", T2, "P", c.P2 * 1000, n)
            rho2 = rho2 or CP.PropsSI("D", "T", T2, "P", c.P2 * 1000, n)
            origen = f"biblioteca de propiedades ({biblio}), expansión isoentálpica"
        except Exception:
            pass
    if T2 is None:
        T2, origen = T1, "igual a T1 (gas ideal)"
    if tipo == "gas":
        Z2 = Z2 or Z1
        rho2 = c.P2 * M / (Z2 * R_UNIV * T2)
    else:
        rho2 = rho2 or rho1 * c.P2 / c.P1 * T1 / T2
        Z2 = c.P2 * M / (rho2 * R_UNIV * T2)
    return Estado(M, mu, gamma, Z1, rho1, T1, T2, Z2, rho2, origen=origen)


def _estado_steam(c: CasoGas) -> Estado:
    if not propiedades.DISPONIBLE:
        raise ErrorDatos([_err(c.nombre, "dato_propiedades", "Propiedades del vapor de agua",
                               "la biblioteca IAPWS no está disponible.")])
    CP = propiedades.CP
    P1, P2 = c.P1 * 1000, c.P2 * 1000
    try:
        Pc = CP.PropsSI("Pcrit", "Water")
        if P1 >= Pc:
            raise ErrorDatos([_err(c.nombre, "dato_p1", "Presión supercrítica",
                                   "la presión de entrada supera la crítica del agua (220,6 bar a).")])
        Tsat1 = CP.PropsSI("T", "P", P1, "Q", 1, "Water")
        saturado = c.T1 is None or abs(c.T1 - Tsat1) < 0.05
        if not saturado and c.T1 < Tsat1:
            raise ErrorDatos([_err(c.nombre, "dato_t1", "Temperatura bajo la saturación",
                                   f"a esa presión la saturación es {Tsat1 - 273.15:.1f} °C y T1 es "
                                   f"{c.T1 - 273.15:.1f} °C: el fluido sería agua líquida. Use el tipo de "
                                   "fluido Líquido o deje T1 en blanco para vapor saturado seco.")])
        args = ("P", P1, "Q", 1) if saturado else ("T", c.T1, "P", P1)
        T1 = Tsat1 if saturado else c.T1
        rho1 = CP.PropsSI("D", *args, "Water")
        mu = CP.PropsSI("V", *args, "Water")
        # Exponente isoentrópico κ = ρ·c²/P (cerca de la saturación cp/cv lo sobrestima mucho)
        gamma = rho1 * CP.PropsSI("A", *args, "Water") ** 2 / P1
        h1 = CP.PropsSI("H", *args, "Water")
        M = CP.PropsSI("M", "Water") * 1000
        Tsat2 = CP.PropsSI("T", "P", P2, "Q", 1, "Water")
        if c.T2 is not None:
            T2 = c.T2
            rho2 = CP.PropsSI("D", "T", T2, "P", P2, "Water")
            origen = "T2 dato del usuario"
        else:
            q2 = CP.PropsSI("Q", "H", h1, "P", P2, "Water")
            if 0 <= q2 < 1:
                T2 = Tsat2
                rho2 = CP.PropsSI("D", "P", P2, "Q", q2, "Water")
            else:
                T2 = CP.PropsSI("T", "H", h1, "P", P2, "Water")
                rho2 = CP.PropsSI("D", "H", h1, "P", P2, "Water")
            origen = "IAPWS-95, expansión isoentálpica"
    except ErrorDatos:
        raise
    except Exception as e:
        raise ErrorDatos([_err(c.nombre, "dato_propiedades", "Propiedades del vapor de agua", str(e))]) from None
    Z1 = c.P1 * M / (rho1 * R_UNIV * T1)
    Z2 = c.P2 * M / (rho2 * R_UNIV * T2)
    return Estado(M, mu, gamma, Z1, rho1, T1, T2, Z2, rho2, saturado, T2 - Tsat2, origen)


def estado_gas(c: CasoGas, e: Estado) -> Gas:
    return Gas(P1=c.P1, P2=c.P2, T1=e.T1, M=e.M, gamma=e.gamma, Z=e.Z1, mu=e.mu, W=c.W, QN=c.QN,
               rho1=e.rho1)


def densidad_normal(M: float) -> float:
    return P_N * M / (R_UNIV * T_N)


def sonido(gamma: float, P_kPa: float, rho: float) -> float:
    """Velocidad del sonido c = √(γ·P/ρ) = √(γ·Z·R·T/M) [m/s]."""
    return math.sqrt(gamma * P_kPa * 1000 / rho)


def ruido_caso(W_kgh, c: CasoGas, e: Estado, Kv, FL_eff, Fd, d_salida_mm, D2_mm, tp2_mm, Rn_m) -> dict:
    """Ruido IEC 60534-8-3 con el Fd dado; devuelve componentes y nivel a Rn."""
    r = ruido.ruido_gas(W_kgh / 3600, c.P1, c.P2, e.T1, e.rho1, e.gamma, e.M, Kv, d_salida_mm / 1000,
                        D2_mm / 1000, tp2_mm / 1000, Fd, FL_eff, T2=e.T2, rho2=e.rho2,
                        c2=sonido(e.gamma, c.P2, e.rho2))
    r["LpAe_Rn"] = r["LpAe1m"] + ruido.correccion_distancia(D2_mm / 1000, tp2_mm / 1000, Rn_m)
    return r


def alertas_velocidad(Ma_valv: float, Ma1: float, Ma2: float, tipo: str) -> list[Alerta]:
    al = []
    if Ma_valv > MACH_SALIDA_VALVULA:
        sev = Severidad.CRITICA if Ma_valv > 0.5 else Severidad.ADVERTENCIA
        inten = min(100.0, (Ma_valv - MACH_SALIDA_VALVULA) / 0.7 * 100)
        al.append(Alerta("mach_salida", sev, "Mach alto en la salida de la válvula",
                         f"Número de Mach en la salida de la válvula: {_n(Ma_valv, 3)}. Por encima de "
                         f"{_n(MACH_SALIDA_VALVULA, 1)} el ruido de salida crece rápidamente y por encima de 0,5 "
                         "hay riesgo de vibración y erosión.", inten,
                         "leve" if inten < 33 else "moderada" if inten < 66 else "severa",
                         ["Seleccionar una válvula de mayor diámetro o con salida expandida.",
                          "Aumentar el diámetro de la tubería aguas abajo.",
                          "Repartir la caída de presión en etapas o con un difusor."],
                         "IEC 60534-8-3 (validez y práctica de diseño)"))
    for Ma, donde in ((Ma1, "aguas arriba"), (Ma2, "aguas abajo")):
        if Ma > MACH_TUBERIA:
            inten = min(100.0, (Ma - MACH_TUBERIA) / 0.4 * 100)
            al.append(Alerta("mach_tuberia", Severidad.ADVERTENCIA, f"Mach alto en la tubería {donde}",
                             f"Número de Mach en la tubería {donde}: {_n(Ma, 3)} (práctica habitual ≤ "
                             f"{_n(MACH_TUBERIA, 1)}{' y ≤ 0,2 en vapor de agua' if tipo == 'steam' else ''}).",
                             inten, "leve" if inten < 33 else "moderada" if inten < 66 else "severa",
                             ["Aumentar el diámetro de la tubería."]))
    return al


def tipo_calculo(tipo: str, bloqueado: bool, regimen: str, e: Estado) -> str:
    """Texto corto: fluido, régimen crítico o subcrítico y, si no es turbulento, el régimen de Reynolds."""
    base = {"gas": "Gas", "vapor": "Vapor", "steam": "Steam"}[tipo]
    if tipo == "steam":
        base += " sat." if e.saturado else " sobrecal."
    texto = f"{base}, {'crítico' if bloqueado else 'subcrítico'}"
    return texto if regimen == "turbulento" else f"{texto}, {regimen}"
