import pytest

from dimensionador import asme_b16_34 as A


def test_rating_tabla_e_interpolacion():
    assert A.rating("1.1", 150, 20) == pytest.approx(19.6)
    assert A.rating("1.1", 300, 200) == pytest.approx(43.8)
    assert A.rating("1.1", 300, 175) == pytest.approx((45.1 + 43.8) / 2)
    assert A.rating("1.1", 600, 600) is None


def test_clase_minima_y_alertas():
    assert A.clase_minima("1.1", 30, 200) == 300
    clase, r, al = A.verificar("WCB", None, 15, 100, 20)
    assert clase == 150 and r == pytest.approx(17.7) and not al
    clase, r, al = A.verificar("WCB", 150, 25, 100, -40)
    codigos = {a.codigo for a in al}
    assert {"clase_insuficiente", "material_baja_temperatura"} <= codigos
    _, _, al = A.verificar("WCB", None, 10, 450, 20)
    assert "grafitizacion" in {a.codigo for a in al}
