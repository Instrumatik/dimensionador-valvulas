"""Selección de materiales (solapa 3): B16.34, química, cavitación, galling, NACE y entregables."""
import pytest

from dimensionador import asme_b16_34 as B, entregables as E, materiales as MT, quimica as Q
from dimensionador import seleccion_materiales as SM
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular


def _dim(P1=680, P2=220, T=363, Pv=70.1, FL=0.9):
    c = CasoLiquido("Máximo", 360, None, P1, P2, T, 0.965, 3.15e-4, Pv, FL=FL, Fd=0.46)
    return Dimensionamiento([c], 22120, "globo_contorneado_iso_abre", nps_valvula=6)


def _calc(sv, dim=None, **inst):
    return calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6, **inst), dim or _dim(), sv)


def test_b16_34_valores_de_tabla():
    assert B.rating("1.1", 150, 38) == pytest.approx(19.6)
    assert B.rating("2.2", 150, 816) == pytest.approx(1.0, abs=0.05)
    assert B.rating("2.2", 2500, 38) > B.rating("2.2", 1500, 38)


def test_biblioteca_completa():
    assert len(MT.MATERIALES) >= 60
    for m in MT.MATERIALES.values():
        assert m.componentes and m.nombre and m.quimica
        for c in m.quimica:
            assert c in Q.METALES or c in Q.POLIMEROS, (m.clave, c)
        if m.grupo:
            assert m.grupo in B.GRUPOS, m.clave
    assert MT.para_componente("cuerpo") and MT.buscar("stellite")


def test_quimica_cloruros_en_316():
    cl = Q.normalizar(Q.AgenteServicio("cloruros", "mg/L", 250, "Acuosa"), 101.3, 1.0)
    assert Q.evaluar(MT.MATERIALES["CF8M"], cl, 90, True).nivel in "CD"
    assert Q.evaluar(MT.MATERIALES["CD3MWCuN"], cl, 90, True).nivel in "AB"


def test_agua_industrial_por_defecto():
    m = _calc(SM.ServicioMateriales()).materiales
    assert m.cuerpo.clave == "WCB"
    assert not m.agrio and m.norma == "No aplica"
    assert all(c.elegido for c in m.componentes.values() if c.aplica)


def test_agua_de_mar_descarta_acero_al_carbono():
    m = _calc(SM.ServicioMateriales(fluido="Agua de mar"), _dim(T=298)).materiales
    assert m.cuerpo.familia != MT.MATERIALES["WCB"].familia
    assert Q.evaluar(m.cuerpo, Q.normalizar(Q.AgenteServicio("cloruros", "mg/L", 19400, "Acuosa"), 101.3, 1.0),
                     25, True).nivel in "AB"


def test_cavitacion_severa_endurece_internos():
    m = _calc(SM.ServicioMateriales(fluido="Agua desmineralizada"), _dim(P1=2000, P2=300, T=300, Pv=3.5)).materiales
    assert m.ctx.severidad_cav in ("severa", "extrema")
    for k in ("obturador", "asiento"):
        rc = m.componentes[k]
        assert rc.elegido.HRC_efectiva >= rc.dureza_req_HRC >= 40


def test_servicio_agrio_upstream():
    sv = SM.ServicioMateriales(industria="O&G Upstream", familia_fluido="Mezcla multifásica", fluido="Agua producida",
                               agentes=[Q.AgenteServicio("h2s", "ppmv", 2000, "Gas / vapor")])
    m = _calc(sv, _dim(P1=5000, P2=4000, T=330, Pv=20)).materiales
    assert m.agrio and "15156" in m.norma
    assert m.pH2S_kPa == pytest.approx(10.0, rel=0.05)
    for c in m.componentes.values():
        if c.aplica and c.elegido and not c.elegido.blando:
            assert c.elegido.iso15156.estado in ("aceptable", "condicional"), c.clave


def test_refineria_usa_iso_17945():
    sv = SM.ServicioMateriales(industria="Refinería", familia_fluido="Hidrocarburo", fluido="Otro",
                               agentes=[Q.AgenteServicio("h2s", "ppmv", 5000, "Gas / vapor")])
    m = _calc(sv, _dim(P1=3000, P2=2500, T=330, Pv=20)).materiales
    assert "17945" in m.norma


def test_galling():
    M = MT.MATERIALES
    assert SM.riesgo_galling(M["316"], M["316"], 50)[0] == "ALTO"
    assert SM.riesgo_galling(M["316"], M["ST6"], 50)[0] == "BAJO"
    assert SM.riesgo_galling(M["316"], M["N60"], 50)[0] == "BAJO"


def test_modo_manual_advierte_y_marca_incompatible():
    sv = SM.ServicioMateriales(familia_fluido="Ácido", fluido="Otro", modos={"cuerpo": "MANUAL"},
                               manual={"cuerpo": "WCB"}, agentes=[Q.AgenteServicio("hcl", "% p/p", 10, "Acuosa")])
    m = _calc(sv, _dim(T=310)).materiales
    rc = m.componentes["cuerpo"]
    assert rc.modo == "MANUAL" and rc.elegido.clave == "WCB" and rc.recomendado.clave != "WCB"
    codigos = {a.codigo for a in m.todas_las_alertas()}
    assert "mat_manual" in codigos and "mat_incompatible" in codigos


def test_rating_con_material_del_cuerpo():
    r = _calc(SM.ServicioMateriales())
    assert any(a.codigo == "rating_verificado" for _, a in r.alertas)


def test_entregables_muestran_materiales():
    r = _calc(SM.ServicioMateriales(fluido="Agua de mar"), _dim(T=298))
    pr = E.Presentacion()
    hoja = E.a_html(E.hoja_datos(r, pr))
    assert "A definir (versión futura)" not in hoja and r.materiales.cuerpo.nombre.split(" — ")[0] in hoja
    assert "Selección de materiales" in E.a_html(E.informe_tecnico(r, pr))
    memoria = E.a_html(E.memoria(r, pr))
    assert "Agentes químicos normalizados" in memoria and "Selección por componente" in memoria
