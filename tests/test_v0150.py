"""v0.15.0: barra de herramientas rápidas del encabezado y contacto."""
import math
import os
from urllib.parse import parse_qs, urlparse

import pytest

from dimensionador import contacto as C, herramientas as H, propiedades as P, unidades as U

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_conversor():
    assert H.convertir(100, "coeficiente", "Cv", "Kv") == pytest.approx(86.5)
    assert H.convertir(86.5, "coeficiente", "Kv", "Cv") == pytest.approx(100)
    filas = {s: v for s, _, v in H.convertir_todas(10, "presion", "bar g")}
    assert filas["bar a"] == pytest.approx(11.01325)
    assert filas["psig"] == pytest.approx(145.038, rel=1e-4)
    # con la altitud cambia la presión atmosférica y con ella la absoluta
    patm = H.p_atm_altitud(1500)
    assert 84 < patm < 85.5
    assert H.convertir(0, "presion", "bar g", "kPa a", patm) == pytest.approx(patm)
    assert {k for k, _ in H.MAGNITUDES} - {"coeficiente"} <= set(U.MAGNITUDES)


@pytest.mark.skipif(not P.DISPONIBLE, reason="sin CoolProp")
def test_propiedades_y_tabla_de_vapor():
    f = {p.nombre: p.valor for p in H.propiedades_punto("Agua / vapor de agua", 1000, 423.15)}
    assert f["Fase"] == "Líquido" and 915 < f["Densidad"] < 920
    assert f["Temperatura de saturación a P"] - 273.15 == pytest.approx(179.9, abs=0.1)
    s = {p.nombre: p.valor for p in H.saturacion("Agua / vapor de agua", P_kPa=1000)}
    assert s["Calor latente hfg"] == pytest.approx(2014.6, abs=1.5)        # tabla de vapor a 10 bar a
    s100 = {p.nombre: p.valor for p in H.saturacion("Agua / vapor de agua", T_K=373.15)}
    assert s100["Presión de saturación"] == pytest.approx(101.42, abs=0.1)
    with pytest.raises(ValueError):
        H.saturacion("Agua / vapor de agua")
    g = {p.nombre for p in H.propiedades_punto("Gas natural", 5000, 300)}
    assert "Factor de compresibilidad Z" in g and "Presión crítica" not in g


def test_tuberia_y_velocidad():
    sch40 = next(r for r in H.tabla_tuberia(4) if r.cedula == "40")
    assert sch40.DI_mm == pytest.approx(102.26) and sch40.peso_kg_m == pytest.approx(16.08, abs=0.05)
    assert H.velocidad(100, 102.26) == pytest.approx(3.38, abs=0.01)
    nps, ced, v = H.nps_para_velocidad(100, 3, "40")
    assert nps == 5 and ced == "40" and v <= 3
    assert H.diametro_para_velocidad(100, H.velocidad(100, 80)) == pytest.approx(80)


def test_rating_y_calculadoras():
    ts, tabla = H.tabla_rating("1.1")
    assert ts[0] == 38 and tabla[150][0] == pytest.approx(19.6)
    FF, dp = H.dp_bloqueado(680, 70.1, 22120, 0.9)
    assert FF == pytest.approx(0.96 - 0.28 * math.sqrt(70.1 / 22120))
    assert dp == pytest.approx(0.81 * (680 - FF * 70.1))
    assert H.dp_bloqueado_gas(1000, 0.7, 1.4) == pytest.approx(700)
    # 1000 Nm³/h a 0 °C y 1 atm son 1000 m³/h reales
    assert H.caudal_gas_real(1000, U.P_ATM_KPA, U.T_NORMAL_K) == pytest.approx(1000)
    assert H.caudal_gas_normal(H.caudal_gas_real(500, 1000, 300, 0.95), 1000, 300, 0.95) == pytest.approx(500)
    assert H.masico_desde_normal(22.414, 28.96) == pytest.approx(28.96)


def test_contacto():
    u = urlparse(C.url_whatsapp("9.9.9"))
    assert u.netloc == "wa.me" and u.path == "/5493513213210"
    assert "[Código N25-9.9.9]" in parse_qs(u.query)["text"][0]
    assert C.LINKEDIN == "https://www.linkedin.com/company/instrumatiksite/"
    assert C.WEB == "https://instrumatik.com.ar"
    assert [d[0] for d in C.DESTINOS] == ["whatsapp", "linkedin", "web"]


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_barra_en_el_encabezado(app):
    from dimensionador import ayuda
    from dimensionador.gui import herramientas as GH, iconos
    from dimensionador.gui.ventana import VentanaPrincipal
    w = VentanaPrincipal()
    b = w.barra_herramientas
    claves = [c for c, _ in GH.HERRAMIENTAS] + [d[0] for d in C.DESTINOS]
    assert list(b.botones) == claves
    for boton in b.botones.values():          # chicos, con icono y sin texto
        assert boton.text() == "" and not boton.icon().isNull() and boton.width() == 28 and boton.toolTip()
    assert set(claves) <= set(iconos.SVG)
    assert "herramientas" in ayuda.A
    menus = [a.text() for a in w.menuBar().actions()]
    assert "&Herramientas" in menus
    for c in GH.VENTANAS:                     # cada ventana se abre una sola vez y se reutiliza
        d = b.abrir(c)
        assert d is b.abrir(c)
        d.close()


def test_ventanas_calculan(app):
    from dimensionador.gui import herramientas as GH
    conv = GH.Conversor()
    conv.ed_valor.setText("100")
    conv.cb_mag.setCurrentIndex([k for k, _ in H.MAGNITUDES].index("coeficiente"))
    conv.cb_de.setCurrentText("Cv")
    filas = {conv.tabla.item(i, 0).text(): conv.tabla.item(i, 1).text() for i in range(conv.tabla.rowCount())}
    assert filas["Kv"] == "86,5"
    tub = GH.Tuberias()
    tub.d_Q.edit.setText("100")
    assert tub.tabla.columnCount() == 7 and "5\"" in tub.lb_sug.text()
    rat = GH.Rating()
    rat.ed_P.setText("40")
    rat.ed_T.setText("250")
    assert "Clase 300" in rat.lb_cl.text()


def test_enlaces_editables(tmp_path):
    from dimensionador.gui import herramientas as GH
    ruta = str(tmp_path / "enlaces.json")
    assert GH.leer_enlaces(ruta) == list(H.ENLACES)       # sin archivo: la lista inicial
    GH.guardar_enlaces([("Mi proveedor", "https://ejemplo.com")], ruta)
    assert GH.leer_enlaces(ruta) == [("Mi proveedor", "https://ejemplo.com")]
    assert all(u.startswith("https://") for _, u in H.ENLACES)
