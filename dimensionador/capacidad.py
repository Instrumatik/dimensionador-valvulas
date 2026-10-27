"""Capacidad típica (Cv) de los trims de vástago ascendente, ligada al puerto y a la carrera.

Origen de los datos (v0.12.0)
-----------------------------
Tablas de «Cv y FL según la carrera» publicadas por tres fabricantes de válvulas de globo (dos
boletines técnicos y una planilla de datos certificados), unas 1 200 filas de tamaño, puerto, carrera
y Cv del 10 al 100 % de carrera. NEUTRALIDAD DE MARCA: el programa no guarda las tablas de ningún
fabricante; guarda solo la MEDIANA por familia de trim y tamaño, y la dispersión entre fuentes
(mínimo y máximo) como banda de tolerancia.

Modelo
------
* Trim pleno: tabla por familia y diámetro nominal (NPS): puerto, carrera y Cv con característica
  lineal a carrera nominal. Entre tamaños se interpola en escala logarítmica; fuera de la tabla se
  extrapola con la pendiente del último tramo.
* Característica: el Cv a carrera nominal se multiplica por el factor de la característica
  (``FACTOR_CAR``, mediana de las relaciones isoporcentual/lineal y apertura rápida/lineal medidas
  en el mismo puerto). El sentido del flujo no cambia el Cv nominal en los datos (relación 1,00).
* Puerto y carrera distintos de los del pleno (trim reducido o puerto certificado): el paso por el
  asiento y el paso lateral que descubre el obturador actúan como dos restricciones en serie,

      1/Cv² = 1/(Kp·d²)² + 1/(Kh·π·d·h)²        (d puerto, h carrera, en pulgadas)

  con Kp y Kh ajustados por familia sobre los puertos reducidos de los datos. El resultado nunca
  supera el Cv del pleno del cuerpo.
* Banda: la dispersión entre fabricantes del trim pleno (``PLENO``) y del modelo de reducidos
  (``BANDA_REDUCIDO``). Fuera de ±10 % del típico, el programa avisa (alerta de coherencia).

Son valores para la preingeniería; el Cv certificado del trim ofertado reemplaza a estos.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Familias de capacidad de los trims de vástago ascendente
FAMILIAS = {
    "contorneado": "Obturador contorneado (guiado superior o doble guía)",
    "jaula": "Jaula caracterizada de ventanas",
    "orificios": "Jaula de orificios de una etapa (bajo ruido / anticavitación)",
    "multietapa": "Multietapa (anticavitación o bajo ruido)",
}

# Trim pleno, característica lineal: (NPS, puerto [in], carrera [in], Cv mediana, Cv mín., Cv máx., fuentes)
PLENO: dict[str, tuple] = {
    "contorneado": (
        (0.5, 0.5, 0.8, 6.0, 6.0, 6.0, 1), (0.75, 0.8125, 0.8, 12.0, 12.0, 12.0, 1),
        (1.0, 0.8125, 0.8, 12.0, 12.0, 12.0, 1), (1.5, 1.625, 0.8, 35.0, 35.0, 35.0, 1),
        (2.0, 1.625, 0.8, 46.0, 46.0, 46.0, 1), (3.0, 2.625, 1.5, 110.0, 110.0, 110.0, 1),
        (4.0, 3.5, 1.5, 195.0, 195.0, 195.0, 1), (6.0, 5.0, 2.0, 400.0, 400.0, 400.0, 1),
        (8.0, 6.25, 2.5, 640.0, 640.0, 640.0, 1),
    ),
    "jaula": (
        (1.0, 0.8125, 0.8, 12.0, 12.0, 12.0, 0), (1.5, 1.625, 0.8, 35.0, 35.0, 35.0, 0),
        (2.0, 2.3125, 1.125, 40.0, 30.0, 40.0, 1), (3.0, 3.4375, 1.5, 142.0, 135.0, 148.0, 2),
        (4.0, 4.375, 2.0, 218.0, 200.0, 236.0, 2), (6.0, 6.0, 2.0, 394.0, 370.0, 417.0, 2),
        (8.0, 7.25, 2.5, 585.0, 550.0, 620.0, 2), (10.0, 8.0, 3.0, 860.0, 860.0, 860.0, 1),
        (14.0, 11.5, 5.0, 1910.0, 1910.0, 1910.0, 1), (16.0, 13.0, 5.0, 2530.0, 2530.0, 2530.0, 1),
        (18.0, 14.5, 7.0, 3130.0, 3130.0, 3130.0, 1), (20.0, 19.0, 9.0, 4550.0, 4550.0, 4550.0, 1),
        (24.0, 23.0, 11.0, 7080.0, 7080.0, 7080.0, 1), (30.0, 29.0, 15.0, 9550.0, 9550.0, 9550.0, 1),
    ),
    "orificios": (
        (0.75, 0.8125, 0.8, 8.0, 8.0, 8.0, 1), (1.0, 0.8125, 0.8, 8.0, 8.0, 8.0, 1),
        (1.5, 1.25, 0.8, 15.0, 15.0, 15.0, 1), (2.0, 2.0, 1.125, 42.0, 25.0, 58.0, 2),
        (3.0, 3.4375, 1.5, 95.0, 75.0, 99.0, 3), (4.0, 4.375, 2.0, 168.0, 100.0, 169.0, 3),
        (6.0, 5.125, 2.0, 230.0, 200.0, 338.0, 3), (8.0, 6.5, 3.0, 410.0, 290.0, 426.0, 3),
        (12.0, 9.75, 5.0, 915.0, 915.0, 915.0, 1), (14.0, 11.5, 5.5, 1450.0, 1450.0, 1450.0, 1),
        (16.0, 13.0, 6.0, 1800.0, 1800.0, 1800.0, 1), (18.0, 14.5, 7.0, 2430.0, 2430.0, 2430.0, 1),
        (20.0, 19.0, 9.0, 3500.0, 3500.0, 3500.0, 1), (24.0, 23.0, 15.0, 6600.0, 6600.0, 6600.0, 1),
        (30.0, 29.0, 15.0, 8000.0, 8000.0, 8000.0, 1), (36.0, 35.0, 20.0, 13500.0, 13500.0, 13500.0, 1),
    ),
    "multietapa": (
        (2.0, 2.25, 1.5, 26.0, 23.0, 30.0, 2), (3.0, 3.3125, 1.5, 70.0, 65.0, 75.0, 2),
        (4.0, 4.1875, 2.0, 105.0, 105.0, 105.0, 2), (6.0, 4.75, 2.5, 150.0, 71.0, 160.0, 3),
        (8.0, 6.125, 2.5, 250.0, 178.0, 260.0, 3), (10.0, 7.75, 3.0, 365.0, 350.0, 380.0, 2),
        (12.0, 9.5, 4.0, 620.0, 600.0, 640.0, 2), (14.0, 11.5, 5.0, 863.0, 863.0, 863.0, 1),
        (16.0, 12.75, 6.0, 1210.0, 1105.0, 1310.0, 2), (18.0, 14.5, 7.0, 1530.0, 1460.0, 1600.0, 2),
        (20.0, 19.0, 9.0, 3700.0, 2900.0, 4500.0, 2), (24.0, 23.0, 15.0, 4525.0, 4200.0, 4850.0, 2),
        (36.0, 34.5, 20.0, 11500.0, 11500.0, 11500.0, 1),
    ),
}

# Cv a carrera nominal relativo al lineal, mismo puerto (mediana de los datos; «apertura rápida» solo
# medida en jaula y extendida a las demás familias; parabólica modificada: promedio de lineal e
# isoporcentual, sin datos propios)
FACTOR_CAR: dict[str, dict[str, float]] = {
    "contorneado": {"lineal": 1.00, "isoporcentual": 1.00, "parabolica": 1.00, "apertura_rapida": 1.09},
    "jaula": {"lineal": 1.00, "isoporcentual": 0.89, "parabolica": 0.95, "apertura_rapida": 1.09},
    "orificios": {"lineal": 1.00, "isoporcentual": 0.75, "parabolica": 0.88, "apertura_rapida": 1.09},
    "multietapa": {"lineal": 1.00, "isoporcentual": 0.75, "parabolica": 0.88, "apertura_rapida": 1.00},
}

# Restricciones en serie del puerto (Kp) y del paso lateral (Kh) de los puertos reducidos, y su dispersión
# (Kp, Kh); su dispersión entre fabricantes va en BANDA_REDUCIDO
SERIE: dict[str, tuple[float, float]] = {
    "contorneado": (21.0, 19.1),
    "jaula": (12.5, 1.0e6),        # en los datos de jaula la carrera no limita: solo el área del puerto
    "orificios": (10.0, 14.9),
    "multietapa": (13.0, 5.7),
}
BANDA_REDUCIDO: dict[str, tuple[float, float]] = {   # Cv real / Cv del modelo, entre fabricantes (p10–p90)
# Contorneado: en cuerpos de 2" y menores el modelo queda 15–30 % bajo (lado seguro: apertura algo mayor).
    "contorneado": (0.85, 1.35), "jaula": (0.50, 1.55), "orificios": (0.75, 1.30), "multietapa": (0.80, 1.20),
}

# Rangeabilidad de los trims de bajo ruido y anticavitación: Cv mínimo controlable publicado (mediana)
RANGEABILIDAD = {"orificios": 15.0, "multietapa": 33.0}

# Factor de capacidad de un multietapa según el número de etapas (la tabla corresponde a ~3 etapas)
FACTOR_ETAPAS = {1: 1.0, 2: 1.25, 3: 1.0, 4: 0.875, 6: 0.70}


def factor_etapas(n: int) -> float:
    """Factor de capacidad de N etapas; fuera de la tabla sigue √(3/N), que la tabla cumple con ±3 %."""
    return FACTOR_ETAPAS.get(n, round(math.sqrt(3 / n), 3))

TOLERANCIA = 0.10     # ±10 %: fuera de esto el dato del usuario se informa como no coherente


def _interp(fam: str, nps: float, col: int) -> float:
    t = PLENO[fam]
    xs = [r[0] for r in t]
    if nps <= xs[0]:
        a, b = t[0], t[1]
    elif nps >= xs[-1]:
        a, b = t[-2], t[-1]
    else:
        i = next(i for i in range(len(xs) - 1) if xs[i] <= nps <= xs[i + 1])
        a, b = t[i], t[i + 1]
    if a[col] <= 0 or b[col] <= 0:
        return a[col]
    m = math.log(b[col] / a[col]) / math.log(b[0] / a[0])
    return a[col] * (nps / a[0]) ** m


@dataclass(frozen=True)
class TrimTipico:
    familia: str
    nps: float
    puerto_in: float
    carrera_in: float
    Cv: float                # característica pedida, a carrera nominal
    Cv_min: float            # banda entre fabricantes
    Cv_max: float
    fuentes: int             # cantidad de fabricantes con dato en ese tamaño (0 = extrapolado)
    reducido: bool = False

    @property
    def texto_banda(self) -> str:
        from .modelos import _n
        if self.fuentes <= 1 or abs(self.Cv_max - self.Cv_min) < 1e-9:
            return "un solo dato publicado" if self.fuentes == 1 else "extrapolado"
        return f"{_n(self.Cv_min, 0)} a {_n(self.Cv_max, 0)} entre fabricantes"


def _fila(fam: str, nps: float):
    return next((r for r in PLENO[fam] if abs(r[0] - nps) < 1e-6), None)


def _redondeo_puerto(p: float) -> float:
    return round(p * 16) / 16


def pleno(fam: str, nps: float, caracteristica: str = "lineal") -> TrimTipico:
    """Trim pleno típico de la familia en el cuerpo de ``nps``."""
    f = FACTOR_CAR[fam].get(caracteristica, 1.0)
    r = _fila(fam, nps)
    if r:
        return TrimTipico(fam, nps, r[1], r[2], r[3] * f, r[4] * f, r[5] * f, r[6])
    cv = _interp(fam, nps, 3)
    return TrimTipico(fam, nps, _redondeo_puerto(_interp(fam, nps, 1)), _interp(fam, nps, 2), cv * f,
                      _interp(fam, nps, 4) * f, _interp(fam, nps, 5) * f, 0)


def cv_serie(fam: str, puerto_in: float, carrera_in: float) -> float:
    """Cv (lineal) de las restricciones en serie del puerto y del paso lateral."""
    Kp, Kh = SERIE[fam]
    return 1 / math.sqrt(1 / (Kp * puerto_in ** 2) ** 2 + 1 / (Kh * math.pi * puerto_in * carrera_in) ** 2)


def cv_geometria(fam: str, nps: float, puerto_in: float, carrera_in: float | None = None,
                 caracteristica: str = "lineal") -> float:
    """Cv típico para un puerto (y carrera) dados en el cuerpo de ``nps``.

    Con el puerto del pleno (±3 %) devuelve el Cv del pleno corregido por la carrera; con un puerto
    menor usa el modelo de restricciones en serie, sin superar el pleno del cuerpo."""
    p = pleno(fam, nps, caracteristica)
    f = FACTOR_CAR[fam].get(caracteristica, 1.0)
    h = carrera_in or carrera_para(fam, nps, puerto_in)
    if puerto_in >= 0.97 * p.puerto_in:
        return p.Cv * min(1.0, cv_serie(fam, p.puerto_in, h) / cv_serie(fam, p.puerto_in, p.carrera_in)) \
            if h < p.carrera_in else p.Cv
    return min(cv_serie(fam, puerto_in, h) * f, p.Cv)


def carrera_para(fam: str, nps: float, puerto_in: float) -> float:
    """Carrera típica de un puerto: la del pleno del tamaño cuyo puerto pleno es ``puerto_in``."""
    t = PLENO[fam]
    p = pleno(fam, nps)
    if puerto_in >= 0.97 * p.puerto_in:
        return p.carrera_in
    for r in t:
        if r[1] >= puerto_in - 1e-6:
            return min(r[2], p.carrera_in)
    return p.carrera_in


def reducidos(fam: str, nps: float, caracteristica: str = "lineal", n: int = 3) -> list[TrimTipico]:
    """Juegos reducidos típicos del cuerpo: los puertos plenos de los tamaños menores de la tabla
    (la práctica habitual es montar el trim pleno de una o dos medidas menos), con su Cv en este cuerpo."""
    p = pleno(fam, nps, caracteristica)
    out = []
    for r in reversed(PLENO[fam]):
        if r[1] < 0.95 * p.puerto_in and len(out) < n and r[1] not in {t.puerto_in for t in out}:
            h = min(r[2], p.carrera_in)
            cv = cv_geometria(fam, nps, r[1], h, caracteristica)
            lo, hi = BANDA_REDUCIDO[fam]
            out.append(TrimTipico(fam, nps, r[1], h, cv, cv * lo, cv * hi, r[6], True))
    return out


def juegos(fam: str, nps: float, caracteristica: str = "lineal") -> list[TrimTipico]:
    """Pleno y reducidos típicos del cuerpo de ``nps``, de mayor a menor Cv."""
    return [pleno(fam, nps, caracteristica)] + reducidos(fam, nps, caracteristica)


def puerto_para_cv(fam: str, nps: float, Cv: float, caracteristica: str = "lineal") -> float:
    """Puerto [in] cuyo Cv típico en el cuerpo de ``nps`` es ``Cv`` (inversa de cv_geometria)."""
    p = pleno(fam, nps, caracteristica)
    if Cv >= p.Cv:
        return p.puerto_in
    lo, hi = 0.05, p.puerto_in
    for _ in range(60):
        m = (lo + hi) / 2
        if cv_geometria(fam, nps, m, None, caracteristica) < Cv:
            lo = m
        else:
            hi = m
    return hi


@dataclass
class Coherencia:
    """Comparación de los datos certificados (puerto, carrera, Cv) con los típicos."""
    Cv_tipico: float
    Cv_usuario: float | None
    desvio: float | None          # (usuario − típico)/típico
    banda: tuple[float, float]
    puerto_in: float
    carrera_in: float
    detalle: str

    @property
    def coherente(self) -> bool:
        return self.desvio is None or abs(self.desvio) <= TOLERANCIA

    @property
    def dentro_de_banda(self) -> bool:
        return self.Cv_usuario is None or self.banda[0] * 0.97 <= self.Cv_usuario <= self.banda[1] * 1.03


def coherencia(fam: str, nps: float, caracteristica: str, puerto_in: float | None, carrera_in: float | None,
               Cv_usuario: float | None) -> Coherencia:
    """Compara el Cv certificado (o estimado) con el típico del puerto y la carrera del trim."""
    from .modelos import _n
    p = pleno(fam, nps, caracteristica)
    d = puerto_in or p.puerto_in
    h = carrera_in or carrera_para(fam, nps, d)
    tip = cv_geometria(fam, nps, d, h, caracteristica)
    if d >= 0.97 * p.puerto_in:
        banda = (p.Cv_min * tip / p.Cv, p.Cv_max * tip / p.Cv) if p.fuentes > 1 else (tip * 0.9, tip * 1.1)
    else:
        lo, hi = BANDA_REDUCIDO[fam]
        banda = (tip * lo, tip * hi)
    dv = None if not Cv_usuario else (Cv_usuario - tip) / tip
    det = (f"Puerto {_n(d, 3)} in, carrera {_n(h, 3)} in en cuerpo de {_n(nps)}\": Cv típico {_n(tip, 1)} "
           f"(banda entre fabricantes {_n(banda[0], 0)} a {_n(banda[1], 0)})")
    return Coherencia(tip, Cv_usuario, dv, banda, d, h, det)
