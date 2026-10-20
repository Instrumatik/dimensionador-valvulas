"""Flujo de trabajo de la versión 2: datos de instalación + datos de
dimensionamiento -> resultados, alertas y recomendaciones, para líquidos,
gases, vapores y vapor de agua (estos tres en ``compresible.py``).

Todos los valores se reciben y devuelven en unidades base (kPa abs, K,
m³/h, kg/h, kg/m³, Pa·s, mm, m/s). Las unidades de presentación las
resuelve la interfaz y los entregables.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from . import asme_b16_34, compresible as CG, tuberias
from .estilos import ANTICAVITACION, CUERPOS, ESTILOS, TAMANOS, apertura_requerida
from .iec60534_2_1 import RHO_AGUA_15C, Liquido, factor_FLP
from . import ruido
from .modelos import _n, Alerta, ErrorDatos, Severidad, fdP, fP, fT, fV
from .servicio import Caso, Informe, Seleccion, dimensionar

RATINGS = [150, 300, 600, 900, 1500, 2500]
CONEXIONES = ["BWE", "RF bridada", "RTJ bridada", "SCH XXS BWE", "SWE", "FF bridada",
              "Sin bridas", "Wafer", "FNPT", "MNPT"]
CIERRES = ["ANSI Clase I", "ANSI Clase II", "ANSI Clase III", "ANSI Clase IV", "ANSI Clase V",
           "ANSI Clase VI", "Tight Shutoff"]
FUGA_CIERRE = {
    "ANSI Clase I": "Según acuerdo entre usuario y fabricante (sin ensayo).",
    "ANSI Clase II": "0,5 % de la capacidad nominal.",
    "ANSI Clase III": "0,1 % de la capacidad nominal.",
    "ANSI Clase IV": "0,01 % de la capacidad nominal.",
    "ANSI Clase V": "5·10⁻⁴ ml/min de agua por pulgada de diámetro de puerto y por psi de ΔP.",
    "ANSI Clase VI": "Burbujas por minuto según el diámetro de puerto (asiento blando típico).",
    "Tight Shutoff": "Sin fuga visible en el ensayo (requisito del proyecto, p. ej. API 598 / ISO 5208 tasa A).",
}
REF_CIERRE = "ANSI/FCI 70-2 / IEC 60534-4"
T_ASIENTO_BLANDO_C = 200.0       # PTFE / RPTFE, límite práctico
T_SELLO_BALANCE_C = 232.0        # sello de balanceo de PTFE, límite práctico
DP_BALANCE = 1000.0              # kPa: por encima, con NPS ≥ 3, conviene trim balanceado
REF_BALANCE = "Práctica de la industria (manuales de fabricantes de válvulas de control)"
T_ELASTOMERO_C = 120.0           # asientos elastoméricos de mariposa concéntrica
V_TUBERIA_LIQ = 4.5              # m/s, práctica habitual para líneas de líquido


@dataclass
class Identificacion:
    proyecto: str = ""
    cliente: str = ""
    tag: str = ""
    servicio: str = ""
    documento: str = ""
    revision: str = "0"
    preparado: str = ""
    fecha: str = ""


@dataclass
class Instalacion:
    cuerpo: str = "globo"
    rating: int = 300
    nps_entrada: float = 4
    nps_salida: float = 4
    sch_entrada: str = "40"
    sch_salida: str = "40"
    ruido_permitido: float = 85.0
    conexion: str = "RF bridada"
    P_diseno: float | None = None     # kPa abs
    T_diseno: float | None = None     # K
    cierre: str = "ANSI Clase IV"


@dataclass
class CasoLiquido:
    nombre: str
    Q: float | None        # m³/h (volumétrico) o None
    W: float | None        # kg/h (másico) o None
    P1: float              # kPa abs
    P2: float
    T1: float              # K
    SG: float              # densidad relativa al agua a 15 °C
    mu: float              # Pa·s
    Pv: float              # kPa abs
    FL: float = 0.9        # factores del trim a la carrera de este caso
    Fd: float = 0.46
    Kc: float | None = None    # cavitación constante del trim; None = se usa el xFz típico de IEC 60534-8-4
    criterio: bool = True      # participa del criterio de selección de tamaño (no en transitorios)


@dataclass
class CasoCierre:
    """Condición de cierre (Tight Shutoff): válvula cerrada, sin caudal."""
    nombre: str
    P1: float              # kPa abs
    P2: float
    T1: float | None = None    # K

    @property
    def dP(self) -> float:
        return self.P1 - self.P2


CasoGas = CG.CasoGas
RuidoAerodinamico = CG.RuidoAerodinamico


@dataclass
class Dimensionamiento:
    casos: list                        # CasoLiquido (líquido) o CasoGas (gas, vapor, steam)
    Pc: float | None                   # kPa abs (solo líquidos)
    trim: str                          # clave de ESTILOS
    nps_valvula: float | None = None   # None = selección automática
    caracteristica: str = "isoporcentual"
    fluido: str | None = None          # nombre de la biblioteca de propiedades
    cierre: CasoCierre | None = None
    Cv_nominal: float | None = None    # None = típico del estilo
    c_sonido: float | None = None      # m/s; None = calculada o 1 400 m/s
    tipo: str = "liquido"              # liquido, gas, vapor, steam (ver compresible.TIPOS)
    ruido: RuidoAerodinamico = field(default_factory=RuidoAerodinamico)
    balanceado: bool | None = None     # trim balanceado (True) o desbalanceado (False); None = no aplica
    variante: str = ""                 # calidad / variante del fluido (fluido_servicio.variantes)
    agua_libre: str = ""               # Sí, No, Intermitente, Desconocida ("" = la que sugiere el fluido)
    salinidad_pct: float = 0.0         # % p/p NaCl eq. con que se corrigieron SG, μ y Pv (0 = sin corrección)
    puerto_mm: float | None = None     # diámetro del puerto certificado (None = estimado)
    carrera_mm: float | None = None    # carrera nominal certificada (None = estimada)

    @property
    def compresible(self) -> bool:
        return self.tipo != "liquido"


@dataclass
class Resultado:
    ident: Identificacion
    inst: Instalacion
    dim: Dimensionamiento
    informe: Informe
    salidas: list[dict]
    alertas: list[tuple[str, Alerta]]
    recomendaciones: list[tuple[str, str]]
    D1: float
    D2: float
    tp1: float
    tp2: float
    Cv_nominal: float
    rating_admisible: float | None = None   # kPa abs a T de diseño (grupo 1.1 referencial)
    P_diseno: float = 0.0
    T_diseno: float = 0.0
    curva: list[tuple[float, float]] = field(default_factory=list)
    materiales: object | None = None        # seleccion_materiales.ResultadoMateriales
    equipo: object | None = None            # actuadores.ResultadoEquipo (solapas 4, 5 y 6)

    @property
    def cuerpo(self):
        return CUERPOS[self.inst.cuerpo]

    @property
    def trim(self):
        return ESTILOS[self.dim.trim]

    @property
    def nps_valvula(self) -> float:
        return self.informe.d_pulg

    @property
    def geometria(self):
        """Tamaño del trim (puerto) y carrera del vástago, estimados o certificados."""
        from . import geometria as G
        from .estilos import kv_nominal
        d = self.nps_valvula
        DI = next((di for p, _, di in TAMANOS if abs(p - d) < 1e-6), None)
        return G.estimar(self.dim.trim, self.cuerpo.rotativa, d, self.Cv_nominal,
                         kv_nominal(self.trim, d) / 0.865, DI, self.dim.puerto_mm, self.dim.carrera_mm)

    def peor(self) -> Severidad:
        return max([a.severidad for _, a in self.alertas] or [Severidad.INFO])


def _area(d_mm: float) -> float:
    return math.pi * (d_mm / 1000) ** 2 / 4


def caudal_relativo(h: float, caracteristica: str, R: float) -> float:
    """Inversa de apertura_requerida: Cv/Cv_nominal para una carrera h (0–1)."""
    if h <= 0:
        return 0.0
    if caracteristica == "lineal":
        return 1 / R + (1 - 1 / R) * h
    if caracteristica == "isoporcentual":
        return R ** (h - 1)
    return math.sqrt(h)


def _tuberias_inst(inst: Instalacion):
    errores: list[Alerta] = []
    D1 = D2 = tp1 = tp2 = None
    try:
        D1 = tuberias.diametro_interior(inst.nps_entrada, inst.sch_entrada)
        tp1 = tuberias.espesor(inst.nps_entrada, inst.sch_entrada)
    except tuberias.ErrorTuberia as e:
        errores.append(Alerta("dato_tuberia", Severidad.ERROR, "Tubería de entrada no definida", str(e)))
    try:
        D2 = tuberias.diametro_interior(inst.nps_salida, inst.sch_salida)
        tp2 = tuberias.espesor(inst.nps_salida, inst.sch_salida)
    except tuberias.ErrorTuberia as e:
        errores.append(Alerta("dato_tuberia", Severidad.ERROR, "Tubería de salida no definida", str(e)))
    return D1, D2, tp1, tp2, errores


def _validar_factores(c, errores, gas: bool):
    if not 0.3 <= c.FL <= 1.0:
        errores.append(Alerta("dato_FL", Severidad.ERROR, "FL fuera de rango",
                              f"Caso {c.nombre}: FL = {_n(c.FL)}; el factor de recuperación está entre 0,3 y 1,0."))
    if not 0.01 <= c.Fd <= 1.0:
        errores.append(Alerta("dato_Fd", Severidad.ERROR, "Fd fuera de rango",
                              f"Caso {c.nombre}: Fd = {_n(c.Fd)}; el modificador de estilo está entre 0,01 y 1,0."))
    if gas and not 0.05 <= c.xT <= 1.0:
        errores.append(Alerta("dato_xT", Severidad.ERROR, "xT fuera de rango",
                              f"Caso {c.nombre}: xT = {_n(c.xT)}; el factor de caída de presión crítica está "
                              "entre 0,05 y 1,0."))


def calcular(ident: Identificacion, inst: Instalacion, dim: Dimensionamiento, mat=None, equipo=None) -> Resultado:
    """``mat`` (seleccion_materiales.ServicioMateriales) activa la selección de materiales; ``equipo``
    (actuadores.Equipo) el dimensionamiento del actuador, del posicionador y de los accesorios."""
    if dim.compresible:
        return _equipo(_calcular_compresible(ident, inst, dim, mat), equipo)
    errores: list[Alerta] = []
    try:
        D1 = tuberias.diametro_interior(inst.nps_entrada, inst.sch_entrada)
        tp1 = tuberias.espesor(inst.nps_entrada, inst.sch_entrada)
    except tuberias.ErrorTuberia as e:
        errores.append(Alerta("dato_tuberia", Severidad.ERROR, "Tubería de entrada no definida", str(e)))
    try:
        D2 = tuberias.diametro_interior(inst.nps_salida, inst.sch_salida)
        tp2 = tuberias.espesor(inst.nps_salida, inst.sch_salida)
    except tuberias.ErrorTuberia as e:
        errores.append(Alerta("dato_tuberia", Severidad.ERROR, "Tubería de salida no definida", str(e)))
    if not dim.casos:
        errores.append(Alerta("sin_casos", Severidad.ERROR, "Sin casos de operación",
                              "Active al menos un caso de operación."))
    for c in dim.casos:
        if not 0.3 <= c.FL <= 1.0:
            errores.append(Alerta("dato_FL", Severidad.ERROR, "FL fuera de rango",
                                  f"Caso {c.nombre}: FL = {_n(c.FL)}; el factor de recuperación está entre 0,3 y 1,0."))
        if not 0.01 <= c.Fd <= 1.0:
            errores.append(Alerta("dato_Fd", Severidad.ERROR, "Fd fuera de rango",
                                  f"Caso {c.nombre}: Fd = {_n(c.Fd)}; el modificador de estilo está entre 0,01 y 1,0."))
        if c.Kc is not None and not 0.05 <= c.Kc <= 1.0:
            errores.append(Alerta("dato_Kc", Severidad.ERROR, "Kc fuera de rango",
                                  f"Caso {c.nombre}: Kc = {_n(c.Kc)}; el coeficiente de cavitación está entre 0,05 y 1,0."))
        if c.SG <= 0:
            errores.append(Alerta("dato_rho", Severidad.ERROR, "Gravedad específica inválida",
                                  f"Caso {c.nombre}: la gravedad específica debe ser mayor que cero."))
        if c.mu <= 0:
            errores.append(Alerta("dato_nu", Severidad.ERROR, "Viscosidad inválida",
                                  f"Caso {c.nombre}: la viscosidad debe ser mayor que cero."))
    if dim.cierre is not None and dim.cierre.P2 >= dim.cierre.P1:
        errores.append(Alerta("dato_cierre", Severidad.ERROR, "Condición de cierre inválida",
                              "En el caso Tight Shutoff la presión de entrada debe ser mayor que la de salida."))
    if errores:
        raise ErrorDatos(errores)

    cuerpo = CUERPOS[inst.cuerpo]
    estilo = replace(ESTILOS[dim.trim], caracteristica=dim.caracteristica)
    tamanos = tuple(p for p, _, _ in TAMANOS if cuerpo.nps_min <= p <= cuerpo.nps_max)
    sel = Seleccion(estilo, d_pulg=dim.nps_valvula,
                    Kv_nominal=dim.Cv_nominal * 0.865 if dim.Cv_nominal else None,
                    D1_mm=D1, D2_mm=D2, FL=dim.casos[0].FL, Fd=dim.casos[0].Fd, xT=estilo.xT,
                    tp_mm=tp2, c_liquido=dim.c_sonido,
                    limite_ruido=inst.ruido_permitido, tamanos=tamanos, An=cuerpo.An,
                    verificar_clase=False)
    casos = []
    for c in dim.casos:
        rho = c.SG * RHO_AGUA_15C
        casos.append(Caso(c.nombre, Liquido(P1=c.P1, P2=c.P2, T1=c.T1, rho1=rho, Pv=c.Pv, Pc=dim.Pc,
                                            nu=c.mu / rho, Q=c.Q, W=c.W), dim.fluido,
                          FL=c.FL, Fd=c.Fd, Kc=c.Kc, criterio=c.criterio))
    inf = dimensionar(casos, sel)

    salidas = []
    for c, rc in zip(dim.casos, inf.casos):
        e, r, d = rc.caso.estado, rc.resultado, rc.datos
        Q = r.extra["Q"]
        Kc = d["Kc"]
        salidas.append({
            "Cv": r.Cv, "Kv": r.Kv, "Kapp": d["xF"], "Kc": Kc, "Kc_estimado": d["Kc_estimado"],
            "xFzp1": d["xFzp1"], "xFz_estimado": d["xFz_estimado"],
            "dPinc": d["xFzp1"] * (e.P1 - e.Pv),
            "FL": c.FL, "Fd": c.Fd, "dP": e.P1 - e.P2,
            "dP_P1": (e.P1 - e.P2) / e.P1, "dPchoked": r.extra["dPchoked"],
            "dPcav": Kc * (e.P1 - e.Pv), "FF": r.extra["FF"], "FP": r.FP, "FLP": r.extra["FLP"],
            "mu": c.mu, "nu": e.nu, "D1": D1, "D2": D2, "Rev": r.Rev, "FR": r.FR, "rho": e.rho1,
            "Q": Q, "W": Q * e.rho1, "Lp": d.get("ruido_LpAe1m"),
            "v1": Q / 3600 / _area(D1), "v2": Q / 3600 / _area(D2),
            "v_valvula": d.get("v_salida_valvula"), "apertura": rc.apertura,
            "condicion": d.get("regimen", ""), "bloqueado": r.bloqueado, "regimen_flujo": r.regimen,
            "calidad": d.get("calidad_salida"), "sigma": d.get("sigma"),
        })

    alertas = [(rc.caso.nombre, a) for rc in inf.casos for a in rc.alertas]
    alertas = [("General", a) for a in inf.alertas_generales] + alertas

    P_ops = [c.P1 for c in dim.casos] + ([dim.cierre.P1] if dim.cierre else [])
    T_ops = [c.T1 for c in dim.casos] + ([dim.cierre.T1] if dim.cierre and dim.cierre.T1 else [])
    P_d = inst.P_diseno or max(P_ops)
    T_d = inst.T_diseno or max(T_ops)
    mres = _materiales(mat, inst, dim, salidas, P_d, T_d)
    generales, rating_adm = _verificaciones(inst, cuerpo, inf, dim, salidas, P_d, T_d, D1, D2, mres)
    alertas = [("General", a) for a in generales] + alertas
    if mres is not None:
        alertas += [("Materiales", a) for a in mres.todas_las_alertas()]
    alertas.sort(key=lambda t: -t[1].severidad)

    Cv_nom = inf.Kv_nominal / 0.865
    curva = [(h, Cv_nom * caudal_relativo(h / 100, estilo.caracteristica, estilo.rangeabilidad))
             for h in range(0, 101, 2)]
    res = Resultado(ident, inst, dim, inf, salidas, alertas, [], D1, D2, tp1, tp2, Cv_nom,
                    rating_adm, P_d, T_d, curva, mres)
    res.recomendaciones = recomendaciones(res)
    _carreras(res)
    return _equipo(res, equipo)


def _equipo(res: Resultado, equipo) -> Resultado:
    """Actuador, posicionador y accesorios con los resultados de las solapas 1 a 3."""
    if equipo is None:
        return res
    from . import actuadores
    res.equipo = actuadores.evaluar(res, equipo)
    res.alertas += res.equipo.todas_las_alertas()
    res.alertas.sort(key=lambda t: -t[1].severidad)
    return res


def _carreras(res: Resultado):
    geo = res.geometria
    for s in res.salidas:
        s["carrera"] = geo.operacion(s["apertura"])


def _materiales(mat, inst, dim, salidas, P_d, T_d):
    if mat is None:
        return None
    from types import SimpleNamespace
    from . import seleccion_materiales as SM
    ctx = SM.contexto(SimpleNamespace(inst=inst, dim=dim, salidas=salidas, P_diseno=P_d, T_diseno=T_d))
    return SM.seleccionar(SM.completar_desde_calculo(mat, dim, salidas, ctx), ctx)


def _rating_referencial(inst, P_d, T_d, P_barg, T_C) -> Alerta:
    """Clase verificada con acero al carbono (grupo 1.1) cuando no hay material definido."""
    r = asme_b16_34.rating("1.1", inst.rating, T_C)
    rating_adm = None if r is None else r * 100 + 101.325
    ref = "ASME B16.34, Tabla 2-1.1 (clase estándar)"
    if r is None:
        return Alerta("rating_fuera_tabla", Severidad.ADVERTENCIA, "Temperatura fuera de la tabla de clase",
                      f"La temperatura de diseño ({fT(T_d)}) supera la tabla de referencia de "
                      f"acero al carbono ({fT(538 + 273.15)}). La clase debe verificarse con el material definitivo.",
                      referencia=ref)
    if P_barg > r:
        minima = asme_b16_34.clase_minima("1.1", P_barg, T_C)
        return Alerta("clase_insuficiente", Severidad.CRITICA, f"Rating CL{inst.rating} insuficiente",
                      f"Con acero al carbono (grupo 1.1, referencia) la clase {inst.rating} admite "
                      f"{fP(rating_adm)} a {fT(T_d)} y la presión de diseño es {fP(P_d)}.",
                      remedios=[f"Usar rating CL{minima}." if minima else "Ninguna clase estándar alcanza: "
                                "revise las condiciones de diseño."], referencia=ref)
    return Alerta("rating_referencial", Severidad.INFO, "Rating verificado en forma referencial",
                  f"CL{inst.rating} admite {fP(rating_adm)} a {fT(T_d)} con acero al carbono "
                  f"(grupo 1.1); diseño {fP(P_d)}. Defina el material del cuerpo en la solapa "
                  "3-Materiales para verificar con su grupo real.", referencia=ref)


def _verificaciones(inst, cuerpo, inf, dim, salidas, P_d, T_d, D1, D2, mres=None):
    al: list[Alerta] = []
    d = inf.d_pulg
    P_barg = (P_d - 101.325) / 100
    T_C = T_d - 273.15
    m_cuerpo = mres.cuerpo if mres is not None else None
    if m_cuerpo is not None and m_cuerpo.grupo:
        # Clase de presión con el grupo del material del cuerpo (solapa 3)
        g = m_cuerpo.grupo
        r = asme_b16_34.rating(g, inst.rating, T_C)
        rating_adm = None if r is None else r * 100 + 101.325
        ref = f"ASME B16.34, Tabla 2-{g} (clase estándar)"
        if r is None:
            al.append(Alerta("rating_fuera_tabla", Severidad.CRITICA, "Temperatura fuera de la tabla de clase",
                             f"La temperatura de diseño ({fT(T_d)}) supera la tabla del grupo {g} "
                             f"({m_cuerpo.nombre}).", referencia=ref))
        elif P_barg > r:
            minima = asme_b16_34.clase_minima(g, P_barg, T_C)
            al.append(Alerta("clase_insuficiente", Severidad.CRITICA, f"Rating CL{inst.rating} insuficiente",
                             f"Con {m_cuerpo.nombre} (grupo {g}) la clase {inst.rating} admite {fP(rating_adm)} a "
                             f"{fT(T_d)} y la presión de diseño es {fP(P_d)}.",
                             remedios=[f"Usar rating CL{minima}." if minima else "Ninguna clase estándar alcanza: "
                                       "revise las condiciones de diseño o el material."], referencia=ref))
        else:
            al.append(Alerta("rating_verificado", Severidad.INFO, "Rating verificado con el material del cuerpo",
                             f"CL{inst.rating} con {m_cuerpo.nombre} (grupo {g}) admite {fP(rating_adm)} a "
                             f"{fT(T_d)}; diseño {fP(P_d)}.", referencia=ref))
    elif m_cuerpo is not None:
        rating_adm = None
        al.append(Alerta("mat_no_b1634", Severidad.INFO, "Rating a definir por el fabricante",
                         f"{m_cuerpo.nombre} no figura en ASME B16.34: el rating de CL{inst.rating} lo confirma el "
                         "fabricante."))
    else:
        r = asme_b16_34.rating("1.1", inst.rating, T_C)
        rating_adm = None if r is None else r * 100 + 101.325
        al.append(_rating_referencial(inst, P_d, T_d, P_barg, T_C))
    if inst.P_diseno is None or inst.T_diseno is None:
        al.append(Alerta("diseno_por_operacion", Severidad.INFO, "Condiciones de diseño supuestas",
                         "No se ingresaron presión y/o temperatura de diseño: se usaron las máximas de "
                         "operación."))

    # Conexión a proceso
    con = inst.conexion
    if con == "Wafer" and not inst.cuerpo.startswith("mariposa"):
        al.append(Alerta("conexion_incompatible", Severidad.ADVERTENCIA, "Conexión wafer no habitual",
                         f"La conexión wafer es propia de válvulas mariposa; para un cuerpo "
                         f"{cuerpo.nombre.lower()} use bridada o sin bridas.",
                         remedios=["Cambiar a RF bridada o sin bridas (flangeless)."]))
    if con in ("FNPT", "MNPT", "SWE") and d > 2:
        al.append(Alerta("conexion_incompatible", Severidad.ADVERTENCIA, f"Conexión {con} en {_n(d)}\"",
                         f"Las conexiones roscadas y de enchufe soldado se usan hasta 2\". La válvula "
                         f"seleccionada es de {_n(d)}\".",
                         remedios=["Usar bridada o soldada a tope (BWE)."], referencia="ASME B16.34 / B16.11"))
    if con in ("FNPT", "MNPT") and inst.rating > 600:
        al.append(Alerta("conexion_incompatible", Severidad.ADVERTENCIA, "Rosca NPT en alta presión",
                         "Las uniones roscadas no son recomendables por encima de CL600 ni en servicios "
                         "cíclicos o peligrosos.", remedios=["Usar SWE o BWE."]))
    if con == "FF bridada" and inst.rating > 150:
        al.append(Alerta("conexion_incompatible", Severidad.ADVERTENCIA, "Brida cara plana con rating alto",
                         "Las bridas de cara plana (FF) se usan en CL150 para unir con bridas de fundición o "
                         "no metálicas.", remedios=["Usar RF o RTJ bridada."], referencia="ASME B16.5"))
    if con == "RTJ bridada" and inst.rating < 600:
        al.append(Alerta("conexion_info", Severidad.INFO, "RTJ en rating bajo",
                         "La junta de anillo (RTJ) es habitual desde CL600 o en servicios críticos; en "
                         f"CL{inst.rating} lo usual es RF."))
    if con == "SCH XXS BWE" and inst.rating < 1500:
        al.append(Alerta("conexion_info", Severidad.INFO, "Extremos XXS en rating bajo",
                         "Los extremos soldados XXS son propios de servicios de muy alta presión."))

    # Tamaño de válvula frente a tubería y al estilo
    nps_linea = min(inst.nps_entrada, inst.nps_salida)
    if d > nps_linea:
        al.append(Alerta("valvula_mayor_linea", Severidad.ADVERTENCIA, "Válvula mayor que la tubería",
                         f"La válvula ({_n(d)}\") es mayor que la tubería ({_n(nps_linea)}\"). Revise el "
                         "diámetro de la línea o el estilo elegido."))
    elif d < 0.5 * nps_linea:
        al.append(Alerta("valvula_chica_linea", Severidad.INFO, "Válvula mucho menor que la tubería",
                         f"La válvula ({_n(d)}\") es menor que la mitad de la línea ({_n(nps_linea)}\"): "
                         "los reductores reducen la capacidad (FP) y deben verificarse por velocidad y "
                         "soportes."))
    if not cuerpo.nps_min <= d <= cuerpo.nps_max:
        al.append(Alerta("tamano_estilo", Severidad.ADVERTENCIA, "Diámetro poco habitual para el estilo",
                         f"Las válvulas {cuerpo.nombre.lower()} se fabrican habitualmente entre "
                         f"{_n(cuerpo.nps_min)}\" y {_n(cuerpo.nps_max)}\"."))

    # Validez de las ecuaciones de IEC 60534-2-1 (C/d² < 0,04 con Kv y d en mm)
    rel = max(x["Kv"] for x in salidas) / (d * 25.4) ** 2
    if rel > 0.04:
        al.append(Alerta("fuera_validez_cd2", Severidad.ADVERTENCIA, "Coeficiente alto para el diámetro",
                         f"Kv/d² = {_n(rel, 3)} supera 0,04 (Cv/d² > 0,047 con d en mm): fuera del rango de "
                         "validez de las ecuaciones de IEC 60534-2-1. El resultado es aproximado y la válvula "
                         "está cerca de su capacidad máxima.",
                         remedios=["Seleccionar un diámetro de válvula mayor."],
                         referencia="IEC 60534-2-1:2011, cláusula 1 (alcance)"))

    # Clase de cierre y balanceo del obturador
    al += _verificar_cierre(inst, cuerpo, T_d)
    al += _verificar_balance(inst, cuerpo, dim, T_d, d)

    # Velocidad en tuberías (líquidos; en compresibles se evalúa el número de Mach)
    for donde, clave in (() if dim.compresible else (("entrada", "v1"), ("salida", "v2"))):
        v = max(s[clave] for s in salidas)
        if v > V_TUBERIA_LIQ:
            inten = min(100.0, (v / V_TUBERIA_LIQ - 1) * 100)
            al.append(Alerta("velocidad_tuberia", Severidad.ADVERTENCIA, f"Velocidad alta en la tubería de {donde}",
                             f"Velocidad máxima en la tubería de {donde}: {fV(v)} (práctica habitual "
                             f"≤ {fV(V_TUBERIA_LIQ, 1)} en líquidos). Favorece erosión, ruido y golpe de ariete.",
                             inten, "leve" if inten < 33 else "moderada" if inten < 66 else "severa",
                             ["Revisar el diámetro de la tubería.",
                              f"Si hay sólidos en suspensión, limitar a unos {fV(3.0, 1)}."]))
    # Kc dado por el usuario frente a la aplicación
    return al, rating_adm


def _guia_obturador(dim, dP_max, nps) -> str:
    """Texto de guía y balanceo del obturador para el informe (cuerpos de vástago deslizante)."""
    conviene = dP_max > DP_BALANCE and nps >= 3
    jaula = "jaula" in dim.trim or "multietapa" in dim.trim
    base = ("Obturador guiado por jaula" if jaula else
            "Obturador contorneado guiado superior (o superior y por puerto en diámetros grandes)")
    if dim.balanceado is None:
        return base + (", balanceado (reduce la fuerza del actuador; verificar que el sello de balanceo "
                       "cumpla la clase de cierre)." if conviene and jaula else ".")
    if dim.balanceado:
        return (base + ", balanceado (elegido). Verificar que el sello de balanceo cumpla la clase de cierre "
                "y la temperatura." + ("" if conviene else " Con esta ΔP y diámetro el balanceo no es "
                                       "imprescindible: un trim desbalanceado cierra mejor."))
    return (base + ", desbalanceado (elegido)." + (" Con esta ΔP y diámetro conviene balanceado para reducir "
                                                    "el empuje del actuador." if conviene else ""))


def fuerza_desbalance(dP_kPa: float, d_puerto_pulg: float) -> float:
    """Fuerza de desbalance orientativa [N] sobre un obturador no balanceado: ΔP·π·d²/4."""
    return dP_kPa * 1000 * math.pi / 4 * (d_puerto_pulg * 0.0254) ** 2


def _verificar_balance(inst, cuerpo, dim, T_d, d) -> list[Alerta]:
    if cuerpo.rotativa or dim.balanceado is None:
        return []
    al = []
    dP = max([c.P1 - c.P2 for c in dim.casos] + ([dim.cierre.dP] if dim.cierre else []))
    jaula = "jaula" in dim.trim or "multietapa" in dim.trim
    if not dim.balanceado:
        if dP > DP_BALANCE and d >= 3:
            F = fuerza_desbalance(dP, d)
            al.append(Alerta("desbalance_fuerza", Severidad.ADVERTENCIA, "Fuerza de desbalance alta",
                             f"Con trim desbalanceado, ΔP máxima {fP(dP)} y válvula de {_n(d)}\" la fuerza "
                             f"del fluido sobre el obturador es del orden de {_n(F / 1000, 1)} kN "
                             f"({_n(F / 4.44822, 0)} lbf), estimada con ΔP·π·d²/4 y el puerto igual al "
                             "diámetro de la válvula. El actuador debe vencerla para cerrar y modular: "
                             "resulta grande y la estabilidad cerca del asiento empeora.",
                             remedios=["Usar trim balanceado (obturador guiado por jaula con sello de balanceo).",
                                       "Confirmar con el fabricante el diámetro de puerto real y el empuje del "
                                       "actuador."],
                             referencia=REF_BALANCE))
        return al
    if not jaula:
        al.append(Alerta("balance_sin_jaula", Severidad.ADVERTENCIA, "Trim balanceado sin jaula",
                         "Los obturadores balanceados son, casi siempre, guiados por jaula: el sello de "
                         "balanceo trabaja contra el interior de la jaula. El trim elegido es de obturador "
                         "contorneado.",
                         remedios=["Elegir un trim de jaula (4 ventanas, multiorificio o multietapa).",
                                   "O confirmar con el fabricante que ofrece el balanceo en este trim."],
                         referencia=REF_BALANCE))
    if CIERRES.index(inst.cierre) >= 4:
        al.append(Alerta("balance_cierre", Severidad.ADVERTENCIA, "Trim balanceado y clase de cierre alta",
                         f"El sello de balanceo agrega una vía de fuga además del asiento. Con trim "
                         f"balanceado la clase habitual es IV; la {inst.cierre.replace('ANSI ', '').lower()}"
                         " o mayor requiere un sello de balanceo especial (o asiento blando) y debe "
                         "confirmarse con el fabricante.",
                         remedios=["Pedir al fabricante la clase de cierre garantizada con el sello de balanceo.",
                                   "Si la ΔP lo permite, usar trim desbalanceado para clase V o VI."],
                         referencia=REF_CIERRE))
    if T_d - 273.15 > T_SELLO_BALANCE_C:
        al.append(Alerta("balance_temperatura", Severidad.ADVERTENCIA, "Sello de balanceo y temperatura",
                         f"La temperatura de diseño ({fT(T_d)}) supera el límite práctico del sello de "
                         f"balanceo de PTFE (unos {fT(T_SELLO_BALANCE_C + 273.15)}).",
                         remedios=["Especificar sello de balanceo de grafito o metálico para alta temperatura.",
                                   "Confirmar con el fabricante la clase de cierre que se obtiene con ese sello."],
                         referencia=REF_BALANCE))
    return al


def _verificar_cierre(inst, cuerpo, T_d) -> list[Alerta]:
    al = []
    c = inst.cierre
    T_C = T_d - 273.15
    n = CIERRES.index(c)
    blando = False
    if inst.cuerpo in ("globo", "angulo"):
        blando = n >= 5
        if c == "Tight Shutoff":
            al.append(Alerta("cierre_estilo", Severidad.ADVERTENCIA, "Cierre hermético en válvula de globo",
                             "Una válvula de control de globo no suele garantizar cierre hermético (sin fuga).",
                             remedios=["Usar asiento blando clase VI o una válvula de bloqueo en serie."],
                             referencia=REF_CIERRE))
    elif inst.cuerpo == "globo_liner":
        blando = True
    elif inst.cuerpo.startswith("bola") or inst.cuerpo == "tapon_excentrico":
        blando = n >= 5
        if inst.cuerpo in ("bola_paso_completo", "bola_paso_reducido") and inst.rating > 600:
            al.append(Alerta("bola_flotante_presion", Severidad.ADVERTENCIA, "Bola flotante en clase alta",
                             f"En una bola flotante la presión empuja la bola contra el asiento de aguas abajo; con "
                             f"CL{inst.rating} el par de maniobra, el desgaste del asiento y el riesgo de fuga son "
                             "altos.", remedios=["Usar bola trunnion (montada en muñón) para CL900 y superiores.",
                                                 "Si se mantiene flotante, pedir al fabricante el par y la carga "
                                                 "admisible del asiento a la ΔP de cierre."],
                             referencia="API 6D / ISO 17292"))
    elif inst.cuerpo == "mariposa":
        blando = n >= 4
        if n < 4:
            al.append(Alerta("cierre_info", Severidad.INFO, "Mariposa concéntrica",
                             "La mariposa concéntrica con asiento metálico no supera la clase III–IV."))
    elif inst.cuerpo == "mariposa_doble":
        blando = n >= 5
    elif inst.cuerpo == "mariposa_triple":
        blando = False
    if blando:
        limite = T_ELASTOMERO_C if inst.cuerpo == "mariposa" else T_ASIENTO_BLANDO_C
        if T_C > limite:
            al.append(Alerta("cierre_temperatura", Severidad.CRITICA, "Asiento blando fuera de temperatura",
                             f"La clase {c} en un cuerpo {cuerpo.nombre.lower()} requiere asiento blando o "
                             f"revestimiento, cuyo límite práctico es unos {fT(limite + 273.15)}. La temperatura de "
                             f"diseño es {fT(T_d)}.",
                             remedios=["Usar asiento metálico clase V (globo con asiento lapeado) o una "
                                       "mariposa triple excéntrica de cierre metal-metal.",
                                       "Verificar el material del asiento con el fabricante."],
                             referencia=REF_CIERRE))
    return al


def recomendaciones(res: Resultado) -> list[tuple[str, str]]:
    """Características óptimas de la válvula a partir de los resultados (texto para el informe)."""
    if res.dim.compresible:
        return recomendaciones_compresible(res)
    s = res.salidas
    inst, dim = res.inst, res.dim
    cuerpo, trim = res.cuerpo, res.trim
    rec: list[tuple[str, str]] = []
    cav = [x for x in s if x["condicion"].startswith("cavitación") and "incipiente" not in x["condicion"]]
    flash = [x for x in s if x["condicion"] == "flashing"]
    Kapp = max(x["Kapp"] for x in s)
    Kc = min(x["Kc"] for x in s)
    FL2 = min(c.FL for c in dim.casos) ** 2
    dP_max = max(x["dP"] for x in s)
    Cv_max = max(x["Cv"] for x in s)
    h = [x["apertura"] for x in s]

    # Coeficiente y tamaño
    rec.append(("Coeficiente de caudal",
                f"Cv requerido máximo {_n(Cv_max, 1)}. Se recomienda una válvula con Cv nominal de al "
                f"menos {_n(Cv_max / 0.85, 1)} (apertura ≤ 85 % en el caso máximo). Con la válvula "
                f"de {_n(res.nps_valvula)}\" (Cv nominal {_n(res.Cv_nominal, 1)}) la apertura queda entre "
                f"{_n(min(h) * 100, 0)} % y {_n(max(h) * 100, 0)} %."))
    # Cuerpo
    if flash:
        txt = ("Hay flashing: se recomienda cuerpo angular con flujo que tiende a cerrar, descarga directa "
               "a recipiente o a tubería de mayor diámetro, y cuerpo de material resistente a la erosión.")
    elif cav and Kapp >= FL2 * 0.9 and cuerpo.rotativa:
        txt = (f"La cavitación es intensa para un cuerpo rotativo (FL² = {_n(FL2, 3)}). Se recomienda "
               "cambiar a globo con internos anticavitación.")
    else:
        txt = f"Cuerpo {cuerpo.nombre.lower()} adecuado para el servicio, rating CL{inst.rating}, conexión {inst.conexion}."
    rec.append(("Estilo de cuerpo", txt))
    # Trim y jaula
    grado = ANTICAVITACION.get(dim.trim, 0)
    if flash:
        trim_txt = ("Los internos anticavitación no eliminan el flashing. Usar obturador y asiento "
                    "endurecidos (recubrimiento de estelita o carburo de tungsteno).")
    elif not cav:
        trim_txt = (f"Sin cavitación (Kapp {_n(Kapp, 3)} < Kc {_n(Kc, 3)}): internos estándar "
                    f"({trim.nombre.lower()}).")
    elif Kapp >= FL2:
        trim_txt = ("Cavitación con flujo bloqueado: se requieren internos multietapa, o repartir la caída "
                    "de presión entre la válvula y una restricción aguas abajo.")
    elif grado == 0:
        trim_txt = (f"Kapp {_n(Kapp, 3)} supera Kc {_n(Kc, 3)}: se recomienda jaula anticavitación de "
                    "orificios pequeños (etapa simple) o multietapa si la intensidad es severa, con obturador "
                    "y asiento endurecidos.")
    else:
        trim_txt = (f"Internos anticavitación seleccionados. Verifique con el fabricante que el Kc certificado "
                    f"del trim sea mayor que Kapp = {_n(Kapp, 3)}.")
    rec.append(("Internos (trim) y jaula", trim_txt))
    # Guía y obturador
    if cuerpo.rotativa:
        guia = f"{cuerpo.guia}. Disco o bola con eje de diámetro suficiente para el par de cierre a ΔP máxima."
    else:
        guia = _guia_obturador(dim, dP_max, res.nps_valvula)
    rec.append(("Tipo de guía y obturador", guia))
    # Asiento
    n = CIERRES.index(inst.cierre)
    if inst.cuerpo == "mariposa_triple":
        asiento = "Asiento metálico de sello laminado (cierre metal-metal)."
    elif inst.cuerpo == "globo_liner":
        asiento = "Asiento y revestimiento de PFA/PTFE."
    elif n >= 5:
        asiento = "Asiento blando (PTFE/RPTFE) o metálico especial para la clase solicitada."
    elif n == 4:
        asiento = "Asiento metálico lapeado con carga de asiento alta (clase V)."
    else:
        asiento = "Asiento metálico."
    rec.append(("Asiento y clase de cierre", f"{asiento} {inst.cierre}: fuga admisible "
                f"{FUGA_CIERRE[inst.cierre]}"))
    # Característica
    dps = [x["dP"] for x in s]
    if len(s) > 1 and min(dps) > 0 and max(dps) / min(dps) > 2:
        car = ("La caída de presión varía mucho entre casos: se recomienda característica isoporcentual.")
    else:
        car = ("La caída de presión varía poco entre casos (menos del doble): la característica lineal da "
               "una ganancia más uniforme.")
    rec.append(("Característica inherente", car + f" Seleccionada: {dim.caracteristica}."))
    # Ruido
    Lp = [x["Lp"] for x in s if x["Lp"] is not None]
    if Lp:
        rec.append(("Ruido", f"Nivel máximo estimado {_n(max(Lp), 1)} dB(A) a 1 m (límite "
                    f"{_n(inst.ruido_permitido, 0)} dB(A))."
                    + (" Cumple." if max(Lp) <= inst.ruido_permitido else " No cumple: aplicar las medidas "
                       "contra la cavitación y el ruido indicadas en las alertas.")))
    if dim.cierre is not None:
        dp_cierre = f"{fdP(dim.cierre.dP)} (caso {dim.cierre.nombre})"
    else:
        dp_cierre = (f"{fdP(max(x['dP'] for x in s))} (máxima de operación; cargue el caso Tight Shutoff "
                     "con la presión de cierre real)")
    rec.append(("Actuador",
                "El cálculo de fuerza o par del actuador se incorporará en una próxima versión. Debe "
                f"vencer la ΔP de cierre {dp_cierre} y asegurar la carga de asiento de la clase "
                f"{inst.cierre}."))
    return rec


# ---------------------------------------------------------------------------
# Gas, vapor y vapor de agua
# ---------------------------------------------------------------------------
def _calcular_compresible(ident: Identificacion, inst: Instalacion, dim: Dimensionamiento, mat=None) -> Resultado:
    D1, D2, tp1, tp2, errores = _tuberias_inst(inst)
    if not dim.casos:
        errores.append(Alerta("sin_casos", Severidad.ERROR, "Sin casos de operación",
                              "Cargue al menos un caso de operación con caudal."))
    for c in dim.casos:
        _validar_factores(c, errores, gas=True)
        if c.W is None and c.QN is None:
            errores.append(Alerta("dato_caudal", Severidad.ERROR, "Falta el caudal", f"Caso {c.nombre}."))
    if dim.ruido.trim not in CG.TRIMS_RUIDO:
        errores.append(Alerta("dato_trim_ruido", Severidad.ERROR, "Trim para ruido no reconocido", dim.ruido.trim))
    if dim.ruido.Rn <= 0:
        errores.append(Alerta("dato_Rn", Severidad.ERROR, "Distancia Rn inválida",
                              "La distancia para el ruido debe ser mayor que cero."))
    if dim.cierre is not None and dim.cierre.P2 >= dim.cierre.P1:
        errores.append(Alerta("dato_cierre", Severidad.ERROR, "Condición de cierre inválida",
                              "En el caso Tight Shutoff la presión de entrada debe ser mayor que la de salida."))
    if errores:
        raise ErrorDatos(errores)
    fluido = "Agua / vapor de agua" if dim.tipo == "steam" else dim.fluido
    estados = [CG.resolver_estado(c, dim.tipo, fluido) for c in dim.casos]

    cuerpo = CUERPOS[inst.cuerpo]
    estilo = replace(ESTILOS[dim.trim], caracteristica=dim.caracteristica)
    tamanos = tuple(p for p, _, _ in TAMANOS if cuerpo.nps_min <= p <= cuerpo.nps_max)
    c0 = dim.casos[0]
    sel = Seleccion(estilo, d_pulg=dim.nps_valvula,
                    Kv_nominal=dim.Cv_nominal * 0.865 if dim.Cv_nominal else None,
                    D1_mm=D1, D2_mm=D2, FL=c0.FL, Fd=c0.Fd, xT=c0.xT, tp_mm=tp2,
                    limite_ruido=inst.ruido_permitido, tamanos=tamanos, calcular_ruido=False,
                    verificar_clase=False)
    casos = [Caso(c.nombre, CG.estado_gas(c, e), fluido, FL=c.FL, Fd=c.Fd, xT=c.xT, criterio=c.criterio)
             for c, e in zip(dim.casos, estados)]
    inf = dimensionar(casos, sel)

    d_mm = inf.d_pulg * 25.4
    A_nom = _area(d_mm) * 1e6
    A_out = dim.ruido.area_salida or A_nom
    d_out = math.sqrt(4 * A_out / math.pi)
    salidas, alertas = [], []
    if dim.ruido.area_salida and not 0.2 <= A_out / A_nom <= 1.6:
        alertas.append(("General", Alerta(
            "area_salida_rango", Severidad.ADVERTENCIA, "Área de salida fuera del rango esperado",
            f"El área de salida ingresada ({_n(A_out, 0)} mm² = {_n(A_out / 645.16, 2)} in²) es "
            f"{_n(A_out / A_nom, 2)} veces el área del diámetro nominal de la válvula "
            f"({_n(A_nom, 0)} mm² = {_n(A_nom / 645.16, 2)} in²). Verifique la unidad seleccionada.",
            remedios=["Revisar la unidad del área (mm², cm² o in²).",
                             "Dejar el campo en blanco para usar el área del diámetro nominal."])))
    for c, e, rc in zip(dim.casos, estados, inf.casos):
        r, x = rc.resultado, rc.resultado.extra
        v = replace(inf.valvula, FL=c.FL, Fd=c.Fd, xT=c.xT)
        FLP = factor_FLP(r.Kv, v)
        W = x["W"]
        Q1 = W / e.rho1                       # m³/h reales a la entrada
        Q2 = W / e.rho2
        c1 = CG.sonido(e.gamma, c.P1, e.rho1)
        c2 = CG.sonido(e.gamma, c.P2, e.rho2)
        v1 = Q1 / 3600 / _area(D1)
        v2 = Q2 / 3600 / _area(D2)
        v_out = Q2 / 3600 / (A_out * 1e-6)
        sonico = v_out > c2
        if sonico:
            # Un gas no supera la velocidad del sonido en la sección mínima: la salida se bloquea
            # a Mach 1 y la presión en ella sube por encima de P2.
            A_min = Q2 / 3600 / c2 * 1e6
            al_sonico = Alerta(
                "salida_sonica", Severidad.CRITICA, "Flujo sónico en la salida de la válvula",
                f"Con P2 y el área de salida usada ({_n(A_out, 0)} mm²) la velocidad sería "
                f"{_n(v_out, 0)} m/s, mayor que la del sonido ({_n(c2, 0)} m/s). La salida queda bloqueada "
                f"a Mach 1 y se informa v = c. Área mínima para salida subsónica: {_n(A_min, 0)} mm² "
                f"({_n(A_min / 645.16, 2)} in²).", 100.0, "severa",
                ["Verificar el área de salida y su unidad.",
                 "Seleccionar una válvula de mayor diámetro o con salida expandida.",
                 "Repartir la caída de presión en etapas."],
                "IEC 60534-8-3 (Mach en la salida de la válvula ≤ 1)")
            v_out = c2
        tub_sonica = v2 > c2
        if tub_sonica:
            al_tub = Alerta(
                "salida_sonica", Severidad.CRITICA, "Flujo sónico en la tubería aguas abajo",
                f"Con P2 la velocidad en la tubería de salida sería {_n(v2, 0)} m/s, mayor que la del sonido "
                f"({_n(c2, 0)} m/s): la tubería no puede conducir el caudal a esa presión. Se informa Mach 1.",
                100.0, "severa", ["Aumentar el diámetro de la tubería aguas abajo.",
                                  "Revisar el caudal y la presión de salida."],
                "IEC 60534-8-3")
            v2 = c2
        FL_eff = FLP / r.FP
        # Ruido con el trim elegido y nivel mínimo de trim de bajo ruido que cumple el límite
        niveles = {}
        for k, (_, Fd_k) in CG.TRIMS_RUIDO.items():
            try:
                niveles[k] = CG.ruido_caso(W, c, e, r.Kv, FL_eff, Fd_k or c.Fd, d_out, D2, tp2, dim.ruido.Rn)
            except (ValueError, ZeroDivisionError, OverflowError):
                niveles[k] = None
        rr = niveles.get(dim.ruido.trim)
        requerido = next((CG.NIVEL_CORTO[k] for k, n in niveles.items()
                          if n is not None and n["LpAe1m"] <= inst.ruido_permitido),
                         "Multietapa o silenciador")
        al = [a for a in rc.alertas if a.codigo not in ("mach_salida", "ruido_no_calculado")]
        if rr is None:
            al.append(Alerta("ruido_no_calculado", Severidad.INFO, "Ruido no calculado",
                             "No se pudo estimar el ruido con IEC 60534-8-3 para estas condiciones."))
        else:
            al += ruido.evaluar_ruido(rr["LpAe1m"], True, inst.ruido_permitido)
            r.memoria.agregar("—", "Predicción de ruido " + ruido.REF8_3, float("nan"))
            r.memoria.pasos.extend(rr["memoria"].pasos)
        al += CG.alertas_velocidad(v_out / c2, v1 / c1, v2 / c2, dim.tipo)
        if sonico:
            al = [a for a in al if a.codigo != "mach_salida"] + [al_sonico]
        if tub_sonica:
            al.append(al_tub)
        alertas += [(c.nombre, a) for a in al]
        rc.alertas = al
        salidas.append({
            "Cv": r.Cv, "Kv": r.Kv, "apertura": rc.apertura, "FL": c.FL, "Fd": c.Fd, "xT": c.xT,
            "W": W, "QN": W / CG.densidad_normal(e.M), "Q1": Q1,
            "dP": c.P1 - c.P2, "dP_P1": x["x"], "x": x["x"], "FP": r.FP, "FLP": FLP, "xTP": x["xTP"],
            "Fgamma": x["Fgamma"], "xchoked": x["xchoked"], "dPchoked": x["xchoked"] * c.P1,
            "Y": x["Y"], "rho": e.rho1, "rho2": e.rho2, "M": e.M, "SG": e.M / CG.M_AIRE,
            "gamma": e.gamma, "Z1": e.Z1, "Z2": e.Z2, "T1": e.T1, "T2": e.T2,
            "mu": e.mu, "nu": e.mu / e.rho1, "Rev": r.Rev, "FR": r.FR, "D1": D1, "D2": D2,
            "bloqueado": r.bloqueado, "regimen_flujo": r.regimen,
            "tipo_calculo": CG.tipo_calculo(dim.tipo, r.bloqueado, r.regimen, e),
            "condicion": "flujo crítico" if r.bloqueado else "subcrítico",
            "sobrecalentamiento2": e.sobrecalentamiento2, "saturado": e.saturado, "origen_salida": e.origen,
            "nivel_trim": requerido,
            "Lp": rr["LpAe1m"] if rr else None, "Lp_trim": rr["LpAe_trim"] if rr else None,
            "Lp_salida": rr["LpAe_salida"] if rr else None, "Lp_Rn": rr["LpAe_Rn"] if rr else None,
            "regimen_ruido": rr["regimen_nombre"] if rr else "",
            "Ma1": v1 / c1, "Ma_valvula": v_out / c2, "Ma2": v2 / c2,
            "v1": v1, "v_valvula": v_out, "v2": v2, "c1": c1, "c_valvula": c2, "c2": c2,
            "d_salida": d_out, "A_salida": A_out,
        })
    alertas = [("General", a) for a in inf.alertas_generales] + alertas
    P_ops = [c.P1 for c in dim.casos] + ([dim.cierre.P1] if dim.cierre else [])
    T_ops = [e.T1 for e in estados] + ([dim.cierre.T1] if dim.cierre and dim.cierre.T1 else [])
    P_d = inst.P_diseno or max(P_ops)
    T_d = inst.T_diseno or max(T_ops)
    mres = _materiales(mat, inst, dim, salidas, P_d, T_d)
    generales, rating_adm = _verificaciones(inst, cuerpo, inf, dim, salidas, P_d, T_d, D1, D2, mres)
    alertas = [("General", a) for a in generales] + alertas
    if mres is not None:
        alertas += [("Materiales", a) for a in mres.todas_las_alertas()]
    alertas.sort(key=lambda t: -t[1].severidad)
    Cv_nom = inf.Kv_nominal / 0.865
    curva = [(h, Cv_nom * caudal_relativo(h / 100, estilo.caracteristica, estilo.rangeabilidad))
             for h in range(0, 101, 2)]
    res = Resultado(ident, inst, dim, inf, salidas, alertas, [], D1, D2, tp1, tp2, Cv_nom,
                    rating_adm, P_d, T_d, curva, mres)
    res.recomendaciones = recomendaciones(res)
    _carreras(res)
    return res


def recomendaciones_compresible(res: Resultado) -> list[tuple[str, str]]:
    s, inst, dim = res.salidas, res.inst, res.dim
    cuerpo, trim = res.cuerpo, res.trim
    rec: list[tuple[str, str]] = []
    Cv_max = max(x["Cv"] for x in s)
    h = [x["apertura"] for x in s]
    rec.append(("Coeficiente de caudal",
                f"Cv requerido máximo {_n(Cv_max, 1)}. Se recomienda una válvula con Cv nominal de al "
                f"menos {_n(Cv_max / 0.85, 1)} (apertura ≤ 85 % en el caso máximo). Con la válvula "
                f"de {_n(res.nps_valvula)}\" (Cv nominal típico {_n(res.Cv_nominal, 1)}) la apertura queda "
                f"entre {_n(min(h) * 100, 0)} % y {_n(max(h) * 100, 0)} %."))
    Ma = max(x["Ma_valvula"] for x in s)
    txt = f"Cuerpo {cuerpo.nombre.lower()}, rating CL{inst.rating}, conexión {inst.conexion}."
    if Ma > CG.MACH_SALIDA_VALVULA:
        txt += (f" El Mach en la salida de la válvula llega a {_n(Ma, 2)}: conviene un cuerpo de mayor "
                "diámetro o con salida expandida.")
    rec.append(("Estilo de cuerpo", txt))
    Lp = [x["Lp"] for x in s if x["Lp"] is not None]
    req = [x["nivel_trim"] for x in s]
    orden = list(CG.NIVEL_CORTO.values()) + ["Multietapa o silenciador"]
    peor = max(req, key=orden.index) if req else "No requerido"
    if peor == "No requerido":
        t = f"Internos estándar ({trim.nombre.lower()}): el ruido cumple el límite sin trim de bajo ruido."
    elif peor == "Multietapa o silenciador":
        t = ("Ningún trim de una etapa cumple el límite de ruido: se requieren internos multietapa, "
             "difusor o silenciador aguas abajo, o repartir la caída de presión.")
    else:
        t = (f"Se requiere trim de bajo ruido: jaula multiorificio {peor.lower()} "
             f"({CG.TRIMS_RUIDO['multiorificio_' + peor[-1]][0].split('(')[-1].rstrip(')')}).")
    rec.append(("Internos (trim) y ruido", t))
    if cuerpo.rotativa:
        guia = f"{cuerpo.guia}."
    else:
        guia = _guia_obturador(dim, max(x["dP"] for x in s), res.nps_valvula)
    rec.append(("Tipo de guía y obturador", guia))
    rec.append(("Asiento y clase de cierre", f"{inst.cierre}: fuga admisible {FUGA_CIERRE[inst.cierre]}"))
    dps = [x["dP"] for x in s]
    if len(s) > 1 and min(dps) > 0 and max(dps) / min(dps) > 2:
        car = "La caída de presión varía mucho entre casos: se recomienda característica isoporcentual."
    else:
        car = ("La caída de presión varía poco entre casos: la característica lineal da una ganancia "
               "más uniforme.")
    rec.append(("Característica inherente", car + f" Seleccionada: {dim.caracteristica}."))
    if Lp:
        rec.append(("Ruido", f"Nivel máximo estimado {_n(max(Lp), 1)} dB(A) a 1 m de la tubería "
                    f"(límite {_n(inst.ruido_permitido, 0)} dB(A), IEC 60534-8-3)."
                    + (" Cumple." if max(Lp) <= inst.ruido_permitido else " No cumple.")))
    if any(x["bloqueado"] for x in s):
        rec.append(("Flujo crítico", "En al menos un caso el flujo está estrangulado (sónico en la vena "
                    "contracta): el caudal no aumenta al bajar P2 y el ruido es alto."))
    dp_cierre = (f"{fdP(dim.cierre.dP)} (caso {dim.cierre.nombre})" if dim.cierre else
                 f"{fdP(max(dps))} (máxima de operación; cargue el caso Tight Shutoff con la presión de cierre real)")
    rec.append(("Actuador", "El cálculo de fuerza o par del actuador se incorporará en una próxima versión. "
                f"Debe vencer la ΔP de cierre {dp_cierre} y asegurar la carga de asiento de la clase {inst.cierre}."))
    return rec
