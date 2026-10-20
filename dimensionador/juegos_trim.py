"""Juegos de internos (trim) estándar: combinaciones de asiento, jaula y obturador compatibles.

En la industria los internos no se especifican pieza por pieza sino como un juego probado: los
materiales del asiento, la jaula y el obturador se eligen juntos para que la pareja deslizante no
sufra galling, que las durezas acompañen la severidad del servicio y que las dilataciones sean
compatibles. Cada juego lleva un código propio del programa (N25-Txx) y un nombre funcional.

El motor de materiales (``seleccion_materiales``) evalúa cada juego con las mismas reglas que a
los materiales sueltos (temperatura, química, servicio agrio, dureza y galling), informa el juego
que coincide con la selección o el juego apto más económico y permite elegir un juego completo.

Combinaciones típicas de la práctica de la industria; la aptitud final la confirma el fabricante
de la válvula con el certificado de cada pieza.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JuegoTrim:
    clave: str
    nombre: str
    asiento: str             # clave de materiales.MATERIALES
    jaula: str
    obturador: str
    blando: bool = False     # asiento con inserto blando (PTFE)
    aplicacion: str = ""
    notas: tuple = ()

    def piezas(self) -> dict[str, str]:
        return {"asiento": self.asiento, "jaula": self.jaula, "obturador": self.obturador}

    @property
    def texto(self) -> str:
        return f"{self.clave} — {self.nombre}"


def _j(*a, **k) -> JuegoTrim:
    return JuegoTrim(*a, **k)


JUEGOS: dict[str, JuegoTrim] = {j.clave: j for j in [
    _j("N25-T01", "Martensítico endurecido", "416", "CB7Cu1", "416",
       aplicacion="Agua, vapor, aire y gas limpios sin cloruros ni H₂S; servicio general económico.",
       notas=("El azufre del 416 reduce su resistencia a las picaduras.",)),
    _j("N25-T02", "Inoxidable 316 con jaula ENC", "316", "316_ENC", "316",
       aplicacion="Servicios corrosivos limpios con ΔP baja y cierre metálico clase IV.",
       notas=("Superficies blandas (≈ 150 HB): no apto para cavitación, flashing ni sólidos.",)),
    _j("N25-T03", "Inoxidable 316 con jaula ENC y asiento blando", "316", "316_ENC", "316", True,
       aplicacion="Como el T02 con cierre clase VI (inserto de PTFE en el asiento, hasta unos 232 °C)."),
    _j("N25-T04", "316 con Stellite en asiento y guía, jaula ENC", "ST6", "316_ENC", "316_ST6",
       aplicacion="ΔP moderada a alta y cierre clase V en servicios corrosivos.",
       notas=("Puede pedirse con recargue solo en el asiento del obturador o en asiento y guía.",)),
    _j("N25-T05", "316 con Stellite, jaula ENC y asiento blando", "316_ST6", "316_ENC", "316_ST6", True,
       aplicacion="Como el T04 con cierre clase VI (inserto de PTFE)."),
    _j("N25-T06", "Stellite macizo en asiento y jaula", "ST6", "ST6", "316_ST6",
       aplicacion="Cavitación, flashing y erosión severos; alta temperatura.",
       notas=("Para servicio continuo por encima de unos 300 °C se pide la versión de alta temperatura, con "
              "holguras de guiado mayores.",)),
    _j("N25-T07", "Stellite macizo con asiento blando", "316_ST6", "ST6", "316_ST6", True,
       aplicacion="Como el T06 con cierre clase VI a temperatura moderada."),
    _j("N25-T08", "316L con jaula ENC", "316L", "316_ENC", "316L",
       aplicacion="Medios que atacan el borde de grano o piezas soldadas: ácidos oxidantes diluidos, química fina."),
    _j("N25-T09", "321 estabilizado con jaula 347 ENC", "321", "CF8C_ENC", "321",
       aplicacion="Alta temperatura prolongada con riesgo de sensibilización (refinería, petroquímica).",
       notas=("El ENC de la jaula limita la temperatura a unos 400 °C.",)),
    _j("N25-T10", "Stellite en asiento con jaula 17-4PH", "ST6", "CB7Cu1", "316_ST6",
       aplicacion="ΔP alta, cavitación moderada y cierre clase V en agua, vapor e hidrocarburos.",
       notas=("Para más de unos 300 °C pedir la versión de alta temperatura (holguras de guiado mayores).",)),
    _j("N25-T11", "316 con Stellite y jaula 17-4PH", "316_ST6", "CB7Cu1", "316_ST6",
       aplicacion="Como el T10 con asiento de 316 recargado (más económico en tamaños grandes)."),
    _j("N25-T12", "Inoxidable 316 con jaula 17-4PH", "316", "CB7Cu1", "316",
       aplicacion="Servicio general limpio con ΔP baja; la jaula endurecida evita el galling."),
    _j("N25-T13", "440C con jaula 17-4PH", "440C", "CB7Cu1", "440C",
       aplicacion="Cavitación severa y flashing en agua y condensado sin cloruros.",
       notas=("440C frágil frente a impactos y con corrosión limitada.",)),
    _j("N25-T14", "316 con asiento blando y jaula 17-4PH", "316", "CB7Cu1", "316", True,
       aplicacion="Cierre clase VI en servicio general limpio."),
    _j("N25-T15", "Asiento blando con obturador 416 y jaula 17-4PH", "316", "CB7Cu1", "416", True,
       aplicacion="Cierre clase VI en agua, aire y gas limpios con un obturador más duro."),
    _j("N25-T16", "NACE de alta resistencia", "ST6", "CB7Cu1_CR", "174_H1150D_ST6",
       aplicacion="Servicio agrio con ΔP alta: base 17-4PH doble envejecida ≤ 33 HRC y superficies recargadas.",
       notas=("Límites ambientales del 17-4PH: pH₂S ≤ 3,4 kPa y pH ≥ 4,5 (ISO 15156-3).",)),
    _j("N25-T17", "Martensítico NACE (CA6NM)", "410_NACE", "CB7Cu1", "410_NACE",
       aplicacion="Agua y gas con H₂S leve y ΔP baja: martensítico revenido ≤ 23 HRC.",
       notas=("La dureza baja no admite cavitación.",)),
]}


def coincide(j: JuegoTrim, elegidos: dict[str, str | None], jaula: bool, blando: bool) -> bool:
    """El juego tiene exactamente los materiales elegidos (la jaula solo cuenta si el trim la lleva)."""
    piezas = j.piezas()
    claves = ["asiento", "obturador"] + (["jaula"] if jaula else [])
    return j.blando == blando and all(elegidos.get(c) == piezas[c] for c in claves)
