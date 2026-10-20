"""Selección de materiales por componente (cuerpo, bonete, asiento, jaula, guía, obturador, vástago).

Con pocos datos del servicio (solapa 3) y los resultados del cálculo
(solapa 2: temperaturas, presión de diseño, rating, cavitación, flashing,
caída de presión) el motor:

1. completa los agentes implícitos del fluido (p. ej. cloruros del agua de mar);
2. detecta los mecanismos de deterioro potenciales y si el servicio es agrio;
3. fija la norma de servicio agrio (ISO 15156 en upstream, ISO 17945 en refino);
4. fija la dureza mínima de los internos según la severidad de la cavitación,
   el flashing, los sólidos y la caída de presión;
5. para cada componente descarta los materiales fuera de temperatura,
   presión-temperatura (ASME B16.34), compatibilidad química, servicio agrio o
   dureza, y elige el de menor costo ponderado por durabilidad;
6. evita las parejas con riesgo alto de galling (obturador–jaula,
   obturador–asiento, obturador/vástago–guía);
7. evalúa la elección manual del usuario y genera las alertas.

Es una preselección de ingeniería conservadora: la aprobación final del
material corresponde al fabricante de la válvula y al especialista en
corrosión del proyecto, con certificados y normas vigentes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import asme_b16_34 as B
from . import empaquetaduras as EM
from . import materiales as MT
from . import quimica as Q
from .modelos import Alerta, Severidad, _n

# ---------------------------------------------------------------------------
# Opciones de los desplegables
# ---------------------------------------------------------------------------
INDUSTRIAS = ["O&G Upstream", "O&G Midstream (transporte)", "Refinería", "Petroquímica", "Generación eléctrica",
              "Química", "Minería", "Tratamiento de agua", "Pulpa y papel", "Alimentos / farmacéutica", "Otra"]
FAMILIAS_FLUIDO = ["Agua", "Vapor", "Gas", "Hidrocarburo líquido", "Hidrocarburo gaseoso", "Ácido", "Alcalino",
                   "Solvente", "Salmuera", "Mezcla multifásica", "Slurry", "Otro"]
FLUIDOS = ["Agua desmineralizada", "Agua industrial", "Agua de mar", "Agua producida", "Condensado",
           "Vapor saturado", "Vapor sobrecalentado", "Gas natural", "Gas combustible", "Crudo", "Diésel",
           "Hidrógeno", "Nitrógeno", "Aire", "Oxígeno", "Dióxido de carbono", "Amoníaco", "Mezcla / otro", "Otro"]
FASES = ["Líquido", "Gas", "Vapor", "Gas-líquido", "Líquido-sólido", "Multifásico", "Desconocida"]
COMPOSICION = ["Confirmada por análisis", "Confirmada por simulación", "Parcialmente conocida",
               "Sin contaminantes conocidos", "Desconocida"]
ACUOSA = ["Sí", "No", "Intermitente", "Desconocida"]
REGIMEN = ["Continuo", "Intermitente", "Batch", "Emergencia", "Desconocido"]
MEDIO = ["Sin mecanismo confirmado", "Servicio corrosivo", "Servicio agrio", "Servicio erosivo",
         "Servicio mixto", "Por evaluar"]
NORMA_AGRIO = ["Por determinar", "No aplica (confirmado)", "ISO 15156 / MR0175", "ISO 17945 / MR0103", "Otra"]
SOLIDOS = ["Ausentes confirmados", "Trazas", "Presentes", "Desconocido"]
MODOS = ["AUTOMÁTICO", "MANUAL"]
UMBRAL_AGRIO_KPA = 0.3       # ISO 15156-2: pH₂S ≥ 0,3 kPa (0,05 psia) con agua libre

# Agentes que el fluido aporta por sí mismo (si el usuario no los informa)
IMPLICITOS = {
    "Agua de mar": [("cloruros", "mg/L", 19400, "Acuosa"), ("o2", "mg/L", 8, "Acuosa")],
    "Agua industrial": [("cloruros", "mg/L", 250, "Acuosa"), ("o2", "mg/L", 8, "Acuosa")],
    "Agua producida": [("cloruros", "mg/L", 60000, "Acuosa")],
    "Agua potable": [("cloruros", "mg/L", 100, "Acuosa"), ("o2", "mg/L", 8, "Acuosa")],
    "Sulfuro de hidrógeno": [("h2s", "% molar", 100, "Gas / vapor")],
    "Cloro": [("cl2", "% molar", 100, "Gas / vapor")],
    "Hidrógeno": [("h2", "% molar", 100, "Gas / vapor")],
    "Oxígeno": [("o2", "% molar", 100, "Gas / vapor")],
    "Dióxido de carbono": [("co2", "% molar", 100, "Gas / vapor")],
    "Amoníaco": [("nh3", "% p/p", 100, "Gas / vapor")],
}
SECO_POR_DEFECTO = {"Vapor sobrecalentado", "Nitrógeno", "Aire", "Oxígeno", "Hidrógeno", "Gas combustible",
                    "Diésel", "Diésel / destilados", "Gasolina / naftas", "Aceite térmico / lubricante",
                    "Argón", "Helio", "R134a"}
# Calidades de agua sin sales ni ácidos: declarar esos agentes las contradice
AGUAS_PURAS = {"Agua desmineralizada", "Agua de alimentación de caldera", "Condensado"}


@dataclass
class ServicioMateriales:
    industria: str = "Otra"
    familia_fluido: str = "Agua"
    fluido: str = "Agua industrial"
    fase: str = "Líquido"
    composicion: str = "Parcialmente conocida"
    acuosa: str = "Sí"
    regimen: str = "Continuo"
    medio: str = "Por evaluar"
    norma_agrio: str = "Por determinar"
    solidos: str = "Ausentes confirmados"
    pH: float | None = None
    agentes: list[Q.AgenteServicio] = field(default_factory=list)
    modos: dict[str, str] = field(default_factory=dict)       # componente -> AUTOMÁTICO / MANUAL
    manual: dict[str, str] = field(default_factory=dict)      # componente -> clave de material


@dataclass
class Contexto:
    """Datos del cálculo que necesita la selección (en °C, bar g, kPa abs)."""
    T_max_C: float
    T_min_C: float
    P_barg: float
    P_kPa: float                     # presión absoluta máxima de operación (presiones parciales)
    clase: int | None
    bridada: bool
    rotativa: bool
    jaula: bool
    liner: bool
    compresible: bool
    tipo: str
    dP_max_kPa: float
    severidad_cav: str               # ninguna, incipiente, moderada, severa, extrema
    flashing: bool
    blando: bool                     # el cierre requiere asiento blando
    SG: float = 1.0
    casos_cav: list[tuple[str, str, float, float, float]] = field(default_factory=list)  # caso, sev, Kapp, Kc, FL²
    P_min_kPa: float = 101.325       # presión absoluta mínima (vacío en la empaquetadura)


@dataclass
class Evaluacion:
    material: MT.Material
    ok: bool
    puntaje: float
    motivos: list[str]               # por qué se descarta (si no ok) o penalidades
    quimica: list[Q.Compatibilidad]
    nivel_quimico: str
    rating: float | None = None
    clase_min: int | None = None


@dataclass
class ResultadoComponente:
    clave: str
    nombre: str
    aplica: bool = True
    modo: str = "AUTOMÁTICO"
    recomendado: MT.Material | None = None
    elegido: MT.Material | None = None
    inserto: MT.Material | None = None
    dureza_req_HRC: float | None = None
    justificacion: list[str] = field(default_factory=list)
    alternativas: list[tuple[MT.Material, str]] = field(default_factory=list)
    descartados: list[tuple[MT.Material, str]] = field(default_factory=list)
    alertas: list[Alerta] = field(default_factory=list)
    eval_elegido: Evaluacion | None = None

    @property
    def texto(self) -> str:
        if not self.aplica:
            return "No aplica"
        if self.elegido is None:
            return "Sin material apto"
        t = self.elegido.nombre
        if self.inserto:
            t += f" con inserto de {self.inserto.nombre.split(' (')[0]}"
        return t

    @property
    def corto(self) -> str:
        if not self.aplica:
            return "No aplica"
        if self.elegido is None:
            return "Sin material apto"
        m = self.elegido
        t = m.nombre.split(" — ")[0] if " — " in m.nombre else m.nombre
        return t + (f" + {self.inserto.clave}" if self.inserto else "")


@dataclass
class Galling:
    par: str
    a: str
    b: str
    nivel: str          # BAJO, MEDIO, ALTO
    motivo: str
    remedio: str


@dataclass
class Mecanismo:
    codigo: str
    nombre: str
    estado: str         # Detectado, Potencial
    motivo: str


@dataclass
class ResultadoMateriales:
    servicio: ServicioMateriales
    ctx: Contexto
    componentes: dict[str, ResultadoComponente]
    agentes: list[Q.AgenteNormalizado]
    mecanismos: list[Mecanismo]
    agrio: bool
    pH2S_kPa: float | None
    norma: str
    norma_motivo: str
    medio_detectado: str
    dureza_req: dict[str, float]
    dureza_motivo: str
    galling: list[Galling]
    alertas: list[Alerta]
    notas: list[str]
    empaquetadura: "EM.ResultadoEmpaquetadura | None" = None

    @property
    def cuerpo(self) -> MT.Material | None:
        return self.componentes["cuerpo"].elegido

    @property
    def grupo_cuerpo(self) -> str | None:
        m = self.cuerpo
        return m.grupo if m else None

    def todas_las_alertas(self) -> list[Alerta]:
        out = list(self.alertas)
        for c in self.componentes.values():
            out += c.alertas
        return sorted(out, key=lambda a: -a.severidad)


# ---------------------------------------------------------------------------
# Cavitación y dureza
# ---------------------------------------------------------------------------
SEVERIDADES = ["ninguna", "incipiente", "moderada", "severa", "extrema"]
DUREZA_CAV = {"ninguna": None, "incipiente": 25.0, "moderada": 35.0, "severa": 40.0, "extrema": 55.0}
# Resistencia relativa mínima a la cavitación (0–10) de las superficies de trabajo
RANGO_CAV = {"ninguna": 0, "incipiente": 3, "moderada": 5, "severa": 7, "extrema": 8}
TEXTO_CAV = {
    "incipiente": "cavitación incipiente (xFz ≤ Kapp < Kc): burbujas aisladas, ruido leve",
    "moderada": "cavitación moderada (Kc ≤ Kapp < (Kc + FL²)/2): implosiones frecuentes cerca del asiento",
    "severa": "cavitación severa ((Kc + FL²)/2 ≤ Kapp < FL²): daño rápido de superficies blandas",
    "extrema": "cavitación extrema / flujo bloqueado (Kapp ≥ FL²): erosión intensa, ruido y vibración",
}


def severidad_cavitacion(s: dict) -> str:
    """Grado de cavitación de un caso de líquido a partir de las salidas del cálculo."""
    cond = (s.get("condicion") or "").lower()
    if "flashing" in cond:
        return "flashing"
    Kapp, Kc, FL, xF = s.get("Kapp"), s.get("Kc"), s.get("FL"), s.get("xFzp1")
    if Kapp is None or FL is None:
        return "ninguna"
    FL2 = FL * FL
    if Kapp >= FL2 or "bloqueo" in cond:
        return "extrema"
    if Kc is not None and Kapp >= Kc:
        return "severa" if Kapp >= (Kc + FL2) / 2 else "moderada"
    if xF is not None and Kapp >= xF:
        return "incipiente"
    if "incipiente" in cond:
        return "incipiente"
    if "cavitación" in cond:
        return "moderada"
    return "ninguna"


def requisitos_desgaste(ctx: Contexto, sv: ServicioMateriales) -> dict[str, tuple[int, int]]:
    """Resistencia relativa mínima (cavitación, erosión) por componente de internos."""
    out: dict[str, tuple[int, int]] = {}

    def subir(comps, cav, ero):
        for c in comps:
            a, b = out.get(c, (0, 0))
            out[c] = (max(a, cav), max(b, ero))

    rc = RANGO_CAV.get(ctx.severidad_cav, 0)
    if rc:
        subir(("obturador", "asiento", "jaula"), rc, 0)
    if ctx.flashing:
        subir(("obturador", "asiento"), 0, 8)
        subir(("jaula",), 0, 5)
    if sv.familia_fluido == "Slurry":
        subir(("obturador", "asiento", "jaula"), 0, 10)
    elif sv.solidos == "Presentes":
        subir(("obturador", "asiento", "jaula"), 0, 8)
    return out


def requisitos_dureza(ctx: Contexto, sv: ServicioMateriales) -> tuple[dict[str, float], list[str]]:
    """Dureza mínima [HRC] de obturador, asiento y jaula, con su justificación."""
    req: dict[str, float] = {}
    porque: list[str] = []

    def subir(comps, hrc, motivo):
        for c in comps:
            if hrc > req.get(c, 0):
                req[c] = hrc
        porque.append(motivo)

    trim = ("obturador", "asiento", "jaula")
    hrc = DUREZA_CAV.get(ctx.severidad_cav)
    if hrc:
        subir(trim, hrc, f"{TEXTO_CAV[ctx.severidad_cav].capitalize()}: superficies de obturador, asiento y "
                         f"jaula ≥ {hrc:.0f} HRC (≈ {MT.hrc_a_hb(hrc):.0f} HB)"
              + (". Además se requiere trim multietapa." if ctx.severidad_cav == "extrema" else "."))
    if ctx.flashing:
        h = 55.0 if ctx.dP_max_kPa > 2000 else 40.0
        subir(("obturador", "asiento"), h, f"Flashing (P2 < Pv): la mezcla líquido-vapor a alta velocidad erosiona "
                                           f"el obturador y el asiento; ≥ {h:.0f} HRC"
              + (" (carburo de tungsteno por la ΔP alta)." if h >= 55 else "."))
        subir(("jaula",), 38.0, "Flashing: jaula endurecida ≥ 38 HRC.")
    if sv.solidos == "Trazas":
        subir(("obturador", "asiento"), 35.0, "Sólidos en trazas: superficies de cierre ≥ 35 HRC.")
    elif sv.solidos == "Presentes" or sv.familia_fluido == "Slurry":
        subir(trim, 55.0 if sv.familia_fluido == "Slurry" else 45.0,
              "Sólidos abrasivos presentes: superficies de trabajo ≥ "
              f"{55 if sv.familia_fluido == 'Slurry' else 45} HRC (carburo, cerámica o recargue duro).")
    if ctx.dP_max_kPa > 2000:
        subir(("obturador", "asiento"), 38.0, f"Caída de presión {_n(ctx.dP_max_kPa / 100, 1)} bar > 20 bar: "
                                              "obturador y asiento endurecidos ≥ 38 HRC.")
    elif ctx.dP_max_kPa > 1000:
        subir(("asiento",), 38.0, f"Caída de presión {_n(ctx.dP_max_kPa / 100, 1)} bar > 10 bar: asiento con "
                                  "recargue duro (≥ 38 HRC).")
    if ctx.compresible and ctx.dP_max_kPa > 1000:
        subir(("asiento",), 38.0, "Gas o vapor con ΔP > 10 bar: asiento con recargue duro contra el wire-drawing.")
    return req, porque


# ---------------------------------------------------------------------------
# Galling
# ---------------------------------------------------------------------------
_SUBE = {"BAJO": "MEDIO", "MEDIO": "ALTO", "ALTO": "ALTO"}
BLANDOS_GALL = {"aus", "ni", "dup", "ti"}


def _unir(motivos) -> str:
    """Une motivos como frases, cada una terminada en punto."""
    return " ".join(x.strip().rstrip(".") + "." for x in motivos if x.strip())


def riesgo_galling(a: MT.Material, b: MT.Material, T_C: float) -> tuple[str, str, str]:
    """Riesgo de galling de una pareja deslizante: (nivel, motivo, remedio)."""
    ga, gb = a.galling, b.galling
    ha, hb = a.HRC_efectiva, b.HRC_efectiva
    rem = ("Usar una pareja disímil: recargue de Stellite 6 en una de las superficies, buje de Nitronic 60, "
           "endurecer una de las partes a ≥ 38 HRC o lograr una diferencia de dureza ≥ 10 HRC; verificar con "
           "ensayo ASTM G98.")
    if "polimero" in (ga, gb):
        nivel, mot = "BAJO", "Una de las superficies es no metálica."
    elif {ga, gb} & {"cocr", "wc", "ceram"}:
        nivel, mot = "BAJO", "Superficie de recargue Co-Cr, carburo o cerámica: resistentes a la adhesión."
    elif "n60" in (ga, gb):
        nivel, mot = ("MEDIO", "Nitronic 60 contra sí mismo.") if ga == gb else \
            ("BAJO", "Nitronic 60 (S21800) está formulado contra el galling, incluso frente a austeníticos.")
    elif "cu" in (ga, gb):
        nivel, mot = ("MEDIO", "Bronce contra bronce.") if ga == gb else \
            ("BAJO", "Bronce contra acero: pareja disímil clásica de bajo galling.")
    elif "enc" in (ga, gb):
        nivel, mot = ("MEDIO", "Níquel químico en ambas superficies.") if ga == gb else \
            ("BAJO", "Recubrimiento de níquel químico (≈ 50 HRC) en una superficie.")
    elif min(ha, hb) >= 38:
        nivel, mot = "BAJO", f"Ambas superficies endurecidas ({ha:.0f} y {hb:.0f} HRC ≥ 38)."
    elif abs(ha - hb) >= 10 and max(ha, hb) >= 30:
        nivel, mot = "BAJO", f"Diferencia de dureza ≥ 10 HRC ({a.dureza_txt} frente a {b.dureza_txt})."
    elif ga in BLANDOS_GALL and gb in BLANDOS_GALL:
        nivel = "ALTO"
        mot = ("Pareja idéntica de aleación austenítica / níquel / dúplex / titanio sin endurecer: alta "
               "tendencia a la soldadura en frío." if ga == gb else
               "Aleaciones austeníticas, de níquel o dúplex blandas en contacto: tendencia alta a la soldadura en frío.")
    elif ga == gb == "ph" and abs(ha - hb) < 5:
        nivel, mot = "ALTO", "17-4PH contra 17-4PH en la misma condición de tratamiento."
    elif ga == gb and abs(ha - hb) < 5:
        nivel, mot = "MEDIO", "Mismo material y dureza similar."
    else:
        nivel, mot = "MEDIO", "Pareja metálica disímil sin endurecimiento suficiente."
    if T_C > 316 and nivel != "ALTO":
        nivel = _SUBE[nivel]
        mot += " La temperatura (> 316 °C) reduce la dureza y la película de óxido protectora."
    return nivel, mot, ("" if nivel == "BAJO" else rem)


# ---------------------------------------------------------------------------
# Servicio agrio
# ---------------------------------------------------------------------------
def _nace(m: MT.Material, norma: str) -> MT.Nace:
    return m.iso17945 if norma.startswith("ISO 17945") else m.iso15156


def evaluar_agrio(m: MT.Material, norma: str, pH2S: float | None, T_C: float, pH: float | None,
                  azufre: bool) -> str | None:
    """None si cumple; texto del incumplimiento si no."""
    n = _nace(m, norma)
    if m.blando:
        return None
    if n.estado == "no":
        return f"No aceptable según {norma}" + (f": {n.nota}" if n.nota else ".")
    if n.estado == "sin_datos":
        return f"Sin calificación conocida según {norma}."
    if n.estado == "condicional":
        if n.pH2S_max_kPa is not None and pH2S is not None and pH2S > n.pH2S_max_kPa:
            return f"pH₂S {_n(pH2S, 2)} kPa supera el límite ambiental del material ({_n(n.pH2S_max_kPa, 1)} kPa)."
        if n.T_max_C is not None and T_C > n.T_max_C:
            return f"Temperatura {_n(T_C, 0)} °C supera el límite ambiental ({_n(n.T_max_C, 0)} °C) en servicio agrio."
        if n.pH_min is not None and pH is not None and pH < n.pH_min:
            return f"pH {_n(pH, 1)} menor que el mínimo admitido ({_n(n.pH_min, 1)})."
    if azufre and not n.azufre:
        return "No admite azufre elemental en servicio agrio."
    return None


# ---------------------------------------------------------------------------
# Evaluación de un material para un componente
# ---------------------------------------------------------------------------
F_QUIM_CUERPO = {"A": 1.0, "B": 1.15, "C": 2.5, "?": 1.6}
F_QUIM_TRIM = {"A": 1.0, "B": 1.5, "C": 3.0, "?": 1.8}


def evaluar_material(m: MT.Material, comp: str, ctx: Contexto, sv: ServicioMateriales,
                     agentes: list[Q.AgenteNormalizado], acuoso: bool, agrio: bool, norma: str,
                     pH2S: float | None, azufre: bool, hrc_req: float | None,
                     desgaste: tuple[int, int] = (0, 0)) -> Evaluacion:
    motivos: list[str] = []
    ok = True
    # temperatura
    if ctx.T_max_C > m.T_max_C:
        ok = False
        motivos.append(f"Temperatura máxima {_n(ctx.T_max_C, 0)} °C > límite del material {_n(m.T_max_C, 0)} °C.")
    if ctx.T_min_C < m.T_min_C:
        ok = False
        motivos.append(f"Temperatura mínima {_n(ctx.T_min_C, 0)} °C < límite del material {_n(m.T_min_C, 0)} °C "
                       "(fragilidad o pérdida de propiedades).")
    # química
    comps = []
    if not (comp == "cuerpo" and ctx.liner):
        comps = [Q.evaluar(m, n, ctx.T_max_C, acuoso) for n in agentes]
    nivel = Q._peor(*(c.nivel for c in comps)) if comps else "A"
    if any(c.nivel == "?" for c in comps) and nivel in "AB":
        nivel = "?"
    if nivel == "D":
        ok = False
        malos = [c.detalle for c in comps if c.nivel == "D"]
        motivos.append("Incompatible químicamente: " + "; ".join(malos))
    # servicio agrio
    if agrio:
        fallo = evaluar_agrio(m, norma, pH2S, ctx.T_max_C, sv.pH, azufre)
        if fallo:
            ok = False
            motivos.append(fallo)
    # dureza
    if hrc_req and not m.blando and m.HRC_efectiva < hrc_req - 0.5:
        ok = False
        motivos.append(f"Dureza {m.dureza_txt} menor que la requerida ({hrc_req:.0f} HRC).")
    cav_min, ero_min = desgaste
    if not m.blando and m.cavitacion < cav_min:
        ok = False
        motivos.append(f"Resistencia a la cavitación {m.cavitacion}/10 menor que la requerida ({cav_min}/10).")
    if not m.blando and m.erosion < ero_min:
        ok = False
        motivos.append(f"Resistencia a la erosión {m.erosion}/10 menor que la requerida ({ero_min}/10).")
    # grafitización: acero al carbono en servicio prolongado por encima de 425 °C
    if comp in ("cuerpo", "bonete") and m.grupo in ("1.1", "1.2", "1.3", "1.4") and ctx.T_max_C > 425 \
            and sv.regimen != "Emergencia":
        ok = False
        motivos.append(f"Acero al carbono a {_n(ctx.T_max_C, 0)} °C (> 425 °C) en servicio prolongado: riesgo de "
                       "grafitización (usar Cr-Mo WC6 / WC9).")
    # presión-temperatura
    rating = clase_min = None
    if comp in ("cuerpo", "bonete") and m.grupo:
        if ctx.bridada and ctx.T_max_C > B.T_BRIDADAS_C:
            ok = False
            motivos.append(f"Válvula bridada: ASME B16.34 termina el rating a {B.T_BRIDADAS_C} °C; la temperatura "
                           f"es {_n(ctx.T_max_C, 0)} °C (usar extremos soldados).")
        clase_min = B.clase_minima(m.grupo, ctx.P_barg, ctx.T_max_C)
        if ctx.clase:
            rating = B.rating(m.grupo, ctx.clase, ctx.T_max_C)
            if rating is None:
                ok = False
                motivos.append(f"Temperatura fuera de la tabla del grupo {m.grupo}.")
            elif rating < ctx.P_barg:
                ok = False
                motivos.append(f"CL{ctx.clase} admite {_n(rating, 1)} bar g a {_n(ctx.T_max_C, 0)} °C (grupo {m.grupo}) "
                               f"y el diseño es {_n(ctx.P_barg, 1)} bar g"
                               + (f": requiere CL{clase_min}." if clase_min else "."))
        elif clase_min is None:
            ok = False
            motivos.append("Ninguna clase estándar alcanza la presión de diseño.")
    # erosión del cuerpo
    f_ero = 1.0
    if comp == "cuerpo" and m.erosion < 4:
        if ctx.flashing:
            f_ero = 2.5
            motivos.append("El flashing erosiona el cuerpo aguas abajo del asiento: el acero al carbono es poco "
                           "resistente (preferir Cr-Mo WC9/C5 o inoxidable).")
        elif sv.solidos == "Presentes" or sv.familia_fluido == "Slurry":
            f_ero = 2.0
            motivos.append("Sólidos abrasivos: resistencia a la erosión del cuerpo limitada.")
        elif ctx.severidad_cav in ("severa", "extrema"):
            f_ero = 1.3
            motivos.append("Cavitación severa: las burbujas pueden colapsar aguas abajo, sobre el cuerpo.")
    # puntaje: costo ponderado por durabilidad química y mecánica
    fq = (F_QUIM_CUERPO if comp in ("cuerpo", "bonete") else F_QUIM_TRIM).get(nivel, 1.0)
    puntaje = m.costo * fq * f_ero
    if comp == "vastago":
        alta = ctx.dP_max_kPa > 1000 or (ctx.clase or 0) >= 600
        if alta and (m.Rp_MPa or 0) < 400:
            puntaje *= 1.5
            motivos.append("Límite de fluencia bajo para el empuje del actuador con esta ΔP / clase.")
    if comp in ("obturador", "asiento", "jaula") and hrc_req:
        puntaje *= 1 + max(0.0, (6 - m.cavitacion)) * 0.04
    if nivel == "C":
        motivos.append("Compatibilidad química regular (C): vida reducida; solo si no hay alternativa.")
    if nivel == "?":
        motivos.append("Sin datos de compatibilidad para algún agente: confirmar con el fabricante.")
    return Evaluacion(m, ok, puntaje, motivos, comps, nivel, rating, clase_min)


# ---------------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------------
def _agentes(sv: ServicioMateriales, ctx: Contexto) -> tuple[list[Q.AgenteNormalizado], list[str]]:
    notas = []
    filas = [a for a in sv.agentes if a.clave in Q.AGENTES]
    presentes = {a.clave for a in filas}
    for clave, u, v, fase in IMPLICITOS.get(sv.fluido, []):
        if clave not in presentes:
            filas.append(Q.AgenteServicio(clave, u, v, fase))
            notas.append(f"{sv.fluido}: se agrega {Q.AGENTES[clave].nombre.lower()} típico "
                         f"({_n(v, 0)} {u}) porque no se informó.")
    if sv.familia_fluido == "Salmuera" and not presentes & {"cloruros", "nacl", "cacl2", "mgcl2"}:
        filas.append(Q.AgenteServicio("cloruros", "mg/L", 140000, "Acuosa"))
        notas.append("Salmuera sin cloruros informados: se evalúa con 140.000 mg/L de Cl⁻ (≈ 20 % de NaCl, la "
                     "misma salinidad con la que se corrigen sus propiedades en la solapa 2).")
    norm = [Q.normalizar(a, ctx.P_kPa, ctx.SG) for a in filas]
    return norm, notas


def _acuoso(sv: ServicioMateriales) -> bool:
    if sv.acuosa == "No":
        return False
    if sv.acuosa == "Desconocida" and sv.fluido in SECO_POR_DEFECTO:
        return False
    return True


def _coherencia(sv: ServicioMateriales, agentes: list[Q.AgenteNormalizado], acuoso: bool) -> list[Alerta]:
    """Contradicciones entre el fluido definido en la solapa 2 y los datos complementarios de materiales."""
    out = []
    ref = "Fluido definido en 2-Cálculos Válvula"
    if sv.acuosa == "No":
        acuosos = [n.agente.nombre for n in agentes if n.entrada.fase == "Acuosa"]
        if acuosos:
            out.append(Alerta("mat_agua_libre_contradiccion", Severidad.ADVERTENCIA,
                              "Agentes en fase acuosa sin agua libre",
                              f"En 2-Cálculos Válvula se indicó que no hay agua libre, pero {', '.join(acuosos)} se "
                              "informaron disueltos en fase acuosa. Se evalúa con agua presente (conservador).",
                              remedios=["Si hay agua libre o arrastre de condensado, indicar «Sí» o «Intermitente» en "
                                        "«Agua libre» (solapa 2).",
                                        "Si el servicio es seco, informar los agentes en fase «Gas / vapor»."],
                              referencia=ref))
        if sv.pH is not None:
            out.append(Alerta("mat_pH_sin_agua", Severidad.INFO, "pH sin fase acuosa",
                              "El pH solo tiene sentido con agua libre; con servicio seco no se usa.",
                              referencia=ref))
    if sv.fluido in AGUAS_PURAS:
        sucios = [n.agente.nombre for n in agentes if n.agente.familia in ("Halogenuros / sales", "Ácidos inorgánicos")
                  and (n.valor or 0) > (1 if n.agente.base == "mgL" else 0.001) and not n.supuesto]
        if sucios:
            out.append(Alerta("mat_calidad_agua", Severidad.ADVERTENCIA, "Calidad del agua contradictoria",
                              f"La calidad declarada es «{sv.fluido}» (sin sales ni ácidos), pero se informaron "
                              f"{', '.join(sucios)}. La selección usa los agentes informados.",
                              remedios=["Corregir la calidad / variante del fluido en la solapa 2 (por ejemplo, agua "
                                        "industrial, de mar o producida) o revisar las concentraciones."],
                              referencia=ref))
    if sv.pH is not None and acuoso:
        if sv.familia_fluido == "Ácido" and sv.pH > 7:
            out.append(Alerta("mat_pH_familia", Severidad.ADVERTENCIA, "pH alcalino en un ácido",
                              f"El fluido es un ácido y el pH informado es {_n(sv.pH, 1)} (> 7).",
                              remedios=["Revisar el pH o la variante del fluido."], referencia=ref))
        elif sv.familia_fluido == "Alcalino" and sv.pH < 7:
            out.append(Alerta("mat_pH_familia", Severidad.ADVERTENCIA, "pH ácido en un álcali",
                              f"El fluido es alcalino y el pH informado es {_n(sv.pH, 1)} (< 7).",
                              remedios=["Revisar el pH o la variante del fluido."], referencia=ref))
    if sv.composicion == "Sin contaminantes conocidos" and any(not n.supuesto for n in agentes if n.entrada in sv.agentes):
        out.append(Alerta("mat_composicion_contradiccion", Severidad.INFO, "Contaminantes informados",
                          "El estado de la composición dice «Sin contaminantes conocidos», pero hay agentes cargados. "
                          "Se evalúan los agentes informados.",
                          remedios=["Cambiar el estado de la composición a «Confirmada por análisis» o «Parcialmente "
                                    "conocida», o quitar los agentes."]))
    if sv.familia_fluido == "Slurry" and sv.solidos == "Ausentes confirmados":
        out.append(Alerta("mat_slurry_solidos", Severidad.ADVERTENCIA, "Slurry sin sólidos",
                          "El fluido es un slurry y en materiales se declararon sólidos ausentes. Se evalúa con "
                          "sólidos presentes.", remedios=["Indicar «Presentes» en «Sólidos»."], referencia=ref))
    return out


def completar_desde_calculo(sv: ServicioMateriales, dim, salidas, ctx: Contexto) -> ServicioMateriales:
    """Toma el fluido de la solapa 2: familia, fluido, fase y fase acuosa (la solapa 3 no los define)."""
    from dataclasses import replace
    from . import fluido_servicio as FS
    var = getattr(dim, "variante", "") or ""
    agua = getattr(dim, "agua_libre", "") or FS.agua_libre_sugerida(dim.tipo, dim.fluido, var)
    fm = FS.para_materiales(dim.tipo, dim.fluido, var, agua, salidas, ctx.flashing)
    solidos = "Presentes" if fm.familia == "Slurry" and sv.solidos != "Presentes" and \
        sv.solidos != "Ausentes confirmados" else sv.solidos
    return replace(sv, familia_fluido=fm.familia, fluido=fm.fluido, fase=fm.fase, acuosa=fm.acuosa, solidos=solidos)


def _norma(sv: ServicioMateriales, agrio: bool) -> tuple[str, str]:
    if sv.norma_agrio in ("ISO 15156 / MR0175", "ISO 17945 / MR0103"):
        return sv.norma_agrio, "Elegida por el usuario."
    if sv.industria in ("Refinería", "Petroquímica"):
        return "ISO 17945 / MR0103", ("Refino y petroquímica: la norma de servicio agrio es ISO 17945 / NACE "
                                      "MR0103 (ambientes de refinería).")
    if sv.industria in ("O&G Upstream", "O&G Midstream (transporte)"):
        return "ISO 15156 / MR0175", ("Producción de petróleo y gas: la norma de servicio agrio es ISO 15156 / "
                                      "NACE MR0175.")
    return "ISO 15156 / MR0175", ("Sin industria de refino declarada: se aplica ISO 15156 / MR0175, que es la "
                                  "más restrictiva.")


def _mecanismos(sv, ctx, agentes, acuoso, agrio, pH2S) -> list[Mecanismo]:
    out: list[Mecanismo] = []
    claves = {n.agente.clave: n for n in agentes}

    def add(cod, nom, est, mot):
        out.append(Mecanismo(cod, nom, est, mot))

    def val(k):
        n = claves.get(k)
        return None if n is None else n.valor

    acidos = [k for k in ("hcl", "h2so4", "hno3", "h3po4", "hclo4", "acetico", "formico", "oxalico", "citrico",
                          "lactico") if k in claves]
    if acidos and acuoso:
        add("M01", "Corrosión general por ácidos", "Detectado",
            "Ácidos presentes: " + ", ".join(Q.AGENTES[k].formula for k in acidos) + ".")
    cl = sum((val(k) or 0) * (Q.AGENTES[k].alias[1] if Q.AGENTES[k].alias else 1)
             for k in ("cloruros", "bromuros", "nacl", "cacl2", "mgcl2") if k in claves)
    if cl > 0 and acuoso:
        add("M02", "Corrosión localizada por cloruros (picaduras / rendijas)", "Detectado" if cl >= 200 else "Potencial",
            f"Cloruros equivalentes ≈ {_n(cl, 0)} mg/L.")
        if ctx.T_max_C > 60 and cl >= 50:
            add("M03", "Corrosión bajo tensión por cloruros (Cl-SCC)", "Detectado",
                f"Cl⁻ ≈ {_n(cl, 0)} mg/L y {_n(ctx.T_max_C, 0)} °C > 60 °C: los austeníticos 304/316 son susceptibles.")
    if agrio:
        add("M04", "Agrietamiento por H₂S (SSC)", "Detectado", f"pH₂S = {_n(pH2S, 2)} kPa ≥ 0,3 kPa con agua libre.")
        add("M05", "HIC / SOHIC", "Potencial", "H₂S húmedo: relevante en chapas y tubos laminados; las fundiciones "
                                                "no requieren ensayo HIC.")
    elif pH2S and pH2S > 0:
        add("M04", "Agrietamiento por H₂S (SSC)", "Potencial",
            f"pH₂S = {_n(pH2S, 3)} kPa" + (" sin agua libre." if not acuoso else " < 0,3 kPa."))
    if "co2" in claves and acuoso:
        p = claves["co2"].kPa or claves["co2"].valor or 0
        add("M06", "Corrosión por CO₂ (sweet)", "Detectado" if p >= 20 else "Potencial",
            f"pCO₂ ≈ {_n(p, 1)} kPa con agua: " + ("severa (> 200 kPa)." if p > 200 else
                                                   "moderada (20–200 kPa)." if p >= 20 else "baja (< 20 kPa)."))
    ox = [k for k in ("hno3", "cl2", "hipoclorito", "h2o2", "fecl3", "hclo4") if k in claves]
    if ox:
        add("M07", "Ataque por oxidantes", "Detectado", "Oxidantes: " + ", ".join(Q.AGENTES[k].formula for k in ox) + ".")
    alc = [k for k in ("naoh", "koh") if k in claves]
    if alc:
        add("M08", "Corrosión / agrietamiento cáustico", "Detectado" if ctx.T_max_C > 50 else "Potencial",
            "Álcalis presentes; el agrietamiento cáustico del acero al carbono aparece por encima de ~50–80 °C "
            "según la concentración (NACE SP0403).")
    if {"hf", "fluoruros"} & set(claves):
        add("M09", "Ataque por HF / fluoruros", "Detectado", "Requiere aleación de Ni-Cu (Monel) o acero al "
                                                              "carbono en HF anhidro.")
    if {"azufre", "sulfuros", "polisulfuros"} & set(claves):
        add("M10", "Ataque por azufre / sulfuros", "Detectado", "Azufre elemental o sulfuros en el fluido.")
    if sv.solidos in ("Presentes", "Trazas") or sv.familia_fluido == "Slurry":
        add("M14", "Erosión por partículas", "Detectado" if sv.solidos == "Presentes" else "Potencial",
            f"Sólidos: {sv.solidos.lower()}.")
    if ctx.severidad_cav not in ("ninguna",):
        add("M16", "Cavitación", "Detectado", TEXTO_CAV[ctx.severidad_cav].capitalize() + " (solapa 2).")
    if ctx.flashing:
        add("M17", "Flashing", "Detectado", "P2 < Pv en al menos un caso (solapa 2).")
    add("M19", "Galling / soldadura en frío", "Potencial", "Contacto deslizante obturador–jaula, obturador–asiento "
                                                            "y vástago–guía (se evalúa cada pareja).")
    if ctx.T_max_C > 425:
        add("M21", "Grafitización / creep a alta temperatura", "Detectado",
            f"{_n(ctx.T_max_C, 0)} °C: aceros al carbono no recomendados para uso prolongado (> 425 °C).")
    if "h2" in claves:
        p = claves["h2"].kPa or 0
        if p >= 690 and ctx.T_max_C > 200:
            add("M22", "Ataque por hidrógeno a alta temperatura (HTHA)", "Detectado",
                f"pH₂ ≈ {_n(p / 100, 1)} bar y {_n(ctx.T_max_C, 0)} °C: verificar con las curvas de Nelson (API RP 941).")
        else:
            add("M22", "Fragilización por hidrógeno", "Potencial", "Evitar internos de dureza muy alta (> 38 HRC) "
                                                                    "en hidrógeno a presión.")
    if "nh3" in claves and not acuoso:
        add("M24", "SCC del acero al carbono en amoníaco anhidro", "Potencial",
            "El amoníaco anhidro con aire y sin agua (< 0,2 %) agrieta aceros al carbono de alta resistencia.")
    if "aminas" in claves:
        add("M25", "SCC por aminas", "Potencial" if ctx.T_max_C < 60 else "Detectado",
            "Acero al carbono en aminas: PWHT obligatorio por encima de ~60 °C (API RP 945).")
    if "nitratos" in claves and ctx.T_max_C > 60:
        add("M26", "SCC por nitratos", "Potencial", "Nitratos calientes concentrados agrietan aceros al carbono.")
    if "o2" in claves and sv.fluido == "Oxígeno":
        add("M27", "Ignición en servicio de oxígeno", "Detectado",
            "Oxígeno gaseoso: limpieza para oxígeno y materiales resistentes a la ignición (ASTM G88/G94, "
            "CGA G-4.4).")
    return out


def _medio_detectado(mecs: list[Mecanismo]) -> str:
    cods = {m.codigo for m in mecs if m.estado == "Detectado"}
    tipos = []
    if cods & {"M01", "M02", "M03", "M06", "M07", "M08", "M09", "M10"}:
        tipos.append("corrosivo")
    if cods & {"M04"}:
        tipos.append("agrio")
    if cods & {"M14", "M16", "M17"}:
        tipos.append("erosivo")
    if not tipos:
        return "Sin mecanismo confirmado"
    if len(tipos) > 1:
        return "Servicio mixto (" + ", ".join(tipos) + ")"
    return "Servicio " + tipos[0]


def seleccionar(sv: ServicioMateriales, ctx: Contexto) -> ResultadoMateriales:
    alertas: list[Alerta] = []
    agentes, notas = _agentes(sv, ctx)
    acuoso = _acuoso(sv)
    # presión parcial de H₂S
    pH2S = None
    for n in agentes:
        if n.agente.clave == "h2s":
            pH2S = (pH2S or 0) + (n.kPa if n.kPa is not None else n.valor or 0)
        elif n.agente.clave == "sulfuros" and acuoso:
            eq = (n.valor or 0) / Q.AGENTES["h2s"].henry
            pH2S = max(pH2S or 0, eq)
            notas.append(f"Sulfuros disueltos: a pH ácido equivalen a pH₂S ≈ {_n(eq, 2)} kPa (cota conservadora).")
    agrio = bool(acuoso and pH2S is not None and pH2S >= UMBRAL_AGRIO_KPA)
    if sv.medio == "Servicio agrio" and not agrio:
        agrio = True
        if pH2S is None:
            pH2S = 100.0
            notas.append("Servicio agrio declarado sin H₂S informado: se evalúa con pH₂S = 100 kPa (conservador).")
    if sv.norma_agrio in ("ISO 15156 / MR0175", "ISO 17945 / MR0103") and not agrio and (pH2S or 0) > 0:
        agrio = True
        notas.append("Norma de servicio agrio elegida por el usuario: se aplica aunque pH₂S < 0,3 kPa.")
    norma, norma_motivo = _norma(sv, agrio)
    if sv.norma_agrio == "No aplica (confirmado)" and agrio:
        alertas.append(Alerta("mat_norma_conflicto", Severidad.ADVERTENCIA, "Servicio agrio y norma «No aplica»",
                              f"Se declaró que la norma de servicio agrio no aplica, pero pH₂S = {_n(pH2S, 2)} kPa con "
                              "agua libre supera el umbral de ISO 15156 (0,3 kPa). Se aplica igualmente "
                              f"{norma} por seguridad.",
                              remedios=["Confirmar el contenido de H₂S y la presencia de agua.",
                                        "Si el servicio no es agrio, corregir la concentración informada."],
                              referencia="ISO 15156-2, 7.2.1"))
    if not agrio:
        norma, norma_motivo = "No aplica", ("pH₂S < 0,3 kPa o sin agua libre: no se requieren materiales para "
                                            "servicio agrio.") if pH2S else ("Sin H₂S informado.")
    azufre = any(n.agente.clave == "azufre" for n in agentes)
    mecs = _mecanismos(sv, ctx, agentes, acuoso, agrio, pH2S)
    medio = _medio_detectado(mecs)
    req, porque_dureza = requisitos_dureza(ctx, sv)
    desg = requisitos_desgaste(ctx, sv)

    # alertas de datos
    if sv.composicion in ("Desconocida", "Parcialmente conocida") and not sv.agentes:
        alertas.append(Alerta("mat_composicion", Severidad.ADVERTENCIA, "Composición del fluido incompleta",
                              f"Estado de la composición: {sv.composicion.lower()} y sin agentes informados. La "
                              "selección se basa solo en el fluido principal y puede no cubrir contaminantes.",
                              remedios=["Solicitar un análisis de laboratorio o la hoja de datos del proceso "
                                        "(H₂S, CO₂, cloruros, pH, sólidos, agua libre)."]))
    if sv.familia_fluido in ("Ácido", "Alcalino", "Solvente") and not sv.agentes:
        alertas.append(Alerta("mat_sin_agente", Severidad.ADVERTENCIA, "Indique el agente químico",
                              f"Familia de fluido «{sv.familia_fluido}» sin agente informado: no se puede evaluar la "
                              "compatibilidad química.", remedios=["Cargar el agente, su unidad y concentración."]))
    for n in agentes:
        if n.supuesto and n.agente.clave != "otro":
            alertas.append(Alerta("mat_sin_concentracion", Severidad.INFO,
                                  f"{n.agente.nombre}: sin concentración",
                                  f"No se informó la concentración de {n.agente.nombre.lower()}; se evaluó con un valor "
                                  f"alto conservador ({n.texto()}).",
                                  remedios=["Ingresar la concentración medida para afinar la selección."]))
        if n.agente.clave == "otro":
            alertas.append(Alerta("mat_agente_otro", Severidad.ADVERTENCIA, "Agente no catalogado",
                                  f"El agente «{n.entrada.texto or 'otro'}» no está en la base química del programa; "
                                  "su efecto no se evalúa.", remedios=["Consultar curvas de corrosión del fabricante."]))
    alertas += _coherencia(sv, agentes, acuoso)
    if sv.medio not in ("Por evaluar",) and sv.medio.split(" (")[0] not in medio and \
            not (sv.medio == "Servicio mixto" and medio.startswith("Servicio mixto")):
        alertas.append(Alerta("mat_medio_distinto", Severidad.INFO, "Medio declarado distinto del detectado",
                              f"Medio esperado declarado: {sv.medio.lower()}; según los datos: {medio.lower()}. "
                              "Revise los datos o el medio declarado."))
    if sv.regimen in ("Intermitente", "Batch", "Emergencia"):
        notas.append(f"Régimen {sv.regimen.lower()}: en paradas el fluido queda estanco (oxígeno, condensación, "
                     "depósitos), lo que favorece picaduras y corrosión bajo depósitos; prever drenaje o purga.")
    if any(m.codigo == "M27" for m in mecs):
        alertas.append(Alerta("mat_oxigeno", Severidad.ADVERTENCIA, "Servicio de oxígeno",
                              "El oxígeno a presión puede encender metales y elastómeros por impacto de partículas o "
                              "compresión adiabática.", remedios=[
                                  "Limpieza para servicio de oxígeno (ASTM G93) y materiales resistentes a la ignición "
                                  "(Monel, bronce, aleaciones de níquel) en zonas de alta velocidad.",
                                  "Evitar titanio y elastómeros NBR."], referencia="ASTM G88 / G94; CGA G-4.4"))
    if any(m.codigo == "M22" and m.estado == "Detectado" for m in mecs):
        alertas.append(Alerta("mat_htha", Severidad.CRITICA, "Ataque por hidrógeno a alta temperatura",
                              "La combinación de presión parcial de hidrógeno y temperatura está en la zona donde el "
                              "acero al carbono sufre descarburación interna.",
                              remedios=["Verificar con las curvas de Nelson (API RP 941) y usar Cr-Mo o inoxidable."],
                              referencia="API RP 941"))

    comps: dict[str, ResultadoComponente] = {}
    nombres = MT.COMPONENTES_ROTATIVA if ctx.rotativa else MT.COMPONENTES
    for k, nombre in nombres.items():
        comps[k] = ResultadoComponente(k, nombre, modo=sv.modos.get(k, "AUTOMÁTICO"))
    comps["jaula"].aplica = ctx.jaula
    comps["guia"].aplica = not ctx.jaula
    if not ctx.jaula:
        comps["jaula"].justificacion.append("El trim elegido no lleva jaula: el obturador se guía en la guía.")
    else:
        comps["guia"].justificacion.append("Obturador guiado por la jaula: no lleva guía separada.")

    def evaluar_todos(comp: str) -> list[Evaluacion]:
        hrc = req.get(comp)
        cand = [m for m in MT.para_componente(comp) if not m.blando]
        return [evaluar_material(m, comp, ctx, sv, agentes, acuoso, agrio, norma, pH2S, azufre, hrc,
                                 desg.get(comp, (0, 0))) for m in cand]

    def escoger(rc: ResultadoComponente, evs: list[Evaluacion], pareja: list[MT.Material] | None = None):
        rc.dureza_req_HRC = req.get(rc.clave)
        aptos = [e for e in evs if e.ok]
        if pareja:
            filtrados = []
            for e in aptos:
                riesgos = [riesgo_galling(e.material, p, ctx.T_max_C)[0] for p in pareja]
                if "ALTO" not in riesgos:
                    filtrados.append(e)
                else:
                    rc.descartados.append((e.material, "Riesgo alto de galling con " +
                                           " / ".join(p.clave for p in pareja) + "."))
            aptos = filtrados or aptos
        aptos.sort(key=lambda e: (e.nivel_quimico == "C", e.puntaje))
        for e in evs:
            if not e.ok:
                rc.descartados.append((e.material, _unir(e.motivos)))
        if aptos:
            mejor = aptos[0]
            rc.recomendado = mejor.material
            rc.alternativas = [(e.material, f"puntaje {_n(e.puntaje, 2)}; química {e.nivel_quimico}")
                               for e in aptos[1:4]]
            barato = min(aptos, key=lambda e: e.material.costo)
            if barato is not mejor and barato.nivel_quimico == "C" and barato.material.costo < mejor.material.costo / 2:
                rc.alternativas.append((barato.material, "alternativa económica con compatibilidad C: solo con "
                                        "sobreespesor de corrosión, inhibidor y evaluación del especialista"))
            return mejor
        return None

    def explicar(rc: ResultadoComponente, e: Evaluacion | None):
        if e is None:
            return
        m = e.material
        j = rc.justificacion
        j.append(f"Seleccionado: {m.nombre} (UNS {m.uns or '—'}; {m.astm}).")
        j.append(f"Temperatura del servicio {_n(ctx.T_min_C, 0)} a {_n(ctx.T_max_C, 0)} °C dentro del rango del "
                 f"material ({_n(m.T_min_C, 0)} a {_n(m.T_max_C, 0)} °C).")
        if e.quimica:
            j.append(f"Compatibilidad química global: {Q.NIVEL_TXT[e.nivel_quimico]}.")
            j += ["  · " + c.detalle for c in e.quimica]
        else:
            j.append("Sin agentes corrosivos informados." if not (rc.clave == "cuerpo" and ctx.liner) else
                     "Cuerpo revestido: la superficie mojada es el revestimiento (PFA/PTFE); el material del cuerpo "
                     "se verifica solo por presión-temperatura.")
        if rc.clave in ("cuerpo", "bonete") and m.grupo:
            if e.rating is not None:
                j.append(f"ASME B16.34 grupo {m.grupo}: CL{ctx.clase} admite {_n(e.rating, 1)} bar g a "
                         f"{_n(ctx.T_max_C, 0)} °C ≥ diseño {_n(ctx.P_barg, 1)} bar g.")
            elif e.clase_min:
                j.append(f"ASME B16.34 grupo {m.grupo}: clase mínima CL{e.clase_min} para {_n(ctx.P_barg, 1)} bar g "
                         f"a {_n(ctx.T_max_C, 0)} °C.")
            if m.grupo_equivalente:
                j.append(f"La fundición no figura en la Tabla 1 de B16.34: rating del forjado equivalente "
                         f"({m.equivalente}), a confirmar por el fabricante.")
        elif rc.clave in ("cuerpo", "bonete"):
            j.append("Material no incluido en ASME B16.34: el rating lo fija el fabricante (ASME B31.3 / Sec. VIII).")
        if agrio:
            n = _nace(m, norma)
            j.append(f"{norma}: {n.estado}" + (f" — {n.nota}" if n.nota else "") + ".")
        if rc.dureza_req_HRC:
            j.append(f"Dureza requerida ≥ {rc.dureza_req_HRC:.0f} HRC (≈ {MT.hrc_a_hb(rc.dureza_req_HRC):.0f} HB); "
                     f"el material ofrece {m.dureza_txt}.")
        j.append(f"Índice de costo {m.costo:g} (cuerpo WCB = 1; internos 316 = 1). Es la opción apta de menor costo "
                 "ponderado por durabilidad química y mecánica.")
        for x in e.motivos:
            j.append("Observación: " + x)

    def aplicar_modo(rc: ResultadoComponente, evs: list[Evaluacion], mejor: Evaluacion | None,
                     pareja: list[MT.Material] | None = None):
        if rc.modo == "MANUAL" and sv.manual.get(rc.clave) in MT.MATERIALES:
            m = MT.MATERIALES[sv.manual[rc.clave]]
            e = next((x for x in evs if x.material.clave == m.clave), None)
            if e is None:
                e = evaluar_material(m, rc.clave, ctx, sv, agentes, acuoso, agrio, norma, pH2S, azufre,
                                     req.get(rc.clave), desg.get(rc.clave, (0, 0)))
                e.ok = False
                e.motivos.insert(0, f"El material no se usa habitualmente como {rc.nombre.lower()}.")
            rc.elegido = m
            rc.eval_elegido = e
            rc.alertas.append(Alerta("mat_manual", Severidad.ADVERTENCIA, f"{rc.nombre}: selección manual",
                                     f"El material de {rc.nombre.lower()} ({m.nombre}) fue elegido manualmente. La "
                                     "selección manual no es recomendada: la responsabilidad por su aptitud queda "
                                     "fuera del alcance del programa." + (f" Recomendado: {rc.recomendado.nombre}."
                                                                          if rc.recomendado and rc.recomendado != m else "")))
            if not e.ok:
                rc.alertas.append(Alerta("mat_incompatible", Severidad.CRITICA, f"{rc.nombre}: material no apto",
                                         f"{m.nombre}: " + _unir(e.motivos),
                                         remedios=[f"Usar {rc.recomendado.nombre}." if rc.recomendado else
                                                   "Consultar al fabricante por un material especial."]))
            elif e.nivel_quimico == "C":
                rc.alertas.append(Alerta("mat_quimica_regular", Severidad.ADVERTENCIA,
                                         f"{rc.nombre}: compatibilidad química regular",
                                         f"{m.nombre} tiene compatibilidad C con el fluido: vida reducida."))
            rc.justificacion.insert(0, "Modo MANUAL: el material lo eligió el usuario.")
            explicar(rc, e)
        else:
            rc.modo = "AUTOMÁTICO"
            rc.elegido = rc.recomendado
            rc.eval_elegido = mejor
            if mejor is None:
                rc.alertas.append(Alerta("mat_sin_candidato", Severidad.CRITICA, f"{rc.nombre}: sin material apto",
                                         f"Ningún material de la biblioteca cumple a la vez temperatura, química, "
                                         "servicio agrio, dureza y presión-temperatura para "
                                         f"{rc.nombre.lower()}.", remedios=[
                                             "Revisar los datos del servicio y la clase de presión.",
                                             "Consultar al fabricante por una aleación o recubrimiento especial."]))
                motivos = {}
                for mm, mot in rc.descartados:
                    motivos.setdefault(mot.split(":")[0][:60], mm)
                rc.justificacion.append("Causas de descarte más frecuentes: " +
                                        "; ".join(list(motivos)[:4]) + ".")
            else:
                explicar(rc, mejor)
                if mejor.nivel_quimico == "C":
                    rc.alertas.append(Alerta("mat_quimica_regular", Severidad.ADVERTENCIA,
                                             f"{rc.nombre}: compatibilidad química regular",
                                             f"El mejor material disponible ({mejor.material.nombre}) tiene "
                                             "compatibilidad C: vida reducida.",
                                             remedios=["Consultar aleaciones especiales o revestimientos."]))

    # Cuerpo
    ev = evaluar_todos("cuerpo")
    mejor = escoger(comps["cuerpo"], ev)
    aplicar_modo(comps["cuerpo"], ev, mejor)
    cuerpo = comps["cuerpo"].elegido
    # alertas P-T del cuerpo elegido
    if cuerpo and cuerpo.grupo is None:
        comps["cuerpo"].alertas.append(Alerta("mat_no_b1634", Severidad.INFO, "Material fuera de ASME B16.34",
                                              f"{cuerpo.nombre} no figura en las tablas de ASME B16.34: el rating lo "
                                              "fija el fabricante.", referencia="ASME B16.34, Tabla 1"))
    e = comps["cuerpo"].eval_elegido
    if cuerpo and e and cuerpo.grupo:
        fuera = [x for x in e.motivos if "CL" in x and "admite" in x or "fuera de la tabla" in x or "bridada" in x]
        if fuera:
            comps["cuerpo"].alertas.append(Alerta("mat_fuera_pt", Severidad.CRITICA,
                                                  "Cuerpo fuera de los límites presión-temperatura",
                                                  " ".join(fuera), remedios=[
                                                      f"Usar CL{e.clase_min}." if e.clase_min else
                                                      "Cambiar de material o de clase."],
                                                  referencia=f"ASME B16.34, Tabla 2-{cuerpo.grupo}"))
        if cuerpo.grupo_equivalente:
            comps["cuerpo"].alertas.append(Alerta("mat_grupo_equivalente", Severidad.INFO,
                                                  "Rating por el forjado equivalente",
                                                  f"{cuerpo.nombre} no figura en la Tabla 1 de B16.34; se usó el "
                                                  f"grupo {cuerpo.grupo} de {cuerpo.equivalente}.",
                                                  referencia="ASME B16.34, 2.1"))
    if cuerpo and cuerpo.grupo in ("1.1", "1.2", "1.3", "1.4") and ctx.T_max_C > 425:
        comps["cuerpo"].alertas.append(Alerta("grafitizacion", Severidad.ADVERTENCIA,
                                              "Riesgo de grafitización del acero al carbono",
                                              "Con exposición prolongada por encima de 425 °C la fase carburo del acero "
                                              "al carbono puede convertirse en grafito.",
                                              remedios=["Especificar ASTM A217 WC6 o WC9."],
                                              referencia="ASME B16.34, notas de las Tablas 2-1.1 y 2-1.2"))
    # Bonete: mismo material del cuerpo (o su equivalente forjado)
    bon = comps["bonete"]
    if bon.modo == "MANUAL" and sv.manual.get("bonete") in MT.MATERIALES:
        evb = evaluar_todos("bonete")
        escoger(bon, evb)
        aplicar_modo(bon, evb, None)
    else:
        bon.modo = "AUTOMÁTICO"
        bon.elegido = bon.recomendado = cuerpo
        bon.eval_elegido = comps["cuerpo"].eval_elegido
        if cuerpo:
            bon.justificacion.append(f"El bonete se especifica del mismo material que el cuerpo ({cuerpo.nombre}) "
                                     f"o de su equivalente forjado ({cuerpo.equivalente or '—'}), con el mismo grupo "
                                     "de ASME B16.34 y la misma resistencia química.")
    if cuerpo and bon.elegido and bon.elegido.grupo and cuerpo.grupo and bon.elegido.grupo != cuerpo.grupo and ctx.clase:
        rb = B.rating(bon.elegido.grupo, ctx.clase, ctx.T_max_C)
        if rb is not None and rb < ctx.P_barg:
            bon.alertas.append(Alerta("mat_fuera_pt", Severidad.CRITICA, "Bonete fuera de presión-temperatura",
                                      f"CL{ctx.clase} con el grupo {bon.elegido.grupo} admite {_n(rb, 1)} bar g."))

    # Obturador
    ev = evaluar_todos("obturador")
    mejor = escoger(comps["obturador"], ev)
    aplicar_modo(comps["obturador"], ev, mejor)
    obt = comps["obturador"].elegido
    # Asiento (contra el obturador)
    ev = evaluar_todos("asiento")
    mejor = escoger(comps["asiento"], ev, [obt] if obt else None)
    aplicar_modo(comps["asiento"], ev, mejor)
    if ctx.blando:
        ins = _inserto(ctx, sv, agentes, acuoso)
        comps["asiento"].inserto = ins
        if ins:
            comps["asiento"].justificacion.append(
                f"La clase de cierre requiere asiento blando: inserto de {ins.nombre} (hasta {_n(ins.T_max_C, 0)} °C).")
        else:
            comps["asiento"].alertas.append(Alerta("mat_inserto", Severidad.CRITICA, "Sin inserto blando apto",
                                                   "Ningún material de asiento blando resiste la temperatura o el "
                                                   "fluido.", remedios=["Usar cierre metal-metal clase V."]))
    # Jaula (contra el obturador)
    if ctx.jaula:
        ev = evaluar_todos("jaula")
        mejor = escoger(comps["jaula"], ev, [obt] if obt else None)
        aplicar_modo(comps["jaula"], ev, mejor)
    # Vástago
    ev = evaluar_todos("vastago")
    mejor = escoger(comps["vastago"], ev)
    aplicar_modo(comps["vastago"], ev, mejor)
    vas = comps["vastago"].elegido
    # Guía (contra el obturador y el vástago)
    if not ctx.jaula:
        ev = evaluar_todos("guia")
        par = [x for x in (obt, vas) if x]
        mejor = escoger(comps["guia"], ev, par or None)
        aplicar_modo(comps["guia"], ev, mejor)

    # Galling de las parejas elegidas
    gall: list[Galling] = []

    def par(nombre, ka, kb):
        a, b = comps[ka].elegido, comps[kb].elegido
        if not (a and b and comps[ka].aplica and comps[kb].aplica):
            return
        nivel, mot, rem = riesgo_galling(a, b, ctx.T_max_C)
        gall.append(Galling(nombre, a.clave, b.clave, nivel, mot, rem))
        if nivel != "BAJO":
            sev = Severidad.CRITICA if nivel == "ALTO" else Severidad.ADVERTENCIA
            alertas.append(Alerta("galling", sev, f"Riesgo {nivel.lower()} de galling: {nombre.lower()}",
                                  f"{a.nombre} contra {b.nombre}: {mot}", remedios=[rem] if rem else [],
                                  referencia="ASTM G98 (umbral de galling)"))

    n_obt = nombres["obturador"]
    if ctx.jaula:
        par(f"{n_obt} – {nombres['jaula']}", "obturador", "jaula")
    par(f"{n_obt} – {nombres['asiento']}", "obturador", "asiento")
    if not ctx.jaula:
        par(f"{n_obt} – {nombres['guia']}", "obturador", "guia")
        par(f"{nombres['vastago']} – {nombres['guia']}", "vastago", "guia")

    # Resumen de dureza
    motivo = " ".join(porque_dureza) if porque_dureza else "Servicio sin cavitación, flashing, sólidos ni ΔP alta: no se exige dureza mínima."
    if req:
        alertas.append(Alerta("cavitacion_dureza", Severidad.INFO, "Dureza mínima de los internos",
                              motivo, referencia="ISA-RP75.23; práctica de fabricantes de válvulas"))
    if agrio:
        alertas.append(Alerta("servicio_agrio", Severidad.ADVERTENCIA, "Servicio agrio (H₂S)",
                              f"pH₂S = {_n(pH2S, 2)} kPa ≥ 0,3 kPa con agua libre: materiales según {norma}. "
                              "Pernos de cuerpo-bonete expuestos o aislados: ASTM A193 B7M / A194 2HM.",
                              remedios=["Exigir certificados con dureza (MTR) y procedimientos de soldadura "
                                        "calificados con dureza de ZAC ≤ 250 HV."],
                              referencia=norma))
    emp = EM.seleccionar(sv, ctx, agentes, acuoso, agrio, sv.modos.get("empaquetadura", "AUTOMÁTICO"),
                         sv.manual.get("empaquetadura"))
    alertas += emp.alertas
    return ResultadoMateriales(sv, ctx, comps, agentes, mecs, agrio, pH2S, norma, norma_motivo, medio, req,
                               motivo, gall, alertas, notas, emp)


def _inserto(ctx, sv, agentes, acuoso) -> MT.Material | None:
    cands = [m for m in MT.MATERIALES.values() if m.blando]
    aptos = []
    for m in cands:
        if ctx.T_max_C > m.T_max_C or ctx.T_min_C < m.T_min_C:
            continue
        niv = Q._peor(*(Q.evaluar(m, n, ctx.T_max_C, acuoso).nivel for n in agentes)) if agentes else "A"
        if niv in ("D", "C"):
            continue
        f = 1.0 if niv == "A" else 1.5
        if ctx.dP_max_kPa > 1000 and m.clave == "PTFE":
            f *= 1.6   # fluencia en frío del PTFE virgen con ΔP alta
        aptos.append((m.costo * f, m))
    aptos.sort(key=lambda t: t[0])
    return aptos[0][1] if aptos else None


def contexto(res, sv: ServicioMateriales | None = None) -> Contexto:
    """Construye el contexto de selección a partir de un ``proyecto.Resultado`` (o equivalente)."""
    from .estilos import CUERPOS
    inst, dim, salidas = res.inst, res.dim, res.salidas
    T_ops = [s.get("T1") or c.T1 for c, s in zip(dim.casos, salidas)] + [s["T2"] for s in salidas if s.get("T2")]
    if dim.cierre and dim.cierre.T1:
        T_ops.append(dim.cierre.T1)
    T_ops = [t for t in T_ops if t]
    T_max = max([res.T_diseno] + T_ops) - 273.15
    T_min = min(T_ops) - 273.15
    sevs = []
    flashing = False
    casos_cav = []
    if not dim.compresible:
        for c, s in zip(dim.casos, salidas):
            sev = severidad_cavitacion(s)
            if sev == "flashing":
                flashing = True
            else:
                sevs.append(sev)
            casos_cav.append((c.nombre, sev, s.get("Kapp") or 0, s.get("Kc") or 0, (s.get("FL") or 0) ** 2))
    peor = max(sevs or ["ninguna"], key=SEVERIDADES.index)
    cuerpo = CUERPOS[inst.cuerpo]
    from .proyecto import CIERRES
    n = CIERRES.index(inst.cierre)
    blando = {"globo": n >= 5, "angulo": n >= 5, "globo_liner": True, "bola_paso_completo": n >= 5,
              "bola_paso_reducido": n >= 5, "bola_trunnion": n >= 5, "bola_segmentada": n >= 5,
              "tapon_excentrico": n >= 5, "mariposa": n >= 4,
              "mariposa_doble": n >= 5}.get(inst.cuerpo, False)
    dPs = [c.P1 - c.P2 for c in dim.casos] + ([dim.cierre.dP] if dim.cierre else [])
    SG = getattr(dim.casos[0], "SG", 1.0) if dim.casos else 1.0
    return Contexto(T_max_C=T_max, T_min_C=T_min, P_barg=(res.P_diseno - 101.325) / 100,
                    P_kPa=max(c.P1 for c in dim.casos), clase=inst.rating,
                    bridada="bridada" in inst.conexion.lower() or inst.conexion == "Wafer",
                    rotativa=cuerpo.rotativa, jaula="jaula" in dim.trim or "multietapa" in dim.trim,
                    liner=inst.cuerpo == "globo_liner", compresible=dim.compresible, tipo=dim.tipo,
                    dP_max_kPa=max(dPs), severidad_cav=peor, flashing=flashing, blando=blando, SG=SG or 1.0,
                    casos_cav=casos_cav, P_min_kPa=min([c.P2 for c in dim.casos] + [c.P1 for c in dim.casos]))
