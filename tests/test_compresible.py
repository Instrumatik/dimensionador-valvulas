"""Gas, vapor y vapor de agua: validación contra IEC 60534-2-1 y contra una
implementación independiente (biblioteca «fluids», C. Bell, MIT) cuando está instalada."""
import math

import pytest

from dimensionador import compresible as CG, ruido
from dimensionador.proyecto import (CasoCierre, CasoGas, Dimensionamiento, Identificacion, Instalacion,
                                    RuidoAerodinamico, calcular)

TRIM = "globo_contorneado_iso_abre"


def _co2(**k):
    base = dict(nombre="Normal", W=None, QN=3800, P1=680, P2=310, T1=433, M=44.01, mu=1.59e-5,
                gamma=1.30, Z1=0.988, xT=0.60, FL=0.85, Fd=0.42)
    base.update(k)
    return CasoGas(**base)


def test_ejemplo3_iec_gas_por_el_flujo_completo():
    r = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                 Dimensionamiento([_co2()], None, TRIM, nps_valvula=4, tipo="gas"))
    s = r.salidas[0]
    assert s["Kv"] == pytest.approx(62.7, rel=3e-3)
    assert s["Y"] == pytest.approx(0.674, abs=1e-3)
    assert s["xchoked"] == pytest.approx(0.557, abs=5e-4)
    assert s["dPchoked"] == pytest.approx(0.557 * 680, rel=2e-3)
    assert not s["bloqueado"]
    # Caudal opuesto al ingresado: másico = QN·ρN
    assert s["W"] == pytest.approx(3800 * 101.325 * 44.01 / (8.314462618 * 273.15), rel=1e-9)


@pytest.mark.parametrize("P2,nps_v,nps_l", [(310, 4, 4), (150, 3, 6), (500, 3, 4), (100, 6, 8)])
def test_dimensionamiento_gas_contra_fluids(P2, nps_v, nps_l):
    fl = pytest.importorskip("fluids.control_valve")
    from dimensionador import tuberias
    c = _co2(P2=P2, QN=None, W=9000)
    r = calcular(Identificacion(), Instalacion(nps_entrada=nps_l, nps_salida=nps_l),
                 Dimensionamiento([c], None, TRIM, nps_valvula=nps_v, tipo="gas"))
    s = r.salidas[0]
    D = tuberias.diametro_interior(nps_l, "40") / 1000
    Kv = fl.size_control_valve_g(T=433, MW=44.01, mu=1.59e-5, gamma=1.30, Z=0.988, P1=680e3, P2=P2 * 1e3,
                                 Q=9000 / CG.densidad_normal(44.01) / 3600, D1=D, D2=D, d=nps_v * 0.0254, FL=0.85, Fd=0.42, xT=0.60)
    # Con reductores la norma itera hasta que Ci/C ≥ 0,99 (cláusula 8), la tolerancia que aplica «fluids»;
    # el programa resuelve la ecuación en forma exacta, así que coinciden dentro de 1 %.
    assert s["Kv"] == pytest.approx(Kv, rel=1e-2 if nps_v != nps_l else 2e-3)
    # Verificación exacta: el Kv obtenido pasa el caudal de diseño con las ecuaciones de IEC
    from dimensionador.iec60534_2_1 import Gas, Valvula, caudal_gas
    v = Valvula(0.85, 0.60, 0.42, nps_v * 25.4, D * 1000, D * 1000)
    g = Gas(P1=680, P2=P2, T1=433, M=44.01, gamma=1.30, Z=0.988, mu=1.59e-5, W=9000)
    assert caudal_gas(s["Kv"], g, v) == pytest.approx(9000, rel=1e-6)


@pytest.mark.parametrize("P2", [700, 480, 300, 150])
def test_ruido_gas_contra_fluids(P2):
    fl = pytest.importorskip("fluids.control_valve")
    args = (2.2, 1000e3, P2 * 1e3, 450, 5.3, 1.22, 19.8, 90 * 0.865, 0.1, 0.2031, 0.008, 0.296, 0.792 / 0.98)
    ref = fl.control_valve_noise_g_2011(*args[:12], FL=args[12], rho_pipe=7800.0, An=-3.8)
    r = ruido.ruido_gas(2.2, 1000, P2, 450, 5.3, 1.22, 19.8, 90 * 0.865, 0.1, 0.2031, 0.008, 0.296,
                        0.792 / 0.98)
    assert r["LpAe1m"] == pytest.approx(ref, abs=0.01)
    # Componentes: la suma energética de trim y salida es el total
    tot = [r["LpAe_trim"]] + ([r["LpAe_salida"]] if r["LpAe_salida"] is not None else [])
    assert 10 * math.log10(sum(10 ** (L / 10) for L in tot)) == pytest.approx(r["LpAe1m"], abs=0.5)


def test_distancia_rn():
    assert ruido.correccion_distancia(0.2, 0.008, 1.0) == pytest.approx(0)
    # Fuente lineal: cerca de −3 dB al duplicar la distancia lejos de la tubería
    assert ruido.correccion_distancia(0.2, 0.008, 2.0) == pytest.approx(-10 * math.log10(4.216 / 2.216), abs=1e-6)


def test_trim_multiorificio_reduce_ruido_y_nivel_requerido():
    c = _co2(P2=150, QN=None, W=20000)
    inst = Instalacion(nps_entrada=6, nps_salida=6, ruido_permitido=85)
    base = calcular(Identificacion(), inst, Dimensionamiento([c], None, TRIM, nps_valvula=4, tipo="gas"))
    m3 = calcular(Identificacion(), inst, Dimensionamiento([c], None, TRIM, nps_valvula=4, tipo="gas",
                                                           ruido=RuidoAerodinamico("multiorificio_3")))
    assert m3.salidas[0]["Lp"] < base.salidas[0]["Lp"] - 5
    assert base.salidas[0]["nivel_trim"] != "No requerido"


def test_vapor_con_densidad_dato():
    # Vapor con ρ1 ingresada: Z se deduce de ρ1 y el resultado coincide con el gas equivalente
    g = _co2()
    gas = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                   Dimensionamiento([g], None, TRIM, nps_valvula=4, tipo="gas"))
    rho1 = gas.salidas[0]["rho"]
    v = _co2(Z1=None, rho1=rho1, rho2=gas.salidas[0]["rho2"])
    vap = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                   Dimensionamiento([v], None, TRIM, nps_valvula=4, tipo="vapor"))
    assert vap.salidas[0]["Kv"] == pytest.approx(gas.salidas[0]["Kv"], rel=1e-9)
    assert vap.salidas[0]["Z1"] == pytest.approx(0.988, rel=1e-9)
    assert vap.salidas[0]["Lp"] == pytest.approx(gas.salidas[0]["Lp"], abs=1e-6)


def test_steam_sobrecalentado_iapws():
    pytest.importorskip("CoolProp")
    import CoolProp.CoolProp as CP
    c = CasoGas("Normal", 10000, None, 1100, 600, 523.15, xT=0.72, FL=0.9, Fd=0.46)
    r = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=6),
                 Dimensionamiento([c], None, TRIM, nps_valvula=3, tipo="steam",
                                  cierre=CasoCierre("Tight Shutoff", 1500, 101.325)))
    s = r.salidas[0]
    rho = CP.PropsSI("D", "T", 523.15, "P", 1.1e6, "Water")
    assert s["rho"] == pytest.approx(rho, rel=1e-9)
    # Isoentálpico: T2 menor que T1 y sobrecalentamiento a P2 positivo
    h1 = CP.PropsSI("H", "T", 523.15, "P", 1.1e6, "Water")
    assert s["T2"] == pytest.approx(CP.PropsSI("T", "H", h1, "P", 6e5, "Water"), rel=1e-9)
    assert s["sobrecalentamiento2"] > 0
    # IEC 60534-2-1 ec. (10): W = N6·FP·Y·Kv·√(x·P1·ρ1)
    from dimensionador.iec60534_2_1 import N6
    W = N6 * s["FP"] * s["Y"] * s["Kv"] * math.sqrt(s["x"] * 1100 * rho)
    assert W == pytest.approx(10000, rel=1e-6)
    assert "sobrecal." in s["tipo_calculo"]


def test_steam_saturado_y_bajo_saturacion():
    pytest.importorskip("CoolProp")
    from dimensionador.modelos import ErrorDatos
    sat = CasoGas("Normal", 5000, None, 1000, 500, None)
    r = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                 Dimensionamiento([sat], None, TRIM, tipo="steam"))
    assert r.salidas[0]["saturado"] and "sat." in r.salidas[0]["tipo_calculo"]
    frio = CasoGas("Normal", 5000, None, 1000, 500, 400)
    with pytest.raises(ErrorDatos):
        calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                 Dimensionamiento([frio], None, TRIM, tipo="steam"))


def test_gas_con_fluido_de_biblioteca_completa_propiedades():
    pytest.importorskip("CoolProp")
    c = CasoGas("Normal", 5000, None, 2000, 1200, 300)
    r = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                 Dimensionamiento([c], None, TRIM, tipo="gas", fluido="Metano"))
    s = r.salidas[0]
    assert s["M"] == pytest.approx(16.04, abs=0.01)
    assert s["T2"] < 300           # efecto Joule-Thomson del metano
    assert 0.9 < s["Z1"] < 1.0


def test_salida_sonica_se_limita_a_mach_1_y_avisa():
    def calc(A):
        r = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                     Dimensionamiento([_co2()], None, TRIM, nps_valvula=4, tipo="gas",
                                      ruido=RuidoAerodinamico(area_salida=A)))
        return r.salidas[0], {a.codigo for _, a in r.alertas}
    s, cod = calc(None)
    assert s["Ma_valvula"] < 1 and not {"salida_sonica", "area_salida_rango"} & cod
    # Un área en in² ingresada como mm² (12,57 en vez de 8107): Mach 1, v = c y dos alertas
    s, cod = calc(12.57)
    assert s["Ma_valvula"] == pytest.approx(1.0) and s["v_valvula"] == pytest.approx(s["c_valvula"])
    assert {"salida_sonica", "area_salida_rango"} <= cod
