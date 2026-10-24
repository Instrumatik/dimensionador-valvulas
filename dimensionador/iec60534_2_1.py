"""Ecuaciones de dimensionamiento IEC 60534-2-1:2011 / ANSI/ISA-75.01.01-2012.

Todo el cálculo se hace en unidades base SI (kPa abs, K, m³/h, kg/h, kg/m³,
m²/s, mm) y con el coeficiente Kv. El Cv se obtiene al final con
Cv = 1,156·Kv. Cada valor intermedio se registra en la memoria de cálculo
para que el usuario pueda revisar el procedimiento completo.

Cláusulas cubiertas:
  * 5   Fluidos incompresibles, flujo turbulento (crítico y no crítico)
  * 6   Fluidos compresibles, flujo turbulento (crítico y no crítico)
  * 7   Factor de geometría de tubería FP, FLP y xTP (reductores)
  * 8/9 Flujo no turbulento (laminar y de transición), factor FR
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .modelos import _n, Alerta, ErrorDatos, Memoria, Severidad

# ---------------------------------------------------------------------------
# Constantes numéricas (Tabla 1 de la norma) para Kv con kPa, m³/h, kg/h, mm, K
# ---------------------------------------------------------------------------
RHO_AGUA_15C = 999.1           # ρ0, densidad del agua a 15 °C [kg/m³]
R_UNIV = 8.314462618           # kJ/(kmol·K)
P_N = 101.325                  # kPa, condición normal
T_N = 273.15                   # K, condición normal

N1 = 0.1
N2 = 1.60e-3
N4 = 7.07e-2
N5 = 1.80e-3
N6 = math.sqrt(RHO_AGUA_15C / 100.0)   # 3,16 (valor exacto derivado)
N18 = 0.865
N22 = 17.3                     # Q en m³/h normales (0 °C)
N27 = 0.775
N32 = 1.40e2

REF = "IEC 60534-2-1:2011"


# ---------------------------------------------------------------------------
# Datos de entrada
# ---------------------------------------------------------------------------
@dataclass
class Valvula:
    """Factores de la válvula a la carrera considerada.

    FL : factor de recuperación de presión del líquido (sin accesorios)
    xT : factor de relación de caída de presión diferencial crítica (gases)
    Fd : modificador de estilo de válvula (para Reynolds)
    d_mm : diámetro nominal de la válvula
    D1_mm, D2_mm : diámetro interior de la tubería aguas arriba / abajo.
                   Si se omiten se asume válvula del mismo tamaño que la línea.
    """
    FL: float
    xT: float
    Fd: float
    d_mm: float
    D1_mm: float | None = None
    D2_mm: float | None = None

    @property
    def con_reductores(self) -> bool:
        return (self.D1_mm is not None and abs(self.D1_mm - self.d_mm) > 1e-9) or (
            self.D2_mm is not None and abs(self.D2_mm - self.d_mm) > 1e-9
        )


@dataclass
class Liquido:
    P1: float          # kPa abs
    P2: float          # kPa abs
    T1: float          # K
    rho1: float        # kg/m³
    Pv: float          # kPa abs, presión de vapor a T1
    Pc: float          # kPa abs, presión crítica termodinámica
    nu: float          # m²/s, viscosidad cinemática
    Q: float | None = None   # m³/h
    W: float | None = None   # kg/h

    def caudal_volumetrico(self) -> float:
        if self.Q is not None:
            return self.Q
        return self.W / self.rho1


@dataclass
class Gas:
    P1: float          # kPa abs
    P2: float          # kPa abs
    T1: float          # K
    M: float           # kg/kmol
    gamma: float       # relación de calores específicos cp/cv
    Z: float           # factor de compresibilidad a la entrada
    mu: float          # Pa·s, viscosidad dinámica
    W: float | None = None    # kg/h
    QN: float | None = None   # m³/h normales (0 °C; 101,325 kPa)
    rho1: float | None = None  # kg/m³; si se omite se calcula con P1·M/(Z·R·T1)

    def densidad(self) -> float:
        if self.rho1 is not None:
            return self.rho1
        return self.P1 * self.M / (self.Z * R_UNIV * self.T1)

    def caudal_masico(self) -> float:
        if self.W is not None:
            return self.W
        rho_n = P_N * self.M / (R_UNIV * T_N)
        return self.QN * rho_n


@dataclass
class Resultado:
    Kv: float
    Cv: float
    bloqueado: bool             # flujo crítico (choked)
    regimen: str                # «turbulento», «transición», «laminar»
    FP: float
    Rev: float
    FR: float
    memoria: Memoria
    alertas: list[Alerta] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Factores de geometría de tubería (cláusula 7)
# ---------------------------------------------------------------------------
def coeficientes_reductores(d: float, D1: float | None, D2: float | None):
    """Coeficientes de pérdida ζ de reductores concéntricos cortos."""
    D1 = D1 or d
    D2 = D2 or d
    z1 = 0.5 * (1 - (d / D1) ** 2) ** 2
    z2 = 1.0 * (1 - (d / D2) ** 2) ** 2
    zB1 = 1 - (d / D1) ** 4
    zB2 = 1 - (d / D2) ** 4
    return z1, z2, zB1, zB2


def factor_FP(C: float, v: Valvula) -> float:
    if not v.con_reductores:
        return 1.0
    z1, z2, zB1, zB2 = coeficientes_reductores(v.d_mm, v.D1_mm, v.D2_mm)
    suma = z1 + z2 + zB1 - zB2
    return 1.0 / math.sqrt(1 + suma / N2 * (C / v.d_mm ** 2) ** 2)


def factor_FLP(C: float, v: Valvula) -> float:
    if not v.con_reductores:
        return v.FL
    z1, _, zB1, _ = coeficientes_reductores(v.d_mm, v.D1_mm, v.D2_mm)
    return v.FL / math.sqrt(1 + v.FL ** 2 / N2 * (z1 + zB1) * (C / v.d_mm ** 2) ** 2)


def factor_xTP(C: float, v: Valvula, FP: float) -> float:
    if not v.con_reductores:
        return v.xT
    z1, _, zB1, _ = coeficientes_reductores(v.d_mm, v.D1_mm, v.D2_mm)
    return (v.xT / FP ** 2) / (1 + v.xT * (z1 + zB1) / N5 * (C / v.d_mm ** 2) ** 2)


# ---------------------------------------------------------------------------
# Número de Reynolds y factor FR (cláusulas 8 y 9)
# ---------------------------------------------------------------------------
def reynolds_valvula(Q_m3h: float, nu: float, C: float, v: Valvula) -> float:
    D = v.D1_mm or v.d_mm
    return (N4 * v.Fd * Q_m3h / (nu * math.sqrt(C * v.FL))
            * (v.FL ** 2 * C ** 2 / (N2 * D ** 4) + 1) ** 0.25)


def factor_FR(Rev: float, C: float, v: Valvula) -> float:
    if Rev >= 10000:
        return 1.0
    rel = C / v.d_mm ** 2
    if rel >= 0.016 * N18:          # obturador de tamaño completo
        n = N2 / rel ** 2
    else:                            # obturador reducido
        n = 1 + N32 * rel ** (2.0 / 3.0)
    FR_lam = 0.026 / v.FL * math.sqrt(n * Rev)
    if Rev < 10:
        return min(FR_lam, 1.0)
    FR_tr = 1 + (0.33 * math.sqrt(v.FL) / n ** 0.25) * math.log10(Rev / 10000)
    return max(min(FR_tr, FR_lam, 1.0), 1e-9)


class CapacidadInsuficiente(ArithmeticError):
    """El diámetro de válvula no puede pasar el caudal pedido con ningún C."""


# ---------------------------------------------------------------------------
# Resolución numérica
# ---------------------------------------------------------------------------
def _resolver(f, c0: float, tol: float = 1e-10, max_iter: int = 200) -> tuple[float, int]:
    """Resuelve C = f(C). Busca un cambio de signo de h(C) = C/f(C) − 1 en escala
    logarítmica alrededor de c0 y luego aplica bisección (robusto aunque el punto
    fijo sea inestable, como ocurre en régimen laminar)."""
    def h(c):
        try:
            return c / f(c) - 1
        except (OverflowError, ZeroDivisionError, ValueError):
            return float("nan")
    # 1) intento rápido de punto fijo
    c = c0
    for i in range(1, 40):
        try:
            cn = f(c)
        except (OverflowError, ZeroDivisionError, ValueError):
            break
        if not math.isfinite(cn) or cn <= 0:
            break
        if abs(cn - c) <= tol * cn:
            return cn, i
        c = cn
    # 2) búsqueda de intervalo con cambio de signo
    puntos = [c0 * 10 ** (k / 8) for k in range(-24, 49)]
    valores = [h(p) for p in puntos]
    lo = hi = None
    for a, b, ha, hb in zip(puntos, puntos[1:], valores, valores[1:]):
        if math.isfinite(ha) and math.isfinite(hb) and ha * hb <= 0:
            lo, hi, hlo = a, b, ha
            break
    if lo is None:
        raise CapacidadInsuficiente(
            "No existe un coeficiente de caudal que cumpla las condiciones con este diámetro de "
            "válvula: los reductores o el régimen no turbulento limitan la capacidad. Pruebe un "
            "diámetro de válvula mayor.")
    for i in range(max_iter):
        mid = math.sqrt(lo * hi)
        hm = h(mid)
        if hm * hlo > 0:
            lo, hlo = mid, hm
        else:
            hi = mid
        if hi / lo - 1 < tol:
            break
    return math.sqrt(lo * hi), 40 + i


def _validar_comun(P1, P2, v: Valvula, alertas: list[Alerta]):
    if P1 <= 0:
        alertas.append(Alerta("dato_p1", Severidad.ERROR, "Presión de entrada inválida",
                              "La presión de entrada P1 debe ser mayor que cero (absoluta)."))
    if P2 <= 0:
        alertas.append(Alerta("dato_p2", Severidad.ERROR, "Presión de salida inválida",
                              "La presión de salida P2 debe ser mayor que cero (absoluta). "
                              "Revise si ingresó presión manométrica como absoluta."))
    if P2 >= P1:
        alertas.append(Alerta("dato_dp", Severidad.ERROR, "Caída de presión nula o negativa",
                              "P2 debe ser menor que P1: sin caída de presión no hay flujo a "
                              "través de la válvula."))
    if not 0.2 <= v.FL <= 1.0:
        alertas.append(Alerta("dato_fl", Severidad.ERROR, "FL fuera de rango",
                              f"FL = {_n(v.FL)}. Los valores físicos están entre 0,2 y 1,0."))
    if not 0.05 <= v.xT <= 1.0:
        alertas.append(Alerta("dato_xt", Severidad.ERROR, "xT fuera de rango",
                              f"xT = {_n(v.xT)}. Los valores físicos están entre 0,05 y 1,0."))
    if not 0 < v.Fd <= 1.0:
        alertas.append(Alerta("dato_fd", Severidad.ERROR, "Fd fuera de rango",
                              f"Fd = {_n(v.Fd)}. Debe estar entre 0 y 1."))
    if v.d_mm <= 0:
        alertas.append(Alerta("dato_d", Severidad.ERROR, "Diámetro de válvula inválido",
                              "El diámetro nominal de la válvula debe ser mayor que cero."))
    for D, nombre in ((v.D1_mm, "aguas arriba"), (v.D2_mm, "aguas abajo")):
        if D is not None and D < v.d_mm:
            alertas.append(Alerta("dato_D_menor", Severidad.ADVERTENCIA,
                                  "Tubería menor que la válvula",
                                  f"La tubería {nombre} ({_n(D)} mm) es menor que la válvula "
                                  f"({_n(v.d_mm)} mm). Las fórmulas de reductores de la norma "
                                  "suponen reducciones concéntricas desde una línea mayor."))


# ---------------------------------------------------------------------------
# Líquidos (cláusula 5)
# ---------------------------------------------------------------------------
def dimensionar_liquido(f: Liquido, v: Valvula) -> Resultado:
    alertas: list[Alerta] = []
    _validar_comun(f.P1, f.P2, v, alertas)
    if f.rho1 <= 0:
        alertas.append(Alerta("dato_rho", Severidad.ERROR, "Densidad inválida",
                              "La densidad del líquido debe ser mayor que cero."))
    if f.Pv < 0 or f.Pc <= 0:
        alertas.append(Alerta("dato_pv", Severidad.ERROR, "Presión de vapor o crítica inválida",
                              "La presión de vapor no puede ser negativa y la presión crítica "
                              "debe ser mayor que cero."))
    elif f.Pv >= f.Pc:
        alertas.append(Alerta("dato_pv", Severidad.ERROR, "Presión de vapor ≥ presión crítica",
                              "La presión de vapor no puede superar la presión crítica: "
                              "el fluido estaría en estado supercrítico."))
    if f.Pv >= f.P1 > 0:
        alertas.append(Alerta("dato_pv_p1", Severidad.ERROR, "El líquido ya vaporiza a la entrada",
                              "La presión de vapor es mayor o igual que P1: el fluido no es un "
                              "líquido a la entrada. Use el cálculo de gas, vapor o bifásico."))
    if f.nu <= 0:
        alertas.append(Alerta("dato_nu", Severidad.ERROR, "Viscosidad inválida",
                              "La viscosidad cinemática debe ser mayor que cero."))
    Q = None
    if f.Q is None and f.W is None:
        alertas.append(Alerta("dato_caudal", Severidad.ERROR, "Falta el caudal",
                              "Indique caudal volumétrico o másico."))
    else:
        Q = f.caudal_volumetrico() if f.rho1 > 0 else None
        if Q is not None and Q <= 0:
            alertas.append(Alerta("dato_caudal", Severidad.ERROR, "Caudal inválido",
                                  "El caudal debe ser mayor que cero."))
    errores = [a for a in alertas if a.severidad == Severidad.ERROR]
    if errores:
        raise ErrorDatos(errores)

    m = Memoria()
    m.agregar("Q", "Caudal volumétrico a condiciones de entrada", Q, "m³/h")
    dP = m.agregar("ΔP", "Caída de presión a través de la válvula", f.P1 - f.P2, "kPa", "P1 − P2")
    rel = m.agregar("ρ1/ρ0", "Densidad relativa respecto al agua a 15 °C", f.rho1 / RHO_AGUA_15C,
                    "-", "ρ1 / 999,1")
    FF = m.agregar("FF", "Factor de relación de presión crítica del líquido",
                   0.96 - 0.28 * math.sqrt(f.Pv / f.Pc), "-", "0,96 − 0,28·√(Pv/Pc)",
                   f"{REF} ec. (4)")

    def calc(C):
        FP = factor_FP(C, v)
        FLP = factor_FLP(C, v)
        dPch = (FLP / FP) ** 2 * (f.P1 - FF * f.Pv)
        dPs = min(dP, dPch)
        return Q / (N1 * FP) * math.sqrt(rel / dPs), FP, FLP, dPch

    C0 = Q / N1 * math.sqrt(rel / min(dP, v.FL ** 2 * (f.P1 - FF * f.Pv)))
    C_t, it = _resolver(lambda c: calc(c)[0], C0) if v.con_reductores else (C0, 1)
    _, FP, FLP, dPch = calc(C_t)
    m.agregar("FP", "Factor de geometría de tubería", FP, "-",
              "1/√(1 + Σζ/N2·(C/d²)²)", f"{REF} ec. (19)")
    if v.con_reductores:
        m.agregar("FLP", "FL combinado válvula + reductores", FLP, "-",
                  "FL/√(1 + FL²/N2·Σζ1·(C/d²)²)", f"{REF} ec. (24)")
    m.agregar("ΔPchoked", "Caída de presión límite de flujo crítico (bloqueado)", dPch, "kPa",
              "(FLP/FP)²·(P1 − FF·Pv)", f"{REF} ec. (3)")
    bloqueado = dP >= dPch
    m.agregar("ΔPs", "Caída de presión usada para dimensionar", min(dP, dPch), "kPa",
              "mín(ΔP, ΔPchoked)")
    m.agregar("C_turb", "Kv requerido en régimen turbulento", C_t, "m³/h",
              "Q/(N1·FP)·√((ρ1/ρ0)/ΔPs)" if not bloqueado else "Q/(N1·FLP)·√((ρ1/ρ0)/(P1 − FF·Pv))",
              f"{REF} ec. (1)/(2)")

    # Reynolds y flujo no turbulento
    Rev = reynolds_valvula(Q, f.nu, C_t, v)
    FR, C = 1.0, C_t
    regimen = "turbulento"
    if Rev < 10000:
        # La norma no corrige por accesorios en régimen no turbulento
        C_noFP = Q / N1 * math.sqrt(rel / dP)
        def g(c):
            return C_noFP / factor_FR(reynolds_valvula(Q, f.nu, c, v), c, v)
        C, _ = _resolver(g, C_noFP)
        Rev = reynolds_valvula(Q, f.nu, C, v)
        FR = factor_FR(Rev, C, v)
        regimen = "laminar" if Rev < 10 or FR < 0.3 else "transición"
        alertas.append(Alerta(
            "flujo_no_turbulento", Severidad.ADVERTENCIA, "Flujo no turbulento",
            f"Rev = {_n(Rev, 0)} < 10 000: el flujo es de {regimen}. La capacidad se corrigió "
            f"con FR = {_n(FR, 3)}. La exactitud de las ecuaciones es menor en este régimen.",
            remedios=["Verifique la viscosidad a la temperatura real de operación.",
                      "Para fluidos muy viscosos considere válvulas de paso recto (bola, "
                      "segmento) que tienen mayor Fd."],
            referencia=f"{REF} cláusula 9"))
    m.agregar("Rev", "Número de Reynolds de la válvula", Rev, "-",
              "N4·Fd·Q/(ν·√(C·FL))·(FL²·C²/(N2·D⁴) + 1)^¼", f"{REF} ec. (28)")
    m.agregar("FR", "Factor de número de Reynolds", FR, "-", "", f"{REF} cláusula 9")
    m.agregar("Kv", "Coeficiente de caudal requerido", C, "m³/h")
    m.agregar("Cv", "Coeficiente de caudal requerido", C / 0.865, "gpm·psi^-½", "Kv / 0,865")

    return Resultado(C, C / 0.865, bloqueado, regimen, FP, Rev, FR, m, alertas,
                     {"FF": FF, "dP": dP, "dPchoked": dPch, "FLP": FLP, "Q": Q})


# ---------------------------------------------------------------------------
# Gases y vapores (cláusula 6)
# ---------------------------------------------------------------------------
def dimensionar_gas(f: Gas, v: Valvula) -> Resultado:
    alertas: list[Alerta] = []
    _validar_comun(f.P1, f.P2, v, alertas)
    if not 1.0 < f.gamma <= 2.0:
        alertas.append(Alerta("dato_gamma", Severidad.ERROR, "γ fuera de rango",
                              f"γ = {_n(f.gamma)}. La relación de calores específicos de gases "
                              "reales está entre 1,0 y 1,67 (monoatómicos)."))
    if not 0.05 <= f.Z <= 2.0:
        alertas.append(Alerta("dato_z", Severidad.ERROR, "Z fuera de rango",
                              f"Z = {_n(f.Z)}. Revise el factor de compresibilidad."))
    if f.M <= 0:
        alertas.append(Alerta("dato_m", Severidad.ERROR, "Masa molar inválida",
                              "La masa molar debe ser mayor que cero."))
    if f.T1 <= 0:
        alertas.append(Alerta("dato_t1", Severidad.ERROR, "Temperatura inválida",
                              "La temperatura absoluta debe ser mayor que cero."))
    if f.mu <= 0:
        alertas.append(Alerta("dato_mu", Severidad.ERROR, "Viscosidad inválida",
                              "La viscosidad dinámica debe ser mayor que cero."))
    if f.W is None and f.QN is None:
        alertas.append(Alerta("dato_caudal", Severidad.ERROR, "Falta el caudal",
                              "Indique caudal másico o caudal en condiciones normales."))
    errores = [a for a in alertas if a.severidad == Severidad.ERROR]
    if errores:
        raise ErrorDatos(errores)

    m = Memoria()
    W = m.agregar("W", "Caudal másico", f.caudal_masico(), "kg/h")
    if W <= 0:
        raise ErrorDatos([Alerta("dato_caudal", Severidad.ERROR, "Caudal inválido",
                                 "El caudal debe ser mayor que cero.")])
    rho1 = m.agregar("ρ1", "Densidad a la entrada", f.densidad(), "kg/m³", "P1·M/(Z·R·T1)")
    x = m.agregar("x", "Relación de caída de presión", (f.P1 - f.P2) / f.P1, "-", "ΔP/P1",
                  f"{REF} cláusula 6")
    Fg = m.agregar("Fγ", "Factor de relación de calores específicos", f.gamma / 1.40, "-",
                   "γ/1,40", f"{REF} ec. (14)")

    def calc(C):
        FP = factor_FP(C, v)
        xTP = factor_xTP(C, v, FP)
        xch = Fg * xTP
        xs = min(x, xch)
        Y = 1 - xs / (3 * xch)
        return W / (N6 * FP * Y * math.sqrt(xs * f.P1 * rho1)), FP, xTP, xch, xs, Y

    xch0 = Fg * v.xT
    xs0 = min(x, xch0)
    C0 = W / (N6 * (1 - xs0 / (3 * xch0)) * math.sqrt(xs0 * f.P1 * rho1))
    C_t, _ = _resolver(lambda c: calc(c)[0], C0) if v.con_reductores else (C0, 1)
    _, FP, xTP, xch, xs, Y = calc(C_t)
    m.agregar("FP", "Factor de geometría de tubería", FP, "-",
              "1/√(1 + Σζ/N2·(C/d²)²)", f"{REF} ec. (19)")
    if v.con_reductores:
        m.agregar("xTP", "xT combinado válvula + reductores", xTP, "-",
                  "(xT/FP²)/(1 + xT·ζi/N5·(C/d²)²)", f"{REF} ec. (26)")
    m.agregar("xchoked", "Relación de caída de presión de flujo crítico", xch, "-",
              "Fγ·xTP", f"{REF} ec. (13)")
    bloqueado = x >= xch
    m.agregar("xs", "Relación de caída de presión usada para dimensionar", xs, "-",
              "mín(x, xchoked)")
    m.agregar("Y", "Factor de expansión", Y, "-", "1 − xs/(3·xchoked)", f"{REF} ec. (15)")
    m.agregar("C_turb", "Kv requerido en régimen turbulento", C_t, "m³/h",
              "W/(N6·FP·Y·√(xs·P1·ρ1))", f"{REF} ec. (10)")

    Qreal = m.agregar("Q", "Caudal volumétrico real a la entrada (para Rev)", W / rho1, "m³/h", "W/ρ1",
                      f"{REF} cláusula 9, nota 1: caudal real, no normal ni estándar")
    nu = m.agregar("ν", "Viscosidad cinemática a la entrada", f.mu / rho1, "m²/s", "μ/ρ1")
    Rev = reynolds_valvula(Qreal, nu, C_t, v)
    FR, C, regimen = 1.0, C_t, "turbulento"
    if Rev < 10000:
        dP = f.P1 - f.P2
        C_lam = W / N27 * math.sqrt(f.T1 / (dP * (f.P1 + f.P2) * f.M))
        def g(c):
            return C_lam / factor_FR(reynolds_valvula(Qreal, nu, c, v), c, v)
        C, _ = _resolver(g, C_lam)
        Rev = reynolds_valvula(Qreal, nu, C, v)
        FR = factor_FR(Rev, C, v)
        regimen = "laminar" if Rev < 10 or FR < 0.3 else "transición"
        alertas.append(Alerta(
            "flujo_no_turbulento", Severidad.ADVERTENCIA, "Flujo no turbulento",
            f"Rev = {_n(Rev, 0)} < 10 000: el flujo de gas es de {regimen}. "
            f"Se usó la ecuación no turbulenta con FR = {_n(FR, 3)}.",
            referencia=f"{REF} cláusula 9"))
    m.agregar("Rev", "Número de Reynolds de la válvula", Rev, "-",
              "N4·Fd·Q/(ν·√(C·FL))·(FL²·C²/(N2·D⁴) + 1)^¼", f"{REF} ec. (28)")
    m.agregar("FR", "Factor de número de Reynolds", FR, "-", "", f"{REF} cláusula 9")
    m.agregar("Kv", "Coeficiente de caudal requerido", C, "m³/h")
    m.agregar("Cv", "Coeficiente de caudal requerido", C / 0.865, "gpm·psi^-½", "Kv / 0,865")
    return Resultado(C, C / 0.865, bloqueado, regimen, FP, Rev, FR, m, alertas,
                     {"x": x, "xchoked": xch, "Y": Y, "xTP": xTP, "rho1": rho1, "W": W,
                      "Fgamma": Fg})


# ---------------------------------------------------------------------------
# Cálculo inverso: caudal que pasa un Kv dado (verificación de una válvula)
# ---------------------------------------------------------------------------
def caudal_liquido(Kv: float, f: Liquido, v: Valvula) -> float:
    """Caudal volumétrico [m³/h] turbulento que pasa por una válvula de Kv dado."""
    FP = factor_FP(Kv, v)
    FLP = factor_FLP(Kv, v)
    FF = 0.96 - 0.28 * math.sqrt(f.Pv / f.Pc)
    dPs = min(f.P1 - f.P2, (FLP / FP) ** 2 * (f.P1 - FF * f.Pv))
    return Kv * N1 * FP * math.sqrt(dPs / (f.rho1 / RHO_AGUA_15C))


def caudal_gas(Kv: float, f: Gas, v: Valvula) -> float:
    """Caudal másico [kg/h] turbulento que pasa por una válvula de Kv dado."""
    FP = factor_FP(Kv, v)
    xch = f.gamma / 1.4 * factor_xTP(Kv, v, FP)
    xs = min((f.P1 - f.P2) / f.P1, xch)
    Y = 1 - xs / (3 * xch)
    return Kv * N6 * FP * Y * math.sqrt(xs * f.P1 * f.densidad())


# ---------------------------------------------------------------------------
# Flujo bifásico líquido + gas/vapor a la entrada (fuera del alcance de IEC)
# ---------------------------------------------------------------------------
@dataclass
class Bifasico:
    """Mezcla líquido + gas (o vapor) a la entrada de la válvula.

    W     : caudal másico total [kg/h]
    xg    : fracción másica de gas o vapor (calidad) 0 < xg < 1
    rho_l : densidad del líquido a la entrada [kg/m³]
    rho_g : densidad del gas o vapor a la entrada [kg/m³]
    Pv, Pc: presión de vapor y crítica del líquido [kPa abs]
    gamma : relación de calores específicos del gas
    """
    P1: float
    P2: float
    T1: float
    W: float
    xg: float
    rho_l: float
    rho_g: float
    Pv: float
    Pc: float
    gamma: float

    def densidad_homogenea(self, P: float | None = None) -> float:
        rg = self.rho_g if P is None else self.rho_g * P / self.P1
        return 1.0 / (self.xg / rg + (1 - self.xg) / self.rho_l)


def dimensionar_bifasico(f: Bifasico, v: Valvula) -> Resultado:
    """Método de suma de fases separadas (ecuación publicada en la literatura de
    dimensionamiento, basada en los factores de IEC 60534-2-1 para cada fase):

        C = W/(N6·FP) · √( ff/(ΔPf·ρl) + fg/(ΔPg·ρg·Y²) )

    con ΔPf limitado por el flujo crítico del líquido y ΔPg por el del gas.
    """
    alertas: list[Alerta] = []
    _validar_comun(f.P1, f.P2, v, alertas)
    if not 0 < f.xg < 1:
        alertas.append(Alerta("dato_xg", Severidad.ERROR, "Fracción de gas inválida",
                              "La fracción másica de gas o vapor debe estar entre 0 y 1 (sin incluirlos). "
                              "Con 0 use el cálculo de líquido y con 1 el de gas."))
    if f.rho_l <= 0 or f.rho_g <= 0 or f.rho_g >= f.rho_l:
        alertas.append(Alerta("dato_rho", Severidad.ERROR, "Densidades inválidas",
                              "Las densidades deben ser positivas y la del gas menor que la del líquido."))
    if f.W is None or f.W <= 0:
        alertas.append(Alerta("dato_caudal", Severidad.ERROR, "Caudal inválido",
                              "El caudal másico total debe ser mayor que cero."))
    if not 1.0 < f.gamma <= 2.0:
        alertas.append(Alerta("dato_gamma", Severidad.ERROR, "γ fuera de rango",
                              f"γ = {_n(f.gamma)}. Debe estar entre 1,0 y 2,0."))
    errores = [a for a in alertas if a.severidad == Severidad.ERROR]
    if errores:
        raise ErrorDatos(errores)
    m = Memoria()
    ref = "Método de suma de fases (fuera del alcance de IEC 60534-2-1)"
    dP = m.agregar("ΔP", "Caída de presión", f.P1 - f.P2, "kPa", "P1 − P2")
    ff = m.agregar("ff", "Fracción másica de líquido", 1 - f.xg, "-")
    fg = m.agregar("fg", "Fracción másica de gas o vapor", f.xg, "-")
    FF = m.agregar("FF", "Factor de presión crítica del líquido", 0.96 - 0.28 * math.sqrt(min(f.Pv, f.Pc) / f.Pc),
                   "-", "0,96 − 0,28·√(Pv/Pc)", f"{REF} ec. (4)")
    Fg = m.agregar("Fγ", "Factor de calores específicos", f.gamma / 1.4, "-", "γ/1,40")

    def calc(C):
        FP = factor_FP(C, v)
        FLP = factor_FLP(C, v)
        xTP = factor_xTP(C, v, FP)
        dPf = min(dP, (FLP / FP) ** 2 * (f.P1 - FF * f.Pv))
        dPg = min(dP, Fg * xTP * f.P1)
        Y = 1 - (dPg / f.P1) / (3 * Fg * xTP)
        C_new = f.W / (N6 * FP) * math.sqrt(ff / (dPf * f.rho_l) + fg / (dPg * f.rho_g * Y ** 2))
        return C_new, FP, dPf, dPg, Y, xTP

    C0 = calc(1.0)[0] if not v.con_reductores else None
    if v.con_reductores:
        C, _ = _resolver(lambda c: calc(c)[0], calc(1e-6)[0])
    else:
        C = C0
    _, FP, dPf, dPg, Y, xTP = calc(C)
    m.agregar("FP", "Factor de geometría de tubería", FP, "-", "", f"{REF} cláusula 7")
    m.agregar("ΔPf", "Caída de presión efectiva de la fase líquida", dPf, "kPa", "mín(ΔP, (FLP/FP)²·(P1 − FF·Pv))")
    m.agregar("ΔPg", "Caída de presión efectiva de la fase gaseosa", dPg, "kPa", "mín(ΔP, Fγ·xTP·P1)")
    m.agregar("Y", "Factor de expansión de la fase gaseosa", Y, "-", "1 − (ΔPg/P1)/(3·Fγ·xTP)")
    m.agregar("Kv", "Coeficiente de caudal requerido", C, "m³/h",
              "W/(N6·FP)·√(ff/(ΔPf·ρl) + fg/(ΔPg·ρg·Y²))", ref)
    m.agregar("Cv", "Coeficiente de caudal requerido", C / 0.865, "gpm·psi^-½", "Kv / 0,865")
    bloqueado = dPf < dP or dPg < dP
    alertas.append(Alerta(
        "bifasico_metodo", Severidad.INFO, "Flujo bifásico: método fuera de la norma IEC",
        "IEC 60534-2-1 no cubre fluidos bifásicos. Se usó el método de suma de fases separadas, de "
        "uso extendido en la industria. Su exactitud es menor que la de las ecuaciones de la norma; "
        "seleccione la válvula con un margen de capacidad adicional y verifique la erosión.",
        remedios=["Si es posible, separe las fases aguas arriba (separador) y controle cada una por separado."],
        referencia=ref))
    return Resultado(C, C / 0.865, bloqueado, "bifásico", FP, float("nan"), 1.0, m, alertas,
                     {"dPf": dPf, "dPg": dPg, "Y": Y, "xTP": xTP, "FF": FF})
