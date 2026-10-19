"""Selección de materiales (solapa 3): B16.34, química, cavitación, galling, NACE y entregables."""
import pytest

from dimensionador import asme_b16_34 as B, entregables as E, fluido_servicio as FS, materiales as MT, quimica as Q
from dimensionador import seleccion_materiales as SM
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular


def _dim(P1=680, P2=220, T=363, Pv=70.1, FL=0.9, fluido=FS.AGUA, variante="Agua industrial / de enfriamiento",
         agua_libre=""):
    c = CasoLiquido("Máximo", 360, None, P1, P2, T, 0.965, 3.15e-4, Pv, FL=FL, Fd=0.46)
    return Dimensionamiento([c], 22120, "globo_contorneado_iso_abre", nps_valvula=6, fluido=fluido,
                            variante=variante, agua_libre=agua_libre)


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
    m = _calc(SM.ServicioMateriales(), _dim(T=298, variante="Agua de mar")).materiales
    assert m.cuerpo.familia != MT.MATERIALES["WCB"].familia
    assert Q.evaluar(m.cuerpo, Q.normalizar(Q.AgenteServicio("cloruros", "mg/L", 19400, "Acuosa"), 101.3, 1.0),
                     25, True).nivel in "AB"


def test_cavitacion_severa_endurece_internos():
    m = _calc(SM.ServicioMateriales(), _dim(P1=2000, P2=300, T=300, Pv=3.5, variante="Agua desmineralizada")).materiales
    assert m.ctx.severidad_cav in ("severa", "extrema")
    for k in ("obturador", "asiento"):
        rc = m.componentes[k]
        assert rc.elegido.HRC_efectiva >= rc.dureza_req_HRC >= 40


def test_servicio_agrio_upstream():
    sv = SM.ServicioMateriales(industria="O&G Upstream", agentes=[Q.AgenteServicio("h2s", "ppmv", 2000, "Gas / vapor")])
    m = _calc(sv, _dim(P1=5000, P2=4000, T=330, Pv=20, variante="Agua producida (yacimiento)")).materiales
    assert m.agrio and "15156" in m.norma
    assert m.pH2S_kPa == pytest.approx(10.0, rel=0.05)
    for c in m.componentes.values():
        if c.aplica and c.elegido and not c.elegido.blando:
            assert c.elegido.iso15156.estado in ("aceptable", "condicional"), c.clave


def test_refineria_usa_iso_17945():
    sv = SM.ServicioMateriales(industria="Refinería", agentes=[Q.AgenteServicio("h2s", "ppmv", 5000, "Gas / vapor")])
    m = _calc(sv, _dim(P1=3000, P2=2500, T=330, Pv=20, fluido=None, variante="Hidrocarburo líquido (otro)",
                       agua_libre="Intermitente")).materiales
    assert "17945" in m.norma


def test_galling():
    M = MT.MATERIALES
    assert SM.riesgo_galling(M["316"], M["316"], 50)[0] == "ALTO"
    assert SM.riesgo_galling(M["316"], M["ST6"], 50)[0] == "BAJO"
    assert SM.riesgo_galling(M["316"], M["N60"], 50)[0] == "BAJO"


def test_modo_manual_advierte_y_marca_incompatible():
    sv = SM.ServicioMateriales(modos={"cuerpo": "MANUAL"}, manual={"cuerpo": "WCB"},
                               agentes=[Q.AgenteServicio("hcl", "% p/p", 10, "Acuosa")])
    m = _calc(sv, _dim(T=310, fluido=None, variante="Ácido")).materiales
    rc = m.componentes["cuerpo"]
    assert rc.modo == "MANUAL" and rc.elegido.clave == "WCB" and rc.recomendado.clave != "WCB"
    codigos = {a.codigo for a in m.todas_las_alertas()}
    assert "mat_manual" in codigos and "mat_incompatible" in codigos


def test_rating_con_material_del_cuerpo():
    r = _calc(SM.ServicioMateriales())
    assert any(a.codigo == "rating_verificado" for _, a in r.alertas)


def test_entregables_muestran_materiales():
    r = _calc(SM.ServicioMateriales(), _dim(T=298, variante="Agua de mar"))
    pr = E.Presentacion()
    hoja = E.a_html(E.hoja_datos(r, pr))
    assert "A definir (versión futura)" not in hoja and r.materiales.cuerpo.nombre.split(" — ")[0] in hoja
    assert "Selección de materiales" in E.a_html(E.informe_tecnico(r, pr))
    memoria = E.a_html(E.memoria(r, pr))
    assert "Agentes químicos normalizados" in memoria and "Selección por componente" in memoria


# --- fluido único (solapa 2) -------------------------------------------------------------
def test_fluido_de_la_solapa_2_manda_sobre_materiales():
    # aunque el servicio de materiales traiga otro fluido, se usa el de la solapa 2
    m = _calc(SM.ServicioMateriales(familia_fluido="Hidrocarburo líquido", fluido="Crudo", acuosa="No"),
              _dim(T=298, variante="Agua de mar")).materiales
    sv = m.servicio
    assert (sv.familia_fluido, sv.fluido, sv.fase, sv.acuosa) == ("Agua", "Agua de mar", "Líquido", "Sí")


def test_variantes_y_agua_libre():
    assert "Agua de mar" in FS.variantes("liquido", FS.AGUA)
    assert FS.variantes("steam", FS.AGUA) == [] and FS.variantes("gas", "Nitrógeno") == []
    assert "Gas natural" in FS.variantes("gas", FS.USUARIO)
    assert FS.agua_libre_fija("liquido", FS.AGUA, "Condensado") == "Sí"
    assert FS.agua_libre_fija("steam", FS.AGUA, "") == FS.AUTO_AGUA
    assert FS.agua_libre_fija("gas", "Nitrógeno", "") is None
    assert FS.agua_libre_sugerida("gas", "Nitrógeno", "") == "No"
    assert FS.agua_libre_fija("liquido", FS.USUARIO, "Ácido") == "Sí"


def test_vapor_saturado_y_sobrecalentado():
    sat = FS.para_materiales("steam", FS.AGUA, "", "", [{"saturado": True}])
    sob = FS.para_materiales("steam", FS.AGUA, "", "", [{"saturado": False}])
    assert (sat.fluido, sat.acuosa) == ("Vapor saturado", "Intermitente")
    assert (sob.fluido, sob.acuosa) == ("Vapor sobrecalentado", "No")


def test_flashing_y_slurry_cambian_la_fase():
    assert FS.para_materiales("liquido", FS.AGUA, "Condensado", "Sí", flashing=True).fase == "Gas-líquido"
    assert FS.para_materiales("liquido", FS.USUARIO, "Slurry (líquido con sólidos)", "Sí").fase == "Líquido-sólido"


def test_correccion_salina():
    c = FS.correccion_salina(FS.salinidad_pct("liquido", FS.AGUA, "Agua de mar"))
    assert c.f_rho == pytest.approx(1.026, abs=0.002) and c.f_mu == pytest.approx(1.08, abs=0.01)
    assert c.f_Pv == pytest.approx(0.979, abs=0.003)
    assert FS.correccion_salina(FS.salinidad_pct("liquido", FS.AGUA, "Agua desmineralizada")) is None
    # los cloruros informados mandan sobre la salinidad típica
    assert FS.salinidad_pct("liquido", FS.AGUA, "Agua producida (yacimiento)", 19400) == pytest.approx(3.2, abs=0.2)


def _codigos(sv, dim):
    return {a.codigo for a in _calc(sv, dim).materiales.todas_las_alertas()}


def test_alertas_de_coherencia():
    seco = _dim(fluido="Nitrógeno", variante="", agua_libre="No")
    sv = SM.ServicioMateriales(agentes=[Q.AgenteServicio("cloruros", "mg/L", 500, "Acuosa")], pH=6)
    c = _codigos(sv, seco)
    assert "mat_agua_libre_contradiccion" in c and "mat_pH_sin_agua" in c
    sv = SM.ServicioMateriales(agentes=[Q.AgenteServicio("cloruros", "mg/L", 500, "Acuosa")])
    assert "mat_calidad_agua" in _codigos(sv, _dim(variante="Condensado"))
    sv = SM.ServicioMateriales(pH=10, agentes=[Q.AgenteServicio("hcl", "% p/p", 5, "Acuosa")])
    assert "mat_pH_familia" in _codigos(sv, _dim(fluido=None, variante="Ácido"))
    sv = SM.ServicioMateriales(solidos="Ausentes confirmados")
    assert "mat_slurry_solidos" in _codigos(sv, _dim(fluido=None, variante="Slurry (líquido con sólidos)"))
    assert not {"mat_agua_libre_contradiccion", "mat_calidad_agua", "mat_pH_familia", "mat_slurry_solidos"} & \
        _codigos(SM.ServicioMateriales(), _dim())


def test_gas_puro_es_su_propio_agente():
    m = _calc(SM.ServicioMateriales(), _dim(fluido="Sulfuro de hidrógeno", variante="", agua_libre="Sí")).materiales
    assert m.agrio
