"""Propiedades termofísicas de fluidos mediante CoolProp (licencia MIT).

Agua y vapor de agua usan la formulación IAPWS-95 incluida en CoolProp.
Si CoolProp no está instalado, el programa sigue funcionando con
propiedades ingresadas manualmente por el usuario.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import CoolProp.CoolProp as CP
    DISPONIBLE = True
    ERROR_IMPORTACION = ""
except Exception as _e:  # pragma: no cover
    CP = None
    DISPONIBLE = False
    ERROR_IMPORTACION = f"{type(_e).__name__}: {_e}"

# Nombre en español -> nombre CoolProp
FLUIDOS = {
    "Agua / vapor de agua": "Water",
    "Aire": "Air",
    "Nitrógeno": "Nitrogen",
    "Oxígeno": "Oxygen",
    "Dióxido de carbono": "CarbonDioxide",
    "Hidrógeno": "Hydrogen",
    "Metano": "Methane",
    "Etano": "Ethane",
    "Propano": "Propane",
    "n-Butano": "n-Butane",
    "Isobutano": "IsoButane",
    "n-Pentano": "n-Pentane",
    "n-Hexano": "n-Hexane",
    "n-Heptano": "n-Heptane",
    "Amoníaco": "Ammonia",
    "Etileno": "Ethylene",
    "Propileno": "Propylene",
    "Benceno": "Benzene",
    "Tolueno": "Toluene",
    "Metanol": "Methanol",
    "Etanol": "Ethanol",
    "Sulfuro de hidrógeno": "HydrogenSulfide",
    "Argón": "Argon",
    "Helio": "Helium",
    "Cloro": "Chlorine",
    "Monóxido de carbono": "CarbonMonoxide",
    "R134a": "R134a",
}


class ErrorPropiedades(ValueError):
    pass


@dataclass
class PropiedadesLiquido:
    rho: float   # kg/m³
    Pv: float    # kPa abs
    Pc: float    # kPa abs
    nu: float    # m²/s
    mu: float    # Pa·s


@dataclass
class PropiedadesGas:
    rho: float
    M: float
    gamma: float
    Z: float
    mu: float
    fase: str


def _cp_nombre(fluido: str) -> str:
    if not DISPONIBLE:
        raise ErrorPropiedades("La biblioteca de propiedades no está disponible; ingrese las "
                               f"propiedades manualmente. ({ERROR_IMPORTACION})")
    return FLUIDOS.get(fluido, fluido)


def liquido(fluido: str, P1_kPa: float, T1_K: float) -> PropiedadesLiquido:
    n = _cp_nombre(fluido)
    try:
        Pv = CP.PropsSI("P", "T", T1_K, "Q", 0, n) / 1000
        if P1_kPa <= Pv:
            raise ErrorPropiedades(
                f"A {T1_K - 273.15:.1f} °C la presión de vapor de {fluido} es {Pv:.1f} kPa a, "
                f"mayor que P1 = {P1_kPa:.1f} kPa a: el fluido no es líquido a la entrada.")
        rho = CP.PropsSI("D", "T", T1_K, "P", P1_kPa * 1000, n)
        mu = CP.PropsSI("V", "T", T1_K, "P", P1_kPa * 1000, n)
        Pc = CP.PropsSI("Pcrit", n) / 1000
    except ErrorPropiedades:
        raise
    except Exception as e:
        raise ErrorPropiedades(f"No se pudieron obtener las propiedades de {fluido}: {e}") from None
    return PropiedadesLiquido(rho, Pv, Pc, mu / rho, mu)


def gas(fluido: str, P1_kPa: float, T1_K: float | None, saturado: bool = False) -> PropiedadesGas:
    """Propiedades a la entrada. Con ``saturado=True`` se toma vapor saturado seco a P1."""
    n = _cp_nombre(fluido)
    try:
        if saturado:
            args = ("P", P1_kPa * 1000, "Q", 1)
        else:
            args = ("T", T1_K, "P", P1_kPa * 1000)
            Tc = CP.PropsSI("Tcrit", n)
            if T1_K < Tc:
                Tsat = CP.PropsSI("T", "P", P1_kPa * 1000, "Q", 1, n)
                if T1_K < Tsat - 0.05:
                    raise ErrorPropiedades(
                        f"A {P1_kPa:.1f} kPa a la temperatura de saturación de {fluido} es "
                        f"{Tsat - 273.15:.1f} °C: a {T1_K - 273.15:.1f} °C el fluido es líquido.")
                if T1_K < Tsat + 0.05:
                    args = ("P", P1_kPa * 1000, "Q", 1)
        rho = CP.PropsSI("D", *args, n)
        M = CP.PropsSI("M", n) * 1000
        # Exponente isoentrópico κ = ρ·c²/P: es el γ que corresponde usar en gases reales y vapores
        # (en gas ideal κ = cp/cv) y hace que c = √(κ·P/ρ) sea la velocidad del sonido real.
        kappa = rho * CP.PropsSI("A", *args, n) ** 2 / (P1_kPa * 1000)
        Z = CP.PropsSI("Z", *args, n)
        mu = CP.PropsSI("V", *args, n)
        fase = CP.PhaseSI(*args, n)
    except ErrorPropiedades:
        raise
    except Exception as e:
        raise ErrorPropiedades(f"No se pudieron obtener las propiedades de {fluido}: {e}") from None
    return PropiedadesGas(rho, M, kappa, Z, mu, fase)


def temperatura_saturacion(fluido: str, P_kPa: float) -> float:
    return CP.PropsSI("T", "P", P_kPa * 1000, "Q", 0, _cp_nombre(fluido))


def calidad_isoentalpica(fluido: str, P1_kPa: float, T1_K: float, P2_kPa: float) -> float | None:
    """Fracción másica de vapor tras una expansión isoentálpica de P1,T1 a P2 (flashing)."""
    try:
        n = _cp_nombre(fluido)
        h1 = CP.PropsSI("H", "T", T1_K, "P", P1_kPa * 1000, n)
        q = CP.PropsSI("Q", "H", h1, "P", P2_kPa * 1000, n)
        if 0 <= q <= 1:
            return q
        return 0.0 if q < 0 else 1.0
    except Exception:
        return None


def densidad_bifasica(fluido: str, P2_kPa: float, calidad: float) -> float | None:
    try:
        n = _cp_nombre(fluido)
        return CP.PropsSI("D", "P", P2_kPa * 1000, "Q", calidad, n)
    except Exception:
        return None


def velocidad_sonido(fluido: str, P_kPa: float, T_K: float) -> float | None:
    try:
        return CP.PropsSI("A", "T", T_K, "P", P_kPa * 1000, _cp_nombre(fluido))
    except Exception:
        return None


@dataclass
class PropiedadesBifasico:
    T1: float
    rho_l: float
    rho_g: float
    Pv: float
    Pc: float
    gamma: float


def bifasico_saturado(fluido: str, P1_kPa: float) -> PropiedadesBifasico:
    """Mezcla saturada de un componente puro a P1 (T1 = temperatura de saturación)."""
    n = _cp_nombre(fluido)
    try:
        P = P1_kPa * 1000
        T = CP.PropsSI("T", "P", P, "Q", 0, n)
        rl = CP.PropsSI("D", "P", P, "Q", 0, n)
        rg = CP.PropsSI("D", "P", P, "Q", 1, n)
        g = CP.PropsSI("Cpmass", "P", P, "Q", 1, n) / CP.PropsSI("Cvmass", "P", P, "Q", 1, n)
        Pc = CP.PropsSI("Pcrit", n) / 1000
    except Exception as e:
        raise ErrorPropiedades(f"No se pudieron obtener las propiedades de saturación de {fluido}: {e}") from None
    return PropiedadesBifasico(T, rl, rg, P1_kPa, Pc, g)
