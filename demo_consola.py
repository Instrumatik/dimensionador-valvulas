"""Demostración por consola del núcleo de cálculo (sin interfaz gráfica)."""
from dimensionador import propiedades as pr
from dimensionador.estilos import ESTILOS
from dimensionador.iec60534_2_1 import Gas, Liquido
from dimensionador.servicio import Caso, Seleccion, dimensionar


def mostrar(titulo, inf):
    print(f"\n=== {titulo} ===")
    print(f"Válvula seleccionada: {inf.d_pulg:g}\" (DN {inf.DN}), Kv nominal típico {inf.Kv_nominal:.1f}")
    for rc in inf.casos:
        r = rc.resultado
        print(f"  Caso {rc.caso.nombre:8s}: Kv = {r.Kv:8.2f}  Cv = {r.Cv:8.2f}  apertura {rc.apertura*100:5.1f} %"
              f"  régimen {r.regimen}{'  [FLUJO CRÍTICO]' if r.bloqueado else ''}")
    for caso, a in inf.todas_las_alertas():
        inten = f" intensidad {a.intensidad:.0f} % ({a.nivel})" if a.intensidad is not None and a.nivel else ""
        print(f"  [{a.severidad.name}] {caso}: {a.titulo}{inten}")
        if a.remedios:
            print(f"      Remedio principal: {a.remedios[0]}")


def agua(P1, P2, T, Q):
    p = pr.liquido("Agua / vapor de agua", P1, T)
    return Liquido(Q=Q, P1=P1, P2=P2, T1=T, rho1=p.rho, Pv=p.Pv, Pc=p.Pc, nu=p.nu)


# 1) Agua de alimentación con cavitación, línea de 6"
casos = [Caso("Mínimo", agua(2500, 600, 400, 20)), Caso("Normal", agua(2400, 700, 400, 60)),
         Caso("Máximo", agua(2300, 800, 400, 90))]
mostrar("Agua a 127 °C con alta caída de presión",
        dimensionar(casos, Seleccion(ESTILOS["globo_contorneado_iso_abre"], D1_mm=154.05, D2_mm=154.05)))

# 2) Condensado con flashing
mostrar("Condensado con flashing",
        dimensionar([Caso("Máximo", agua(1000, 200, 450, 20), fluido="Agua / vapor de agua")],
                    Seleccion(ESTILOS["angular_contorneado_cierra"], D1_mm=77.92, D2_mm=154.05)))

# 3) Vapor sobrecalentado
p = pr.gas("Agua / vapor de agua", 1000, 473.15)
g = lambda W, P2: Gas(P1=1000, P2=P2, T1=473.15, M=p.M, gamma=p.gamma, Z=p.Z, mu=p.mu, W=W, rho1=p.rho)
mostrar("Vapor a 10 bar a y 200 °C",
        dimensionar([Caso("Normal", g(5000, 600)), Caso("Máximo", g(8000, 300))],
                    Seleccion(ESTILOS["globo_jaula_4v_fuera"], D1_mm=154.05, D2_mm=202.72)))
