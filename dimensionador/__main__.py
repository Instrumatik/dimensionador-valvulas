"""Punto de entrada: python -m dimensionador"""
import sys


def autoprueba() -> int:
    """Verificación rápida del ejecutable: calcula el ejemplo 1 de IEC 60534-2-1."""
    from . import propiedades
    from .iec60534_2_1 import Liquido, Valvula, dimensionar_liquido
    r = dimensionar_liquido(Liquido(Q=360, P1=680, P2=220, T1=363, rho1=0.965 * 999.1, Pv=70.1,
                                    Pc=22120, nu=3.26e-7), Valvula(FL=0.9, xT=0.75, Fd=0.46, d_mm=150))
    p = propiedades.liquido("Agua / vapor de agua", 680, 363)
    ok = abs(r.Kv - 165) < 0.5 and 960 < p.rho < 970
    print(f"Kv = {r.Kv:.1f} (norma: 165); densidad agua 90 °C = {p.rho:.1f} kg/m³ -> {'OK' if ok else 'FALLA'}")
    return 0 if ok else 1


def main():
    if "--prueba" in sys.argv:
        return autoprueba()
    from PySide6.QtWidgets import QApplication

    from .gui.ventana import VentanaPrincipal
    app = QApplication(sys.argv)
    app.setApplicationName("Dimensionador de válvulas de control")
    app.setStyle("Fusion")
    w = VentanaPrincipal()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
