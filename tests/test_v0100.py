"""v0.10.0: actuador certificado (modo MANUAL), fricción certificada y trims anticavitación por etapas."""
import pytest

from dimensionador import actuadores as A, anticavitacion as AC
from tests.test_v090 import _act, _sv


def _codigos(r):
    return {a.codigo for a in r.alertas}


def test_friccion_certificada_reemplaza_c():
    fz = A.fuerzas_lineales(_sv(), _act(friccion_cert_lbf=300))
    assert fz.C == 300 and "certificada" in fz.textos["C"]


@pytest.mark.parametrize("falla", [A.FC, A.FO])
def test_diafragma_certificado_igual_al_automatico_cumple(falla):
    sv = _sv()
    auto = A.evaluar_actuador(sv, _act(falla=falla))
    assert auto.ok
    a = A.DIAFRAGMA[[t.nombre for t in A.DIAFRAGMA].index(auto.seleccion.split()[3].rstrip(":"))]
    man = A.evaluar_actuador(sv, _act(falla=falla, modo="MANUAL", cert_area_in2=a.area_in2,
                                      cert_banco_psig=auto.P_banco, cert_carrera_in=a.carrera_max_in,
                                      cert_pmax_psig=a.P_max_psig))
    assert man.ok, man.alertas
    assert "certificado" in man.seleccion
    assert any(v.startswith("CUMPLE") for _, v, _ in man.filas)
    assert man.P_req_psig == pytest.approx(auto.P_req_psig, rel=1e-6)
    chico = A.evaluar_actuador(sv, _act(falla=falla, modo="MANUAL", cert_area_in2=a.area_in2 / 10,
                                        cert_banco_psig=auto.P_banco, cert_carrera_in=a.carrera_max_in,
                                        cert_pmax_psig=a.P_max_psig))
    assert not chico.ok and "act_cert_no_cumple" in _codigos(chico)
    assert any(v.startswith("NO CUMPLE") for _, v, _ in chico.filas)


def test_faltan_datos_certificados():
    r = A.evaluar_actuador(_sv(), _act(modo="MANUAL", cert_area_in2=105))
    assert not r.ok and "act_cert_faltan" in _codigos(r)
    assert "ajuste de banco" in next(a for a in r.alertas if a.codigo == "act_cert_faltan").mensaje


def test_carrera_corta_no_cumple():
    r = A.evaluar_actuador(_sv(), _act(modo="MANUAL", cert_area_in2=105, cert_banco_psig=(6, 18),
                                       cert_carrera_in=0.75, cert_pmax_psig=50))
    assert any(f.startswith("Carrera") and v.startswith("NO CUMPLE") for f, v, _ in r.filas)


def test_piston_y_electrico_certificados():
    sv = _sv()
    p = A.evaluar_actuador(sv, _act(tipo="Pistón doble acción sin resorte", falla=A.FL, modo="MANUAL",
                                    cert_area_in2=28.3, cert_carrera_in=4, cert_pmax_psig=150))
    assert p.ok and p.P_req_psig > 0
    e = A.evaluar_actuador(sv, _act(tipo="Eléctrico", falla=A.FL, modo="MANUAL", cert_nominal=100))
    assert not e.ok
    e = A.evaluar_actuador(sv, _act(tipo="Eléctrico", falla=A.FL, modo="MANUAL", cert_nominal=2000))
    assert e.ok


def test_cuarto_vuelta_certificado():
    sv = _sv(rotativa=True, cuerpo="mariposa_doble", nps=6, carrera_in=None, rotacion=90, trim="mariposa_alto_rendimiento_90",
             puerto_in=6, casos=[("Normal", 0.6, 50, 50)], dP=100)
    auto = A.evaluar_actuador(sv, _act(tipo="Piñón y cremallera (Rack and pinion)", falla=A.FL, flujo="Unidireccional"))
    assert auto.ok
    T80 = float(auto.seleccion.split(":")[1].split("N·m")[0].strip().replace(".", "").replace(",", ".")) / A.LBFIN_NM
    man = A.evaluar_actuador(sv, _act(tipo="Piñón y cremallera (Rack and pinion)", falla=A.FL, flujo="Unidireccional",
                                      modo="MANUAL", cert_par_aire_lbfin=T80, cert_p_par_psig=80, cert_pmax_psig=116))
    assert man.ok, man.alertas
    assert man.P_req_psig == pytest.approx(auto.P_req_psig, rel=0.01)
    debil = A.evaluar_actuador(sv, _act(tipo="Piñón y cremallera (Rack and pinion)", falla=A.FL,
                                        flujo="Unidireccional", modo="MANUAL", cert_par_aire_lbfin=T80 / 10,
                                        cert_p_par_psig=80, cert_pmax_psig=116))
    assert not debil.ok


def test_reparto_de_etapas():
    rep = AC.reparto(4000, 400, 7.4, 3)
    assert rep[0][0] == 4000 and rep[-1][1] == pytest.approx(400)
    assert rep[0][2] > rep[1][2] > rep[2][2]          # las primeras etapas toman más caída
    k = AC.k_etapa(4000, 400, 7.4, 3)
    for p1, p2, _ in rep:
        assert (p1 - p2) / (p1 - 7.4) == pytest.approx(k)
    assert AC.etapas_recomendadas(4000, 400, 7.4) == (4, 3)
    assert AC.oferta(5) == 6 and AC.oferta(7) is None
    t = AC.TRIMS["etapas_2"]
    assert t.Kc == pytest.approx(1 - 0.3 ** 2) and t.Kc < t.FL ** 2
