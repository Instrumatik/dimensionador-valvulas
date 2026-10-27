"""Clasificación de los trims de la solapa 2 (v0.13.0).

Globo y ángulo (vástago deslizante), en el orden de los desplegables:

1. Tipo de trim: guiado por obturador o guiado por jaula.
2. Guiado por obturador: guía (superior reforzada, doble superior, superior e inferior, por el puerto,
   por el bonete) y obturador (contorneado, en V, microcaudal, disco plano; en ángulo, Venturi). La
   característica la da el perfil del obturador.
3. Guiado por jaula: la jaula guía al obturador, sujeta el asiento y da la característica. Las jaulas de
   bajo ruido solo se ofrecen con gas o vapor y las de anticavitación solo con líquido.
4. Nivel o etapas: cada nivel de una jaula especial se elige por separado, porque cada uno tiene su
   propia capacidad de mitigar el ruido o la cavitación.

Rotativas: un solo desplegable con el elemento de cierre (característica fija).

Cada combinación se traduce a la clave de ``estilos.ESTILOS`` (factores y capacidad del trim) y, en las
jaulas especiales, a la clave del nivel en ``anticavitacion.TRIMS`` (líquidos) o ``compresible.TRIMS_RUIDO``
(gases), que reemplaza FL, xT, Fd, Kc y la capacidad del trim.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import anticavitacion as AC, compresible as CG
from .estilos import CUERPOS, ESTILOS, geometria_sentido

TIPOS = {"obturador": "Guiado por obturador", "jaula": "Guiado por jaula"}

CARACT_CONTORNEADO = ("isoporcentual", "lineal", "apertura_rapida", "parabolica")


@dataclass(frozen=True)
class Guia:
    clave: str
    nombre: str
    obturadores: tuple
    nota: str


GUIAS: dict[str, Guia] = {g.clave: g for g in [
    Guia("superior_reforzada", "Superior reforzada (heavy top guided)", ("contorneado", "microcaudal", "disco_plano",
                                                                         "venturi"),
         "Un buje largo por encima del obturador. Servicio general, fluidos sucios o viscosos, tamaños chicos y "
         "medianos."),
    Guia("doble_superior", "Doble guía de vástago superior (double top stem guided)", ("contorneado",),
         "El obturador o el vástago se apoya en dos puntos de guiado separados, ambos por encima de la corriente "
         "del fluido."),
    Guia("superior_inferior", "Superior e inferior (top and bottom guided)", ("contorneado", "disco_plano",
                                                                              "venturi"),
         "Bujes por encima y por debajo del obturador. Tamaños grandes, ΔP altas y cuerpos de doble asiento."),
    Guia("puerto", "Por el puerto (port guided)", ("vport", "disco_plano"),
         "Faldas o aletas del obturador guiadas dentro del asiento. Servicio general con ΔP bajas; bajo costo."),
    Guia("bonete", "Por el bonete (bonnet / stem guided)", ("microcaudal", "contorneado"),
         "El buje del bonete guía al vástago. Válvulas chicas y de microcaudal."),
]}


@dataclass(frozen=True)
class Elemento:
    clave: str
    nombre: str
    tipo: str                   # «obturador» o «jaula»
    fluidos: str                # «L» líquido, «G» gas/vapor/steam
    caracteristicas: tuple
    nota: str = ""


ELEMENTOS: dict[str, Elemento] = {e.clave: e for e in [
    Elemento("contorneado", "Obturador contorneado", "obturador", "LG", CARACT_CONTORNEADO),
    Elemento("vport", "Obturador en V (V-port)", "obturador", "LG", ("isoporcentual", "lineal")),
    Elemento("microcaudal", "Obturador de microcaudal (aguja o ranurado)", "obturador", "LG",
             ("isoporcentual", "lineal")),
    Elemento("disco_plano", "Obturador de disco plano", "obturador", "LG", ("apertura_rapida",)),
    Elemento("venturi", "Obturador contorneado con salida Venturi", "obturador", "LG", ("lineal",)),
    Elemento("jaula_4v", "Jaula caracterizada de ventanas", "jaula", "LG",
             ("isoporcentual", "lineal", "apertura_rapida")),
    Elemento("jaula_retencion", "Jaula de retención de asiento, obturador contorneado", "jaula", "LG",
             CARACT_CONTORNEADO),
    Elemento("jaula_multiorificio", "Jaula multiorificio de bajo ruido", "jaula", "G", ("lineal", "isoporcentual")),
    Elemento("jaula_multietapa_gas", "Jaula multietapa multiorificio (bajo ruido)", "jaula", "G", ("lineal",)),
    Elemento("jaula_anticav", "Jaula anticavitación", "jaula", "L", ("lineal",)),
    Elemento("jaula_discos", "Discos apilados (laberinto)", "jaula", "LG", ("lineal",)),
    Elemento("jaula_pasajes", "Multietapa de pasajes grandes (sólidos)", "jaula", "L", ("lineal",)),
]}

_GLOBO = ("contorneado", "vport", "microcaudal", "disco_plano", "jaula_4v", "jaula_retencion",
          "jaula_multiorificio", "jaula_multietapa_gas", "jaula_anticav", "jaula_discos", "jaula_pasajes")
_ANGULO = ("contorneado", "venturi", "jaula_4v", "jaula_multiorificio", "jaula_multietapa_gas", "jaula_anticav",
           "jaula_discos", "jaula_pasajes")
POR_CUERPO = {"globo": _GLOBO, "angulo": _ANGULO, "globo_liner": ("contorneado",)}

# Niveles de las jaulas especiales: (claves para líquido, claves para gas)
NIVELES: dict[str, tuple[tuple, tuple]] = {
    "jaula_multiorificio": ((), ("multiorificio_1", "multiorificio_2", "multiorificio_3")),
    "jaula_multietapa_gas": ((), ("multietapa_2", "multietapa_3", "multietapa_4")),
    "jaula_anticav": (("jaula_1", "etapas_2", "etapas_3", "etapas_4", "etapas_6"), ()),
    "jaula_discos": (("discos_4", "discos_6", "discos_8", "discos_10"), ("discos_4", "discos_6", "discos_8",
                                                                          "discos_10")),
    "jaula_pasajes": (("pasajes_2", "pasajes_3", "pasajes_4"), ()),
}


def deslizante(cuerpo: str) -> bool:
    return cuerpo in POR_CUERPO


def elementos(cuerpo: str, tipo: str, liquido: bool) -> list[str]:
    """Obturadores o jaulas del cuerpo para el tipo de trim, solo los que corresponden al fluido."""
    letra = "L" if liquido else "G"
    return [k for k in POR_CUERPO.get(cuerpo, ()) if ELEMENTOS[k].tipo == tipo and letra in ELEMENTOS[k].fluidos]


def tipos(cuerpo: str) -> list[str]:
    return [t for t in TIPOS if any(ELEMENTOS[k].tipo == t for k in POR_CUERPO.get(cuerpo, ()))]


def guias(cuerpo: str) -> list[str]:
    obt = {k for k in POR_CUERPO.get(cuerpo, ()) if ELEMENTOS[k].tipo == "obturador"}
    return [g for g, d in GUIAS.items() if obt & set(d.obturadores)]


def obturadores(cuerpo: str, guia: str) -> list[str]:
    """Obturadores del cuerpo que admite la guía, en el orden de la guía."""
    return [k for k in GUIAS[guia].obturadores if k in POR_CUERPO.get(cuerpo, ())]


def guia_por_defecto(elemento: str) -> str:
    return next(g for g, d in GUIAS.items() if elemento in d.obturadores)


def niveles(elemento: str, liquido: bool) -> list[str]:
    liq, gas = NIVELES.get(elemento, ((), ()))
    return list(liq if liquido else gas)


def texto_nivel(clave: str, liquido: bool) -> str:
    return AC.texto_nivel(AC.TRIMS[clave]) if liquido else CG.texto_nivel(clave)


def sentidos(cuerpo: str, elemento: str) -> list[str]:
    if cuerpo == "globo_liner":
        return ["abre"]
    if elemento == "venturi":
        return ["cierra"]
    return ["abre", "cierra"]


def clave_estilo(cuerpo: str, elemento: str, sentido: str, nivel: str = "") -> str:
    """Clave de ESTILOS de la combinación elegida."""
    if cuerpo == "globo_liner":
        return "globo_liner_contorneado"
    p = "globo" if cuerpo == "globo" else "angular"
    sd = sentido if sentido in ("abre", "cierra") else "abre"
    if elemento == "venturi":
        return "angular_venturi"
    if elemento == "jaula_4v":
        if p == "globo":
            return "globo_jaula_4v_fuera" if sd == "abre" else "globo_jaula_4v_dentro"
        return f"angular_jaula_{sd}"
    if elemento == "jaula_anticav" and nivel.startswith("etapas_"):
        if p == "globo":
            return "globo_multietapa" if sd == "abre" else "globo_multietapa_cierra"
        return f"angular_multietapa_{sd}"
    return f"{p}_{elemento}_{sd}"


def especial(elemento: str, nivel: str, liquido: bool) -> tuple[str, str]:
    """(clave de anticavitacion.TRIMS, clave de compresible.TRIMS_RUIDO) del nivel elegido."""
    if nivel and nivel in niveles(elemento, liquido):
        return (nivel, "estandar") if liquido else ("estandar", nivel)
    return "estandar", "estandar"


@dataclass
class Eleccion:
    tipo: str
    guia: str
    elemento: str
    sentido: str
    nivel: str = ""


def desde_claves(cuerpo: str, trim: str, guia: str = "", anticav: str = "estandar", ruido: str = "estandar",
                 liquido: bool = True) -> Eleccion | None:
    """Elección de los desplegables a partir de las claves guardadas (también las de versiones anteriores).

    Jaulas de 60 y 120 orificios y multietapa de v0.12: con líquido pasan a la jaula anticavitación (1 etapa
    o 3 etapas, la capacidad de la tabla de multietapas); con gas, a la jaula multiorificio nivel 1 o al
    multietapa de 3 etapas. Un trim especial elegido aparte en una versión anterior pasa a su jaula."""
    if not deslizante(cuerpo):
        return None
    if trim in ("globo_doble_guia_abre", "globo_doble_guia_cierra", "globo_doble_guia_superior"):
        guia = "doble_superior"
    sd = geometria_sentido(trim)[1] or ("cierra" if trim == "angular_venturi" else "abre")
    if anticav != "estandar" and liquido:
        for e in ("jaula_anticav", "jaula_discos", "jaula_pasajes"):
            if anticav in niveles(e, True) and e in POR_CUERPO[cuerpo]:
                return Eleccion("jaula", "", e, sd, anticav)
    if ruido != "estandar" and not liquido:
        for e in ("jaula_multiorificio", "jaula_multietapa_gas", "jaula_discos"):
            if ruido in niveles(e, False) and e in POR_CUERPO[cuerpo]:
                return Eleccion("jaula", "", e, sd, ruido)
    nombre = trim.split("_", 1)[1] if "_" in trim else trim
    for sfx in ("_abre", "_cierra", "_fuera", "_dentro"):
        if nombre.endswith(sfx):
            nombre = nombre[: -len(sfx)]
    mapa = {"contorneado": "contorneado", "doble_guia": "contorneado", "doble_guia_superior": "contorneado",
            "liner_contorneado": "contorneado", "venturi": "venturi", "jaula": "jaula_4v", "jaula_4v": "jaula_4v",
            "jaula_60_orificios": "orificios", "jaula_120_orificios": "orificios", "multietapa": "multietapa",
            "contorneado_lineal": "contorneado", "contorneado_iso": "contorneado"}
    e = mapa.get(nombre, nombre)
    if e == "orificios":
        e, nivel = ("jaula_anticav", "jaula_1") if liquido else ("jaula_multiorificio", "multiorificio_1")
        return Eleccion("jaula", "", e, sd, nivel)
    if e == "multietapa":
        e, nivel = ("jaula_anticav", "etapas_3") if liquido else ("jaula_multietapa_gas", "multietapa_3")
        return Eleccion("jaula", "", e, sd, nivel)
    if e not in ELEMENTOS or e not in POR_CUERPO[cuerpo]:
        return None
    el = ELEMENTOS[e]
    letra = "L" if liquido else "G"
    if letra not in el.fluidos:          # jaula especial de otro fluido: la equivalente de este
        e = {"jaula_multiorificio": "jaula_anticav", "jaula_multietapa_gas": "jaula_anticav",
             "jaula_anticav": "jaula_multiorificio", "jaula_pasajes": "jaula_multietapa_gas"}[e]
        el = ELEMENTOS[e]
    nv = niveles(e, liquido)
    nivel = nv[0] if nv else ""
    if el.tipo == "obturador":
        guia = guia if guia in GUIAS and e in GUIAS[guia].obturadores else guia_por_defecto(e)
        return Eleccion("obturador", guia, e, sd)
    return Eleccion("jaula", "", e, sd, nivel)


def nombre_eleccion(cuerpo: str, el: Eleccion, liquido: bool) -> str:
    """Texto del trim para los documentos: tipo, guía u obturador, jaula y nivel."""
    e = ELEMENTOS[el.elemento]
    if el.tipo == "obturador":
        return f"{TIPOS['obturador']}: {e.nombre.lower()}, guía {GUIAS[el.guia].nombre.split(' (')[0].lower()}"
    txt = f"{TIPOS['jaula']}: {e.nombre.lower()}"
    if el.nivel:
        txt += ", " + (AC.TRIMS[el.nivel].nombre.split(", ")[-1] if liquido else
                       CG.TRIMS_RUIDO[el.nivel].nombre.split(", ")[-1])
    return txt


def claves_en_uso() -> set[str]:
    """Claves de ESTILOS que la solapa 2 puede elegir."""
    out = set()
    for c in CUERPOS:
        if not deslizante(c):
            out |= set(CUERPOS[c].trims)
            continue
        for e in POR_CUERPO[c]:
            for sd in sentidos(c, e):
                for nv in [""] + niveles(e, True) + niveles(e, False):
                    out.add(clave_estilo(c, e, sd, nv))
    return {k for k in out if k in ESTILOS}
