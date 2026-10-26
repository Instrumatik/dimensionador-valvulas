"""Agentes químicos, conversión de unidades y compatibilidad química de materiales.

Cada agente tiene una unidad base en la que se expresan sus reglas:

* ``mgL``  mg/L de la especie disuelta en el agua (iones y sales);
* ``pct``  % en masa (p/p) en la fase acuosa (ácidos, bases, oxidantes líquidos);
* ``kPa``  presión parcial en la fase gaseosa (gases ácidos o reactivos).

Las reglas dan, para cada clase de comportamiento químico de los materiales
(``Material.quimica``), el nivel de compatibilidad en la misma escala que las
tablas de resistencia química de la industria:

  A  excelente (sin efecto, < 0,05 mm/año)
  B  bueno (efecto menor; apto con sobreespesor o vigilancia)
  C  regular (no recomendado para servicio continuo)
  D  no usar

Se evalúan rangos de concentración y temperatura: la primera fila que
contiene el punto de servicio da el nivel; fuera de todas las filas el nivel
es D. Son reglas de preselección conservadoras, construidas a partir de
guías públicas (Nickel Institute, fichas de Haynes / Special Metals, NACE
SP0403, API 571, manuales de fabricantes de válvulas). Además se consulta la
tabla cualitativa de resistencia química A–D a temperatura ambiente
(``TABLA_AD``); cuando ambas fuentes difieren se toma la más conservadora.

Ninguna regla reemplaza las curvas de isocorrosión del fabricante para la
concentración, temperatura, aireación e impurezas reales.
"""
from __future__ import annotations

from dataclasses import dataclass, field

INF = 1e12
NIVELES = "ABCD"
NIVEL_TXT = {"A": "A — excelente", "B": "B — bueno", "C": "C — regular (no recomendado)",
             "D": "D — no usar", "?": "sin datos"}

FAMILIAS = ["Gases ácidos / reactivos", "Halogenuros / sales", "Ácidos inorgánicos", "Ácidos orgánicos",
            "Álcalis / bases", "Azufre / sulfuros", "Oxidantes", "Otros"]
UNIDADES = ["mg/L", "ppm masa", "ppmv", "% p/p", "% molar", "mol/L", "bar(a) parcial", "kPa parcial"]
FASES = ["Acuosa", "Orgánica líquida", "Gas / vapor", "Sólida", "Desconocida"]
UNIDADES_GAS = ("ppmv", "bar(a) parcial", "kPa parcial")


@dataclass(frozen=True)
class Agente:
    clave: str
    nombre: str
    formula: str
    familia: str
    base: str                      # mgL, pct o kPa
    MW: float                      # g/mol
    unidad_sugerida: str
    alto: float                    # concentración conservadora (unidad base) si no se informa
    mecanismos: tuple[str, ...] = ()
    henry: float | None = None     # mg/L disueltos por kPa de presión parcial (25 °C)
    alias: tuple[str, float] | None = None   # se evalúa como otro agente × factor
    acuoso: bool = True            # necesita agua libre para atacar


AGENTES: dict[str, Agente] = {a.clave: a for a in [
    # Gases ácidos / reactivos
    Agente("h2s", "Sulfuro de hidrógeno", "H₂S", FAMILIAS[0], "kPa", 34.08, "ppmv", 100,
           ("SSC", "HIC", "SOHIC", "corrosion_sulfuro"), henry=34),
    Agente("co2", "Dióxido de carbono", "CO₂", FAMILIAS[0], "kPa", 44.01, "% molar", 500,
           ("corrosion_co2",), henry=15),
    Agente("so2", "Dióxido de azufre", "SO₂", FAMILIAS[0], "kPa", 64.07, "ppmv", 50,
           ("acido_inorganico", "punto_rocio_acido"), henry=770),
    Agente("so3", "Trióxido de azufre", "SO₃", FAMILIAS[0], "pct", 80.06, "ppmv", 98,
           ("acido_inorganico", "punto_rocio_acido")),
    Agente("cl2", "Cloro", "Cl₂", FAMILIAS[0], "kPa", 70.9, "ppmv", 50, ("oxidante", "picaduras"), henry=65),
    Agente("o2", "Oxígeno", "O₂", FAMILIAS[0], "kPa", 32.0, "mg/L", 21, ("oxidante", "ignicion_o2"),
           henry=0.42),
    Agente("nh3", "Amoníaco", "NH₃", FAMILIAS[0], "pct", 17.03, "% p/p", 30, ("scc_amoniaco",),
           henry=10000),
    Agente("h2", "Hidrógeno", "H₂", FAMILIAS[0], "kPa", 2.016, "% molar", 1000, ("HTHA", "fragilizacion_h2"),
           henry=0.0156, acuoso=False),
    # Halogenuros / sales
    Agente("cloruros", "Cloruros", "Cl⁻", FAMILIAS[1], "mgL", 35.45, "mg/L", 20000,
           ("picaduras", "crevice", "scc_cloruros")),
    Agente("bromuros", "Bromuros", "Br⁻", FAMILIAS[1], "mgL", 79.9, "mg/L", 1000,
           ("picaduras", "crevice"), alias=("cloruros", 1.5)),
    Agente("fluoruros", "Fluoruros", "F⁻", FAMILIAS[1], "mgL", 19.0, "mg/L", 1000, ("ataque_fluoruro",)),
    Agente("nacl", "Cloruro de sodio", "NaCl", FAMILIAS[1], "mgL", 58.44, "mg/L", 35000,
           ("picaduras", "scc_cloruros"), alias=("cloruros", 0.607)),
    Agente("cacl2", "Cloruro de calcio", "CaCl₂", FAMILIAS[1], "mgL", 110.98, "% p/p", 300000,
           ("picaduras", "scc_cloruros"), alias=("cloruros", 0.639)),
    Agente("mgcl2", "Cloruro de magnesio", "MgCl₂", FAMILIAS[1], "mgL", 95.21, "% p/p", 300000,
           ("picaduras", "scc_cloruros"), alias=("cloruros", 0.90)),
    Agente("fecl3", "Cloruro férrico", "FeCl₃", FAMILIAS[1], "mgL", 162.2, "% p/p", 100000,
           ("picaduras", "oxidante")),
    # Ácidos inorgánicos
    Agente("hcl", "Ácido clorhídrico", "HCl", FAMILIAS[2], "pct", 36.46, "% p/p", 20, ("acido_inorganico",
           "picaduras"), henry=None),
    Agente("h2so4", "Ácido sulfúrico", "H₂SO₄", FAMILIAS[2], "pct", 98.08, "% p/p", 70, ("acido_inorganico",)),
    Agente("hno3", "Ácido nítrico", "HNO₃", FAMILIAS[2], "pct", 63.01, "% p/p", 65, ("acido_inorganico",
           "oxidante", "intergranular")),
    Agente("h3po4", "Ácido fosfórico", "H₃PO₄", FAMILIAS[2], "pct", 98.0, "% p/p", 85, ("acido_inorganico",)),
    Agente("hf", "Ácido fluorhídrico", "HF", FAMILIAS[2], "pct", 20.01, "% p/p", 50, ("ataque_fluoruro",)),
    Agente("h2co3", "Ácido carbónico", "H₂CO₃", FAMILIAS[2], "pct", 62.03, "mg/L", 0.2, ("corrosion_co2",)),
    Agente("hclo4", "Ácido perclórico", "HClO₄", FAMILIAS[2], "pct", 100.46, "% p/p", 70,
           ("acido_inorganico", "oxidante")),
    # Ácidos orgánicos
    Agente("acetico", "Ácido acético", "CH₃COOH", FAMILIAS[3], "pct", 60.05, "% p/p", 100, ("acido_organico",)),
    Agente("formico", "Ácido fórmico", "HCOOH", FAMILIAS[3], "pct", 46.03, "% p/p", 85, ("acido_organico",)),
    Agente("oxalico", "Ácido oxálico", "C₂H₂O₄", FAMILIAS[3], "pct", 90.03, "% p/p", 10, ("acido_organico",)),
    Agente("citrico", "Ácido cítrico", "C₆H₈O₇", FAMILIAS[3], "pct", 192.1, "% p/p", 50, ("acido_organico",)),
    Agente("lactico", "Ácido láctico", "C₃H₆O₃", FAMILIAS[3], "pct", 90.08, "% p/p", 80, ("acido_organico",)),
    # Álcalis / bases
    Agente("naoh", "Hidróxido de sodio (soda cáustica)", "NaOH", FAMILIAS[4], "pct", 40.0, "% p/p", 50,
           ("scc_caustica",)),
    Agente("koh", "Hidróxido de potasio", "KOH", FAMILIAS[4], "pct", 56.11, "% p/p", 50, ("scc_caustica",),
           alias=("naoh", 1.0)),
    Agente("nh4oh", "Hidróxido de amonio (amoníaco acuoso)", "NH₄OH", FAMILIAS[4], "pct", 35.05, "% p/p", 30,
           ("scc_amoniaco",), alias=("nh3", 1.0)),
    # Azufre / sulfuros
    Agente("azufre", "Azufre elemental", "S₈", FAMILIAS[5], "mgL", 256.5, "mg/L", 100,
           ("azufre_elemental", "picaduras")),
    Agente("sulfuros", "Sulfuros (HS⁻ / S²⁻)", "HS⁻ / S²⁻", FAMILIAS[5], "mgL", 33.07, "mg/L", 1000,
           ("corrosion_sulfuro", "SSC")),
    Agente("polisulfuros", "Polisulfuros", "Sₓ²⁻", FAMILIAS[5], "mgL", 96.0, "mg/L", 1000, ("corrosion_sulfuro",)),
    Agente("tiosulfatos", "Tiosulfatos", "S₂O₃²⁻", FAMILIAS[5], "mgL", 112.1, "mg/L", 1000, ("picaduras",)),
    # Oxidantes
    Agente("hipoclorito", "Hipoclorito (cloro activo)", "OCl⁻", FAMILIAS[6], "mgL", 51.45, "mg/L", 1000,
           ("oxidante", "picaduras")),
    Agente("h2o2", "Peróxido de hidrógeno", "H₂O₂", FAMILIAS[6], "pct", 34.01, "% p/p", 50, ("oxidante",)),
    Agente("nitratos", "Nitratos", "NO₃⁻", FAMILIAS[6], "mgL", 62.0, "mg/L", 50000, ("scc_nitratos",)),
    # Otros
    Agente("aminas", "Aminas (MEA, DEA, MDEA)", "R-NH₂", FAMILIAS[7], "pct", 61.08, "% p/p", 50, ("scc_aminas",)),
    Agente("solidos", "Sólidos abrasivos", "—", FAMILIAS[7], "mgL", 100.0, "mg/L", 5000, ("erosion",),
           acuoso=False),
    Agente("otro", "Otro (especificar)", "—", FAMILIAS[7], "mgL", 100.0, "mg/L", 1, ("sin_datos",)),
]}


def por_familia(familia: str) -> list[Agente]:
    return [a for a in AGENTES.values() if a.familia == familia]


# ---------------------------------------------------------------------------
# Clases químicas de materiales
# ---------------------------------------------------------------------------
METALES = ["cs", "crmo", "crmo9", "ss304", "ss316", "ss317", "superaus", "duplex", "sduplex", "a20", "in825",
           "monel", "ni600", "ni_c", "ni625", "ni_b", "ti", "mart", "mart440", "ph", "cocr", "enc", "wc", "wc_ni",
           "ceram", "bronce"]
POLIMEROS = ["ptfe", "vidrio", "peek", "fkm", "epdm", "nbr", "grafito"]   # grafito flexible: empaquetaduras


def r(*filas) -> list[tuple[float, float, float, str]]:
    """Filas (c_max, T_max, nivel) o (c_min, c_max, T_max, nivel)."""
    out = []
    for f in filas:
        out.append(f if len(f) == 4 else (0.0, f[0], f[1], f[2]))
    return out


def _todos(clases, filas):
    return {c: filas for c in clases}


A_ = r((INF, 2000, "A"))
B_ = r((INF, 2000, "B"))
C_ = r((INF, 2000, "C"))
D_ = r()
ACERO = ["cs", "crmo", "crmo9"]
MART = ["mart", "mart440", "ph"]
AUST = ["ss304", "ss316", "ss317"]
NIQ = ["a20", "in825", "monel", "ni600", "ni_c", "ni_b"]

# Reglas con agua presente (o fase del agente acuosa)
REGLAS: dict[str, dict[str, list]] = {
    "cloruros": {  # agua neutra aireada; los límites bajan con pH ácido u oxidantes. Austeníticos: por encima de
        # 100 °C, aun con ≤ 50 mg/L, B (los cloruros se concentran por evaporación: Cl-SCC)
        **_todos(ACERO, r((200, 200, "B"), (1000, 100, "B"), (INF, 100, "C"))),
        "ss304": r((50, 100, "A"), (200, 60, "A"), (50, 200, "B"), (200, 100, "B"), (1000, 40, "B"), (1000, 60, "C"),
                   (200, 150, "C"), (3000, 25, "C")),
        "ss316": r((50, 100, "A"), (1000, 40, "A"), (50, 200, "B"), (200, 100, "B"), (1000, 60, "B"), (3000, 30, "B"),
                   (1000, 120, "C"), (25000, 25, "C")),
        "ss317": r((50, 100, "A"), (2000, 40, "A"), (50, 200, "B"), (500, 100, "B"), (2000, 60, "B"), (5000, 30, "B"),
                   (2000, 120, "C"), (25000, 30, "C")),
        "duplex": r((1000, 150, "A"), (3600, 80, "A"), (5000, 100, "B"), (10000, 40, "B"), (25000, 60, "C")),
        **_todos(["sduplex", "superaus"], r((5000, 150, "A"), (25000, 30, "A"), (25000, 60, "B"), (60000, 40, "B"),
                                            (INF, 100, "C"))),
        "a20": r((1000, 100, "A"), (2000, 60, "A"), (5000, 40, "B"), (25000, 25, "C")),
        "in825": r((1000, 150, "A"), (5000, 60, "A"), (25000, 40, "B"), (INF, 60, "C")),
        "ni_c": r((INF, 150, "A"), (INF, 250, "B"), (INF, 2000, "C")), "ni_b": r((INF, 100, "A"), (INF, 200, "B")),
        "ni625": r((INF, 120, "A"), (INF, 200, "B"), (INF, 2000, "C")),
        "monel": r((INF, 60, "A"), (INF, 150, "B")), "ni600": r((1000, 150, "A"), (5000, 100, "B"), (INF, 100, "C")),
        "ti": r((INF, 80, "A"), (INF, 130, "B"), (INF, 2000, "C")),
        "mart": r((50, 200, "A"), (200, 60, "B"), (1000, 40, "C")),
        "mart440": r((50, 150, "A"), (100, 60, "B"), (1000, 30, "C")),
        "ph": r((200, 100, "A"), (500, 60, "A"), (3000, 40, "B"), (1000, 100, "C"), (25000, 30, "C")),
        "cocr": r((25000, 60, "A"), (INF, 100, "B")), "enc": r((200, 100, "A"), (1000, 60, "B"), (25000, 40, "C")),
        "wc": r((200, 100, "A"), (1000, 60, "B"), (INF, 60, "C")), "wc_ni": r((INF, 100, "A"), (INF, 200, "B")),
        "ceram": A_, "bronce": r((INF, 60, "B"), (INF, 100, "C")),
        **_todos(POLIMEROS, A_),
    },
    "fluoruros": {
        **_todos(ACERO, r((1000, 60, "B"), (INF, 60, "C"))), **_todos(AUST + ["mart", "ph"], r((100, 60, "A"),
                                                                                             (1000, 60, "B"), (INF, 60, "C"))),
        "mart440": r((100, 40, "B"), (1000, 40, "C")),
        **_todos(["duplex", "sduplex", "superaus", "a20", "in825"], r((1000, 60, "A"), (INF, 60, "B"))),
        **_todos(["ni_c", "ni_b", "monel", "ni600"], r((INF, 100, "A"), (INF, 2000, "B"))),
        "ti": r((10, 60, "B"), (100, 40, "C")), "cocr": r((1000, 60, "B"), (INF, 60, "C")),
        "enc": r((1000, 60, "B")), "wc": r((1000, 60, "B")), "wc_ni": r((INF, 60, "B")),
        "ceram": r((100, 60, "B"), (INF, 60, "C")), "bronce": r((1000, 40, "B")), "vidrio": r((100, 40, "B")),
        **_todos(["ptfe", "peek", "fkm"], A_), "epdm": r((INF, 100, "B")), "nbr": r((1000, 60, "B")),
    },
    "fecl3": {
        **_todos(ACERO + MART + ["ni_b", "monel", "wc", "bronce", "enc"], D_), "ni600": r((1000, 30, "C")),
        **_todos(AUST, r((100, 40, "B"), (1000, 25, "C"))), "duplex": r((1000, 30, "B"), (10000, 25, "C")),
        **_todos(["sduplex", "superaus"], r((5000, 40, "B"), (INF, 25, "C"))),
        **_todos(["a20", "in825"], r((1000, 40, "B"), (5000, 25, "C"))),
        "ni_c": r((60000, 60, "A"), (INF, 90, "B")), "ti": r((INF, 100, "A"), (INF, 150, "B")),
        "cocr": r((10000, 30, "C")), "wc_ni": r((10000, 30, "C")), "ceram": A_,
        **_todos(["ptfe", "vidrio", "peek", "fkm", "epdm"], A_), "nbr": r((10000, 30, "C")),
    },
    "hipoclorito": {
        **_todos(ACERO, r((10, 40, "C"))), "ss304": r((5, 40, "B"), (50, 25, "C")),
        **_todos(["ss316", "ss317"], r((10, 40, "B"), (200, 25, "C"))), "duplex": r((10, 40, "A"), (200, 30, "B"),
                                                                                    (2000, 25, "C")),
        **_todos(["sduplex", "superaus"], r((20, 40, "A"), (1000, 30, "B"), (INF, 25, "C"))),
        **_todos(["a20", "in825"], r((10, 40, "B"), (200, 25, "C"))), "ni_c": r((INF, 40, "A"), (INF, 80, "B")),
        **_todos(["ni_b", "monel", "bronce", "wc", "enc"], r((5, 30, "C"))), "ni600": r((50, 30, "C")),
        "ti": r((INF, 80, "A"), (INF, 120, "B")), **_todos(MART, r((5, 30, "C"))), "cocr": r((50, 30, "C")),
        "wc_ni": r((50, 30, "C")), "ceram": A_, **_todos(["ptfe", "vidrio", "peek", "fkm"], A_),
        "epdm": r((INF, 60, "B")), "nbr": r((50, 30, "C")),
    },
    "cl2": {  # cloro húmedo
        **_todos(METALES, D_), "ti": r((INF, 100, "A"), (INF, 150, "B")), "ni_c": r((INF, 40, "B"), (INF, 80, "C")),
        "ceram": A_, "ptfe": A_, "vidrio": A_, "fkm": r((INF, 80, "B")), "peek": r((INF, 40, "C")),
        "epdm": r((INF, 40, "C")), "nbr": D_,
    },
    "hcl": {
        **_todos(ACERO + MART + ["enc", "wc", "bronce"], r((0.05, 30, "C"))),
        **_todos(AUST, r((0.1, 30, "C"))), "duplex": r((0.5, 30, "C")),
        **_todos(["sduplex", "superaus"], r((1, 30, "B"), (2, 40, "C"))),
        "a20": r((1, 40, "B"), (5, 30, "C")), "in825": r((2, 40, "B"), (5, 40, "C")),
        "ni_c": r((2, 60, "A"), (5, 80, "B"), (20, 40, "B"), (20, 70, "C"), (37, 30, "C")),
        "ni_b": r((INF, 100, "A"), (INF, 150, "B")), "monel": r((1, 40, "B"), (10, 25, "C")),
        "ni600": r((1, 30, "C")), "ti": r((3, 30, "B"), (5, 30, "C")), "cocr": r((1, 30, "C")),
        "wc_ni": r((1, 30, "C")), "ceram": r((37, 100, "A")), "ptfe": r((INF, 200, "A")), "vidrio": r((37, 100, "A")),
        "peek": r((37, 60, "A"), (37, 100, "B")), "fkm": r((37, 70, "A"), (37, 120, "B")),
        "epdm": r((20, 40, "B"), (37, 40, "C")), "nbr": r((10, 30, "C")),
    },
    "h2so4": {
        **_todos(ACERO, r((93, 99, 30, "C"))), "ss304": r((0, 0.5, 30, "C"), (93, 99, 40, "B")),
        "ss316": r((0, 1, 40, "B"), (0, 5, 25, "C"), (93, 99, 40, "B"), (98, 101, 60, "C")),
        "ss317": r((0, 2, 40, "B"), (0, 10, 25, "C"), (93, 99, 50, "B")),
        "duplex": r((0, 5, 40, "B"), (0, 10, 25, "C"), (93, 99, 40, "B")),
        **_todos(["sduplex", "superaus"], r((0, 10, 50, "A"), (0, 40, 40, "B"), (0, 70, 30, "C"),
                                            (90, 99, 40, "B"))),
        "a20": r((0, 101, 50, "A"), (0, 101, 80, "B"), (0, 101, 100, "C")),
        "in825": r((0, 40, 60, "A"), (0, 101, 60, "B"), (0, 101, 90, "C")),
        "ni_c": r((0, 101, 66, "A"), (0, 101, 100, "B"), (0, 101, 120, "C")),
        "ni_b": r((0, 60, 100, "A"), (0, 101, 100, "B")), "monel": r((0, 20, 40, "B"), (0, 60, 30, "C")),
        "ni600": r((0, 10, 40, "C")), "ti": r((0, 1, 40, "B"), (0, 5, 30, "C")),
        **_todos(MART, r((93, 99, 30, "C"))), "cocr": r((0, 10, 40, "B"), (0, 50, 30, "C"), (93, 99, 40, "B")),
        "enc": r((0, 10, 30, "C")), "wc": D_, "wc_ni": r((0, 10, 40, "C")), "ceram": r((0, 101, 150, "A")),
        "bronce": r((0, 40, 40, "C")), "ptfe": r((INF, 200, "A")), "vidrio": r((INF, 150, "A")),
        "peek": r((0, 50, 60, "A"), (0, 80, 40, "B")), "fkm": r((0, 90, 60, "A"), (0, 98, 40, "B"), (0, 101, 40, "C")),
        "epdm": r((0, 50, 40, "B")), "nbr": r((0, 10, 30, "C")),
    },
    "hno3": {
        **_todos(ACERO + ["ni_b", "monel", "enc", "wc", "wc_ni", "bronce"], D_),
        "ss304": r((0, 65, 60, "A"), (0, 65, 100, "B"), (65, 95, 40, "B")),
        **_todos(["ss316", "ss317"], r((0, 50, 60, "A"), (0, 65, 90, "B"), (65, 95, 30, "C"))),
        **_todos(["duplex", "sduplex", "superaus"], r((0, 65, 60, "A"), (0, 65, 90, "B"), (65, 95, 30, "C"))),
        **_todos(["a20", "in825"], r((0, 65, 80, "A"), (0, 65, 100, "B"), (65, 95, 40, "B"))),
        "ni_c": r((0, 20, 60, "B"), (0, 65, 60, "C")), "ni600": r((0, 20, 40, "B"), (0, 65, 40, "C")),
        "ti": r((0, 70, 100, "A"), (0, 90, 60, "B")), "mart": r((0, 20, 40, "B"), (0, 50, 30, "C")),
        "mart440": r((0, 10, 30, "C")), "ph": r((0, 20, 40, "B"), (0, 50, 30, "C")),
        "cocr": r((0, 10, 30, "B"), (0, 30, 30, "C")), "ceram": r((0, 101, 100, "A")),
        "ptfe": r((INF, 200, "A")), "vidrio": r((INF, 150, "A")), "peek": r((0, 30, 40, "B")),
        "fkm": r((0, 50, 40, "A"), (0, 70, 25, "B")), "epdm": r((0, 10, 30, "C")), "nbr": D_,
    },
    "h3po4": {
        **_todos(ACERO, D_), "ss304": r((0, 20, 60, "B"), (0, 85, 40, "C")),
        **_todos(["ss316", "ss317"], r((0, 40, 60, "A"), (0, 85, 60, "B"), (0, 85, 95, "C"))),
        "duplex": r((0, 50, 60, "A"), (0, 85, 80, "B")), **_todos(["sduplex", "superaus"], r((0, 85, 80, "A"),
                                                                                         (0, 85, 110, "B"))),
        **_todos(["a20", "in825"], r((0, 85, 90, "A"), (0, 85, 120, "B"))),
        "ni_c": r((0, 85, 100, "A"), (0, 85, 150, "B")), "ni_b": r((0, 85, 150, "A")),
        "monel": r((0, 50, 40, "B"), (0, 85, 40, "C")), "ni600": r((0, 50, 40, "C")),
        "ti": r((0, 10, 30, "B"), (0, 30, 25, "C")), **_todos(MART, r((0, 10, 30, "C"))),
        "cocr": r((0, 85, 60, "B")), "enc": r((0, 20, 30, "C")), "wc": D_, "wc_ni": r((0, 20, 40, "C")),
        "ceram": r((0, 85, 150, "A")), "bronce": r((0, 20, 30, "C")), "ptfe": A_, "vidrio": r((0, 85, 100, "B")),
        "peek": r((0, 85, 80, "A")), "fkm": r((0, 85, 80, "A")), "epdm": r((0, 85, 60, "B")), "nbr": r((0, 20, 30, "C")),
    },
    "hf": {
        **_todos(ACERO, r((70, 101, 65, "B"))), **_todos(AUST + ["duplex", "sduplex", "superaus"], r((0, 1, 25, "C"))),
        "a20": r((0, 10, 40, "C")), "in825": r((0, 40, 40, "C")),
        "ni_c": r((0, 50, 60, "B"), (0, 101, 40, "C")), "ni_b": r((0, 50, 80, "B")),
        "monel": r((0, 101, 100, "A"), (0, 101, 150, "B")), "ni600": r((0, 101, 60, "B")),
        **_todos(["ti"] + MART + ["cocr", "enc", "wc", "wc_ni", "ceram", "vidrio", "nbr"], D_),
        "bronce": r((0, 50, 30, "C")), "ptfe": A_, "peek": r((0, 40, 25, "C")),
        "fkm": r((0, 50, 40, "B"), (0, 101, 40, "C")), "epdm": r((0, 50, 30, "C")),
    },
    "h2co3": {
        **_todos(ACERO, r((INF, 60, "C"))), **_todos(MART + AUST + ["duplex", "sduplex", "superaus"] + NIQ +
                                                    ["ti", "cocr", "enc", "wc_ni", "ceram"], A_),
        "wc": B_, "bronce": B_, **_todos(POLIMEROS, A_),
    },
    "hclo4": {
        **_todos(METALES, D_), **_todos(AUST, r((0, 10, 40, "B"), (0, 70, 25, "C"))),
        "ti": r((0, 70, 60, "A")), "ni_c": r((0, 70, 40, "B")), "ceram": A_,
        "ptfe": A_, "vidrio": A_, "fkm": r((0, 70, 40, "B")), "peek": r((0, 30, 25, "C")),
    },
    "acetico": {
        **_todos(ACERO, r((99, 101, 40, "C"))), "ss304": r((0, 101, 60, "A"), (0, 101, 100, "B"), (0, 101, 120, "C")),
        **_todos(["ss316", "ss317"], r((0, 101, 80, "A"), (0, 101, 118, "B"))),
        **_todos(["duplex", "sduplex", "superaus", "a20", "in825", "ni_c", "ni_b"], r((0, 101, 118, "A"))),
        "monel": r((0, 101, 40, "B"), (0, 101, 100, "C")), "ni600": r((0, 101, 60, "B")),
        "ti": r((0, 99, 118, "A"), (0, 101, 118, "B")), "mart": r((0, 20, 30, "B"), (0, 101, 25, "C")),
        "mart440": r((0, 101, 30, "C")), "ph": r((0, 101, 40, "B")), "cocr": r((0, 101, 100, "A")),
        "enc": r((0, 101, 40, "B")), "wc": r((0, 20, 30, "C")), "wc_ni": r((0, 101, 40, "B")),
        "ceram": A_, "bronce": r((0, 101, 30, "C")), "ptfe": A_, "vidrio": A_, "peek": A_,
        "fkm": r((0, 20, 40, "B"), (0, 101, 25, "C")), "epdm": r((0, 101, 60, "A")), "nbr": r((0, 20, 30, "C")),
    },
    "formico": {
        **_todos(ACERO, D_), "ss304": r((0, 10, 40, "B"), (0, 101, 30, "C")),
        **_todos(["ss316", "ss317"], r((0, 101, 40, "A"), (0, 101, 80, "B"), (0, 101, 100, "C"))),
        "duplex": r((0, 101, 60, "A"), (0, 101, 100, "B")),
        **_todos(["sduplex", "superaus", "a20", "in825", "ni_c", "ni_b"], r((0, 101, 100, "A"))),
        "monel": r((0, 101, 40, "B"), (0, 101, 80, "C")), "ni600": r((0, 101, 40, "B")),
        "ti": r((0, 50, 60, "A"), (0, 101, 40, "B"), (0, 101, 80, "C")), **_todos(["mart", "mart440"], r((0, 10, 25, "C"))),
        "ph": r((0, 10, 30, "C")), "cocr": r((0, 101, 60, "B")), "enc": r((0, 101, 30, "C")), "wc": D_,
        "wc_ni": r((0, 50, 30, "C")), "ceram": A_, "bronce": r((0, 50, 30, "C")), "ptfe": A_, "vidrio": A_,
        "peek": A_, "fkm": r((0, 10, 25, "C")), "epdm": r((0, 101, 60, "A")), "nbr": D_,
    },
    "oxalico": {
        **_todos(ACERO + ["wc"], D_), "ss304": r((0, 10, 40, "B"), (0, 101, 30, "C")),
        **_todos(["ss316", "ss317"], r((0, 10, 60, "B"), (0, 101, 40, "C"))),
        "duplex": r((0, 10, 60, "A"), (0, 10, 90, "B")),
        **_todos(["sduplex", "superaus", "a20", "in825", "ni_c", "ni_b"], r((0, 101, 100, "A"))),
        "monel": r((0, 10, 60, "B")), "ni600": r((0, 10, 40, "B")), "ti": r((0, 1, 25, "C")),
        **_todos(["mart", "mart440"], r((0, 5, 25, "C"))), "ph": r((0, 10, 30, "C")), "cocr": r((0, 10, 60, "B")),
        "enc": r((0, 10, 30, "C")), "wc_ni": r((0, 10, 30, "C")), "ceram": A_, "bronce": r((0, 10, 30, "C")),
        **_todos(["ptfe", "vidrio", "peek", "fkm", "epdm"], A_), "nbr": B_,
    },
    "citrico": {
        **_todos(ACERO, D_), "ss304": r((0, 50, 60, "A"), (0, 101, 100, "B")),
        **_todos(["ss316", "ss317", "duplex", "sduplex", "superaus", "a20", "in825", "ni_c", "ni_b", "monel",
                  "ni600", "ti", "cocr", "ceram"], r((0, 101, 100, "A"), (0, 101, 150, "B"))),
        **_todos(MART, r((0, 50, 40, "B"), (0, 101, 30, "C"))), "enc": r((0, 101, 60, "B")), "wc": r((0, 20, 30, "C")),
        "wc_ni": r((0, 101, 60, "B")), "bronce": r((0, 50, 40, "B")), **_todos(POLIMEROS, A_),
    },
    "lactico": {
        **_todos(ACERO, D_), "ss304": r((0, 50, 40, "A"), (0, 101, 60, "B"), (0, 101, 100, "C")),
        **_todos(["ss316", "ss317"], r((0, 101, 60, "A"), (0, 101, 100, "B"))),
        **_todos(["duplex", "sduplex", "superaus", "a20", "in825", "ni_c", "ni_b", "ti", "cocr", "ceram"],
                 r((0, 101, 100, "A"))),
        "monel": r((0, 101, 60, "B")), "ni600": r((0, 101, 60, "B")), **_todos(["mart", "mart440"], r((0, 20, 30, "C"))),
        "ph": r((0, 101, 40, "B")), "enc": r((0, 101, 40, "B")), "wc": r((0, 10, 30, "C")), "wc_ni": r((0, 101, 40, "B")),
        "bronce": r((0, 20, 30, "C")), **_todos(["ptfe", "vidrio", "peek", "fkm", "epdm"], A_), "nbr": B_,
    },
    "naoh": {
        **_todos(ACERO, r((0, 10, 80, "A"), (0, 50, 50, "B"), (0, 50, 90, "C"), (0, 101, 40, "C"))),
        **_todos(AUST, r((0, 50, 95, "A"), (0, 50, 120, "B"), (0, 80, 120, "C"))),
        **_todos(["duplex", "sduplex", "superaus"], r((0, 50, 100, "A"), (0, 50, 140, "B"), (0, 80, 120, "C"))),
        **_todos(["a20", "in825"], r((0, 70, 150, "A"), (0, 101, 200, "B"))),
        "ni_c": r((0, 50, 100, "A"), (0, 80, 150, "B")), "ni_b": r((0, 50, 100, "B")),
        "monel": r((0, 75, 150, "A"), (0, 101, 300, "B")), "ni600": r((0, 101, 300, "A")),
        "ti": r((0, 10, 80, "A"), (0, 50, 80, "B"), (0, 50, 120, "C")), "mart": r((0, 30, 60, "B"), (0, 50, 60, "C")),
        "mart440": r((0, 20, 40, "B"), (0, 50, 40, "C")), "ph": r((0, 30, 80, "B"), (0, 50, 80, "C")),
        "cocr": r((0, 50, 80, "B")), "enc": r((0, 50, 90, "A"), (0, 75, 120, "B")), "wc": r((0, 20, 60, "B"), (0, 50, 60, "C")),
        "wc_ni": r((0, 50, 80, "B")), "ceram": r((0, 10, 60, "B"), (0, 50, 40, "C")), "bronce": r((0, 10, 30, "C")),
        "ptfe": A_, "vidrio": r((0, 10, 40, "B"), (0, 50, 25, "C")), "peek": r((0, 50, 100, "A")),
        "fkm": r((0, 20, 40, "C")), "epdm": r((0, 50, 100, "A"), (0, 75, 120, "B")), "nbr": r((0, 20, 60, "B"), (0, 50, 40, "C")),
    },
    "nh3": {
        **_todos(ACERO + AUST + ["duplex", "sduplex", "superaus", "a20", "in825", "ni_c", "ni_b", "ni600", "ti"] +
                 MART + ["ceram", "enc", "wc_ni"], A_),
        "monel": r((0, 3, 40, "B"), (0, 101, 40, "C")), "cocr": B_, "wc": B_, "bronce": D_,
        "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": D_, "epdm": A_, "nbr": r((0, 101, 50, "B")),
    },
    "o2": {  # oxígeno disuelto en agua (kPa equivalente)
        **_todos(ACERO, r((0.05, 300, "A"), (0.5, 200, "B"), (25, 120, "B"), (INF, 300, "C"))),
        **_todos([c for c in METALES if c not in ACERO], A_),
        "ni_b": r((0.05, 300, "A"), (INF, 300, "C")), "bronce": r((25, 60, "A"), (INF, 100, "B")),
        **_todos(POLIMEROS, A_),
    },
    "so2": {  # húmedo: ácido sulfuroso
        **_todos(ACERO + ["mart", "wc", "bronce"], D_), "ss304": r((INF, 40, "C")),
        **_todos(["ss316", "ss317"], r((INF, 60, "B"), (INF, 100, "C"))), "duplex": r((INF, 60, "A"), (INF, 100, "B")),
        **_todos(["sduplex", "superaus", "a20", "in825", "ni_c", "ti", "ceram"], r((INF, 100, "A"), (INF, 200, "B"))),
        **_todos(["ni_b", "monel", "ni600", "ph", "enc", "wc_ni"], r((INF, 60, "C"))), "mart440": D_,
        "cocr": r((INF, 80, "B")), "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": A_, "epdm": B_, "nbr": D_,
    },
    "so3": {"_alias": [("h2so4", 98)]},
    "azufre": {  # azufre elemental con agua (y normalmente H₂S)
        **_todos(ACERO, r((INF, 120, "C"))), **_todos(AUST + ["duplex", "sduplex"] + MART, D_),
        **_todos(["superaus", "a20", "in825", "monel", "ni600", "ni_b"], r((INF, 120, "C"))),
        "ni_c": r((INF, 200, "A")), "ti": r((INF, 120, "B")), "cocr": r((INF, 150, "B")), "enc": D_, "wc": D_,
        "wc_ni": r((INF, 120, "C")), "ceram": A_, "bronce": D_, **_todos(["ptfe", "vidrio", "peek", "fkm", "epdm"], A_),
        "nbr": C_,
    },
    "sulfuros": {
        **_todos(ACERO, r((100, 80, "B"), (INF, 80, "C"))), **_todos(AUST + ["duplex", "sduplex", "superaus", "a20",
                                                                            "in825", "ni_c", "ti", "cocr", "ceram"], A_),
        **_todos(["ni_b", "monel", "ni600"], B_), **_todos(MART + ["enc", "wc_ni"], B_), "wc": C_, "bronce": D_,
        **_todos(["ptfe", "vidrio", "peek", "fkm", "epdm"], A_), "nbr": C_,
    },
    "polisulfuros": {
        **_todos(ACERO, C_), **_todos(AUST + ["duplex", "sduplex", "superaus", "a20", "in825", "ni_c", "ti", "ceram"], A_),
        **_todos(["ni_b", "monel", "ni600", "cocr"] + MART + ["enc", "wc_ni"], B_), "wc": C_, "bronce": D_,
        **_todos(["ptfe", "vidrio", "peek", "fkm", "epdm"], A_), "nbr": C_,
    },
    "tiosulfatos": {
        **_todos(ACERO, r((INF, 80, "C"))), "ss304": r((100, 60, "B"), (INF, 60, "C")),
        **_todos(["ss316", "ss317"], r((1000, 80, "A"), (INF, 80, "B"))),
        **_todos(["duplex", "sduplex", "superaus", "a20", "in825", "ni_c", "ni_b", "ni600", "ti", "cocr", "ceram"], A_),
        "monel": B_, **_todos(MART, r((1000, 60, "B"), (INF, 60, "C"))), "enc": B_, "wc": C_, "wc_ni": B_, "bronce": D_,
        **_todos(POLIMEROS, A_),
    },
    "h2o2": {
        **_todos(ACERO + ["bronce", "wc"], D_), "ss304": r((0, 50, 40, "A"), (0, 101, 40, "B")),
        **_todos(["ss316", "ss317", "duplex", "sduplex", "superaus", "a20", "in825"], r((0, 101, 60, "A"), (0, 101, 90, "B"))),
        "ni_c": r((0, 101, 60, "B")), **_todos(["ni_b", "monel", "ni600"], r((0, 30, 40, "C"))),
        "ti": r((0, 30, 40, "B"), (0, 101, 40, "C")), **_todos(["mart", "mart440"], r((0, 30, 40, "C"))),
        "ph": r((0, 50, 40, "B")), "cocr": r((0, 30, 30, "C")), "enc": r((0, 30, 30, "C")), "wc_ni": r((0, 10, 30, "C")),
        "ceram": A_, "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": A_, "epdm": r((0, 30, 40, "B")), "nbr": D_,
    },
    "nitratos": {
        **_todos(ACERO, r((10000, 60, "B"), (INF, 80, "C"))), **_todos([c for c in METALES if c not in ACERO], A_),
        "bronce": r((10000, 60, "B"), (INF, 60, "C")), "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": C_, "epdm": A_,
        "nbr": C_,
    },
    "aminas": {
        **_todos(ACERO, r((0, 101, 60, "A"), (0, 101, 150, "B"))),
        **_todos([c for c in METALES if c not in ACERO], A_), "monel": A_, "cocr": A_, "bronce": D_,
        "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": D_, "epdm": A_, "nbr": B_,
    },
    "co2": {  # CO₂ con agua libre (corrosión "sweet")
        **_todos(["cs", "crmo"], r((20, 2000, "B"), (1000, 2000, "C"), (INF, 2000, "D"))),
        "crmo9": r((200, 2000, "B"), (INF, 2000, "C")),
        **_todos(["mart", "mart440", "ph"], r((INF, 150, "A"), (INF, 175, "B"))),
        **_todos([c for c in METALES if c not in ACERO + MART], A_), "bronce": B_, "wc": B_,
        "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": B_, "epdm": B_, "nbr": B_,
    },
    "h2s": {  # corrosión general por H₂S húmedo (el agrietamiento se evalúa con ISO 15156)
        **_todos(ACERO, B_), **_todos([c for c in METALES if c not in ACERO], A_), "bronce": D_, "wc": B_,
        "ptfe": A_, "vidrio": A_, "peek": A_, "fkm": r((INF, 100, "B")), "epdm": B_, "nbr": r((10, 2000, "B"), (INF, 2000, "C")),
    },
    "h2": {**_todos(METALES, A_), "ti": r((10, 80, "B"), (INF, 2000, "D")), **_todos(POLIMEROS, A_)},
    "solidos": {**_todos(METALES + POLIMEROS, A_)},
}

# Inconel 625 / 718: como C-276 salvo en ácidos reductores (menos Mo) y nítrico (más Cr)
for _ag, _t in REGLAS.items():
    if "ni_c" in _t and "ni625" not in _t:
        _t["ni625"] = _t["ni_c"]
REGLAS["hcl"]["ni625"] = r((1, 60, "B"), (5, 40, "C"))
REGLAS["h2so4"]["ni625"] = r((0, 40, 60, "B"), (0, 60, 40, "C"), (90, 101, 40, "B"))
REGLAS["hno3"]["ni625"] = r((0, 65, 80, "A"), (0, 65, 100, "B"))
REGLAS["fecl3"]["ni625"] = r((10000, 40, "B"), (60000, 25, "C"))
REGLAS["hf"]["ni625"] = r((0, 10, 40, "C"))

# Grafito flexible (empaquetaduras y juntas): casi inerte salvo frente a oxidantes fuertes.
for _t in REGLAS.values():
    if "_alias" not in _t:
        _t.setdefault("grafito", A_)
REGLAS["hno3"]["grafito"] = r((0, 5, 90, "B"), (0, 20, 40, "C"))
REGLAS["h2so4"]["grafito"] = r((0, 70, 120, "A"), (0, 90, 60, "B"), (0, 96, 30, "C"))
REGLAS["hclo4"]["grafito"] = D_
REGLAS["hipoclorito"]["grafito"] = r((200, 60, "B"), (5000, 40, "C"))
REGLAS["h2o2"]["grafito"] = r((0, 10, 40, "B"), (0, 30, 25, "C"))
REGLAS["cl2"]["grafito"] = r((INF, 100, "B"))
REGLAS["nitratos"]["grafito"] = r((INF, 100, "B"))
REGLAS["so3"]["grafito"] = r((0, 1, 60, "B"))

# Reglas sin agua libre (gas seco o fase orgánica). Lo no listado: A.
SECO: dict[str, dict[str, list]] = {
    "cl2": {**_todos(ACERO, r((INF, 120, "A"), (INF, 200, "B"))), **_todos(AUST, r((INF, 150, "A"), (INF, 300, "B"))),
            "ti": D_, "ptfe": A_, "fkm": B_, "epdm": D_, "nbr": D_, "peek": C_},
    "hcl": {**_todos(ACERO, r((INF, 200, "A"), (INF, 300, "B"))), "ti": r((INF, 200, "B")), "nbr": C_},
    "hf": {**_todos(ACERO, r((INF, 65, "A"), (INF, 150, "B"))), "ti": D_, "ceram": D_, "vidrio": D_, "nbr": D_,
           "epdm": C_},
    "h2s": {**_todos(ACERO, r((INF, 260, "A"), (INF, 400, "C"))), "crmo9": r((INF, 400, "A"), (INF, 500, "B")),
            **_todos(AUST, r((INF, 400, "A"), (INF, 550, "B"))), "bronce": C_, "nbr": B_, "fkm": B_},
    "so2": {**_todos(ACERO, r((INF, 300, "A"), (INF, 400, "B"))), "bronce": B_, "nbr": C_},
    "so3": {**_todos(ACERO, r((INF, 300, "B"))), "epdm": D_, "nbr": D_},
    "o2": {"ti": r((50, 2000, "B"), (INF, 2000, "D")), **_todos(ACERO, r((1000, 200, "A"), (INF, 200, "C"))),
           "nbr": C_, "epdm": B_, "fkm": B_},
    "nh3": {"bronce": D_, "monel": B_, "fkm": D_},
    "azufre": {**_todos(ACERO, r((INF, 300, "A"), (INF, 450, "C"))), **_todos(["ni_c", "ni_b", "monel", "ni600"],
                                                                              r((INF, 300, "B"), (INF, 2000, "D"))),
               "bronce": D_},
    "aminas": {"bronce": D_, "fkm": D_},
    "h2": {"ti": r((10, 80, "B"), (INF, 2000, "D"))},
}
SECO["o2"]["grafito"] = r((INF, 200, "A"), (INF, 370, "B"))   # grafito oxidable en O₂ caliente

# Tabla cualitativa A–D (resistencia química a temperatura ambiente; extracto de las
# filas que corresponden a los agentes del programa). Fuente: tabla de resistencia
# química de materiales de bombas y equipos (Mettler-Toledo / Little Giant).
TABLA_AD = {
    "hcl20": ("Ácido clorhídrico (20 %)", {"ss304": "D", "ss316": "D", "mart440": "D", "ti": "C", "ni_c": "B", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "C", "epdm": "A"}),
    "hcl37": ("Ácido clorhídrico (37 %)", {"ss304": "D", "ss316": "D", "mart440": "D", "ti": "C", "ni_c": "B", "bronce": "D", "ptfe": "A", "ceram": "C", "fkm": "A", "nbr": "C", "epdm": "C"}),
    "h2so4_10": ("Ácido sulfúrico (≤ 10 %)", {"ss304": "D", "ss316": "C", "mart440": "C", "ti": "A", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "C", "epdm": "D"}),
    "h2so4_75": ("Ácido sulfúrico (10–75 %)", {"ss304": "D", "ss316": "D", "mart440": "D", "ti": "C", "ni_c": "B", "bronce": "D", "ptfe": "A", "ceram": "D", "fkm": "A", "nbr": "D", "epdm": "D"}),
    "h2so4_100": ("Ácido sulfúrico (75–100 %)", {"ss316": "D", "ti": "D", "ni_c": "B", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "D"}),
    "hno3_10": ("Ácido nítrico (10 %)", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "D", "cs": "D", "ptfe": "A", "ceram": "B", "fkm": "A", "nbr": "D", "epdm": "B"}),
    "hno3_20": ("Ácido nítrico (20 %)", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "C", "fkm": "A", "nbr": "D", "epdm": "D"}),
    "hno3_50": ("Ácido nítrico (50 %)", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "D", "epdm": "D"}),
    "hno3_c": ("Ácido nítrico (concentrado)", {"ss304": "D", "ss316": "B", "ti": "A", "ni_c": "B", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "B", "nbr": "D", "epdm": "D"}),
    "h3po4_40": ("Ácido fosfórico (≤ 40 %)", {"ss304": "B", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "C", "fkm": "A", "nbr": "D", "epdm": "B"}),
    "h3po4_100": ("Ácido fosfórico (40–100 %)", {"ss304": "C", "ss316": "B", "mart440": "B", "ti": "B", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "D", "fkm": "A", "nbr": "D", "epdm": "B"}),
    "acetico20": ("Ácido acético (20 %)", {"ss304": "B", "ss316": "A", "ti": "A", "ni_c": "A", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "C"}),
    "acetico80": ("Ácido acético (80 %)", {"ss304": "B", "ss316": "A", "ti": "A", "ni_c": "A", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "C"}),
    "acetico100": ("Ácido acético glacial", {"ss304": "B", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "C", "ptfe": "A", "ceram": "A", "fkm": "D", "nbr": "D", "epdm": "B"}),
    "formico": ("Ácido fórmico", {"ss304": "A", "ss316": "B", "mart440": "B", "ti": "C", "ni_c": "A", "bronce": "C", "cs": "D", "ptfe": "A", "ceram": "A", "fkm": "B", "nbr": "D", "epdm": "A"}),
    "oxalico": ("Ácido oxálico (frío)", {"ss304": "A", "ss316": "B", "mart440": "A", "ti": "C", "ni_c": "B", "bronce": "B", "cs": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "B", "epdm": "A"}),
    "citrico": ("Ácido cítrico", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "D", "epdm": "A"}),
    "lactico": ("Ácido láctico", {"ss304": "A", "ss316": "B", "mart440": "C", "ti": "A", "ni_c": "A", "bronce": "D", "cs": "D", "ptfe": "A", "ceram": "A", "fkm": "B", "nbr": "B", "epdm": "B"}),
    "naoh20": ("Hidróxido de sodio (20 %)", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "C", "ptfe": "A", "ceram": "D", "fkm": "A", "nbr": "A", "epdm": "A"}),
    "naoh50": ("Hidróxido de sodio (50 %)", {"ss304": "A", "ss316": "B", "ti": "A", "ni_c": "A", "bronce": "C", "ptfe": "A", "ceram": "D", "fkm": "D", "nbr": "D"}),
    "naoh80": ("Hidróxido de sodio (80 %)", {"ss304": "A", "ss316": "D", "ti": "A", "ni_c": "B", "bronce": "C", "ptfe": "A", "ceram": "D", "fkm": "B", "nbr": "D"}),
    "nh4oh": ("Hidróxido de amonio", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "A", "bronce": "D", "cs": "C", "ptfe": "A", "ceram": "A", "fkm": "B", "nbr": "B", "epdm": "A"}),
    "nh3": ("Amoníaco anhidro", {"ss304": "B", "ss316": "A", "mart440": "A", "ti": "B", "ni_c": "A", "bronce": "D", "cs": "B", "ptfe": "A", "ceram": "A", "fkm": "D", "nbr": "B", "epdm": "A"}),
    "cl2_seco": ("Cloro seco", {"ss304": "A", "ss316": "A", "ti": "D", "ni_c": "A", "bronce": "A", "ptfe": "A", "ceram": "A", "fkm": "D"}),
    "agua_clorada": ("Agua clorada", {"ss316": "D", "ti": "A", "ni_c": "B", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "D"}),
    "hipoclorito": ("Hipoclorito de sodio (20 %)", {"ss304": "C", "ss316": "C", "mart440": "C", "ti": "A", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "C", "epdm": "B"}),
    "h2o2_10": ("Peróxido de hidrógeno (10 %)", {"ss304": "C", "ss316": "C", "ti": "C", "ni_c": "A", "bronce": "D", "ptfe": "A", "ceram": "A", "nbr": "A"}),
    "h2o2_30": ("Peróxido de hidrógeno (30 %)", {"ss316": "B", "ti": "B", "ni_c": "A", "ptfe": "A", "fkm": "A", "nbr": "D"}),
    "so2": ("Dióxido de azufre (húmedo)", {"ss304": "A", "ss316": "A", "mart440": "C", "ti": "A", "ni_c": "B", "bronce": "B", "ptfe": "A", "ceram": "A", "fkm": "D", "nbr": "D", "epdm": "A"}),
    "so2_seco": ("Dióxido de azufre (seco)", {"ss304": "A", "ss316": "A", "ni_c": "A", "bronce": "A", "cs": "B", "ptfe": "A", "ceram": "A", "fkm": "D"}),
    "fecl3": ("Cloruro férrico", {"ss304": "D", "ss316": "D", "mart440": "D", "ti": "A", "ni_c": "B", "bronce": "D", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "D", "epdm": "A"}),
    "aminas": ("Aminas", {"ss304": "A", "ss316": "A", "ti": "B", "ni_c": "A", "bronce": "B", "cs": "B", "ptfe": "A", "ceram": "A", "fkm": "D", "nbr": "D", "epdm": "B"}),
    "tiosulfato": ("Tiosulfato de sodio", {"ss304": "A", "ss316": "A", "ti": "A", "bronce": "D", "cs": "B", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "B", "epdm": "A"}),
    "sulfuro": ("Sulfuro de sodio", {"ss304": "A", "ss316": "B", "ti": "A", "ni_c": "B", "bronce": "D", "cs": "B", "ptfe": "A", "ceram": "A", "fkm": "A", "nbr": "C", "epdm": "A"}),
    "nitrato": ("Nitrato de sodio", {"ss304": "A", "ss316": "A", "mart440": "A", "ti": "A", "ni_c": "B", "bronce": "B", "cs": "B", "ptfe": "A", "ceram": "A", "fkm": "D", "nbr": "C", "epdm": "A"}),
}
FUENTE_TABLA_AD = ("Tabla de resistencia química A–D (Mettler-Toledo / Little Giant), a temperatura ambiente; "
                   "extracto de las filas aplicables")


def fila_tabla(agente: str, c: float | None, acuoso: bool) -> str | None:
    """Fila de TABLA_AD que corresponde al agente y la concentración (unidad base)."""
    c = c or 0
    if agente == "hcl":
        return "hcl20" if c <= 20 else "hcl37"
    if agente == "h2so4":
        return "h2so4_10" if c <= 10 else "h2so4_75" if c <= 75 else "h2so4_100"
    if agente == "hno3":
        return "hno3_10" if c <= 10 else "hno3_20" if c <= 20 else "hno3_50" if c <= 50 else "hno3_c"
    if agente == "h3po4":
        return "h3po4_40" if c <= 40 else "h3po4_100"
    if agente == "acetico":
        return "acetico20" if c <= 20 else "acetico80" if c <= 80 else "acetico100"
    if agente in ("naoh", "koh"):
        return "naoh20" if c <= 20 else "naoh50" if c <= 50 else "naoh80"
    if agente == "nh3":
        return "nh4oh" if acuoso else "nh3"
    if agente == "cl2":
        return "agua_clorada" if acuoso else "cl2_seco"
    if agente == "h2o2":
        return "h2o2_10" if c <= 10 else "h2o2_30"
    if agente == "so2":
        return "so2" if acuoso else "so2_seco"
    return {"formico": "formico", "oxalico": "oxalico", "citrico": "citrico", "lactico": "lactico",
            "hipoclorito": "hipoclorito", "fecl3": "fecl3", "aminas": "aminas", "tiosulfatos": "tiosulfato",
            "sulfuros": "sulfuro", "nitratos": "nitrato"}.get(agente)


# ---------------------------------------------------------------------------
# Normalización de la concentración ingresada
# ---------------------------------------------------------------------------
@dataclass
class AgenteServicio:
    """Una fila de la tabla de agentes de la solapa de materiales."""
    clave: str
    unidad: str = ""
    concentracion: float | None = None
    fase: str = "Desconocida"
    texto: str = ""                # nombre libre (agente «Otro»)


@dataclass
class AgenteNormalizado:
    agente: Agente
    entrada: AgenteServicio
    valor: float | None            # en la unidad base (None = fase gaseosa sin agua o sin dato)
    kPa: float | None = None       # presión parcial cuando corresponde
    supuesto: bool = False         # se usó la concentración conservadora por falta de dato
    notas: list[str] = field(default_factory=list)
    masa_en_gas: bool = False      # se informó en % p/p o ppm masa estando en fase gas (convertido a molar)

    @property
    def unidad_base(self) -> str:
        return {"mgL": "mg/L", "pct": "% p/p", "kPa": "kPa"}[self.agente.base]

    def texto(self) -> str:
        from .modelos import _n
        partes = []
        if self.valor is not None:
            partes.append(f"{_n(self.valor, 4 if self.valor < 1 else 1)} {self.unidad_base}")
        if self.kPa is not None and self.agente.base != "kPa":
            partes.append(f"{_n(self.kPa, 3)} kPa parcial")
        return " · ".join(partes) or "—"


def _w_desde_molar(x_pct: float, MW: float) -> float:
    x = x_pct / 100
    return 100 * x * MW / (x * MW + (1 - x) * 18.015)


def _fmt(x: float) -> str:
    return f"{x:.4g}".replace(".", ",")


def normalizar(a: AgenteServicio, P_kPa: float, SG: float = 1.0, M_gas: float | None = None) -> AgenteNormalizado:
    """Convierte la concentración ingresada a la unidad base del agente.

    P_kPa es la presión absoluta del servicio (para pasar de ppmv o % molar en
    gas a presión parcial). SG es la densidad relativa del líquido (mg/L ↔ ppm).
    M_gas es la masa molar del gas [kg/kmol]: con ella una fracción en masa
    informada en fase gas (% p/p, ppm masa) se pasa a fracción molar,
    y_i = w_i · M_gas / M_i (sin dato se usa la del aire, 28,97 kg/kmol).
    """
    ag = AGENTES[a.clave]
    u, v = a.unidad, a.concentracion
    n = AgenteNormalizado(ag, a, None)
    if v is None or v < 0:
        n.valor = ag.alto if ag.base != "kPa" else None
        n.kPa = ag.alto if ag.base == "kPa" else None
        n.supuesto = True
        n.notas.append("Sin concentración informada: se evalúa con un valor alto conservador.")
        if ag.base == "kPa":
            n.valor = n.kPa
        return n
    if a.fase == "Gas / vapor" and u in ("% p/p", "ppm masa"):
        w = v / 100 if u == "% p/p" else v * 1e-6
        Mm = M_gas or 28.97
        y = min(1.0, w * Mm / ag.MW) if ag.MW else w
        n.masa_en_gas = True
        n.notas.append(f"Informado en {u} en fase gas: convertido a fracción molar y = w·M/Mi = {_fmt(y * 100)} % "
                       f"molar (M del gas {_fmt(Mm)} kg/kmol{'' if M_gas else ', la del aire por falta de dato'}). "
                       "Para gases la unidad habitual es ppmv o % molar.")
        u, v = "% molar", y * 100
    gas = u in UNIDADES_GAS or (u == "% molar" and a.fase == "Gas / vapor")
    if gas:
        p = v * 100 if u == "bar(a) parcial" else v if u == "kPa parcial" else \
            v * 1e-6 * P_kPa if u == "ppmv" else v / 100 * P_kPa
        n.kPa = p
        if ag.base == "kPa":
            n.valor = p
        elif ag.henry:
            mgL = p * ag.henry
            n.valor = mgL if ag.base == "mgL" else min(100.0, mgL / 10000)
            n.notas.append("Concentración disuelta estimada con la ley de Henry a 25 °C.")
        else:
            n.valor = None      # ácido en fase gas: se decide con o sin agua al evaluar
        return n
    # unidades de líquido
    if u == "mg/L":
        mgL = v
    elif u == "ppm masa":
        mgL = v * SG
    elif u == "% p/p":
        mgL = v * 10000 * SG
    elif u == "mol/L":
        mgL = v * ag.MW * 1000
    elif u == "% molar":
        mgL = _w_desde_molar(v, ag.MW) * 10000 * SG
    else:
        mgL = v
    if ag.base == "mgL":
        n.valor = mgL
    elif ag.base == "pct":
        n.valor = min(100.0, mgL / 10000 / SG)
    else:
        if not ag.henry:
            n.valor = None
        else:
            n.kPa = mgL / ag.henry
            n.valor = n.kPa
            n.notas.append("Presión parcial equivalente estimada con la ley de Henry a 25 °C.")
    return n


# ---------------------------------------------------------------------------
# Evaluación
# ---------------------------------------------------------------------------
def _peor(*niveles: str) -> str:
    v = [x for x in niveles if x and x in NIVELES]
    return max(v, key=NIVELES.index) if v else "?"


def nivel_regla(agente: str, clase: str, c: float | None, T_C: float, acuoso: bool) -> str:
    """Nivel A–D según las reglas (``?`` si no hay datos para la clase)."""
    ag = AGENTES[agente]
    if ag.alias:
        dest, f = ag.alias
        return nivel_regla(dest, clase, None if c is None else c * f, T_C, acuoso)
    if not acuoso and (ag.acuoso or agente in SECO):
        tabla = SECO.get(agente, {})
        filas = tabla.get(clase, A_)
    else:
        tabla = REGLAS.get(agente)
        if tabla is None:
            return "?"
        if "_alias" in tabla:
            dest, cc = tabla["_alias"][0]
            return nivel_regla(dest, clase, cc, T_C, True)
        if clase not in tabla:
            return "?"
        filas = tabla[clase]
    if c is None:
        c = ag.alto
    for cmin, cmax, Tmax, niv in filas:
        if cmin <= c <= cmax and T_C <= Tmax:
            return niv
    return "D"


@dataclass
class Compatibilidad:
    agente: str
    nivel: str
    nivel_regla: str
    nivel_tabla: str | None
    detalle: str


def evaluar(material, n: AgenteNormalizado, T_C: float, acuoso: bool) -> Compatibilidad:
    """Compatibilidad de un material (``materiales.Material``) con un agente normalizado."""
    from .modelos import _n
    ag = n.agente
    c = n.valor
    hay_agua = acuoso and n.entrada.fase not in ("Orgánica líquida",)
    if c is None and ag.base == "pct":
        # ácido informado como gas: con agua condensa concentrado
        c = ag.alto if hay_agua else None
    regla = _peor(*(nivel_regla(ag.clave, q, c, T_C, hay_agua) for q in material.quimica))
    fila = fila_tabla(ag.clave, c, hay_agua)
    tab = None
    if fila:
        vals = [TABLA_AD[fila][1].get(q) for q in material.quimica]
        vals = [v for v in vals if v]
        tab = _peor(*vals) if vals else None
    final = _peor(regla, tab) if regla != "?" else (tab or "?")
    cond = f"{_n(c, 4 if c < 1 else 1)} {n.unidad_base}" if c is not None else "fase gaseosa sin agua"
    det = (f"{ag.formula} ({cond}, {_n(T_C, 0)} °C, {'con agua' if hay_agua else 'sin agua libre'}): "
           f"regla {NIVEL_TXT.get(regla, regla)}")
    if tab:
        det += f"; tabla A–D «{TABLA_AD[fila][0]}» {tab}"
        if tab != regla and regla != "?":
            det += " → se adopta el más conservador"
    return Compatibilidad(ag.clave, final, regla, tab, det)
