"""Estructuras de datos comunes: pasos de la memoria de cálculo y alertas."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


def _n(v: float, dec: int | None = None) -> str:
    """Número con coma decimal y punto de miles (formato español)."""
    t = f"{v:,.{dec}f}" if dec is not None else f"{v:,.6g}"
    return t.replace(",", "X").replace(".", ",").replace("X", ".")


class Severidad(IntEnum):
    INFO = 0          # dato informativo, no requiere acción
    ADVERTENCIA = 1   # condición a revisar
    CRITICA = 2       # condición que daña la válvula o invalida la selección
    ERROR = 3         # dato de entrada inválido: no se puede calcular


class ErrorDatos(ValueError):
    """Dato de entrada inválido. Contiene la lista de alertas de tipo ERROR."""

    def __init__(self, alertas: list["Alerta"]):
        self.alertas = alertas
        super().__init__("; ".join(a.mensaje for a in alertas))


@dataclass
class Alerta:
    codigo: str                 # identificador estable, también clave de la ayuda
    severidad: Severidad
    titulo: str
    mensaje: str
    intensidad: float | None = None   # 0 a 100 %, cuando el fenómeno admite gradación
    nivel: str | None = None          # texto: «leve», «moderada», «severa»...
    remedios: list[str] = field(default_factory=list)
    referencia: str = ""              # cláusula de la norma


@dataclass
class Paso:
    """Un paso de la memoria de cálculo: hace visible cada valor intermedio."""
    simbolo: str
    descripcion: str
    valor: float
    unidad: str = "-"
    formula: str = ""
    referencia: str = ""


@dataclass
class Memoria:
    pasos: list[Paso] = field(default_factory=list)

    def agregar(self, simbolo, descripcion, valor, unidad="-", formula="", referencia=""):
        self.pasos.append(Paso(simbolo, descripcion, valor, unidad, formula, referencia))
        return valor

    def valor(self, simbolo: str) -> float:
        for p in reversed(self.pasos):
            if p.simbolo == simbolo:
                return p.valor
        raise KeyError(simbolo)


# ---------------------------------------------------------------------------
# Unidades de presentación de los mensajes. La interfaz las fija antes de
# calcular para que alertas, recomendaciones y entregables usen las mismas
# unidades que los datos de entrada.
# ---------------------------------------------------------------------------
PRESENTACION = {"presion": "kPa a", "presion_dif": "kPa", "velocidad": "m/s", "temperatura": "°C",
                "densidad": "kg/m³", "longitud": "mm"}


def _con(v: float, magnitud: str, dec: int) -> str:
    from . import unidades
    u = PRESENTACION[magnitud]
    return f"{_n(unidades.desde_base(v, magnitud, u), dec)} {u}"


def fP(kPa_abs: float, dec: int = 2) -> str:
    """Presión (absoluta en base) en la unidad de presentación."""
    return _con(kPa_abs, "presion", dec)


def fdP(kPa: float, dec: int = 2) -> str:
    return _con(kPa, "presion_dif", dec)


def fV(m_s: float, dec: int = 2) -> str:
    return _con(m_s, "velocidad", dec)


def fT(K: float, dec: int = 0) -> str:
    return _con(K, "temperatura", dec)


def fRho(kg_m3: float, dec: int = 1) -> str:
    return _con(kg_m3, "densidad", dec)
