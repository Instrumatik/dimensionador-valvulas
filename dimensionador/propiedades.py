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
    "Gas natural": "",            # mezcla: la arma _cp_nombre con la composición molar (COMPONENTES_GN)
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


# --- Gas natural: mezcla de la ecuación de estado GERG/HEOS de CoolProp con composición editable
GAS_NATURAL = "Gas natural"
COMPONENTES_GN = {
    "Metano": "Methane", "Etano": "Ethane", "Propano": "Propane", "n-Butano": "n-Butane",
    "Isobutano": "IsoButane", "n-Pentano": "n-Pentane", "Isopentano": "Isopentane", "n-Hexano": "n-Hexane",
    "Nitrógeno": "Nitrogen", "Dióxido de carbono": "CarbonDioxide", "Sulfuro de hidrógeno": "HydrogenSulfide",
    "Hidrógeno": "Hydrogen", "Helio": "Helium", "Oxígeno": "Oxygen", "Agua": "Water",
}
# Composición típica de un gas natural seco de gasoducto (% molar). No corresponde a ningún yacimiento.
GN_TIPICO = {"Metano": 90.0, "Etano": 5.0, "Propano": 2.0, "n-Butano": 0.5, "Isobutano": 0.5,
             "Nitrógeno": 1.0, "Dióxido de carbono": 1.0}


def texto_composicion(comp: dict) -> str:
    """«Metano 90; Etano 5; …» con coma decimal."""
    return "; ".join(f"{k} {f'{v:g}'.replace('.', ',')}" for k, v in comp.items() if v)


def leer_composicion(texto: str) -> dict:
    """Lee «Metano 90; Etano 5; …» (% molar). Vacío = composición típica. Normaliza a 100 %."""
    t = (texto or "").strip()
    if not t:
        return dict(GN_TIPICO)
    comp, nombres = {}, {k.lower(): k for k in COMPONENTES_GN}
    for parte in t.replace("\n", ";").split(";"):
        parte = parte.strip()
        if not parte:
            continue
        nombre, _, valor = parte.rpartition(" ")
        clave = nombres.get(nombre.strip().rstrip(":=").strip().lower())
        try:
            v = float(valor.replace("%", "").replace(",", "."))
        except ValueError:
            v = None
        if clave is None or v is None or v < 0:
            raise ErrorPropiedades(
                f"Composición del gas natural: no se entiende «{parte}». Escriba cada componente con su % "
                f"molar separado por punto y coma, por ejemplo «Metano 90; Etano 5». Componentes posibles: "
                f"{', '.join(COMPONENTES_GN)}.")
        comp[clave] = comp.get(clave, 0.0) + v
    total = sum(comp.values())
    if total <= 0:
        raise ErrorPropiedades("Composición del gas natural: la suma de los % molares es cero.")
    if abs(total - 100) > 5:
        raise ErrorPropiedades(f"Composición del gas natural: los % molares suman {total:.2f} %; deben sumar "
                               "100 % (se acepta hasta ±5 % y se normaliza).")
    return {k: v * 100 / total for k, v in comp.items() if v > 0}


def masa_molar_mezcla(comp: dict) -> float:
    return sum(CP.PropsSI("M", COMPONENTES_GN[k]) * 1000 * v / 100 for k, v in comp.items())


def _mezcla(comp: dict) -> str:
    total = sum(comp.values())
    return "HEOS::" + "&".join(f"{COMPONENTES_GN[k]}[{v / total:.6f}]" for k, v in comp.items() if v > 0)


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


def _cp_nombre(fluido: str, composicion: dict | None = None) -> str:
    if not DISPONIBLE:
        raise ErrorPropiedades("La biblioteca de propiedades no está disponible; ingrese las "
                               f"propiedades manualmente. ({ERROR_IMPORTACION})")
    if fluido == GAS_NATURAL:
        return _mezcla(composicion or GN_TIPICO)
    return FLUIDOS.get(fluido, fluido)


def liquido(fluido: str, P1_kPa: float, T1_K: float) -> PropiedadesLiquido:
    if fluido == GAS_NATURAL:
        raise ErrorPropiedades("El gas natural de la lista se calcula como gas: elija el tipo de fluido Gas.")
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


def gas(fluido: str, P1_kPa: float, T1_K: float | None, saturado: bool = False,
        composicion: dict | None = None) -> PropiedadesGas:
    """Propiedades a la entrada. Con ``saturado=True`` se toma vapor saturado seco a P1."""
    n = _cp_nombre(fluido, composicion)
    try:
        if fluido == GAS_NATURAL:
            args = ("T", T1_K, "P", P1_kPa * 1000)
            rho = CP.PropsSI("D", *args, n)
            kappa = rho * CP.PropsSI("A", *args, n) ** 2 / (P1_kPa * 1000)
            return PropiedadesGas(rho, CP.PropsSI("M", *args, n) * 1000, kappa, CP.PropsSI("Z", *args, n),
                                  CP.PropsSI("V", *args, n), "gas")
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
