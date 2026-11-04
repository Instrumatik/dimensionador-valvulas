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
    # v0.16.0: componentes de gases de refinería, gas de síntesis y gas ácido
    "Monóxido de carbono": "CarbonMonoxide", "Etileno": "Ethylene", "Propileno": "Propylene",
    "Amoníaco": "Ammonia", "Argón": "Argon",
}
COMPONENTES = COMPONENTES_GN
# Mezclas de la biblioteca (nombre -> composición típica, % molar). Las registra fluidos_proceso.
MEZCLAS: dict[str, dict] = {}


def _reglas_de_mezcla():
    """Pares de componentes sin coeficientes de interacción publicados en CoolProp (olefinas, amoníaco):
    se completan con la regla de Lorentz-Berthelot, la que recomienda CoolProp cuando falta el par."""
    if not DISPONIBLE:
        return
    import itertools
    cas = {}
    for n in COMPONENTES_GN.values():
        try:
            cas[n] = CP.get_fluid_param_string(n, "CAS")
        except Exception:
            pass

    def tiene(a, b):
        for x, y in ((a, b), (b, a)):
            try:
                CP.get_mixture_binary_pair_data(cas[x], cas[y], "betaT")
                return True
            except Exception:
                pass
        return False

    for a, b in itertools.combinations(cas, 2):
        if not tiene(a, b):
            try:
                CP.apply_simple_mixing_rule(cas[a], cas[b], "Lorentz-Berthelot")
            except Exception:
                pass


_reglas_de_mezcla()
# Composición típica de un gas natural seco de gasoducto (% molar). No corresponde a ningún yacimiento.
GN_TIPICO = {"Metano": 90.0, "Etano": 5.0, "Propano": 2.0, "n-Butano": 0.5, "Isobutano": 0.5,
             "Nitrógeno": 1.0, "Dióxido de carbono": 1.0}


def texto_composicion(comp: dict) -> str:
    """«Metano 90; Etano 5; …» con coma decimal."""
    return "; ".join(f"{k} {f'{v:g}'.replace('.', ',')}" for k, v in comp.items() if v)


def es_mezcla(fluido: str | None) -> bool:
    """Gas natural o mezcla de la biblioteca con composición editable."""
    return fluido == GAS_NATURAL or fluido in MEZCLAS


def composicion_tipica(fluido: str = GAS_NATURAL) -> dict:
    return dict(MEZCLAS.get(fluido) or GN_TIPICO)


def leer_composicion(texto: str, fluido: str = GAS_NATURAL) -> dict:
    """Lee «Metano 90; Etano 5; …» (% molar). Vacío = composición típica. Normaliza a 100 %."""
    t = (texto or "").strip()
    nombre = "del gas natural" if fluido == GAS_NATURAL else f"de {fluido}"
    if not t:
        return composicion_tipica(fluido)
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
                f"Composición {nombre}: no se entiende «{parte}». Escriba cada componente con su % "
                f"molar separado por punto y coma, por ejemplo «Metano 90; Etano 5». Componentes posibles: "
                f"{', '.join(COMPONENTES_GN)}.")
        comp[clave] = comp.get(clave, 0.0) + v
    total = sum(comp.values())
    if total <= 0:
        raise ErrorPropiedades(f"Composición {nombre}: la suma de los % molares es cero.")
    if abs(total - 100) > 5:
        raise ErrorPropiedades(f"Composición {nombre}: los % molares suman {total:.2f} %; deben sumar "
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
    if es_mezcla(fluido):
        return _mezcla(composicion or composicion_tipica(fluido))
    return FLUIDOS.get(fluido, fluido)


def _viscosidad(args: tuple, n: str) -> float:
    """Viscosidad de CoolProp; en mezclas con un componente sin modelo de viscosidad (propileno) se usa la
    regla de Herning y Zipperer con la viscosidad de cada componente a su presión parcial (gas a baja y
    media presión; el propileno se toma como propano, de viscosidad casi igual)."""
    try:
        return CP.PropsSI("V", *args, n)
    except Exception:
        if "&" not in n:
            raise
    T = args[1] if args[0] == "T" else CP.PropsSI("T", *args, n)
    P = args[3] if args[2] == "P" else CP.PropsSI("P", *args, n)
    num = den = 0.0
    for parte in n.split("::", 1)[1].split("&"):
        comp, y = parte.rstrip("]").split("[")
        y = float(y)
        c = "Propane" if comp == "Propylene" else comp
        try:
            mu = CP.PropsSI("V", "T", T, "P", max(y * P, 100.0), c)
        except Exception:
            mu = CP.PropsSI("V", "T", T, "P", 101325.0, "Nitrogen")
        M = CP.PropsSI("M", c) * 1000
        num += y * mu * M ** 0.5
        den += y * M ** 0.5
    return num / den


def _pc_kay(n: str) -> float:
    """Presión pseudocrítica de una mezcla (regla de Kay, Σ yi·Pci) [Pa]: la que usa FF = 0,96 − 0,28·√(Pv/Pc)."""
    total = 0.0
    for parte in n.split("::", 1)[1].split("&"):
        comp, y = parte.rstrip("]").split("[")
        total += float(y) * CP.PropsSI("Pcrit", comp)
    return total


def liquido(fluido: str, P1_kPa: float, T1_K: float, composicion: dict | None = None) -> PropiedadesLiquido:
    if fluido == GAS_NATURAL:
        raise ErrorPropiedades("El gas natural de la lista se calcula como gas: elija el tipo de fluido Gas.")
    n = _cp_nombre(fluido, composicion)
    mezcla = "&" in n
    try:
        try:
            Pv = CP.PropsSI("P", "T", T1_K, "Q", 0, n) / 1000     # en mezclas: presión de burbuja
        except Exception:
            if not mezcla:
                raise
            raise ErrorPropiedades(f"A {T1_K - 273.15:.1f} °C {fluido} no tiene punto de burbuja: con esta "
                                   "composición es un gas. Elija el tipo de fluido Gas.") from None
        if P1_kPa <= Pv:
            raise ErrorPropiedades(
                f"A {T1_K - 273.15:.1f} °C la presión de vapor de {fluido} es {Pv:.1f} kPa a, "
                f"mayor que P1 = {P1_kPa:.1f} kPa a: el fluido no es líquido a la entrada.")
        rho = CP.PropsSI("D", "T", T1_K, "P", P1_kPa * 1000, n)
        mu = _viscosidad(("T", T1_K, "P", P1_kPa * 1000), n)
        Pc = (_pc_kay(n) if mezcla else CP.PropsSI("Pcrit", n)) / 1000
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
        if fluido in MEZCLAS:
            return _gas_mezcla(fluido, n, P1_kPa, T1_K)
        if es_mezcla(fluido):
            args = ("T", T1_K, "P", P1_kPa * 1000)
            rho = CP.PropsSI("D", *args, n)
            kappa = rho * CP.PropsSI("A", *args, n) ** 2 / (P1_kPa * 1000)
            return PropiedadesGas(rho, CP.PropsSI("M", *args, n) * 1000, kappa, CP.PropsSI("Z", *args, n),
                                  _viscosidad(args, n), "gas")
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
        mu = _viscosidad(args, n)
        fase = CP.PhaseSI(*args, n)
    except ErrorPropiedades:
        raise
    except Exception as e:
        raise ErrorPropiedades(f"No se pudieron obtener las propiedades de {fluido}: {e}") from None
    return PropiedadesGas(rho, M, kappa, Z, mu, fase)


def _gas_mezcla(fluido: str, n: str, P1_kPa: float, T1_K: float) -> PropiedadesGas:
    """Gas de proceso con la raíz de vapor impuesta: en mezclas con agua o hidrocarburos pesados el cálculo de
    fases de CoolProp puede elegir la raíz líquida aun cuando el gas está apenas debajo de su punto de rocío;
    para dimensionar se usa el gas (el condensado se separa aguas arriba)."""
    comps, ys = [], []
    for parte in n.split("::", 1)[1].split("&"):
        c, y = parte.rstrip("]").split("[")
        comps.append(c)
        ys.append(float(y))
    try:
        AS = CP.AbstractState("HEOS", "&".join(comps))
        AS.set_mole_fractions(ys)
        AS.specify_phase(CP.iphase_gas)
        AS.update(CP.PT_INPUTS, P1_kPa * 1000, T1_K)
        rho, Z, c = AS.rhomass(), AS.compressibility_factor(), AS.speed_sound()
        M = AS.molar_mass() * 1000
    except Exception:
        raise ErrorPropiedades(
            f"A {P1_kPa:.1f} kPa a y {T1_K - 273.15:.1f} °C {fluido} con esta composición no es un gas: elija el "
            "tipo de fluido Líquido o revise la presión, la temperatura o la composición.") from None
    kappa = rho * c ** 2 / (P1_kPa * 1000) if c > 0 else 0
    if Z < 0.3 or not (c > 0) or (Z < 0.6 and kappa > 2.5):
        raise ErrorPropiedades(
            f"A {P1_kPa:.1f} kPa a y {T1_K - 273.15:.1f} °C {fluido} con esta composición está en fase líquida "
            f"(Z = {Z:.3f}): elija el tipo de fluido Líquido.")
    try:
        mu = AS.viscosity()
    except Exception:
        mu = _viscosidad(("T", T1_K, "P", P1_kPa * 1000), n)
    return PropiedadesGas(rho, M, kappa, Z, mu, "gas")


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


# Fluidos de proceso (refinería, mejoradores, servicios y químicos): registra sus mezclas en MEZCLAS y FLUIDOS
from . import fluidos_proceso as _fluidos_proceso  # noqa: E402,F401
