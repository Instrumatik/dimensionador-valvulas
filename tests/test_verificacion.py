"""Verificaciones permanentes: unidades (ida y vuelta, entradas y resultados), ruido hidrodinámico contra los
ejemplos del anexo de IEC 60534-8-4 y Cv por debajo del mínimo controlable."""
import glob
import json
import math
import os

import pytest

from dimensionador import ruido as R, unidades as U
from dimensionador.ruido import CV_POR_KV

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_unidades_ida_y_vuelta():
    for mag, us in U.MAGNITUDES.items():
        for s in us:
            for v in (0.137, 1.0, 523.7):
                assert U.desde_base(U.a_base(v, mag, s), mag, s) == pytest.approx(v, rel=1e-9, abs=1e-9), (mag, s)


# Anexo de IEC 60534-8-4 (edición 2005): agua, P1 10 bar a, Cv 90, FL 0,92, Fd 0,42, válvula DN100,
# tubería Di 107,1 mm con pared de 3,6 mm. (m kg/s, P2 kPa, xFz impuesto, Lpi dB, fp,turb Hz, LpA,e,1m dB(A))
ANEXO = [(30, 800, None, 149.596, 494.5, 62.7),
         (40, 650, None, 156.543, 654.35, 81.0),
         (40, 650, 0.3543, 154.532, 397.93, 66.9)]


@pytest.mark.parametrize("m, P2, xFz, Lpi, fp, LpA", ANEXO)
def test_ruido_liquido_anexo_iec_60534_8_4(m, P2, xFz, Lpi, fp, LpA):
    r = R.ruido_liquido(m, 1000, P2, 2.32, 997, 1400, 90 / CV_POR_KV, 0.1, 0.1071, 0.0036, 0.92, 0.42,
                        xFz=xFz, An=-4.6)
    mem = r["memoria"]
    assert mem.valor("Lpi") == pytest.approx(Lpi, abs=0.1)          # 10^−4,6 ≈ rW·10^−4 de la edición 2005
    assert mem.valor("fp,turb") == pytest.approx(fp, rel=0.002)
    # La edición 2015 (la de N25) suma el espectro por bandas: queda 0 a 3,5 dB por encima del anexo 2005
    assert 0 <= r["LpAe1m"] - LpA <= 3.5


def test_cv_por_debajo_del_minimo_controlable():
    from dimensionador.proyecto import CasoLiquido, Dimensionamiento, Identificacion, Instalacion, calcular
    psi, lb, T = 6.894757, 0.45359237, (225 - 32) / 1.8 + 273.15
    cs = [CasoLiquido(n, None, W * lb, P1 * psi, 244.69 * psi, T, 0.9565, 0.2631e-3, 18.928 * psi, FL=0.98,
                      Fd=0.29, Kc=1.0) for n, W, P1 in (("Mínimo", 29093, 814.69), ("Máximo", 269100, 809.69))]
    r = calcular(Identificacion(), Instalacion(cuerpo="globo", rating=600, nps_entrada=6, nps_salida=6,
                                               sch_entrada="STD", sch_salida="STD"),
                 Dimensionamiento(cs, 3200.11 * psi, "globo_jaula_4v_dentro", nps_valvula=3, caracteristica="lineal"))
    assert r.salidas[0]["bajo_cv_minimo"] and not r.salidas[1]["bajo_cv_minimo"]
    assert r.salidas[0]["Cv_minimo"] == pytest.approx(142 / 50, rel=0.01)
    cod = [(c, a.codigo) for c, a in r.alertas]
    assert ("Mínimo", "bajo_cv_minimo") in cod and ("Mínimo", "apertura_baja") not in cod
    from dimensionador import entregables as E
    assert E._ap(r.salidas[0]) == E.BAJO_MINIMO


@pytest.fixture(scope="module")
def app():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _numero(t):
    from dimensionador.gui.ventana import leer_numero
    return leer_numero(t.replace(".", ""))


def test_unidades_de_entradas_y_resultados(app):
    """Cambiar cada unidad y volver no altera el dato; cada resultado mostrado, leído en la unidad que
    muestra su etiqueta, es el valor calculado."""
    from dimensionador.gui.ventana import ALIAS_SALIDA, CASOS, VentanaPrincipal
    raiz = os.path.dirname(os.path.dirname(__file__))
    archivos = sorted(glob.glob(os.path.join(raiz, "kit_workshop", "casos", "*.valvula")))
    assert archivos
    for f in archivos:
        w = VentanaPrincipal()
        w._cargar(json.load(open(f, encoding="utf-8")))
        for fila in w._todas_las_filas():
            if not fila.unidad.isEnabled() or fila.unidad.count() < 2:
                continue
            orig = fila.unidad.currentText()
            antes = []
            for j in range(len(fila.edits)):
                try:
                    antes.append(fila.valor_base(j))
                except ValueError:
                    antes.append(None)
            for i in range(fila.unidad.count()):
                s = fila.unidad.itemText(i)
                fila.unidad.setCurrentText(s)
                if fila.mag_de[s] != fila.mag_de[orig]:
                    continue
                for j, a in enumerate(antes):
                    if a is not None:
                        assert fila.valor_base(j) == pytest.approx(a, rel=2e-3, abs=1e-6), (f, fila.clave, s)
            fila.unidad.setCurrentText(orig)
        for clave in ("P1", "T1"):
            fila = w.filas[clave]
            orig = fila.unidad.currentText()
            for i in range(fila.unidad.count()):
                fila.unidad.setCurrentText(fila.unidad.itemText(i))
                w.calcular()
                pr = w.presentacion()
                nombres = [rc.caso.nombre for rc in w.res.informe.casos]
                for k, fs in w.salidas.items():
                    mag = fs.magnitud
                    if mag not in pr.u or k in ("carrera", "visc", "caudal_otro"):
                        continue
                    for j, caso in enumerate(CASOS):
                        if caso not in nombres:
                            continue
                        v = w.res.salidas[nombres.index(caso)].get(ALIAS_SALIDA.get(k, k))
                        if not isinstance(v, (int, float)) or v == 0:
                            continue
                        try:
                            shown = _numero(fs.celdas[j].text())
                        except ValueError:
                            continue
                        if shown is None:
                            continue
                        back = U.a_base(shown, "presion" if mag == "presion_abs" else mag, pr.un(mag))
                        assert math.isclose(back, v, rel_tol=6e-3, abs_tol=abs(v) * 6e-3 + 1e-3), (f, k, pr.un(mag))
            fila.unidad.setCurrentText(orig)
