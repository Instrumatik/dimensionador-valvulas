"""Definición única del fluido (solapa 2-Cálculos Válvula) y lo que de ella deriva.

El fluido se define una sola vez: tipo (líquido, gas, vapor, vapor de agua), fluido de la
biblioteca de propiedades o «Definido por el usuario», calidad / variante y presencia de agua
libre. De ahí salen las propiedades corregidas por salinidad (cálculo de la válvula) y la
familia, fluido, fase y fase acuosa que usa la selección de materiales. La solapa 3-Materiales
solo agrega datos complementarios (agentes, sólidos, pH, industria...).
"""
from __future__ import annotations

from dataclasses import dataclass

USUARIO = "Definido por el usuario"
AGUA = "Agua / vapor de agua"

# Agua libre (fase acuosa) en el servicio
AGUA_LIBRE = ["Sí", "No", "Intermitente", "Desconocida"]
AUTO_AGUA = "Según el cálculo"          # vapor de agua: lo decide el estado calculado

# Variantes por fluido. Cada una: (familia para materiales, salinidad típica % p/p NaCl eq.,
# agua libre fija o sugerida, fija?)
_V = dict
VARIANTES_AGUA = {
    "Agua industrial / de enfriamiento": _V(familia="Agua", sal=0.0, agua="Sí", mat="Agua industrial"),
    "Agua potable": _V(familia="Agua", sal=0.0, agua="Sí", mat="Agua potable"),
    "Agua desmineralizada": _V(familia="Agua", sal=0.0, agua="Sí", mat="Agua desmineralizada"),
    "Agua de alimentación de caldera": _V(familia="Agua", sal=0.0, agua="Sí", mat="Agua de alimentación de caldera"),
    "Condensado": _V(familia="Agua", sal=0.0, agua="Sí", mat="Condensado"),
    "Agua de mar": _V(familia="Agua", sal=3.5, agua="Sí", mat="Agua de mar"),
    "Agua producida (yacimiento)": _V(familia="Agua", sal=10.0, agua="Sí", mat="Agua producida"),
    "Salmuera": _V(familia="Salmuera", sal=20.0, agua="Sí", mat="Salmuera"),
}
VARIANTES_USUARIO = {
    "liquido": {
        "Crudo": _V(familia="Hidrocarburo líquido", agua="Desconocida"),
        "Diésel / destilados": _V(familia="Hidrocarburo líquido", agua="No"),
        "Gasolina / naftas": _V(familia="Hidrocarburo líquido", agua="No"),
        "Hidrocarburo líquido (otro)": _V(familia="Hidrocarburo líquido", agua="Desconocida"),
        "Aceite térmico / lubricante": _V(familia="Hidrocarburo líquido", agua="No"),
        "Ácido": _V(familia="Ácido", agua="Sí"),
        "Alcalino (soda / potasa cáustica)": _V(familia="Alcalino", agua="Sí"),
        "Solvente": _V(familia="Solvente", agua="Desconocida"),
        "Slurry (líquido con sólidos)": _V(familia="Slurry", agua="Sí"),
        "Otro líquido": _V(familia="Otro", agua="Desconocida"),
    },
    "gas": {
        "Gas natural": _V(familia="Hidrocarburo gaseoso", agua="Desconocida"),
        "Gas combustible": _V(familia="Hidrocarburo gaseoso", agua="No"),
        "Gas ácido (con H₂S / CO₂)": _V(familia="Gas", agua="Desconocida"),
        "Gas de proceso (otro)": _V(familia="Gas", agua="Desconocida"),
    },
    "vapor": {
        "Vapor de hidrocarburo": _V(familia="Hidrocarburo gaseoso", agua="Desconocida"),
        "Vapor de proceso (otro)": _V(familia="Gas", agua="Desconocida"),
    },
}
# Familia de los fluidos de la biblioteca (el nombre ya define el fluido)
_HC = {"Metano", "Etano", "Propano", "n-Butano", "Isobutano", "n-Pentano", "n-Hexano", "n-Heptano",
       "Etileno", "Propileno", "Benceno", "Tolueno"}
_SOLV = {"Metanol", "Etanol"}
# Gases de la biblioteca que se suponen secos salvo indicación del usuario
SECOS = {"Aire", "Nitrógeno", "Oxígeno", "Hidrógeno", "Argón", "Helio", "Monóxido de carbono", "R134a",
         "Metano", "Etano", "Etileno", "Propileno"}
# Fluido puro de la biblioteca que es en sí un agente químico
AGENTE_DEL_FLUIDO = {"Oxígeno": "o2", "Dióxido de carbono": "co2", "Amoníaco": "nh3", "Hidrógeno": "h2",
                     "Sulfuro de hidrógeno": "h2s", "Cloro": "cl2"}


def grupo_tipo(tipo: str) -> str:
    return "liquido" if tipo == "liquido" else ("vapor" if tipo == "vapor" else "gas")


def variantes(tipo: str, fluido: str | None) -> list[str]:
    """Opciones de «Calidad / variante del fluido» para el tipo y fluido elegidos ([] = no se pide)."""
    if fluido == AGUA:
        return list(VARIANTES_AGUA) if tipo == "liquido" else []
    if fluido in (USUARIO, None, ""):
        return list(VARIANTES_USUARIO[grupo_tipo(tipo)])
    return []


def _datos_variante(tipo: str, fluido: str | None, variante: str) -> dict | None:
    if fluido == AGUA and tipo == "liquido":
        return VARIANTES_AGUA.get(variante)
    if fluido in (USUARIO, None, ""):
        return VARIANTES_USUARIO[grupo_tipo(tipo)].get(variante)
    return None


def variante_por_defecto(tipo: str, fluido: str | None) -> str:
    v = variantes(tipo, fluido)
    return v[0] if v else ""


def agua_libre_fija(tipo: str, fluido: str | None, variante: str) -> str | None:
    """Agua libre que el propio fluido impone (None = la elige el usuario)."""
    if fluido == AGUA:
        return "Sí" if tipo == "liquido" else AUTO_AGUA
    d = _datos_variante(tipo, fluido, variante)
    if d and d.get("familia") in ("Agua", "Salmuera", "Ácido", "Alcalino", "Slurry"):
        return "Sí"
    return None


def agua_libre_sugerida(tipo: str, fluido: str | None, variante: str) -> str:
    fija = agua_libre_fija(tipo, fluido, variante)
    if fija:
        return fija
    d = _datos_variante(tipo, fluido, variante)
    if d:
        return d["agua"]
    if fluido in SECOS or fluido in _SOLV or fluido in _HC:
        return "No"
    return "Desconocida"


def salinidad_pct(tipo: str, fluido: str | None, variante: str, cloruros_mgL: float | None = None) -> float:
    """Salinidad en % p/p de NaCl equivalente (0 = agua sin sales disueltas significativas)."""
    if fluido != AGUA or tipo != "liquido":
        return 0.0
    d = VARIANTES_AGUA.get(variante)
    base = d["sal"] if d else 0.0
    if cloruros_mgL and base > 0:
        # NaCl = 1,648 × Cl⁻; mg/L ≈ mg/kg × SG (se itera una vez con la SG de la salmuera)
        w = 1.648 * cloruros_mgL / 1e4
        w = 1.648 * cloruros_mgL / 1e4 / (1 + 0.0073 * w)
        return min(w, 26.0)
    return base


@dataclass
class CorreccionSalina:
    sal_pct: float
    f_rho: float
    f_mu: float
    f_Pv: float

    @property
    def texto(self) -> str:
        c = lambda x, d: f"{x:.{d}f}".replace(".", ",")
        return (f"salinidad {c(self.sal_pct, 1)} % p/p NaCl eq.: densidad ×{c(self.f_rho, 3)}, viscosidad "
                f"×{c(self.f_mu, 2)}, presión de vapor ×{c(self.f_Pv, 3)}")


def correccion_salina(sal_pct: float) -> CorreccionSalina | None:
    """Factores sobre las propiedades del agua pura para una solución de NaCl (orientativos, 0–26 %).

    Densidad: ρ/ρw ≈ 1 + 0,0073·w (w en % p/p; 3,5 % → 1,026 como el agua de mar).
    Viscosidad: μ/μw ≈ 1 + 0,021·w + 0,00037·w² (3,5 % → 1,08; 20 % → 1,57).
    Presión de vapor: ley de Raoult con disociación completa de NaCl (i = 2).
    """
    if not sal_pct or sal_pct <= 0:
        return None
    w = min(sal_pct, 26.0)
    n_sal = w / 58.44 * 2
    n_agua = (100 - w) / 18.015
    return CorreccionSalina(w, 1 + 0.0073 * w, 1 + 0.021 * w + 0.00037 * w * w, n_agua / (n_agua + n_sal))


@dataclass
class FluidoMateriales:
    familia: str
    fluido: str
    fase: str
    acuosa: str
    descripcion: str
    agente_propio: str | None = None


def para_materiales(tipo: str, fluido: str | None, variante: str, agua_libre: str,
                    salidas: list[dict] | None = None, flashing: bool = False) -> FluidoMateriales:
    """Familia, fluido, fase y fase acuosa que la selección de materiales deriva de la solapa 2."""
    salidas = salidas or []
    nombre = fluido or USUARIO
    d = _datos_variante(tipo, fluido, variante)
    if fluido == AGUA and tipo == "steam":
        sat = any(s.get("saturado") for s in salidas)
        mat = "Vapor saturado" if sat or not salidas else "Vapor sobrecalentado"
        familia, fase = "Vapor", "Vapor"
        acuosa = "Intermitente" if sat or not salidas else "No"
    elif fluido == AGUA and tipo == "liquido":
        d = d or VARIANTES_AGUA["Agua industrial / de enfriamiento"]
        familia, mat, fase, acuosa = d["familia"], d["mat"], "Líquido", "Sí"
    elif fluido == AGUA:
        familia, mat, fase, acuosa = "Vapor", "Vapor sobrecalentado", "Vapor", agua_libre
    elif d is not None:
        familia, mat = d["familia"], variante
        fase = {"liquido": "Líquido", "gas": "Gas", "vapor": "Vapor"}[grupo_tipo(tipo)]
        acuosa = agua_libre
    else:
        if nombre in _HC:
            familia = "Hidrocarburo líquido" if tipo == "liquido" else "Hidrocarburo gaseoso"
        elif nombre in _SOLV:
            familia = "Solvente"
        elif tipo == "liquido":
            familia = "Otro"
        else:
            familia = "Gas"
        mat = nombre
        fase = "Líquido" if tipo == "liquido" else ("Vapor" if tipo == "vapor" else "Gas")
        acuosa = agua_libre
    if flashing and fase == "Líquido":
        fase = "Gas-líquido"
    if familia == "Slurry":
        fase = "Líquido-sólido"
    desc = nombre if not variante or nombre == AGUA and tipo != "liquido" else f"{nombre} — {variante}"
    if nombre == USUARIO and variante:
        desc = f"{variante} (propiedades del usuario)"
    return FluidoMateriales(familia, mat, fase, acuosa, desc, AGENTE_DEL_FLUIDO.get(nombre))
