"""v0.9.0: actuador (fuerzas y pares), posicionador y accesorios."""
import pytest

from dimensionador import actuadores as A


def _sv(**k):
    base = dict(rotativa=False, cuerpo="globo", nps=2, rating=300, cierre="ANSI Clase II", P1=200, P2=0, dP=200,
                dP_flujo=150, cierre_supuesto=False, T_C=38, puerto_in=2.3125, carrera_in=1.125, rotacion=None,
                blando=False, balanceado=True, balance_auto=False, empaque="ptfe_v", empaque_nombre="PTFE",
                casos=[("Normal", 0.6, 150, 150)], trim="globo_jaula_4v_dentro", compresible=False)
    base.update(k)
    return A.Servicio(**base)


def _act(**k):
    base = dict(tipo="Diafragma y resorte", falla=A.FC, volante=False, P_aire_min=35 * A.PSI_KPA,
                P_aire_max=50 * A.PSI_KPA, flujo="Down", d_vastago_mm=12.7)
    base.update(k)
    return A.DatosActuador(**base)


def test_fuerzas_ejemplo_de_referencia():
    # NPS 2 balanceado, flujo hacia abajo, clase II, PTFE simple, vástago 1/2", ΔP 200 psi
    fz = A.fuerzas_lineales(_sv(), _act())
    assert fz.A == pytest.approx(54, abs=1)
    assert fz.B == pytest.approx(145, abs=1)
    assert fz.C == pytest.approx(50)
    assert fz.cierre == pytest.approx(249, abs=2)


def test_desbalanceado_flujo_arriba_y_abajo():
    sv = _sv(balanceado=False, P2=50, dP=150)
    up = A.fuerzas_lineales(sv, _act(flujo="Up"))
    down = A.fuerzas_lineales(sv, _act(flujo="Down"))
    Ap, Av = 3.1416 * 2.3125 ** 2 / 4, 3.1416 * 0.5 ** 2 / 4
    assert up.A == pytest.approx(150 * Ap + 50 * Av, rel=1e-3)
    assert down.A == pytest.approx(-(150 * Ap - 200 * Av), rel=1e-3)
    assert down.apertura > up.apertura          # con flujo hacia abajo la presión retiene el obturador


def test_cargas_de_asiento_por_clase():
    PC = 3.1416 * 2
    assert A.carga_asiento("ANSI Clase IV", 100, 2, False, False)[0] == pytest.approx(40 * PC, rel=1e-3)
    assert A.carga_asiento("ANSI Clase IV", 100, 5, False, False)[0] == pytest.approx(80 * 3.1416 * 5, rel=1e-3)
    assert A.carga_asiento("ANSI Clase V", 1000, 2, False, False)[0] == pytest.approx(222 * PC, rel=1e-3)
    assert A.carga_asiento("ANSI Clase VI", 1000, 2, False, False)[0] == pytest.approx(300 * PC, rel=1e-3)
    ptfe = A.carga_asiento("ANSI Clase VI", 1000, 2.875, True, False)[0]
    assert ptfe == pytest.approx(0.114 * 1000 + 272, rel=0.02)    # factores típicos de asiento de PTFE


def test_friccion_empaquetaduras():
    assert A.friccion_empaquetadura("ptfe_v", 1.0, 300)[0] == pytest.approx(100)
    assert A.friccion_empaquetadura("grafito", 0.75, 600)[0] == pytest.approx(660)
    assert A.friccion_empaquetadura("grafito_hs_718", 1.0, 600)[0] == pytest.approx(3390)
    assert A.friccion_empaquetadura("grafito", 0.75, 150)[0] == pytest.approx(0.8 * 440)


def test_diafragma_falla_cierra_y_abre():
    for falla in (A.FC, A.FO):
        r = A.evaluar_actuador(_sv(), _act(falla=falla))
        assert r.ok and r.seleccion.startswith("Diafragma y resorte D-069")
        Pbl, Pbu = r.P_banco
        assert Pbl >= 3 and Pbu > Pbl and r.P_req_psig <= 35
    r = A.evaluar_actuador(_sv(), _act(falla=A.FC))
    assert r.P_banco[0] * 69 >= 249 * A.MARGEN_LINEAL      # el resorte asienta solo


def test_aire_insuficiente_y_vastago():
    r = A.evaluar_actuador(_sv(balanceado=False, dP=1500, P1=1500, puerto_in=4.375, carrera_in=2, nps=6),
                           _act(P_aire_min=20 * A.PSI_KPA, P_aire_max=20 * A.PSI_KPA))
    assert not r.ok and any(a.codigo == "act_no_alcanza" for a in r.alertas)


def test_senales_bloqueadas_por_presion():
    act = _act()
    r = A.evaluar_actuador(_sv(), act)
    assert r.P_req_psig > 15
    p = A.evaluar_posicionador(A.DatosPosicionador(tipo="Neumático", senal="3-15 psi"), act, r)
    assert {"3-15 psi", "3-9 psi", "9-15 psi"} <= set(p.bloqueadas) and "6-30 psi" in p.permitidas
    assert any(a.codigo == "pos_senal_bloqueada" for a in p.alertas)
    p = A.evaluar_posicionador(A.DatosPosicionador(tipo="Digital-HART", senal="4-20mA dc"), act, r)
    assert p.permitidas == ["4-20mA dc", "4-12mA dc", "12-20mA dc"] and not any(
        a.codigo == "pos_senal_bloqueada" for a in p.alertas)


def test_accesorios_coherencia_y_omision():
    act = _act(falla=A.FC)
    r = A.evaluar_actuador(_sv(), act)
    acc = A.DatosAccesorios(boosters="", quick_exhaust="1 unidad 1/2\"", sol_accion="Desenergiza para abrir",
                            sol_vias="4 vías")
    rc = A.evaluar_accesorios(acc, act, r, _sv())
    cods = {a.codigo for a in rc.alertas}
    assert {"acc_sol_falla", "acc_sol_vias"} <= cods
    nombres = [f[0] for f in rc.filas]
    assert not any(n.startswith("Boosters") for n in nombres) and any(n.startswith("Quick") for n in nombres)
    assert "Potencia" not in rc.filas[-1][1]


def test_rotativas_y_cuarto_de_vuelta():
    sv = _sv(rotativa=True, cuerpo="bola_segmentada", nps=4, cierre="ANSI Clase IV", dP=150, P1=150, puerto_in=3.8,
             carrera_in=None, rotacion=90, balanceado=False, casos=[("Normal", 0.6, 100, 80)])
    f, TB, TD, _ = A.pares_rotativos(sv, _act())
    assert TB == pytest.approx(0.10 * 150 + 380)
    assert TD == pytest.approx(f.C_en(54) * 80)
    for tipo in ("Piñón y cremallera (Rack and pinion)", "Yugo escocés", "Eléctrico"):
        r = A.evaluar_actuador(sv, _act(tipo=tipo, P_aire_min=60 * A.PSI_KPA, P_aire_max=100 * A.PSI_KPA,
                                        flujo="Unidireccional"))
        assert r.ok, tipo
    r = A.evaluar_actuador(sv, _act(tipo="Diafragma y resorte", flujo="Unidireccional"))
    assert not r.ok and any(a.codigo == "act_incompatible" for a in r.alertas)
    r = A.evaluar_actuador(_sv(), _act(tipo="Yugo escocés"))
    assert any(a.codigo == "act_incompatible" for a in r.alertas)


def test_falla_electrico_y_switching():
    r = A.evaluar_actuador(_sv(), _act(tipo="Eléctrico"))
    assert any(a.codigo == "act_falla_electrico" for a in r.alertas)
    act = _act(tipo="Pistón doble acción sin resorte", P_aire_min=60 * A.PSI_KPA, P_aire_max=100 * A.PSI_KPA)
    r = A.evaluar_actuador(_sv(), act)
    rc = A.evaluar_accesorios(A.DatosAccesorios(), act, r, _sv())
    assert any(a.codigo == "acc_switching" for a in rc.alertas)
    p = A.evaluar_posicionador(A.DatosPosicionador(accion="Directo"), act, r)
    assert any(a.codigo == "pos_accion" for a in p.alertas)


def test_concordancia_actuador_y_flujo():
    assert set(A.tipos_bloqueados(False)) == set(A.TIPOS_ROTATIVOS)
    assert set(A.tipos_bloqueados(True)) == set(A.TIPOS_LINEALES)
    assert set(A.flujos_bloqueados("globo", False)) == {"Unidireccional", "Bidireccional"}
    assert set(A.flujos_bloqueados("bola_trunnion", True)) == {"Up", "Down"}
    assert set(A.flujos_bloqueados("mariposa", True)) == {"Up", "Down", "Bidireccional"}
    # una opción de Flow que no corresponde se avisa y se reemplaza por la que aplica
    r = A.evaluar_actuador(_sv(), _act(flujo="Bidireccional"))
    assert r.ok and any(a.codigo == "act_flujo_valvula" for a in r.alertas)
    ref = A.evaluar_actuador(_sv(), _act(flujo="Down"))
    assert r.seleccion == ref.seleccion


def test_trim_reducido_por_puerto_y_cv_certificado():
    from dataclasses import replace
    from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular
    c = CasoLiquido("Máximo", 60, None, 680, 220, 363, 0.965, 3.26e-7 * 0.965 * 999.1, 70.1, FL=0.9, Fd=0.46)
    ident, inst = Identificacion(), Instalacion(nps_entrada=6, nps_salida=6)
    dim = Dimensionamiento([c], 22120, "globo_contorneado_lineal_abre", nps_valvula=6, caracteristica="lineal")
    base = calcular(ident, inst, dim)
    d = base.nps_valvula
    red = calcular(ident, inst, replace(dim, nps_valvula=d, puerto_mm=base.geometria.puerto_mm * 0.5))
    assert red.trim_reducido is not None and not red.trim_reducido.Cv_certificado
    assert red.Cv_nominal == pytest.approx(base.Cv_nominal * 0.25, rel=0.02)
    assert max(s["apertura"] for s in red.salidas) > max(s["apertura"] for s in base.salidas)
    cert = calcular(ident, inst, replace(dim, nps_valvula=d, puerto_mm=base.geometria.puerto_mm * 0.5,
                                         Cv_reducido_cert=base.Cv_nominal * 0.4))
    assert cert.Cv_nominal == pytest.approx(base.Cv_nominal * 0.4) and cert.trim_reducido.Cv_certificado
    assert any(a.codigo == "trim_reducido" for _, a in cert.alertas)
    igual = calcular(ident, inst, replace(dim, nps_valvula=d, puerto_mm=base.geometria.puerto_mm * 1.1))
    assert igual.trim_reducido is None and igual.Cv_nominal == pytest.approx(base.Cv_nominal)
