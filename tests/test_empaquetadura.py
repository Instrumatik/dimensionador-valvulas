"""Estilos de bola y tapón excéntrico (v0.8.0) y selección de empaquetadura y bonete."""
import pytest

from dimensionador import empaquetaduras as EM, entregables as E, fluido_servicio as FS, quimica as Q
from dimensionador import seleccion_materiales as SM
from dimensionador.estilos import CUERPOS, ESTILOS, KC_TIPICO, NOMBRES_ANTERIORES
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular


def _dim(P1=680, P2=220, T=363, Pv=70.1, fluido=FS.AGUA, variante="Agua industrial / de enfriamiento",
         trim="globo_contorneado_iso_abre", nps=6):
    e = ESTILOS[trim]
    c = CasoLiquido("Máximo", 360, None, P1, P2, T, 0.965, 3.15e-4, Pv, FL=e.FL, Fd=e.Fd)
    return Dimensionamiento([c], 22120, trim, nps_valvula=nps, fluido=fluido, variante=variante)


def _emp(sv=None, dim=None, **inst):
    r = calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6, **inst), dim or _dim(),
                 sv or SM.ServicioMateriales())
    return r, r.materiales.empaquetadura


def test_estilos_nuevos_completos():
    for k in ("bola_paso_completo", "bola_paso_reducido", "bola_trunnion", "bola_segmentada", "tapon_excentrico"):
        c = CUERPOS[k]
        assert c.rotativa and c.trims
        for t in c.trims:
            e = ESTILOS[t]
            assert 0 < e.FL <= 1 and 0 < e.xT < 1 and 0 < e.Fd <= 1
            assert t in KC_TIPICO or "excentrico" in t
    # la bola a 90° recupera más presión que a 70° y el paso reducido menos que el completo
    assert ESTILOS["bola_paso_completo_90"].FL < ESTILOS["bola_paso_total_70"].FL
    assert ESTILOS["bola_paso_reducido_70"].FL > ESTILOS["bola_paso_total_70"].FL
    assert ESTILOS["bola_segmentada_v30"].xT > ESTILOS["bola_segmentada"].xT
    assert "Bola-T" in CUERPOS["bola_trunnion"].nombre
    assert NOMBRES_ANTERIORES["Bola"] == "bola_trunnion"


def test_estilo_influye_en_el_calculo():
    cv = {}
    for t in ("bola_paso_total_70", "bola_paso_completo_90", "bola_paso_reducido_70"):
        r = calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6, cuerpo="bola_trunnion"),
                     _dim(P1=1500, P2=300, T=300, Pv=3.5, trim=t))
        cv[t] = (r.salidas[0]["Cv"], r.salidas[0]["condicion"])
    # FL bajo (90°) ahoga antes: el caudal es el mismo pero la condición es más severa
    assert cv["bola_paso_completo_90"][1] != "sin cavitación"
    assert len({v[0] for v in cv.values()}) > 1


def test_bola_flotante_clase_alta():
    r = calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6, cuerpo="bola_paso_completo",
                                               rating=900), _dim(trim="bola_paso_total_70"))
    assert "bola_flotante_presion" in {a.codigo for _, a in r.alertas}
    r = calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6, cuerpo="bola_trunnion",
                                               rating=900), _dim(trim="bola_paso_total_70"))
    assert "bola_flotante_presion" not in {a.codigo for _, a in r.alertas}


def test_agua_ptfe_estandar():
    _, e = _emp()
    assert e.elegida.clave == "ptfe_v" and e.bonete.startswith("Estándar") and e.emision_req == "estándar"


def test_vapor_caliente_grafito():
    _, e = _emp(dim=_dim(P1=9000, P2=8000, T=573, Pv=8590))
    assert "grafito" in e.elegida.quimica
    assert {"empaque_friccion"} <= {a.codigo for a in e.alertas}
    assert any("inhibidor" in n for n in e.notas)


def test_hidrocarburo_baja_emision():
    _, e = _emp(dim=_dim(fluido=FS.USUARIO, variante="Crudo"))
    assert e.elegida.baja_emision and e.emision_req == "baja"


def test_toxico_fuelle_en_globo_y_carga_viva_en_bola():
    sv = SM.ServicioMateriales(agentes=[Q.AgenteServicio("h2s", "mg/L", 500, "Acuosa")])
    _, e = _emp(sv, _dim(fluido=FS.USUARIO, variante="Crudo"))
    assert e.elegida.clave == "fuelle" and "fuelle" in e.bonete and e.eval_elegida.metal_fuelle
    _, e = _emp(sv, _dim(fluido=FS.USUARIO, variante="Crudo", trim="bola_paso_total_70"), cuerpo="bola_trunnion")
    assert e.elegida.clave != "fuelle" and e.elegida.baja_emision
    assert any("API 641" in n for n in e.notas)


def test_vacio_descarta_ptfe_simple():
    _, e = _emp(dim=_dim(P1=150, P2=40, T=300, Pv=3.5))
    assert e.elegida.vacio
    assert any(x.clave == "ptfe_v" for x, _ in e.descartadas)


def test_criogenico_bonete_prolongado():
    _, e = _emp(dim=_dim(fluido=FS.USUARIO, variante="Otro líquido", T=120, P1=500, P2=300, Pv=50))
    assert e.bonete.startswith("Criogénico") and "bonete_prolongado" in {a.codigo for a in e.alertas}


def test_nitrico_descarta_grafito():
    sv = SM.ServicioMateriales(agentes=[Q.AgenteServicio("hno3", "% p/p", 60, "Acuosa")])
    _, e = _emp(sv, _dim(variante="", P1=9000, P2=8000, T=520, Pv=4000))
    # PTFE no llega a la temperatura y el grafito no resiste el nítrico: sin candidata, o fuelle si su metal sirve
    assert all("grafito" not in x.quimica for x, _ in e.alternativas)
    assert e.elegida is None or e.elegida.clave == "fuelle"


def test_manual_no_apta_y_entregables():
    sv = SM.ServicioMateriales(modos={"empaquetadura": "MANUAL"}, manual={"empaquetadura": "ptfe_v"})
    r, e = _emp(sv, _dim(P1=9000, P2=8000, T=573, Pv=8590))
    codigos = {a.codigo for a in e.alertas}
    assert e.elegida.clave == "ptfe_v" and {"empaque_manual", "empaque_incompatible"} <= codigos
    assert "empaque_incompatible" in {a.codigo for a in r.materiales.todas_las_alertas()}
    for cons in ("hoja_datos", "informe_tecnico", "memoria"):
        txt = E.a_html(E.CONSTRUCTORES[cons](r, E.Presentacion()))
        assert "Empaquetadura" in txt and "bonete" in txt.lower()


def test_catalogo_quimica_grafito():
    for e in EM.EMPAQUETADURAS.values():
        assert e.T_min_C < e.T_max_C and e.T_max_oxid_C <= e.T_max_C
    assert Q.nivel_regla("hno3", "grafito", 60, 25, True) == "D"
    assert Q.nivel_regla("cloruros", "grafito", 20000, 90, True) in "AB"


def test_acero_al_carbono_descartado_sobre_425():
    r, _ = _emp(dim=_dim(P1=9000, P2=8000, T=573, Pv=8590), rating=1500, T_diseno=713.15, P_diseno=10000)
    m = r.materiales
    assert m.ctx.T_max_C > 425
    assert m.cuerpo.grupo not in ("1.1", "1.2", "1.3", "1.4")
    assert "grafitizacion" not in {a.codigo for a in m.todas_las_alertas()}
    # con fuelle a temperatura moderada no se informa bonete prolongado
    sv = SM.ServicioMateriales(agentes=[Q.AgenteServicio("h2s", "mg/L", 500, "Acuosa")])
    _, e = _emp(sv, _dim(fluido=FS.USUARIO, variante="Crudo"))
    assert e.elegida.clave == "fuelle" and "bonete_prolongado" not in {a.codigo for a in e.alertas}
