"""Pernos y tuercas cuerpo-bonete y espárragos y tuercas de la brida prensaempaques (v0.14.0).

Cada opción del desplegable de 1-Sistema nombra el espárrago (o tornillo), la tuerca y, en la brida
prensaempaques, el material de la brida. Los materiales están en la biblioteca (``materiales.py``). El
programa verifica la temperatura de uso de cada pieza y, en servicio agrio, si la combinación es apta según
ISO 15156; no calcula la junta (precarga, cantidad ni diámetro de pernos), que es del fabricante.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import materiales as MT
from .modelos import Alerta, Severidad

ESTANDAR = "estandar"
REF_PERNOS = "ASTM A193 / A194 (ASME SA-193 / SA-194), EN 10269, ISO 3506-1; ISO 15156-2 / -3 (servicio agrio)"


@dataclass(frozen=True)
class OpcionPernos:
    clave: str
    nombre: str
    esparrago: str = ""          # clave de materiales.MATERIALES ("" = estándar del fabricante)
    tuerca: str = ""
    brida: str = ""              # brida prensaempaques: material (texto) cuando la opción lo define
    lubricado: bool = False
    nota: str = ""

    @property
    def piezas(self) -> list[tuple[str, MT.Material]]:
        out = []
        if self.esparrago:
            out.append(("Espárragos" if self.esparrago != "SAE_G5" else "Tornillos", MT.MATERIALES[self.esparrago]))
        if self.tuerca:
            out.append(("Tuercas" if self.clave != "cf10smnn" else "Tuerca prensaempaques",
                        MT.MATERIALES[self.tuerca]))
        return out

    @property
    def detalle(self) -> str:
        """Especificación de cada pieza (descripción emergente del desplegable)."""
        if not self.piezas:
            return "El fabricante de la válvula elige los pernos y tuercas según su estándar."
        det = "; ".join(f"{n}: {m.nombre}" for n, m in self.piezas)
        return det + (f"; brida de {self.brida}" if self.brida else "") + (
            "; montaje con lubricante antiagarrotante" if self.lubricado else "") + (f". {self.nota}" if self.nota else "")


def _o(*a, **k):
    return OpcionPernos(*a, **k)


CUERPO_BONETE = {o.clave: o for o in [
    _o(ESTANDAR, "Estándar del fabricante"),
    _o("en1181", "EN 1.1181 espárragos / EN 1.0501 tuercas", "EN11181", "EN10501"),
    _o("en1181_lub", "EN 1.1181 espárragos / EN 1.0501 tuercas, lubricados", "EN11181", "EN10501", lubricado=True),
    _o("en17709_lub", "EN 1.7709 espárragos / EN 1.7258 tuercas, lubricados", "EN17709", "EN17258", lubricado=True),
    _o("a2_70", "A2-70 espárragos / A2-70 tuercas", "A2_70", "A2_70"),
    _o("a2_70_lub", "A2-70 espárragos / A2-70 tuercas, lubricados", "A2_70", "A2_70", lubricado=True),
    _o("sae5", "Tornillos de cabeza SAE grado 5", "SAE_G5", ""),
    _o("xm19", "Nitronic 50 (XM-19) espárragos y tuercas", "N50", "N50"),
    _o("n07718_cr", "N07718 tratado térmicamente y cromado / tuercas grado 7", "718", "G7",
       nota="Espárrago de aleación 718 envejecido con recubrimiento de cromo (antigalling)."),
    _o("s20910_8ma", "S20910 (XM-19) espárragos / tuercas 8MA, NACE", "N50", "8M",
       nota="Tuercas 8MA: 316 solubilizado (carburos en solución)."),
    _o("s20910_8m", "S20910 (XM-19) espárragos / tuercas 8M", "N50", "8M"),
    _o("b16_7", "SA-193 B16 espárragos / tuercas grado 7", "B16", "G7"),
    _o("b7_2h", "SA-193 B7 espárragos / tuercas 2H", "B7", "2H"),
    _o("b7_2h_lub", "SA-193 B7 espárragos / tuercas 2H, lubricados", "B7", "2H", lubricado=True),
    _o("b7m_2hm", "SA-193 B7M espárragos / tuercas 2HM, NACE", "B7M", "2HM"),
    _o("b8m2_8m", "SA-193 B8M endurecido por deformación (Clase 2) espárragos / tuercas 8M", "B8M2", "8M"),
    _o("b8m_8m", "SA-193 B8M espárragos / tuercas 8M", "B8M1", "8M"),
    _o("b8m_8m_c", "SA-193 B8M / 8M", "B8M1", "8M"),
    _o("b8m_cr_8m", "SA-193 B8M con cromo delgado denso / tuercas 8M", "B8M_CR", "8M"),
    _o("a453_660_7", "SA-453 grado 660 espárragos / tuercas grado 7", "A286", "G7"),
    _o("a479_cr_7", "SA-479 inoxidable cromado espárragos / tuercas grado 7", "316", "G7",
       nota="Espárrago de barra inoxidable ASME SA-479 con recubrimiento de cromo; confirmar el grado del "
            "inoxidable con el fabricante (N25 lo verifica como 316)."),
    _o("a564_630_2hm", "SA-564 630 (17-4PH H1150D) espárragos / tuercas 2HM, NACE", "174_H1150D", "2HM"),
    _o("c276", "SB-564 N10276 (C-276) espárragos y tuercas", "C276", "C276"),
]}

PRENSAEMPAQUES = {o.clave: o for o in [
    _o(ESTANDAR, "Estándar del fabricante"),
    _o("cf10smnn", "Tuerca prensaempaques de CF10SMnN", "", "CF10SMnN",
       nota="Prensaempaques con tuerca roscada (sin brida ni espárragos)."),
    _o("n04400", "N04400 (Monel 400) espárragos y tuercas", "M400", "M400"),
    _o("n08020", "N08020 (Aleación 20) espárragos y tuercas", "A20", "A20"),
    _o("n10276", "N10276 (C-276) espárragos y tuercas", "C276", "C276"),
    _o("n10665", "N10665 (B-2) espárragos y tuercas", "B2", "B2"),
    _o("s30400", "S30400 (304) espárragos y tuercas", "304", "304"),
    _o("brida316_b8m", "Brida de 316 con espárragos B8M / tuercas 8M", "B8M1", "8M", brida="inoxidable 316 (S31600)"),
    _o("b7m_2hm", "SA-193 B7M espárragos / tuercas 2HM, NACE", "B7M", "2HM"),
    _o("sst", "Brida, espárragos y tuercas de inoxidable", "B8M1", "8M", brida="inoxidable",
       nota="N25 verifica los espárragos y tuercas como B8M / 8M; confirmar el grado con el fabricante."),
    _o("acero_b7", "Brida de acero con espárragos SA-193 B7 / tuercas 2H", "B7", "2H", brida="acero"),
    _o("acero_sst", "Brida de acero con espárragos y tuercas de inoxidable", "B8M1", "8M", brida="acero",
       nota="N25 verifica los espárragos y tuercas como B8M / 8M; confirmar el grado con el fabricante."),
    _o("acero", "Brida, espárragos y tuercas de acero", "B7", "2H", brida="acero",
       nota="N25 verifica los espárragos y tuercas como B7 / 2H; confirmar el grado con el fabricante."),
]}


def opcion(tabla: dict, nombre_o_clave: str) -> OpcionPernos:
    """Opción por clave o por nombre (los proyectos guardan el texto del desplegable)."""
    if nombre_o_clave in tabla:
        return tabla[nombre_o_clave]
    return next((o for o in tabla.values() if o.nombre == nombre_o_clave), tabla[ESTANDAR])


def nace_ok(o: OpcionPernos) -> bool | None:
    """True si todas las piezas son aceptables en ISO 15156; None si es el estándar del fabricante."""
    if not o.piezas:
        return None
    return all(m.iso15156.estado in ("aceptable", "condicional") for _, m in o.piezas)


def alertas(bonete: OpcionPernos, prensa: OpcionPernos, T_max_C: float, T_min_C: float,
            agrio: bool) -> list[Alerta]:
    """Temperatura de uso de cada pieza y aptitud en servicio agrio."""
    out = []
    for lugar, o, codigo in (("cuerpo-bonete", bonete, "pernos_bonete"),
                             ("de la brida prensaempaques", prensa, "pernos_prensa")):
        for pieza, m in o.piezas:
            if T_max_C > m.T_max_C + 1e-6 or T_min_C < m.T_min_C - 1e-6:
                out.append(Alerta(
                    codigo + "_temperatura", Severidad.ADVERTENCIA, f"Pernos {lugar} fuera de su temperatura",
                    f"{pieza} {m.astm}: uso de {m.T_min_C:.0f} °C a {m.T_max_C:.0f} °C y el servicio va de "
                    f"{T_min_C:.0f} °C a {T_max_C:.0f} °C. Los pernos trabajan cerca de la temperatura del fluido "
                    "(los de la brida prensaempaques algo por debajo).",
                    remedios=["Elegir otra combinación de espárragos y tuercas en 1-Sistema.",
                              "Por encima de 450 °C: B16, A453 660 o aleación 718; por debajo de −48 °C: B8M / 8M o "
                              "aceros con ensayo de impacto (L7 / 7L)."], referencia=REF_PERNOS))
        if agrio and nace_ok(o) is False:
            malos = ", ".join(f"{p.lower()} {m.astm}" for p, m in o.piezas
                              if m.iso15156.estado not in ("aceptable", "condicional"))
            out.append(Alerta(
                codigo + "_nace", Severidad.ADVERTENCIA, f"Pernos {lugar} no aptos para servicio agrio",
                f"El servicio es agrio y {malos} no son aceptables según ISO 15156 cuando quedan expuestos al H₂S "
                "(aislación térmica, cubiertas o una fuga que los moje). Sin exposición se admiten.",
                remedios=["Usar B7M / 2HM, B8M Clase 1 / 8M(A) o 17-4PH H1150D / 2HM si los pernos pueden quedar "
                          "expuestos.", "Confirmar con el usuario final si los pernos quedan expuestos."],
                referencia=REF_PERNOS))
    return out
