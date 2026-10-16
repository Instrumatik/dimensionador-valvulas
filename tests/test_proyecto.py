"""Versión 2: tuberías, Kc/Kapp, verificaciones y entregables."""
import pytest

from dimensionador import tuberias
from dimensionador.proyecto import (CasoCierre, CasoLiquido, Dimensionamiento, Identificacion,
                                    Instalacion, calcular)


def test_diametros_b36():
    assert tuberias.diametro_interior(6, "40") == pytest.approx(154.08, abs=0.01)
    assert tuberias.diametro_interior(2, "80") == pytest.approx(49.22, abs=0.01)
    assert tuberias.diametro_interior(12, "STD") == pytest.approx(304.74, abs=0.01)
    assert tuberias.diametro_interior(4, "10S") == pytest.approx(108.2, abs=0.01)
    with pytest.raises(tuberias.ErrorTuberia):
        tuberias.diametro_interior(48, "160")


def _dim(Kc=None, trim="globo_contorneado_iso_abre", FL=0.9, Fd=0.46):
    c = CasoLiquido("Máximo", 360, None, 680, 220, 363, 0.965, 3.26e-7 * 0.965 * 999.1, 70.1,
                    FL=FL, Fd=Fd, Kc=Kc)
    return Dimensionamiento([c], 22120, trim, nps_valvula=6)


def test_ejemplo_iec_con_kapp_kc():
    # Ejemplo 1 de IEC 60534-2-1 con líneas del mismo diámetro que la válvula (FP = 1)
    inst = Instalacion(nps_entrada=6, nps_salida=6)
    r = calcular(Identificacion(), inst, _dim())
    s = r.salidas[0]
    assert s["Kv"] == pytest.approx(165, rel=0.01)
    assert s["Kapp"] == pytest.approx(460 / (680 - 70.1), rel=1e-6)
    assert s["dPcav"] == pytest.approx(s["Kc"] * (680 - 70.1), rel=1e-6)
    assert s["W"] == pytest.approx(360 * 0.965 * 999.1, rel=1e-6)


def test_kc_usuario_se_usa_sin_corregir():
    inst = Instalacion(nps_entrada=6, nps_salida=6)
    r = calcular(Identificacion(), inst, _dim(Kc=0.8, trim="globo_multietapa", FL=0.97, Fd=0.07))
    assert r.salidas[0]["Kc"] == pytest.approx(0.8)
    assert r.salidas[0]["condicion"] == "sin cavitación"


def test_verificaciones_de_instalacion():
    inst = Instalacion(nps_entrada=6, nps_salida=6, conexion="Wafer", rating=150,
                       P_diseno=2500, T_diseno=300 + 273.15, cierre="ANSI Clase VI")
    r = calcular(Identificacion(), inst, _dim())
    codigos = {a.codigo for _, a in r.alertas}
    assert {"conexion_incompatible", "clase_insuficiente", "cierre_temperatura"} <= codigos


def test_documentos_word(tmp_path):
    pytest.importorskip("docx")
    from dimensionador import entregables as E
    r = calcular(Identificacion(tag="FV-1"), Instalacion(nps_entrada=6, nps_salida=6), _dim())
    docs = [f(r, E.Presentacion()) for f in E.CONSTRUCTORES.values()]
    ruta = tmp_path / "e.docx"
    E.a_docx(docs, str(ruta))
    import docx
    texto = "\n".join(p.text for p in docx.Document(str(ruta)).paragraphs)
    assert "Memoria de cálculo" in texto and "Hoja de datos" in texto and "Informe técnico" in texto


def test_fl_fd_por_caso_y_transitorio():
    mu = 3.26e-7 * 0.965 * 999.1
    casos = [CasoLiquido("Normal", 200, None, 680, 220, 363, 0.965, mu, 70.1, FL=0.9, Fd=0.46),
             CasoLiquido("Mínimo", 40, None, 680, 220, 363, 0.965, mu, 70.1, FL=0.7, Fd=0.3),
             CasoLiquido("Transitorio", 500, None, 680, 220, 363, 0.965, mu, 70.1, criterio=False)]
    dim = Dimensionamiento(casos, 22120, "globo_contorneado_iso_abre",
                           cierre=CasoCierre("Tight Shutoff", 1000, 0))
    r = calcular(Identificacion(), Instalacion(nps_entrada=8, nps_salida=8), dim)
    assert r.salidas[0]["FL"] == pytest.approx(0.9)
    assert r.salidas[1]["FL"] == pytest.approx(0.7)
    assert r.salidas[1]["Fd"] == pytest.approx(0.3)
    # El transitorio no fija el tamaño: puede quedar por encima del 100 % de apertura
    assert all(s["apertura"] <= 1.0 for s in r.salidas[:2])
    # El caso de cierre define la presión de diseño
    assert dim.cierre.dP == pytest.approx(1000)


def test_cierre_invalido():
    from dimensionador.modelos import ErrorDatos
    c = CasoLiquido("Normal", 200, None, 680, 220, 363, 0.965, 0.3, 70.1)
    dim = Dimensionamiento([c], 22120, "globo_contorneado_iso_abre", cierre=CasoCierre("Tight Shutoff", 100, 200))
    with pytest.raises(ErrorDatos):
        calcular(Identificacion(), Instalacion(nps_entrada=6, nps_salida=6), dim)
