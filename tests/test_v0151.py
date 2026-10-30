"""v0.15.1: Cv rápido (líquido, gas y vapor de agua) y tabla de constantes N de IEC 60534-2-1."""
import os

import pytest

from dimensionador import herramientas as H, iec60534_2_1 as I, propiedades as P

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_liquido_igual_que_el_calculo_completo():
    r = H.cv_liquido(360, 680, 220, 0.965, 70.1, 22120, 0.90)       # IEC 60534-2-1, ejemplo 1
    f = I.Liquido(Q=360, P1=680, P2=220, T1=363, rho1=0.965 * 999.1, Pv=70.1, Pc=22120, nu=3.26e-7)
    assert r.Kv == pytest.approx(I.dimensionar_liquido(f, I.Valvula(0.9, 0.75, 0.46, 150)).Kv)
    assert r.Kv == pytest.approx(165, abs=0.5) and r.Cv == pytest.approx(r.Kv / 0.865) and not r.bloqueado
    b = H.cv_liquido(360, 680, 50, 0.965, 70.1, 22120, 0.90)
    assert b.bloqueado and b.pasos[4][1] == pytest.approx(b.pasos[3][1])     # se dimensiona con la ΔP de bloqueo
    acc = H.cv_liquido(360, 680, 50, 0.965, 70.1, 22120, 0.90, FP=0.95, FLP=0.85)
    assert acc.pasos[1][1] == pytest.approx(0.85 / 0.95)
    with pytest.raises(ValueError):
        H.cv_liquido(360, 680, 220, 0.965, 70.1, 22120, 0.90, FP=0.95)       # falta FLP


def test_gas_igual_que_el_calculo_completo():
    g = I.Gas(P1=680, P2=310, T1=433, M=44.01, gamma=1.30, Z=0.988, mu=1.4e-5, QN=3800)   # ejemplo 2
    r = H.cv_gas(g.caudal_masico(), 680, 310, H.densidad_gas(680, 433, 44.01, 0.988), 1.30, 0.60)
    assert r.Kv == pytest.approx(I.dimensionar_gas(g, I.Valvula(0.9, 0.60, 0.42, 100)).Kv, rel=1e-6)
    assert r.Kv == pytest.approx(62.7, abs=0.1)
    b = H.cv_gas(1000, 1000, 200, 5, 1.4, 0.6)
    y = dict((n, v) for n, v, _ in b.pasos)
    assert b.bloqueado and y["Y = 1 − x / (3·Fγ·xT)"] == pytest.approx(2 / 3)


def test_constantes_n():
    nombres = [c.nombre for c in H.CONSTANTES_N]
    assert {"N1", "N2", "N4", "N5", "N6", "N8", "N17", "N18", "N19", "N27", "N32"} <= set(nombres)
    c = {x.nombre: x for x in H.CONSTANTES_N}
    assert c["N1"].Kv[0] == I.N1 and c["N6"].Kv[0] == pytest.approx(I.N6, abs=0.005)
    assert c["N18"].Kv[0] == I.N18 and c["N27"].Kv[0] == I.N27 and c["N32"].Kv[0] == I.N32
    assert c["N22 (ts = 0 °C)"].Kv[0] == I.N22
    # Con Cv el valor es el de Kv por 0,865 elevado a la potencia de C en la ecuación (±1 %)
    potencia = {"N1": 1, "N2": -2, "N4": -0.5, "N5": -2, "N6": 1, "N8": 1, "N9 (ts = 0 °C)": 1, "N9 (ts = 15 °C)": 1,
                "N17": -1, "N18": -1, "N19": 0.5, "N22 (ts = 0 °C)": 1, "N22 (ts = 15 °C)": 1, "N27": 1}
    for n, e in potencia.items():
        for kv, cv in zip(c[n].Kv, c[n].Cv):
            assert cv == pytest.approx(kv * 0.865 ** e, rel=0.015), n
    # Con P en bar cada constante cambia por la potencia de la presión de su ecuación
    assert c["N1"].Kv[1] == pytest.approx(c["N1"].Kv[0] * 10)
    assert c["N8"].Kv[1] == pytest.approx(c["N8"].Kv[0] * 100)


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_ventanas_cv_y_constantes(app):
    from dimensionador.gui import herramientas as GH
    w = GH.CvRapidoVentana()
    assert w.tabs.count() == 3
    assert any("Kv = <b>164,9" in t for t in (l.text() for l in w.tabs.widget(0).findChildren(GH.QLabel)))
    assert any("Kv = <b>62,7" in t for t in (l.text() for l in w.tabs.widget(1).findChildren(GH.QLabel)))
    if P.DISPONIBLE:
        assert any("Kv = <b>" in t for t in (l.text() for l in w.tabs.widget(2).findChildren(GH.QLabel)))
    c = GH.Constantes()
    t = c.tabla
    assert t.rowCount() >= len(H.CONSTANTES_N) and t.item(0, 0).text() == "N1"
    assert [c for c, _ in GH.HERRAMIENTAS][:2] == ["conversor", "cv"] and "constantes" in GH.VENTANAS
