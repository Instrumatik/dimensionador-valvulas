"""Fluidos de proceso de refinerías, mejoradores de crudo pesado y extrapesado, servicios y químicos (v0.16.0).

Cada fluido tiene sus presentaciones (grado API, concentración, uso o composición típica) y un modelo de
propiedades:

* ``mezcla``    gases y líquidos livianos de composición conocida: ecuación de estado de CoolProp (GERG /
  HEOS) con la composición molar editable, igual que el gas natural.
* ``petroleo``  crudos y cortes de refinería como pseudocomponente: densidad con los coeficientes de
  dilatación térmica de API MPMS 11.1 (1980), viscosidad con la ecuación de Walther de ASTM D341 a partir
  de dos puntos, Tb con el factor de Watson, propiedades críticas y factor acéntrico de Kesler-Lee, masa
  molar de Riazi-Daubert, y presión de vapor de Lee-Kesler o, con RVP, la verdadera presión de vapor de
  EPA AP-42 cap. 7.1 (la mayor de las dos).
* ``solucion``  soluciones acuosas (ácidos, álcalis, sales, aminas, polímeros): densidad y viscosidad de
  tablas de datos publicados a 20 °C y 80 °C (interpoladas en concentración; viscosidad con la ecuación de
  Andrade), presión de vapor = actividad del agua × presión de vapor del agua (Raoult modificado).
* ``glicol``    glicoles puros y con agua: MEG y MPG hasta 60 % con las soluciones de CoolProp; el resto con
  mezcla ideal en volumen y regla logarítmica de viscosidad en masa; presión de vapor por Raoult.
* ``azufre``    azufre líquido: densidad lineal y viscosidad tabulada, con el salto de polimerización a 159 °C.
* ``slurry``    sólidos en agua: densidad de la mezcla y viscosidad de Thomas (1965).

Los valores de las tablas son aproximados (orden ±2 % en densidad, ±20 % en viscosidad y más en los
crudos pesados, cuya viscosidad varía un orden de magnitud entre crudos del mismo API). La línea
«Caracterización» acepta los datos de laboratorio o del certificado y esos datos mandan sobre los típicos.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import propiedades as P
from .modelos import Alerta, Severidad

RHO_AGUA_15C = 999.1          # kg/m³ (la misma de iec60534_2_1)
PC_AGUA = 22064.0             # kPa a
PSI = 6.894757                # kPa por psi
R = 8.314462


class ErrorFluido(P.ErrorPropiedades):
    pass


# ---------------------------------------------------------------------------------------------------- datos
@dataclass(frozen=True)
class Presentacion:
    nombre: str
    datos: dict                                 # parámetros del modelo (API, ν, concentración, composición...)
    agentes: tuple = ()                         # agentes implícitos para materiales: (clave, unidad, valor, fase)
    nota: str = ""
    modelo: str | None = None                   # si difiere del modelo del fluido
    toxico: bool | None = None                  # si difiere del fluido
    T_min_C: float | None = None                # por debajo: solidifica o cristaliza
    T_max_C: float | None = None                # por encima: se degrada, polimeriza o extrapola


@dataclass(frozen=True)
class FluidoProceso:
    nombre: str
    ingles: str
    grupo: str
    modelo: str
    tipos: str                                  # L (líquido), G (gas / vapor), LG
    familia: str                                # familia para materiales
    agua: str                                   # agua libre: Sí / No / Desconocida
    presentaciones: tuple[Presentacion, ...]
    descripcion: str
    servicio: str = ""                          # recomendaciones para la válvula
    toxico: bool = False
    seco: bool = False                          # sin agua libre salvo indicación (materiales)
    param: dict = field(default_factory=dict, hash=False, compare=False)   # tabla, soluto, glicol...

    def presentacion(self, nombre: str | None) -> Presentacion:
        for p in self.presentaciones:
            if p.nombre == nombre:
                return p
        return self.presentaciones[0]


GRUPOS = ["Crudos y cortes de refinería", "Gases de proceso y de refinería", "Hidrocarburos livianos y LPG",
          "Aminas y glicoles", "Ácidos, álcalis y sales", "Azufre", "Polímeros (tratamiento de agua)",
          "Slurry"]

# Agentes de materiales que aportan los hidrocarburos
HC = ("hidrocarburos", "% p/p", 100, "Orgánica líquida")


def _hc(azufre=None, tan=None, extra=()):
    a = [HC]
    if azufre:
        a.append(("azufre_hc", "% p/p", azufre, "Orgánica líquida"))
    if tan:
        a.append(("tan", "mg KOH/g", tan, "Orgánica líquida"))
    return tuple(a) + tuple(extra)


# ------------------------------------------------------------------------- crudos y cortes (pseudocomponente)
# Viscosidad típica de crudos muertos por grado API (cSt a 50 °C y a 100 °C). Orden de magnitud de crudos
# pesados y extrapesados venezolanos, canadienses y de Medio Oriente; entre crudos del mismo API puede
# variar 3 veces o más: use el dato de laboratorio.
_NU_CRUDO = [(8, 8000, 250), (10, 3000, 140), (12, 1200, 80), (14, 550, 50), (16, 250, 35), (18, 130, 23),
             (20, 80, 17), (22, 45, 11), (24, 25, 7.5), (27, 12, 4.5)]
_RVP_CRUDO = [(8, 2.0), (12, 2.5), (16, 5.0), (27, 6.0)]


def _interp(tabla, x, col=1, log=False):
    xs = [t[0] for t in tabla]
    if x <= xs[0]:
        i = 0
    elif x >= xs[-1]:
        i = len(xs) - 2
    else:
        i = max(j for j in range(len(xs) - 1) if xs[j] <= x)
    x0, x1 = xs[i], xs[i + 1]
    y0, y1 = tabla[i][col], tabla[i + 1][col]
    f = (x - x0) / (x1 - x0)
    if log:
        return math.exp(math.log(y0) + f * (math.log(y1) - math.log(y0)))
    return y0 + f * (y1 - y0)


def _loglog(nu):
    return math.log10(math.log10(nu + 0.7))


def _nu_crudo(api):
    """ν a 50 °C y 100 °C interpolando log log (ν + 0,7) en el API."""
    out = []
    for col in (1, 2):
        ll = _interp([(a, _loglog(n50), _loglog(n100)) for a, n50, n100 in _NU_CRUDO], api, col)
        out.append(10 ** (10 ** ll) - 0.7)
    return out


def _crudo(api: int) -> Presentacion:
    n50, n100 = _nu_crudo(api)
    kw = 11.3 + (api - 8) * (11.8 - 11.3) / 19
    s = 4.2 + (api - 8) * (1.2 - 4.2) / 19
    tan = 3.0 + (api - 8) * (0.3 - 3.0) / 19
    rvp = _interp(_RVP_CRUDO, api)
    nota = ("Extrapesado: a temperatura ambiente no fluye; se maneja caliente o diluido con nafta." if api < 10
            else "Pesado." if api < 22.3 else "Mediano.")
    return Presentacion(f"{api} °API", dict(API=api, Kw=round(kw, 2), nu=[(50.0, round(n50, 3 if n50 < 10 else 1)),
                                                                          (100.0, round(n100, 2))],
                                             RVP=round(rvp, 1), crudo=True, S=round(s, 2), TAN=round(tan, 2)),
                        _hc(round(s, 2), round(tan, 2)), nota)


def _corte(nombre, API, Kw, nu, S=None, TAN=None, RVP=None, pendiente=None, nota="", T_min=None, T_max=None,
           extra=(), solidos=None):
    d = dict(API=API, Kw=Kw, nu=list(nu))
    if RVP is not None:
        d.update(RVP=RVP, pendiente=pendiente or 3.0)
    if S is not None:
        d["S"] = S
    if TAN is not None:
        d["TAN"] = TAN
    if solidos:
        d["solidos_mgL"] = solidos
    ag = _hc(S, TAN, extra + ((("solidos", "mg/L", solidos, "Sólida"),) if solidos else ()))
    return Presentacion(nombre, d, ag, nota, T_min_C=T_min, T_max_C=T_max)


_SERV_HC_PESADO = ("Viscosidad alta: N25 corrige el Cv por número de Reynolds (FR, IEC 60534-2-1 cl. 7); con FR "
                   "bajo prefiera cuerpos de paso amplio (globo de puerto grande, bola segmentada o tapón "
                   "excéntrico). Línea y válvula con traceado o camisa para no bajar del punto de fluidez. Arriba "
                   "de 230 °C revise sulfidación y, con TAN > 0,5, corrosión nafténica: N25 las evalúa en "
                   "3-Materiales. Empaquetadura de baja emisión (COV); arriba de 232 °C grafito.")
_SERV_HC_LIVIANO = ("Hidrocarburo volátil e inflamable: con Pv cerca de P2 aparece flashing; N25 usa la presión de "
                    "vapor verdadera estimada con el RVP. Empaquetadura de baja emisión (COV, ISO 15848-1 / "
                    "API 622). Asientos y juntas: sin EPDM.")

CRUDOS = FluidoProceso(
    "Crudo comercial", "Commercial crude oil", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido", "Desconocida",
    tuple(_crudo(a) for a in range(8, 28)),
    "Crudo muerto (estabilizado) de 8 a 27 °API: extrapesado (< 10 °API), pesado (10 a 22,3 °API) y mediano. "
    "Valores típicos de viscosidad, Kw, azufre, TAN y RVP por grado; cárguelos del certificado del crudo.",
    _SERV_HC_PESADO + " Con agua y sal (crudo sin desalar) cargue los cloruros en 3-Materiales.")

_CORTES = [
    FluidoProceso("Nafta diluente", "Diluent naphtha", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido", "No", (
        _corte("Nafta liviana (diluente)", 70, 12.2, [(20, 0.55), (50, 0.42)], S=0.05, RVP=10, pendiente=3.5,
               nota="Diluente del crudo extrapesado (crudo diluido / DCO)."),
        _corte("Nafta pesada (diluente)", 52, 11.9, [(20, 0.9), (50, 0.65)], S=0.1, RVP=2.5, pendiente=2.5),
    ), "Nafta usada para diluir crudo extrapesado y bajar su viscosidad para el transporte.", _SERV_HC_LIVIANO),
    FluidoProceso("Gasolina", "Gasoline", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido", "No", tuple(
        _corte(f"Gasolina RVP {str(r).replace('.', ',')} psi", 60, 11.8, [(20, 0.65), (50, 0.48)], S=0.003, RVP=r,
               pendiente=3.0) for r in (7, 9, 11.5, 13.5)),
        "Gasolina de motor terminada o componente de mezcla, por presión de vapor Reid.", _SERV_HC_LIVIANO),
    FluidoProceso("Jet A-1 (combustible de aviación)", "Jet A-1", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido",
                  "No", (_corte("Jet A-1", 44, 11.7, [(-20, 4.0), (40, 1.3)], S=0.1, T_min=-47),),
                  "Kerosene de aviación. Punto de congelamiento ≤ −47 °C; viscosidad ≤ 8 cSt a −20 °C.",
                  "Inflamable (punto de inflamación ≥ 38 °C). Limpieza: sin contaminar con agua ni partículas; "
                  "empaquetadura de baja emisión. Asientos sin EPDM."),
    FluidoProceso("Diésel", "Diesel", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido", "No", (
        _corte("Diésel ULSD (≤ 15 ppm de azufre)", 35, 11.8, [(40, 3.0), (100, 1.25)], S=0.0015, T_min=-10),
        _corte("Diésel convencional (0,05 a 0,5 % de azufre)", 34, 11.8, [(40, 3.2), (100, 1.3)], S=0.3, T_min=-5),
    ), "Gasoil de automoción o industrial.", "Inflamable, poco volátil. Empaquetadura de baja emisión; asientos sin "
       "EPDM."),
    FluidoProceso("Gasóleo (Gas Oil)", "Gas oil", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido", "No", (
        _corte("Gasóleo atmosférico liviano (LAGO)", 34, 11.8, [(40, 3.5), (100, 1.4)], S=0.8, TAN=0.3),
        _corte("Gasóleo atmosférico pesado (HAGO)", 27, 11.8, [(40, 9.0), (100, 2.5)], S=1.5, TAN=0.6),
    ), "Corte de la torre atmosférica entre el kerosene y el residuo.", _SERV_HC_PESADO),
    FluidoProceso("Gasóleo liviano de vacío (LVGO)", "Light Vacuum Gas Oil", GRUPOS[0], "petroleo", "L",
                  "Hidrocarburo líquido", "No",
                  (_corte("LVGO", 28, 11.9, [(40, 10.0), (100, 2.7)], S=1.8, TAN=0.8),),
                  "Corte liviano de la torre de vacío.", _SERV_HC_PESADO),
    FluidoProceso("Gasóleo medio de vacío (MVGO)", "Medium Vacuum Gas Oil", GRUPOS[0], "petroleo", "L",
                  "Hidrocarburo líquido", "No",
                  (_corte("MVGO", 22, 11.9, [(50, 35.0), (100, 8.0)], S=2.3, TAN=1.2, T_min=25),),
                  "Corte medio de la torre de vacío.", _SERV_HC_PESADO),
    FluidoProceso("Gasóleo pesado de vacío (HVGO)", "Heavy Vacuum Gas Oil", GRUPOS[0], "petroleo", "L",
                  "Hidrocarburo líquido", "No",
                  (_corte("HVGO", 17, 11.9, [(50, 250.0), (100, 30.0)], S=2.8, TAN=1.5, T_min=35),),
                  "Corte pesado de la torre de vacío; carga de FCC o hidrocraqueo.", _SERV_HC_PESADO),
    FluidoProceso("Gasóleo liviano de coquización (LCGO)", "Light Coker Gas Oil", GRUPOS[0], "petroleo", "L",
                  "Hidrocarburo líquido", "No",
                  (_corte("LCGO", 30, 11.4, [(40, 3.5), (100, 1.4)], S=2.5, TAN=0.3),),
                  "Gasóleo liviano del coquizador retardado; aromático y olefínico, con azufre y nitrógeno.",
                  _SERV_HC_PESADO + " Puede arrastrar finos de coque: considere trim endurecido."),
    FluidoProceso("Gasóleo pesado de coquización (HCGO)", "Heavy Coker Gas Oil", GRUPOS[0], "petroleo", "L",
                  "Hidrocarburo líquido", "No",
                  (_corte("HCGO", 16, 11.4, [(50, 60.0), (100, 11.0)], S=3.5, TAN=0.5, T_min=25),),
                  "Gasóleo pesado del coquizador retardado.",
                  _SERV_HC_PESADO + " Arrastra finos de coque: trim endurecido (Stellite o carburo de "
                  "tungsteno)."),
    FluidoProceso("Hidrocarburos pesados", "Heavy hydrocarbons", GRUPOS[0], "petroleo", "L", "Hidrocarburo líquido",
                  "No", (
                      _corte("Residuo atmosférico (12 °API)", 12, 11.6, [(100, 300.0), (150, 45.0)], S=3.5, TAN=2.0,
                             T_min=40),
                      _corte("Residuo de vacío (5 °API)", 5, 11.5, [(100, 8000.0), (150, 450.0)], S=4.5, TAN=2.0,
                             T_min=60),
                      _corte("Fuel oil pesado (n.º 6 / búnker, 12 °API)", 12, 11.4, [(50, 380.0), (100, 40.0)], S=2.5,
                             T_min=25),
                      _corte("Aceite pesado genérico (15 °API)", 15, 11.6, [(50, 400.0), (100, 45.0)], S=3.0, TAN=1.0,
                             T_min=20),
                  ), "Residuos y aceites pesados de refinería y mejoradores.", _SERV_HC_PESADO),
]


# ----------------------------------------------------------------------------- mezclas (CoolProp, % molar)
def _mez(nombre, comp, nota="", agentes=(), toxico=None):
    return Presentacion(nombre, dict(comp=comp), tuple(agentes), nota, toxico=toxico)


def _gas_ag(comp):
    """Agentes de materiales de un gas según su composición (% molar)."""
    a = []
    for comp_n, clave in (("Sulfuro de hidrógeno", "h2s"), ("Dióxido de carbono", "co2"), ("Hidrógeno", "h2"),
                          ("Amoníaco", "nh3"), ("Oxígeno", "o2")):
        if comp.get(comp_n):
            a.append((clave, "% molar", comp[comp_n], "Gas / vapor"))
    return tuple(a)


def _g(nombre, comp, nota="", toxico=None):
    return _mez(nombre, comp, nota, _gas_ag(comp), toxico)


_SERV_GAS = ("Gas: N25 calcula Z, κ y la viscosidad de la mezcla con la ecuación de estado. Con ΔP alta revise el "
             "ruido aerodinámico (IEC 60534-8-3) y la velocidad de salida.")
_SERV_TOX = (" Fluido tóxico: empaquetadura de emisión muy baja (fuelle o carga viva certificada ISO 15848-1 "
             "clase A/B) y bonete con conexión de purga si lo pide la especificación.")

GASES = [
    FluidoProceso("Gas de síntesis (syngas)", "Synthesis gas", GRUPOS[1], "mezcla", "G", "Gas", "No", (
        _g("Reformado con vapor (SMR), base seca",
           {"Hidrógeno": 74, "Monóxido de carbono": 12, "Dióxido de carbono": 8, "Metano": 5, "Nitrógeno": 1}),
        _g("Gasificación con oxígeno (crudo, con H₂S)",
           {"Hidrógeno": 38, "Monóxido de carbono": 45, "Dióxido de carbono": 12, "Metano": 1, "Nitrógeno": 2,
            "Argón": 1, "Sulfuro de hidrógeno": 1}),
        _g("Relación H₂/CO = 2 (metanol, Fischer-Tropsch)",
           {"Hidrógeno": 64, "Monóxido de carbono": 32, "Dióxido de carbono": 3, "Metano": 1}),
    ), "Mezcla de H₂ y CO de reformado o gasificación.",
        _SERV_GAS + " El H₂ obliga a revisar HTHA (API 941) arriba de 200 °C y la fragilización de aceros duros; el "
        "CO a alta presión forma carbonilos con el níquel y el hierro (evite aleaciones de níquel)." + _SERV_TOX,
        toxico=True),
    FluidoProceso("Off-gas C1–C3", "Off gas C1–C3", GRUPOS[1], "mezcla", "G", "Hidrocarburo gaseoso", "Desconocida", (
        _g("Off-gas dulce (tratado)", {"Hidrógeno": 20, "Metano": 45, "Etano": 18, "Etileno": 5, "Propano": 8,
                                        "Propileno": 3, "Nitrógeno": 1}),
        _g("Off-gas ácido (antes de aminas)", {"Hidrógeno": 18, "Metano": 42, "Etano": 17, "Etileno": 5,
                                                "Propano": 8, "Propileno": 3, "Nitrógeno": 1,
                                                "Sulfuro de hidrógeno": 4, "Dióxido de carbono": 2}, toxico=True),
    ), "Gases livianos de las unidades de proceso (C1 a C3 con hidrógeno).", _SERV_GAS),
    FluidoProceso("Gas combustible", "Fuel gas", GRUPOS[1], "mezcla", "G", "Hidrocarburo gaseoso", "No", (
        _g("Gas combustible de refinería", {"Hidrógeno": 25, "Metano": 50, "Etano": 12, "Etileno": 3, "Propano": 6,
                                             "Propileno": 1, "n-Butano": 1, "Nitrógeno": 1.5,
                                             "Dióxido de carbono": 0.5}),
        _g("Gas natural de red", dict(P.GN_TIPICO)),
    ), "Gas de la red de combustible de hornos y calderas.", _SERV_GAS),
    FluidoProceso("Gas ácido", "Acid gas / sour gas", GRUPOS[1], "mezcla", "G", "Gas", "Desconocida", (
        _g("Gas ácido de regeneradora de aminas", {"Sulfuro de hidrógeno": 85, "Dióxido de carbono": 10, "Agua": 4,
                                                    "Metano": 1}, "Saturado en agua a la salida del condensador."),
        _g("Gas ácido de despojadora de aguas agrias (SWS)", {"Sulfuro de hidrógeno": 35, "Amoníaco": 35, "Agua": 30},
           "Se maneja caliente (80 a 90 °C) para que no condensen sales de amonio."),
        _g("Gas amargo de proceso (5 % de H₂S)", {"Metano": 80, "Etano": 8, "Propano": 2, "Dióxido de carbono": 5,
                                                  "Sulfuro de hidrógeno": 5}),
    ), "Gas con H₂S (y CO₂ o NH₃) hacia la planta de azufre o la antorcha.",
        _SERV_GAS + " Servicio agrio: materiales según ISO 17945 / NACE MR0103 (N25 lo verifica en 3-Materiales)."
        + _SERV_TOX, toxico=True),
    FluidoProceso("Gas de refinería", "Refinery gas", GRUPOS[1], "mezcla", "G", "Hidrocarburo gaseoso",
                  "Desconocida", (
                      _g("Gas de FCC (craqueo catalítico)", {"Hidrógeno": 15, "Metano": 35, "Etano": 15, "Etileno": 15,
                                                             "Propano": 6, "Propileno": 10, "Nitrógeno": 3,
                                                             "Sulfuro de hidrógeno": 1}, toxico=True),
                      _g("Gas de reformado catalítico (rico en H₂)", {"Hidrógeno": 80, "Metano": 8, "Etano": 6,
                                                                       "Propano": 4, "Isobutano": 1, "n-Butano": 1}),
                      _g("Gas de coquización retardada", {"Hidrógeno": 12, "Metano": 55, "Etano": 17, "Etileno": 3,
                                                          "Propano": 6, "Propileno": 3, "Sulfuro de hidrógeno": 3,
                                                          "Dióxido de carbono": 1}, toxico=True),
                      _g("Gas de reciclo de hidrotratamiento", {"Hidrógeno": 85, "Metano": 8, "Etano": 3,
                                                                "Propano": 1.5, "Sulfuro de hidrógeno": 2.5},
                         toxico=True),
                  ), "Gases de las unidades de conversión.",
                  _SERV_GAS + " Con H₂ a alta temperatura revise HTHA (API 941)."),
]

_LIV = [
    FluidoProceso("LPG (gas licuado de petróleo)", "Liquefied Petroleum Gas", GRUPOS[2], "mezcla", "LG",
                  "Hidrocarburo líquido", "No", (
                      _mez("Propano comercial", {"Propano": 95, "Etano": 2, "Isobutano": 1.5, "n-Butano": 1.5},
                           agentes=(HC,)),
                      _mez("Mezcla propano-butano 60/40", {"Propano": 60, "n-Butano": 28, "Isobutano": 12},
                           agentes=(HC,)),
                      _mez("Butano comercial", {"n-Butano": 70, "Isobutano": 28, "Propano": 2}, agentes=(HC,)),
                  ), "Propano y butanos licuados a presión. Elija Líquido o Gas según la fase en la válvula.",
                  "Líquido en su punto de burbuja: casi siempre hay flashing o cavitación en la válvula (Pv ≈ P1); "
                  "N25 toma Pv = presión de burbuja de la mezcla. A baja temperatura (autorrefrigeración al "
                  "despresurizar) revise el material del cuerpo para T mínima (LCC / LCB o inoxidable). "
                  "Empaquetadura de baja emisión; asientos sin EPDM."),
    FluidoProceso("Hidrocarburos livianos", "Light hydrocarbons", GRUPOS[2], "mezcla", "LG", "Hidrocarburo líquido",
                  "No", (
                      _mez("Corriente C2–C3 (etano-propano)", {"Etano": 30, "Propano": 70}, agentes=(HC,)),
                      _mez("Pentanos / hexanos (C5–C6)", {"n-Pentano": 40, "Isopentano": 30, "n-Hexano": 30},
                           agentes=(HC,)),
                      _mez("Condensado liviano C4–C6", {"n-Butano": 10, "Isobutano": 5, "Isopentano": 25,
                                                        "n-Pentano": 30, "n-Hexano": 30}, agentes=(HC,)),
                  ), "Corrientes livianas de composición conocida (líquido o gas).", _SERV_HC_LIVIANO),
]


# ----------------------------------------------------------------------------------- soluciones acuosas
# Filas (concentración % p/p, ρ a 20 °C kg/m³, μ a 20 °C cP, μ a 80 °C cP, actividad del agua a_w, p del
# soluto a 20 °C kPa). Datos aproximados de manuales (Perry, CRC, fichas de productores); a_w redondeada
# hacia arriba: una Pv mayor es conservadora para cavitación y flashing.
_T_NAOH = [(0, 998.2, 1.002, 0.355, 1.0), (4, 1043, 1.17, 0.42, 0.97), (10, 1109, 1.86, 0.66, 0.92),
           (15, 1164, 2.9, 0.95, 0.86), (20, 1219, 4.5, 1.35, 0.79), (25, 1274, 7.0, 1.9, 0.70),
           (32, 1349, 13.0, 3.2, 0.57), (40, 1430, 28.0, 5.5, 0.38), (50, 1525, 78.0, 10.0, 0.18)]
_T_H2SO4 = [(0, 998.2, 1.002, 0.355, 1.0), (10, 1066, 1.23, 0.45, 0.96), (20, 1139, 1.55, 0.58, 0.88),
            (30, 1219, 2.0, 0.75, 0.76), (40, 1303, 2.8, 1.0, 0.60), (50, 1395, 4.2, 1.45, 0.42),
            (60, 1498, 6.6, 2.1, 0.24), (70, 1611, 11.5, 3.3, 0.10), (80, 1727, 18.0, 5.0, 0.03),
            (88, 1802, 22.0, 6.0, 0.01), (93, 1830, 23.0, 6.3, 0.005), (96, 1835, 24.0, 6.5, 0.002),
            (98, 1836, 25.0, 6.6, 0.001)]
_T_H3PO4 = [(0, 998.2, 1.002, 0.355, 1.0), (10, 1053, 1.15, 0.43, 0.97), (20, 1113, 1.55, 0.57, 0.92),
            (30, 1181, 2.1, 0.75, 0.86), (40, 1254, 3.0, 1.0, 0.78), (50, 1335, 4.6, 1.5, 0.68),
            (62, 1440, 8.5, 2.4, 0.52), (75, 1579, 18.0, 4.5, 0.33), (85, 1685, 45.0, 8.5, 0.18)]
_T_FECL3 = [(0, 998.2, 1.002, 0.355, 1.0), (10, 1085, 1.25, 0.45, 0.96), (20, 1182, 1.75, 0.62, 0.90),
            (30, 1291, 2.9, 0.95, 0.80), (40, 1417, 6.0, 1.7, 0.68), (45, 1490, 9.0, 2.4, 0.60)]
_T_HCL = [(0, 998.2, 1.002, 0.355, 1.0, 0.0), (5, 1023, 1.06, 0.38, 0.97, 0.0), (10, 1048, 1.16, 0.42, 0.93, 0.0),
          (20, 1098, 1.37, 0.50, 0.82, 0.03), (32, 1159, 1.75, 0.65, 0.60, 2.0), (37, 1183, 1.95, 0.72, 0.50, 15.0)]
_T_HNO3 = [(0, 998.2, 1.002, 0.355, 1.0, 0.0), (10, 1054, 1.04, 0.38, 0.95, 0.0), (20, 1115, 1.15, 0.42, 0.88, 0.0),
           (40, 1246, 1.6, 0.58, 0.68, 0.0), (53, 1330, 2.0, 0.70, 0.52, 0.1), (60, 1367, 2.2, 0.77, 0.43, 0.3),
           (68, 1405, 2.3, 0.80, 0.33, 0.6)]
_T_NAOCL = [(0, 998.2, 1.002, 0.355, 1.0), (5, 1080, 1.2, 0.45, 0.97), (10, 1160, 1.9, 0.65, 0.93),
            (12.5, 1205, 2.6, 0.85, 0.90), (15, 1250, 3.3, 1.0, 0.88)]
_T_MDEA = [(0, 998.2, 1.002, 0.355, 1.0), (30, 1025, 3.6, 0.95, 0.96), (40, 1035, 6.4, 1.4, 0.94),
           (45, 1040, 8.5, 1.75, 0.93), (50, 1045, 11.5, 2.2, 0.91)]
_T_DEA = [(0, 998.2, 1.002, 0.355, 1.0), (20, 1022, 2.1, 0.62, 0.98), (25, 1028, 2.6, 0.72, 0.97),
          (30, 1035, 3.1, 0.85, 0.96), (35, 1040, 3.9, 1.0, 0.95)]
_T_MEA = [(0, 998.2, 1.002, 0.355, 1.0), (15, 1005, 1.6, 0.52, 0.97), (20, 1007, 1.9, 0.58, 0.96),
          (30, 1012, 2.9, 0.78, 0.94)]
M_SOLUTO = {"naoh": 40.0, "h2so4": 98.08, "h3po4": 98.0, "fecl3": 162.2, "hcl": 36.46, "hno3": 63.01,
            "naocl": 74.44, "mdea": 119.16, "dea": 105.14, "mea": 61.08}


def _sol(nombre, c, agentes, nota="", T_min=None, T_max=None, extra=None):
    d = dict(conc=c)
    if extra:
        d.update(extra)
    return Presentacion(nombre, d, tuple(agentes), nota, T_min_C=T_min, T_max_C=T_max)


def _pct(c):
    return f"{c:g}".replace(".", ",") + " %"


_SERV_ACIDO = ("Corrosivo: N25 elige cuerpo e internos por compatibilidad con la concentración y la temperatura "
               "(3-Materiales). Para cuerpos de acero, asientos y obturador de aleación resistente o revestidos "
               "(PTFE / PFA). Empaquetadura de PTFE o grafito según la temperatura.")



def _quim(nombre, ingles, familia, soluto, tabla, presentaciones, descripcion, servicio, agua="Sí", toxico=False,
          grupo=GRUPOS[4]):
    return FluidoProceso(nombre, ingles, grupo, "solucion", "L", familia, agua, tuple(presentaciones), descripcion,
                         servicio, toxico, param=dict(tabla=tabla, soluto=soluto))


QUIMICOS = [
    _quim("Hidróxido de sodio (soda cáustica)", "Sodium hydroxide / caustic soda", "Alcalino", "naoh", _T_NAOH,
          [_sol(_pct(c), c, [("naoh", "% p/p", c, "Acuosa")], T_min=12 if c == 50 else None)
           for c in (4, 10, 20, 25, 32, 50)]
          + [_sol("Soda gastada (spent caustic, ≈ 8 % con sulfuros)", 8,
                  [("naoh", "% p/p", 8, "Acuosa"), ("sulfuros", "mg/L", 20000, "Acuosa")],
                  "Soda de lavado de LPG y naftas con Na₂S, mercaptanos y fenoles: al acidificarse libera H₂S.")],
          "NaOH en agua. Comercial al 50 % y al 32 %; diluida para neutralización y lavados.",
          "Fragilización cáustica del acero al carbono por encima de ~ 50 a 80 °C según la concentración (curva de "
          "NACE SP0403): N25 la evalúa en 3-Materiales. La soda al 50 % cristaliza por debajo de ~ 12 °C: trace "
          "la línea. Asientos de EPDM o PTFE (no FKM en soda caliente)."),
    _quim("Ácido sulfúrico", "Sulfuric acid", "Ácido", "h2so4", _T_H2SO4,
          [_sol(_pct(c), c, [("h2so4", "% p/p", c, "Acuosa")], T_min=2 if c == 98 else None)
           for c in (10, 20, 30, 50, 70, 93, 96, 98)]
          + [_sol("Ácido gastado de alquilación (≈ 90 %, con hidrocarburos)", 90,
                  [("h2so4", "% p/p", 90, "Acuosa"), HC])],
          "H₂SO₄ en agua. Concentrado (93 a 98 %) en alquilación y tratamiento de agua; diluido en neutralización.",
          "El concentrado (> 90 %) es poco corrosivo para el acero al carbono a baja velocidad y temperatura "
          "ambiente, pero el diluido (10 a 80 %) lo ataca: no deje que se diluya en la válvula (purgas, lavados). "
          "La velocidad erosiona la película de sulfato de hierro: limite la velocidad en el acero. Aleación 20, "
          "Hastelloy C o revestimiento PTFE / PFA en internos. " + _SERV_ACIDO),
    _quim("Ácido fosfórico", "Phosphoric acid", "Ácido", "h3po4", _T_H3PO4,
          [_sol(_pct(c), c, [("h3po4", "% p/p", c, "Acuosa")], T_min=21 if c == 85 else None)
           for c in (10, 20, 30, 50, 75, 85)],
          "H₃PO₄ en agua; el grado técnico es 75 u 85 %.",
          "El 85 % puede cristalizar por debajo de ~ 21 °C: trace la línea. " + _SERV_ACIDO),
    _quim("Cloruro férrico", "Ferric chloride", "Ácido", "fecl3", _T_FECL3,
          [_sol(_pct(c), c, [("fecl3", "% p/p", c, "Acuosa")]) for c in (10, 20, 30, 40, 45)],
          "FeCl₃ en agua (coagulante de tratamiento de agua); comercial al 40 %. Es ácido (pH 1 a 2) y oxidante.",
          "Muy agresivo con los aceros inoxidables (picaduras): titanio, Hastelloy C o revestimiento PTFE / PFA y "
          "cuerpo revestido. Asientos de PTFE o EPDM."),
    _quim("Ácido clorhídrico", "Hydrochloric acid", "Ácido", "hcl", _T_HCL,
          [_sol(_pct(c), c, [("hcl", "% p/p", c, "Acuosa")]) for c in (5, 10, 20, 32, 37)],
          "HCl en agua; comercial al 32 a 37 % (humeante).",
          "Ataca a casi todos los metales: válvulas revestidas de PTFE / PFA, Hastelloy B o tantalio. Por encima "
          "del 30 % desprende HCl gaseoso: N25 suma su presión parcial a la presión de vapor. " + _SERV_ACIDO,
          toxico=True),
    _quim("Ácido nítrico", "Nitric acid", "Ácido", "hno3", _T_HNO3,
          [_sol(_pct(c), c, [("hno3", "% p/p", c, "Acuosa")]) for c in (10, 20, 40, 53, 60, 68)],
          "HNO₃ en agua; comercial al 53 a 68 %. Ácido oxidante.",
          "El inoxidable 304L es el material habitual; evite el acero al carbono, el Hastelloy B y los elastómeros "
          "(salvo FKM en frío). Empaquetadura de PTFE. " + _SERV_ACIDO, toxico=True),
    _quim("Hipoclorito de sodio", "Sodium hypochlorite", "Alcalino", "naocl", _T_NAOCL,
          [_sol(_pct(c), c, [("hipoclorito", "% p/p", round(c * 0.952, 2), "Acuosa"), ("naoh", "% p/p", 0.5, "Acuosa")],
                T_max=40) for c in (5, 10, 12.5, 15)],
          "NaOCl en agua (desinfección, control de bioincrustación). El comercial tiene 10 a 15 %.",
          "Oxidante con cloruros: picadura del inoxidable; use titanio, PVC / CPVC o revestimiento PTFE. Se "
          "descompone con la temperatura y la luz liberando O₂: evite tramos ciegos y temperaturas > 40 °C."),
]


def _amina(rica: bool):
    pres = []
    for amina, tabla, concs in (("MDEA", _T_MDEA, (40, 45, 50)), ("DEA", _T_DEA, (25, 30, 35)),
                                ("MEA", _T_MEA, (15, 20, 30))):
        for c in concs:
            ag = [("aminas", "% p/p", c, "Acuosa")]
            ag += ([("h2s", "mg/L", 5000, "Acuosa"), ("co2", "mg/L", 3000, "Acuosa")] if rica
                   else [("h2s", "mg/L", 300, "Acuosa")])
            pres.append(Presentacion(f"{amina} {_pct(c)}", dict(conc=c, amina=amina.lower(), rica=rica), tuple(ag)))
    nombre = "Amina rica" if rica else "Amina pobre"
    desc = ("Solución de amina cargada con H₂S y CO₂ (fondo de la absorbedora, hacia la regeneradora)." if rica else
            "Solución de amina regenerada (fondo de la regeneradora, hacia la absorbedora).")
    serv = ("Válvula de control de nivel de la absorbedora (letdown): al bajar la presión la amina rica libera H₂S y "
            "CO₂ (desgasificación) y el flujo sale bifásico, con erosión-corrosión. Ubique la válvula cerca del "
            "separador flash, con salida expandida; cuerpo de acero al carbono con PWHT o inoxidable 316 y trim "
            "316 / Stellite. La IEC 60534 para líquidos no cubre la desgasificación: deje margen de apertura."
            + _SERV_TOX) if rica else (
            "Corrosión baja si la carga residual es baja; SCC por aminas del acero al carbono por encima de ~ 60 °C "
            "sin PWHT (API RP 945). Trim de inoxidable 316.")
    return FluidoProceso(nombre, "Rich amine" if rica else "Lean amine", GRUPOS[3], "solucion", "L", "Otro", "Sí",
                         tuple(pres), desc, serv, toxico=rica,
                         param=dict(tablas={"mdea": _T_MDEA, "dea": _T_DEA, "mea": _T_MEA},
                                    soluto="amina", rica=rica))


AMINAS = [_amina(False), _amina(True)]

# Glicoles puros: M, ρ20 kg/m³, μ20 cP, μ80 cP, β 1/K, Tb K, Pc kPa a
GLICOLES = {"MEG": (62.07, 1113, 19.9, 3.4, 6.2e-4, 470.5, 8200),
            "MPG": (76.09, 1036, 56.0, 4.6, 7.2e-4, 461.0, 6100),
            "DEG": (106.12, 1118, 35.7, 5.0, 6.4e-4, 518.0, 4600),
            "TEG": (150.17, 1125, 49.0, 6.3, 6.9e-4, 561.0, 3300),
            "TREG": (194.23, 1125, 61.0, 7.6, 7.0e-4, 601.0, 2600)}


def _glicol(nombre, ingles, g, presentaciones, desc, serv):
    pres = tuple(Presentacion(n, dict(conc=c), (("glicoles", "% p/p", c, "Acuosa"),) + tuple(ex), nota,
                              T_max_C=tmax)
                 for n, c, ex, nota, tmax in presentaciones)
    return FluidoProceso(nombre, ingles, GRUPOS[3], "glicol", "L", "Otro", "Sí", pres, desc, serv,
                         param=dict(glicol=g))


_SERV_GLICOL = ("Poco corrosivo mientras no se degrade: oxidado o sobrecalentado forma ácidos orgánicos y baja el "
                "pH. Trim de inoxidable 316; asientos de EPDM, FKM o PTFE.")
_RICO = (("co2", "mg/L", 500, "Acuosa"), ("h2s", "mg/L", 100, "Acuosa"))
GLICOL_FLUIDOS = [
    _glicol("Monoetilenglicol (MEG)", "Monoethylene glycol", "MEG", [
        (f"MEG {_pct(c)} en agua", c, (), "Refrigerante / anticongelante." if c <= 60 else "", None)
        for c in (20, 30, 40, 50, 60)] + [
        ("MEG pobre 80 % (inhibición de hidratos)", 80, (), "Inyección en gasoductos y pozos.", None),
        ("MEG rico 50 % (con agua de formación)", 50, (("cloruros", "mg/L", 20000, "Acuosa"),),
         "Retorna del gasoducto con agua y sales hacia la regeneración.", None),
        ("MEG puro (≥ 99 %)", 99.5, (), "", None)],
        "Etilenglicol: anticongelante, refrigerante e inhibidor de hidratos.", _SERV_GLICOL),
    _glicol("Propilenglicol (MPG)", "Monopropylene glycol", "MPG", [
        (f"MPG {_pct(c)} en agua", c, (), "Refrigerante de grado alimenticio.", None) for c in (30, 40, 50)] + [
        ("MPG puro (≥ 99 %)", 99.5, (), "", None)],
        "Propilenglicol: refrigerante y anticongelante de baja toxicidad.", _SERV_GLICOL),
    _glicol("Dietilenglicol (DEG)", "Diethylene glycol", "DEG", [
        ("DEG pobre 99 % (deshidratación)", 99, (), "", 165), ("DEG rico 95 %", 95, _RICO, "", 165),
        ("DEG puro (≥ 99,5 %)", 99.8, (), "", 165)],
        "Dietilenglicol: deshidratación de gas e inhibición de hidratos.", _SERV_GLICOL),
    _glicol("Trietilenglicol (TEG)", "Triethylene glycol", "TEG", [
        ("TEG pobre 99,5 % (deshidratación de gas)", 99.5, (), "Regenerado: 99 a 99,9 %.", 205),
        ("TEG 99 %", 99, (), "", 205),
        ("TEG rico 97 %", 97, _RICO, "Del fondo de la contactora, con agua e hidrocarburos absorbidos.", 205),
        ("TEG rico 95 %", 95, _RICO, "", 205), ("TEG puro (≥ 99,9 %)", 99.9, (), "", 205)],
        "Trietilenglicol: el desecante más usado en deshidratación de gas natural.",
        "La válvula de nivel de la contactora (TEG rico) desgasifica hidrocarburos y CO₂ al bajar la presión: "
        "dimensione con margen de apertura. El rehervidor no debe pasar de ~ 204 °C (degradación). "
        + _SERV_GLICOL),
    _glicol("Tetraetilenglicol (TREG)", "Tetraethylene glycol", "TREG", [
        ("TREG pobre 99,5 % (deshidratación)", 99.5, (), "", 220), ("TREG rico 97 %", 97, _RICO, "", 220),
        ("TREG 95 % (solvente de extracción de aromáticos)", 95, (HC,), "Proceso de extracción de BTX.", 220),
        ("TREG puro (≥ 99,5 %)", 99.8, (), "", 220)],
        "Tetraetilenglicol: deshidratación profunda de gas y solvente de extracción de aromáticos.", _SERV_GLICOL),
]

AZUFRE = FluidoProceso(
    "Azufre líquido", "Liquid sulfur", GRUPOS[5], "azufre", "L", "Otro", "No", (
        Presentacion("Azufre líquido sin desgasificar (H₂S 250 a 300 ppm)", dict(h2s_ppm=300),
                     (("azufre", "% p/p", 100, "Orgánica líquida"), ("h2s", "ppmv", 300, "Gas / vapor")),
                     "Sale de los condensadores de la planta Claus.", toxico=True, T_min_C=120, T_max_C=155),
        Presentacion("Azufre líquido desgasificado (H₂S < 10 ppm)", dict(h2s_ppm=10),
                     (("azufre", "% p/p", 100, "Orgánica líquida"),), "Producto de la fosa desgasificada.",
                     T_min_C=120, T_max_C=155),
    ), "Azufre fundido de la recuperación de azufre (Claus).",
    "Solidifica a ~ 119 °C y polimeriza por encima de ~ 159 °C (la viscosidad sube de 7 a más de 90.000 cP): "
    "opere entre 125 y 155 °C con válvulas encamisadas en vapor de 3,5 a 4,5 bar g (camisa completa, sin tramos "
    "ciegos). Cuerpo de acero al carbono; empaquetadura de grafito; preferibles válvulas de tapón o bola "
    "encamisadas y globo de paso amplio. El H₂S disuelto se libera en la fosa y en la válvula (tóxico).")

POLIMEROS = [
    FluidoProceso("Polímero aniónico (floculante)", "Anionic polymer", GRUPOS[6], "solucion", "L", "Agua", "Sí", (
        Presentacion("Solución diluida 0,1 %", dict(rho20=1000.0, mu20=15.0, mu80=5.0)),
        Presentacion("Solución madre 0,5 %", dict(rho20=1001.0, mu20=150.0, mu80=60.0)),
        Presentacion("Emulsión concentrada (producto puro)", dict(rho20=1040.0, mu20=1000.0, mu80=250.0), (HC,),
                     "Emulsión inversa en aceite mineral."),
    ), "Poliacrilamida aniónica para floculación (tratamiento de agua y efluentes).",
        "No newtoniano (pseudoplástico): la viscosidad indicada es la aparente a bajo corte, conservadora para el "
        "Cv. El corte intenso en la válvula rompe las cadenas del polímero: prefiera ΔP bajas, válvulas de paso "
        "amplio (diafragma, pinch o bola segmentada) o regular con la velocidad de la bomba.",
        param=dict(directo=True)),
    FluidoProceso("Polímero catiónico (floculante / coagulante)", "Cationic polymer", GRUPOS[6], "solucion", "L",
                  "Agua", "Sí", (
                      Presentacion("Floculante catiónico, solución 0,1 %", dict(rho20=1000.0, mu20=15.0, mu80=5.0),
                                   (("cloruros", "mg/L", 50, "Acuosa"),)),
                      Presentacion("Floculante catiónico, solución madre 0,5 %",
                                   dict(rho20=1001.0, mu20=150.0, mu80=60.0), (("cloruros", "mg/L", 250, "Acuosa"),)),
                      Presentacion("Emulsión concentrada (producto puro)", dict(rho20=1050.0, mu20=1200.0, mu80=300.0),
                                   (HC, ("cloruros", "mg/L", 30000, "Acuosa"))),
                      Presentacion("Coagulante poliamina / poliDADMAC 40 %", dict(rho20=1100.0, mu20=600.0, mu80=120.0),
                                   (("cloruros", "mg/L", 90000, "Acuosa"),),
                                   "El contraión cloruro llega a ~ 9 % en el producto."),
                  ), "Polímeros catiónicos para coagulación y floculación.",
                  "Igual que el aniónico (no newtoniano, sensible al corte). Los catiónicos llevan cloruros: con el "
                  "producto concentrado el inoxidable 316 puede picarse; use PVC / CPVC, PTFE o dúplex.",
                  param=dict(directo=True)),
]

SLURRY = FluidoProceso(
    "Slurry", "Slurry", GRUPOS[7], "petroleo", "L", "Slurry", "Desconocida", (
        _corte("Aceite decantado de FCC (con finos de catalizador)", 2, 10.6, [(50, 200.0), (100, 25.0)], S=2.0,
               solidos=3000, T_min=10,
               nota="Fondo de la fraccionadora de FCC: aromático, con 500 a 5.000 ppm de finos de catalizador."),
        Presentacion("Slurry acuoso 5 % de sólidos", dict(solidos=5.0), (("solidos", "mg/L", 50000, "Sólida"),),
                     modelo="slurry"),
        Presentacion("Slurry acuoso 15 % de sólidos", dict(solidos=15.0), (("solidos", "mg/L", 150000, "Sólida"),),
                     modelo="slurry"),
        Presentacion("Slurry acuoso 30 % de sólidos", dict(solidos=30.0), (("solidos", "mg/L", 300000, "Sólida"),),
                     modelo="slurry"),
    ), "Líquido con sólidos abrasivos: aceite de FCC con catalizador o sólidos en agua (lodos, pulpas).",
    "Erosivo: cuerpo de ángulo con flujo hacia el obturador, trim de Stellite, carburo de tungsteno o cerámica, "
    "velocidad baja y salida expandida; evite trims de jaula de orificios chicos. Para el slurry de FCC la "
    "práctica es la válvula de ángulo con trim endurecido. N25 marca sólidos presentes en 3-Materiales.")

CATALOGO: dict[str, FluidoProceso] = {f.nombre: f for f in (
    [CRUDOS] + _CORTES + [SLURRY] + GASES + _LIV + AMINAS + GLICOL_FLUIDOS + QUIMICOS + [AZUFRE] + POLIMEROS)}

# Las mezclas se registran en la biblioteca de propiedades (composición típica = primera presentación)
for _f in CATALOGO.values():
    if _f.modelo == "mezcla":
        P.MEZCLAS[_f.nombre] = dict(_f.presentaciones[0].datos["comp"])
        P.FLUIDOS.setdefault(_f.nombre, "")


def es_proceso(nombre: str | None) -> bool:
    return nombre in CATALOGO


def es_liquido_proceso(nombre: str | None) -> bool:
    """Fluido de proceso con modelo propio de líquido (no CoolProp)."""
    f = CATALOGO.get(nombre)
    return f is not None and f.modelo != "mezcla"


def presentaciones(nombre: str) -> list[str]:
    return [p.nombre for p in CATALOGO[nombre].presentaciones]


def admite(nombre: str, tipo: str) -> bool:
    f = CATALOGO.get(nombre)
    if f is None:
        return True
    return ("L" in f.tipos) if tipo == "liquido" else ("G" in f.tipos)


# ------------------------------------------------------------------------- texto de caracterización
def _n(x, d=3):
    """Número para mostrar: d cifras significativas, coma decimal y punto de miles."""
    if x is None:
        return "—"
    if abs(x) >= 10 ** d:
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:.{d}g}".replace(".", ",")


def _t(x):
    """Número para la línea de caracterización (editable): sin separador de miles."""
    return (f"{x:.0f}" if abs(x) >= 1000 else f"{x:.4g}").replace(".", ",")


def _num(t: str) -> float:
    """Acepta coma o punto decimal; con los dos, el punto es separador de miles."""
    t = t.strip()
    if "," in t and "." in t:
        t = t.replace(".", "")
    return float(t.replace(",", "."))


def texto_por_defecto(nombre: str, presentacion: str | None) -> str:
    """Texto inicial de la línea de caracterización (o de composición) para la presentación."""
    f = CATALOGO[nombre]
    p = f.presentacion(presentacion)
    d = p.datos
    modelo = p.modelo or f.modelo
    if modelo == "mezcla":
        return P.texto_composicion(d["comp"])
    if modelo == "petroleo":
        partes = [f"API {_t(d['API'])}", f"Kw {_t(d['Kw'])}"]
        partes += [f"ν {_t(v)} cSt a {_t(t)} °C" for t, v in d["nu"]]
        if "RVP" in d:
            partes.append(f"RVP {_t(d['RVP'])} psi")
        if "S" in d:
            partes.append(f"S {_t(d['S'])} %")
        if "TAN" in d:
            partes.append(f"TAN {_t(d['TAN'])}")
        return "; ".join(partes)
    if modelo in ("solucion", "glicol"):
        if f.param.get("directo"):
            return f"μ {_t(d['mu20'])} cP a 20 °C"
        return f"Concentración {_t(d['conc'])} %"
    if modelo == "slurry":
        return f"Sólidos {_t(d['solidos'])} %; ρs 2.650 kg/m³"
    return ""


_PAT = [
    ("API", re.compile(r"^API\s*(-?[\d.,]+)$", re.I)),
    ("SG", re.compile(r"^SG\s*([\d.,]+)$", re.I)),
    ("Kw", re.compile(r"^(?:Kw|K)\s*([\d.,]+)$", re.I)),
    ("RVP", re.compile(r"^RVP\s*([\d.,]+)\s*(psi|kpa)?$", re.I)),
    ("nu", re.compile(r"^(?:ν|nu|visc\w*)\s*([\d.,]+)\s*(?:cst)?\s*a\s*(-?[\d.,]+)\s*°?\s*(c|f)?$", re.I)),
    ("mu", re.compile(r"^(?:μ|mu)\s*([\d.,]+)\s*(?:cp)?(?:\s*a\s*(-?[\d.,]+)\s*°?\s*(c|f)?)?$", re.I)),
    ("S", re.compile(r"^(?:S|azufre)\s*([\d.,]+)\s*%?$", re.I)),
    ("TAN", re.compile(r"^TAN\s*([\d.,]+)(?:\s*mg\s*KOH/g)?$", re.I)),
    ("conc", re.compile(r"^(?:concentraci[oó]n|conc\.?|c)\s*([\d.,]+)\s*%?$", re.I)),
    ("solidos", re.compile(r"^s[oó]lidos\s*([\d.,]+)\s*%?$", re.I)),
    ("rhos", re.compile(r"^(?:ρs|rhos)\s*([\d.,]+)\s*(?:kg/m³|kg/m3)?$", re.I)),
]


def _TC(v, u):
    return (v - 32) / 1.8 if (u or "c").lower() == "f" else v


def leer_texto(nombre: str, presentacion: str | None, texto: str | None) -> dict:
    """Datos del modelo: los de la presentación, reemplazados por los que el usuario escribió."""
    f = CATALOGO[nombre]
    p = f.presentacion(presentacion)
    d = {k: (list(v) if isinstance(v, list) else v) for k, v in p.datos.items()}
    t = (texto or "").strip()
    if not t or f.modelo == "mezcla":
        return d
    nus = []
    for parte in t.replace("\n", ";").split(";"):
        parte = parte.strip()
        if not parte:
            continue
        for clave, pat in _PAT:
            m = pat.match(parte)
            if not m:
                continue
            try:
                if clave == "nu":
                    nus.append((_TC(_num(m.group(2)), m.group(3)), _num(m.group(1))))
                elif clave == "mu":
                    d["mu_usuario"] = (_num(m.group(1)), _TC(_num(m.group(2)), m.group(3)) if m.group(2) else 20.0)
                elif clave == "RVP":
                    v = _num(m.group(1))
                    d["RVP"] = v / PSI if (m.group(2) or "").lower() == "kpa" else v
                    d.setdefault("pendiente", 3.0)
                elif clave == "SG":
                    d["API"] = 141.5 / _num(m.group(1)) - 131.5
                else:
                    d[clave] = _num(m.group(1))
            except ValueError:
                break
            break
        else:
            raise ErrorFluido(
                f"Caracterización de {nombre}: no se entiende «{parte}». Escriba los datos separados por punto y "
                "coma, por ejemplo «API 16; ν 250 cSt a 50 °C; ν 35 cSt a 100 °C; RVP 5 psi; S 3,5 %; TAN 2» o "
                "«Concentración 47 %».")
    if nus:
        if len(nus) == 1:
            d["nu_uno"] = nus[0]
        else:
            nus.sort()
            d["nu"] = [nus[0], nus[-1]]
    _validar(nombre, d)
    return d


def _validar(nombre, d):
    if "API" in d and not -10 <= d["API"] <= 100:
        raise ErrorFluido(f"{nombre}: el grado API debe estar entre −10 y 100.")
    if "Kw" in d and not 9.5 <= d["Kw"] <= 13.5:
        raise ErrorFluido(f"{nombre}: el factor de Watson Kw debe estar entre 9,5 y 13,5 (típico 10,5 a 12,5).")
    if "conc" in d and not 0 <= d["conc"] <= 100:
        raise ErrorFluido(f"{nombre}: la concentración debe estar entre 0 y 100 %.")
    if "solidos" in d and not 0 <= d["solidos"] < 70:
        raise ErrorFluido(f"{nombre}: los sólidos deben estar entre 0 y 70 % en masa.")
    for t, v in d.get("nu", []):
        if v <= 0:
            raise ErrorFluido(f"{nombre}: la viscosidad cinemática debe ser positiva.")
    if len(d.get("nu", [])) == 2 and d["nu"][0][0] == d["nu"][1][0]:
        raise ErrorFluido(f"{nombre}: las dos viscosidades deben estar a temperaturas distintas.")
    if "RVP" in d and not 0 < d["RVP"] <= 20:
        raise ErrorFluido(f"{nombre}: el RVP debe estar entre 0 y 20 psi (la correlación de AP-42 vale de 2 a 15).")


# --------------------------------------------------------------------------------------- agua (CoolProp)
def _agua(T_K, P_kPa=101.325):
    """ρ, μ y Pv del agua líquida a T (si P < Pv se toma líquido saturado)."""
    if not P.DISPONIBLE:
        raise ErrorFluido("La biblioteca de propiedades no está disponible: ingrese las propiedades manualmente.")
    CP = P.CP
    Pv = CP.PropsSI("P", "T", T_K, "Q", 0, "Water") / 1000 if T_K < 647.0 else PC_AGUA
    if P_kPa > Pv * 1.0001:
        rho = CP.PropsSI("D", "T", T_K, "P", P_kPa * 1000, "Water")
        mu = CP.PropsSI("V", "T", T_K, "P", P_kPa * 1000, "Water")
    else:
        rho = CP.PropsSI("D", "T", T_K, "Q", 0, "Water")
        mu = CP.PropsSI("V", "T", T_K, "Q", 0, "Water")
    return rho, mu, Pv


@dataclass
class ResultadoLiquido:
    rho: float                  # kg/m³
    mu: float                   # Pa·s
    Pv: float                   # kPa a
    Pc: float                   # kPa a
    M: float | None = None      # kg/kmol
    Tc: float | None = None     # K
    metodo: str = ""
    notas: list = field(default_factory=list)

    @property
    def SG(self):
        return self.rho / RHO_AGUA_15C

    @property
    def nu_cSt(self):
        return self.mu / self.rho * 1e6


# ------------------------------------------------------------------------------- petróleo (pseudocomponente)
# API MPMS 11.1 (1980): α60 = K0/ρ60² + K1/ρ60 (ρ60 en kg/m³), ΔT en °F
_K_API = {"crudo": (341.0957, 0.0), "fuel": (103.8720, 0.2701), "jet": (330.3010, 0.0),
          "gasolina": (192.4571, 0.2438)}


def _alfa60(rho60, crudo):
    if crudo:
        k0, k1 = _K_API["crudo"]
    elif rho60 >= 838.3:
        k0, k1 = _K_API["fuel"]
    elif rho60 >= 787.5:
        k0, k1 = _K_API["jet"]
    elif rho60 >= 770.4:
        return -0.00336312 + 2680.3206 / rho60 ** 2
    else:
        k0, k1 = _K_API["gasolina"]
    return k0 / rho60 ** 2 + k1 / rho60


def pseudo(API: float, Kw: float) -> dict:
    """SG, Tb, M, Tc, Pc y ω del pseudocomponente (Watson, Riazi-Daubert, Kesler-Lee)."""
    SG = 141.5 / (API + 131.5)
    TbR = (Kw * SG) ** 3
    Tb = TbR / 1.8
    M = 42.965 * math.exp(2.097e-4 * Tb - 7.78712 * SG + 2.08476e-3 * Tb * SG) * Tb ** 1.26007 * SG ** 4.98308
    TcR = 341.7 + 811 * SG + (0.4244 + 0.1174 * SG) * TbR + (0.4669 - 3.2623 * SG) * 1e5 / TbR
    lnPc = (8.3634 - 0.0566 / SG - (0.24244 + 2.2898 / SG + 0.11857 / SG ** 2) * 1e-3 * TbR
            + (1.4685 + 3.648 / SG + 0.47227 / SG ** 2) * 1e-7 * TbR ** 2
            - (0.42019 + 1.6977 / SG ** 2) * 1e-10 * TbR ** 3)
    Pc_psia = math.exp(lnPc)
    Tbr = TbR / TcR
    if Tbr < 0.8:
        w = ((-math.log(Pc_psia / 14.696) - 5.92714 + 6.09648 / Tbr + 1.28862 * math.log(Tbr) - 0.169347 * Tbr ** 6)
             / (15.2518 - 15.6875 / Tbr - 13.4721 * math.log(Tbr) + 0.43577 * Tbr ** 6))
    else:
        w = -7.904 + 0.1352 * Kw - 0.007465 * Kw ** 2 + 8.359 * Tbr + (1.408 - 0.01063 * Kw) / Tbr
    return dict(SG=SG, Tb=Tb, M=M, Tc=TcR / 1.8, Pc=Pc_psia * PSI, w=w)


def _pv_lee_kesler(T_K, ps):
    Tr = T_K / ps["Tc"]
    if Tr >= 1:
        return ps["Pc"]
    f0 = 5.92714 - 6.09648 / Tr - 1.28862 * math.log(Tr) + 0.169347 * Tr ** 6
    f1 = 15.2518 - 15.6875 / Tr - 13.4721 * math.log(Tr) + 0.43577 * Tr ** 6
    return ps["Pc"] * math.exp(f0 + ps["w"] * f1)


def _tvp_ap42(T_K, RVP, crudo, S=3.0):
    """Presión de vapor verdadera (kPa a) desde el RVP (psi): EPA AP-42 cap. 7.1, ec. 1-24 (crudos) y 1-25 / 1-26
    (productos refinados, S = pendiente ASTM D86 al 10 % evaporado, °F/% vol)."""
    TR = T_K * 1.8
    lr = math.log(RVP)
    if crudo:
        A, B = 12.82 - 0.9672 * lr, 7261 - 1216 * lr
    else:
        s = math.sqrt(S)
        A = 15.64 - 1.854 * s - (0.8742 - 0.3280 * s) * lr
        B = 8742 - 1042 * s - (1049 - 179.4 * s) * lr
    return math.exp(A - B / TR) * PSI


def _walther(nu_pts, nu_uno=None):
    (t1, n1), (t2, n2) = nu_pts
    T1, T2 = t1 + 273.15, t2 + 273.15
    B = (_loglog(n1) - _loglog(n2)) / (math.log10(T2) - math.log10(T1))
    A = _loglog(n1) + B * math.log10(T1)
    if nu_uno:                       # un solo dato del usuario: misma pendiente B que la típica
        t, n = nu_uno
        A = _loglog(n) + B * math.log10(t + 273.15)
    return A, B


def nu_walther(T_K, A, B):
    return 10 ** (10 ** (A - B * math.log10(T_K))) - 0.7


def _petroleo(d, T_K, P_kPa):
    ps = pseudo(d["API"], d["Kw"])
    rho60 = ps["SG"] * 999.016
    a = _alfa60(rho60, d.get("crudo", False))
    dT = T_K * 1.8 - 459.67 - 60
    rho = rho60 * math.exp(-a * dT * (1 + 0.8 * a * dT))
    A, B = _walther(d["nu"], d.get("nu_uno"))
    nu = nu_walther(T_K, A, B)
    mu = nu * 1e-6 * rho
    Pv = _pv_lee_kesler(T_K, ps)
    metodo = "pseudocomponente (Watson, Riazi-Daubert, Kesler-Lee); ρ API MPMS 11.1; ν ASTM D341"
    if d.get("RVP"):
        Pv = max(Pv, _tvp_ap42(T_K, d["RVP"], d.get("crudo", False), d.get("pendiente", 3.0)))
        metodo += "; Pv verdadera desde el RVP (EPA AP-42 7.1)"
    else:
        metodo += "; Pv Lee-Kesler"
    notas = []
    if T_K - 273.15 > 150:
        notas.append("Densidad y presión de vapor extrapoladas por encima de 150 °C: use datos del proceso si los hay.")
    return ResultadoLiquido(rho, mu, Pv, ps["Pc"], ps["M"], ps["Tc"], metodo, notas)


# --------------------------------------------------------------------------------------- soluciones
def _fila(tabla, c):
    """Fila interpolada en la concentración (ρ y a_w lineales, μ logarítmica)."""
    c = min(max(c, tabla[0][0]), tabla[-1][0])
    out = [c]
    for col in range(1, len(tabla[0])):
        log = col in (2, 3)
        out.append(_interp(tabla, c, col, log))
    return out


def _andrade(mu20, mu80, T_K):
    b = math.log(mu20 / mu80) / (1 / 293.15 - 1 / 353.15)
    return mu20 * math.exp(b * (1 / T_K - 1 / 293.15))


def _solucion(f, d, T_K, P_kPa):
    rw, muw, Pvw = _agua(T_K, P_kPa)
    rw20 = _agua(293.15)[0]
    notas = []
    if f.param.get("directo"):
        rho20, mu20, mu80, aw, ps, M = d["rho20"], d["mu20"], d["mu80"], 1.0, 0.0, None
        metodo = "viscosidad aparente típica del producto a bajo corte"
    else:
        sol = f.param.get("soluto")
        tabla = f.param["tablas"][d["amina"]] if sol == "amina" else f.param["tabla"]
        fila = _fila(tabla, d["conc"])
        rho20, mu20, mu80, aw = fila[1:5]
        ps = fila[5] if len(fila) > 5 else 0.0
        if d.get("rica"):
            rho20, mu20, mu80 = rho20 * 1.03, mu20 * 1.15, mu80 * 1.15
            notas.append("Amina rica: densidad +3 % y viscosidad +15 % por la carga de gases ácidos (≈ 0,4 mol/mol).")
        Ms = M_SOLUTO.get(d.get("amina", sol), 100.0)
        w = d["conc"] / 100
        M = 1 / (w / Ms + (1 - w) / 18.015)
        metodo = "tablas de datos publicados (20 y 80 °C, Andrade); Pv = a_w · Pv del agua"
        if d["conc"] > tabla[-1][0] or d["conc"] < tabla[0][0]:
            notas.append(f"Concentración fuera de la tabla ({_n(tabla[0][0])} a {_n(tabla[-1][0])} %): se usa el "
                         "extremo más cercano.")
    if d.get("mu_usuario"):
        mu_u, t_u = d["mu_usuario"]
        f_T = _andrade(mu20, mu80, T_K) / _andrade(mu20, mu80, t_u + 273.15)
        mu_cP = mu_u * f_T
        notas.append("Viscosidad del usuario, corregida por temperatura con la pendiente de la tabla.")
    else:
        mu_cP = _andrade(mu20, mu80, T_K)
    rho = rho20 * rw / rw20
    Pv = aw * Pvw + ps * math.exp(7000 * (1 / 293.15 - 1 / T_K))
    if T_K - 273.15 > 100:
        notas.append("Por encima de 100 °C la viscosidad se extrapola (ecuación de Andrade).")
    return ResultadoLiquido(rho, mu_cP / 1000, Pv, PC_AGUA, M, None, metodo, notas)


def _glicol_calc(f, d, T_K, P_kPa):
    g = f.param["glicol"]
    Mg, rg20, mug20, mug80, beta, Tb, Pcg = GLICOLES[g]
    w = d["conc"] / 100
    rw, muw, Pvw = _agua(T_K, P_kPa)
    tC = T_K - 273.15
    notas = []
    rho = mu = None
    metodo = ""
    if g in ("MEG", "MPG") and w <= 0.6 and P.DISPONIBLE:
        try:
            n = f"INCOMP::{g}-{d['conc']:g}%"
            rho = P.CP.PropsSI("D", "T", T_K, "P", max(P_kPa, 101.325) * 1000, n)
            mu = P.CP.PropsSI("V", "T", T_K, "P", max(P_kPa, 101.325) * 1000, n)
            metodo = f"CoolProp, solución acuosa {g} (Melinder / SecCool)"
        except Exception:
            rho = mu = None
    if rho is None:
        rg = rg20 / (1 + beta * (tC - 20))
        rho = 1 / (w / rg + (1 - w) / rw)
        mug = _andrade(mug20, mug80, T_K) / 1000
        mu = math.exp(w * math.log(mug) + (1 - w) * math.log(muw))
        metodo = "glicol puro (20 y 80 °C, Andrade) con mezcla ideal y regla logarítmica en masa"
        if tC > 100:
            notas.append("Viscosidad extrapolada por encima de 100 °C (Andrade): orden de magnitud.")
    xw = (1 - w) / 18.015 / ((1 - w) / 18.015 + w / Mg) if w < 1 else 0.0
    Pg = 101.325 * math.exp(110 * Tb / R * (1 / Tb - 1 / T_K))          # Trouton-Kistiakowsky (ΔS ≈ 110 J/mol·K)
    Pv = xw * Pvw + (1 - xw) * Pg
    Pc = xw * PC_AGUA + (1 - xw) * Pcg
    M = 1 / (w / Mg + (1 - w) / 18.015)
    metodo += "; Pv por Raoult"
    return ResultadoLiquido(rho, mu, Pv, Pc, M, None, metodo, notas)


_MU_AZUFRE = [(115, 20.0), (120, 16.0), (125, 12.5), (130, 10.4), (135, 9.0), (140, 8.2), (145, 7.6), (150, 7.1),
              (155, 6.8), (157, 6.6), (158, 7.5), (159, 30.0), (160, 100.0), (165, 5000.0), (170, 30000.0),
              (180, 80000.0), (187, 93000.0), (200, 60000.0), (250, 8000.0), (300, 1500.0)]


def _azufre(d, T_K, P_kPa):
    tC = T_K - 273.15
    if tC < 115:
        raise ErrorFluido(f"A {tC:.1f} °C el azufre es sólido (funde a ~ 115 a 119 °C): opere entre 125 y 155 °C.")
    rho = 1899.0 - 0.80 * tC
    mu = _interp(_MU_AZUFRE, tC, 1, log=True) / 1000
    Pv = 101.325 * math.exp(70000 / R * (1 / 717.8 - 1 / T_K))
    return ResultadoLiquido(rho, mu, Pv, 20700.0, 256.5, 1314.0,
                            "datos publicados del azufre líquido (densidad lineal, viscosidad tabulada)")


def _slurry(d, T_K, P_kPa):
    rw, muw, Pvw = _agua(T_K, P_kPa)
    w = d["solidos"] / 100
    rs = d.get("rhos", 2650.0)
    rho = 1 / (w / rs + (1 - w) / rw)
    phi = (w / rs) / (w / rs + (1 - w) / rw)
    mu = muw * (1 + 2.5 * phi + 10.05 * phi ** 2 + 0.00273 * math.exp(16.6 * phi))
    return ResultadoLiquido(rho, mu, Pvw, PC_AGUA, None, None,
                            "agua con sólidos: densidad de la mezcla y viscosidad de Thomas (1965)",
                            [f"Fracción de sólidos en volumen φ = {_n(phi * 100)} %."])


def liquido(nombre: str, presentacion: str | None, P1_kPa: float, T1_K: float, texto: str | None = "") -> ResultadoLiquido:
    """Propiedades del fluido de proceso como líquido a la entrada."""
    f = CATALOGO[nombre]
    if "L" not in f.tipos:
        raise ErrorFluido(f"{nombre} es un gas: elija el tipo de fluido Gas.")
    p = f.presentacion(presentacion)
    modelo = p.modelo or f.modelo
    if modelo == "mezcla":
        comp = P.leer_composicion(texto, nombre) if (texto or "").strip() else dict(p.datos["comp"])
        pl = P.liquido(nombre, P1_kPa, T1_K, comp)
        n = P._cp_nombre(nombre, comp)
        return ResultadoLiquido(pl.rho, pl.mu, pl.Pv, pl.Pc, P.CP.PropsSI("M", n) * 1000, None,
                                "ecuación de estado de CoolProp (mezcla); Pv = presión de burbuja")
    d = leer_texto(nombre, presentacion, texto)
    try:
        if modelo == "petroleo":
            r = _petroleo(d, T1_K, P1_kPa)
        elif modelo == "solucion":
            r = _solucion(f, d, T1_K, P1_kPa)
        elif modelo == "glicol":
            r = _glicol_calc(f, d, T1_K, P1_kPa)
        elif modelo == "azufre":
            r = _azufre(d, T1_K, P1_kPa)
        elif modelo == "slurry":
            r = _slurry(d, T1_K, P1_kPa)
        else:
            raise ErrorFluido(f"Modelo desconocido: {modelo}")
    except (ValueError, OverflowError, ZeroDivisionError) as e:
        if isinstance(e, P.ErrorPropiedades):
            raise
        raise ErrorFluido(f"No se pudieron estimar las propiedades de {nombre} a {T1_K - 273.15:.1f} °C: {e}") from None
    if r.Pv >= P1_kPa:
        raise ErrorFluido(
            f"A {T1_K - 273.15:.1f} °C la presión de vapor estimada de {nombre} ({p.nombre}) es {r.Pv:.1f} kPa a, "
            f"mayor que P1 = {P1_kPa:.1f} kPa a: el fluido hierve a la entrada. Revise la temperatura, la presión "
            "o el RVP de la caracterización.")
    return r


def resumen(nombre: str, presentacion: str | None, texto: str | None = "") -> str:
    """Línea corta con lo que define la caracterización (para mostrar debajo de la línea de datos)."""
    f = CATALOGO[nombre]
    p = f.presentacion(presentacion)
    modelo = p.modelo or f.modelo
    try:
        if modelo == "mezcla":
            comp = P.leer_composicion(texto, nombre) if (texto or "").strip() else dict(p.datos["comp"])
            M = P.masa_molar_mezcla(comp)
            return f"M = {_n(M)} kg/kmol · SG del gas = {_n(M / 28.9647)}"
        d = leer_texto(nombre, presentacion, texto)
        if modelo == "petroleo":
            ps = pseudo(d["API"], d["Kw"])
            return (f"SG 15 °C = {_n(ps['SG'], 4)} · Tb ≈ {_n(ps['Tb'] - 273.15)} °C · M ≈ {_n(ps['M'])} kg/kmol · "
                    f"Pc ≈ {_n(ps['Pc'])} kPa a. Valores típicos: reemplácelos con los del laboratorio.")
        r = liquido(nombre, presentacion, 1000.0, 293.15 if modelo != "azufre" else 408.15, texto)
        t = "135 °C" if modelo == "azufre" else "20 °C"
        return f"A {t}: SG = {_n(r.SG, 4)} · μ = {_n(r.mu * 1000)} cP. Datos aproximados de tablas publicadas."
    except P.ErrorPropiedades as e:
        return str(e)


# ------------------------------------------------------------------------------------ materiales y empaques
_IMPL: dict[str, list] = {}
_TOX: dict[str, bool] = {}


def nombre_materiales(nombre: str, presentacion: str | None) -> str:
    return f"{nombre} — {CATALOGO[nombre].presentacion(presentacion).nombre}"


def _agentes(f: FluidoProceso, p: Presentacion, d: dict) -> list:
    out = []
    for clave, u, v, fase in p.agentes:
        if clave == "azufre_hc" and "S" in d:
            v = d["S"]
        elif clave == "tan" and "TAN" in d:
            v = d["TAN"]
        elif "conc" in d and clave in ("naoh", "h2so4", "h3po4", "fecl3", "hcl", "hno3", "aminas", "glicoles"):
            v = d["conc"]
        elif clave == "hipoclorito" and "conc" in d:
            v = round(d["conc"] * 0.952, 2)
        out.append((clave, u, v, fase))
    claves = {a[0] for a in out}
    if "S" in d and "azufre_hc" not in claves and f.modelo == "petroleo" and p.modelo is None:
        out.append(("azufre_hc", "% p/p", d["S"], "Orgánica líquida"))
    if "TAN" in d and "tan" not in claves and f.modelo == "petroleo" and p.modelo is None:
        out.append(("tan", "mg KOH/g", d["TAN"], "Orgánica líquida"))
    return [a for a in out if a[2]]


def para_materiales(nombre: str, presentacion: str | None, texto: str | None, tipo: str, agua_libre: str) -> dict:
    """Familia, nombre, fase, agua libre y agentes implícitos que el fluido de proceso aporta a 3-Materiales."""
    f = CATALOGO[nombre]
    p = f.presentacion(presentacion)
    try:
        d = leer_texto(nombre, p.nombre, texto)
    except P.ErrorPropiedades:
        d = dict(p.datos)
    mat = nombre_materiales(nombre, p.nombre)
    ag = _agentes(f, p, d)
    if (p.modelo or f.modelo) == "mezcla" and (texto or "").strip():
        try:
            comp = P.leer_composicion(texto, nombre)
            ag = [a for a in ag if a[0] not in ("h2s", "co2", "h2", "nh3", "o2")] + list(_gas_ag(comp))
        except P.ErrorPropiedades:
            pass
    _IMPL[mat] = ag
    _TOX[mat] = p.toxico if p.toxico is not None else f.toxico
    fase = "Líquido" if tipo == "liquido" else ("Vapor" if tipo == "vapor" else "Gas")
    acuosa = "Sí" if f.agua == "Sí" else agua_libre
    familia = f.familia
    if f.nombre == "Slurry" and p.modelo == "slurry":
        familia = "Slurry"
    return dict(familia=familia, fluido=mat, fase=fase, acuosa=acuosa, agentes=ag)


def implicitos(mat: str) -> list:
    """Agentes implícitos del fluido de proceso (para la selección de materiales)."""
    if mat not in _IMPL:
        nombre, _, pres = mat.partition(" — ")
        if nombre in CATALOGO:
            para_materiales(nombre, pres, "", "liquido" if "L" in CATALOGO[nombre].tipos else "gas", "Desconocida")
    return list(_IMPL.get(mat, []))


def es_toxico(mat: str) -> bool:
    if mat not in _TOX:
        implicitos(mat)
    return _TOX.get(mat, False)


def agua_libre(nombre: str, presentacion: str | None) -> tuple[str, bool]:
    """(agua libre sugerida, fija)."""
    f = CATALOGO[nombre]
    return (f.agua, f.agua == "Sí")


# ---------------------------------------------------------------------------------------------- alertas
def alertas(nombre: str, presentacion: str | None, texto: str | None, T1s_K: list, tipo: str) -> list[Alerta]:
    f = CATALOGO.get(nombre)
    if f is None:
        return []
    p = f.presentacion(presentacion)
    modelo = p.modelo or f.modelo
    out = []
    ts = [t - 273.15 for t in T1s_K if t]
    ref = "Fluidos de proceso (N25)"
    if ts and p.T_min_C is not None and min(ts) < p.T_min_C + (5 if modelo == "azufre" else 0):
        sev = Severidad.CRITICA if modelo == "azufre" else Severidad.ADVERTENCIA
        out.append(Alerta("fp_solidifica", sev, "Riesgo de solidificación o cristalización",
                          f"{nombre} ({p.nombre}) a {min(ts):.0f} °C: por debajo de ~ {p.T_min_C:.0f} °C solidifica, "
                          "cristaliza o deja de fluir (punto de fluidez).",
                          remedios=["Trazar o encamisar la línea y la válvula para mantener la temperatura.",
                                    "Verificar el punto de fluidez o de cristalización con el certificado."],
                          referencia=ref))
    if ts and p.T_max_C is not None and max(ts) > p.T_max_C:
        if modelo == "azufre":
            sev = Severidad.CRITICA if max(ts) > 159 else Severidad.ADVERTENCIA
            txt = (f"Azufre a {max(ts):.0f} °C: por encima de ~ 159 °C polimeriza y la viscosidad sube a miles de cP "
                   "(hasta ~ 93.000 cP a 187 °C).")
        else:
            sev = Severidad.ADVERTENCIA
            txt = (f"{nombre} ({p.nombre}) a {max(ts):.0f} °C: por encima de ~ {p.T_max_C:.0f} °C se degrada o "
                   "se descompone.")
        out.append(Alerta("fp_temperatura_alta", sev, "Temperatura por encima del rango del fluido", txt,
                          remedios=["Revisar la temperatura de operación.",
                                    "Para el azufre: camisa de vapor de 3,5 a 4,5 bar g (≈ 140 a 150 °C)."],
                          referencia=ref))
    if nombre == "Amina rica" or (f.modelo == "glicol" and "rico" in p.nombre.lower()):
        out.append(Alerta("fp_desgasificacion", Severidad.ADVERTENCIA, "Desgasificación en la válvula",
                          f"{nombre}: al bajar la presión libera los gases absorbidos (H₂S, CO₂, hidrocarburos) y el "
                          "flujo puede salir bifásico. La IEC 60534 para líquidos no lo cubre: el Cv real es mayor.",
                          remedios=["Dejar margen de apertura (≤ 70 a 80 % a caudal máximo).",
                                    "Ubicar la válvula cerca del separador flash, con salida expandida.",
                                    "Trim endurecido o de inoxidable 316 con Stellite."], referencia=ref))
    if f.grupo == GRUPOS[6]:
        out.append(Alerta("fp_polimero_corte", Severidad.INFO, "Polímero sensible al corte",
                          f"{nombre}: la viscosidad es aparente (no newtoniano) y el corte en la válvula degrada el "
                          "polímero.", remedios=["ΔP baja y válvula de paso amplio, o regular con la bomba."],
                          referencia=ref))
    if modelo != "mezcla":
        try:
            r = liquido(nombre, p.nombre, 1000.0, (ts[0] if ts else 20.0) + 273.15, texto)
            metodo = r.metodo
        except P.ErrorPropiedades:
            metodo = modelo
        out.append(Alerta("fp_propiedades_estimadas", Severidad.INFO, "Propiedades estimadas del fluido de proceso",
                          f"{nombre} ({p.nombre}): SG, viscosidad, presión de vapor y Pc estimadas con {metodo}. "
                          "Son valores típicos; con datos del laboratorio o del proceso, cárguelos en la "
                          "caracterización del fluido.", referencia=ref))
    return out


def nota_servicio(nombre: str, presentacion: str | None = None) -> str:
    f = CATALOGO[nombre]
    p = f.presentacion(presentacion)
    return " ".join(x for x in (p.nota, f.servicio) if x)


def propiedades_punto(nombre: str, presentacion: str | None, P_kPa: float, T_K: float, texto: str | None = ""):
    """Filas (nombre, valor, magnitud, unidad) para la ventana de propiedades de fluidos."""
    r = liquido(nombre, presentacion, P_kPa, T_K, texto)
    filas = [("Fase", "Líquido", None, ""), ("Densidad", r.rho, "densidad", ""),
             ("Gravedad específica SG (agua a 15 °C = 1)", r.SG, None, "-"),
             ("Viscosidad dinámica", r.mu, "viscosidad_din", ""), ("Viscosidad cinemática", r.mu / r.rho,
                                                                      "viscosidad_cin", ""),
             ("Presión de vapor a T", r.Pv, "presion", ""), ("Presión crítica (pseudocrítica)", r.Pc, "presion", "")]
    if r.M:
        filas.append(("Masa molar", r.M, "masa_molar", ""))
    if r.Tc:
        filas.append(("Temperatura crítica (pseudocrítica)", r.Tc, "temperatura", ""))
    f = CATALOGO[nombre]
    p = f.presentacion(presentacion)
    if (p.modelo or f.modelo) == "petroleo":
        d = leer_texto(nombre, presentacion, texto)
        ps = pseudo(d["API"], d["Kw"])
        filas += [("Grado API", d["API"], None, "°API"), ("Factor de Watson Kw", d["Kw"], None, "-"),
                  ("Temperatura de ebullición media Tb", ps["Tb"], "temperatura", ""),
                  ("Factor acéntrico ω", ps["w"], None, "-")]
    filas.append(("Método", r.metodo, None, ""))
    return filas
