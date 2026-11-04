"""Ayuda de los fluidos de proceso (v0.16.0): catálogo, caracterización y alertas.

El artículo del catálogo se arma desde fluidos_proceso.CATALOGO, así que siempre coincide con lo que el
programa calcula.
"""
from __future__ import annotations

import html as _html

from . import fluidos_proceso as FP

ENTRADAS: dict[str, dict] = {}
GUIA: dict[str, dict] = {}


def _e(clave, titulo, texto, categoria, guia, formula="", tipicos="", referencia="", relacionadas=()):
    ENTRADAS[clave] = dict(titulo=titulo, texto=texto, formula=formula, tipicos=tipicos, referencia=referencia,
                           relacionadas=list(relacionadas), categoria=categoria)
    GUIA[clave] = guia


def _g(que_es, que_hace, que_indica, umbrales, por_debajo, por_encima, afecta, recomendaciones, ejemplo):
    return dict(que_es=que_es, que_hace=que_hace, que_indica=que_indica, umbrales=umbrales, por_debajo=por_debajo,
                por_encima=por_encima, afecta=list(afecta), recomendaciones=list(recomendaciones), ejemplo=ejemplo)


_MODELO = {"petroleo": "Pseudocomponente de petróleo", "mezcla": "Ecuación de estado (mezcla)",
           "solucion": "Tablas de soluciones acuosas", "glicol": "Glicol con agua", "azufre": "Azufre líquido",
           "slurry": "Sólidos en agua"}


def _catalogo_html() -> str:
    partes = []
    for grupo in FP.GRUPOS:
        filas = []
        for f in FP.CATALOGO.values():
            if f.grupo != grupo:
                continue
            modelos = sorted({_MODELO[p.modelo or f.modelo] for p in f.presentaciones})
            pres = "; ".join(_html.escape(p.nombre) for p in f.presentaciones)
            filas.append(f"<tr><td valign='top'><b>{_html.escape(f.nombre)}</b><br><i>{_html.escape(f.ingles)}</i></td>"
                         f"<td valign='top'>{pres}</td><td valign='top'>{' / '.join(modelos)}</td>"
                         f"<td valign='top'>{_html.escape(f.descripcion)} {_html.escape(f.servicio)}</td></tr>")
        partes.append(f"<h4>{_html.escape(grupo)}</h4><table border='1' cellspacing='0' cellpadding='4' width='100%'>"
                      "<tr bgcolor='#eef2f6'><th>Fluido</th><th>Presentaciones</th><th>Modelo</th>"
                      "<th>Descripción y recomendaciones para la válvula</th></tr>" + "".join(filas) + "</table>")
    return "".join(partes)


_e("fluidos_proceso", "Fluidos de refinería, mejoradores, servicios y químicos",
   "<p>Desde la v0.16.0 la lista <b>Fluido</b> de la solapa 2 incluye, debajo de los fluidos puros, los fluidos "
   "de proceso de refinerías y mejoradores de crudo pesado y extrapesado, los servicios (aguas, vapores, "
   "condensados) y los químicos de tratamiento. Se eligen una sola vez: con la <b>presentación / "
   "concentración</b> y la <b>caracterización</b> N25 calcula SG, viscosidad, presión de vapor y presión "
   "crítica de cada caso (Cv, factores FF, FR, cavitación y flashing) y pasa a 3-Materiales la familia del "
   "fluido y sus agentes típicos (azufre, TAN, H₂S, NH₃, cloruros, sólidos, concentración del químico), que "
   "deciden cuerpo, internos, asientos y empaquetadura.</p>"
   "<p><b>Modelos de propiedades.</b></p><ul>"
   "<li><b>Gases y LPG</b>: ecuación de estado multicomponente de CoolProp (HEOS / GERG) con la composición "
   "molar editable; los pares sin coeficientes publicados (olefinas, amoníaco) usan la regla de "
   "Lorentz-Berthelot y la viscosidad de la mezcla con propileno, la de Herning-Zipperer. Para gases con agua "
   "se toma la raíz de vapor (el condensado se separa aguas arriba).</li>"
   "<li><b>Crudos y cortes</b>: pseudocomponente con el grado API y el factor de Watson Kw. Densidad con los "
   "coeficientes de dilatación de API MPMS 11.1 (1980); viscosidad con la ecuación de Walther de ASTM D341 entre "
   "dos puntos; Tb = (Kw·SG)³; Tc, Pc y ω de Kesler-Lee; M de Riazi-Daubert; presión de vapor de Lee-Kesler o, "
   "si hay RVP, la verdadera de EPA AP-42 cap. 7.1 (se usa la mayor).</li>"
   "<li><b>Soluciones acuosas</b> (soda, ácidos, sales, aminas, polímeros): densidad y viscosidad de tablas "
   "publicadas a 20 y 80 °C interpoladas en la concentración (Andrade en la temperatura); Pv = actividad del "
   "agua × Pv del agua (redondeada hacia arriba, conservadora) más la presión del soluto volátil (HCl, HNO₃).</li>"
   "<li><b>Glicoles</b>: MEG y MPG hasta 60 % con las soluciones de CoolProp; el resto con mezcla ideal y regla "
   "logarítmica de viscosidad; Pv por Raoult.</li>"
   "<li><b>Azufre líquido</b>: densidad lineal y viscosidad tabulada con el salto de polimerización a 159 °C. "
   "<b>Slurry acuoso</b>: densidad de la mezcla y viscosidad de Thomas.</li></ul>"
   "<p><b>Exactitud.</b> Del orden de ±2 % en densidad y ±20 % en viscosidad para los químicos; en crudos "
   "pesados la viscosidad típica puede diferir 3 veces o más del crudo real del mismo API. Por eso la línea de "
   "<b>caracterización</b> acepta los datos del laboratorio o del certificado y esos datos mandan.</p>"
   "<p><b>Materiales.</b> Además de los agentes de siempre, N25 evalúa la sulfidación a alta temperatura (M30), "
   "la corrosión por ácidos nafténicos (M31), el bisulfuro de amonio de las aguas agrias (M32) y el "
   "hinchamiento de elastómeros en hidrocarburos (M33, descarta EPDM). Los fluidos con H₂S, CO o HCl se tratan "
   "como tóxicos para la empaquetadura.</p>"
   "<p><b>Aguas y vapores</b> se eligen con <b>Agua / vapor de agua</b> y su variante: agua de servicio, de "
   "enfriamiento, potable, desmineralizada, condensados de media y baja presión, agua agria, agua despojada de "
   "SWS, aguas servidas y agua aceitosa; vapor de alta, media y baja presión.</p>"
   "<h3>Catálogo</h3>" + _catalogo_html(),
   "Datos",
   _g("Es la lista de fluidos de proceso con propiedades estimadas y agentes típicos ya cargados.",
      "Calcula SG, μ, Pv y Pc (o M, Z, κ para gases) de cada caso y define el fluido para materiales y empaques.",
      "Si el fluido está en la lista, no hace falta cargar las propiedades a mano: alcanza con la presentación "
      "y, si los hay, los datos del laboratorio.",
      "Cada presentación tiene su rango: por ejemplo, el azufre de 120 a 155 °C, la soda al 50 % por encima de "
      "12 °C o el HVGO por encima de su punto de fluidez.",
      "Por debajo del rango aparece la alerta de solidificación o cristalización.",
      "Por encima, la de temperatura alta (degradación, polimerización o extrapolación).",
      ["SG, μ, Pv y Pc (solapa 2)", "Cv, FR, FF, cavitación y flashing", "Familia y agentes (3-Materiales)",
       "Empaquetadura y emisiones"],
      ["Cargue en la caracterización los datos del certificado o del laboratorio (API, dos viscosidades, RVP, "
       "azufre, TAN o la concentración real).",
       "Si el fluido no está, use «Definido por el usuario» y cargue las propiedades de la hoja de datos."],
      "Crudo de 16 °API a 60 °C: N25 estima SG ≈ 0,94 y μ ≈ 135 cP, aplica la corrección por Reynolds y en "
      "materiales descarta EPDM; a 300 °C agrega sulfidación y corrosión nafténica."),
   referencia="API MPMS 11.1 (1980); ASTM D341; Riazi-Daubert; Kesler-Lee; EPA AP-42 cap. 7.1; API 571; "
              "API RP 939-C; API RP 945; NACE SP0403; CoolProp (HEOS / GERG-2008)",
   relacionadas=["fluido", "caracterizacion_fluido", "variante_fluido", "composicion_gn", "viscosidad", "Pv", "Pc"])

_e("caracterizacion_fluido", "Caracterización del fluido de proceso",
   "<p>Línea de texto editable, debajo del fluido, con los datos que definen sus propiedades. Al elegir la "
   "presentación se carga con los valores típicos; reemplácelos con los del certificado o del laboratorio. "
   "Separe los datos con punto y coma; se aceptan coma o punto decimal:</p><ul>"
   "<li><b>API 16</b> o <b>SG 0,96</b>: grado API o densidad relativa a 15,6 °C.</li>"
   "<li><b>Kw 11,8</b>: factor de caracterización de Watson (10,5 aromático a 12,5 parafínico).</li>"
   "<li><b>ν 250 cSt a 50 °C</b> y <b>ν 35 cSt a 100 °C</b>: dos viscosidades cinemáticas (con una sola se "
   "conserva la pendiente típica). También «a 122 °F».</li>"
   "<li><b>RVP 5 psi</b> o <b>RVP 34 kPa</b>: presión de vapor Reid (crudos, naftas, gasolinas).</li>"
   "<li><b>S 3,5 %</b> y <b>TAN 2</b>: azufre total y número de acidez (mg KOH/g), para materiales.</li>"
   "<li><b>Concentración 47 %</b>: en soluciones y glicoles (% en masa).</li>"
   "<li><b>μ 50 cP a 20 °C</b>: viscosidad aparente de polímeros o de una solución.</li>"
   "<li><b>Sólidos 15 %</b> y <b>ρs 2650 kg/m³</b>: en slurry acuoso.</li></ul>"
   "<p>En gases y LPG la línea es la composición molar, igual que en el gas natural.</p>",
   "Datos",
   _g("Son los datos propios del fluido real que reemplazan a los típicos de la presentación.",
      "Con ellos N25 recalcula densidad, viscosidad, presión de vapor, presión crítica y los agentes de "
      "materiales (azufre, TAN, concentración).",
      "Debajo de la línea se muestra el resumen: SG a 15 °C, Tb, M y Pc del pseudocomponente, o SG y μ a 20 °C.",
      "La correlación de RVP vale de 2 a 15 psi; el factor de Watson, de 10 a 13.",
      "No aplica.", "No aplica.",
      ["SG, μ, Pv y Pc", "Agentes azufre y TAN en 3-Materiales"],
      ["Use dos viscosidades medidas a temperaturas que encierren la de operación.",
       "Con crudos diluidos cargue el RVP del producto real: define la presión de vapor y el flashing."],
      "«API 9; ν 4500 cSt a 60 °C; ν 210 cSt a 100 °C; RVP 3 psi; S 3,8 %; TAN 2,8» para un crudo "
      "extrapesado diluido."),
   relacionadas=["fluidos_proceso", "fluido", "viscosidad", "Pv"])

_REF = "Fluidos de proceso (N25)"
_e("fp_solidifica", "Riesgo de solidificación o cristalización",
   "<p>La temperatura de entrada de algún caso está por debajo del punto de solidificación, cristalización o "
   "fluidez de la presentación: azufre líquido (< ~ 120 °C), soda al 50 % (< ~ 12 °C), ácido fosfórico al 85 % "
   "(< ~ 21 °C), ácido sulfúrico al 98 % (< ~ 2 °C), gasóleos de vacío y residuos (punto de fluidez).</p>",
   "Fenómenos",
   _g("Avisa que el fluido puede dejar de fluir o formar cristales a esa temperatura.",
      "No cambia el Cv, pero la válvula puede trabarse u obstruirse.",
      "El cálculo vale solo si la línea se mantiene caliente.",
      "El de cada presentación (ver el catálogo).", "Por debajo: solidifica, cristaliza o gelifica.", "No aplica.",
      ["Alertas", "Especificación de traceado y camisa"],
      ["Trace o encamise la línea y la válvula.", "Verifique el punto de fluidez en el certificado."],
      "Soda al 50 % a 8 °C: cristaliza en el bonete y traba el vástago."),
   referencia=_REF, relacionadas=["fluidos_proceso"])
_e("fp_temperatura_alta", "Temperatura por encima del rango del fluido",
   "<p>La temperatura supera el rango de la presentación: el azufre polimeriza por encima de ~ 159 °C y su "
   "viscosidad sube a miles de cP; el hipoclorito se descompone por encima de ~ 40 °C; los glicoles se degradan "
   "(TEG > ~ 204 °C).</p>", "Fenómenos",
   _g("Avisa que el fluido sale de su rango de uso.", "No cambia el cálculo, pero las propiedades pueden no valer.",
      "Las propiedades son extrapoladas o el fluido cambia químicamente.", "El de cada presentación.", "No aplica.",
      "Por encima: polimeriza, se degrada o se descompone.", ["Alertas"],
      ["Revise la temperatura de operación.", "Para el azufre use camisa de vapor de 3,5 a 4,5 bar g."],
      "Azufre a 175 °C: la viscosidad pasa de 7 a ~ 50.000 cP."),
   referencia=_REF, relacionadas=["fluidos_proceso"])
_e("fp_desgasificacion", "Desgasificación en la válvula",
   "<p>La amina rica y el glicol rico llevan gases absorbidos (H₂S, CO₂, hidrocarburos) que se liberan al bajar "
   "la presión en la válvula: el flujo sale bifásico y la capacidad real es menor que la de un líquido. La IEC "
   "60534-2-1 no cubre este caso.</p>", "Fenómenos",
   _g("Avisa que el líquido libera gas en la vena contracta.", "No cambia el Cv calculado: pide margen.",
      "El Cv necesario es mayor que el calculado como líquido.", "Siempre en amina rica y glicol rico.",
      "No aplica.", "No aplica.", ["Apertura", "Erosión"],
      ["Deje la apertura a caudal máximo en 70 a 80 % o menos.",
       "Ubique la válvula cerca del separador flash y con salida expandida."],
      "Válvula de nivel de la absorbedora de MDEA: trim 316 con Stellite y cuerpo 316."),
   referencia="API RP 945; práctica de plantas de aminas", relacionadas=["fluidos_proceso", "flashing"])
_e("fp_polimero_corte", "Polímero sensible al corte",
   "<p>Las soluciones de polímeros floculantes son no newtonianas: la viscosidad indicada es la aparente a bajo "
   "corte (conservadora para el Cv) y el corte intenso en la válvula rompe las cadenas.</p>", "Fenómenos",
   _g("Avisa que el corte en la válvula degrada el polímero.", "No cambia el cálculo.",
      "Una ΔP alta en la válvula reduce la eficacia del floculante.", "No hay umbral fijo.", "No aplica.",
      "No aplica.", ["Selección del tipo de válvula"],
      ["Prefiera ΔP bajas y válvulas de paso amplio (diafragma, pinch, bola segmentada).",
       "Si se puede, regule con la velocidad de la bomba."], "Solución madre al 0,5 % con ΔP de 3 bar: se degrada."),
   referencia=_REF, relacionadas=["fluidos_proceso"])
_e("fp_propiedades_estimadas", "Propiedades estimadas del fluido de proceso",
   "<p>Informa con qué método se estimaron SG, viscosidad, presión de vapor y Pc del fluido de proceso. Los "
   "valores típicos deben confirmarse con los datos del proceso o del laboratorio.</p>", "Fenómenos",
   _g("Indica de dónde salen las propiedades del fluido.", "Documenta el origen en la memoria y el informe.",
      "El cálculo usa valores típicos mientras no se cargue la caracterización real.", "No aplica.", "No aplica.",
      "No aplica.", ["Memoria de cálculo", "Informe técnico"],
      ["Cargue en la caracterización los datos del certificado."],
      "Crudo de 12 °API con la viscosidad del laboratorio: el FR y el Cv cambian respecto del típico."),
   referencia=_REF, relacionadas=["fluidos_proceso", "caracterizacion_fluido"])
