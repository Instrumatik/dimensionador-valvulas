"""v0.8.2: tamaño del trim y carrera, juegos de internos, catálogo de empaquetaduras, materiales nuevos y ajustes."""
import pytest

from dimensionador import empaquetaduras as EM, entregables as E, fluido_servicio as FS, geometria as G
from dimensionador import juegos_trim as JT, materiales as MT, quimica as Q, seleccion_materiales as SM
from dimensionador.estilos import ESTILOS
from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular


def _calc(trim="globo_jaula_4v_fuera", nps=4, P1=1500, P2=1300, sv=None, cierre="ANSI Clase IV", cuerpo="globo", **dim):
    e = ESTILOS[trim]
    c = CasoLiquido("Máximo", 80, None, P1, P2, 313, 0.995, 6e-4, 7.4, FL=e.FL, Fd=e.Fd)
    d = Dimensionamiento([c], 22120, trim, nps_valvula=nps, fluido=FS.AGUA,
                         variante="Agua industrial / de enfriamiento", **dim)
    return calcular(Identificacion(), Instalacion(nps_entrada=nps, nps_salida=nps, cierre=cierre, cuerpo=cuerpo), d,
                    sv or SM.ServicioMateriales())


def test_fraccion_y_carrera_normalizada():
    assert G.fraccion_in(5.375) == "5 3/8 in" and G.fraccion_in(0.75) == "3/4 in" and G.fraccion_in(3) == "3 in"
    g = G.estimar("globo_jaula_4v_fuera", False, 8, 100, 100)
    assert g.texto_puerto.startswith("7 in (177,8 mm)") and g.carrera_in == pytest.approx(3)
    # los trims de orificios llevan la carrera normalizada siguiente
    assert G.estimar("globo_multietapa", False, 8, 100, 100).carrera_in == pytest.approx(4)
    # trim reducido: el puerto baja con la raíz de la relación de Cv
    r = G.estimar("globo_jaula_4v_fuera", False, 4, 59, 236)
    assert r.reducido and r.puerto_in == pytest.approx(1.75)


def test_geometria_en_resultado_y_certificada():
    r = _calc()
    g = r.geometria
    assert not g.rotativa and g.carrera_mm == pytest.approx(50.8)
    assert "mm" in r.salidas[0]["carrera"] and "in" in r.salidas[0]["carrera"]
    r = _calc(puerto_mm=136.525, carrera_mm=76.2)
    assert r.geometria.texto_puerto == "5 3/8 in (136,5 mm) certificado"
    assert r.geometria.texto_carrera == "3 in (76,2 mm) certificada"
    hd = E.hoja_datos(r, E.Presentacion())
    txt = str(hd.__dict__)
    assert "Carrera nominal del vástago" in txt and "5 3/8 in" in txt


def test_geometria_rotativa():
    r = _calc(trim="bola_paso_total_70", nps=6, cuerpo="bola_trunnion")
    g = r.geometria
    assert g.rotativa and g.rotacion_grados == 70 and "°" in r.salidas[0]["carrera"]


def test_juegos_validos():
    for j in JT.JUEGOS.values():
        for c, k in j.piezas().items():
            assert k in MT.MATERIALES, (j.clave, k)
            assert c in MT.MATERIALES[k].componentes, (j.clave, c, k)
    assert len(JT.JUEGOS) == 17


def test_juego_equivalente_y_aptos():
    m = _calc().materiales
    assert m.juegos and m.juego is not None
    aptos = {v.juego.clave for v in m.juegos if v.ok}
    assert aptos
    # los juegos blandos quedan fuera sin clase VI
    assert not any(v.juego.blando for v in m.juegos if v.ok)
    m6 = _calc(cierre="ANSI Clase VI").materiales
    assert all(v.juego.blando for v in m6.juegos if v.ok)


def test_juego_elegido_por_usuario():
    sv = SM.ServicioMateriales(juego_trim="N25-T12")
    m = _calc(sv=sv).materiales
    assert m.componentes["obturador"].elegido.clave == "316" and m.componentes["jaula"].elegido.clave == "CB7Cu1"
    assert m.juego_coincide and m.juego.juego.clave == "N25-T12"
    assert "mat_juego" in {a.codigo for a in m.todas_las_alertas()}


def test_materiales_nuevos_de_trim_y_vastago():
    for k in ("316L", "321", "CF8M_T", "CF8C_ENC", "174_H1150D_ST6", "CB7Cu1_CR", "N50", "A286"):
        m = MT.MATERIALES[k]
        assert m.componentes and m.fuentes
    vas = {m.uns.split(" ")[0] for m in MT.para_componente("vastago")}
    for uns in ("N05500", "N06022", "S20910", "S31600", "S31603", "S32100", "S66286"):
        assert any(uns in u for u in vas) or any(uns in m.uns for m in MT.para_componente("vastago")), uns


def test_catalogo_empaquetaduras():
    E_ = EM.EMPAQUETADURAS
    for k in ("ptfe_v_doble_p", "ptfe_v_doble_vac", "ptfe_carbono_cv_doble", "ptfe_vidrio_cv", "grafito_hs_718",
              "grafito_hs_177", "ptfe_trenzado", "ptfe_trenzado_lub"):
        assert E_[k].tipo
    assert E_["grafito_hs_718"].carga_viva and E_["grafito_hs_718"].T_max_C > 371
    assert E_["ptfe_v"].guia_temperatura.startswith("Hasta 232 °C")
    assert E_["grafito"].guia_temperatura.startswith("Por encima de 232 °C")
    nombres = " ".join(e.nombre for e in E_.values()).lower()
    assert "enviro" not in nombres


def test_sin_marcas_de_multinacionales():
    import pathlib
    raiz = pathlib.Path(__file__).resolve().parent.parent / "dimensionador"
    for p in raiz.rglob("*.py"):
        t = p.read_text(encoding="utf-8").lower()
        for marca in ("fisher", "emerson", "enviro-seal", "masoneilan", "flowserve"):
            assert marca not in t, (p.name, marca)


def test_masa_en_fase_gas_se_convierte_a_molar():
    a = Q.AgenteServicio("h2s", "% p/p", 0.5, "Gas / vapor")
    n = Q.normalizar(a, 5000, 1.0, M_gas=18.0)
    assert n.masa_en_gas
    assert n.kPa == pytest.approx(0.005 * 18 / Q.AGENTES["h2s"].MW * 5000, rel=1e-3)


def test_agrio_no_declarado_es_advertencia():
    sv = SM.ServicioMateriales(medio="Servicio corrosivo",
                               agentes=[Q.AgenteServicio("h2s", "mg/L", 500, "Acuosa")])
    m = _calc(sv=sv).materiales
    a = next(a for a in m.alertas if a.codigo == "mat_medio_distinto")
    assert a.severidad == SM.Severidad.ADVERTENCIA and "agrio" in a.titulo.lower()
