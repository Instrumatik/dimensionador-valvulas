"""Empaquetadura del vástago (o del eje) y tipo de bonete.

Elige la empaquetadura más adecuada para el fluido, la presión y la temperatura: límites de
temperatura (incluido el grafito en medio oxidante), presión, compatibilidad química (las
mismas reglas A–D de ``quimica``), vacío, servicio de oxígeno, vapor, sólidos y exigencia de
baja emisión fugitiva (fluidos tóxicos, inflamables o COV). Define además el bonete: estándar,
prolongado (alta o baja temperatura), criogénico o con fuelle de estanqueidad.

Valores genéricos y típicos de catálogo; no corresponden a ningún fabricante. Verificar con la
hoja técnica de la empaquetadura ofertada y, para baja emisión, con su certificado de ensayo
(ISO 15848-1, API 622 / 624 / 641).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import quimica as Q
from .modelos import Alerta, Severidad, _n

F_PRACTICA = "Práctica de la industria de válvulas de control (empaquetaduras y bonetes); ASME B16.34"
F_EMISION = "ISO 15848-1:2015; API 622 (empaquetadura), API 624 (vástago ascendente), API 641 (cuarto de vuelta)"


@dataclass(frozen=True)
class Empaquetadura:
    clave: str
    nombre: str
    quimica: tuple            # clases de quimica.REGLAS
    T_min_C: float
    T_max_C: float            # medio no oxidante
    T_max_oxid_C: float       # con aire / oxígeno / oxidantes
    P_max_bar: float          # presión máxima típica del conjunto (con anillos antiextrusión)
    emision: str              # «estándar», «baja (ISO 15848-1 clase B)», «muy baja (clase A)»
    carga_viva: bool
    friccion: str             # baja, media, alta
    costo: float              # índice relativo (PTFE en V simple = 1)
    vacio: bool               # apta para vacío
    solo_lineal: bool = False  # fuelle: solo vástago ascendente
    descripcion: str = ""
    notas: tuple = ()
    tipo: str = ""            # disposición: anillos en V, presión / vacío, carga viva, trenzada, cinta moldeada

    @property
    def guia_temperatura(self) -> str:
        """Guía rápida de temperatura: hasta 232 °C (PTFE) o por encima (grafito)."""
        if self.T_max_C <= 260:
            return f"Hasta {_n(self.T_max_C, 0)} °C ({_n(self.T_max_C * 9 / 5 + 32, 0)} °F)"
        return f"Por encima de 232 °C (450 °F), hasta {_n(self.T_max_C, 0)} °C"

    @property
    def baja_emision(self) -> bool:
        return self.emision != "estándar"

    # interfaz mínima para quimica.evaluar
    @property
    def blando(self) -> bool:
        return True


EMPAQUETADURAS: dict[str, Empaquetadura] = {e.clave: e for e in [
    Empaquetadura("ptfe_v", "Anillos en V de PTFE, simple, con resorte", ("ptfe",), -46, 232, 232, 103,
                  "estándar", False, "baja", 1.0, False, tipo="Anillos en V con resorte",
                  descripcion="Juego de anillos en V (chevron) de PTFE virgen con adaptadores macho y hembra y un "
                              "resorte que mantiene la carga. Es la empaquetadura estándar de las válvulas de "
                              "control: baja fricción (buena precisión de posicionamiento) y resistencia química "
                              "casi universal.",
                  notas=("Fluye en frío con presión y temperatura altas: no supera 232 °C.",)),
    Empaquetadura("ptfe_v_doble", "PTFE doble en V, para presión y vacío (juegos opuestos)", ("ptfe",), -46, 232, 232, 103,
                  "estándar", False, "baja", 1.3, True, tipo="Presión / vacío",
                  descripcion="Dos juegos de anillos en V enfrentados: uno sella la presión y otro impide la "
                              "entrada de aire. Para vacío y para servicios con presión alternada.",
                  notas=("Requiere vástago bien terminado (Ra ≤ 0,4 µm).",)),
    Empaquetadura("ptfe_cv", "PTFE con carga viva (resortes Belleville), baja emisión", ("ptfe",), -46, 232,
                  232, 207, "baja (ISO 15848-1 clase B, ≤ 100 ppmv)", True, "baja", 2.5, True, tipo="Carga viva",
                  descripcion="Anillos de PTFE con resortes de disco (Belleville) que mantienen la carga de "
                              "compresión con el desgaste y los ciclos térmicos. Baja emisión fugitiva sin "
                              "reajustes frecuentes.",
                  notas=("Certificar la emisión con ensayo ISO 15848-1 o API 622 / 641.",)),
    Empaquetadura("ptfe_carbono", "Anillos de PTFE con carbono / grafito (relleno)", ("ptfe",), -46, 260, 260,
                  138, "estándar", False, "media", 1.5, False, tipo="Anillos moldeados",
                  descripcion="PTFE cargado con carbono o grafito: menos flujo en frío, mejor conductividad "
                              "térmica y algo más de temperatura que el PTFE virgen.",
                  notas=("No usar con oxidantes fuertes por el carbono del relleno.",)),
    Empaquetadura("grafito", "Grafito simple: cinta moldeada + trenzas de carbono antiextrusión",
                  ("grafito",), -198, 538, 371, 414, "estándar", False, "alta", 1.3, False, tipo="Cinta moldeada",
                  descripcion="Anillos de grafito flexible expandido con anillos de trenza de carbono en los "
                              "extremos para evitar la extrusión. Para alta temperatura, vapor y servicio "
                              "contra fuego (fire-safe).",
                  notas=("Fricción alta: considerarla en el par o la fuerza del actuador y en la precisión.",
                         "En agua o vapor, usar grafito con inhibidor de corrosión (o arandela de sacrificio) "
                         "para evitar la corrosión galvánica del vástago.",
                         "Se oxida en aire u oxidantes por encima de unos 371 °C.")),
    Empaquetadura("grafito_cv", "Grafito de baja fricción con carga viva (resortes Belleville), baja emisión", ("grafito",),
                  -198, 371, 371, 414, "baja (ISO 15848-1 clase B/C, API 622 / 624)", True, "alta", 3.0, True,
                  tipo="Carga viva",
                  descripcion="Grafito flexible con resortes de disco que compensan la relajación y el "
                              "desgaste: baja emisión fugitiva en alta presión y temperatura.",
                  notas=("Fricción alta: verificar el actuador.",
                         "Certificar la emisión con ensayo ISO 15848-1, API 622 o API 624 / 641.")),
    # ---- v0.8.2
    Empaquetadura("ptfe_v_doble_p", "PTFE doble en V, para presión (dos juegos en serie)", ("ptfe",), -46, 232, 232,
                  103, "estándar", False, "baja", 1.2, False, tipo="Presión / vacío",
                  descripcion="Dos juegos de anillos en V orientados a la presión, uno sobre otro, con un anillo "
                              "distanciador: el segundo juego respalda al primero y alarga los intervalos de "
                              "mantenimiento en presión alta o ciclos frecuentes.",
                  notas=("No sirve para vacío: los anillos solo sellan en el sentido de la presión.",)),
    Empaquetadura("ptfe_v_doble_vac", "PTFE doble en V, para vacío (juegos invertidos)", ("ptfe",), -46, 232, 232,
                  3.5, "estándar", False, "baja", 1.25, True, tipo="Presión / vacío",
                  descripcion="Juegos de anillos en V invertidos para que la presión atmosférica los cierre e "
                              "impida la entrada de aire al proceso.",
                  notas=("Solo para vacío o presiones muy bajas: con presión interna los anillos se abren.",)),
    Empaquetadura("ptfe_carbono_cv_doble", "PTFE/carbono con carga viva, doble juego, baja emisión", ("ptfe",), -46,
                  232, 232, 207, "baja (ISO 15848-1 clase B, ≤ 100 ppmv)", True, "baja", 3.0, True,
                  tipo="Carga viva",
                  descripcion="Dos juegos de anillos de PTFE cargado con carbono separados por un anillo "
                              "distanciador, con resortes de disco: redundancia para emisión baja y presión o "
                              "vacío.", notas=("No usar con oxidantes fuertes por el carbono del relleno.",
                                               "Certificar la emisión con ensayo ISO 15848-1 o API 622 / 641.")),
    Empaquetadura("ptfe_vidrio_cv", "PTFE/vidrio con carga viva, baja emisión", ("ptfe", "vidrio"), -46, 232, 232,
                  207, "baja (ISO 15848-1 clase B, ≤ 100 ppmv)", True, "baja", 2.6, True, tipo="Carga viva",
                  descripcion="Anillos de PTFE cargado con fibra de vidrio y resortes de disco: menos flujo en frío "
                              "que el PTFE virgen y apto con oxidantes, donde no se admite el carbono.",
                  notas=("El vidrio es atacado por HF y álcalis concentrados calientes.",)),
    Empaquetadura("grafito_hs_718", "Grafito de alta hermeticidad con carga viva, resortes de Inconel 718",
                  ("grafito",), -198, 538, 371, 414, "baja (ISO 15848-1 clase B, API 622 / 624)", True, "alta",
                  3.6, True, tipo="Carga viva",
                  descripcion="Anillos de grafito de alta densidad con anillos antiextrusión y resortes de disco de "
                              "Inconel 718, que conservan la carga a alta temperatura: baja emisión por encima del "
                              "límite de los resortes de acero.",
                  notas=("Fricción alta: verificar el actuador.", "Se oxida en aire por encima de unos 371 °C.")),
    Empaquetadura("grafito_hs_177", "Grafito de alta hermeticidad con carga viva, resortes de 17-7PH",
                  ("grafito",), -198, 343, 343, 414, "baja (ISO 15848-1 clase B, API 622 / 624)", True, "alta",
                  3.3, True, tipo="Carga viva",
                  descripcion="Como la anterior con resortes de disco de 17-7PH, más económicos, limitados a unos "
                              "343 °C.", notas=("Fricción alta: verificar el actuador.",)),
    Empaquetadura("ptfe_trenzado", "PTFE trenzado (empaquetadura de compresión)", ("ptfe",), -46, 232, 232, 69,
                  "estándar", False, "media", 1.1, False, tipo="Trenzada",
                  descripcion="Anillos de trenza de hilo de PTFE comprimidos por el prensaestopas. Económica y "
                              "tolerante a vástagos con desgaste, pero requiere reapriete periódico.",
                  notas=("Pierde carga con el tiempo: no es apta para baja emisión.",)),
    Empaquetadura("ptfe_trenzado_lub", "PTFE trenzado con lubricador y válvula de aislamiento", ("ptfe",), -46,
                  232, 232, 69, "estándar", False, "media", 1.4, False, tipo="Trenzada",
                  descripcion="Trenza de PTFE con un anillo distanciador alimentado por un lubricador y una válvula "
                              "de aislamiento: el lubricante sella y reduce la fricción. Para fluidos que "
                              "cristalizan o con sólidos finos.",
                  notas=("El lubricante debe ser compatible con el proceso.",)),
    Empaquetadura("fuelle", "Bonete con fuelle metálico + empaquetadura de respaldo", ("fuelle",), -198, 538,
                  538, 100, "muy baja (ISO 15848-1 clase A, estanqueidad total)", False, "baja", 6.0, True,
                  solo_lineal=True, tipo="Fuelle + respaldo",
                  descripcion="Un fuelle metálico soldado al vástago y al bonete forma una barrera estanca; la "
                              "empaquetadura queda como respaldo. Para fluidos letales o tóxicos, alta pureza "
                              "o cuando no se admite ninguna emisión.",
                  notas=("Solo para vástago ascendente (globo y ángulo).",
                         "Vida limitada por ciclos y por presión: pedir la presión admisible y la vida en "
                         "ciclos del fuelle al fabricante.")),
]}
# Orden de presentación: PTFE, PTFE con carga viva, grafito y fuelle
_ORDEN = ("ptfe_v", "ptfe_v_doble_p", "ptfe_v_doble_vac", "ptfe_v_doble", "ptfe_trenzado", "ptfe_trenzado_lub",
          "ptfe_carbono", "ptfe_cv", "ptfe_carbono_cv_doble", "ptfe_vidrio_cv", "grafito", "grafito_cv",
          "grafito_hs_177", "grafito_hs_718", "fuelle")
EMPAQUETADURAS = {k: EMPAQUETADURAS[k] for k in _ORDEN}

# Metales del fuelle, del más común al más resistente
FUELLE_METALES = ("316", "625", "C276")
# Fluidos (o agentes) letales / tóxicos y COV para la exigencia de emisión
TOXICOS_AGENTES = {"h2s", "cl2", "hf", "so2", "so3", "nh3", "hcl"}
TOXICOS_FLUIDOS = {"Sulfuro de hidrógeno", "Cloro", "Amoníaco", "Monóxido de carbono", "Benceno"}
COV_FAMILIAS = {"Hidrocarburo líquido", "Hidrocarburo gaseoso", "Solvente"}
OXIDANTES = {"o2", "hno3", "h2o2", "hipoclorito", "cl2", "hclo4", "nitratos", "so3"}


@dataclass
class EvaluacionEmpaque:
    empaque: Empaquetadura
    ok: bool
    puntaje: float
    motivos: list[str]
    quimica: list[Q.Compatibilidad]
    nivel: str
    metal_fuelle: str | None = None


@dataclass
class ResultadoEmpaquetadura:
    modo: str
    recomendada: Empaquetadura | None
    elegida: Empaquetadura | None
    bonete: str
    bonete_motivo: str
    emision_req: str
    emision_motivo: str
    justificacion: list[str] = field(default_factory=list)
    alternativas: list[tuple[Empaquetadura, str]] = field(default_factory=list)
    descartadas: list[tuple[Empaquetadura, str]] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)
    alertas: list[Alerta] = field(default_factory=list)
    eval_elegida: EvaluacionEmpaque | None = None

    @property
    def texto(self) -> str:
        if self.elegida is None:
            return "Sin empaquetadura apta"
        t = self.elegida.nombre
        if self.eval_elegida and self.eval_elegida.metal_fuelle:
            from .materiales import MATERIALES
            t += f" (fuelle de {MATERIALES[self.eval_elegida.metal_fuelle].nombre.split(' (')[0]})"
        return t


def _bonete(T_min: float, T_max: float, rotativa: bool) -> tuple[str, str]:
    pieza = "prensaestopas del eje" if rotativa else "bonete"
    if T_min < -101:
        return (f"Criogénico prolongado ({pieza})",
                f"T mínima {_n(T_min, 0)} °C < −101 °C: {pieza} prolongado (BS 6364 / MSS SP-134) para que la "
                "empaquetadura trabaje cerca de la temperatura ambiente y no se congele.")
    if T_min < -29:
        return (f"Prolongado para baja temperatura ({pieza})",
                f"T mínima {_n(T_min, 0)} °C < −29 °C: {pieza} prolongado para alejar la empaquetadura del "
                "frío.")
    if T_max > 427:
        return (f"Prolongado con aletas para alta temperatura ({pieza})",
                f"T máxima {_n(T_max, 0)} °C > 427 °C: {pieza} prolongado con aletas para bajar la temperatura "
                "en la empaquetadura y proteger el actuador.")
    if T_max > 232:
        return (f"Estándar con empaquetadura de alta temperatura, o prolongado ({pieza})",
                f"T máxima {_n(T_max, 0)} °C > 232 °C: supera el PTFE; con {pieza} estándar se usa grafito, o "
                "un prolongado si se quiere conservar PTFE.")
    return (f"Estándar ({pieza})", f"T de {_n(T_min, 0)} a {_n(T_max, 0)} °C dentro del rango de un {pieza} "
            "estándar.")


def _emision(sv, agentes, agrio: bool) -> tuple[str, str]:
    toxicos = [n.agente.nombre for n in agentes if n.agente.clave in TOXICOS_AGENTES and not n.supuesto
               and (n.kPa or n.valor or 0) > 0]
    if sv.fluido in TOXICOS_FLUIDOS:
        toxicos.insert(0, sv.fluido)
    if agrio:
        toxicos.append("servicio agrio (H₂S)")
    if toxicos:
        return "muy baja", (f"Fluido tóxico o letal ({', '.join(dict.fromkeys(toxicos))}): emisión fugitiva muy "
                            "baja; fuelle en válvulas de vástago ascendente o empaquetadura con carga viva "
                            "certificada ISO 15848-1 clase A/B.")
    if sv.familia_fluido in COV_FAMILIAS or sv.fluido in ("Gas natural", "Gas combustible"):
        return "baja", ("Hidrocarburo o solvente (COV, inflamable): empaquetadura de baja emisión con carga viva "
                        "certificada (ISO 15848-1 clase B, API 622 / 624 / 641).")
    return "estándar", "Fluido no tóxico ni COV: alcanza una empaquetadura estándar."


def evaluar(e: Empaquetadura, sv, ctx, agentes, acuoso: bool, req_emision: str) -> EvaluacionEmpaque:
    motivos: list[str] = []
    ok = True
    T_max, T_min = ctx.T_max_C, ctx.T_min_C
    claves = {n.agente.clave for n in agentes}
    oxid = bool(claves & OXIDANTES) or sv.fluido in ("Aire", "Oxígeno")
    T_lim = e.T_max_oxid_C if oxid else e.T_max_C
    if T_max > T_lim:
        ok = False
        motivos.append(f"T máxima {_n(T_max, 0)} °C supera su límite de {_n(T_lim, 0)} °C"
                       + (" en medio oxidante" if oxid and T_lim < e.T_max_C else "") + ".")
    # con T mínima < −29 °C el bonete prolongado aleja la empaquetadura del frío
    if T_min < e.T_min_C and T_min >= -29:
        ok = False
        motivos.append(f"T mínima {_n(T_min, 0)} °C menor que su límite de {_n(e.T_min_C, 0)} °C.")
    if ctx.P_barg > e.P_max_bar:
        ok = False
        motivos.append(f"Presión de diseño {_n(ctx.P_barg, 1)} bar g mayor que su límite típico de "
                       f"{_n(e.P_max_bar, 0)} bar.")
    if e.solo_lineal and ctx.rotativa:
        ok = False
        motivos.append("El fuelle solo existe para vástago ascendente (globo y ángulo).")
    if getattr(ctx, "P_min_kPa", 101.325) < 90 and not e.vacio:
        ok = False
        motivos.append(f"Servicio en vacío (P mínima {_n(ctx.P_min_kPa, 1)} kPa abs): requiere PTFE doble, carga "
                       "viva o fuelle.")
    if req_emision == "muy baja" and not e.baja_emision:
        ok = False
        motivos.append("Fluido tóxico: no cumple la emisión fugitiva requerida.")
    elif req_emision == "baja" and not e.baja_emision:
        ok = False
        motivos.append("Hidrocarburo / COV: requiere empaquetadura de baja emisión certificada.")
    if sv.fluido == "Oxígeno" and "grafito" in e.quimica and T_max > 200:
        motivos.append("Oxígeno caliente: el grafito debe ser de grado apto para oxígeno (ensayo BAM).")
    if "carbono" in e.clave and claves & OXIDANTES:
        ok = False
        motivos.append("El relleno de carbono no es apto con oxidantes fuertes.")

    comp: list[Q.Compatibilidad] = []
    metal = None
    if e.clave == "fuelle":
        from .materiales import MATERIALES
        for k in FUELLE_METALES:
            c = [Q.evaluar(MATERIALES[k], n, T_max, acuoso) for n in agentes]
            peor = Q._peor(*[x.nivel for x in c]) if c else "A"
            if peor in ("A", "B"):
                metal, comp = k, c
                break
        if metal is None:
            ok = False
            motivos.append("Ningún metal de fuelle (316L, 625, C-276) es compatible con el fluido.")
            metal = FUELLE_METALES[-1]
    else:
        comp = [Q.evaluar(e, n, T_max, acuoso) for n in agentes]
    nivel = Q._peor(*[c.nivel for c in comp]) if comp else "A"
    if nivel == "D":
        ok = False
        motivos.append("Incompatible químicamente: " + "; ".join(c.detalle for c in comp if c.nivel == "D") + ".")
    f_quim = {"A": 1.0, "B": 1.3, "C": 3.0, "?": 1.6}.get(nivel, 1.0)
    if nivel == "C":
        motivos.append("Compatibilidad química regular (C): vida reducida.")
    f = 1.0
    vapor = sv.familia_fluido == "Vapor" or sv.fluido in ("Condensado", "Agua de alimentación de caldera")
    if "ptfe" in e.quimica and vapor and T_max > 150:
        f *= 1.6
        motivos.append("PTFE en vapor por encima de 150 °C: flujo en frío y reajustes frecuentes.")
    if e.friccion == "alta":
        f *= 1.15        # la fricción empeora el control
    if sv.solidos in ("Presentes",) or sv.familia_fluido == "Slurry":
        motivos.append("Con sólidos conviene un anillo distanciador (lantern ring) con purga o barrido.")
    return EvaluacionEmpaque(e, ok, e.costo * f_quim * f, motivos, comp, nivel, metal if e.clave == "fuelle" else None)


def seleccionar(sv, ctx, agentes, acuoso: bool, agrio: bool, modo: str = "AUTOMÁTICO",
                manual: str | None = None) -> ResultadoEmpaquetadura:
    req, req_motivo = _emision(sv, agentes, agrio)
    bon, bon_motivo = _bonete(ctx.T_min_C, ctx.T_max_C, ctx.rotativa)
    evs = [evaluar(e, sv, ctx, agentes, acuoso, req) for e in EMPAQUETADURAS.values()]
    aptas = sorted([v for v in evs if v.ok], key=lambda v: v.puntaje)
    # en servicio tóxico con vástago ascendente se prefiere el fuelle si es apto
    if req == "muy baja" and not ctx.rotativa:
        fu = [v for v in aptas if v.empaque.clave == "fuelle"]
        if fu:
            aptas = fu + [v for v in aptas if v.empaque.clave != "fuelle"]
    rec = aptas[0] if aptas else None
    res = ResultadoEmpaquetadura(modo, rec.empaque if rec else None, rec.empaque if rec else None, bon, bon_motivo,
                                 req, req_motivo)
    if rec and rec.empaque.clave == "fuelle":
        res.bonete = "Con fuelle de estanqueidad" + (" y prolongado" if "rolongado" in bon else "")
        res.bonete_motivo = ("Bonete con fuelle por la emisión fugitiva requerida (fluido tóxico o letal). "
                             + (bon_motivo if not bon.startswith("Estándar (") else
                                f"Temperatura de {_n(ctx.T_min_C, 0)} a {_n(ctx.T_max_C, 0)} °C: sin prolongación."))
    elegida = rec
    if modo == "MANUAL" and manual in EMPAQUETADURAS:
        elegida = next(v for v in evs if v.empaque.clave == manual)
        res.elegida = elegida.empaque
        res.alertas.append(Alerta("empaque_manual", Severidad.ADVERTENCIA, "Empaquetadura: selección manual",
                                  "La selección manual no es recomendada: la responsabilidad por su aptitud queda "
                                  "fuera del alcance del programa.",
                                  remedios=[f"Recomendada: {rec.empaque.nombre}." if rec else
                                            "No hay empaquetadura apta en la biblioteca."]))
        if not elegida.ok:
            res.alertas.append(Alerta("empaque_incompatible", Severidad.CRITICA, "Empaquetadura no apta",
                                      f"{elegida.empaque.nombre}: " + " ".join(elegida.motivos),
                                      remedios=[f"Usar {rec.empaque.nombre}." if rec else
                                                "Consultar al fabricante."], referencia=F_PRACTICA))
    res.eval_elegida = elegida
    if elegida is None:
        res.alertas.append(Alerta("empaque_sin_candidato", Severidad.CRITICA, "Sin empaquetadura apta",
                                  "Ninguna empaquetadura de la biblioteca cumple temperatura, presión, química y "
                                  "emisión a la vez.",
                                  remedios=["Revisar las condiciones o consultar una solución especial al "
                                            "fabricante (empaquetadura doble con purga, sello de barrera)."],
                                  referencia=F_PRACTICA))
        return res
    e = elegida.empaque
    res.justificacion = [
        f"Seleccionada: {e.nombre}. {e.descripcion}",
        f"Temperatura {_n(ctx.T_min_C, 0)} a {_n(ctx.T_max_C, 0)} °C dentro de su rango ({_n(e.T_min_C, 0)} a "
        f"{_n(e.T_max_C, 0)} °C; {_n(e.T_max_oxid_C, 0)} °C en medio oxidante).",
        f"Presión de diseño {_n(ctx.P_barg, 1)} bar g ≤ {_n(e.P_max_bar, 0)} bar.",
        f"Compatibilidad química: {Q.NIVEL_TXT.get(elegida.nivel, elegida.nivel)}.",
        f"Emisión: requerida {req}; la empaquetadura es {e.emision}. {req_motivo}",
        f"Fricción {e.friccion}; índice de costo {_n(e.costo, 2)} (PTFE en V simple = 1).",
    ] + [c.detalle for c in elegida.quimica]
    if elegida.metal_fuelle:
        from .materiales import MATERIALES
        res.justificacion.append(f"Fuelle de {MATERIALES[elegida.metal_fuelle].nombre}: el metal más común "
                                 "compatible con el fluido.")
    res.justificacion += [m for m in elegida.motivos if m]
    res.notas = list(e.notas)
    if "grafito" in e.quimica and acuoso:
        res.notas.append("Servicio con agua: pedir grafito con inhibidor de corrosión para proteger el vástago.")
    if ctx.rotativa:
        res.notas.append("Válvula rotativa: la emisión se certifica con API 641 (cuarto de vuelta).")
    for v in aptas:
        if v.empaque is not e:
            res.alternativas.append((v.empaque, f"índice {_n(v.puntaje, 2)}"))
    res.descartadas = [(v.empaque, " ".join(v.motivos)) for v in evs if not v.ok]
    if e.friccion == "alta":
        res.alertas.append(Alerta("empaque_friccion", Severidad.INFO, "Empaquetadura de fricción alta",
                                  f"{e.nombre}: su fricción es mayor que la del PTFE. Afecta la fuerza o el par del "
                                  "actuador y la banda muerta del posicionador.",
                                  remedios=["Sumar la fricción de la empaquetadura al dimensionar el actuador.",
                                            "Usar posicionador digital para compensar la banda muerta."],
                                  referencia=F_PRACTICA))
    if req != "estándar":
        res.alertas.append(Alerta("empaque_emision", Severidad.INFO, "Emisión fugitiva controlada",
                                  req_motivo, remedios=["Exigir el certificado de ensayo de emisión: "
                                                        "ISO 15848-1, API 622 / 624 (lineal) o API 641 (rotativa)."],
                                  referencia=F_EMISION))
    if not bon.startswith("Estándar"):
        res.alertas.append(Alerta("bonete_prolongado", Severidad.INFO, "Bonete prolongado", bon_motivo,
                                  referencia=F_PRACTICA))
    return res
