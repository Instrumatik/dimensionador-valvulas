"""Biblioteca de materiales para válvulas de control.

Cada material lleva los datos que usa el motor de selección
(``seleccion_materiales.py``) y la ficha que se muestra en la biblioteca:
designaciones UNS / ASTM, grupo de ASME B16.34, límites de temperatura,
composición nominal, propiedades mecánicas típicas, dureza, PREN, índice
de costo, componentes en los que se usa, situación frente a NACE
MR0175 / ISO 15156 y NACE MR0103 / ISO 17945, comportamiento al galling y
resistencia a la cavitación y a la erosión.

Los valores son típicos u orientativos (práctica de la industria de
válvulas, fichas de los productores de aleaciones y normas citadas en
``fuentes``). La selección final requiere el certificado del material
(MTR), la edición vigente de cada norma y la confirmación del fabricante.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

# Componentes de la válvula (clave interna -> nombre)
COMPONENTES = {
    "cuerpo": "Cuerpo",
    "bonete": "Bonete",
    "asiento": "Asiento",
    "jaula": "Jaula caracterizada",
    "guia": "Guía",
    "obturador": "Obturador",
    "vastago": "Vástago",
}
# Nombres equivalentes en válvulas rotativas (bola, mariposa, obturador excéntrico)
COMPONENTES_ROTATIVA = {
    "cuerpo": "Cuerpo",
    "bonete": "Tapa / brida de eje",
    "asiento": "Anillo de asiento",
    "jaula": "Atenuador / jaula (si lleva)",
    "guia": "Cojinetes del eje",
    "obturador": "Bola / disco / obturador",
    "vastago": "Eje",
}

# Índice de costo: cuerpo de acero al carbono fundido WCB = 1; internos: 316 = 1.
# Es relativo y orientativo (material más mecanizado típico), sirve para ordenar opciones.


@dataclass(frozen=True)
class Nace:
    """Situación del material frente a una norma de servicio agrio."""
    estado: str                       # "aceptable", "condicional", "no", "sin_datos"
    dureza_max_HRC: float | None = None
    pH2S_max_kPa: float | None = None   # límite ambiental (None = sin límite propio)
    T_max_C: float | None = None
    pH_min: float | None = None
    azufre: bool = True               # admite azufre elemental
    nota: str = ""


@dataclass(frozen=True)
class Material:
    clave: str
    nombre: str
    familia: str                      # familia metalúrgica (texto)
    quimica: tuple[str, ...]          # clases de comportamiento químico (quimica.py); varias si hay recargue
    componentes: frozenset
    uns: str = ""
    astm: str = ""                    # especificación(es) ASTM / AWS
    forma: str = ""                   # fundición, forja, barra, recargue, inserto...
    equivalente: str = ""             # equivalente fundido/forjado
    grupo: str | None = None          # grupo de ASME B16.34 (solo cuerpos y bonetes)
    grupo_equivalente: bool = False   # True: fundición no listada; se usa el grupo del forjado equivalente
    T_min_C: float = -29
    T_max_C: float = 538
    composicion: str = ""
    Rm_MPa: float | None = None       # resistencia a la tracción
    Rp_MPa: float | None = None       # límite de fluencia 0,2 %
    HB: float | None = None           # dureza típica Brinell
    HRC: float | None = None          # dureza típica Rockwell C (superficie de trabajo)
    pren: float | None = None
    costo: float = 1.0
    galling: str = "aus"              # grupo tribológico (ver seleccion_materiales.riesgo_galling)
    cavitacion: int = 2               # resistencia relativa 0–10
    erosion: int = 2                  # resistencia relativa 0–10
    iso15156: Nace = Nace("sin_datos")
    iso17945: Nace = Nace("sin_datos")
    blando: bool = False              # inserto no metálico (asiento blando)
    notas: tuple[str, ...] = ()
    fuentes: tuple[str, ...] = ()

    @property
    def dureza_txt(self) -> str:
        if self.HRC is not None and self.HRC >= 20:
            hb = f" (≈ {hrc_a_hb(self.HRC):.0f} HB)" if self.HRC <= 58 else ""
            return f"{self.HRC:.0f} HRC{hb}"
        if self.HB is not None:
            return f"{self.HB:.0f} HB"
        return "—"

    @property
    def HRC_efectiva(self) -> float:
        """Dureza de la superficie de trabajo en HRC (las blandas se convierten desde HB)."""
        if self.HRC is not None:
            return self.HRC
        if self.HB is not None:
            return hb_a_hrc(self.HB)
        return 0.0


# ---------------------------------------------------------------------------
# Conversión aproximada de durezas (ASTM E140, aceros no austeníticos). Es
# orientativa: ISO 15156 no admite convertir durezas como criterio de aceptación.
# ---------------------------------------------------------------------------
_HRC_HB = [(-10, 150), (0, 180), (10, 200), (20, 226), (22, 237), (25, 253), (28, 271), (30, 286),
           (33, 311), (35, 327), (38, 353), (40, 371), (43, 401), (45, 421), (48, 451), (50, 475),
           (52, 500), (55, 545), (58, 595), (60, 620), (65, 700), (70, 780)]


def hrc_a_hb(hrc: float) -> float:
    for (c0, b0), (c1, b1) in zip(_HRC_HB, _HRC_HB[1:]):
        if hrc <= c1:
            return b0 + (b1 - b0) * (hrc - c0) / (c1 - c0)
    return _HRC_HB[-1][1]


def hb_a_hrc(hb: float) -> float:
    for (c0, b0), (c1, b1) in zip(_HRC_HB, _HRC_HB[1:]):
        if hb <= b1:
            return c0 + (c1 - c0) * (hb - b0) / (b1 - b0)
    return _HRC_HB[-1][0]


C = frozenset  # abreviatura
CUERPO = C({"cuerpo", "bonete"})
TRIM = C({"asiento", "jaula", "guia", "obturador"})

_ISO = "ISO 15156-2/-3 (NACE MR0175)"
_REF = "ISO 17945 (NACE MR0103)"
F_PRACTICA = "Práctica de la industria de válvulas de control (selección de materiales de internos)"
F_B1634 = "ASME B16.34-2017, Tabla 1 y Tabla 2"
F_15156 = "ISO 15156-2:2020 / ISO 15156-3:2020"
F_17945 = "ISO 17945:2015 / NACE MR0103"
F_ASTM = "ASTM (especificación del grado)"

# Durezas NACE habituales
CS_15156 = Nace("aceptable", 22, nota="Acero al carbono / baja aleación: ≤ 22 HRC (≈ 237 HB) en metal base; "
                "soldaduras y ZAC ≤ 250 HV10. Para castings, sin requisitos de HIC (HIC aplica a laminados).")
CS_17945 = Nace("aceptable", None, nota="Aceros P-No. 1 (WCB, WCC, LCC, A105, LF2) aceptables sin límite de "
                "dureza del metal base; soldaduras ≤ 200 HBW.")
AUS_15156 = Nace("condicional", 22, 100, 60, nota="Austeníticos serie 300 (solubilizados, ≤ 22 HRC): sin "
                 "cloruros especificados, hasta 60 °C y pH₂S ≤ 100 kPa en uso general (ISO 15156-3, anexo A). Sin "
                 "azufre elemental.", azufre=False)
AUS_17945 = Nace("aceptable", 22, nota="Austeníticos serie 300 solubilizados, ≤ 22 HRC.")


def _m(*a, **k) -> Material:
    return Material(*a, **k)


MATERIALES: dict[str, Material] = {m.clave: m for m in [
    # ------------------------------------------------------------------ cuerpos (fundición)
    _m("WCB", "ASTM A216 WCB — acero al carbono fundido", "Acero al carbono", ("cs",), CUERPO,
       uns="J03002", astm="ASTM A216 Gr. WCB", forma="Fundición", equivalente="A105 (forja)", grupo="1.1",
       T_min_C=-29, T_max_C=538, composicion="C ≤ 0,30 · Mn ≤ 1,00 · Si ≤ 0,60",
       Rm_MPa=485, Rp_MPa=250, HB=150, costo=1.0, galling="cs", cavitacion=1, erosion=2,
       iso15156=CS_15156, iso17945=CS_17945,
       notas=("Material de cuerpo más económico; estándar para agua, vapor, aire, hidrocarburos no "
              "corrosivos.", "Uso prolongado por encima de 425 °C: grafitización (pérdida de resistencia).",
              "Por debajo de −29 °C requiere acero con ensayo de impacto (LCC / LCB).",
              "Sin protección frente a cloruros, ácidos ni CO₂ húmedo: requiere sobreespesor de corrosión."),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("WCC", "ASTM A216 WCC — acero al carbono-manganeso fundido", "Acero al carbono", ("cs",), CUERPO,
       uns="J02503", astm="ASTM A216 Gr. WCC", forma="Fundición", equivalente="A105 / A350 LF2", grupo="1.2",
       T_min_C=-29, T_max_C=538, composicion="C ≤ 0,25 · Mn ≤ 1,20 · Si ≤ 0,60",
       Rm_MPa=485, Rp_MPa=275, HB=160, costo=1.05, galling="cs", cavitacion=1, erosion=2,
       iso15156=CS_15156, iso17945=CS_17945,
       notas=("Algo más resistente que WCB (rating mayor, grupo 1.2).",
              "Uso prolongado por encima de 425 °C: grafitización."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("LCC", "ASTM A352 LCC — acero al carbono para baja temperatura", "Acero baja temperatura", ("cs",),
       CUERPO, uns="J02505", astm="ASTM A352 Gr. LCC", forma="Fundición", equivalente="A350 LF2 Cl.1 (forja)",
       grupo="1.2", T_min_C=-46, T_max_C=345, composicion="C ≤ 0,25 · Mn ≤ 1,20 · ensayo de impacto a −46 °C",
       Rm_MPa=485, Rp_MPa=275, HB=160, costo=1.3, galling="cs", cavitacion=1, erosion=2,
       iso15156=CS_15156, iso17945=CS_17945,
       notas=("Para servicio entre −46 °C y −29 °C (despresurización de gas, GLP, intemperie fría).",
              "ASME B16.34: no usar por encima de 345 °C."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("LC3", "ASTM A352 LC3 — acero 3,5 % Ni para baja temperatura", "Acero baja temperatura", ("cs",),
       CUERPO, uns="J31550", astm="ASTM A352 Gr. LC3", forma="Fundición", equivalente="A350 LF3 (forja)",
       grupo="1.2", T_min_C=-101, T_max_C=345, composicion="C ≤ 0,15 · Ni 3,0–4,0 · impacto a −101 °C",
       Rm_MPa=485, Rp_MPa=275, HB=170, costo=2.0, galling="cs", cavitacion=1, erosion=2,
       iso15156=Nace("condicional", 22, nota="Aceros con Ni > 1 % no son aceptables en ISO 15156-2 salvo "
                     "calificación específica."), iso17945=Nace("condicional", 22, nota="Ni > 1 %: requiere "
                                                                 "calificación."),
       notas=("Para −101 °C a −46 °C (etileno, CO₂ líquido, etano).",), fuentes=(F_B1634, F_ASTM)),
    _m("WC6", "ASTM A217 WC6 — acero 1¼Cr-½Mo fundido", "Acero Cr-Mo", ("crmo",), CUERPO,
       uns="J12072", astm="ASTM A217 Gr. WC6", forma="Fundición", equivalente="A182 F11 Cl.2 (forja)",
       grupo="1.9", T_min_C=-29, T_max_C=595, composicion="C ≤ 0,20 · Cr 1,0–1,5 · Mo 0,45–0,65",
       Rm_MPa=485, Rp_MPa=275, HB=170, costo=1.8, galling="cs", cavitacion=2, erosion=3,
       iso15156=CS_15156, iso17945=Nace("aceptable", 22, nota="Cr-Mo: ≤ 225 HBW (P-No. 4)."),
       notas=("Vapor y servicios de alta temperatura hasta 595 °C (creep).",
              "Válvulas bridadas: rating hasta 538 °C.", "Normalizado y revenido; requiere PWHT en soldaduras."),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("WC9", "ASTM A217 WC9 — acero 2¼Cr-1Mo fundido", "Acero Cr-Mo", ("crmo",), CUERPO,
       uns="J21890", astm="ASTM A217 Gr. WC9", forma="Fundición", equivalente="A182 F22 Cl.3 (forja)",
       grupo="1.10", T_min_C=-29, T_max_C=595, composicion="C ≤ 0,18 · Cr 2,0–2,75 · Mo 0,9–1,2",
       Rm_MPa=485, Rp_MPa=275, HB=180, costo=2.0, galling="cs", cavitacion=3, erosion=4,
       iso15156=CS_15156, iso17945=Nace("aceptable", 22, nota="Cr-Mo: ≤ 225 HBW (P-No. 5A)."),
       notas=("Estándar para vapor de alta temperatura y para servicios con flashing / erosión-corrosión "
              "(el cromo mejora la resistencia a la erosión respecto del acero al carbono).",
              "Hasta 595 °C; bridadas hasta 538 °C."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("C5", "ASTM A217 C5 — acero 5Cr-½Mo fundido", "Acero Cr-Mo", ("crmo9",), CUERPO,
       uns="J42045", astm="ASTM A217 Gr. C5", forma="Fundición", equivalente="A182 F5a (forja)", grupo="1.13",
       T_min_C=-29, T_max_C=649, composicion="C ≤ 0,20 · Cr 4,0–6,5 · Mo 0,45–0,65",
       Rm_MPa=620, Rp_MPa=415, HB=200, costo=2.6, galling="cs", cavitacion=3, erosion=5,
       iso15156=CS_15156, iso17945=Nace("aceptable", 22, nota="≤ 235 HBW (P-No. 5B)."),
       notas=("Alta temperatura con azufre (sulfidación en refinería) y flashing severo.",),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("C12A", "ASTM A217 C12A — acero 9Cr-1Mo-V fundido", "Acero Cr-Mo", ("crmo9",), CUERPO,
       uns="J84090", astm="ASTM A217 Gr. C12A", forma="Fundición", equivalente="A182 F91 (forja)",
       grupo="1.15", T_min_C=-29, T_max_C=649, composicion="C 0,08–0,12 · Cr 8–9,5 · Mo 0,85–1,05 · V · Nb",
       Rm_MPa=585, Rp_MPa=415, HB=210, costo=3.2, galling="cs", cavitacion=4, erosion=6,
       iso15156=Nace("condicional", 22, nota="Requiere calificación."), iso17945=Nace("condicional", 22),
       notas=("Vapor supercrítico y alta temperatura en centrales (hasta 649 °C).",
              "Tratamiento térmico crítico; soldadura con procedimiento calificado."),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CF8", "ASTM A351 CF8 — inoxidable 304 fundido", "Inoxidable austenítico", ("ss304",), CUERPO,
       uns="J92600", astm="ASTM A351 Gr. CF8", forma="Fundición", equivalente="A182 F304 (forja)", grupo="2.1",
       T_min_C=-254, T_max_C=816, composicion="C ≤ 0,08 · Cr 18–21 · Ni 8–11", Rm_MPa=485, Rp_MPa=205,
       HB=150, pren=19, costo=2.6, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Ácido nítrico y oxidantes, criogenia.", "Por encima de 538 °C solo con C ≥ 0,04 %.",
              "Sensible a picaduras y a corrosión bajo tensión por cloruros (SCC) por encima de ~60 °C."),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CF3", "ASTM A351 CF3 — inoxidable 304L fundido", "Inoxidable austenítico", ("ss304",), CUERPO,
       uns="J92500", astm="ASTM A351 Gr. CF3", forma="Fundición", equivalente="A182 F304L (forja)",
       grupo="2.1", T_min_C=-254, T_max_C=425, composicion="C ≤ 0,03 · Cr 17–21 · Ni 8–12",
       Rm_MPa=485, Rp_MPa=205, HB=150, pren=19, costo=2.8, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Bajo carbono: evita la sensibilización en soldadura; preferido en ácido nítrico.",
              "ASME B16.34: no usar por encima de 425 °C."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CF8M", "ASTM A351 CF8M — inoxidable 316 fundido", "Inoxidable austenítico", ("ss316",), CUERPO,
       uns="J92900", astm="ASTM A351 Gr. CF8M", forma="Fundición", equivalente="A182 F316 (forja)",
       grupo="2.2", T_min_C=-254, T_max_C=816, composicion="C ≤ 0,08 · Cr 18–21 · Ni 9–12 · Mo 2–3",
       Rm_MPa=485, Rp_MPa=205, HB=160, pren=24, costo=3.0, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Estándar en servicios corrosivos moderados, criogenia y alta temperatura.",
              "Por encima de 538 °C solo con C ≥ 0,04 %; bridadas hasta 538 °C.",
              "Cloruros: picaduras y SCC por encima de ~60 °C."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CF3M", "ASTM A351 CF3M — inoxidable 316L fundido", "Inoxidable austenítico", ("ss316",), CUERPO,
       uns="J92800", astm="ASTM A351 Gr. CF3M", forma="Fundición", equivalente="A182 F316L (forja)",
       grupo="2.2", T_min_C=-254, T_max_C=454, composicion="C ≤ 0,03 · Cr 17–21 · Ni 9–13 · Mo 2–3",
       Rm_MPa=485, Rp_MPa=205, HB=160, pren=24, costo=3.2, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Bajo carbono para soldadura sin sensibilización.", "Uso hasta ~455 °C."),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CG8M", "ASTM A351 CG8M — inoxidable 317 fundido", "Inoxidable austenítico", ("ss317",), CUERPO,
       uns="J93000", astm="ASTM A351 Gr. CG8M", forma="Fundición", equivalente="A182 F317 (forja)",
       grupo="2.2", T_min_C=-254, T_max_C=538, composicion="C ≤ 0,08 · Cr 18–21 · Ni 9–13 · Mo 3–4",
       Rm_MPa=520, Rp_MPa=240, HB=170, pren=29, costo=3.6, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Más molibdeno que el 316: mejor frente a ácido sulfúrico diluido, sulfuroso y picaduras.",
              "No usar por encima de 538 °C."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CK3MCuN", "ASTM A351 CK3MCuN — superaustenítico 6Mo fundido (254 SMO)", "Superaustenítico",
       ("superaus",), CUERPO, uns="J93254", astm="ASTM A351 Gr. CK3MCuN", forma="Fundición",
       equivalente="A182 F44 / S31254 (forja)", grupo="2.8", T_min_C=-196, T_max_C=400,
       composicion="Cr 19,5–20,5 · Ni 17,5–19,5 · Mo 6–7 · N 0,18–0,24 · Cu 0,5–1",
       Rm_MPa=550, Rp_MPa=260, HB=180, pren=43, costo=6.5, galling="aus", cavitacion=3, erosion=4,
       iso15156=Nace("aceptable", 35, nota="Superausteníticos (PREN ≥ 40) con límites ambientales amplios "
                     "(ISO 15156-3, anexo A); ≤ 35 HRC."), iso17945=Nace("aceptable", 35),
       notas=("Agua de mar, salmueras y cloruros calientes donde el 316 sufre picaduras.",),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CD3MN", "ASTM A995 CD3MN (4A) — dúplex 2205 fundido", "Inoxidable dúplex (Duplex SS)", ("duplex",), CUERPO,
       uns="J92205", astm="ASTM A995 Gr. 4A (CD3MN)", forma="Fundición", equivalente="A182 F51 / F60 (forja)",
       grupo="2.8", T_min_C=-46, T_max_C=315, composicion="Cr 21–23,5 · Ni 4,5–6,5 · Mo 2,5–3,5 · N 0,1–0,3",
       Rm_MPa=620, Rp_MPa=415, HB=240, pren=35, costo=4.5, galling="dup", cavitacion=4, erosion=5,
       iso15156=Nace("condicional", 28, 10, 232, nota="Dúplex PREN 30–40: pH₂S ≤ 10 kPa, ≤ 232 °C, ≤ 28 HRC "
                     "(ISO 15156-3, anexo A).", azufre=False),
       iso17945=Nace("aceptable", 28, nota="Dúplex solubilizado, ≤ 28 HRC; ferrita 35–65 %."),
       notas=("Doble de resistencia mecánica que el 316 y mucho mejor frente a SCC por cloruros.",
              "Límite práctico 315 °C (fragilización a 475 °C); impacto limitado por debajo de −46 °C."),
       fuentes=(F_B1634, F_PRACTICA, F_15156)),
    _m("CD3MWCuN", "ASTM A995 CD3MWCuN (6A) — superdúplex fundido (S32760)", "Inoxidable superdúplex (Super Duplex SS)",
       ("sduplex",), CUERPO, uns="J93380", astm="ASTM A995 Gr. 6A (CD3MWCuN)", forma="Fundición",
       equivalente="A182 F55 / S32760 (forja)", grupo="2.8", T_min_C=-46, T_max_C=315,
       composicion="Cr 24–26 · Ni 6,5–8,5 · Mo 3–4 · W 0,5–1 · Cu 0,5–1 · N 0,2–0,3",
       Rm_MPa=690, Rp_MPa=450, HB=260, pren=41, costo=6.0, galling="dup", cavitacion=5, erosion=6,
       iso15156=Nace("condicional", 32, 20, 232, nota="Superdúplex PREN > 40: pH₂S ≤ 20 kPa, ≤ 232 °C "
                     "(ISO 15156-3, anexo A).", azufre=False), iso17945=Nace("aceptable", 32),
       notas=("Agua de mar y producción con cloruros altos; muy buena resistencia a erosión-corrosión.",
              "Límite práctico 315 °C."), fuentes=(F_B1634, F_PRACTICA, F_15156)),
    _m("CN7M", "ASTM A351 CN7M — Aleación 20 fundida", "Aleación Ni-Fe-Cr", ("a20",), CUERPO,
       uns="J95150", astm="ASTM A351 Gr. CN7M", forma="Fundición", equivalente="B462 N08020 (forja)",
       grupo="3.17", T_min_C=-29, T_max_C=316, composicion="Ni 27,5–30,5 · Cr 19–22 · Mo 2–3 · Cu 3–4",
       Rm_MPa=425, Rp_MPa=170, HB=150, pren=28, costo=7.0, galling="ni", cavitacion=2, erosion=3,
       iso15156=Nace("aceptable", 35, nota="Aleaciones Ni-Fe-Cr solubilizadas (ISO 15156-3, anexo A)."),
       iso17945=Nace("aceptable", 35),
       notas=("Ácido sulfúrico (todas las concentraciones a temperaturas moderadas), fosfórico.",
              "ASME B16.34: rating hasta 325 °C."), fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CU5MCuC", "ASTM A494 CU5MCuC — Aleación 825 fundida", "Aleación Ni-Fe-Cr", ("in825",), CUERPO,
       uns="N08826", astm="ASTM A494 Gr. CU5MCuC", forma="Fundición", equivalente="B564 N08825 (forja)",
       grupo="3.8", grupo_equivalente=True, T_min_C=-196, T_max_C=538,
       composicion="Ni 38–44 · Cr 19,5–23,5 · Mo 2,5–3,5 · Cu 1,5–3,5 · Nb",
       Rm_MPa=520, Rp_MPa=240, HB=170, pren=31, costo=8.0, galling="ni", cavitacion=3, erosion=3,
       iso15156=Nace("aceptable", 35, nota="Aleación tipo 4c (ISO 15156-3, anexo A)."), iso17945=Nace("aceptable", 35),
       notas=("Ácidos sulfúrico y fosfórico, SCC por cloruros.",), fuentes=(F_PRACTICA, F_ASTM)),
    _m("M35-1", "ASTM A494 M35-1 — Monel 400 fundido", "Aleación Ni-Cu", ("monel",), CUERPO,
       uns="N24135", astm="ASTM A494 Gr. M35-1", forma="Fundición", equivalente="B564 N04400 (forja)",
       grupo="3.4", T_min_C=-198, T_max_C=475, composicion="Ni ≥ 63 · Cu 26–33 · Fe ≤ 2,5",
       Rm_MPa=450, Rp_MPa=170, HB=140, costo=10.0, galling="ni", cavitacion=3, erosion=3,
       iso15156=Nace("aceptable", 35, nota="Ni-Cu (ISO 15156-3, anexo A)."), iso17945=Nace("aceptable", 35),
       notas=("Ácido fluorhídrico, agua de mar, cloro seco, álcalis.",
              "No apto para oxidantes (HNO₃, FeCl₃, hipoclorito) ni amoníaco húmedo."),
       fuentes=(F_B1634, F_PRACTICA, F_ASTM)),
    _m("CY40", "ASTM A494 CY40 — Inconel 600 fundido", "Aleación Ni-Cr", ("ni600",), CUERPO,
       uns="N06040", astm="ASTM A494 Gr. CY40", forma="Fundición", equivalente="B564 N06600 (forja)",
       grupo="3.5", grupo_equivalente=True, T_min_C=-198, T_max_C=649,
       composicion="Ni ≥ 72 · Cr 14–17 · Fe ≤ 11", Rm_MPa=485, Rp_MPa=195, HB=170, costo=11.0,
       galling="ni", cavitacion=3, erosion=3,
       iso15156=Nace("aceptable", 35), iso17945=Nace("aceptable", 35),
       notas=("Álcalis cáusticos concentrados y calientes, alta temperatura oxidante.",),
       fuentes=(F_PRACTICA, F_ASTM)),
    _m("CW6MC", "ASTM A494 CW6MC — Inconel 625 fundido", "Aleación Ni-Cr-Mo", ("ni625",), CUERPO,
       uns="N26625", astm="ASTM A494 Gr. CW6MC", forma="Fundición", equivalente="B564 N06625 (forja)",
       grupo="3.8", grupo_equivalente=True, T_min_C=-198, T_max_C=645,
       composicion="Ni ≥ 58 · Cr 20–23 · Mo 8–10 · Nb 3,2–4,2", Rm_MPa=485, Rp_MPa=275, HB=190, pren=51,
       costo=13.0, galling="ni", cavitacion=4, erosion=4,
       iso15156=Nace("aceptable", 35, nota="Tipo 4d (ISO 15156-3, anexo A): muy amplio en H₂S y cloruros."),
       iso17945=Nace("aceptable", 35),
       notas=("Agua de mar caliente, cloruros con H₂S, ácidos mixtos.",), fuentes=(F_PRACTICA, F_ASTM)),
    _m("CW2M", "ASTM A494 CW2M — Hastelloy C fundido (C-276)", "Aleación Ni-Cr-Mo", ("ni_c",), CUERPO,
       uns="N26455", astm="ASTM A494 Gr. CW2M", forma="Fundición", equivalente="B564 N10276 (forja)",
       grupo="3.8", grupo_equivalente=True, T_min_C=-198, T_max_C=538,
       composicion="Ni bal. · Cr 15–17,5 · Mo 15–17,5 · W ≤ 1", Rm_MPa=495, Rp_MPa=275, HB=200, pren=68,
       costo=14.0, galling="ni", cavitacion=4, erosion=4,
       iso15156=Nace("aceptable", 35, nota="Tipo 4e (ISO 15156-3, anexo A): sin límites de pH₂S ni azufre."),
       iso17945=Nace("aceptable", 35),
       notas=("Ácido clorhídrico diluido, cloruros oxidantes (FeCl₃, cloro húmedo), mezclas ácidas.",),
       fuentes=(F_PRACTICA, F_ASTM)),
    _m("CX2MW", "ASTM A494 CX2MW — Hastelloy C-22 fundido", "Aleación Ni-Cr-Mo", ("ni_c",), CUERPO,
       uns="N26022", astm="ASTM A494 Gr. CX2MW", forma="Fundición", equivalente="B564 N06022 (forja)",
       grupo="3.8", grupo_equivalente=True, T_min_C=-198, T_max_C=538,
       composicion="Ni bal. · Cr 20–22,5 · Mo 12,5–14,5 · W 2,5–3,5", Rm_MPa=550, Rp_MPa=280, HB=200,
       pren=65, costo=15.0, galling="ni", cavitacion=4, erosion=4,
       iso15156=Nace("aceptable", 35, nota="Tipo 4e (ISO 15156-3, anexo A)."), iso17945=Nace("aceptable", 35),
       notas=("Medios oxidantes y reductores mixtos; mejor que C-276 en oxidantes.",),
       fuentes=(F_PRACTICA, F_ASTM)),
    _m("N7M", "ASTM A494 N7M — Hastelloy B2 fundido", "Aleación Ni-Mo", ("ni_b",), CUERPO,
       uns="N30007", astm="ASTM A494 Gr. N7M", forma="Fundición", equivalente="B564 N10665 / N10675 (forja)",
       grupo="3.7", grupo_equivalente=True, T_min_C=-198, T_max_C=425,
       composicion="Ni bal. · Mo 30–33 · Fe ≤ 3 · Cr ≤ 1", Rm_MPa=525, Rp_MPa=275, HB=238, costo=18.0,
       galling="ni", cavitacion=4, erosion=4,
       iso15156=Nace("aceptable", 35), iso17945=Nace("aceptable", 35),
       notas=("Ácido clorhídrico en todas las concentraciones y temperaturas (medio reductor).",
              "Muy sensible a oxidantes: Fe³⁺, Cu²⁺, O₂ disuelto o cloro lo destruyen rápidamente."),
       fuentes=(F_PRACTICA, F_ASTM)),
    _m("TiC3", "ASTM B367 Gr. C-2 / B381 F2 — titanio grado 2", "Titanio", ("ti",), CUERPO,
       uns="R50400", astm="ASTM B367 Gr. C-2 (fund.) / B381 F2 (forja)", forma="Fundición / forja",
       equivalente="B381 F2", grupo=None, T_min_C=-60, T_max_C=316, composicion="Ti ≥ 99 · O ≤ 0,25 · Fe ≤ 0,3",
       Rm_MPa=345, Rp_MPa=275, HB=200, costo=16.0, galling="ti", cavitacion=3, erosion=4,
       iso15156=Nace("aceptable", None, nota="Titanio grados listados en ISO 15156-3, anexo A."),
       iso17945=Nace("aceptable", None),
       notas=("Cloro húmedo, hipocloritos, agua de mar caliente, ácido nítrico.",
              "No apto para HF, ácidos reductores calientes ni cloro seco (reacción violenta) ni oxígeno "
              "a presión.", "No está en las tablas de ASME B16.34: rating por el fabricante (B31.3 / "
              "Sección VIII)."), fuentes=(F_PRACTICA, F_ASTM)),

    # ------------------------------------------------------------------ cuerpos forjados más usados
    _m("A105", "ASTM A105 — acero al carbono forjado", "Acero al carbono", ("cs",), CUERPO,
       uns="K03504", astm="ASTM A105", forma="Forja", equivalente="A216 WCB (fundición)", grupo="1.1",
       T_min_C=-29, T_max_C=538, composicion="C ≤ 0,35 · Mn 0,6–1,05", Rm_MPa=485, Rp_MPa=250, HB=170,
       costo=1.1, galling="cs", cavitacion=1, erosion=2, iso15156=CS_15156, iso17945=CS_17945,
       notas=("Cuerpos forjados y válvulas pequeñas; > 425 °C riesgo de grafitización.",),
       fuentes=(F_B1634, F_ASTM)),
    _m("LF2", "ASTM A350 LF2 Cl.1 — acero al carbono forjado baja temperatura", "Acero baja temperatura",
       ("cs",), CUERPO, uns="K03011", astm="ASTM A350 Gr. LF2 Cl.1", forma="Forja", equivalente="A352 LCC",
       grupo="1.1", T_min_C=-46, T_max_C=345, composicion="C ≤ 0,30 · Mn 0,6–1,35 · impacto a −46 °C",
       Rm_MPa=485, Rp_MPa=250, HB=170, costo=1.35, galling="cs", cavitacion=1, erosion=2,
       iso15156=CS_15156, iso17945=CS_17945, fuentes=(F_B1634, F_ASTM)),
    _m("F316", "ASTM A182 F316 — inoxidable 316 forjado", "Inoxidable austenítico", ("ss316",), CUERPO,
       uns="S31600", astm="ASTM A182 Gr. F316", forma="Forja", equivalente="A351 CF8M", grupo="2.2",
       T_min_C=-254, T_max_C=816, composicion="C ≤ 0,08 · Cr 16–18 · Ni 10–14 · Mo 2–3", Rm_MPa=515,
       Rp_MPa=205, HB=160, pren=24, costo=3.3, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945, fuentes=(F_B1634, F_ASTM)),
    _m("F304", "ASTM A182 F304 — inoxidable 304 forjado", "Inoxidable austenítico", ("ss304",), CUERPO,
       uns="S30400", astm="ASTM A182 Gr. F304", forma="Forja", equivalente="A351 CF8 (fundición)", grupo="2.1",
       T_min_C=-254, T_max_C=816, composicion="C ≤ 0,08 · Cr 18–20 · Ni 8–11", Rm_MPa=515, Rp_MPa=205,
       HB=150, pren=19, costo=3.1, galling="aus", cavitacion=2, erosion=3,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Cuerpos y bonetes forjados para ácido nítrico, oxidantes y criogenia.",
              "No es la opción recomendada en general: el CF8 fundido cumple lo mismo a menor costo, y frente a "
              "cloruros el 316 (F316 / CF8M) resiste mejor porque lleva molibdeno.",
              "Por encima de 538 °C solo con C ≥ 0,04 %; picaduras y SCC por cloruros por encima de ~60 °C."),
       fuentes=(F_B1634, F_ASTM)),
    _m("F51", "ASTM A182 F51 — dúplex 2205 forjado", "Inoxidable dúplex (Duplex SS)", ("duplex",), CUERPO,
       uns="S31803", astm="ASTM A182 Gr. F51", forma="Forja", equivalente="A995 CD3MN", grupo="2.8",
       T_min_C=-46, T_max_C=315, composicion="Cr 21–23 · Ni 4,5–6,5 · Mo 2,5–3,5 · N 0,08–0,2",
       Rm_MPa=620, Rp_MPa=450, HB=240, pren=34, costo=4.8, galling="dup", cavitacion=4, erosion=5,
       iso15156=Nace("condicional", 28, 10, 232, azufre=False, nota="ISO 15156-3, anexo A."),
       iso17945=Nace("aceptable", 28), fuentes=(F_B1634, F_15156)),
    _m("F55", "ASTM A182 F55 — superdúplex forjado (S32760)", "Inoxidable superdúplex (Super Duplex SS)", ("sduplex",), CUERPO,
       uns="S32760", astm="ASTM A182 Gr. F55", forma="Forja", equivalente="A995 CD3MWCuN", grupo="2.8",
       T_min_C=-46, T_max_C=315, composicion="Cr 24–26 · Ni 6–8 · Mo 3–4 · W · Cu · N 0,2–0,3", Rm_MPa=750,
       Rp_MPa=550, HB=260, pren=41, costo=6.3, galling="dup", cavitacion=5, erosion=6,
       iso15156=Nace("condicional", 32, 20, 232, azufre=False, nota="ISO 15156-3, anexo A."),
       iso17945=Nace("aceptable", 32), fuentes=(F_B1634, F_15156)),
    _m("F22", "ASTM A182 F22 Cl.3 — acero 2¼Cr-1Mo forjado", "Acero Cr-Mo", ("crmo",), CUERPO,
       uns="K21590", astm="ASTM A182 Gr. F22 Cl.3", forma="Forja", equivalente="A217 WC9", grupo="1.10",
       T_min_C=-29, T_max_C=595, composicion="Cr 2–2,5 · Mo 0,87–1,13", Rm_MPa=515, Rp_MPa=310, HB=180,
       costo=2.2, galling="cs", cavitacion=3, erosion=4, iso15156=CS_15156,
       iso17945=Nace("aceptable", 22), fuentes=(F_B1634, F_ASTM)),
    _m("F91", "ASTM A182 F91 — acero 9Cr-1Mo-V forjado", "Acero Cr-Mo", ("crmo9",), CUERPO,
       uns="K90901", astm="ASTM A182 Gr. F91", forma="Forja", equivalente="A217 C12A", grupo="1.15",
       T_min_C=-29, T_max_C=649, composicion="Cr 8–9,5 · Mo 0,85–1,05 · V · Nb", Rm_MPa=585, Rp_MPa=415,
       HB=210, costo=3.5, galling="cs", cavitacion=4, erosion=6, iso15156=Nace("condicional", 22),
       iso17945=Nace("condicional", 22), fuentes=(F_B1634, F_ASTM)),

    # ------------------------------------------------------------------ internos (obturador, asiento, jaula, guía)
    _m("316", "Inoxidable 316 / 316L (A479, A276)", "Inoxidable austenítico", ("ss316",),
       TRIM | {"vastago"}, uns="S31600 / S31603", astm="ASTM A479 / A276 316", forma="Barra / forja",
       T_min_C=-254, T_max_C=816, composicion="Cr 16–18 · Ni 10–14 · Mo 2–3", Rm_MPa=515, Rp_MPa=205,
       HB=150, pren=24, costo=1.0, galling="aus", cavitacion=2, erosion=2,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Interno estándar en servicios limpios con ΔP moderada.",
              "Blando (≈ 150 HB): se desgasta con cavitación, erosión o sólidos; galling 316/316 alto."),
       fuentes=(F_PRACTICA, F_15156)),
    _m("304", "Inoxidable 304 / 304L (A479, A276)", "Inoxidable austenítico", ("ss304",),
       TRIM | {"vastago"}, uns="S30400 / S30403", astm="ASTM A479 / A276 304", forma="Barra / forja",
       T_min_C=-254, T_max_C=816, composicion="C ≤ 0,08 · Cr 18–20 · Ni 8–10,5", Rm_MPa=515, Rp_MPa=205,
       HB=150, pren=19, costo=1.05, galling="aus", cavitacion=2, erosion=2,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Obturador, bola, disco, asiento, jaula, guía o vástago en ácido nítrico, oxidantes, agua limpia y "
              "criogenia.",
              "No es la opción recomendada en general: en internos de válvulas el 316 es el estándar de stock y "
              "cuesta prácticamente lo mismo, y el 304 resiste peor las picaduras y la corrosión bajo tensión por "
              "cloruros (no lleva molibdeno, PREN ≈ 19 frente a 24).",
              "Blando (≈ 150 HB): igual que el 316, se desgasta con cavitación, erosión o sólidos y tiene galling "
              "alto contra sí mismo o contra 316."),
       fuentes=(F_PRACTICA, F_ASTM, F_15156)),
    _m("316_NIT", "316 nitrurado (nitruración a baja temperatura, ≈ 1000 HV superficial)",
       "Inoxidable + capa nitrurada", ("ss316",), C({"guia", "jaula", "obturador", "vastago"}),
       uns="S31600 + capa nitrurada", astm="ASTM A479 / A276 316 + nitruración (gas o plasma) a baja temperatura",
       forma="Barra / forja con tratamiento superficial", T_min_C=-196, T_max_C=400,
       composicion="Base 316; capa de austenita expandida en N (fase S) de 15–35 µm", Rm_MPa=515, Rp_MPa=205,
       HB=150, HRC=65, pren=24, costo=1.5, galling="nit", cavitacion=3, erosion=4,
       iso15156=Nace("condicional", None, 100, 60, nota="La capa superficial no cambia la aceptación: vale la base "
                     "316 (ISO 15156-3, anexo A). Confirmar con la edición vigente y el fabricante.", azufre=False),
       iso17945=AUS_17945,
       notas=("Evita el galling y el desgaste en guías, bujes, ejes de rotativas, obturadores y jaulas de 316 "
              "sin cambiar el material base.",
              "Nitruración a baja temperatura (menos de unos 450 °C): conserva casi toda la resistencia a la "
              "corrosión del 316. La nitruración convencional a alta temperatura forma nitruros de cromo y la "
              "reduce: pedir siempre la de baja temperatura.",
              "Capa delgada: no reemplaza un recargue de Stellite ni un inserto de carburo frente a cavitación "
              "severa o sólidos. Por encima de unos 400 °C la capa pierde estabilidad."),
       fuentes=(F_PRACTICA, F_15156)),
    _m("316_ST6", "316 con recargue de Stellite 6 (asiento y/o superficie de guiado)", "Inoxidable + recargue Co-Cr",
       ("ss316", "cocr"), TRIM, uns="S31600 + R30006", astm="ASTM A479 316 + AWS A5.21 ERCoCr-A",
       forma="Barra con recargue soldado", T_min_C=-254, T_max_C=816,
       composicion="Base 316; recargue Co bal. · Cr 27–32 · W 4–6 · C 0,9–1,4", Rm_MPa=515, Rp_MPa=205,
       HB=150, HRC=40, pren=24, costo=2.2, galling="cocr", cavitacion=8, erosion=8,
       iso15156=Nace("aceptable", None, nota="Recargue Co-Cr-W aceptable (ISO 15156-3, anexo A); base 316 según A.2.",
                     pH2S_max_kPa=100, T_max_C=60, azufre=False),
       iso17945=Nace("aceptable", None, nota="Recargue Co-Cr-W aceptable; base 316 ≤ 22 HRC."),
       notas=("Estándar para asientos y obturadores con ΔP alta, cavitación moderada y cierre clase V.",
              "La dureza (38–45 HRC) está solo en la capa de recargue: el sustrato sigue siendo 316."),
       fuentes=(F_PRACTICA, F_15156)),
    _m("ST6", "Stellite 6 macizo (Co-Cr-W, fundido o forjado 6B)", "Aleación Co-Cr-W", ("cocr",), TRIM,
       uns="R30006 / R30016", astm="AMS 5387 / AMS 5894 (6B)", forma="Fundición / barra",
       T_min_C=-273, T_max_C=816, composicion="Co bal. · Cr 28 · W 4,5 · C 1,1", Rm_MPa=900, Rp_MPa=640,
       HRC=40, costo=6.0, galling="cocr", cavitacion=9, erosion=9,
       iso15156=Nace("aceptable", None, nota="Aleaciones Co-Cr-W (ISO 15156-3, anexo A)."),
       iso17945=Nace("aceptable", None),
       notas=("Máxima resistencia combinada a cavitación, erosión y galling entre los metales.",
              "Atacado por ácidos reductores fuertes (HCl) y amoníaco caliente."), fuentes=(F_PRACTICA,)),
    _m("410_HT", "Inoxidable 410 templado (38–45 HRC)", "Inoxidable martensítico", ("mart",), TRIM | {"vastago"},
       uns="S41000", astm="ASTM A276 / A479 410", forma="Barra templada y revenida", T_min_C=-29,
       T_max_C=427, composicion="Cr 11,5–13,5 · C ≤ 0,15", Rm_MPa=1000, Rp_MPa=790, HRC=40, pren=12,
       costo=0.8, galling="mart", cavitacion=5, erosion=5,
       iso15156=Nace("no", nota="Endurecido por encima de 22 HRC: no aceptable en servicio agrio."),
       iso17945=Nace("no", nota="> 22 HRC no aceptable."),
       notas=("Económico, buena resistencia al desgaste en agua, vapor y aceites.",
              "Corrosión moderada: no apto para cloruros altos ni ácidos."), fuentes=(F_PRACTICA,)),
    _m("410_NACE", "Inoxidable 410 / CA6NM revenido doble (≤ 22–23 HRC)", "Inoxidable martensítico", ("mart",),
       TRIM | {"vastago"}, uns="S41000 / J91540", astm="ASTM A479 410 / A487 CA6NM Cl.A", forma="Barra / fundición",
       T_min_C=-29, T_max_C=427, composicion="Cr 11,5–14 · Ni 3,5–4,5 (CA6NM) · Mo 0,4–1", Rm_MPa=760,
       Rp_MPa=550, HRC=22, pren=13, costo=0.9, galling="mart", cavitacion=3, erosion=4,
       iso15156=Nace("condicional", 22, 10, None, 3.5, azufre=False,
                     nota="410 ≤ 22 HRC, CA6NM ≤ 23 HRC; pH₂S ≤ 10 kPa, pH ≥ 3,5 (ISO 15156-3, anexo A)."),
       iso17945=Nace("aceptable", 22, nota="Doble revenido, ≤ 22 HRC (CA6NM ≤ 23 HRC)."),
       notas=("Alternativa martensítica para servicio agrio leve; dureza insuficiente para cavitación.",),
       fuentes=(F_PRACTICA, F_15156)),
    _m("416", "Inoxidable 416 templado (38–43 HRC)", "Inoxidable martensítico (fácil mecanizado)", ("mart",),
       TRIM | {"vastago"}, uns="S41600", astm="ASTM A582 416", forma="Barra templada", T_min_C=-29, T_max_C=427,
       composicion="Cr 12–14 · S ≥ 0,15 (fácil mecanizado)", Rm_MPa=965, Rp_MPa=760, HRC=40, pren=12,
       costo=0.8, galling="mart", cavitacion=5, erosion=5,
       iso15156=Nace("no", nota="Aceros de fácil mecanizado (S alto) no aceptables."),
       iso17945=Nace("no", nota="No aceptable."),
       notas=("Jaulas y obturadores estándar en agua, vapor y gas limpios.",
              "El azufre añadido reduce la resistencia a la corrosión (picaduras)."), fuentes=(F_PRACTICA,)),
    _m("440C", "Inoxidable 440C templado (56–60 HRC)", "Inoxidable martensítico alto C", ("mart440",),
       TRIM, uns="S44004", astm="ASTM A276 440C", forma="Barra templada", T_min_C=-29, T_max_C=427,
       composicion="C 0,95–1,2 · Cr 16–18 · Mo ≤ 0,75", Rm_MPa=1970, Rp_MPa=1900, HRC=58, pren=18,
       costo=1.1, galling="mart", cavitacion=8, erosion=8,
       iso15156=Nace("no", nota="No aceptable (dureza muy superior a los límites)."),
       iso17945=Nace("no", nota="No aceptable."),
       notas=("Obturadores y asientos para cavitación severa y flashing en agua y condensado.",
              "Frágil frente a impacto; corrosión limitada en cloruros."), fuentes=(F_PRACTICA,)),
    _m("174_H1150D", "17-4PH H1150D (≤ 33 HRC, NACE)", "Inoxidable endurecido por precipitación", ("ph",),
       TRIM | {"vastago"}, uns="S17400", astm="ASTM A564 / A705 Tipo 630 H1150D", forma="Barra / forja",
       T_min_C=-29, T_max_C=343, composicion="Cr 15–17,5 · Ni 3–5 · Cu 3–5 · Nb 0,15–0,45", Rm_MPa=860,
       Rp_MPa=725, HRC=30, pren=17, costo=1.3, galling="ph", cavitacion=5, erosion=5,
       iso15156=Nace("condicional", 33, 3.4, None, 4.5, azufre=False,
                     nota="Doble envejecido H1150D, ≤ 33 HRC; pH₂S ≤ 3,4 kPa, pH ≥ 4,5 (ISO 15156-3, anexo A)."),
       iso17945=Nace("aceptable", 33, nota="H1150D, ≤ 33 HRC, sin límite ambiental propio."),
       notas=("Vástago estándar en servicio agrio y en general; buena resistencia mecánica.",),
       fuentes=(F_PRACTICA, F_15156)),
    _m("174_H1075", "17-4PH H1075 (≈ 33–38 HRC)", "Inoxidable endurecido por precipitación", ("ph",),
       TRIM | {"vastago"}, uns="S17400", astm="ASTM A564 Tipo 630 H1075", forma="Barra", T_min_C=-29, T_max_C=427,
       composicion="Cr 15–17,5 · Ni 3–5 · Cu 3–5 · Nb", Rm_MPa=1000, Rp_MPa=860, HRC=35, pren=17, costo=1.3,
       galling="ph", cavitacion=6, erosion=6, iso15156=Nace("no", nota="Solo H1150D es aceptable."),
       iso17945=Nace("no"), notas=("Jaulas y vástagos de alta resistencia en servicio no agrio.",),
       fuentes=(F_PRACTICA,)),
    _m("174_H900", "17-4PH H900 (40–47 HRC)", "Inoxidable endurecido por precipitación", ("ph",),
       TRIM, uns="S17400", astm="ASTM A564 Tipo 630 H900", forma="Barra", T_min_C=-29, T_max_C=343,
       composicion="Cr 15–17,5 · Ni 3–5 · Cu 3–5 · Nb", Rm_MPa=1310, Rp_MPa=1170, HRC=44, pren=17, costo=1.3,
       galling="ph", cavitacion=7, erosion=7,
       iso15156=Nace("no", nota="No aceptable (fragilización por hidrógeno)."), iso17945=Nace("no"),
       notas=("Obturadores y jaulas para cavitación severa en agua; sensible a fragilización por H₂.",),
       fuentes=(F_PRACTICA,)),
    _m("CB7Cu1", "ASTM A747 CB7Cu-1 — 17-4PH fundido H1025 (jaulas)", "Inoxidable endurecido por precipitación",
       ("ph",), C({"jaula", "guia"}), uns="J92180", astm="ASTM A747 CB7Cu-1 H1025", forma="Fundición",
       T_min_C=-29, T_max_C=343, composicion="Cr 15,5–17,7 · Ni 3,6–4,6 · Cu 2,5–3,2", Rm_MPa=1000,
       Rp_MPa=860, HRC=36, pren=17, costo=1.4, galling="ph", cavitacion=6, erosion=6,
       iso15156=Nace("no", nota="Solo condición H1150D doble envejecido ≤ 33 HRC."), iso17945=Nace("no"),
       notas=("Jaulas fundidas de forma compleja con dureza media.",), fuentes=(F_PRACTICA,)),
    _m("316_ENC", "316 con níquel químico (ENC, ≈ 50 HRC superficial)", "Inoxidable + recubrimiento Ni-P",
       ("ss316", "enc"), C({"jaula", "guia", "obturador"}), uns="S31600 + Ni-P", astm="ASTM B733 (ENC)",
       forma="Barra / fundición con recubrimiento", T_min_C=-196, T_max_C=400,
       composicion="Base 316; capa Ni-P 25–75 µm", Rm_MPa=515, Rp_MPa=205, HB=150, HRC=50, pren=24,
       costo=1.6, galling="enc", cavitacion=3, erosion=4,
       iso15156=Nace("condicional", None, 100, 60, nota="Recubrimientos no protegen contra SSC: vale la base "
                     "316 (ISO 15156-3, anexo A).", azufre=False), iso17945=AUS_17945,
       notas=("Evita el galling en jaula/obturador de 316 en servicios limpios.",
              "La capa delgada puede desprenderse con cavitación o erosión: no la sustituye un recargue."),
       fuentes=(F_PRACTICA,)),
    # ---- v0.8.2: materiales de juegos de internos y de vástagos
    _m("316L", "Inoxidable 316L (S31603) bajo carbono", "Inoxidable austenítico", ("ss316",), TRIM | {"vastago"},
       uns="S31603", astm="ASTM A479 / A276 316L", forma="Barra / forja", T_min_C=-254, T_max_C=454,
       composicion="C ≤ 0,03 · Cr 16–18 · Ni 10–14 · Mo 2–3", Rm_MPa=485, Rp_MPa=170, HB=150, pren=24,
       costo=1.05, galling="aus", cavitacion=2, erosion=2, iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Variante de bajo carbono del 316: no se sensibiliza al soldar ni al recargar; para piezas soldadas "
              "y medios que atacan el borde de grano (ácidos oxidantes, ácido politiónico).",
              "Algo menos resistente que el 316 (fluencia 170 MPa); por encima de 454 °C se usa 316H o 321."),
       fuentes=(F_ASTM, F_15156)),
    _m("321", "Inoxidable 321 (S32100) estabilizado con titanio", "Inoxidable austenítico estabilizado", ("ss304",),
       TRIM | {"vastago"}, uns="S32100", astm="ASTM A479 / A276 321", forma="Barra / forja", T_min_C=-198,
       T_max_C=816, composicion="C ≤ 0,08 · Cr 17–19 · Ni 9–12 · Ti ≥ 5×(C+N)", Rm_MPa=515, Rp_MPa=205, HB=160,
       pren=18, costo=1.15, galling="aus", cavitacion=2, erosion=2, iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("El titanio fija el carbono: no se sensibiliza en servicio prolongado entre 425 y 815 °C. Internos y "
              "vástagos de alta temperatura en refinería y petroquímica (agrietamiento por ácido politiónico).",
              "Sin molibdeno: menor resistencia a las picaduras por cloruros que el 316."),
       fuentes=(F_ASTM, "API RP 571 (ácido politiónico)")),
    _m("CF8M_T", "ASTM A351 CF8M — 316 fundido (jaulas y guías)", "Inoxidable austenítico", ("ss316",),
       C({"jaula", "guia"}), uns="J92900", astm="ASTM A351 Gr. CF8M", forma="Fundición", T_min_C=-254,
       T_max_C=816, composicion="C ≤ 0,08 · Cr 18–21 · Ni 9–12 · Mo 2–3", Rm_MPa=485, Rp_MPa=205, HB=160,
       pren=24, costo=1.05, galling="aus", cavitacion=2, erosion=2, iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Jaula fundida para servicios corrosivos limpios.",
              "Sin recubrimiento tiene galling alto contra un obturador de 316: combinar con obturador recargado o "
              "pedir la jaula con níquel químico (ENC)."), fuentes=(F_ASTM, F_PRACTICA)),
    _m("CF8C_ENC", "ASTM A351 CF8C (347 fundido) con níquel químico (ENC) — jaulas",
       "Inoxidable estabilizado + recubrimiento Ni-P", ("ss304", "enc"), C({"jaula", "guia"}), uns="J92710 + Ni-P",
       astm="ASTM A351 Gr. CF8C + ASTM B733", forma="Fundición con recubrimiento", T_min_C=-196, T_max_C=400,
       composicion="Base: C ≤ 0,08 · Cr 18–21 · Ni 9–12 · Nb 8×C–1,0; capa Ni-P 25–75 µm", Rm_MPa=485,
       Rp_MPa=205, HB=160, HRC=50, pren=19, costo=1.8, galling="enc", cavitacion=3, erosion=4,
       iso15156=Nace("condicional", None, 100, 60, nota="Recubrimientos no protegen contra SSC: vale la base "
                     "austenítica (ISO 15156-3, anexo A).", azufre=False), iso17945=AUS_17945,
       notas=("Jaula estabilizada con niobio para acompañar internos de 321; el ENC evita el galling.",
              "El ENC limita la temperatura a unos 400 °C."), fuentes=(F_ASTM, F_PRACTICA)),
    _m("174_H1150D_ST6", "17-4PH H1150D con recargue de Stellite 6 (obturadores NACE)",
       "Inoxidable PH + recargue Co-Cr", ("ph", "cocr"), C({"obturador"}), uns="S17400 + R30006",
       astm="ASTM A564 Tipo 630 H1150D + AWS A5.21 ERCoCr-A", forma="Barra con recargue soldado", T_min_C=-29,
       T_max_C=343, composicion="Base 17-4PH doble envejecido; recargue Co · Cr 27–32 · W 4–6", Rm_MPa=860,
       Rp_MPa=725, HRC=40, pren=17, costo=2.6, galling="cocr", cavitacion=8, erosion=8,
       iso15156=Nace("condicional", 33, 3.4, None, 4.5, azufre=False,
                     nota="Base H1150D ≤ 33 HRC con los límites ambientales del 17-4PH (pH₂S ≤ 3,4 kPa, pH ≥ 4,5); "
                          "el recargue Co-Cr-W es aceptable (ISO 15156-3, anexo A)."),
       iso17945=Nace("aceptable", 33, nota="Base H1150D ≤ 33 HRC; recargue Co-Cr-W aceptable."),
       notas=("Obturador de alta resistencia mecánica para servicio agrio con ΔP alta: el recargue protege asiento "
              "y guiado.",), fuentes=(F_15156, F_PRACTICA)),
    _m("CB7Cu1_CR", "CB7Cu-1 (17-4PH fundido) H1150D con cromo duro — jaulas NACE",
       "Inoxidable PH + recubrimiento de cromo", ("ph",), C({"jaula", "guia"}), uns="J92180 + Cr",
       astm="ASTM A747 CB7Cu-1 H1150 doble + cromado duro (AMS 2460)", forma="Fundición con recubrimiento",
       T_min_C=-29, T_max_C=343, composicion="Base Cr 15,5–17,7 · Ni 3,6–4,6 · Cu 2,5–3,2; capa de Cr 25–50 µm",
       Rm_MPa=860, Rp_MPa=725, HRC=60, pren=17, costo=2.0, galling="enc", cavitacion=4, erosion=5,
       iso15156=Nace("condicional", 33, 3.4, None, 4.5, azufre=False,
                     nota="Base doble envejecida ≤ 33 HRC; el cromado no cambia la aceptación (vale la base)."),
       iso17945=Nace("aceptable", 33, nota="Base doble envejecida ≤ 33 HRC."),
       notas=("Jaula fundida para servicio agrio: el cromo duro evita el galling contra el obturador.",
              "La capa delgada se desprende con cavitación severa o sólidos: no reemplaza a un recargue."),
       fuentes=(F_15156, F_PRACTICA)),
    _m("N50", "Nitronic 50 (S20910, XM-19) de alta resistencia", "Inoxidable austenítico al Mn-N",
       ("ss316",), C({"vastago", "guia", "obturador", "asiento"}), uns="S20910", astm="ASTM A479 / A276 XM-19",
       forma="Barra (condición de alta resistencia)", T_min_C=-196, T_max_C=649,
       composicion="Cr 20,5–23,5 · Ni 11,5–13,5 · Mn 4–6 · Mo 1,5–3 · N 0,2–0,4 · Nb · V", Rm_MPa=930,
       Rp_MPa=690, HB=290, pren=34, costo=1.6, galling="aus", cavitacion=4, erosion=4,
       iso15156=Nace("condicional", 35, 100, 60, azufre=False,
                     nota="Austenítico de alto nitrógeno: ≤ 35 HRC con los límites ambientales de los austeníticos "
                          "(ISO 15156-3, anexo A); confirmar con la edición vigente."),
       iso17945=Nace("aceptable", 35),
       notas=("Vástago y eje de alta resistencia con corrosión mejor que la del 316 (PREN ≈ 34): agua de mar, "
              "cloruros moderados, servicios donde el 17-4PH no es apto.",
              "Galling contra sí mismo y contra 316: combinar con buje de Nitronic 60 o recargado."),
       fuentes=(F_ASTM, F_15156)),
    _m("A286", "A-286 (S66286) endurecido por precipitación", "Superaleación Fe-Ni-Cr", ("ss304",),
       C({"vastago"}), uns="S66286", astm="ASTM A638 / A453 Gr. 660", forma="Barra solubilizada y envejecida",
       T_min_C=-196, T_max_C=704, composicion="Ni 24–27 · Cr 13,5–16 · Mo 1–1,5 · Ti 1,9–2,35 · V · B",
       Rm_MPa=895, Rp_MPa=585, HRC=30, pren=18, costo=3.0, galling="aus", cavitacion=4, erosion=4,
       iso15156=Nace("condicional", 35, 100, 60, azufre=False,
                     nota="Solubilizado y envejecido ≤ 35 HRC (ISO 15156-3, anexo A); confirmar los límites "
                          "ambientales con la edición vigente."),
       iso17945=Nace("aceptable", 35),
       notas=("Vástago de alta resistencia para alta temperatura (hasta unos 700 °C): conserva la fluencia donde el "
              "17-4PH ya no sirve (> 343 °C).", "Resistencia a la corrosión parecida a la del 304."),
       fuentes=(F_ASTM, F_15156)),
    _m("N60", "Nitronic 60 (S21800) — inoxidable antigalling", "Inoxidable austenítico al Mn-Si", ("ss304",),
       C({"guia", "jaula", "obturador", "vastago"}), uns="S21800", astm="ASTM A479 / A276 S21800",
       forma="Barra", T_min_C=-196, T_max_C=816, composicion="Cr 16–18 · Ni 8–9 · Mn 7–9 · Si 3,5–4,5 · N",
       Rm_MPa=725, Rp_MPa=415, HB=230, pren=20, costo=1.7, galling="n60", cavitacion=6, erosion=5,
       iso15156=Nace("condicional", 22, 100, 60, azufre=False, nota="Austenítico ISO 15156-3, anexo A (solubilizado)."),
       iso17945=AUS_17945,
       notas=("Bujes de guía y anillos de desgaste: excelente resistencia al galling incluso contra 316.",
              "Muy buena resistencia a la cavitación para un inoxidable austenítico."), fuentes=(F_PRACTICA,)),
    _m("2205", "Dúplex 2205 (S31803 / S32205) barra", "Inoxidable dúplex (Duplex SS)", ("duplex",), TRIM | {"vastago"},
       uns="S31803 / S32205", astm="ASTM A479 / A276 S32205", forma="Barra", T_min_C=-46, T_max_C=315,
       composicion="Cr 22 · Ni 5 · Mo 3 · N 0,17", Rm_MPa=655, Rp_MPa=450, HB=250, pren=35, costo=1.8,
       galling="dup", cavitacion=4, erosion=5,
       iso15156=Nace("condicional", 28, 10, 232, azufre=False, nota="ISO 15156-3, anexo A."),
       iso17945=Nace("aceptable", 28), notas=("Internos y ejes en agua salobre y producción.",),
       fuentes=(F_15156,)),
    _m("S32760", "Superdúplex S32760 (Zeron 100) barra", "Inoxidable superdúplex (Super Duplex SS)", ("sduplex",),
       TRIM | {"vastago"}, uns="S32760", astm="ASTM A479 / A276 S32760", forma="Barra", T_min_C=-46,
       T_max_C=315, composicion="Cr 25 · Ni 7 · Mo 3,5 · W 0,7 · Cu 0,7 · N 0,25", Rm_MPa=750, Rp_MPa=550,
       HB=270, pren=41, costo=2.5, galling="dup", cavitacion=5, erosion=6,
       iso15156=Nace("condicional", 32, 20, 232, azufre=False, nota="ISO 15156-3, anexo A."),
       iso17945=Nace("aceptable", 32), notas=("Internos en agua de mar e inyección.",), fuentes=(F_15156,)),
    _m("254SMO", "Superaustenítico 6Mo (S31254) barra", "Superaustenítico", ("superaus",), TRIM | {"vastago"},
       uns="S31254", astm="ASTM A479 / A276 S31254", forma="Barra", T_min_C=-196, T_max_C=400,
       composicion="Cr 20 · Ni 18 · Mo 6,1 · N 0,2 · Cu 0,7", Rm_MPa=650, Rp_MPa=300, HB=190, pren=43,
       costo=3.0, galling="aus", cavitacion=3, erosion=4, iso15156=Nace("aceptable", 35),
       iso17945=Nace("aceptable", 35), fuentes=(F_15156,)),
    _m("A20", "Aleación 20 (N08020) barra", "Aleación Ni-Fe-Cr", ("a20",), TRIM | {"vastago"}, uns="N08020",
       astm="ASTM B473 N08020", forma="Barra", T_min_C=-29, T_max_C=425,
       composicion="Ni 32–38 · Cr 19–21 · Mo 2–3 · Cu 3–4 · Nb", Rm_MPa=550, Rp_MPa=240, HB=160, pren=28,
       costo=3.0, galling="ni", cavitacion=2, erosion=3, iso15156=Nace("aceptable", 35),
       iso17945=Nace("aceptable", 35), fuentes=(F_PRACTICA,)),
    _m("825", "Incoloy 825 (N08825) barra", "Aleación Ni-Fe-Cr", ("in825",), TRIM | {"vastago"}, uns="N08825",
       astm="ASTM B425 N08825", forma="Barra", T_min_C=-196, T_max_C=538,
       composicion="Ni 38–46 · Cr 19,5–23,5 · Mo 2,5–3,5 · Cu 1,5–3", Rm_MPa=585, Rp_MPa=240, HB=170, pren=31,
       costo=4.0, galling="ni", cavitacion=3, erosion=3, iso15156=Nace("aceptable", 35),
       iso17945=Nace("aceptable", 35), fuentes=(F_PRACTICA,)),
    _m("625", "Inconel 625 (N06625) barra", "Aleación Ni-Cr-Mo", ("ni625",), TRIM | {"vastago"}, uns="N06625",
       astm="ASTM B446 N06625", forma="Barra recocida", T_min_C=-198, T_max_C=645,
       composicion="Ni ≥ 58 · Cr 20–23 · Mo 8–10 · Nb 3,2–4,2", Rm_MPa=830, Rp_MPa=415, HB=200, pren=51,
       costo=6.0, galling="ni", cavitacion=4, erosion=4, iso15156=Nace("aceptable", 35),
       iso17945=Nace("aceptable", 35), fuentes=(F_PRACTICA,)),
    _m("C276", "Hastelloy C-276 (N10276) barra", "Aleación Ni-Cr-Mo", ("ni_c",), TRIM | {"vastago"},
       uns="N10276", astm="ASTM B574 N10276", forma="Barra", T_min_C=-198, T_max_C=538,
       composicion="Ni bal. · Cr 14,5–16,5 · Mo 15–17 · W 3–4,5 · Fe 4–7", Rm_MPa=690, Rp_MPa=285, HB=200,
       pren=68, costo=7.0, galling="ni", cavitacion=4, erosion=4, iso15156=Nace("aceptable", 35),
       iso17945=Nace("aceptable", 35), fuentes=(F_PRACTICA,)),
    _m("C22", "Hastelloy C-22 (N06022) barra", "Aleación Ni-Cr-Mo", ("ni_c",), TRIM | {"vastago"}, uns="N06022",
       astm="ASTM B574 N06022", forma="Barra", T_min_C=-198, T_max_C=538,
       composicion="Ni bal. · Cr 20–22,5 · Mo 12,5–14,5 · W 2,5–3,5", Rm_MPa=690, Rp_MPa=310, HB=200, pren=65,
       costo=7.5, galling="ni", cavitacion=4, erosion=4, iso15156=Nace("aceptable", 35),
       iso17945=Nace("aceptable", 35), fuentes=(F_PRACTICA,)),
    _m("B2", "Hastelloy B-2 / B-3 (N10665 / N10675) barra", "Aleación Ni-Mo", ("ni_b",), TRIM | {"vastago"},
       uns="N10665 / N10675", astm="ASTM B335", forma="Barra", T_min_C=-198, T_max_C=425,
       composicion="Ni bal. · Mo 26–30", Rm_MPa=760, Rp_MPa=350, HB=238, costo=9.0, galling="ni",
       cavitacion=4, erosion=4, iso15156=Nace("aceptable", 35), iso17945=Nace("aceptable", 35),
       fuentes=(F_PRACTICA,)),
    _m("M400", "Monel 400 (N04400) barra", "Aleación Ni-Cu", ("monel",), TRIM | {"vastago"}, uns="N04400",
       astm="ASTM B164 N04400", forma="Barra", T_min_C=-198, T_max_C=475, composicion="Ni ≥ 63 · Cu 28–34",
       Rm_MPa=550, Rp_MPa=240, HB=150, costo=5.0, galling="ni", cavitacion=3, erosion=3,
       iso15156=Nace("aceptable", 35), iso17945=Nace("aceptable", 35), fuentes=(F_PRACTICA,)),
    _m("K500", "Monel K-500 (N05500) envejecido", "Aleación Ni-Cu endurecida", ("monel",), C({"vastago", "guia",
       "obturador"}), uns="N05500", astm="ASTM B865 N05500", forma="Barra envejecida", T_min_C=-198,
       T_max_C=480, composicion="Ni ≥ 63 · Cu 27–33 · Al 2,3–3,15 · Ti 0,35–0,85", Rm_MPa=965, Rp_MPa=690,
       HRC=30, costo=6.0, galling="ni", cavitacion=4, erosion=4,
       iso15156=Nace("aceptable", 35, nota="Envejecido ≤ 35 HRC (ISO 15156-3, anexo A)."), iso17945=Nace("aceptable", 35),
       notas=("Ejes y vástagos para HF, agua de mar y álcalis con alta resistencia mecánica.",),
       fuentes=(F_PRACTICA,)),
    _m("718", "Inconel 718 (N07718) envejecido", "Aleación Ni-Cr endurecida", ("ni625",), C({"vastago", "guia",
       "obturador"}), uns="N07718", astm="ASTM B637 N07718 / API 6A718", forma="Barra envejecida",
       T_min_C=-198, T_max_C=650, composicion="Ni 50–55 · Cr 17–21 · Nb 4,75–5,5 · Mo 2,8–3,3",
       Rm_MPa=1275, Rp_MPa=1035, HRC=38, pren=27, costo=6.5, galling="ni", cavitacion=5, erosion=5,
       iso15156=Nace("aceptable", 40, nota="Precipitación ≤ 40 HRC (ISO 15156-3, anexo A)."),
       iso17945=Nace("aceptable", 40),
       notas=("Vástago de muy alta resistencia en servicio agrio severo.",), fuentes=(F_PRACTICA, F_15156)),
    _m("Ti2", "Titanio grado 2 (R50400) barra", "Titanio", ("ti",), TRIM | {"vastago"}, uns="R50400",
       astm="ASTM B348 Gr. 2", forma="Barra", T_min_C=-60, T_max_C=316, composicion="Ti ≥ 99",
       Rm_MPa=345, Rp_MPa=275, HB=200, costo=6.0, galling="ti", cavitacion=3, erosion=4,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Galling Ti/Ti muy severo: usar pareja con recargue o nitrurado.",), fuentes=(F_PRACTICA,)),
    _m("WC_Co", "Carburo de tungsteno con ligante de cobalto (inserto)", "Carburo cementado", ("wc",),
       C({"asiento", "obturador", "jaula"}), uns="—", astm="Especificación del fabricante",
       forma="Inserto sinterizado / recubrimiento HVOF", T_min_C=-196, T_max_C=500,
       composicion="WC 88–94 % · Co 6–12 %", HRC=72, costo=10.0, galling="wc", cavitacion=10, erosion=10,
       iso15156=Nace("aceptable", None, nota="Carburos cementados aceptables como insertos."),
       iso17945=Nace("aceptable", None),
       notas=("Flashing severo, slurries abrasivos y cavitación extrema.",
              "El ligante de cobalto se disuelve en ácidos y cloruros: usar ligante de níquel en medios "
              "corrosivos.", "Frágil: no tolera impactos ni flexión."), fuentes=(F_PRACTICA,)),
    _m("WC_Ni", "Carburo de tungsteno con ligante de níquel (inserto)", "Carburo cementado", ("wc_ni",),
       C({"asiento", "obturador", "jaula"}), uns="—", astm="Especificación del fabricante",
       forma="Inserto sinterizado", T_min_C=-196, T_max_C=500, composicion="WC 88–94 % · Ni 6–12 %", HRC=70,
       costo=11.0, galling="wc", cavitacion=10, erosion=10,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Como el WC-Co pero apto para agua de mar, ácidos diluidos y H₂S.",), fuentes=(F_PRACTICA,)),
    _m("CERAM", "Cerámica técnica (alúmina 99,7 % / circonia PSZ)", "Cerámica", ("ceram",),
       C({"asiento", "obturador", "jaula"}), uns="—", astm="Especificación del fabricante",
       forma="Inserto", T_min_C=-196, T_max_C=1000, composicion="Al₂O₃ ≥ 99,5 % o ZrO₂ + MgO/Y₂O₃",
       HRC=75, costo=12.0, galling="ceram", cavitacion=7, erosion=10,
       iso15156=Nace("aceptable", None, nota="No metálico: fuera del alcance de la norma."),
       iso17945=Nace("aceptable", None),
       notas=("Slurries muy abrasivos (minería, cenizas) y ácidos fuertes.",
              "Frágil a impacto y choque térmico; atacada por HF y álcalis concentrados calientes."),
       fuentes=(F_PRACTICA,)),
    _m("BRONCE", "Bronce al aluminio C95400 / bronce fosforoso (bujes)", "Aleación de cobre", ("bronce",),
       C({"guia"}), uns="C95400 / C51000", astm="ASTM B148 / B139", forma="Fundición / barra", T_min_C=-196,
       T_max_C=260, composicion="Cu 83–87 · Al 10–11,5 · Fe 3–5", Rm_MPa=515, Rp_MPa=205, HB=170, costo=1.2,
       galling="cu", cavitacion=3, erosion=3, iso15156=Nace("no", nota="Aleaciones de cobre: no se usan con H₂S."),
       iso17945=Nace("no"),
       notas=("Bujes de guía antigalling contra inoxidable en agua y aceite.",
              "Atacado por amoníaco, aminas, H₂S y ácidos oxidantes."), fuentes=(F_PRACTICA,)),

    # ------------------------------------------------------------------ asientos blandos
    _m("PTFE", "PTFE virgen (inserto de asiento blando)", "Polímero fluorado", ("ptfe",), C({"asiento"}),
       astm="ASTM D4894", forma="Inserto", T_min_C=-46, T_max_C=232, composicion="Politetrafluoroetileno",
       costo=1.0, galling="polimero", cavitacion=0, erosion=0, blando=True,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Cierre clase VI; químicamente casi universal.", "Fluye en frío con ΔP alta: usar RPTFE o PEEK."),
       fuentes=(F_PRACTICA,)),
    _m("RPTFE", "PTFE reforzado con vidrio / carbono (RPTFE)", "Polímero fluorado", ("ptfe", "vidrio"), C({"asiento"}),
       forma="Inserto", T_min_C=-46, T_max_C=232, composicion="PTFE + 15–25 % fibra de vidrio o carbono",
       costo=1.2, galling="polimero", cavitacion=0, erosion=1, blando=True,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Más rígido que el PTFE virgen; la fibra de vidrio no es apta para HF ni álcalis fuertes.",),
       fuentes=(F_PRACTICA,)),
    _m("PEEK", "PEEK (inserto de asiento)", "Polímero de alta temperatura", ("peek",), C({"asiento"}),
       forma="Inserto", T_min_C=-60, T_max_C=260, composicion="Polieteretercetona", costo=3.0,
       galling="polimero", cavitacion=0, erosion=2, blando=True,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Clase VI a presión y temperatura mayores que el PTFE.", "Atacado por ácido sulfúrico y "
              "nítrico concentrados."), fuentes=(F_PRACTICA,)),
    _m("FKM", "Elastómero FKM (Viton®)", "Elastómero", ("fkm",), C({"asiento"}), forma="Junta / revestimiento",
       T_min_C=-18, T_max_C=204, composicion="Fluoroelastómero", costo=1.5, galling="polimero", cavitacion=0,
       erosion=0, blando=True, iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Hidrocarburos y ácidos; no apto para aminas, amoníaco, vapor ni cetonas.",), fuentes=(F_PRACTICA,)),
    _m("EPDM", "Elastómero EPDM", "Elastómero", ("epdm",), C({"asiento"}), forma="Junta / revestimiento",
       T_min_C=-40, T_max_C=150, composicion="Etileno-propileno-dieno", costo=0.8, galling="polimero",
       cavitacion=0, erosion=0, blando=True, iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Agua, vapor, álcalis; no apto para hidrocarburos ni aceites.",), fuentes=(F_PRACTICA,)),
    _m("NBR", "Elastómero NBR (Buna-N)", "Elastómero", ("nbr",), C({"asiento"}), forma="Junta / revestimiento",
       T_min_C=-30, T_max_C=107, composicion="Nitrilo-butadieno", costo=0.6, galling="polimero", cavitacion=0,
       erosion=0, blando=True, iso15156=Nace("condicional", None, nota="Resistencia al H₂S limitada."),
       iso17945=Nace("condicional", None),
       notas=("Hidrocarburos, aceites y agua fría; no apto para ozono, ácidos fuertes ni vapor.",),
       fuentes=(F_PRACTICA,)),
]}

# ---------------------------------------------------------------------------------------------------------------
# v0.14.0: pernos, espárragos y tuercas (cuerpo-bonete y brida prensaempaques). Valores típicos de las
# especificaciones citadas; el fabricante confirma el grado, la clase y la dureza con el certificado.
# ---------------------------------------------------------------------------------------------------------------
PERNOS = C({"pernos"})
F_PERNOS = "Especificación del grado (ASTM / ASME Sección II, EN 10269, ISO 3506-1, SAE J429)"
_NO_EXP = ("Si el perno queda expuesto al ambiente agrio (aislación térmica, cubiertas, enterrado) no es aceptable "
           "(ISO 15156-2, A.2.2.4); sin exposición se admite.")
_PERNOS = [
    _m("B7", "ASTM A193 / ASME SA-193 Gr. B7 — espárrago Cr-Mo templado y revenido", "Acero Cr-Mo (pernos)",
       ("crmo",), PERNOS, uns="G41400", astm="ASTM A193 / ASME SA-193 Gr. B7", forma="Barra roscada",
       T_min_C=-48, T_max_C=450, composicion="AISI 4140 / 4142: C 0,37–0,49 · Cr 0,75–1,2 · Mo 0,15–0,25",
       Rm_MPa=860, Rp_MPa=720, HRC=30, costo=1.0, galling="cs", cavitacion=1, erosion=1,
       iso15156=Nace("no", nota="Dureza hasta 35 HRC. " + _NO_EXP), iso17945=Nace("no", nota=_NO_EXP),
       notas=("Espárrago estándar de cuerpo-bonete y bridas en servicio general de −48 °C a unos 450 °C.",
              "Se combina con tuercas A194 2H. Galvanizado o con recubrimiento de flúor-polímero en ambientes "
              "corrosivos."), fuentes=(F_PERNOS,)),
    _m("B7M", "ASTM A193 / ASME SA-193 Gr. B7M — espárrago Cr-Mo para servicio agrio (≤ 235 HB)",
       "Acero Cr-Mo (pernos)", ("crmo",), PERNOS, uns="G41400", astm="ASTM A193 / ASME SA-193 Gr. B7M",
       forma="Barra roscada (100 % de ensayo de dureza)", T_min_C=-48, T_max_C=450,
       composicion="AISI 4140 / 4142 revenido a mayor temperatura", Rm_MPa=690, Rp_MPa=550, HB=235, HRC=22,
       costo=1.15, galling="cs", cavitacion=1, erosion=1,
       iso15156=Nace("aceptable", 22, nota="≤ 22 HRC (235 HB) en toda la pieza (ISO 15156-2)."),
       iso17945=Nace("aceptable", 22),
       notas=("Versión NACE del B7 (con tuercas 2HM o 7M): menor resistencia, por eso a igual diámetro admite "
              "menos precarga.",), fuentes=(F_PERNOS, F_15156)),
    _m("B16", "ASTM A193 / ASME SA-193 Gr. B16 — espárrago Cr-Mo-V para alta temperatura", "Acero Cr-Mo-V (pernos)",
       ("crmo",), PERNOS, uns="K14072", astm="ASTM A193 / ASME SA-193 Gr. B16", forma="Barra roscada",
       T_min_C=-29, T_max_C=593, composicion="C 0,36–0,47 · Cr 0,8–1,15 · Mo 0,5–0,65 · V 0,25–0,35",
       Rm_MPa=860, Rp_MPa=725, HRC=30, costo=1.6, galling="cs", cavitacion=1, erosion=1,
       iso15156=Nace("no", nota=_NO_EXP), iso17945=Nace("no"),
       notas=("Alta temperatura (vapor, refinería) hasta unos 593 °C: el vanadio da resistencia a la relajación.",
              "Se combina con tuercas A194 Gr. 7 o 4."), fuentes=(F_PERNOS,)),
    _m("B8M1", "ASTM A193 / ASME SA-193 Gr. B8M Clase 1 — espárrago inoxidable 316 solubilizado",
       "Inoxidable austenítico (pernos)", ("ss316",), PERNOS, uns="S31600", astm="ASTM A193 Gr. B8M Cl. 1",
       forma="Barra roscada solubilizada", T_min_C=-196, T_max_C=816, composicion="Cr 16–18 · Ni 10–14 · Mo 2–3",
       Rm_MPa=515, Rp_MPa=205, HB=190, pren=24, costo=1.8, galling="aus", cavitacion=2, erosion=2,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Pernos corrosión-resistentes, criogenia y alta temperatura; resistencia baja: requiere más o "
              "mayores pernos para la misma junta.", "Galling alto con tuercas 8M: lubricar con antiagarrotante."),
       fuentes=(F_PERNOS, F_15156)),
    _m("B8M2", "ASTM A193 / ASME SA-193 Gr. B8M Clase 2 — espárrago 316 endurecido por deformación",
       "Inoxidable austenítico (pernos)", ("ss316",), PERNOS, uns="S31600", astm="ASTM A193 Gr. B8M Cl. 2",
       forma="Barra roscada endurecida en frío", T_min_C=-196, T_max_C=425,
       composicion="Cr 16–18 · Ni 10–14 · Mo 2–3", Rm_MPa=760, Rp_MPa=550, HRC=30, pren=24, costo=2.0,
       galling="aus", cavitacion=2, erosion=2,
       iso15156=Nace("no", nota="Trabajado en frío por encima de 22 HRC: no aceptable si queda expuesto."),
       iso17945=Nace("no"),
       notas=("Más resistente que la Clase 1 (la resistencia baja con el diámetro).",
              "El endurecimiento se pierde por encima de unos 425 °C."), fuentes=(F_PERNOS,)),
    _m("B8M_CR", "ASTM A193 B8M con recubrimiento de cromo delgado denso (antigalling)",
       "Inoxidable austenítico + cromo (pernos)", ("ss316",), PERNOS, uns="S31600 + Cr",
       astm="ASTM A193 Gr. B8M + cromado delgado denso", forma="Barra roscada recubierta", T_min_C=-196,
       T_max_C=538, composicion="Base 316; capa de cromo de 2–10 µm", Rm_MPa=515, Rp_MPa=205, HB=190, pren=24,
       costo=2.2, galling="enc", cavitacion=2, erosion=2, iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("La capa delgada de cromo evita el galling entre espárrago y tuerca de inoxidable.",),
       fuentes=(F_PERNOS,)),
    _m("2H", "ASTM A194 / ASME SA-194 Gr. 2H — tuerca de acero al carbono templado", "Acero al carbono (tuercas)",
       ("cs",), PERNOS, uns="—", astm="ASTM A194 / ASME SA-194 Gr. 2H", forma="Tuerca hexagonal pesada",
       T_min_C=-48, T_max_C=538, composicion="C ≥ 0,40 · templada y revenida", HB=290, HRC=30, costo=1.0,
       galling="cs", cavitacion=1, erosion=1, iso15156=Nace("no", nota=_NO_EXP), iso17945=Nace("no"),
       notas=("Tuerca estándar para espárragos B7.",), fuentes=(F_PERNOS,)),
    _m("2HM", "ASTM A194 / ASME SA-194 Gr. 2HM — tuerca para servicio agrio (≤ 235 HB)",
       "Acero al carbono (tuercas)", ("cs",), PERNOS, uns="—", astm="ASTM A194 / ASME SA-194 Gr. 2HM",
       forma="Tuerca hexagonal pesada", T_min_C=-48, T_max_C=538, composicion="Como 2H, revenida a ≤ 235 HB",
       HB=235, HRC=22, costo=1.15, galling="cs", cavitacion=1, erosion=1,
       iso15156=Nace("aceptable", 22, nota="≤ 22 HRC (ISO 15156-2)."), iso17945=Nace("aceptable", 22),
       notas=("Tuerca NACE para espárragos B7M o 17-4PH H1150D.",), fuentes=(F_PERNOS, F_15156)),
    _m("G7", "ASTM A194 / ASME SA-194 Gr. 7 — tuerca Cr-Mo templada", "Acero Cr-Mo (tuercas)", ("crmo",), PERNOS,
       uns="G41400", astm="ASTM A194 / ASME SA-194 Gr. 7", forma="Tuerca hexagonal pesada", T_min_C=-101,
       T_max_C=593, composicion="AISI 4140 templado y revenido", HB=290, HRC=30, costo=1.2, galling="cs",
       cavitacion=1, erosion=1, iso15156=Nace("no", nota=_NO_EXP), iso17945=Nace("no"),
       notas=("Tuerca para B16, A453 660 y aleaciones de alta temperatura o baja temperatura (con impacto).",),
       fuentes=(F_PERNOS,)),
    _m("8M", "ASTM A194 / ASME SA-194 Gr. 8M — tuerca de inoxidable 316", "Inoxidable austenítico (tuercas)",
       ("ss316",), PERNOS, uns="S31600", astm="ASTM A194 / ASME SA-194 Gr. 8M", forma="Tuerca hexagonal pesada",
       T_min_C=-196, T_max_C=816, composicion="Cr 16–18 · Ni 10–14 · Mo 2–3", HB=190, pren=24, costo=1.8,
       galling="aus", cavitacion=2, erosion=2, iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("La variante 8MA se entrega solubilizada (carburos en solución): preferida en servicio agrio.",),
       fuentes=(F_PERNOS, F_15156)),
    _m("A2_70", "ISO 3506-1 A2-70 — perno y tuerca de inoxidable 18-8 (304)", "Inoxidable austenítico (pernos)",
       ("ss304",), PERNOS, uns="S30400", astm="ISO 3506-1 / ISO 3506-2 A2-70", forma="Perno / tuerca trabajado en frío",
       T_min_C=-196, T_max_C=400, composicion="Cr 17–19 · Ni 8–10 (tipo 304)", Rm_MPa=700, Rp_MPa=450, HRC=25,
       pren=19, costo=1.4, galling="aus", cavitacion=2, erosion=2,
       iso15156=Nace("no", nota="Trabajado en frío: no aceptable si queda expuesto."), iso17945=Nace("no"),
       notas=("Bulonería métrica inoxidable de uso general (ambiente marino moderado, alimentos).",
              "Galling alto entre perno y tuerca: lubricar con antiagarrotante."), fuentes=(F_PERNOS,)),
    _m("EN11181", "EN 10269 1.1181 (C35E) — espárrago de acero al carbono", "Acero al carbono (pernos)", ("cs",),
       PERNOS, uns="—", astm="EN 10269 1.1181 (C35E)", forma="Barra roscada templada y revenida", T_min_C=-10,
       T_max_C=350, composicion="C 0,32–0,39 · Mn 0,5–0,8", Rm_MPa=550, Rp_MPa=320, HB=170, costo=0.8,
       galling="cs", cavitacion=1, erosion=1, iso15156=Nace("sin_datos"), iso17945=Nace("sin_datos"),
       notas=("Norma europea para bulonería de equipos a presión; servicio moderado hasta unos 350 °C.",
              "Se combina con tuercas 1.0501 (C35)."), fuentes=(F_PERNOS,)),
    _m("EN10501", "EN 10269 1.0501 (C35) — tuerca de acero al carbono", "Acero al carbono (tuercas)", ("cs",),
       PERNOS, uns="—", astm="EN 10269 1.0501 (C35)", forma="Tuerca", T_min_C=-10, T_max_C=350,
       composicion="C 0,32–0,39 · Mn 0,5–0,8", HB=170, costo=0.8, galling="cs", cavitacion=1, erosion=1,
       iso15156=Nace("sin_datos"), iso17945=Nace("sin_datos"), fuentes=(F_PERNOS,)),
    _m("EN17709", "EN 10269 1.7709 (21CrMoV5-7) — espárrago Cr-Mo-V", "Acero Cr-Mo-V (pernos)", ("crmo",), PERNOS,
       uns="—", astm="EN 10269 1.7709 (21CrMoV5-7)", forma="Barra roscada templada y revenida", T_min_C=-40,
       T_max_C=540, composicion="C 0,17–0,25 · Cr 1,2–1,5 · Mo 0,65–0,8 · V 0,25–0,35", Rm_MPa=800, Rp_MPa=550,
       HRC=25, costo=1.5, galling="cs", cavitacion=1, erosion=1, iso15156=Nace("no", nota=_NO_EXP),
       iso17945=Nace("no"),
       notas=("Equivalente europeo del B16 para alta temperatura; se combina con tuercas 1.7258.",),
       fuentes=(F_PERNOS,)),
    _m("EN17258", "EN 10269 1.7258 (24CrMo5) — tuerca Cr-Mo", "Acero Cr-Mo (tuercas)", ("crmo",), PERNOS, uns="—",
       astm="EN 10269 1.7258 (24CrMo5)", forma="Tuerca templada y revenida", T_min_C=-40, T_max_C=540,
       composicion="C 0,20–0,28 · Cr 0,9–1,2 · Mo 0,2–0,3", HB=230, costo=1.3, galling="cs", cavitacion=1, erosion=1,
       iso15156=Nace("no", nota=_NO_EXP), iso17945=Nace("no"), fuentes=(F_PERNOS,)),
    _m("SAE_G5", "SAE J429 grado 5 — tornillo de cabeza de acero al medio carbono", "Acero al carbono (pernos)",
       ("cs",), PERNOS, uns="—", astm="SAE J429 Gr. 5", forma="Tornillo de cabeza hexagonal (cap screw)",
       T_min_C=-29, T_max_C=232, composicion="C 0,28–0,55 · templado y revenido", Rm_MPa=830, Rp_MPa=635, HRC=30,
       costo=0.7, galling="cs", cavitacion=1, erosion=1, iso15156=Nace("no", nota=_NO_EXP), iso17945=Nace("no"),
       notas=("Bulonería comercial: válvulas pequeñas de baja presión y servicio general.",
              "No es un grado para recipientes a presión: confirmar que el fabricante lo admite para el rating."),
       fuentes=(F_PERNOS,)),
    _m("CF10SMnN", "ASTM A351 CF10SMnN — inoxidable al Mn-Si-N fundido (tuerca prensaempaques)",
       "Inoxidable austenítico al Mn-Si", ("ss304",), PERNOS, uns="J92972", astm="ASTM A351 Gr. CF10SMnN",
       forma="Fundición", T_min_C=-196, T_max_C=425, composicion="Cr 16–18 · Ni 8–9 · Mn 7–9 · Si 3,5–4,5 · N",
       Rm_MPa=655, Rp_MPa=345, HB=200, pren=20, costo=2.0, galling="n60", cavitacion=5, erosion=4,
       iso15156=Nace("condicional", 22, 100, 60, azufre=False, nota="Austenítico solubilizado (ISO 15156-3, anexo A)."),
       iso17945=AUS_17945,
       notas=("Versión fundida del inoxidable antigalling S21800: tuercas prensaempaques roscadas que no se "
              "agarrotan contra el bonete o el vástago.",), fuentes=(F_ASTM, F_PRACTICA)),
]
# ---------------------------------------------------------------------------------------------------------------
# v0.14.1: internos de alta temperatura, resortes, juntas cuerpo-bonete y O-rings
# ---------------------------------------------------------------------------------------------------------------
RESORTE = C({"resorte"})
JUNTA = C({"junta"})
ORING = C({"oring"})
_V0141 = [
    _m("422", "Inoxidable 422 (S42200) templado — 12Cr-Mo-W-V para alta temperatura", "Inoxidable martensítico",
       ("mart",), C({"obturador", "guia", "jaula", "vastago"}), uns="S42200",
       astm="ASTM A565 Gr. 616 (AISI 422) / ASTM A437 B4B", forma="Barra / forja templada y revenida",
       T_min_C=-29, T_max_C=650, composicion="C 0,20–0,25 · Cr 11–12,5 · Mo 0,9–1,25 · W 0,9–1,25 · V 0,2–0,3 · Ni 0,5–1",
       Rm_MPa=965, Rp_MPa=760, HRC=32, pren=15, costo=1.6, galling="mart", cavitacion=5, erosion=5,
       iso15156=Nace("no", nota="Martensítico templado por encima de 22 HRC: no aceptable en servicio agrio."),
       iso17945=Nace("no"),
       notas=("Disco, obturador, guía, buje o manguito (sleeve) del disco y eje en vapor y gases calientes: conserva "
              "la resistencia hasta unos 650 °C, donde el 410 y el 17-4PH ya no sirven.",
              "En N25 el manguito (sleeve) del disco se elige como guía (cojinetes / bujes) o, en globo, como jaula.",
              "Corrosión como el 410: no apto para cloruros altos, ácidos ni servicio agrio."),
       fuentes=(F_ASTM, F_PRACTICA)),
    _m("301", "Inoxidable 301 (S30100) para resortes, laminado duro", "Inoxidable austenítico (resortes)",
       ("ss304",), RESORTE, uns="S30100", astm="ASTM A313 / A666 Tipo 301", forma="Alambre o fleje endurecido en frío",
       T_min_C=-196, T_max_C=288, composicion="C ≤ 0,15 · Cr 16–18 · Ni 6–8", Rm_MPa=1275, Rp_MPa=965, HRC=40,
       pren=17, costo=1.3, galling="aus", cavitacion=2, erosion=2,
       iso15156=Nace("no", nota="Trabajado en frío: no aceptable si el resorte queda expuesto al H₂S."),
       iso17945=Nace("no"),
       notas=("Resortes de sellos, de la empaquetadura con carga viva y resortes pequeños expuestos al ambiente.",
              "Pierde carga por relajación por encima de unos 290 °C: usar 17-7PH o aleación X-750."),
       fuentes=(F_ASTM, F_PRACTICA)),
    _m("302", "Inoxidable 302 (S30200) para resortes", "Inoxidable austenítico (resortes)", ("ss304",), RESORTE,
       uns="S30200", astm="ASTM A313 Tipo 302", forma="Alambre de resorte", T_min_C=-196, T_max_C=288,
       composicion="C ≤ 0,15 · Cr 17–19 · Ni 8–10", Rm_MPa=1400, Rp_MPa=1050, HRC=42, pren=18, costo=1.3,
       galling="aus", cavitacion=2, erosion=2, iso15156=Nace("no", nota="Trabajado en frío."), iso17945=Nace("no"),
       notas=("El alambre de resorte inoxidable más común.",), fuentes=(F_ASTM,)),
    _m("177PH", "17-7PH (S17700) CH900 para resortes", "Inoxidable PH (resortes)", ("ph",), RESORTE, uns="S17700",
       astm="ASTM A313 Tipo 631", forma="Alambre o fleje endurecido", T_min_C=-196, T_max_C=343,
       composicion="Cr 16–18 · Ni 6,5–7,75 · Al 0,75–1,5", Rm_MPa=1650, Rp_MPa=1450, HRC=45, pren=17, costo=1.8,
       galling="ph", cavitacion=3, erosion=3, iso15156=Nace("no"), iso17945=Nace("no"),
       notas=("Resortes Belleville de la empaquetadura con carga viva y resortes de mayor temperatura que el 301.",),
       fuentes=(F_ASTM,)),
    _m("X750", "Aleación X-750 (N07750) para resortes", "Aleación Ni-Cr endurecida (resortes)", ("ni600",), RESORTE,
       uns="N07750", astm="AMS 5698 / AMS 5699 (alambre)", forma="Alambre de resorte envejecido", T_min_C=-196,
       T_max_C=540, composicion="Ni ≥ 70 · Cr 14–17 · Fe 5–9 · Ti 2,25–2,75 · Al · Nb", Rm_MPa=1300, Rp_MPa=900,
       HRC=40, costo=5.0, galling="ni", cavitacion=4, erosion=4,
       iso15156=Nace("condicional", 40, nota="Resortes de X-750 con tratamiento y dureza de ISO 15156-3 (anexo A); "
                     "confirmar con la edición vigente."), iso17945=Nace("aceptable", 40),
       notas=("Resortes en servicio agrio y en alta temperatura.",), fuentes=(F_PRACTICA, F_15156)),
    _m("RES_CS", "Acero aleado para resortes (Cr-Si / Cr-V) pintado", "Acero aleado (resortes)", ("crmo",), RESORTE,
       uns="G92540 / G61500", astm="ASTM A401 (Cr-Si) / ASTM A231 (Cr-V)", forma="Alambre de resorte templado",
       T_min_C=-40, T_max_C=120, composicion="Cr 0,5–0,8 · Si 1,2–1,6 (Cr-Si)", Rm_MPa=1800, Rp_MPa=1600, HRC=50,
       costo=0.6, galling="cs", cavitacion=1, erosion=1, iso15156=Nace("no", nota="Fuera de contacto con el fluido."),
       iso17945=Nace("no"),
       notas=("Resorte estándar de los actuadores de diafragma y de pistón, protegido con pintura dentro de la "
              "carcasa (no está en contacto con el fluido).",), fuentes=(F_ASTM, F_PRACTICA)),
    _m("GRAF", "Grafito flexible (Grafoil) — junta cuerpo-bonete", "Grafito flexible", ("grafito",), JUNTA,
       uns="—", astm="ASTM F104 (grafito flexible, ≥ 98 % C)", forma="Junta laminada, con o sin inserto metálico",
       T_min_C=-200, T_max_C=450, composicion="Grafito expandido ≥ 98 %; cloruros ≤ 50 ppm (grado nuclear ≤ 25)",
       costo=1.5, galling="polimero", cavitacion=0, erosion=0, blando=True,
       iso15156=Nace("aceptable", None, nota="No metálico: fuera del alcance de la norma."),
       iso17945=Nace("aceptable", None),
       notas=("Junta estándar de alta temperatura: hasta unos 450 °C con aire u oxidantes y hasta unos 650 °C en "
              "vapor o medio inerte.", "No apta para oxidantes fuertes (ácido nítrico, oleum, cloro húmedo caliente)."),
       fuentes=(F_PRACTICA,)),
    _m("ESP_GRAF", "Espirometálica 316 con relleno de grafito flexible — junta cuerpo-bonete",
       "Junta espirometálica", ("ss316", "grafito"), JUNTA, uns="S31600 + grafito",
       astm="ASME B16.20 (espirometálica)", forma="Junta espirometálica con anillo interior", T_min_C=-200,
       T_max_C=450, composicion="Fleje 316L + relleno de grafito flexible", costo=2.0, galling="polimero",
       cavitacion=0, erosion=0, blando=True, iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Junta de bonete para presión y temperatura altas.",), fuentes=(F_PRACTICA,)),
    _m("ESP_PTFE", "Espirometálica 316 con relleno de PTFE — junta cuerpo-bonete", "Junta espirometálica",
       ("ss316", "ptfe"), JUNTA, uns="S31600 + PTFE", astm="ASME B16.20 (espirometálica)",
       forma="Junta espirometálica con anillo interior", T_min_C=-200, T_max_C=260,
       composicion="Fleje 316L + relleno de PTFE", costo=2.0, galling="polimero", cavitacion=0, erosion=0, blando=True,
       iso15156=AUS_15156, iso17945=AUS_17945,
       notas=("Para medios químicos agresivos donde el grafito no es apto.",), fuentes=(F_PRACTICA,)),
    _m("XTREME", "Fluoropolímero de alto desempeño «XTREME» (asiento blando y sellos)", "Polímero fluorado",
       ("ptfe",), C({"asiento"}) | JUNTA, uns="—", astm="Especificación del fabricante (formulación propietaria)",
       forma="Inserto de asiento / sello", T_min_C=-46, T_max_C=260,
       composicion="Fluoropolímero de formulación propietaria con mejor recuperación que el PTFE relleno",
       costo=2.5, galling="polimero", cavitacion=0, erosion=1, blando=True,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Nombre comercial de un material de asiento de un fabricante de válvulas de bola y mariposa: "
              "compatibilidad química equivalente a la del PTFE relleno y temperatura hasta unos 260 °C "
              "(rango del PEEK), con más presión admisible que el PTFE relleno a temperatura.",
              "Confirmar con el fabricante el límite de presión y temperatura del asiento ofertado."),
       fuentes=("Información técnica publicada por el fabricante del material (asientos para bola y mariposa)",)),
    _m("FFKM", "Perfluoroelastómero FFKM (O-rings y sellos)", "Elastómero perfluorado", ("ptfe",), ORING,
       forma="O-ring / sello", T_min_C=-15, T_max_C=316, composicion="Perfluoroelastómero", costo=8.0,
       galling="polimero", cavitacion=0, erosion=0, blando=True,
       iso15156=Nace("aceptable", None), iso17945=Nace("aceptable", None),
       notas=("Resistencia química casi universal, como el PTFE, con elasticidad de elastómero; muy caro.",),
       fuentes=(F_PRACTICA,)),
]
MATERIALES.update({m.clave: m for m in _PERNOS + _V0141})
# Materiales de internos y vástagos que también se usan como espárragos y tuercas
for _k in ("N50", "718", "A286", "174_H1150D", "C276", "M400", "A20", "B2", "304", "316"):
    MATERIALES[_k] = replace(MATERIALES[_k], componentes=MATERIALES[_k].componentes | PERNOS)
# Polímeros que también son juntas cuerpo-bonete (PTFE relleno) u O-rings (elastómeros)
for _k, _c in (("RPTFE", JUNTA), ("PTFE", JUNTA), ("EPDM", ORING), ("FKM", ORING), ("NBR", ORING)):
    MATERIALES[_k] = replace(MATERIALES[_k], componentes=MATERIALES[_k].componentes | _c)
# Componentes que no elige el motor de materiales (se eligen en 1-Sistema); solo para la ficha de la biblioteca
COMPONENTES_EXTRA = {"pernos": "Pernos, espárragos y tuercas", "junta": "Junta cuerpo-bonete", "oring": "O-rings",
                     "resorte": "Resortes"}

CUERPOS = [k for k, m in MATERIALES.items() if "cuerpo" in m.componentes]


def para_componente(componente: str) -> list[Material]:
    """Materiales admitidos para un componente, del más económico al más caro."""
    return sorted((m for m in MATERIALES.values() if componente in m.componentes), key=lambda m: m.costo)


def _sin_tildes(t: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def buscar(texto: str) -> list[Material]:
    """Búsqueda por clave, nombre, UNS, ASTM, familia o componente, sin distinguir tildes ni guiones
    («duplex», «super duplex» y «superdúplex» encuentran lo mismo)."""
    t = _sin_tildes(texto).replace("-", " ").strip()
    if not t:
        return list(MATERIALES.values())
    nombres = {**COMPONENTES, **COMPONENTES_ROTATIVA, **COMPONENTES_EXTRA}
    out = []
    for m in MATERIALES.values():
        base = _sin_tildes(" ".join((m.clave, m.nombre, m.uns, m.astm, m.familia, m.equivalente,
                                     *(nombres.get(c, "") for c in m.componentes)))).replace("-", " ")
        if t in base or t.replace(" ", "") in base.replace(" ", ""):
            out.append(m)
    return out


def ficha(m: Material) -> list[tuple[str, str]]:
    """Ficha técnica completa (pares etiqueta, valor)."""
    def num(v, u):
        return "—" if v is None else f"{v:.0f} {u}"

    def nace(n: Nace):
        partes = {"aceptable": "Aceptable", "condicional": "Aceptable con límites", "no": "No aceptable",
                  "sin_datos": "Sin datos"}[n.estado]
        if n.dureza_max_HRC:
            partes += f" · ≤ {n.dureza_max_HRC:.0f} HRC"
        if n.pH2S_max_kPa:
            partes += f" · pH₂S ≤ {n.pH2S_max_kPa:g} kPa"
        if n.T_max_C:
            partes += f" · T ≤ {n.T_max_C:.0f} °C"
        if n.pH_min:
            partes += f" · pH ≥ {n.pH_min:g}"
        return partes + (f". {n.nota}" if n.nota else "")

    nombres = {**COMPONENTES, **COMPONENTES_EXTRA}
    usos = ", ".join(nombres[c] for c in nombres if c in m.componentes)
    filas = [("Designación", m.nombre), ("Familia", m.familia), ("UNS", m.uns or "—"),
             ("Especificación", m.astm or "—"), ("Forma de producto", m.forma or "—"),
             ("Equivalente", m.equivalente or "—"),
             ("Grupo ASME B16.34", (m.grupo + (" (por el forjado equivalente)" if m.grupo_equivalente else ""))
              if m.grupo else ("No aplica" if m.componentes <= PERNOS | JUNTA | ORING | RESORTE else
                               "No incluido en las tablas")),
             ("Temperatura de uso", f"{m.T_min_C:.0f} °C a {m.T_max_C:.0f} °C"),
             ("Composición nominal [%]", m.composicion or "—"),
             ("Resistencia a la tracción", num(m.Rm_MPa, "MPa")), ("Límite de fluencia", num(m.Rp_MPa, "MPa")),
             ("Dureza típica", m.dureza_txt), ("PREN", "—" if m.pren is None else f"{m.pren:.0f}"),
             ("Índice de costo", f"{m.costo:g}"), ("Componentes", usos),
             ("Resistencia a cavitación (0–10)", str(m.cavitacion)), ("Resistencia a erosión (0–10)", str(m.erosion)),
             ("ISO 15156 / MR0175", nace(m.iso15156)), ("ISO 17945 / MR0103", nace(m.iso17945))]
    filas += [("Nota", n) for n in m.notas]
    filas.append(("Fuentes", "; ".join(m.fuentes) or "—"))
    return filas
