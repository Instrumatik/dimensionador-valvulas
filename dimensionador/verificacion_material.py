"""Verificación rápida de un material de la biblioteca (v0.16.1).

Para un material elegido, sin cargar un servicio:
- galling frente a cada material de la biblioteca (misma regla que usa la selección de 3-Materiales);
- comportamiento frente a los mecanismos de deterioro M01–M33: nivel A–D en una condición de referencia y el
  límite del material (hasta qué concentración, presión parcial o temperatura resiste) a la temperatura dada.

Usa las mismas reglas de quimica.py, los datos ISO 15156 / NACE de materiales.py y la regla de galling de
seleccion_materiales.py, así que coincide con lo que el programa decide en un cálculo. Es preselección: no
reemplaza los datos del fabricante ni el criterio del especialista en corrosión.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import materiales as MT, quimica as Q
from .modelos import _n

INTERNOS = frozenset({"obturador", "asiento", "jaula", "guia", "vastago"})

# Lectura del nivel A–D en términos de mitigación
RESULTADO = {"A": "Evita", "B": "Reduce", "C": "Mitiga poco", "D": "No resiste", "?": "Sin datos",
             "-": "No aplica"}
EXPLICA_NIVEL = {
    "A": "resiste sin daño apreciable en esa condición (A, excelente)",
    "B": "resiste con una velocidad de daño baja; aceptable con vigilancia (B, bueno)",
    "C": "se daña a una velocidad que en general no es aceptable (C, no recomendado)",
    "D": "no resiste; descartar (D)",
    "?": "no hay reglas para este material y este agente",
    "-": "el mecanismo no aplica a este material",
}

# Resistencia propia al galling por grupo tribológico
GALLING_GRUPO = {
    "cocr": ("Excelente", "Recargue Co-Cr (Stellite): su película y sus carburos resisten la adhesión aun contra sí "
                          "mismo; es el remedio estándar contra el galling."),
    "wc": ("Excelente", "Carburo cementado: muy duro (≈ 70 HRC) y no se suelda en frío."),
    "ceram": ("Excelente", "Cerámica: no metálica y muy dura; no hay soldadura en frío."),
    "n60": ("Muy buena", "Nitronic 60 (Mn-Si) está formulado contra el galling: resiste incluso frente a los "
                         "austeníticos; contra sí mismo el riesgo es medio."),
    "nit": ("Muy buena", "La capa nitrurada (≈ 1000 HV) separa los metales base; vigilar que no se desgaste."),
    "enc": ("Muy buena", "El recubrimiento duro (níquel químico o cromo, ≈ 50–60 HRC) evita la adhesión mientras "
                         "esté entero."),
    "cu": ("Buena", "El bronce contra acero es la pareja disímil clásica de bajo galling; contra sí mismo, medio."),
    "mart": ("Buena si está endurecido", "Los martensíticos templados (≥ 38 HRC) resisten; recocidos no."),
    "ph": ("Buena si hay diferencia de dureza", "17-4PH contra 17-4PH en la misma condición tiene riesgo alto; con "
                                               "≥ 10 HRC de diferencia o una pareja dura, bajo."),
    "cs": ("Regular", "El acero al carbono blando tiene tendencia media; endurecido o con pareja dura, baja."),
    "aus": ("Pobre", "Los austeníticos (304, 316) blandos se sueldan en frío con facilidad, sobre todo contra sí "
                     "mismos: siempre necesitan una pareja dura o un recargue."),
    "ni": ("Pobre", "Las aleaciones de níquel blandas tienen la tendencia más alta a la soldadura en frío."),
    "dup": ("Pobre", "Los dúplex se comportan como los austeníticos: necesitan una pareja dura."),
    "ti": ("Pobre", "El titanio tiene una tendencia muy alta al galling: necesita recubrimiento o pareja dura."),
    "polimero": ("No aplica", "Material no metálico: no se suelda en frío con el metal."),
}

# SCC por cloruros por clase química: (temperatura orientativa de inicio °C o None si no es susceptible, texto)
_CL_SCC = {
    "ss304": (60, "Austenítico 304: susceptible a la SCC por cloruros por encima de ~ 60 °C."),
    "ss316": (60, "Austenítico 316: susceptible por encima de ~ 60 °C (algo mejor que el 304)."),
    "ss317": (70, "317: susceptible por encima de ~ 70 °C."),
    "superaus": (120, "Superaustenítico (6Mo): resistente hasta ~ 120 °C en la mayoría de los servicios."),
    "duplex": (150, "Dúplex: resistente hasta ~ 150 °C por su estructura de dos fases."),
    "sduplex": (180, "Superdúplex: resistente hasta ~ 180 °C."),
    "a20": (150, "Aleación 20 (≈ 33 % Ni): resistente hasta ~ 150 °C."),
    "in825": (200, "Aleación 825 (≈ 40 % Ni): prácticamente inmune en servicios habituales."),
    "ni600": (None, "Aleación de níquel: prácticamente inmune a la SCC por cloruros."),
    "ni625": (None, "Aleación de níquel: prácticamente inmune a la SCC por cloruros."),
    "ni_c": (None, "Aleación C: prácticamente inmune a la SCC por cloruros."),
    "ni_b": (None, "Aleación B: inmune a la SCC por cloruros."),
    "monel": (None, "Monel: inmune a la SCC por cloruros."),
    "ti": (None, "Titanio: inmune a la SCC por cloruros en agua hasta ~ 200 °C."),
    "cs": (None, "Acero al carbono: no sufre SCC por cloruros (sí corrosión general y picaduras)."),
    "crmo": (None, "Cr-Mo: no sufre SCC por cloruros."),
    "crmo9": (None, "9Cr / 12Cr: no sufre SCC por cloruros."),
    "mart": (60, "Martensítico: susceptible al agrietamiento en cloruros, mayor cuanto más duro."),
    "mart440": (40, "440C: muy susceptible por su dureza."),
    "ph": (80, "17-4PH: susceptible si está en condición dura (H900); H1150 resiste mejor."),
    "bronce": (None, "Bronce: no sufre SCC por cloruros."),
    "cocr": (None, "Co-Cr (Stellite): no sufre SCC por cloruros."),
    "wc": (None, "Carburo: no sufre SCC por cloruros."),
    "wc_ni": (None, "Carburo con ligante de níquel: no sufre SCC por cloruros."),
    "ceram": (None, "Cerámica: no sufre SCC."),
    "enc": (None, "El recubrimiento no sufre SCC; vale lo del metal base."),
}

# NH₄HS (aguas agrias): orden de API 932-B / API 571 por familia
_NH4HS = {"cs": "C", "crmo": "C", "crmo9": "C", "mart": "C", "mart440": "C", "ph": "C", "ss304": "B",
          "ss316": "B", "ss317": "B", "superaus": "A", "duplex": "A", "sduplex": "A", "a20": "A", "in825": "A",
          "ni625": "A", "ni_c": "A", "ni600": "B", "ni_b": "B", "monel": "C", "ti": "A", "bronce": "D",
          "cocr": "A", "wc": "A", "wc_ni": "A", "ceram": "A", "enc": "B"}


@dataclass
class FilaGalling:
    material: MT.Material
    nivel: str
    motivo: str
    remedio: str


@dataclass
class FilaMecanismo:
    codigo: str
    nombre: str
    referencia: str      # condición de referencia evaluada
    nivel: str           # A, B, C, D, ? o -
    limite: str          # hasta dónde resiste el material
    explicacion: str

    @property
    def resultado(self) -> str:
        return RESULTADO[self.nivel]


def metalico(m: MT.Material) -> bool:
    return m.galling != "polimero"


def _nivel(m: MT.Material, agente: str, c: float, T: float, acuoso: bool = True) -> str:
    """Nivel A–D del material con el agente (regla + tabla A–D, el más conservador), como quimica.evaluar."""
    regla = Q._peor(*(Q.nivel_regla(agente, q, c, T, acuoso) for q in m.quimica))
    fila = Q.fila_tabla(agente, c, acuoso)
    tab = None
    if fila:
        vals = [v for v in (Q.TABLA_AD[fila][1].get(q) for q in m.quimica) if v]
        tab = Q._peor(*vals) if vals else None
    return Q._peor(regla, tab) if regla != "?" else (tab or "?")


def _limite(m, agente, valores, T, unidad, acuoso=True, fmt=None) -> str:
    """Mayor valor de la serie con nivel A y con nivel ≤ B a la temperatura T."""
    fmt = fmt or (lambda v: _n(v, 0) if v >= 10 else _n(v, 2))
    hasta = {"A": None, "B": None}
    for v in valores:
        n = _nivel(m, agente, v, T, acuoso)
        if n == "A":
            hasta["A"] = v
        if n in "AB" and n != "?":
            hasta["B"] = v
    if hasta["B"] is None:
        return f"No llega a B ni con {fmt(valores[0])} {unidad}"
    partes = []
    if hasta["A"] is not None:
        partes.append(f"A hasta {fmt(hasta['A'])} {unidad}")
    if hasta["B"] != hasta["A"]:
        partes.append(f"B hasta {fmt(hasta['B'])} {unidad}")
    txt = "; ".join(partes)
    if hasta["B"] == valores[-1]:
        txt += " (todo el rango revisado)"
    return txt


def _limite_T(m, agente, c, unidad_c, acuoso=False) -> str:
    """Mayor temperatura (desde 100 °C, sin interrupciones) con nivel A y con nivel ≤ B a la concentración c."""
    hasta = {"A": None, "B": None}
    okA = okB = True
    for T in range(100, 651, 10):
        n = _nivel(m, agente, c, T, acuoso)
        okA = okA and n == "A"
        okB = okB and n in ("A", "B")
        if okA:
            hasta["A"] = T
        if okB:
            hasta["B"] = T
    if hasta["B"] is None:
        return f"No llega a B a 100 °C con {unidad_c}"
    if hasta["B"] == 650:
        return f"{'A' if hasta['A'] == 650 else 'B'} hasta 650 °C o más con {unidad_c}"
    t = f"A hasta {hasta['A']} °C" if hasta["A"] else ""
    if hasta["B"] != hasta["A"]:
        t += ("; " if t else "") + f"B hasta {hasta['B']} °C"
    return t + f" con {unidad_c}"


_CL = [10, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]
_PCT = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 40, 50, 60, 70, 80, 93, 98]
_KPA = [0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000]


def _expl(nivel: str, extra: str = "") -> str:
    base = f"En la condición de referencia el material {EXPLICA_NIVEL[nivel]}."
    return base + (" " + extra if extra else "")


def mecanismos(m: MT.Material, T: float) -> list[FilaMecanismo]:
    """Comportamiento del material frente a cada mecanismo de deterioro, a la temperatura T [°C]."""
    met = metalico(m) or any(q in Q.METALES for q in m.quimica)
    t = _n(T, 0)
    out: list[FilaMecanismo] = []

    def add(cod, nom, ref, niv, lim, expl):
        out.append(FilaMecanismo(cod, nom, ref, niv, lim, expl))

    # M01 ácidos
    n = _nivel(m, "h2so4", 10, T)
    lims = [f"{f}: " + _limite(m, a, _PCT[:13] if a != "h2so4" else _PCT, T, "%")
            for a, f in (("h2so4", "H₂SO₄"), ("hcl", "HCl"), ("h3po4", "H₃PO₄"), ("hno3", "HNO₃"))]
    add("M01", "Corrosión general por ácidos", f"H₂SO₄ 10 % a {t} °C", n, "\n".join(lims),
        _expl(n, "Cada ácido tiene su propio límite (columna de la derecha); el HCl es el más agresivo para "
                 "los inoxidables y el HNO₃ (oxidante) el más benigno para ellos."))
    # M02 picaduras por cloruros
    n = _nivel(m, "cloruros", 1000, T)
    pren = f" PREN = {_n(m.pren, 0)}: a mayor PREN, mayor resistencia a las picaduras." if m.pren else ""
    add("M02", "Picaduras y rendijas por cloruros", f"Cl⁻ 1.000 mg/L a {t} °C con agua", n,
        _limite(m, "cloruros", _CL, T, "mg/L Cl⁻"), _expl(n, "La resistencia depende del cromo, el molibdeno y "
                                                           "el nitrógeno (PREN)." + pren))
    # M03 SCC por cloruros
    clases = [q for q in m.quimica if q in _CL_SCC]
    if clases and met:
        peor = None
        textos = []
        for q in clases:
            Tl, tx = _CL_SCC[q]
            textos.append(tx)
            if Tl is not None and (peor is None or Tl < peor):
                peor = Tl
        if peor is None:
            niv, lim = "A", "No susceptible"
        else:
            niv = "A" if T < peor - 10 else "B" if T < peor else "C" if T < peor + 40 else "D"
            lim = f"Riesgo desde ~ {peor} °C con cloruros y tensión"
        add("M03", "SCC por cloruros (Cl-SCC)", f"Cloruros con agua a {t} °C", niv, lim, " ".join(textos))
    else:
        add("M03", "SCC por cloruros (Cl-SCC)", "—", "-", "—", "No aplica a materiales no metálicos.")
    # M04 SSC
    nace = m.iso15156
    if not met:
        add("M04", "Agrietamiento por H₂S (SSC)", "ISO 15156 / NACE MR0175", "-", "—",
            "No aplica a materiales no metálicos.")
    else:
        niv = {"aceptable": "A", "condicional": "B", "no": "D"}.get(nace.estado, "?")
        lim = []
        if nace.dureza_max_HRC:
            lim.append(f"dureza ≤ {_n(nace.dureza_max_HRC, 0)} HRC")
        if nace.pH2S_max_kPa:
            lim.append(f"pH₂S ≤ {_n(nace.pH2S_max_kPa, 1)} kPa")
        if nace.T_max_C:
            lim.append(f"T ≤ {_n(nace.T_max_C, 0)} °C")
        if nace.pH_min:
            lim.append(f"pH ≥ {_n(nace.pH_min, 1)}")
        if not nace.azufre:
            lim.append("sin azufre elemental")
        expl = {"A": "Aceptable en ISO 15156 / NACE MR0175 dentro de sus límites.",
                "B": "Aceptable con condiciones (dureza, tratamiento o límites ambientales).",
                "D": "No aceptado para servicio agrio en esta condición (dureza o tratamiento fuera de norma).",
                "?": "Sin datos en ISO 15156 para este material."}[niv]
        if nace.nota:
            expl += " " + nace.nota
        add("M04", "Agrietamiento por H₂S (SSC)", "Servicio agrio (pH₂S ≥ 0,3 kPa)", niv,
            ", ".join(lim) or "Sin límites propios", expl)
    # M05 HIC
    if m.quimica[0] in ("cs", "crmo") and met:
        lam = "fund" not in m.forma.lower() and "forj" not in m.forma.lower() and "forja" not in m.forma.lower()
        niv = "C" if lam else "A"
        add("M05", "HIC / SOHIC", "H₂S húmedo", niv, "Chapa o tubo laminado: requiere ensayo NACE TM0284"
            if lam else "Fundición o forja: no susceptible",
            "El HIC afecta a aceros al carbono laminados con inclusiones alargadas; fundiciones y forjas no lo sufren.")
    else:
        add("M05", "HIC / SOHIC", "H₂S húmedo", "A" if met else "-", "No susceptible" if met else "—",
            "Solo afecta a aceros al carbono y de baja aleación laminados." if met else "No aplica.")
    # M06 CO2
    n = _nivel(m, "co2", 100, T)
    add("M06", "Corrosión por CO₂ (sweet)", f"pCO₂ 100 kPa con agua a {t} °C", n,
        _limite(m, "co2", _KPA, T, "kPa CO₂"),
        _expl(n, "Con más de ~ 12 % de Cr el material forma una película pasiva y resiste."))
    # M07 oxidantes
    n = _nivel(m, "hipoclorito", 10, T)
    add("M07", "Ataque por oxidantes (cloro activo)", f"Hipoclorito 10 mg/L a {t} °C", n,
        _limite(m, "hipoclorito", [0.5, 1, 2, 5, 10, 50, 100, 500, 1000, 5000], T, "mg/L"),
        _expl(n, "El cloro activo rompe la película pasiva; el titanio y la aleación C son los más resistentes."))
    # M08 cáustico
    n = _nivel(m, "naoh", 20, T)
    add("M08", "Corrosión / agrietamiento cáustico", f"NaOH 20 % a {t} °C", n,
        _limite(m, "naoh", [1, 2, 5, 10, 20, 30, 40, 50], T, "% NaOH"),
        _expl(n, "El acero al carbono se agrieta en soda caliente sin alivio de tensiones; el níquel es el "
                 "material de referencia para soda concentrada y caliente."))
    # M09 HF
    n = _nivel(m, "hf", 5, T)
    add("M09", "Ataque por HF / fluoruros", f"HF 5 % a {t} °C", n,
        _limite(m, "hf", [0.1, 0.5, 1, 2, 5, 10, 20, 40, 50], T, "% HF"),
        _expl(n, "Monel y acero al carbono (con limitaciones) son los materiales clásicos; el vidrio y el "
                 "titanio se disuelven."))
    # M10 sulfuros
    n = _nivel(m, "sulfuros", 100, T)
    add("M10", "Ataque por azufre / sulfuros", f"Sulfuros 100 mg/L a {t} °C", n,
        _limite(m, "sulfuros", [1, 10, 50, 100, 500, 1000, 5000, 10000], T, "mg/L"),
        _expl(n, "El cobre y sus aleaciones son los más atacados."))
    # M14 erosión y M16 cavitación (índices 0–10 de la biblioteca)
    for cod, nom, idx, ref in (("M14", "Erosión por partículas", m.erosion, "Sólidos en el fluido"),
                               ("M16", "Cavitación", m.cavitacion, "Cavitación en el trim")):
        niv = "A" if idx >= 8 else "B" if idx >= 5 else "C" if idx >= 3 else "D"
        add(cod, nom, ref, niv, f"Índice {idx}/10 · dureza {m.dureza_txt}",
            f"Resistencia relativa de la biblioteca: {idx} de 10 (Stellite y carburos 8–10; 316 recocido 2). "
            + ("Apto para servicio severo." if niv == "A" else "Apto para servicio moderado." if niv == "B" else
               "Solo para servicio leve; con daño severo use recargue duro." if niv == "C" else
               "No apto: el material se desgasta rápido."))
    # M19 galling: se informa en la otra pestaña
    cal, tx = GALLING_GRUPO.get(m.galling, ("—", ""))
    niv = {"Excelente": "A", "Muy buena": "A", "Buena": "B", "Buena si está endurecido": "B" if m.HRC_efectiva >= 38
           else "C", "Buena si hay diferencia de dureza": "B", "Regular": "C", "Pobre": "D", "No aplica": "-"}.get(cal, "?")
    add("M19", "Galling / soldadura en frío", "Contacto deslizante (pareja)", niv, f"Resistencia propia: {cal}",
        tx + " La pestaña Galling muestra el riesgo con cada material.")
    # M21 creep / grafitización
    niv = "A" if T <= m.T_max_C - 50 else "B" if T <= m.T_max_C else "D"
    add("M21", "Temperatura máxima / creep / grafitización", f"{t} °C", niv,
        f"T máx. de uso {_n(m.T_max_C, 0)} °C · mín. {_n(m.T_min_C, 0)} °C",
        "Por encima de la temperatura máxima el material pierde resistencia (creep), se grafitiza (acero al "
        "carbono > 425 °C prolongado) o se degrada (polímeros).")
    # M22 hidrógeno
    if met:
        n = _nivel(m, "h2", 1000, T, False)
        fr = m.HRC_efectiva > 38
        lim = _limite(m, "h2", [10, 100, 300, 1000, 3000, 10000], T, "kPa H₂", acuoso=False)
        add("M22", "Hidrógeno: HTHA y fragilización", f"pH₂ 1.000 kPa a {t} °C", "B" if fr and n == "A" else n,
            lim + (" · dureza > 38 HRC: riesgo de fragilización" if fr else ""),
            _expl(n, "El HTHA afecta al acero al carbono a alta temperatura (curvas de Nelson, API RP 941); "
                     "los materiales muy duros se fragilizan con hidrógeno."))
    else:
        add("M22", "Hidrógeno: HTHA y fragilización", "—", "-", "—", "No aplica a materiales no metálicos.")
    # M24 amoníaco anhidro
    n = _nivel(m, "nh3", 30, T, False)
    add("M24", "Amoníaco anhidro", f"NH₃ sin agua a {t} °C", n, "Amoníaco seco (con agua, ver M08)", _expl(n, "El acero al carbono puede agrietarse "
        "en amoníaco anhidro con oxígeno; el cobre y sus aleaciones no se usan."))
    # M25 aminas
    n = _nivel(m, "aminas", 45, T)
    add("M25", "SCC y corrosión por aminas", f"Amina 45 % a {t} °C", n,
        _limite(m, "aminas", [5, 15, 30, 45, 50], T, "% amina"),
        _expl(n, "El acero al carbono necesita alivio de tensiones por encima de ~ 60 °C (API RP 945)."))
    # M26 nitratos
    n = _nivel(m, "nitratos", 10000, T)
    add("M26", "SCC por nitratos", f"NO₃⁻ 10.000 mg/L a {t} °C", n,
        _limite(m, "nitratos", [100, 1000, 5000, 10000, 50000], T, "mg/L NO₃⁻"),
        _expl(n, "Los nitratos calientes y concentrados agrietan los aceros al carbono."))
    # M27 oxígeno
    n = _nivel(m, "o2", 1000, T, False)
    add("M27", "Ignición en oxígeno", f"O₂ seco 1.000 kPa a {t} °C", n,
        _limite(m, "o2", [21, 100, 300, 1000, 3000, 10000], T, "kPa O₂", acuoso=False),
        _expl(n, "Las aleaciones de níquel y cobre son las más resistentes a la ignición; el acero al carbono "
                 "y los polímeros se limitan por presión y velocidad (ASTM G94)."))
    # M30 sulfidación
    n = _nivel(m, "azufre_hc", 1.0, T, False)
    add("M30", "Sulfidación a alta temperatura", f"Hidrocarburo con 1 % S a {t} °C", n,
        _limite_T(m, "azufre_hc", 1.0, "1 % S"),
        _expl(n, "Crece con la temperatura y el azufre; el cromo la reduce (API RP 939-C)."))
    # M31 nafténica
    n = _nivel(m, "tan", 2.0, max(T, 0), False)
    n300 = _nivel(m, "tan", 2.0, 300, False)
    add("M31", "Corrosión por ácidos nafténicos", f"TAN 2 a {t} °C", n,
        f"Con TAN 2 a 300 °C: {n300} · con TAN 1 a 300 °C: {_nivel(m, 'tan', 1.0, 300, False)}",
        _expl(n, "Solo actúa entre ~ 220 y 400 °C; el molibdeno la reduce (316, 317L)."))
    # M32 NH4HS
    niv = Q._peor(*(_NH4HS.get(q, "?") for q in m.quimica)) if met else "-"
    add("M32", "Bisulfuro de amonio (aguas agrias)", "NH₄HS en agua, velocidad alta", niv,
        "Depende de la concentración de NH₄HS y la velocidad" if met else "—",
        ("Orden de resistencia de API 932-B / API 571: acero al carbono < 316 < dúplex, 825, 625 y titanio. "
         + EXPLICA_NIVEL[niv].capitalize() + ".") if met else "No aplica.")
    # M33 hinchamiento
    if met:
        add("M33", "Hinchamiento en hidrocarburos", "—", "-", "—",
            "Solo afecta a elastómeros y polímeros; los metales no se hinchan.")
    else:
        n = _nivel(m, "hidrocarburos", 100, T, False)
        add("M33", "Hinchamiento en hidrocarburos", f"Hidrocarburo a {t} °C", n,
            _limite_T(m, "hidrocarburos", 100, "hidrocarburo") if n != "D" else "No usar con hidrocarburos",
            _expl(n, "El EPDM se hincha; NBR y FKM son los elastómeros habituales."))
    return out


def galling(m: MT.Material, T: float, todos: bool = False) -> list[FilaGalling]:
    """Riesgo de galling del material con cada material de la biblioteca (internos, o todos)."""
    from .seleccion_materiales import riesgo_galling
    orden = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}
    filas = []
    for p in MT.MATERIALES.values():
        if not todos and not (p.componentes & INTERNOS):
            continue
        niv, mot, rem = riesgo_galling(m, p, T)
        filas.append(FilaGalling(p, niv, mot, rem))
    filas.sort(key=lambda f: (orden[f.nivel], f.material.nombre))
    return filas


def resumen_galling(m: MT.Material, filas: list[FilaGalling]) -> str:
    cal, tx = GALLING_GRUPO.get(m.galling, ("—", ""))
    n = len(filas) or 1
    c = {k: sum(f.nivel == k for f in filas) for k in ("ALTO", "MEDIO", "BAJO")}
    return (f"Resistencia propia al galling: {cal}. {tx} Con los {len(filas)} materiales revisados: riesgo bajo "
            f"con {c['BAJO']} ({_n(100 * c['BAJO'] / n, 0)} %), medio con {c['MEDIO']} "
            f"({_n(100 * c['MEDIO'] / n, 0)} %) y alto con {c['ALTO']} ({_n(100 * c['ALTO'] / n, 0)} %).")
