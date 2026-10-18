"""Predicción de ruido de válvulas de control.

* Ruido aerodinámico (gases y vapores): IEC 60534-8-3:2010.
* Ruido hidrodinámico (líquidos):        IEC 60534-8-4:2015.

El resultado es el nivel de presión sonora ponderado A a 1 m aguas abajo de
la válvula y a 1 m de la pared de la tubería, LpAe,1m [dB(A)], calculado por
bandas de tercio de octava de 12,5 Hz a 20 kHz.

La estructura del cálculo se verificó contra los ejemplos resueltos de las
normas tal como los reproduce la biblioteca «fluids» (C. Bell, licencia MIT;
ver LICENCIAS_TERCEROS.md).
"""
from __future__ import annotations

import math

from .modelos import Alerta, Memoria, Severidad, _n

R = 8314.462618          # J/(kmol·K)
P_STD = 101325.0
CV_POR_KV = 1 / 0.865

# Bandas de tercio de octava y ponderación A
FRECUENCIAS = [12.5, 16, 20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
               630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000,
               12500, 16000, 20000]
PONDERACION_A = [-63.4, -56.7, -50.5, -44.7, -39.4, -34.6, -30.2, -26.2, -22.5, -19.1, -16.1,
                 -13.4, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9, -0.8, 0.0, 0.6, 1.0, 1.2, 1.3, 1.2,
                 1.0, 0.5, -0.1, -1.1, -2.5, -4.3, -6.6, -9.3]

REF8_3 = "IEC 60534-8-3:2010"
REF8_4 = "IEC 60534-8-4:2015"


def _suma_db(niveles):
    return 10 * math.log10(sum(10 ** (0.1 * L) for L in niveles))


# ---------------------------------------------------------------------------
# IEC 60534-8-3: gases
# ---------------------------------------------------------------------------
def ruido_gas(m_kgs, P1_kPa, P2_kPa, T1, rho1, gamma, M, Kv, d_m, Di_m, tp_m, Fd, FL_eff,
              rho_pared=7800.0, c_pared=5000.0, P_aire=101325.0, c_aire=343.0,
              An=-3.8, Stp=0.2, T2=None, beta=0.93, rho2=None, c2=None,
              memoria: Memoria | None = None) -> dict:
    """Devuelve dict con LpAe1m [dB(A)], régimen, fp, Lpi, espectro, etc.

    FL_eff: FLP/FP si hay reductores, FL en caso contrario.
    rho2, c2: densidad y velocidad del sonido aguas abajo. Si se omiten se usan las
        expresiones de la norma para gas ideal: ρ2 = ρ1·P2/P1 y c2 = √(γ·R·T2/M).
    d_m: diámetro de salida de la válvula (ruido de salida y corrección ΔTL).
    An: corrección de eficiencia acústica de la válvula (−3,8 válvulas
        convencionales de un solo pasaje según la norma).
    """
    mem = memoria or Memoria()
    k = gamma
    P1, P2 = P1_kPa * 1000, P2_kPa * 1000
    T2 = T2 or T1
    C = Kv * CV_POR_KV
    N14 = 4.6e-3
    x = (P1 - P2) / P1
    FL = FL_eff

    x_vcc = 1 - (2 / (k + 1)) ** (k / (k - 1))
    xc = FL ** 2 * x_vcc
    alfa = (1 - x_vcc) / (1 - xc)
    xB = 1 - 1 / alfa * (1 / k) ** (k / (k - 1))
    xCE = 1 - 1 / (22 * alfa)
    if x <= xc:
        regimen = 1
    elif x <= x_vcc:
        regimen = 2
    elif x <= xB:
        regimen = 3
    elif x <= xCE:
        regimen = 4
    else:
        regimen = 5
    nombres = {1: "I (subsónico)", 2: "II (sónico en vena contracta, con recompresión)",
               3: "III (sin recompresión, interacción de choques)", 4: "IV (celdas de choque)",
               5: "V (eficiencia acústica constante)"}
    mem.agregar("x", "Relación de caída de presión", x, "-", "ΔP/P1", REF8_3)
    mem.agregar("xvcc", "x en vena contracta al llegar a flujo sónico", x_vcc, "-",
                "1 − (2/(γ+1))^(γ/(γ−1))", REF8_3)
    mem.agregar("xC", "x de inicio de flujo crítico", xc, "-", "FL²·xvcc", REF8_3)
    mem.agregar("α", "Relación de recuperación", alfa, "-", "(1 − xvcc)/(1 − xC)", REF8_3)
    mem.agregar("xB", "Límite régimen III/IV", xB, "-", "1 − (1/α)·(1/γ)^(γ/(γ−1))", REF8_3)
    mem.agregar("xCE", "Límite régimen IV/V", xCE, "-", "1 − 1/(22·α)", REF8_3)
    mem.agregar("Régimen", f"Régimen de ruido {nombres[regimen]}", regimen, "-", "", REF8_3)

    Dj = mem.agregar("Dj", "Diámetro del chorro", N14 * Fd * math.sqrt(C * FL), "m",
                     "N14·Fd·√(Cv·FL)", REF8_3)
    Mj5 = math.sqrt(2 / (k - 1) * (22 ** ((k - 1) / k) - 1))
    if regimen == 1:
        Mvc = math.sqrt(2 / (k - 1) * ((1 - x / FL ** 2) ** ((1 - k) / k) - 1))
        cvc = math.sqrt(k * P1 / rho1 * (1 - x / FL ** 2) ** ((k - 1) / k))
        Wm = 0.5 * m_kgs * (Mvc * cvc) ** 2
        fp = Stp * Mvc * cvc / Dj
        eta = 10 ** An * FL ** 2 * Mvc ** 3
        mem.agregar("Mvc", "Mach en la vena contracta", Mvc, "-", "", REF8_3)
    else:
        Mj = min(math.sqrt(2 / (k - 1) * ((1 / (alfa * (1 - x))) ** ((k - 1) / k) - 1)), Mj5)
        if regimen == 5:
            Mj = Mj5
        cvcc = math.sqrt(2 * k * P1 / ((k + 1) * rho1))
        Wm = 0.5 * m_kgs * cvcc ** 2
        if regimen in (2, 3):
            fp = Stp * Mj * cvcc / Dj
        else:
            fp = 1.4 * Stp * cvcc / Dj / math.sqrt(Mj ** 2 - 1)
        if regimen == 2:
            eta = 10 ** An * x / x_vcc * Mj ** (6.6 * FL ** 2)
        elif regimen == 3:
            eta = 10 ** An * Mj ** (6.6 * FL ** 2)
        else:
            eta = 0.5 * 10 ** An * Mj ** 2 * math.sqrt(2) ** (6.6 * FL ** 2)
        mem.agregar("Mj", "Mach del chorro libremente expandido", Mj, "-", "", REF8_3)
    mem.agregar("Wm", "Potencia mecánica del chorro", Wm, "W", "", REF8_3)
    mem.agregar("η", "Eficiencia acústica", eta, "-", "", REF8_3)
    Wa = mem.agregar("Wa", "Potencia acústica generada", eta * Wm, "W", "η·Wm", REF8_3)
    mem.agregar("fp", "Frecuencia de pico", fp, "Hz", "", REF8_3)

    rho2 = rho2 or rho1 * P2 / P1
    c2 = c2 or math.sqrt(k * R * T2 / M)
    M2 = 4 * m_kgs / (math.pi * Di_m ** 2 * rho2 * c2)
    mem.agregar("M2", "Mach en la tubería de salida", M2, "-", "4·m/(π·Di²·ρ2·c2)", REF8_3)
    Lg = 16 * math.log10(1 / (1 - min(M2, 0.3)))
    Lpi = mem.agregar("Lpi", "Nivel de presión sonora interno", 10 * math.log10(3.2e9 * Wa * rho2 * c2 / Di_m ** 2) + Lg,
                      "dB", "10·lg(3,2·10⁹·Wa·ρ2·c2/Di²) + Lg", REF8_3)
    LpiR = None
    if M2 > 0.3:   # ruido de salida de la válvula
        Up = 4 * m_kgs / (math.pi * rho2 * Di_m ** 2)
        UR = Up * Di_m ** 2 / (beta * d_m ** 2)
        WmR = 0.5 * m_kgs * UR ** 2 * ((1 - d_m ** 2 / Di_m ** 2) ** 2 + 0.2)
        fpR = Stp * UR / d_m
        WaR = 10 ** An * (UR / c2) ** 3 * WmR
        LpiR = 10 * math.log10(3.2e9 * WaR * rho2 * c2 / Di_m ** 2) + Lg

    fr = c_pared / (math.pi * Di_m)
    fo = 0.25 * fr * (c2 / c_aire)
    fg = math.sqrt(3) * c_aire ** 2 / (math.pi * tp_m * c_pared)
    if d_m > 0.15:
        dTL = 0.0
    elif d_m >= 0.05:
        dTL = -16660 * d_m ** 3 + 6370 * d_m ** 2 - 813 * d_m + 35.8
    else:
        dTL = 9.0
    distancia = 10 * math.log10((Di_m + 2 * tp_m + 2) / (Di_m + 2 * tp_m))
    espectro, esp_trim, esp_salida = [], [], []
    for fi, A in zip(FRECUENCIAS, PONDERACION_A):
        r = fi / fp
        Lpif = Lpi - 8 - 10 * math.log10((1 + (0.5 * r) ** 2.5) * (1 + (0.5 / r) ** 1.7))
        Lpif_trim = Lpif
        if LpiR is not None:
            rR = fi / fpR
            LpiRf = LpiR - 8 - 10 * math.log10((1 + (0.5 * rR) ** 2.5) * (1 + (0.5 / rR) ** 1.7))
            Lpif = _suma_db([Lpif, LpiRf])
        if fi < fo:
            Gx = (fo / fr) ** (2 / 3) * (fi / fo) ** 4
            Gy = fo / fg if fo < fg else 1.0
        else:
            Gx = math.sqrt(fi / fr) if fi < fr else 1.0
            Gy = fi / fg if fi < fg else 1.0
        eta_s = math.sqrt(0.01 / fi)
        den = (rho2 * c2 + 2 * math.pi * tp_m * fi * rho_pared * eta_s) / (415 * Gy) + 1
        TL = 10 * math.log10(8.25e-7 * (c2 / (tp_m * fi)) ** 2 * Gx / den * P_aire / P_STD) - dTL
        Le = Lpif + TL - distancia
        espectro.append((fi, Le, Le + A))
        esp_trim.append(Lpif_trim + TL - distancia + A)
        if LpiR is not None:
            esp_salida.append(LpiRf + TL - distancia + A)
    L_trim = _suma_db(esp_trim)
    L_salida = _suma_db(esp_salida) if esp_salida else None
    mem.agregar("LpAe,trim", "Ruido generado en el trim (ponderado A, a 1 m)", L_trim, "dB(A)",
                "Σ bandas, fuente: chorro en la vena contracta", REF8_3)
    if L_salida is not None:
        mem.agregar("LpAe,salida", "Ruido generado en la salida de la válvula (a 1 m)", L_salida, "dB(A)",
                    "Σ bandas, fuente: expansión a la salida (M2 > 0,3)", REF8_3)
    LpAe = mem.agregar("LpAe,1m", "Nivel de ruido ponderado A a 1 m", _suma_db([e[2] for e in espectro]),
                       "dB(A)", "Σ bandas de 1/3 de octava (Lpi + TL − dist + A)", REF8_3)
    return {"LpAe1m": LpAe, "LpAe_trim": L_trim, "LpAe_salida": L_salida, "regimen": regimen,
            "regimen_nombre": nombres[regimen], "fp": fp, "Lpi": Lpi, "M2": M2, "eta": eta,
            "rho2": rho2, "c2": c2, "espectro": espectro, "memoria": mem}


def correccion_distancia(Di_m: float, tp_m: float, r_m: float) -> float:
    """Diferencia de nivel entre 1 m y r m de la pared de la tubería (fuente lineal).

    IEC 60534-8-3 da el nivel a 1 m de la pared con el término −10·lg((Di + 2tp + 2)/(Di + 2tp));
    a una distancia r el término es −10·lg((Di + 2tp + 2r)/(Di + 2tp)). La corrección a sumar
    al nivel a 1 m es por lo tanto −10·lg((Di + 2tp + 2r)/(Di + 2tp + 2)).
    """
    De = Di_m + 2 * tp_m
    return -10 * math.log10((De + 2 * r_m) / (De + 2))


# ---------------------------------------------------------------------------
# IEC 60534-8-4: líquidos
# ---------------------------------------------------------------------------
def ruido_liquido(m_kgs, P1_kPa, P2_kPa, Pv_kPa, rho, c_liq, Kv, d_m, Di_m, tp_m, FL, Fd,
                  rho_pared=7800.0, c_pared=5000.0, rho_aire=1.293, c_aire=343.0,
                  xFz=None, An=-4.6, memoria: Memoria | None = None) -> dict:
    """An: −4,6 válvulas de globo; −4,3 mariposa; −4,0 expansores (según la norma)."""
    mem = memoria or Memoria()
    P1, P2, Psat = P1_kPa * 1000, P2_kPa * 1000, Pv_kPa * 1000
    N34, N14 = 1.17, 0.0046
    C = Kv * CV_POR_KV
    xF = (P1 - P2) / (P1 - Psat)
    dPc = min(P1 - P2, FL ** 2 * (P1 - Psat))
    if xFz is None:
        xFz = 0.9 / math.sqrt(1 + 3 * Fd * math.sqrt(C / (N34 * FL)))
    xFzp1 = xFz * (6e5 / P1) ** 0.125
    mem.agregar("xF", "Relación diferencial de presión", xF, "-", "ΔP/(P1 − Pv)", REF8_4)
    mem.agregar("xFzp1", "Inicio de cavitación corregido por presión", xFzp1, "-",
                "xFz·(6·10⁵/P1)^0,125", REF8_4)
    Dj = N14 * Fd * math.sqrt(C * FL)
    Uvc = math.sqrt(2 * dPc / rho) / FL
    Wm = 0.5 * m_kgs * Uvc ** 2 * FL ** 2
    cavita = xF > xFzp1
    eta_t = 10 ** An * Uvc / c_liq
    eta_c = 0.0
    if cavita:
        x0 = xF - xFzp1
        eta_c = (0.32 * eta_t * math.sqrt((P1 - P2) / (dPc * xFzp1)) * math.exp(5 * xFzp1)
                 * math.sqrt((1 - xFzp1) / (1 - xF)) * (xF / xFzp1) ** 5 * x0 ** 1.5)
    Wa = (eta_t + eta_c) * Wm
    mem.agregar("Uvc", "Velocidad en la vena contracta", Uvc, "m/s", "√(2·ΔPc/ρ)/FL", REF8_4)
    mem.agregar("Wm", "Potencia mecánica", Wm, "W", "m·Uvc²·FL²/2", REF8_4)
    mem.agregar("ηturb", "Eficiencia acústica turbulenta", eta_t, "-", "10^An·Uvc/cL", REF8_4)
    if cavita:
        mem.agregar("ηcav", "Eficiencia acústica por cavitación", eta_c, "-", "", REF8_4)
    mem.agregar("Wa", "Potencia acústica", Wa, "W", "(ηturb + ηcav)·Wm", REF8_4)
    Lpi = mem.agregar("Lpi", "Nivel de presión sonora interno", 10 * math.log10(3.2e9 * Wa * rho * c_liq / Di_m ** 2),
                      "dB", "10·lg(3,2·10⁹·Wa·ρ·cL/Di²)", REF8_4)
    Stp = (0.036 * FL ** 2 * C * Fd ** 0.75 / (N34 * xFzp1 ** 1.5 * d_m ** 2)
           * (1 / (P1 - Psat)) ** 0.57)
    fp_t = Stp * Uvc / Dj
    mem.agregar("fp,turb", "Frecuencia de pico turbulenta", fp_t, "Hz", "", REF8_4)
    if cavita:
        fp_c = 6 * fp_t * ((1 - xF) / (1 - xFzp1)) ** 2 * (xFzp1 / xF) ** 2.5
        mem.agregar("fp,cav", "Frecuencia de pico de cavitación", fp_c, "Hz", "", REF8_4)
        t1, t2 = eta_t / (eta_t + eta_c), eta_c / (eta_t + eta_c)
    fr = c_pared / (math.pi * Di_m)
    TL_fr = -10 - 10 * math.log10(c_pared * rho_pared * tp_m / (c_aire * rho_aire * Di_m))
    dist = 10 * math.log10((Di_m + 2 * tp_m + 2) / (Di_m + 2 * tp_m))
    espectro = []
    for fi, A in zip(FRECUENCIAS, PONDERACION_A):
        F_turb = -0.8 - math.log10(0.25 * (fi / fp_t) ** 3 + (fi / fp_t) ** -1)
        if cavita:
            F_cav = 10 ** -0.9 / (0.25 * (fi / fp_c) ** 1.5 + (fi / fp_c) ** -1.5)
            Lpif = Lpi + 10 * math.log10(t1 * 10 ** F_turb + t2 * F_cav)
        else:
            Lpif = Lpi + 10 * F_turb
        TL = TL_fr - 20 * math.log10(fr / fi + (fi / fr) ** 1.5)
        Le = Lpif + TL - dist
        espectro.append((fi, Le, Le + A))
    LpAe = mem.agregar("LpAe,1m", "Nivel de ruido ponderado A a 1 m", _suma_db([e[2] for e in espectro]),
                       "dB(A)", "Σ bandas de 1/3 de octava", REF8_4)
    return {"LpAe1m": LpAe, "cavitante": cavita, "fp": fp_c if cavita else fp_t, "Lpi": Lpi,
            "espectro": espectro, "memoria": mem}


# ---------------------------------------------------------------------------
# Alertas de ruido
# ---------------------------------------------------------------------------
def evaluar_ruido(LpAe: float, gas: bool, limite: float = 85.0, nota: str = "") -> list[Alerta]:
    if LpAe < limite - 5:
        return []
    intensidad = max(0.0, min(100.0, (LpAe - (limite - 5)) / 30 * 100))
    if LpAe < limite:
        sev, titulo = Severidad.INFO, "Ruido cercano al límite"
    elif LpAe < 110:
        sev, titulo = Severidad.ADVERTENCIA if LpAe < limite + 10 else Severidad.CRITICA, "Ruido por encima del límite"
    else:
        sev, titulo = Severidad.CRITICA, "Ruido muy alto: riesgo de vibración y daño"
    if gas:
        remedios = ["Internos de bajo ruido (jaula con múltiples orificios pequeños): reducen el ruido "
                    "en 10–20 dB(A).",
                    "Internos multietapa o caída de presión repartida con un difusor aguas abajo.",
                    "Silenciador en línea (especialmente en venteos a la atmósfera).",
                    "Tubería de mayor espesor de pared o aislamiento acústico (tratamiento del camino, "
                    "no de la fuente).",
                    "Reducir la velocidad en la salida (diámetro de válvula o de tubería mayor)."]
    else:
        remedios = ["El ruido en líquidos proviene sobre todo de la cavitación: aplique las medidas "
                    "contra la cavitación (internos anticavitación o multietapa, contrapresión).",
                    "Tubería de mayor espesor o aislamiento acústico."]
    mensaje = (f"Nivel estimado LpAe,1m = {_n(LpAe, 1)} dB(A) a 1 m aguas abajo y a 1 m de la tubería "
               f"(límite usado: {_n(limite, 0)} dB(A)).")
    if LpAe >= 110:
        mensaje += " Por encima de unos 110 dB(A) la energía acústica puede dañar la tubería y accesorios."
    mensaje += nota
    return [Alerta("ruido", sev, titulo, mensaje, intensidad, None, remedios,
                   REF8_3 if gas else REF8_4)]
