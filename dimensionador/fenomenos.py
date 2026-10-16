"""Detección de fenómenos hidrodinámicos y aerodinámicos, con intensidad y remedios.

Criterios usados:
  * Cavitación: inicio según IEC 60534-8-4 (xFz típico y corrección por
    presión xFzp1) y régimen de bloqueo según IEC 60534-2-1 (FL²). El índice
    σ de ISA-RP75.23 se informa como complemento.
  * Flashing (vaporización instantánea): P2 ≤ Pv.
  * Flujo crítico de gas: x ≥ xchoked (IEC 60534-2-1).
  * Velocidad en la salida de la válvula y en la tubería, número de Mach.
  * Velocidad erosional en tubería: API RP 14E, Ve = C/√ρm.
  * Apertura de la válvula seleccionada (sobredimensionamiento).
"""
from __future__ import annotations

import math

from .modelos import _n, Alerta, Severidad

N34 = 1.17   # IEC 60534-8-4, Kv
LB_FT3 = 16.01846337   # kg/m³ por lb/ft³
FT = 0.3048


def nivel_de(intensidad: float) -> str:
    if intensidad < 33:
        return "leve"
    if intensidad < 66:
        return "moderada"
    return "severa"


def area_mm2(d_mm: float) -> float:
    return math.pi * d_mm ** 2 / 4


# ---------------------------------------------------------------------------
# Líquidos
# ---------------------------------------------------------------------------
def xFz_tipico(Kv: float, FL: float, Fd: float) -> float:
    """Relación diferencial de inicio de cavitación típica (IEC 60534-8-4)."""
    return 0.90 / math.sqrt(1 + 3 * Fd * math.sqrt(Kv / (N34 * FL)))


def evaluar_liquido(P1, P2, Pv, FL_eff, Kv, Fd, dPchoked, xFz: float | None = None,
                    calidad_salida: float | None = None) -> tuple[list[Alerta], dict]:
    """Clasifica el régimen de cavitación / flashing.

    FL_eff: FLP/FP cuando hay reductores (FL en caso contrario).
    xFz: valor del fabricante si se conoce; si no, se estima el típico.
    calidad_salida: fracción másica de vapor a P2 (si se conoce).
    """
    alertas: list[Alerta] = []
    dP = P1 - P2
    xF = dP / (P1 - Pv)
    estimado = xFz is None
    if xFz is None:
        xFz = xFz_tipico(Kv, FL_eff, Fd)
    xFzp1 = xFz * (6e5 / (P1 * 1000)) ** 0.125   # corrección por presión
    xFzp1 = min(xFzp1, FL_eff ** 2)
    sigma = (P1 - Pv) / dP
    datos = {"xF": xF, "xFz": xFz, "xFzp1": xFzp1, "sigma": sigma,
             "sigma_i": 1 / xFzp1, "sigma_ch": 1 / FL_eff ** 2}
    ref = "IEC 60534-8-4 / IEC 60534-2-1 / ISA-RP75.23"

    if P2 <= Pv:
        if calidad_salida is not None:
            intensidad = min(100.0, max(5.0, calidad_salida * 100 * 4))  # 25 % de vapor = 100
            detalle = f"Se vaporiza aproximadamente el {_n(calidad_salida * 100, 1)} % del caudal másico."
        else:
            intensidad = min(100.0, max(5.0, (Pv - P2) / Pv * 100 * 2))
            detalle = "No se conoce la fracción de vapor a la salida."
        nivel = nivel_de(intensidad)
        alertas.append(Alerta(
            "flashing", Severidad.CRITICA, "Flashing (vaporización instantánea)",
            f"La presión de salida ({_n(P2, 1)} kPa a) es menor o igual que la presión de vapor "
            f"({_n(Pv, 1)} kPa a): parte del líquido se vaporiza y no vuelve a condensar. "
            f"{detalle} El caudal está limitado (flujo bloqueado) y el vapor a alta velocidad "
            "erosiona internos, cuerpo y tubería aguas abajo.",
            intensidad, nivel,
            remedios=[
                "Usar válvula angular con flujo que tiende a cerrar, descargando directamente "
                "a un recipiente o a una tubería de mayor diámetro.",
                "Internos y cuerpo de materiales resistentes a la erosión (p. ej. aleación "
                "cromo-molibdeno, recubrimiento de estelita o carburo de tungsteno).",
                "Aumentar el diámetro de salida para reducir la velocidad del bifásico.",
                "Si el proceso lo permite, elevar P2 o subenfriar el líquido para evitar la "
                "vaporización.",
                "Los internos anticavitación NO eliminan el flashing: la vaporización la define "
                "P2 respecto de Pv, no la geometría de la válvula.",
            ],
            referencia=ref))
        datos["regimen"] = "flashing"
        return alertas, datos

    if xF < xFzp1:
        datos["regimen"] = "sin cavitación"
        if xF > 0.8 * xFzp1:
            alertas.append(Alerta(
                "cavitacion_proxima", Severidad.INFO, "Cerca del inicio de cavitación",
                f"xF = {_n(xF, 3)} está al {_n(xF / xFzp1 * 100, 0)} % del inicio de cavitación "
                f"(xFzp1 = {_n(xFzp1, 3)}). Pequeños aumentos de ΔP o temperatura pueden iniciarla.",
                remedios=["Verifique las condiciones máximas de ΔP y temperatura."],
                referencia=ref))
        return alertas, datos

    intensidad = min(100.0, (xF - xFzp1) / max(FL_eff ** 2 - xFzp1, 1e-9) * 100)
    bloqueado = dP >= dPchoked
    if bloqueado:
        intensidad = 100.0
    nivel = "severa" if bloqueado else nivel_de(intensidad)
    # Potencial de daño: crece con la presión de colapso (P2 − Pv)
    dano_alto = (P2 - Pv) > 1000 or dP > 2000
    remedios = {
        "leve": [
            "Normalmente tolerable en servicio intermitente; especifique internos endurecidos "
            "(estelita) para mayor vida útil.",
            "Verifique el ruido hidrodinámico (IEC 60534-8-4).",
        ],
        "moderada": [
            "Internos anticavitación (jaula de múltiples orificios pequeños).",
            "Elegir un estilo con FL más alto (globo en lugar de mariposa o bola).",
            "Aumentar la contrapresión: placa de orificio de restricción aguas abajo.",
            "Materiales endurecidos en asiento y obturador.",
        ],
        "severa": [
            "Internos multietapa que dividen la caída de presión en varias etapas.",
            "Repartir la caída de presión entre dos válvulas en serie o válvula + orificio.",
            "Ubicar la válvula donde la presión sea mayor (cota más baja, más cerca de la bomba).",
            "Bajar la temperatura del líquido, si el proceso lo permite, para reducir Pv.",
            "Válvula angular con descarga a tubería de mayor diámetro para alejar el colapso "
            "de burbujas de las paredes.",
        ],
    }[nivel]
    titulo = "Cavitación con flujo bloqueado" if bloqueado else f"Cavitación {nivel}"
    msg = (f"La presión en la vena contracta cae por debajo de la presión de vapor y las "
           f"burbujas colapsan aguas abajo (P2 > Pv). xF = {_n(xF, 3)}, inicio xFzp1 = {_n(xFzp1, 3)}"
           f"{' (estimado típico)' if estimado else ''}, bloqueo FL² = {_n(FL_eff ** 2, 3)}. "
           f"σ = {_n(sigma, 2)}.")
    if bloqueado:
        msg += " El caudal ya no aumenta al bajar P2 (flujo crítico por cavitación plena)."
    if dano_alto:
        msg += " La energía de colapso es alta: alto riesgo de daño por erosión."
    alertas.append(Alerta("cavitacion", Severidad.CRITICA if nivel != "leve" else Severidad.ADVERTENCIA,
                          titulo, msg, intensidad, nivel, remedios, ref))
    datos["regimen"] = "cavitación con bloqueo" if bloqueado else "cavitación"
    return alertas, datos


def evaluar_velocidad_liquido(Q_m3h: float, d_mm: float, D2_mm: float | None,
                              rho_salida: float, bifasico: bool) -> tuple[list[Alerta], dict]:
    alertas = []
    v_valv = Q_m3h / 3600 / (area_mm2(d_mm) * 1e-6)
    datos = {"v_salida_valvula": v_valv}
    if not bifasico:
        datos["v_tuberia_salida"] = Q_m3h / 3600 / (area_mm2(D2_mm or d_mm) * 1e-6)
    limite = 9.0 if not bifasico else 23.0
    if not bifasico and v_valv > limite:
        intensidad = min(100.0, (v_valv / limite - 1) * 100)
        alertas.append(Alerta(
            "velocidad_liquido", Severidad.ADVERTENCIA, "Velocidad de líquido alta en la válvula",
            f"Velocidad en la conexión de salida de la válvula: {_n(v_valv, 1)} m/s (recomendado ≤ "
            f"{_n(limite, 0)} m/s para líquidos limpios). Favorece erosión, vibración y golpe de ariete.",
            intensidad, nivel_de(intensidad),
            ["Seleccionar un diámetro de válvula mayor.",
             "Si el líquido arrastra sólidos, reducir aún más la velocidad (≤ 4,5 m/s)."],
            "Práctica de la industria (ISA / guías de usuarios)"))
    return alertas, datos


# ---------------------------------------------------------------------------
# Gases
# ---------------------------------------------------------------------------
def evaluar_gas(P1, P2, T1, M, gamma, Z, W_kgh, d_mm, D2_mm, x, xchoked) -> tuple[list[Alerta], dict]:
    alertas = []
    R = 8.314462618
    rho2 = P2 * M / (Z * R * T1)              # T2 ≈ T1 (estrangulamiento casi isoentálpico)
    c2 = math.sqrt(gamma * Z * R * 1000 * T1 / M)
    v_valv = W_kgh / 3600 / rho2 / (area_mm2(d_mm) * 1e-6)
    Ma_valv = v_valv / c2
    datos = {"rho2": rho2, "c2": c2, "v_salida_valvula": v_valv, "Mach_salida_valvula": Ma_valv}
    if D2_mm:
        v_tub = W_kgh / 3600 / rho2 / (area_mm2(D2_mm) * 1e-6)
        datos["v_tuberia_salida"] = v_tub
        datos["Mach_tuberia_salida"] = v_tub / c2
    if x >= xchoked:
        alertas.append(Alerta(
            "gas_bloqueado", Severidad.ADVERTENCIA, "Flujo crítico (sónico) de gas",
            f"x = {_n(x, 3)} ≥ xchoked = {_n(xchoked, 3)}: en la vena contracta se alcanza la velocidad "
            "del sonido y el caudal ya no aumenta al bajar P2. Es un régimen de alto ruido "
            "aerodinámico.",
            min(100.0, x / xchoked * 50), None,
            ["Verificar el nivel de ruido (IEC 60534-8-3).",
             "Para ruido elevado: internos de baja emisión (jaula multiorificio), difusor o "
             "silenciador aguas abajo, o caída de presión en etapas."],
            "IEC 60534-2-1 cláusula 6"))
    if Ma_valv > 0.3:
        if Ma_valv > 1.0:
            sev, lim = Severidad.CRITICA, "supera la velocidad del sonido"
        elif Ma_valv > 0.5:
            sev, lim = Severidad.CRITICA, "supera 0,5"
        else:
            sev, lim = Severidad.ADVERTENCIA, "supera 0,3"
        intensidad = min(100.0, (Ma_valv - 0.3) / 0.7 * 100)
        alertas.append(Alerta(
            "mach_salida", sev, "Velocidad alta de gas a la salida de la válvula",
            f"Número de Mach en la salida de la válvula: {_n(Ma_valv, 2)} ({lim}). Por encima de "
            "0,3 el ruido generado en la salida crece rápidamente; por encima de 0,5 hay riesgo "
            "de vibración y daño.",
            intensidad, nivel_de(intensidad),
            ["Seleccionar una válvula de mayor diámetro o con salida expandida.",
             "Aumentar el diámetro de la tubería aguas abajo.",
             "Reducir la caída de presión en la válvula repartiéndola en etapas."],
            "IEC 60534-8-3 (límites de validez de Mach)"))
    return alertas, datos


# ---------------------------------------------------------------------------
# API RP 14E: velocidad erosional
# ---------------------------------------------------------------------------
def velocidad_erosional_api14e(rho_kgm3: float, C: float = 100.0) -> float:
    """Ve = C/√ρm, con Ve en ft/s y ρm en lb/ft³. Devuelve m/s."""
    return C / math.sqrt(rho_kgm3 / LB_FT3) * FT


def evaluar_erosional(v_ms: float, rho_kgm3: float, donde: str, C: float = 100.0) -> list[Alerta]:
    ve = velocidad_erosional_api14e(rho_kgm3, C)
    if v_ms <= ve:
        return []
    intensidad = min(100.0, (v_ms / ve - 1) * 100)
    return [Alerta(
        "erosional_api14e", Severidad.CRITICA, "Velocidad erosional superada (API RP 14E)",
        f"La velocidad en {donde} ({_n(v_ms, 1)} m/s) supera la velocidad erosional "
        f"Ve = C/√ρm = {_n(ve, 1)} m/s (C = {_n(C)}, ρm = {_n(rho_kgm3, 1)} kg/m³).",
        intensidad, nivel_de(intensidad),
        ["Aumentar el diámetro de la tubería.",
         "Si el fluido está libre de sólidos y la corrosión está controlada, API RP 14E admite "
         "C de hasta 150–200 justificándolo.",
         "Materiales resistentes a la erosión en codos y accesorios aguas abajo."],
        "API RP 14E sección 2.5")]


# ---------------------------------------------------------------------------
# Selección: apertura
# ---------------------------------------------------------------------------
def evaluar_apertura(h: float, caracteristica: str, caso: str = "máximo") -> list[Alerta]:
    alertas = []
    pct = h * 100
    if h > 1.0:
        alertas.append(Alerta(
            "subdimensionada", Severidad.CRITICA, "Válvula subdimensionada",
            f"Con el caudal {caso} la válvula necesitaría abrir {_n(pct, 0)} %: no alcanza la "
            "capacidad requerida.",
            100.0, "severa", ["Seleccionar un diámetro mayor o un estilo de mayor capacidad."]))
    elif h > 0.9:
        alertas.append(Alerta(
            "apertura_alta", Severidad.ADVERTENCIA, "Apertura muy alta",
            f"Apertura requerida {_n(pct, 0)} %: queda poco margen de control.",
            remedios=["Considerar el diámetro inmediato superior."]))
    elif h < 0.1:
        alertas.append(Alerta(
            "apertura_baja", Severidad.ADVERTENCIA, "Válvula sobredimensionada",
            f"Apertura requerida {_n(pct, 0)} %: operar cerca del asiento empeora el control, "
            "acelera el desgaste del asiento y aumenta la sensibilidad al rozamiento.",
            remedios=["Seleccionar un diámetro menor o internos de capacidad reducida."]))
    return alertas
