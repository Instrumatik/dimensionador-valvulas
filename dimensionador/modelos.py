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
