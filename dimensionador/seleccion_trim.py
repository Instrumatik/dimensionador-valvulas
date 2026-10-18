"""Selección orientativa del trim a partir de los resultados del dimensionamiento.

Criterios de práctica conservadora de la industria (no son cláusulas de norma); el manual de
selección de trim los explica en detalle:

Líquidos, por caso:
  1. Flashing (P2 ≤ Pv): cuerpo angular con flujo que tiende a cerrar e internos endurecidos.
  2. Kapp ≤ 0,9·Kc del trim elegido: el trim elegido sirve.
  3. Si no, el primer trim de la escalera con Kc ≥ Kapp/0,9 y Kapp < FL².
  4. Si ninguno de etapa simple cumple: multietapa con N = max(2, N_cav) etapas, donde
     N_cav = ln((P2 − Pv)/(P1 − Pv)) / ln(1 − Kc_etapa) con igual Kapp por etapa.
  5. Energía cinética a la salida de la etapa final ≈ ΔP/N: se informa siempre; en un multietapa,
     si supera el límite de servicio severo, se indica cuántas etapas pediría ese criterio.
Gases y vapores: nivel de trim de bajo ruido requerido, Mach de salida y relación P1/P2.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .estilos import ESTILOS, KC_TIPICO

MARGEN_KC = 0.9                 # Kapp ≤ 0,9·Kc
KC_ETAPA = 0.5                  # Kapp admitido por etapa de un multietapa (conservador)
KE_SEVERO = 275.0               # kPa, cavitante, flashing, erosivo o con sólidos
DP_ENDURECIDO = 1000.0          # kPa: con cavitación o ΔP mayor, internos endurecidos
DP_ENDURECIDO_SIEMPRE = 2000.0  # kPa: internos endurecidos aunque no haya cavitación
RELACION_GAS_ETAPAS = 4.0       # P1/P2 a partir de la cual conviene reducir en etapas

# Escalera de trims de etapa simple, de menor a mayor capacidad anticavitación, y el multietapa
ESCALERA = ["globo_jaula_4v_fuera", "globo_jaula_60_orificios", "globo_jaula_120_orificios"]
MULTIETAPA = "globo_multietapa"


@dataclass
class EvaluacionCaso:
    caso: str
    datos: list                 # (etiqueta, valor, magnitud o None) para la tabla del informe
    trim: str                   # trim recomendado para este caso
    etapas: int                 # 1 = etapa simple
    grado: int                  # 0 estándar … 4 multietapa, 5 flashing (para elegir el peor caso)
    motivo: str
    avisos: list[str] = field(default_factory=list)


@dataclass
class SeleccionTrim:
    compresible: bool
    casos: list[EvaluacionCaso]
    trim: str
    etapas: int
    materiales: str
    complementos: list[str]
    pasos: list[str]            # razonamiento, en orden, para el informe

    @property
    def caso_critico(self) -> EvaluacionCaso:
        return max(self.casos, key=lambda c: (c.grado, c.etapas))


def _n(v, d=3) -> str:
    return f"{v:.{d}f}".replace(".", ",")


def _ke(dP: float, etapas: int) -> float:
    return dP / etapas


def _caso_liquido(nombre, c, s, trim_usuario: str, rotativo: bool) -> EvaluacionCaso:
    P1, P2, Pv, dP = c.P1, c.P2, c.Pv, c.P1 - c.P2
    Kapp, Kc_u, FL_u = s["Kapp"], s["Kc"], c.FL
    datos = [("ΔP", dP, "presion_dif"), ("Kapp", Kapp, None), ("Kc del trim elegido", Kc_u, None),
             ("FL² del trim elegido", FL_u ** 2, None), ("Cavitación incipiente xFzp1", s["xFzp1"], None),
             ("σ = 1/Kapp", 1 / Kapp if Kapp > 0 else float("inf"), None)]
    if P2 <= Pv:
        ev = EvaluacionCaso(nombre, datos, "Angular, flujo tiende a cerrar, internos endurecidos (flashing)", 1, 5,
                            f"P2 = {_n(P2, 1)} kPa a ≤ Pv = {_n(Pv, 1)} kPa a: hay flashing. Los trims "
                            "anticavitación no lo evitan.")
        ev.avisos.append("Limite la velocidad de la mezcla a la salida y use cuerpo de aleación resistente a la "
                         "erosión (Cr-Mo).")
        return ev
    if Kapp <= MARGEN_KC * Kc_u and Kapp < FL_u ** 2:
        ev = EvaluacionCaso(nombre, datos, ESTILOS[trim_usuario].nombre, 1, 0,
                            f"Kapp = {_n(Kapp)} ≤ 0,9·Kc = {_n(MARGEN_KC * Kc_u)}: el trim elegido no cavita.")
        if Kapp >= s["xFzp1"]:
            ev.avisos.append(f"Kapp = {_n(Kapp)} supera la cavitación incipiente xFzp1 = {_n(s['xFzp1'])}: hay "
                             "burbujas aisladas y más ruido, normalmente sin daño. Si la especificación del "
                             "cliente no admite cavitación incipiente, o el servicio es continuo con ΔP alta, "
                             "suba un escalón (jaula de orificios) y pida el xFz certificado del trim.")
    else:
        elegido = next((k for k in ESCALERA
                        if KC_TIPICO[k] >= Kapp / MARGEN_KC and Kapp < ESTILOS[k].FL ** 2), None)
        if elegido:
            ev = EvaluacionCaso(nombre, datos, ESTILOS[elegido].nombre, 1, 1 + ESCALERA.index(elegido),
                                f"Kapp = {_n(Kapp)} > 0,9·Kc del trim elegido ({_n(MARGEN_KC * Kc_u)}). "
                                f"El primer trim con Kc ≥ Kapp/0,9 = {_n(Kapp / MARGEN_KC)} y Kapp < FL² es "
                                f"este (Kc típico {_n(KC_TIPICO[elegido], 2)}, FL² "
                                f"{_n(ESTILOS[elegido].FL ** 2)}).")
        else:
            n_cav = math.ceil(math.log((P2 - Pv) / (P1 - Pv)) / math.log(1 - KC_ETAPA))
            n = max(2, n_cav)
            ev = EvaluacionCaso(nombre, datos, ESTILOS[MULTIETAPA].nombre, n, 4,
                                f"Ningún trim de etapa simple cumple Kc ≥ Kapp/0,9 = {_n(Kapp / MARGEN_KC)} con "
                                f"Kapp < FL². Etapas por cavitación: N = ln((P2 − Pv)/(P1 − Pv))/ln(1 − "
                                f"{_n(KC_ETAPA, 1)}) = {_n(math.log((P2 - Pv) / (P1 - Pv)) / math.log(1 - KC_ETAPA), 2)}"
                                f" → al menos {n} etapas.")
            if Kapp >= ESTILOS[MULTIETAPA].FL ** 2:
                ev.avisos.append(f"Kapp = {_n(Kapp)} ≥ FL² del multietapa ({_n(ESTILOS[MULTIETAPA].FL ** 2)}): "
                                 "reparta la caída de presión con una placa de restricción aguas abajo o "
                                 "válvulas en serie.")
        if rotativo:
            ev.avisos.append("El cuerpo elegido es rotativo: para un trim anticavitación cambie a cuerpo globo.")
    ke = _ke(dP, ev.etapas)
    datos.append(("Energía cinética etapa final ≈ ΔP/N", ke, "presion_dif"))
    if ev.etapas >= 2 and ke > KE_SEVERO:
        ev.avisos.append(f"Energía cinética estimada a la salida de la etapa final ≈ ΔP/N = {_n(ke, 0)} kPa. Si la "
                         f"especificación limita la energía cinética (servicio severo: {_n(KE_SEVERO, 0)} kPa en "
                         f"servicio cavitante), ese criterio pide al menos {math.ceil(dP / KE_SEVERO)} etapas: "
                         "confirme con el fabricante la velocidad a la salida del trim.")
    return ev


def _caso_gas(nombre, c, s, trim_usuario: str) -> EvaluacionCaso:
    rel = c.P1 / c.P2
    nivel = s.get("nivel_trim") or "—"
    datos = [("x = ΔP/P1", s["x"], None), ("x choked", s["xchoked"], None), ("P1/P2", rel, None),
             ("LpA a 1 m", s.get("Lp"), "dB(A)"), ("Mach salida de la válvula", s["Ma_valvula"], None)]
    grados = {"No requerido": 0, "Nivel 1": 1, "Nivel 2": 2, "Nivel 3": 3}
    if nivel in grados:
        g = grados[nivel]
        trim = (ESTILOS[trim_usuario].nombre if g == 0 else
                f"Jaula multiorificio de bajo ruido, {nivel.lower()}")
        motivo = ("El ruido con el trim estándar cumple el límite." if g == 0 else
                  f"El menor nivel de trim de bajo ruido que cumple el límite es el {nivel.lower()}.")
        ev = EvaluacionCaso(nombre, datos, trim, 1, g, motivo)
    else:
        ev = EvaluacionCaso(nombre, datos, "Multietapa de bajo ruido con difusor o silenciador", 2, 4,
                            "Ningún nivel de jaula multiorificio alcanza el límite de ruido.")
    if rel >= RELACION_GAS_ETAPAS:
        ev.avisos.append(f"P1/P2 = {_n(rel, 1)} ≥ {_n(RELACION_GAS_ETAPAS, 0)}: conviene reducir en etapas "
                         "(trim multietapa o válvula más placa de restricción).")
        ev.grado, ev.etapas = max(ev.grado, 4), max(ev.etapas, 2)
        if ev.etapas >= 2 and "Multietapa" not in ev.trim:
            ev.trim = "Multietapa de bajo ruido"
    if s["Ma_valvula"] >= 0.999:
        ev.avisos.append("Flujo sónico en la salida de la válvula: agrande el cuerpo o la salida.")
    elif s["Ma_valvula"] > 0.5:
        ev.avisos.append(f"Mach en la salida = {_n(s['Ma_valvula'], 2)} > 0,5: agrande el cuerpo o use "
                         "salida expandida.")
    elif s["Ma_valvula"] > 0.3:
        ev.avisos.append(f"Mach en la salida = {_n(s['Ma_valvula'], 2)} > 0,3: el ruido de salida puede limitar.")
    return ev


def seleccionar(res) -> SeleccionTrim:
    dim = res.dim
    rotativo = res.cuerpo.rotativa
    if dim.compresible:
        casos = [_caso_gas(c.nombre, c, s, dim.trim) for c, s in zip(dim.casos, res.salidas)]
    else:
        casos = [_caso_liquido(c.nombre, c, s, dim.trim, rotativo) for c, s in zip(dim.casos, res.salidas)]
    peor = max(casos, key=lambda c: (c.grado, c.etapas))
    etapas = max(c.etapas for c in casos)
    pasos = []
    if dim.compresible:
        pasos.append("Para gases y vapores el trim se elige por ruido (IEC 60534-8-3), por la relación de "
                     "presiones y por el Mach en la salida de la válvula.")
    else:
        pasos.append("Para líquidos se compara, en cada caso, el coeficiente de cavitación de la aplicación "
                     "Kapp = ΔP/(P1 − Pv) con el Kc y el FL² de cada trim, con un margen del 10 %.")
    for c in casos:
        pasos.append(f"Caso {c.caso}: {c.motivo}")
    pasos.append(f"El caso más exigente es «{peor.caso}»: define el trim de toda la válvula.")
    dP_max = max(c.P1 - c.P2 for c in dim.casos)
    cav = any(c.grado >= 1 for c in casos)
    flash = any(c.grado == 5 for c in casos)
    if dim.compresible:
        materiales = ("Internos de acero inoxidable endurecido (416 o 17-4PH) y asiento con estelita si la "
                      "caída de presión es alta o el gas arrastra partículas.")
    elif flash:
        materiales = ("Obturador y asiento de carburo de tungsteno o con recubrimiento de estelita; cuerpo de "
                      "Cr-Mo (p. ej. WC9) resistente a la erosión.")
    elif cav or dP_max > DP_ENDURECIDO_SIEMPRE:
        materiales = ("Obturador y asiento endurecidos: asiento con estelita 6 y obturador 17-4PH H900 o 440C "
                      "endurecido; jaula de inoxidable endurecido.")
    elif dP_max > DP_ENDURECIDO:
        materiales = "Asiento con recubrimiento de estelita recomendado por la caída de presión."
    else:
        materiales = "Internos estándar de acero inoxidable (316 o 410/416) son adecuados."
    complementos = list(dict.fromkeys(peor.avisos))
    trim = peor.trim + (f", al menos {etapas} etapas" if etapas >= 2 else "")
    return SeleccionTrim(dim.compresible, casos, trim, etapas, materiales, complementos, pasos)
