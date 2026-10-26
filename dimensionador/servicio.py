"""Orquestación del cálculo: varios casos de operación, selección de tamaño y alertas.

Es la capa que usa la interfaz gráfica. Recibe datos ya convertidos a
unidades base (ver ``unidades.py``).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from . import anticavitacion, asme_b16_34, fenomenos, propiedades, ruido
from .estilos import ESTILOS, TAMANOS, EstiloValvula, apertura_requerida, espesor_pared, kv_nominal
from .unidades import kv_a_cv
from .iec60534_2_1 import (Bifasico, CapacidadInsuficiente, Gas, Liquido, Resultado, Valvula,
                           dimensionar_bifasico, dimensionar_gas, dimensionar_liquido, factor_FLP,
                           factor_FP)
from .modelos import _n, Alerta, ErrorDatos, Severidad

APERTURA_MAX_SELECCION = 0.85   # criterio de selección automática (caso máximo)


@dataclass
class Caso:
    nombre: str                    # «Mínimo», «Normal», «Máximo»...
    estado: Liquido | Gas | Bifasico
    fluido: str | None = None      # nombre para propiedades (flashing)
    FL: float | None = None        # factores a la carrera de este caso (sustituyen a los de la selección)
    Fd: float | None = None
    xT: float | None = None
    Kc: float | None = None        # cavitación constante del trim a las condiciones del caso (fabricante)
    xFz: float | None = None       # inicio de cavitación incipiente del fabricante (IEC 60534-8-2, 6 bar)
    criterio: bool = True          # participa del criterio de selección de tamaño
    etapas: int = 1                # etapas del trim anticavitación (líquidos); el ruido sale de la última


@dataclass
class Seleccion:
    estilo: EstiloValvula
    d_pulg: float | None = None            # None = selección automática
    Kv_nominal: float | None = None        # None = valor típico del estilo
    D1_mm: float | None = None             # None = igual a la válvula
    D2_mm: float | None = None
    FL: float | None = None                # sustituyen los típicos del estilo
    xT: float | None = None
    Fd: float | None = None
    xFz: float | None = None
    C_api14e: float = 100.0
    tp_mm: float | None = None             # espesor de pared de la tubería de salida
    c_liquido: float | None = None         # velocidad del sonido en el líquido [m/s]
    limite_ruido: float = 85.0             # dB(A)
    calcular_ruido: bool = True
    material: str = "WCB"                  # clave de asme_b16_34.MATERIALES
    clase: int | None = None               # None = clase mínima que cumple
    P_diseno: float | None = None          # kPa abs; None = máxima P1 de los casos
    T_diseno: float | None = None          # K; None = máxima T1 de los casos
    tamanos: tuple | None = None           # diámetros admitidos en selección automática [pulg]
    An: float | None = None                # coeficiente acústico IEC 60534-8-4
    verificar_clase: bool = True


@dataclass
class ResultadoCaso:
    caso: Caso
    resultado: Resultado
    apertura: float
    alertas: list[Alerta]
    datos: dict


@dataclass
class Informe:
    d_pulg: float
    DN: int
    Kv_nominal: float
    valvula: Valvula
    casos: list[ResultadoCaso]
    tabla_tamanos: list[dict] = field(default_factory=list)
    alertas_generales: list[Alerta] = field(default_factory=list)
    clase: int | None = None
    rating_barg: float | None = None
    P_diseno_barg: float | None = None
    T_diseno_C: float | None = None

    def todas_las_alertas(self) -> list[tuple[str, Alerta]]:
        out = [("General", a) for a in self.alertas_generales]
        for rc in self.casos:
            out += [(rc.caso.nombre, a) for a in rc.alertas]
        return sorted(out, key=lambda t: -t[1].severidad)


def _dn(d_pulg: float) -> int:
    for p, dn, _ in TAMANOS:
        if abs(p - d_pulg) < 1e-6:
            return dn
    return round(d_pulg * 25)


def _valvula(sel: Seleccion, d_pulg: float) -> Valvula:
    d_mm = d_pulg * 25.4
    return Valvula(FL=sel.FL or sel.estilo.FL, xT=sel.xT or sel.estilo.xT,
                   Fd=sel.Fd or sel.estilo.Fd, d_mm=d_mm,
                   D1_mm=sel.D1_mm if sel.D1_mm else None,
                   D2_mm=sel.D2_mm if sel.D2_mm else None)


def _calcular_caso(caso: Caso, v: Valvula, sel: Seleccion, Kv_nom: float) -> ResultadoCaso:
    e = caso.estado
    if caso.FL or caso.Fd or caso.xT:
        v = replace(v, FL=caso.FL or v.FL, Fd=caso.Fd or v.Fd, xT=caso.xT or v.xT)
    if isinstance(e, Bifasico):
        r = dimensionar_bifasico(e, v)
        alertas = list(r.alertas)
        rho2 = e.densidad_homogenea(e.P2)
        Q2 = e.W / rho2
        v_valv = Q2 / 3600 / (fenomenos.area_mm2(v.d_mm) * 1e-6)
        D2 = v.D2_mm or v.d_mm
        v_tub = Q2 / 3600 / (fenomenos.area_mm2(D2) * 1e-6)
        datos = {"rho_mezcla_entrada": e.densidad_homogenea(), "rho_mezcla_salida": rho2,
                 "v_salida_valvula": v_valv, "v_tuberia_salida": v_tub,
                 "v_erosional_api14e": fenomenos.velocidad_erosional_api14e(rho2, sel.C_api14e)}
        alertas += fenomenos.evaluar_erosional(v_valv, rho2, "la salida de la válvula", sel.C_api14e)
        alertas += fenomenos.evaluar_erosional(v_tub, rho2, "la tubería de salida", sel.C_api14e)
        if sel.calcular_ruido:
            alertas.append(Alerta("ruido_no_calculado", Severidad.INFO, "Ruido no calculado en bifásico",
                                  "Las normas IEC 60534-8 no cubren el ruido de flujos bifásicos."))
        h = _apertura(r, Kv_nom, sel, caso, datos, alertas)
        return ResultadoCaso(caso, r, h, alertas, datos)
    if isinstance(e, Liquido):
        r = dimensionar_liquido(e, v)
        alertas = list(r.alertas)
        FL_eff = factor_FLP(r.Kv, v) / factor_FP(r.Kv, v)
        q = None
        if e.P2 <= e.Pv and caso.fluido:
            q = propiedades.calidad_isoentalpica(caso.fluido, e.P1, e.T1, e.P2)
        xFz = caso.xFz if caso.xFz is not None else sel.xFz
        if xFz is None and caso.Kc is not None and "multietapa" in sel.estilo.clave:
            # La estimación típica de IEC 60534-8-4 es de etapa simple: en un multietapa el inicio
            # de cavitación se toma igual al Kc del trim.
            xFz = caso.Kc / (6e5 / (e.P1 * 1000)) ** 0.125
        a, datos = fenomenos.evaluar_liquido(e.P1, e.P2, e.Pv, FL_eff, r.Kv, v.Fd,
                                             r.extra["dPchoked"], xFz, q, caso.Kc)
        alertas += a
        bif = e.P2 <= e.Pv
        a, dv = fenomenos.evaluar_velocidad_liquido(r.extra["Q"], v.d_mm, v.D2_mm, e.rho1, bif)
        alertas += a
        datos.update(dv)
        if bif and q is not None and caso.fluido:
            rho_m = propiedades.densidad_bifasica(caso.fluido, e.P2, q)
            if rho_m:
                D2 = v.D2_mm or v.d_mm
                W = r.extra["Q"] * e.rho1
                v_tub = W / 3600 / rho_m / (fenomenos.area_mm2(D2) * 1e-6)
                datos.update({"calidad_salida": q, "rho_mezcla_salida": rho_m,
                              "v_tuberia_salida": v_tub,
                              "v_erosional_api14e": fenomenos.velocidad_erosional_api14e(rho_m, sel.C_api14e)})
                alertas += fenomenos.evaluar_erosional(v_tub, rho_m, "la tubería de salida",
                                                       sel.C_api14e)
    else:
        r = dimensionar_gas(e, v)
        alertas = list(r.alertas)
        a, datos = fenomenos.evaluar_gas(e.P1, e.P2, e.T1, e.M, e.gamma, e.Z, r.extra["W"],
                                         v.d_mm, v.D2_mm, r.extra["x"], r.extra["xchoked"])
        alertas += a
        if "v_tuberia_salida" in datos:
            datos["v_erosional_api14e"] = fenomenos.velocidad_erosional_api14e(datos["rho2"], sel.C_api14e)
            alertas += fenomenos.evaluar_erosional(datos["v_tuberia_salida"], datos["rho2"],
                                                   "la tubería de salida", sel.C_api14e)
    if sel.calcular_ruido:
        try:
            alertas += _ruido(caso, r, v, sel, datos)
        except (ValueError, ZeroDivisionError, OverflowError) as ex:
            alertas.append(Alerta("ruido_no_calculado", Severidad.INFO, "Ruido no calculado",
                                  f"No se pudo estimar el ruido con estos datos ({ex})."))
    h = _apertura(r, Kv_nom, sel, caso, datos, alertas)
    return ResultadoCaso(caso, r, h, alertas, datos)


def _apertura(r: Resultado, Kv_nom: float, sel: Seleccion, caso: Caso, datos: dict, alertas: list) -> float:
    """Apertura requerida y, si el Cv pedido queda por debajo del mínimo controlable (Cv nominal/R en las
    características lineal e isoporcentual), la marca para que no se lea como «0 %» de apertura."""
    car, R = sel.estilo.caracteristica, sel.estilo.rangeabilidad
    h = apertura_requerida(r.Kv / Kv_nom, car, R)
    Kv_min = Kv_nom / R if car in ("lineal", "isoporcentual") else 0.0
    bajo = r.Kv > 0 and r.Kv < Kv_min
    datos["bajo_cv_minimo"] = bajo
    datos["Cv_minimo"] = kv_a_cv(Kv_min) if Kv_min else None
    alertas += fenomenos.evaluar_apertura(h, car, caso.nombre.lower(),
                                          (kv_a_cv(r.Kv), kv_a_cv(Kv_min), R) if bajo else None)
    return h


def _ruido(caso: Caso, r: Resultado, v: Valvula, sel: Seleccion, datos: dict) -> list[Alerta]:
    e = caso.estado
    Di_mm = v.D2_mm or v.d_mm
    tp_mm = sel.tp_mm or espesor_pared(Di_mm)
    FL_eff = factor_FLP(r.Kv, v) / factor_FP(r.Kv, v)
    if isinstance(e, Liquido):
        if e.P2 <= e.Pv:
            return [Alerta("ruido_no_calculado", Severidad.INFO, "Ruido no calculado en flashing",
                           "IEC 60534-8-4 no cubre el flujo con flashing; el ruido de un servicio "
                           "bifásico no se puede predecir con la norma.", referencia=ruido.REF8_4)]
        c_liq = sel.c_liquido
        if c_liq is None and caso.fluido:
            c_liq = propiedades.velocidad_sonido(caso.fluido, e.P1, e.T1)
        c_liq = c_liq or 1400.0
        An = sel.An if sel.An is not None else (-4.3 if "mariposa" in sel.estilo.clave else -4.6)
        # Inicio de cavitación para el ruido: el Kc del trim (valor de fabricante a las condiciones de
        # servicio, el mismo que usa la alerta de cavitación); sin Kc, el xFz típico de IEC 60534-8-4.
        if not datos["Kc_estimado"]:
            xFz = datos["Kc"] / (6e5 / (e.P1 * 1000)) ** 0.125
        else:
            xFz = None if datos["xFz_estimado"] else datos["xFz"]
        P1_r, Kv_r, FL_r = e.P1, r.Kv, FL_eff
        if caso.etapas > 1:
            # Multietapa: el ruido que sale a la tubería es el de la última etapa (IEC 60534-8-4 aplicada
            # a esa etapa); las anteriores quedan atenuadas dentro del trim.
            P1_r, _, dP_r = anticavitacion.reparto(e.P1, e.P2, e.Pv, caso.etapas)[-1]
            Kv_r = r.Kv * ((e.P1 - e.P2) / dP_r) ** 0.5
            FL_r = anticavitacion.FL_ETAPA
            xFz = anticavitacion.KC_ETAPA / (6e5 / (P1_r * 1000)) ** 0.125
            datos["ruido_P1_etapa_final"] = P1_r
        res = ruido.ruido_liquido(r.extra["Q"] * e.rho1 / 3600, P1_r, e.P2, e.Pv, e.rho1, c_liq, Kv_r,
                                  v.d_mm / 1000, Di_mm / 1000, tp_mm / 1000, FL_r, v.Fd,
                                  xFz=xFz, An=An)
        gas = False
    else:
        res = ruido.ruido_gas(r.extra["W"] / 3600, e.P1, e.P2, e.T1, r.extra["rho1"], e.gamma, e.M,
                              r.Kv, v.d_mm / 1000, Di_mm / 1000, tp_mm / 1000, v.Fd, FL_eff)
        gas = True
    datos["ruido_LpAe1m"] = res["LpAe1m"]
    datos["ruido_fp"] = res["fp"]
    datos["ruido_tp_mm"] = tp_mm
    if gas:
        datos["ruido_regimen"] = res["regimen_nombre"]
    r.memoria.agregar("—", "Predicción de ruido " + (ruido.REF8_3 if gas else ruido.REF8_4), float("nan"))
    r.memoria.pasos.extend(res["memoria"].pasos)
    nota = ""
    if not gas and caso.etapas > 1:
        nota = f" Ruido de la última de las {caso.etapas} etapas del trim anticavitación."
    elif not gas and res["cavitante"] and datos["Kc_estimado"]:
        nota = (" El nivel incluye ruido de cavitación calculado con el xFz típico de IEC 60534-8-4 "
                f"(xFzp1 = {_n(datos['xFzp1'], 3)}), que es conservador porque no se ingresó Kc.")
    return ruido.evaluar_ruido(res["LpAe1m"], gas, sel.limite_ruido, nota)


def dimensionar(casos: list[Caso], sel: Seleccion) -> Informe:
    if not casos:
        raise ErrorDatos([Alerta("sin_casos", Severidad.ERROR, "Sin casos de operación",
                                 "Ingrese al menos un caso de operación.")])
    tabla = []
    elegido = None
    evaluados = []
    tamanos = [t for t in TAMANOS if sel.tamanos is None or t[0] in sel.tamanos] if sel.d_pulg is None else [
        next((t for t in TAMANOS if abs(t[0] - sel.d_pulg) < 1e-6), (sel.d_pulg, _dn(sel.d_pulg), None))]
    for d_pulg, dn, _ in tamanos:
        if sel.d_pulg is None:
            # En selección automática no se evalúan válvulas mayores que la línea
            linea = min([x for x in (sel.D1_mm, sel.D2_mm) if x] or [1e9])
            if d_pulg * 25.4 > linea * 1.05:
                continue
        v = _valvula(sel, d_pulg)
        Kv_nom = sel.Kv_nominal if (sel.Kv_nominal and sel.d_pulg) else kv_nominal(sel.estilo, d_pulg)
        evaluados.append((d_pulg, dn))
        try:
            rcs = [_calcular_caso(c, v, sel, Kv_nom) for c in casos]
        except CapacidadInsuficiente:
            if sel.d_pulg is not None:
                raise
            tabla.append({"d_pulg": d_pulg, "DN": dn, "Kv_nominal": Kv_nom, "Kv_max": None,
                          "apertura_max": None, "aperturas": []})
            continue
        h_max = max([rc.apertura for rc in rcs if rc.caso.criterio] or [0.0])
        tabla.append({"d_pulg": d_pulg, "DN": dn, "Kv_nominal": Kv_nom,
                      "Kv_max": max(rc.resultado.Kv for rc in rcs), "apertura_max": h_max,
                      "aperturas": [rc.apertura for rc in rcs]})
        if elegido is None and (sel.d_pulg is not None or h_max <= APERTURA_MAX_SELECCION):
            elegido = (d_pulg, dn, Kv_nom, v, rcs)
    generales = []
    if elegido is None:
        # El mayor diámetro evaluado (no mayor que la línea en selección automática)
        d_pulg, dn = (evaluados or [(tamanos[-1][0], tamanos[-1][1])])[-1]
        v = _valvula(sel, d_pulg)
        Kv_nom = kv_nominal(sel.estilo, d_pulg)
        try:
            rcs = [_calcular_caso(c, v, sel, Kv_nom) for c in casos]
        except CapacidadInsuficiente as e:
            raise ErrorDatos([Alerta("sin_tamano", Severidad.ERROR, "Ningún tamaño es suficiente",
                                     str(e))]) from None
        elegido = (d_pulg, dn, Kv_nom, v, rcs)
        generales.append(Alerta("sin_tamano", Severidad.CRITICA, "Ningún tamaño es suficiente",
                                "Ningún diámetro evaluado cubre el caudal máximo con apertura "
                                f"≤ {_n(APERTURA_MAX_SELECCION * 100, 0)} %.",
                                remedios=["Revise el diámetro de la tubería, el estilo de válvula "
                                          "o considere válvulas en paralelo."]))
    d_pulg, dn, Kv_nom, v, rcs = elegido
    if sel.Kv_nominal is None:
        generales.append(Alerta("kv_tipico", Severidad.INFO, "Capacidad nominal típica",
                                "La capacidad nominal de la válvula es un valor típico del estilo, "
                                "no de un fabricante. Reemplácela por el valor certificado de la "
                                "válvula ofertada para verificar la apertura real."))
    if not sel.verificar_clase:
        return Informe(d_pulg, dn, Kv_nom, v, rcs, tabla, generales)
    # Clase de presión ASME B16.34
    P_d = sel.P_diseno or max(c.estado.P1 for c in casos)
    T_d = sel.T_diseno or max(c.estado.T1 for c in casos)
    T_min = min(c.estado.T1 for c in casos)
    P_barg = (P_d - 101.325) / 100
    clase, rat, a_clase = asme_b16_34.verificar(sel.material, sel.clase, P_barg, T_d - 273.15,
                                                 min(T_min, T_d) - 273.15)
    generales += a_clase
    if sel.P_diseno is None or sel.T_diseno is None:
        generales.append(Alerta("diseno_por_operacion", Severidad.INFO, "Condiciones de diseño supuestas",
                                "La clase de presión se verificó con la máxima presión y temperatura de "
                                "operación. Ingrese la presión y temperatura de diseño de la línea para "
                                "una verificación formal."))
    return Informe(d_pulg, dn, Kv_nom, v, rcs, tabla, generales, clase, rat, P_barg, T_d - 273.15)
