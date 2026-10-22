"""Tamaño del trim (diámetro del puerto) y carrera del vástago.

Válvulas de vástago ascendente (globo y ángulo):

* El diámetro del puerto del trim completo se toma de ``PUERTO_NPS``, el puerto pleno típico de los
  cuerpos de globo y ángulo de jaula según el diámetro nominal (en tamaños chicos el puerto es igual o
  mayor que la conexión), interpolado entre tamaños y redondeado al 1/16 in. Si el Cv nominal ingresado es menor que
  el típico del estilo (trim reducido), el puerto se reduce con la raíz de la relación de Cv,
  porque la capacidad crece con el área del puerto.
* La carrera nominal (rated travel) es la habitual de un trim pleno del tamaño equivalente al
  puerto (``CARRERA_NPS``): el área lateral que descubre el obturador (π·d·h) supera holgadamente
  el área del puerto (π·d²/4). Los trims de orificios y multietapa reparten el paso a lo largo de
  la jaula y llevan la carrera normalizada siguiente.
* La carrera de operación de cada caso es la apertura relativa × carrera nominal.

Válvulas rotativas (bola, mariposa, tapón excéntrico): el «trim» es el orificio de la bola, el
disco o el asiento del tapón; la carrera es la rotación del eje en grados.

Son estimaciones para la preingeniería. El fabricante certifica el puerto y la carrera de la
válvula ofertada; cargados en la solapa 2 reemplazan a los estimados.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MM_IN = 25.4
# Serie de carreras normalizadas habituales de válvulas de globo [in]
CARRERAS_IN = (0.5, 0.75, 1.125, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0)
# Puerto pleno típico de globo y ángulo según el diámetro nominal: (NPS, puerto [in]). Entre tamaños se
# interpola; por debajo de 1" se escala con la relación de 1" y por encima de 8" con la de 8".
PUERTO_NPS = ((1.0, 1.3125), (1.5, 1.875), (2.0, 2.3125), (3.0, 3.4375), (4.0, 4.375), (6.0, 7.0), (8.0, 8.0))


def puerto_tipico_in(nps: float) -> float:
    """Puerto pleno típico [in] de un globo o ángulo de diámetro nominal ``nps`` (sin redondear)."""
    (n0, p0), (n1, p1) = PUERTO_NPS[0], PUERTO_NPS[-1]
    if nps <= n0:
        return p0 * nps / n0
    if nps >= n1:
        return p1 * nps / n1
    for (a, pa), (b, pb) in zip(PUERTO_NPS, PUERTO_NPS[1:]):
        if a <= nps <= b:
            return pa + (pb - pa) * (nps - a) / (b - a)


def nps_de_puerto(puerto_in: float) -> float:
    """Diámetro nominal cuyo puerto pleno típico es ``puerto_in`` (inversa de puerto_tipico_in)."""
    (n0, p0), (n1, p1) = PUERTO_NPS[0], PUERTO_NPS[-1]
    if puerto_in <= p0:
        return puerto_in * n0 / p0
    if puerto_in >= p1:
        return puerto_in * n1 / p1
    for (a, pa), (b, pb) in zip(PUERTO_NPS, PUERTO_NPS[1:]):
        if pa <= puerto_in <= pb:
            return a + (b - a) * (puerto_in - pa) / (pb - pa)
# Carrera nominal habitual de un trim pleno de globo según el diámetro nominal: (NPS, carrera [in])
CARRERA_NPS = ((0.5, 0.75), (1.5, 0.75), (2, 1.125), (3, 1.5), (4, 2.0), (6, 2.0), (8, 3.0), (10, 3.0),
               (12, 4.0), (16, 4.0), (20, 6.0), (24, 8.0))


@dataclass
class Geometria:
    rotativa: bool
    puerto_mm: float
    puerto_certificado: bool
    carrera_mm: float | None          # lineal: carrera nominal; rotativa: None
    carrera_certificada: bool
    rotacion_grados: float | None     # rotativa: rotación nominal del eje
    reducido: bool = False
    nota: str = ""

    @property
    def puerto_in(self) -> float:
        return self.puerto_mm / MM_IN

    @property
    def carrera_in(self) -> float | None:
        return None if self.carrera_mm is None else self.carrera_mm / MM_IN

    @property
    def nombre_puerto(self) -> str:
        return "Diámetro del orificio / disco" if self.rotativa else "Tamaño del trim (diámetro del puerto)"

    @property
    def texto_puerto(self) -> str:
        return f"{fraccion_in(self.puerto_in)} ({_mm(self.puerto_mm)})" + (" certificado" if self.puerto_certificado
                                                                          else " estimado")

    @property
    def texto_carrera(self) -> str:
        if self.rotativa:
            return f"Rotación nominal {self.rotacion_grados:.0f}°"
        return (f"{fraccion_in(self.carrera_in)} ({_mm(self.carrera_mm)})"
                + (" certificada" if self.carrera_certificada else " estimada"))

    def operacion(self, apertura: float) -> str:
        """Carrera (o rotación) de operación para una apertura relativa 0–1."""
        h = max(0.0, min(apertura, 1.0))
        if self.rotativa:
            return f"{h * self.rotacion_grados:.0f}° de {self.rotacion_grados:.0f}°"
        mm = h * self.carrera_mm
        return f"{_mm(mm)} ({mm / MM_IN:.2f} in)".replace(".", ",")


def _mm(v: float) -> str:
    return f"{v:.1f} mm".replace(".", ",")


def fraccion_in(v: float) -> str:
    """Pulgadas redondeadas al 1/16 más cercano, como fracción: 5,375 → «5 3/8 in»."""
    n = round(v * 16)
    ent, r = divmod(n, 16)
    if r == 0:
        return f"{ent} in" if ent else "0 in"
    g = math.gcd(r, 16)
    frac = f"{r // g}/{16 // g}"
    return f"{ent} {frac} in" if ent else f"{frac} in"


def carrera_normalizada(minima_in: float) -> float:
    for c in CARRERAS_IN:
        if c >= minima_in - 1e-9:
            return c
    return CARRERAS_IN[-1]


def carrera_tipica(puerto_in: float, tipo: str) -> float:
    """Carrera nominal [in] del trim pleno equivalente al puerto; una medida más para trims de orificios."""
    nps = nps_de_puerto(puerto_in)
    c = CARRERA_NPS[0][1]
    for n, h in CARRERA_NPS:
        if nps >= n - 0.05:
            c = h
    if tipo == "orificios":
        c = carrera_normalizada(c + 0.01)
    return c


def _tipo_lineal(trim: str) -> str:
    if "orificios" in trim or "multietapa" in trim:
        return "orificios"
    if "venturi" in trim:
        return "venturi"
    return "jaula" if "jaula" in trim else "contorneado"


def rotacion(trim: str) -> float:
    for g in (60, 70):
        if trim.endswith(f"_{g}"):
            return float(g)
    return 90.0


def _puerto_rotativa(trim: str, d_pulg: float, DI_mm: float | None) -> float:
    """Orificio de la bola, disco de mariposa o asiento del tapón excéntrico [mm]."""
    base = DI_mm or d_pulg * MM_IN * 0.95
    if "reducido" in trim:
        return base * 0.75           # una a dos medidas menor que la conexión
    if "excentrico" in trim:
        return d_pulg * MM_IN * 0.80
    return base


def estimar(trim: str, rotativa: bool, d_pulg: float, Cv_nominal: float, Cv_tipico: float,
            DI_mm: float | None = None, puerto_mm: float | None = None,
            carrera_mm: float | None = None) -> Geometria:
    """Puerto y carrera de la válvula; los valores certificados (no None) reemplazan a los estimados."""
    if rotativa:
        p = puerto_mm or _puerto_rotativa(trim, d_pulg, DI_mm)
        return Geometria(True, p, puerto_mm is not None, None, False, rotacion(trim),
                         nota="La carrera de una válvula rotativa es la rotación del eje.")
    reducido = False
    if puerto_mm:
        p = puerto_mm
    else:
        p = puerto_tipico_in(d_pulg) * MM_IN
        if Cv_tipico and Cv_nominal < 0.95 * Cv_tipico:
            p *= math.sqrt(Cv_nominal / Cv_tipico)
            reducido = True
        p = round(p / MM_IN * 16) / 16 * MM_IN      # al 1/16 in
    if carrera_mm:
        h = carrera_mm
    else:
        h = carrera_tipica(p / MM_IN, _tipo_lineal(trim)) * MM_IN
    nota = "Trim reducido: puerto estimado con la relación de Cv." if reducido else ""
    return Geometria(False, p, puerto_mm is not None, h, carrera_mm is not None, None, reducido, nota)
