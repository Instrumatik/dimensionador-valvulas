"""Textos de ayuda en español para cada dato, coeficiente, opción y fenómeno.

Cada entrada tiene: título, explicación (HTML simple), fórmula (opcional),
valores típicos (opcional), referencia normativa y entradas relacionadas.
La clave de cada entrada es la misma que usa la interfaz (campo) o el
código de la alerta (fenómeno).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ayuda_guia import GUIA


@dataclass
class EntradaAyuda:
    titulo: str
    texto: str
    formula: str = ""
    tipicos: str = ""
    referencia: str = ""
    relacionadas: list[str] = field(default_factory=list)
    categoria: str = "Datos"


A: dict[str, EntradaAyuda] = {}


def _e(clave, titulo, texto, formula="", tipicos="", referencia="", relacionadas=(), categoria="Datos"):
    A[clave] = EntradaAyuda(titulo, texto, formula, tipicos, referencia, list(relacionadas), categoria)


# ---------------------------------------------------------------------------
# Conceptos generales
# ---------------------------------------------------------------------------
_e("sistema_unidades", "Sistema de unidades",
   "<p>El programa trabaja con el Sistema Internacional (SI) o con el sistema imperial. "
   "Al cambiar de sistema todos los campos se convierten automáticamente; además cada dato "
   "tiene su propio selector de unidad para combinar unidades si los datos del proyecto vienen "
   "mezclados.</p><p>Internamente todos los cálculos se hacen en kPa absolutos, K, m³/h, kg/h y "
   "mm, de modo que el resultado no depende de las unidades elegidas.</p>",
   relacionadas=["presion_abs_man", "kv_cv"], categoria="Conceptos")

_e("presion_abs_man", "Presión absoluta y manométrica",
   "<p>La <b>presión absoluta</b> se mide desde el vacío total. La <b>manométrica</b> se mide "
   "desde la presión atmosférica local: P<sub>abs</sub> = P<sub>man</sub> + P<sub>atm</sub>.</p>"
   "<p>Todas las ecuaciones de la norma usan presiones absolutas. Si ingresa una unidad "
   "manométrica (barg, psig, kPa g) el programa suma la presión atmosférica "
   "(101,325 kPa por defecto). Un error frecuente es cargar presión manométrica como absoluta: "
   "en servicios de baja presión cambia por completo el resultado.</p>",
   relacionadas=["P1", "P2"], categoria="Conceptos")

_e("kv_cv", "Coeficiente de caudal Kv y Cv",
   "<p>El coeficiente de caudal indica la capacidad de la válvula.</p><ul>"
   "<li><b>Kv</b>: caudal de agua a 5–40 °C, en m³/h, que pasa por la válvula con una caída de "
   "presión de 1 bar.</li><li><b>Cv</b>: caudal de agua a 60 °F, en galones US por minuto, que "
   "pasa con una caída de 1 psi.</li></ul><p>Ambos describen lo mismo en distintas unidades. "
   "El programa calcula el valor <b>requerido</b> por el proceso; la válvula elegida debe tener "
   "un valor nominal mayor, de modo que opere entre 20 % y 80 % de apertura aproximadamente.</p>",
   formula="Cv = 1,156 · Kv",
   referencia="IEC 60534-1; IEC 60534-2-1 cláusula 4",
   relacionadas=["Kv_nominal", "apertura"], categoria="Resultados")

# ---------------------------------------------------------------------------
# Datos del fluido
# ---------------------------------------------------------------------------
_e("tipo_fluido", "Tipo de fluido",
   "<p>Define qué ecuaciones, entradas y resultados se usan. Al cambiarlo, el programa muestra solo los "
   "datos que corresponden a ese tipo y los entregables se arman con ellos.</p><ul>"
   "<li><b>Líquido</b>: fluido incompresible. Flujo crítico por vaporización, cavitación (Kc, Kapp), "
   "flashing y ruido hidrodinámico (IEC 60534-8-4).</li>"
   "<li><b>Gas</b>: fluido compresible no condensable (aire, gas natural, N₂…). Se ingresa la masa molar "
   "o gravedad específica, γ y el factor de compresibilidad Z; la densidad se calcula con P·M/(Z·R·T).</li>"
   "<li><b>Vapor</b>: vapores de proceso (hidrocarburos, solventes, refrigerantes) cerca de su "
   "saturación, donde conviene ingresar la densidad real en lugar de Z.</li>"
   "<li><b>Vapor de agua (steam)</b>: propiedades IAPWS-95 automáticas; solo se ingresan caudal másico, "
   "presiones y temperatura (en blanco = vapor saturado seco).</li></ul>"
   "<p>En los tres compresibles se aplica el factor de expansión Y, el flujo crítico (sónico), el ruido "
   "aerodinámico IEC 60534-8-3 y los números de Mach.</p>",
   referencia="IEC 60534-2-1:2011 cláusulas 5 y 6",
   relacionadas=["fluido", "xT", "Y", "trim_ruido"], categoria="Conceptos")

_e("fluido", "Fluido",
   "<p>Seleccione el fluido de la lista para que el programa calcule automáticamente densidad, "
   "presión de vapor, presión crítica, viscosidad, masa molar, relación de calores "
   "específicos y factor de compresibilidad a las condiciones de entrada de cada caso.</p>"
   "<p>Elija <b>Definido por el usuario</b> para ingresar las propiedades a mano (mezclas, "
   "fluidos de proceso, datos de la hoja de datos del proyecto). Las propiedades provienen de "
   "la biblioteca CoolProp; para agua y vapor usa la formulación IAPWS-95.</p>"
   "<p>El fluido se define <b>solo aquí</b>: con la <b>calidad / variante</b> (qué agua es, o qué tipo de "
   "fluido definido por el usuario) y el <b>agua libre</b>, alimenta también la selección de materiales de la "
   "solapa 3, que no vuelve a preguntarlo.</p>",
   relacionadas=["rho", "Pv", "Pc", "viscosidad", "variante_fluido", "agua_libre", "composicion_gn"])

_e("composicion_gn", "Composición del gas natural",
   "<p>Con <b>Gas natural</b> en la lista, N25 calcula las propiedades de la mezcla con la ecuación de estado "
   "multicomponente de CoolProp (HEOS, de la familia GERG): masa molar, viscosidad, exponente isoentrópico, "
   "Z1 a la entrada y, por expansión isoentálpica, T2 y Z2 a la salida. Así el enfriamiento por "
   "Joule-Thomson del gas sale del cálculo sin cargarlo a mano.</p>"
   "<p>Escriba el % molar de cada componente separado por punto y coma, por ejemplo «Metano 90; Etano 5; "
   "Propano 2; Nitrógeno 1; Dióxido de carbono 1». Si la suma difiere de 100 % (hasta ±5 %) se normaliza. "
   "En blanco se usa una composición típica de gas seco de gasoducto, que no corresponde a ningún "
   "yacimiento: cargue la cromatografía del proyecto.</p>"
   "<p>Componentes posibles: metano, etano, propano, n-butano, isobutano, n-pentano, isopentano, n-hexano, "
   "nitrógeno, dióxido de carbono, sulfuro de hidrógeno, hidrógeno, helio, oxígeno y agua.</p>"
   "<p>Ejemplo: 90 % metano, de 70 a 20 bar a desde 27 °C da Z1 ≈ 0,86, T2 ≈ 2 °C y Z2 ≈ 0,94.</p>"
   "<p>Si el gas trae H₂S o CO₂, declárelos también como agentes en 3-Materiales para la selección "
   "según ISO 15156.</p>",
   tipicos="Gas de gasoducto: metano 85–96 %, etano 2–8 %, propano 0,5–3 %, N₂ y CO₂ 0–3 % cada uno",
   relacionadas=["fluido", "Z", "T2", "M"])

_e("caudal", "Caudal",
   "<p>Cantidad de fluido que debe pasar la válvula en cada caso de operación. Puede ingresarse "
   "como:</p><ul><li><b>Volumétrico</b> a condiciones de flujo (m³/h, gpm, L/s): para "
   "líquidos.</li><li><b>Másico</b> (kg/h, lb/h, t/h): para cualquier fluido; es la forma más "
   "segura en gases y vapor porque no depende de condiciones de referencia.</li>"
   "<li><b>Normal o estándar</b> (Nm³/h a 0 °C; Sm³/h a 15 °C; scfh a 60 °F): para gases. "
   "Verifique cuál de las condiciones de referencia usa su hoja de datos, porque entre Nm³/h y "
   "Sm³/h hay un 5,5 % de diferencia.</li></ul>"
   "<p>Ingrese los casos <b>mínimo</b>, <b>normal</b> y <b>máximo</b>. El máximo define el "
   "tamaño; el mínimo verifica que la válvula no quede trabajando casi cerrada.</p>",
   relacionadas=["casos", "apertura"])

_e("casos", "Casos de operación",
   "<p>Una válvula de control opera en un rango. Cargue al menos el caso máximo; se recomienda "
   "también el mínimo y el normal. Cada caso se calcula por separado con sus propias "
   "presiones y temperatura.</p><p>Criterio usado para seleccionar el diámetro automáticamente: "
   "el menor tamaño cuya apertura en el caso máximo no supere 85 %. Evite sumar márgenes de "
   "seguridad en varios lugares (caudal, ΔP y Cv) porque se obtiene una válvula "
   "sobredimensionada que controla mal.</p>",
   relacionadas=["caudal", "apertura"])

_e("P1", "Presión de entrada P1",
   "<p>Presión estática en la tubería aguas arriba de la válvula, medida a unos 2 diámetros de la "
   "brida de entrada, en el caso considerado. Debe ser la presión <b>con el caudal circulando</b>, "
   "no la presión de cierre de la bomba.</p>",
   referencia="IEC 60534-2-1 cláusula 4; tomas de presión según IEC 60534-2-3",
   relacionadas=["P2", "presion_abs_man", "dP"])

_e("P2", "Presión de salida P2",
   "<p>Presión estática en la tubería aguas abajo de la válvula, medida a unos 6 diámetros de la "
   "brida de salida. La diferencia P1 − P2 es la caída de presión disponible para la válvula, "
   "que resulta del balance hidráulico del sistema.</p><p>Si P2 es menor o igual que la presión "
   "de vapor del líquido habrá <b>flashing</b>.</p>",
   referencia="IEC 60534-2-1 cláusula 4",
   relacionadas=["P1", "dP", "flashing"])

_e("dP", "Caída de presión ΔP",
   "<p>ΔP = P1 − P2. En líquidos, cuando ΔP alcanza ΔP<sub>choked</sub> el caudal deja de "
   "aumentar (flujo crítico por vaporización) y se usa ΔP<sub>choked</sub> para dimensionar.</p>"
   "<p>Una práctica habitual es asignar a la válvula al menos 1/3 de la pérdida total del "
   "sistema dinámico, o un mínimo absoluto (por ejemplo 0,7 bar), para que tenga autoridad de "
   "control.</p>",
   formula="ΔP = P1 − P2", relacionadas=["dPchoked", "P1", "P2"], categoria="Resultados")

_e("T1", "Temperatura de entrada T1",
   "<p>Temperatura del fluido aguas arriba de la válvula. En líquidos determina la presión de vapor "
   "y la viscosidad; en gases la densidad. En vapor de agua, si la temperatura coincide con la de "
   "saturación a P1, el programa toma vapor saturado seco.</p>",
   relacionadas=["Pv", "rho"])

_e("rho", "Densidad a la entrada ρ1",
   "<p>Masa por unidad de volumen del fluido a P1 y T1. En líquidos se usa como densidad relativa "
   "ρ1/ρ0, con ρ0 = 999,1 kg/m³ (agua a 15 °C).</p><p>En gases, si no se ingresa, se calcula "
   "como ρ1 = P1·M / (Z·R·T1).</p>",
   formula="ρ1/ρ0 (líquidos);   ρ1 = P1·M/(Z·R·T1) (gases)",
   tipicos="Agua 15 °C: 999 kg/m³; gasolina: 720–760; crudo liviano: 820–870",
   relacionadas=["M", "Z"])

_e("Pv", "Presión de vapor Pv",
   "<p>Presión a la cual el líquido hierve a la temperatura de entrada T1. Es el dato que "
   "determina si habrá cavitación o flashing: si en algún punto dentro de la válvula la presión "
   "cae por debajo de Pv, se forman burbujas de vapor.</p><p>Para mezclas de hidrocarburos use la "
   "presión de burbuja de la mezcla.</p>",
   tipicos="Agua a 20 °C: 2,34 kPa a; a 100 °C: 101,3 kPa a; a 150 °C: 476 kPa a",
   relacionadas=["FF", "cavitacion", "flashing", "Pc"])

_e("Pc", "Presión crítica Pc",
   "<p>Presión en el punto crítico termodinámico del fluido. Junto con Pv se usa para calcular el "
   "factor FF, que estima la presión en la vena contracta cuando el líquido vaporiza.</p>",
   tipicos="Agua: 22 064 kPa a; propano: 4 251; amoníaco: 11 333",
   relacionadas=["FF", "Pv"])

_e("viscosidad", "Viscosidad",
   "<p>Resistencia del fluido a fluir. Se usa para calcular el número de Reynolds de la válvula. "
   "Si Rev &lt; 10 000 el flujo no es completamente turbulento y la válvula necesita más "
   "capacidad (factor FR &lt; 1).</p><p>Viscosidad cinemática ν = μ/ρ. 1 cSt = 10⁻⁶ m²/s; "
   "1 cP = 10⁻³ Pa·s.</p>",
   tipicos="Agua 20 °C: 1 cP; aceite liviano: 10–50 cP; gases: 0,01–0,03 cP",
   relacionadas=["Rev", "FR"])

_e("M", "Masa molar o gravedad específica",
   "<p>Masa de un kilomol del gas (kg/kmol). Para mezclas use el promedio ponderado por fracción "
   "molar. Se relaciona con la gravedad específica respecto del aire: SG = M / 28,96.</p>"
   "<p>Elija la unidad «SG (aire = 1)» para ingresar la gravedad específica; el programa la convierte "
   "a masa molar.</p>",
   tipicos="Aire 28,96; gas natural 16–20; vapor de agua 18,015; CO₂ 44,01",
   relacionadas=["rho", "Z"])

_e("gamma", "Relación de calores específicos γ",
   "<p>γ = cp / cv del gas a condiciones de entrada. Afecta la caída de presión a la que el gas "
   "llega a velocidad sónica a través del factor Fγ = γ / 1,40.</p><p>Con un fluido de la lista y en "
   "vapor de agua el programa usa el <b>exponente isoentrópico</b> κ = ρ·c²/P, que es el valor correcto "
   "para gases reales y vapores (en gas ideal κ = cp/cv). Cerca de la saturación cp/cv lo sobrestima: "
   "en vapor saturado a 10 bar cp/cv ≈ 1,41 y κ ≈ 1,29.</p>",
   formula="Fγ = γ / 1,40",
   tipicos="Aire 1,40; gas natural 1,27–1,31; vapor de agua 1,30–1,33; CO₂ 1,30",
   referencia="IEC 60534-2-1 ec. (14)",
   relacionadas=["Fgamma", "xchoked"])

_e("Z", "Factor de compresibilidad Z",
   "<p>Corrige la ley de gases ideales: P·v = Z·R·T. Vale 1 para gas ideal; se aparta de 1 a "
   "presiones altas o cerca de la condensación. Un Z mal estimado produce el mismo error "
   "porcentual en la densidad.</p>",
   tipicos="Gases a baja presión: 0,98–1,00; gas natural a 70 bar: 0,85–0,90",
   relacionadas=["rho", "M"])

_e("mu", "Viscosidad dinámica del gas μ",
   "<p>Se usa solo para verificar el régimen (número de Reynolds). En la mayoría de los "
   "servicios de gas el flujo es turbulento y su valor exacto no influye.</p>",
   tipicos="Gases: 0,01–0,03 cP",
   relacionadas=["Rev"])

# ---------------------------------------------------------------------------
# Datos de la válvula
# ---------------------------------------------------------------------------
_e("estilo", "Estilo de válvula",
   "<p>Tipo constructivo de la válvula y de sus internos. Determina los factores FL, xT y Fd y "
   "la característica inherente. El programa trae estilos <b>genéricos</b> con los valores "
   "típicos de la Tabla 2 de IEC 60534-2-1, sin datos de ningún fabricante.</p>"
   "<p>Orientación general:</p><ul>"
   "<li><b>Globo</b>: mejor control y mayor FL (más resistentes a cavitación); menor capacidad "
   "por diámetro.</li><li><b>Angular</b>: preferida para flashing, fluidos con sólidos y "
   "descarga a recipiente.</li><li><b>Mariposa y bola</b>: gran capacidad y bajo costo en "
   "diámetros grandes; FL bajo, por lo que cavitan antes.</li>"
   "<li><b>Jaulas multiorificio y multietapa</b>: para cavitación y ruido.</li></ul>"
   "<p>Cuando tenga la oferta del proveedor, reemplace los factores por los certificados.</p>",
   relacionadas=["FL", "xT", "Fd", "caracteristica"])

_e("FL", "Factor de recuperación de presión del líquido FL",
   "<p>Indica cuánto se recupera la presión entre la vena contracta (punto de menor presión "
   "dentro de la válvula) y la salida. FL alto (cercano a 1) significa poca recuperación: la "
   "presión mínima interna no cae mucho por debajo de P2 y la válvula resiste mejor la "
   "cavitación.</p><p>FL define la caída de presión máxima útil en líquidos "
   "(ΔP<sub>choked</sub>).</p>",
   formula="FL = √((P1 − P2)/(P1 − Pvc))",
   tipicos="Globo 0,80–0,90; multietapa 0,97; mariposa 0,62–0,70; bola 0,60–0,74",
   referencia="IEC 60534-2-1 cláusula 3 y Tabla 2",
   relacionadas=["dPchoked", "FLP", "cavitacion"], categoria="Coeficientes")

_e("xT", "Factor de caída de presión crítica xT",
   "<p>Relación ΔP/P1 a la cual un gas con γ = 1,40 alcanza flujo crítico (sónico) en una "
   "válvula sin reductores. Cuanto mayor es xT, más caída de presión puede aprovechar la "
   "válvula antes de bloquearse.</p>",
   tipicos="Globo 0,55–0,75; mariposa 0,35–0,42; bola segmentada 0,30",
   referencia="IEC 60534-2-1 cláusula 6 y Tabla 2",
   relacionadas=["xchoked", "xTP", "Y"], categoria="Coeficientes")

_e("Fd", "Modificador de estilo de válvula Fd",
   "<p>Relación entre el diámetro hidráulico de un pasaje de la válvula y el diámetro de un "
   "orificio circular de igual área. Interviene en el número de Reynolds y en el inicio de "
   "cavitación. Valores bajos corresponden a muchos pasajes pequeños (jaulas "
   "multiorificio).</p>",
   tipicos="Un solo pasaje 1,0; doble asiento 0,7; jaula 60 orificios 0,13",
   referencia="IEC 60534-2-1 Anexo A",
   relacionadas=["Rev", "xFz"], categoria="Coeficientes")

_e("xFz", "Cavitación incipiente xFz",
   "<p>Valor de xF = ΔP/(P1 − Pv) a partir del cual pueden aparecer las primeras burbujas (régimen "
   "incipiente de ISA-RP75.23). Normalmente no daña. El programa lo estima con la expresión típica de "
   "IEC 60534-8-4 y lo corrige por la presión de entrada (xFzp1); se muestra como resultado.</p>"
   "<p>Si Kapp supera xFzp1 pero no Kc, la condición es «cavitación incipiente». El ruido se calcula "
   "con el Kc del trim; solo si Kc está en blanco se usa este xFz típico (resultado conservador). En "
   "multietapa se toma igual a Kc.</p>",
   formula="xFz ≈ 0,90 / √(1 + 3·Fd·√(Cv/(N34·FL))), N34 = 1,17;   xFzp1 = xFz·(6·10⁵ Pa / P1)^0,125",
   referencia="IEC 60534-8-4; ISA-RP75.23",
   relacionadas=["cavitacion_incipiente", "Kc", "sigma"], categoria="Coeficientes")

_e("tamano", "Diámetro de la válvula",
   "<p>Diámetro nominal de las conexiones de la válvula. Elija <b>Automático</b> para que el "
   "programa recorra los tamaños estándar y proponga el menor que cumpla el caso máximo con "
   "apertura ≤ 85 %, sin superar el diámetro de la línea. Con un diámetro fijo el programa "
   "verifica esa válvula.</p>",
   relacionadas=["apertura", "D1", "Kv_nominal"])

_e("trim_size", "Tamaño del trim (diámetro del puerto)",
   "<p>Diámetro del orificio del asiento por el que pasa el fluido. Junto con la carrera define la "
   "capacidad del trim y es el dato con que el fabricante identifica el juego de internos.</p>"
   "<p>En blanco el programa lo <b>estima</b> con la <b>tabla de capacidad</b> (desde v0.12.0): cada familia "
   "de trim (contorneado, jaula, jaula de orificios, multietapa) tiene, por diámetro nominal, el puerto pleno, la "
   "carrera y el Cv típicos, tomados como mediana de datos publicados de fabricantes. Puerto, carrera y Cv van "
   "juntos: si el Cv nominal es menor que el típico (trim reducido), el puerto es el que da ese Cv con su "
   "carrera típica. Se informa en pulgadas, redondeado al 1/16 más cercano, y en milímetros.</p><p>En válvulas rotativas el dato es el orificio de la bola, el "
   "disco de la mariposa o el asiento del tapón excéntrico.</p><p>Si tiene la hoja del fabricante, cargue "
   "el puerto certificado: reemplaza al estimado en la pantalla y en los documentos. Si es menor que el del "
   "trim completo, el programa lo trata como <b>trim reducido</b> y calcula el Cv con el puerto reducido "
   "(ver «Cv certificado del trim reducido»).</p>",
   tipicos="Pleno contorneado: 3\" 2 5/8 in, 4\" 3 1/2 in, 6\" 5 in. Pleno de jaula: 3\" 3 7/16 in, "
   "4\" 4 3/8 in, 6\" 6 in",
   relacionadas=["carrera_nominal", "tamano", "Kv_nominal", "Cv_reducido", "capacidad_trim"])

_e("Cv_reducido", "Trim reducido: puerto reducido y Cv con el puerto reducido",
   "<p>Un <b>trim reducido</b> monta en el cuerpo un asiento con puerto menor que el del trim completo. Se usa "
   "cuando el caudal es chico para el diámetro de la línea o del cuerpo (por ejemplo, para que la válvula no "
   "trabaje pegada al asiento) o en servicios con cavitación y flujo estrangulado.</p>"
   "<p>El programa muestra por separado:</p><ul>"
   "<li><b>Trim completo típico</b>: puerto y Cv típicos del estilo para el diámetro de la válvula.</li>"
   "<li><b>Trim reducido</b>: el puerto certificado cargado arriba, cuando es menor que el típico.</li>"
   "<li><b>Cv con el puerto reducido</b>: el certificado que se carga en esta celda o, si queda en blanco, el "
   "típico de ese puerto y esa carrera (tabla de capacidad): el paso por el asiento y el paso lateral que "
   "descubre el obturador se suman como dos restricciones en serie.</li></ul>"
   "<p>Ese Cv reemplaza al típico en la apertura estimada de cada caso, la carrera de operación, la curva de Cv, "
   "las alertas de válvula sobredimensionada o subdimensionada y los documentos. El actuador usa el puerto "
   "reducido en el desbalance y la carga de asiento.</p>"
   "<p>Hasta v0.11.0 el programa escalaba el Cv con la relación de áreas, que subestima mucho los puertos "
   "chicos (un 3\" con puerto 2 5/16\" daba Cv 49). Con la tabla de capacidad el Cv del reducido se calcula "
   "con su puerto y su carrera. Aun así, el Cv de un trim reducido varía mucho entre fabricantes (en jaulas, "
   "de la mitad a 1,5 veces el típico): cargue el Cv certificado de la hoja de datos en cuanto lo tenga. Si "
   "carga solo el Cv certificado, el puerto se estima con la tabla.</p>",
   formula="1/Cv² = 1/(Kp·d²)² + 1/(Kh·π·d·h)²   (d puerto y h carrera en pulgadas; Kp, Kh por familia)",
   tipicos="Jaula, cuerpo de 3\" con puerto 2 5/16\" y carrera 1 1/8\": Cv típico ≈ 67 lineal (fabricantes: "
   "≈ 40 a 102)",
   relacionadas=["trim_size", "carrera_nominal", "Kv_nominal", "capacidad_trim"])

_e("carrera_nominal", "Carrera nominal y carrera de operación del vástago",
   "<p>La <b>carrera nominal</b> (rated travel) es el recorrido total del vástago entre la válvula "
   "cerrada y abierta del todo. La <b>carrera de operación</b> de cada caso es la apertura estimada × la "
   "carrera nominal, y se muestra en milímetros y en pulgadas.</p><p>En blanco el programa usa la carrera "
   "normalizada habitual de un trim pleno del tamaño equivalente al puerto, de la tabla de capacidad de "
   "cada familia (contorneado, jaula, orificios, multietapa); un puerto reducido lleva la carrera del pleno "
   "del tamaño cuyo puerto es ese.</p><p>En válvulas rotativas la carrera es la rotación del eje (60°, 70° o 90° según el "
   "estilo).</p><p>La carrera define la carrera del actuador y la calibración del posicionador: confirme "
   "la certificada con el fabricante.</p>",
   tipicos="Contorneado pleno: 2\" 0,8 in (20 mm); 4\" 1 1/2 in (38 mm); 8\" 2 1/2 in (64 mm). Jaula: 4\" "
   "2 in (51 mm); 8\" 2 1/2 in",
   relacionadas=["trim_size", "apertura", "capacidad_trim"])

_e("D1", "Diámetro interior de la tubería",
   "<p>Diámetro interior de la tubería aguas arriba (D1) y aguas abajo (D2). Si son mayores que la "
   "válvula se consideran reductores concéntricos y se calculan FP, FLP y xTP. Dejar en blanco "
   "equivale a línea del mismo tamaño que la válvula.</p><p>El diámetro de salida también se "
   "usa para calcular velocidades y verificar API RP 14E.</p>",
   tipicos="DI cédula 40 (ASME B36.10M): 2\" 52,5 mm; 4\" 102,3 mm; 6\" 154,1 mm; 8\" 202,7 mm",
   relacionadas=["FP", "FLP", "xTP", "erosional_api14e"])

_e("Kv_nominal", "Capacidad nominal de la válvula",
   "<p>Kv (o Cv) de la válvula completamente abierta. Si se deja en blanco el programa usa un "
   "valor <b>típico</b> del estilo, suficiente para preseleccionar el tamaño. En globo y ángulo (contorneado, "
   "jaula, jaula de orificios y multietapa) el típico sale de la <b>tabla de capacidad</b> de N25: la mediana, "
   "por tamaño, de los Cv publicados por varios fabricantes, con la característica elegida (ver «Tabla de "
   "capacidad: Cv, puerto y carrera»). En rotativas se usa Cv ≈ Cd·d² (d en pulgadas). Para verificar una "
   "válvula ofertada, ingrese su valor certificado y fije el diámetro.</p>",
   relacionadas=["apertura", "kv_cv", "capacidad_trim"])

_e("caracteristica", "Característica inherente",
   "<p>Relación entre la carrera y la capacidad a caída de presión constante.</p><ul>"
   "<li><b>Isoporcentual</b>: cada incremento igual de carrera aumenta la capacidad en el mismo "
   "porcentaje. Es la más usada cuando la caída de presión de la válvula disminuye al aumentar "
   "el caudal.</li><li><b>Lineal</b>: capacidad proporcional a la carrera. Apta cuando la "
   "válvula toma casi toda la pérdida del sistema (control de nivel, by-pass).</li>"
   "<li><b>Parabólica modificada</b>: intermedia entre lineal e isoporcentual; el programa la aproxima "
   "con φ = 1/R + (1 − 1/R)·h². Solo obturadores contorneados.</li>"
   "<li><b>Apertura rápida</b>: para servicios todo-nada.</li></ul>"
   "<p>Desde v0.13.0 la lista solo habilita las características que ofrece el obturador o la jaula elegidos "
   "(por ejemplo, el obturador en V no ofrece apertura rápida y las jaulas multietapa solo lineal).</p>"
   "<p><b>Tres datos independientes</b> (desde v0.12.0): el <b>estilo de trim</b> es la geometría de los "
   "internos (contorneado, jaula, orificios, multietapa); el <b>sentido de flujo</b> dice si el fluido tiende "
   "a abrir o a cerrar el obturador; la <b>característica</b> es la curva de capacidad frente a la carrera. "
   "En válvulas de vástago se elige lineal, isoporcentual o apertura rápida para cualquier estilo; en "
   "rotativas la fija la forma del disco, la bola o el segmento.</p><p>La característica también cambia el "
   "Cv a carrera nominal según la familia (datos de fabricantes, mismo puerto): en contorneados el lineal y "
   "el isoporcentual tienen el mismo Cv; en jaulas el isoporcentual tiene ≈ 0,89 veces el del lineal y la "
   "apertura rápida ≈ 1,09 veces; en jaulas de orificios el isoporcentual ≈ 0,75 veces. En contorneados "
   "cambia además xT (0,72 lineal, 0,75 isoporcentual con flujo que tiende a abrir; IEC 60534-2-1).</p>",
   formula="Isoporcentual: φ = R^(h−1);   Lineal: φ = 1/R + (1 − 1/R)·h",
   relacionadas=["apertura", "rangeabilidad"])

_e("rangeabilidad", "Rangeabilidad inherente R",
   "<p>Relación entre la capacidad máxima y la mínima controlable de la característica. Se usa "
   "para estimar la apertura requerida.</p>", tipicos="Globo 30–50; rotativas 50–100",
   relacionadas=["caracteristica"])

_e("C_api14e", "Constante empírica C de API RP 14E",
   "<p>Constante de la fórmula de velocidad erosional Ve = C/√ρm (ft/s, lb/ft³).</p><ul>"
   "<li>C = 100: servicio continuo (valor conservador por defecto).</li>"
   "<li>C = 125: servicio intermitente.</li>"
   "<li>C = 150 a 200: servicio continuo sin sólidos y con corrosión controlada o materiales "
   "resistentes, si se justifica.</li></ul>",
   referencia="API RP 14E sección 2.5", relacionadas=["erosional_api14e"])

# ---------------------------------------------------------------------------
# Resultados y factores calculados
# ---------------------------------------------------------------------------
_e("FF", "Factor de presión crítica del líquido FF",
   "<p>Relación entre la presión en la vena contracta cuando el flujo está bloqueado y la "
   "presión de vapor. Se estima con Pv y Pc.</p>",
   formula="FF = 0,96 − 0,28·√(Pv/Pc)", referencia="IEC 60534-2-1 ec. (4)",
   relacionadas=["Pv", "Pc", "dPchoked"], categoria="Resultados")

_e("dPchoked", "Caída de presión de flujo crítico ΔPchoked",
   "<p>Máxima caída de presión que aumenta el caudal en un líquido. Más allá de este valor la "
   "vena contracta está a la presión de vaporización y el caudal queda limitado (flujo "
   "bloqueado o crítico). Si ΔP ≥ ΔPchoked, la válvula se dimensiona con ΔPchoked.</p>"
   "<p><b>En gases y vapores</b> es la caída de presión a la que el gas llega a velocidad sónica en la "
   "vena contracta: ΔPchoked = Fγ·xTP·P1. No es lo mismo que xT: xT es un factor sin unidades (una "
   "relación ΔP/P1 medida con aire) y ΔPchoked es una presión. Por ejemplo, con P1 = 10 bar a, Fγ = 0,93 "
   "y xT = 0,72, ΔPchoked = 0,93·0,72·10 ≈ 6,7 bar.</p>",
   formula="Líquidos: ΔPchoked = (FLP/FP)²·(P1 − FF·Pv);   gases: ΔPchoked = Fγ·xTP·P1", referencia="IEC 60534-2-1 ec. (3)",
   relacionadas=["FL", "FF", "cavitacion", "flashing"], categoria="Resultados")

_e("FP", "Factor de geometría de tubería FP",
   "<p>Corrige la capacidad cuando la válvula se instala entre reductores (válvula menor que la "
   "línea). Siempre FP ≤ 1: los reductores consumen parte de la caída de presión.</p>",
   formula="FP = 1/√(1 + Σζ/N2·(C/d²)²);  Σζ = ζ1 + ζ2 + ζB1 − ζB2",
   referencia="IEC 60534-2-1 cláusula 7", relacionadas=["D1", "FLP", "xTP"], categoria="Resultados")

_e("FLP", "FL combinado con reductores FLP",
   "<p>Factor de recuperación de presión del conjunto válvula + reductores. Reemplaza a FL en el "
   "cálculo de flujo crítico.</p>",
   formula="FLP = FL/√(1 + FL²/N2·(ζ1 + ζB1)·(C/d²)²)", referencia="IEC 60534-2-1 ec. (24)",
   relacionadas=["FL", "FP"], categoria="Resultados")

_e("x", "Relación de caída de presión x",
   "<p>x = ΔP/P1 en gases y vapores. Cuando alcanza x<sub>choked</sub> el flujo se vuelve "
   "sónico.</p>", formula="x = (P1 − P2)/P1", relacionadas=["xchoked", "Y"], categoria="Resultados")

_e("xchoked", "Relación de caída de presión crítica xchoked",
   "<p>Valor de x a partir del cual el gas alcanza velocidad sónica en la vena contracta y el "
   "caudal ya no aumenta al bajar P2.</p>", formula="xchoked = Fγ·xTP",
   referencia="IEC 60534-2-1 ec. (13)", relacionadas=["xT", "Fgamma", "gas_bloqueado"],
   categoria="Resultados")

_e("xTP", "xT combinado con reductores xTP",
   "<p>xT del conjunto válvula + reductores.</p>",
   formula="xTP = (xT/FP²)/(1 + xT·ζi/N5·(C/d²)²)", referencia="IEC 60534-2-1 ec. (26)",
   relacionadas=["xT", "FP"], categoria="Resultados")

_e("Fgamma", "Factor de calores específicos Fγ",
   "<p>El factor de caída de presión crítica xT de una válvula se mide en el banco de ensayo con aire, cuyo "
   "γ = cp/cv vale 1,40. Un gas con otro γ se expande de otra manera en la vena contracta y llega a "
   "velocidad sónica con otra caída relativa. Fγ corrige ese efecto: es el cociente entre el γ del gas real "
   "y el del aire.</p><p>Dónde interviene:</p><ul>"
   "<li><b>Límite de flujo estrangulado</b>: xchoked = Fγ·xTP. Con Fγ &lt; 1 (vapor, hidrocarburos) el gas "
   "bloquea con menos caída que el aire; con Fγ &gt; 1 (helio, argón) con más.</li>"
   "<li><b>ΔP choked del gas</b>: ΔPchoked = Fγ·xTP·P1.</li>"
   "<li><b>Factor de expansión</b>: Y = 1 − x/(3·Fγ·xTP), y el x de cálculo se limita a Fγ·xTP.</li></ul>"
   "<p>El programa toma γ de la biblioteca de propiedades a P1 y T1 (o el valor cargado) y calcula Fγ en cada "
   "caso. Use γ a las condiciones de entrada: a alta presión γ real puede diferir bastante del de gas "
   "ideal.</p>",
   formula="Fγ = γ/1,40;   xchoked = Fγ·xTP;   Y = 1 − x/(3·Fγ·xTP)",
   tipicos="Aire, N₂, H₂ ≈ 1,00; metano ≈ 0,94; gas natural ≈ 0,93; vapor de agua ≈ 0,93–0,95; "
   "CO₂ ≈ 0,92; propano ≈ 0,81; helio ≈ 1,19",
   referencia="IEC 60534-2-1 ec. (13) a (15)",
   relacionadas=["gamma", "xT", "xchoked", "Y", "dPchoked"], categoria="Resultados")

_e("Y", "Factor de expansión Y",
   "<p>Tiene en cuenta el cambio de densidad del gas desde la entrada hasta la vena contracta. "
   "Vale 1 con caída de presión nula y 2/3 con flujo crítico.</p>",
   formula="Y = 1 − x/(3·xchoked)", referencia="IEC 60534-2-1 ec. (15)",
   relacionadas=["x", "xchoked"], categoria="Resultados")

_e("Rev", "Número de Reynolds de la válvula Rev",
   "<p>Indica el régimen de flujo en la válvula. Con Rev ≥ 10 000 el flujo es turbulento "
   "(caso habitual). Por debajo, el flujo es de transición o laminar (líquidos viscosos o "
   "caudales muy bajos) y se aplica la corrección FR.</p>",
   formula="Rev = N4·Fd·Q/(ν·√(C·FL)) · (FL²·C²/(N2·D⁴) + 1)^¼",
   referencia="IEC 60534-2-1 ec. (28)", relacionadas=["FR", "viscosidad", "Fd"], categoria="Resultados")

_e("FR", "Factor de número de Reynolds FR",
   "<p>Reduce la capacidad efectiva de la válvula en régimen no turbulento. FR = 1 en flujo "
   "turbulento; el Kv requerido se divide por FR.</p>", referencia="IEC 60534-2-1 cláusula 9",
   relacionadas=["Rev", "flujo_no_turbulento"], categoria="Resultados")

_e("xF", "Relación diferencial de presión xF",
   "<p>xF = ΔP/(P1 − Pv). Se compara con xFz (inicio de cavitación) y con FL² (flujo "
   "bloqueado).</p>", formula="xF = ΔP/(P1 − Pv)", referencia="IEC 60534-8-4",
   relacionadas=["xFz", "sigma", "cavitacion"], categoria="Resultados")

_e("sigma", "Índice de cavitación σ",
   "<p>σ = (P1 − Pv)/(P1 − P2) = 1/xF. Cuanto menor σ, más intensa la cavitación. ISA-RP75.23 "
   "define niveles característicos: σi (inicio), σc (constante), σmv (vibración máxima) y σch "
   "(bloqueo). El programa informa σ y sus límites para comparar con datos de ensayo del "
   "fabricante si los tiene.</p>", formula="σ = (P1 − Pv)/(P1 − P2)",
   referencia="ISA-RP75.23", relacionadas=["xF", "cavitacion"], categoria="Resultados")

_e("apertura", "Apertura requerida",
   "<p>Carrera estimada de la válvula (0 % cerrada, 100 % abierta) para el caso, a partir del "
   "Kv requerido, el Kv nominal y la característica inherente. Criterios orientativos: "
   "isoporcentual 15–85 %, lineal 10–80 %. Aperturas sobre 90 % indican válvula chica; "
   "por debajo de 10 % válvula sobredimensionada.</p><p>Nota: los factores FL y xT también "
   "varían con la carrera; el cálculo usa los valores a carrera nominal.</p>",
   relacionadas=["caracteristica", "Kv_nominal", "subdimensionada", "apertura_baja"],
   categoria="Resultados")

_e("memoria", "Memoria de cálculo",
   "<p>Lista ordenada de todos los valores intermedios de cada caso, con la fórmula y la "
   "cláusula de la norma que los produce. Permite a un revisor verificar el cálculo a mano.</p>",
   categoria="Conceptos")

# ---------------------------------------------------------------------------
# Fenómenos (códigos de alerta)
# ---------------------------------------------------------------------------
_e("cavitacion", "Cavitación",
   "<p><b>Qué es.</b> Al pasar por el orificio de la válvula el líquido se acelera y su presión "
   "cae. Si en la vena contracta la presión baja de la presión de vapor, se forman burbujas. "
   "Aguas abajo la presión se recupera por encima de Pv y las burbujas <b>colapsan "
   "(implosionan)</b>, generando microchorros y ondas de presión de miles de bar sobre las "
   "superficies cercanas.</p><p><b>Consecuencias.</b> Erosión con aspecto de picaduras o "
   "esponja en obturador, asiento y cuerpo; ruido como de grava; vibración; pérdida de "
   "capacidad.</p><p><b>Cómo se mide la intensidad.</b> Con xF = ΔP/(P1 − Pv): por debajo de "
   "xFzp1 no hay cavitación; entre xFzp1 y FL² la intensidad crece (0 a 100 %); al llegar a FL² "
   "hay cavitación plena y flujo bloqueado. El programa clasifica 0–33 % leve, 33–66 % moderada y "
   "más de 66 % severa. El daño también crece con la presión de colapso (P2 − Pv) y con el "
   "tamaño de la válvula.</p><p><b>Soluciones</b> (de menor a mayor costo): internos endurecidos; "
   "estilo con FL más alto; internos anticavitación multiorificio; internos multietapa; "
   "orificio de contrapresión o válvulas en serie; reubicar la válvula a un punto de mayor "
   "presión o bajar la temperatura.</p>",
   referencia="IEC 60534-8-4; ISA-RP75.23; IEC 60534-2-1",
   relacionadas=["xFz", "sigma", "FL", "flashing"], categoria="Fenómenos")

_e("cavitacion_proxima", "Cerca del inicio de cavitación",
   "<p>El servicio no cavita, pero Kapp está a menos del 20 % del Kc del trim. Variaciones normales de "
   "operación (mayor temperatura, menor P2) pueden hacerlo cavitar.</p>",
   relacionadas=["cavitacion", "Kc"], categoria="Fenómenos")

_e("desbalance_fuerza", "Fuerza de desbalance alta",
   "<p>Con trim desbalanceado, ΔP mayor que 10 bar y válvula de 3\" o más, la fuerza del fluido sobre "
   "el obturador es grande. Se estima con F ≈ ΔP·π·d²/4 y el puerto igual al diámetro de la válvula "
   "(orientativo). El actuador resulta grande y la estabilidad cerca del asiento empeora.</p>",
   formula="F ≈ ΔP·π·d²/4", relacionadas=["balance"], categoria="Fenómenos")

_e("balance_sin_jaula", "Trim balanceado sin jaula",
   "<p>El balanceo se fabrica casi siempre en obturadores guiados por jaula, porque el sello trabaja "
   "contra el interior de la jaula. Elija un trim de jaula o confirme con el fabricante.</p>",
   relacionadas=["balance", "trim"], categoria="Fenómenos")

_e("balance_cierre", "Trim balanceado y clase de cierre alta",
   "<p>El sello de balanceo agrega una vía de fuga además del asiento. Con trim balanceado la clase "
   "habitual es IV; las clases V y VI requieren un sello especial o asiento blando, a confirmar con el "
   "fabricante.</p>", relacionadas=["balance", "clase_cierre"], categoria="Fenómenos")

_e("balance_temperatura", "Sello de balanceo y temperatura",
   "<p>La temperatura de diseño supera unos 232 °C, límite práctico del sello de balanceo de PTFE. "
   "Especifique sello de grafito o metálico y confirme la clase de cierre que se obtiene.</p>",
   relacionadas=["balance", "clase_cierre"], categoria="Fenómenos")

_e("cavitacion_incipiente", "Cavitación incipiente",
   "<p>Kapp supera el inicio de cavitación incipiente xFzp1 (típico de IEC 60534-8-4) pero no el Kc del "
   "trim. Pueden formarse burbujas aisladas, normalmente sin daño; por eso no se emite la alerta de "
   "cavitación.</p><p>Con ΔP mayor que 10 bar se emite como advertencia: muchas especificaciones piden "
   "trim anticavitación ya en este régimen. Confirme el Kc certificado del trim con el fabricante.</p>",
   referencia="ISA-RP75.23 (σi); IEC 60534-8-4",
   relacionadas=["xFz", "Kc", "cavitacion"], categoria="Fenómenos")

_e("flashing", "Flashing (vaporización instantánea)",
   "<p><b>Qué es.</b> Ocurre cuando la presión de salida P2 es menor o igual que la presión de "
   "vapor: el líquido se vaporiza en la válvula y <b>no vuelve a condensar</b>. Aguas abajo "
   "circula una mezcla de líquido y vapor a alta velocidad.</p><p><b>Consecuencias.</b> Erosión "
   "con superficies lisas y brillantes, como pulidas, en internos, cuerpo y tubería de salida; "
   "flujo bloqueado (el caudal no aumenta al bajar P2).</p><p><b>Intensidad.</b> Depende de la "
   "fracción de líquido que vaporiza: el programa la calcula con un balance de entalpía "
   "(expansión isoentálpica) cuando conoce el fluido.</p><p><b>Soluciones.</b> No se elimina con "
   "internos anticavitación, porque depende de P2 respecto de Pv. Se mitiga con válvula "
   "angular flujo-cierra descargando a recipiente o a tubería de mayor diámetro, materiales "
   "duros (aleaciones Cr-Mo, estelita, carburo de tungsteno), baja velocidad de salida; o se "
   "evita elevando P2 o subenfriando el líquido.</p>",
   referencia="IEC 60534-2-1; ISA-RP75.23",
   relacionadas=["Pv", "P2", "erosional_api14e"], categoria="Fenómenos")

_e("gas_bloqueado", "Flujo crítico (sónico) de gas",
   "<p>Cuando x ≥ x<sub>choked</sub> el gas alcanza la velocidad del sonido en la vena contracta. "
   "Bajar más la presión de salida no aumenta el caudal. No es en sí un error, pero es un "
   "régimen de alta energía acústica: verifique ruido y vibración. Para dimensionar se usa "
   "x<sub>choked</sub> y Y = 0,667.</p>",
   relacionadas=["xchoked", "mach_salida"], categoria="Fenómenos")

_e("mach_salida", "Velocidad alta de gas a la salida",
   "<p>El número de Mach es la velocidad del gas dividida por la velocidad del sonido en él. En "
   "la conexión de salida de la válvula se recomienda Mach ≤ 0,3 para servicios de bajo ruido y "
   "no superar 0,5 en general; valores mayores generan ruido, vibración y fatiga en la tubería. "
   "Se corrige con un diámetro de válvula o de salida mayor, o repartiendo la caída de presión.</p>",
   referencia="IEC 60534-8-3", relacionadas=["gas_bloqueado"], categoria="Fenómenos")

_e("salida_sonica", "Flujo sónico en la salida de la válvula",
   "<p>Un gas no puede superar la velocidad del sonido en la sección más estrecha por la que "
   "pasa. Si con la presión P2 y el área de salida la velocidad calculada resulta mayor que la "
   "del sonido, la salida de la válvula se bloquea a Mach 1: la presión en la salida sube por "
   "encima de P2 y el gas termina de expandirse en la tubería, con ruido y vibración intensos. "
   "El programa informa entonces Mach 1 y v = c, e indica el área mínima para una salida "
   "subsónica. Si el área fue ingresada a mano, verifique primero su unidad.</p>",
   referencia="IEC 60534-8-3", relacionadas=["mach_salida", "area_salida"], categoria="Fenómenos")

_e("area_salida_rango", "Área de salida fuera del rango esperado",
   "<p>El área de salida ingresada difiere mucho del área del diámetro nominal de la válvula "
   "(menos de 0,2 o más de 1,6 veces). Suele indicar una unidad equivocada, por ejemplo un "
   "valor en in² ingresado con la unidad mm². El área afecta la velocidad y el Mach en la "
   "salida de la válvula y el ruido aerodinámico.</p>",
   relacionadas=["area_salida", "salida_sonica"], categoria="Fenómenos")

_e("velocidad_liquido", "Velocidad alta de líquido",
   "<p>Velocidades elevadas en la salida de la válvula causan erosión, vibración y golpe de "
   "ariete al cerrar. Referencias usuales: hasta 9 m/s (30 ft/s) para líquidos limpios en la "
   "conexión de la válvula; menos si hay sólidos.</p>", categoria="Fenómenos")

_e("erosional_api14e", "Velocidad erosional (API RP 14E)",
   "<p>API RP 14E establece una velocidad máxima para tuberías con flujo bifásico o con riesgo de "
   "erosión: Ve = C/√ρm, con Ve en ft/s y ρm densidad de la mezcla en lb/ft³. Superarla acelera "
   "la pérdida de espesor en codos, tes y reducciones aguas abajo.</p>",
   formula="Ve = C / √ρm", referencia="API RP 14E sección 2.5",
   relacionadas=["C_api14e", "flashing"], categoria="Fenómenos")

_e("flujo_no_turbulento", "Flujo no turbulento",
   "<p>Con Rev &lt; 10 000 las fuerzas viscosas son importantes: la válvula pasa menos caudal "
   "que en flujo turbulento. El programa aplica el factor FR de la norma. Verifique la "
   "viscosidad a la temperatura mínima de operación, que suele ser el caso más exigente.</p>",
   relacionadas=["Rev", "FR"], categoria="Fenómenos")

_e("subdimensionada", "Válvula subdimensionada",
   "<p>La válvula no alcanza el caudal requerido ni totalmente abierta. Elija un diámetro mayor o "
   "un estilo de mayor capacidad.</p>", relacionadas=["apertura"], categoria="Fenómenos")

_e("apertura_alta", "Apertura muy alta",
   "<p>Con aperturas sobre 90 % queda poco margen para perturbaciones y la ganancia de la válvula "
   "es baja.</p>", relacionadas=["apertura"], categoria="Fenómenos")

_e("apertura_baja", "Válvula sobredimensionada",
   "<p>Con aperturas por debajo de 10 % el obturador trabaja cerca del asiento: el control es "
   "inestable, el desgaste por alta velocidad es mayor y la fricción de la empaquetadura "
   "domina el movimiento.</p>", relacionadas=["apertura"], categoria="Fenómenos")

_e("bajo_cv_minimo", "Caudal por debajo del Cv mínimo controlable",
   "<p>Toda válvula tiene un Cv mínimo por debajo del cual no puede regular: Cv mínimo = Cv nominal / R, "
   "donde R es la rangeabilidad inherente del trim (≈ 50 en globo estándar, ≈ 15 en jaulas de orificios, "
   "≈ 33 en multietapa). Si el caso pide un Cv menor, la curva característica no tiene una carrera que "
   "lo dé: el obturador quedaría apoyado en el asiento, abriendo y cerrando (control de dos posiciones), "
   "con erosión del asiento por la velocidad en la ranura mínima.</p>"
   "<p>En ese caso N25 muestra «&lt; Cv mín.» en la apertura y la carrera, en lugar de 0 %, que se "
   "podría leer como un resultado válido.</p>",
   formula="Cv mínimo = Cv nominal / R",
   tipicos="Jaula de 3\" lineal, Cv 142, R 50: Cv mínimo ≈ 2,8",
   relacionadas=["apertura", "apertura_baja", "Kv_nominal", "caracteristica"], categoria="Fenómenos")

_e("kv_tipico", "Capacidad nominal típica",
   "<p>La capacidad nominal usada para la apertura es un valor típico del estilo genérico, no de "
   "un producto. Cargue el Kv o Cv certificado y fije el diámetro para verificar una válvula "
   "concreta.</p>", relacionadas=["Kv_nominal"], categoria="Fenómenos")


_e("ruido", "Ruido de la válvula",
   "<p><b>Qué es.</b> Parte de la energía que la válvula disipa al reducir la presión se convierte en "
   "sonido. En gases y vapor el ruido es <b>aerodinámico</b> (turbulencia y ondas de choque del chorro "
   "a alta velocidad); en líquidos es <b>hidrodinámico</b> y crece mucho cuando hay cavitación.</p>"
   "<p><b>Cómo se calcula.</b> El programa aplica IEC 60534-8-3 (gases) o IEC 60534-8-4 (líquidos): "
   "potencia del chorro en la vena contracta, fracción que se convierte en sonido (eficiencia acústica, "
   "según el régimen), nivel dentro de la tubería, pérdida de transmisión a través de la pared por "
   "bandas de frecuencia y nivel ponderado A a 1 m aguas abajo y a 1 m de la pared: LpAe,1m.</p>"
   "<p><b>Regímenes de ruido en gases.</b> I subsónico; II sónico con recompresión; III sin "
   "recompresión; IV celdas de choque; V eficiencia constante. A mayor régimen, mayor eficiencia "
   "acústica.</p><p><b>Límites usuales.</b> 85 dB(A) es el límite habitual de exposición laboral en "
   "especificaciones de proyecto. Por encima de unos 110 dB(A) la vibración puede dañar la tubería, "
   "instrumentos y soportes.</p><p><b>Soluciones.</b> Tratamiento de la fuente (internos de bajo ruido, "
   "multietapa, difusores) o del camino (silenciador, mayor espesor de pared, aislamiento acústico). "
   "En líquidos, eliminar la cavitación.</p><p>Exactitud típica de la norma: ±5 dB.</p>",
   formula="Lpi = 10·lg(3,2·10⁹·Wa·ρ2·c2/Di²) + Lg;   LpAe,1m = Σ(Lpi,f + TLf − distancia + Af)",
   referencia="IEC 60534-8-3:2010; IEC 60534-8-4:2015",
   relacionadas=["espesor_pared", "limite_ruido", "cavitacion", "gas_bloqueado"], categoria="Fenómenos")

_e("ruido_no_calculado", "Ruido no calculado",
   "<p>El ruido no se estimó porque las condiciones están fuera del alcance de las normas (por "
   "ejemplo flashing en líquidos) o faltan datos.</p>", relacionadas=["ruido"], categoria="Fenómenos")

_e("espesor_pared", "Espesor de pared de la tubería de salida",
   "<p>Se usa para la pérdida de transmisión del ruido a través de la pared. Una pared más gruesa "
   "atenúa más. Si se deja en blanco se toma el espesor cédula 40 (ASME B36.10M) correspondiente "
   "al diámetro interior.</p>", tipicos="Cédula 40: 4\" 6,02 mm; 6\" 7,11 mm; 8\" 8,18 mm",
   relacionadas=["ruido", "D1"])

_e("limite_ruido", "Límite de ruido",
   "<p>Nivel máximo admisible en dB(A) a 1 m, según la especificación del proyecto o la "
   "legislación laboral. Por defecto 85 dB(A). El programa avisa desde 5 dB por debajo del límite.</p>",
   relacionadas=["ruido"])


_e("bifasico", "Flujo bifásico",
   "<p>Servicio en el que a la entrada de la válvula ya circulan juntas una fase líquida y una gaseosa: "
   "líquido con gas no condensable (por ejemplo crudo con gas) o líquido con su propio vapor (por "
   "ejemplo agua saturada con vapor).</p><p><b>Cómo se calcula.</b> IEC 60534-2-1 no cubre este caso. "
   "El programa usa el método de suma de fases separadas: cada fase se trata con su propia caída de "
   "presión límite (la del líquido por vaporización y la del gas por flujo sónico) y se suman sus "
   "demandas de capacidad. Es un método conservador y de uso extendido, pero menos exacto que las "
   "ecuaciones de la norma para una sola fase.</p><p><b>Erosión.</b> La mezcla sale a alta velocidad: el "
   "programa verifica la velocidad erosional de API RP 14E con la densidad homogénea de la mezcla a la "
   "salida.</p><p>Con un fluido de la lista el programa toma la mezcla saturada a P1 (T1 = temperatura de "
   "saturación) y calcula las densidades de cada fase.</p>",
   formula="C = W/(N6·FP)·√( ff/(ΔPf·ρl) + fg/(ΔPg·ρg·Y²) )",
   relacionadas=["xg", "erosional_api14e", "flashing"], categoria="Conceptos")

_e("bifasico_metodo", "Flujo bifásico: método fuera de la norma IEC",
   "<p>El cálculo bifásico no está normalizado por IEC. Use un margen de capacidad adicional y "
   "verifique la erosión.</p>", relacionadas=["bifasico"], categoria="Fenómenos")

_e("xg", "Fracción másica de gas o vapor",
   "<p>Parte del caudal másico total que es gas o vapor a la entrada (también llamada calidad o "
   "título). 0 % es líquido puro y 100 % gas puro.</p><p>Si conoce la relación gas-líquido en "
   "volumen, conviértala a masa con las densidades de cada fase: xg = Qg·ρg/(Qg·ρg + Ql·ρl).</p>",
   relacionadas=["bifasico"])

_e("rho_l", "Densidad de cada fase",
   "<p>Densidad del líquido (ρl) y del gas o vapor (ρg) a las condiciones de entrada, cada una "
   "por separado.</p>", relacionadas=["bifasico", "rho"])
_e("rho_g", "Densidad del gas o vapor ρg",
   "<p>Densidad de la fase gaseosa a P1 y T1. Para gas ideal: ρg = P1·M/(Z·R·T1).</p>",
   relacionadas=["bifasico", "rho"])


_e("material", "Material del cuerpo",
   "<p>Material del cuerpo y bonete según especificación ASTM. Define el grupo de materiales de "
   "ASME B16.34 y, con él, la presión admisible a cada temperatura.</p><ul>"
   "<li><b>ASTM A216 WCB / A105</b> (grupo 1.1): acero al carbono, de −29 °C a 425 °C en servicio "
   "continuo. Es la opción económica habitual.</li>"
   "<li><b>ASTM A351 CF8M / A182 F316</b> (grupo 2.2): inoxidable 316, para corrosión y "
   "temperaturas criogénicas.</li></ul><p>Para baja temperatura en acero al carbono se usan "
   "A352 LCC/LCB o A350 LF2 (con ensayo de impacto); para alta temperatura A217 WC6 o WC9 "
   "(cromo-molibdeno).</p>",
   referencia="ASME B16.34 Tabla 1; especificaciones ASTM A216, A105, A351, A182",
   relacionadas=["clase_presion", "P_diseno"])

_e("clase_presion", "Clase de presión ASME B16.34",
   "<p>Designación (150, 300, 600, 900, 1500, 2500) que fija la presión máxima de trabajo de la "
   "válvula en función del material y la temperatura. La presión admisible <b>disminuye</b> al subir "
   "la temperatura. Con «Automática» el programa propone la menor clase que soporta la presión y "
   "temperatura de diseño.</p><p>La clase de la válvula debe coincidir con la clase de las bridas de "
   "la línea (ASME B16.5) salvo justificación.</p>",
   referencia="ASME B16.34 sección 2 y Tablas 2", relacionadas=["material", "P_diseno"])

_e("P_diseno", "Presión y temperatura de diseño",
   "<p>Condiciones de diseño de la línea donde se instala la válvula (de la lista de líneas o del "
   "P&amp;ID), normalmente mayores que las de operación. Se usan para verificar la clase de presión. "
   "Si se dejan en blanco se usan la máxima P1 y la máxima T1 de los casos, con un aviso.</p>",
   relacionadas=["clase_presion"])

_e("clase_insuficiente", "Clase de presión insuficiente",
   "<p>La presión de diseño supera la admisible para la clase y el material a esa temperatura. "
   "Elija una clase mayor o un material de mayor resistencia.</p>",
   relacionadas=["clase_presion"], categoria="Fenómenos")
_e("material_baja_temperatura", "Material no apto para baja temperatura",
   "<p>Los aceros al carbono comunes se vuelven frágiles a baja temperatura. Por debajo de −29 °C se "
   "requieren materiales con ensayo de impacto o inoxidables.</p>",
   relacionadas=["material"], categoria="Fenómenos")
_e("material_alta_temperatura", "Temperatura fuera del rango del material",
   "<p>La temperatura supera el rango de la tabla incluida para el material elegido.</p>",
   relacionadas=["material"], categoria="Fenómenos")
_e("grafitizacion", "Grafitización del acero al carbono",
   "<p>En servicio prolongado por encima de 425 °C los carburos del acero al carbono se descomponen "
   "en grafito, que debilita el material. ASME B16.34 advierte sobre este uso.</p>",
   relacionadas=["material"], categoria="Fenómenos")
_e("diseno_por_operacion", "Condiciones de diseño supuestas",
   "<p>No se ingresaron presión y temperatura de diseño; la clase se verificó con las máximas de "
   "operación.</p>", relacionadas=["P_diseno"], categoria="Fenómenos")


# ---------------------------------------------------------------------------
# Versión 2: datos de instalación, coeficientes de cavitación y entregables
# ---------------------------------------------------------------------------
_e("identificacion", "Identificación del proyecto",
   "<p>Proyecto, cliente, tag, servicio, número de documento, revisión, autor y fecha. Aparecen en "
   "el encabezado de la memoria de cálculo, la hoja de datos y el informe técnico.</p>",
   relacionadas=["entregables"], categoria="Conceptos")
_e("flujo_trabajo", "Flujo de trabajo",
   "<p>1. En <b>1-Sistema</b> cargue los datos de instalación: estilo, rating, tuberías, "
   "conexión, condiciones de diseño, clase de cierre y ruido permitido.</p>"
   "<p>2. En <b>2-Cálculos Válvula</b> cargue las condiciones de operación del líquido (mínimo, normal "
   "y máximo) y revise los factores típicos del trim. Los diámetros y cédulas de tubería se copian "
   "solos desde los datos de instalación.</p><p>3. Presione <b>Calcular</b>. Los resultados aparecen "
   "debajo de las entradas, en celdas verdes, y se actualizan la memoria de cálculo, la hoja de "
   "datos y el informe técnico.</p><p>4. Desde <b>Inicio → Entregables</b> exporte a Word o imprima "
   "cada documento o todos juntos.</p>",
   relacionadas=["identificacion", "entregables"], categoria="Conceptos")
_e("estilo_cuerpo", "Estilo de válvula",
   "<p>Tipo de cuerpo. Define los internos (trims) disponibles, los diámetros habituales, el tipo "
   "de guía y el coeficiente acústico del ruido.</p><ul>"
   "<li><b>Globo</b>: el más versátil; alto FL, admite internos anticavitación y multietapa.</li>"
   "<li><b>Globo con liner</b>: cuerpo revestido (PFA/PTFE) para fluidos corrosivos; limitado en "
   "temperatura.</li><li><b>Ángulo</b>: descarga a 90°; preferido para flashing y fluidos "
   "erosivos.</li>"
   "<li><b>Bola de paso completo (flotante)</b>: el orificio de la bola igual a la conexión; máxima "
   "capacidad y mínima pérdida. La bola flota entre los asientos y la presión la empuja contra el de "
   "aguas abajo: habitual hasta 8\" y CL600.</li>"
   "<li><b>Bola de paso reducido (flotante)</b>: orificio una o dos medidas menor; menos capacidad pero algo "
   "más de FL y xT (cavita y se ahoga un poco más tarde) y menor par.</li>"
   "<li><b>Bola trunnion (montada en muñón)</b>: la bola gira sobre muñones con cojinetes y son los asientos "
   "los que se apoyan con resortes; par bajo y estable aun a alta presión. Para 2\" a 48\" y CL150 a "
   "CL2500. Admite bola de paso completo, reducido o segmentada.</li>"
   "<li><b>Bola segmentada (corte en V)</b>: un segmento de bola con borde en V de 90°, 60° o 30°; "
   "característica isoporcentual, rangeabilidad alta (100 a 200:1) y efecto de corte para pulpas, fibras "
   "y sólidos. Cierre clase IV metálico o VI blando.</li>"
   "<li><b>Tapón excéntrico rotativo</b>: tapón esférico montado en un brazo excéntrico que se separa del "
   "asiento al abrir (menos roce y desgaste); FL mayor que la bola (0,85 con flujo que tiende a abrir), "
   "rangeabilidad 100:1, bueno con fluidos sucios, viscosos o erosivos y para ΔP medias.</li>"
   "<li><b>Mariposa</b> concéntrica, de <b>doble</b> y de <b>triple "
   "excentricidad</b>: gran capacidad y bajo costo en diámetros grandes; FL bajo, cavitan antes.</li></ul>",
   relacionadas=["trim", "FL", "clase_cierre"])
_e("rating", "Rating (clase de presión)",
   "<p>Clase de presión-temperatura del cuerpo según ASME B16.34: CL150, 300, 600, 900, 1500 o "
   "2500. La presión admisible baja al subir la temperatura y depende del material.</p>"
   "<p>El programa verifica el rating con el grupo de ASME B16.34 del material del cuerpo elegido en "
   "3-Materiales; si no hay material definido usa como referencia acero al carbono (grupo 1.1, WCB). Una "
   "bola flotante en CL900 o superior genera un aviso: a esas presiones corresponde bola trunnion.</p>",
   referencia="ASME B16.34, Tabla 2-1.1", relacionadas=["P_diseno"])
_e("nps", "Diámetro nominal de tubería (NPS)",
   "<p>Tamaño nominal de la tubería de entrada o de salida en pulgadas (NPS). Junto con la cédula "
   "define el diámetro interior según ASME B36.10M / B36.19M, que el programa usa para los "
   "factores de reductores (Fp, FLp), las velocidades y el ruido.</p><p>Si la válvula es menor que "
   "la tubería se consideran reductores concéntricos.</p>",
   referencia="ASME B36.10M / ASME B36.19M", relacionadas=["cedula", "FP"])
_e("cedula", "Schedule (cédula) de tubería",
   "<p>Designa el espesor de pared. Las cédulas numéricas (10 a 160), STD, XS y XXS son de "
   "ASME B36.10M (acero al carbono y aleado); las terminadas en «S» (5S, 10S, 40S, 80S) son de "
   "ASME B36.19M (inoxidable). Solo se ofrecen las combinaciones que la norma define para el "
   "diámetro elegido.</p><p>Diámetro interior: DI = OD − 2·espesor. El espesor de la tubería de "
   "salida interviene en la atenuación del ruido.</p>",
   formula="DI = OD − 2·t", referencia="ASME B36.10M / ASME B36.19M", relacionadas=["nps", "ruido"])
_e("conexion", "Tipo de conexión a proceso",
   "<p>Extremos de la válvula: soldados a tope (BWE), soldados de enchufe (SWE), bridados de cara "
   "con resalte (RF), cara plana (FF) o junta de anillo (RTJ), sin bridas (flangeless), wafer, "
   "roscados hembra (FNPT) o macho (MNPT).</p><p>El programa avisa combinaciones poco habituales: "
   "wafer fuera de mariposas, roscas o SWE por encima de 2\", FF con rating mayor que CL150, "
   "rosca NPT por encima de CL600.</p>",
   referencia="ASME B16.5 / B16.25 / B16.11", relacionadas=["rating"])
_e("T_diseno", "Temperatura de diseño",
   "<p>Temperatura de diseño de la línea. Se usa para la verificación del rating y para comprobar "
   "que el asiento blando o el revestimiento admiten la temperatura. Si se deja en blanco se usa "
   "la máxima T1 de operación.</p>", relacionadas=["P_diseno", "rating"])
_e("clase_cierre", "Clase de cierre (shutoff)",
   "<p>Fuga admisible con la válvula cerrada, según ANSI/FCI 70-2 (IEC 60534-4):</p><ul>"
   "<li>Clase I: por acuerdo, sin ensayo.</li><li>Clase II: 0,5 % de la capacidad nominal.</li>"
   "<li>Clase III: 0,1 %.</li><li>Clase IV: 0,01 % (asiento metálico estándar).</li>"
   "<li>Clase V: 5·10⁻⁴ ml/min de agua por pulgada de puerto y por psi de ΔP (asiento metálico "
   "lapeado, alta carga de asiento).</li><li>Clase VI: burbujas por minuto según el diámetro "
   "(asiento blando).</li><li>Tight shutoff: sin fuga visible, requisito habitual de válvulas de "
   "bloqueo (API 598, ISO 5208).</li></ul><p>La clase condiciona el asiento, el obturador y la "
   "fuerza del actuador. El programa avisa si la clase pide un asiento blando y la temperatura "
   "de diseño lo excede.</p>",
   referencia="ANSI/FCI 70-2; IEC 60534-4", relacionadas=["estilo_cuerpo"])
_e("tipo_caudal", "Tipo de caudal",
   "<p>Volumétrico (m³/h, gpm, L/min) a condiciones de entrada, o másico (kg/h, lb/h, t/h). El "
   "programa calcula el otro con la densidad de entrada.</p>", relacionadas=["caudal", "SG"])
_e("SG", "Gravedad específica",
   "<p>Densidad del líquido a las condiciones de entrada dividida por la del agua a 15 °C "
   "(999,1 kg/m³). Es el término ρ1/ρ0 de las ecuaciones de IEC 60534-2-1.</p><p>Con un fluido de "
   "la lista se calcula sola a P1 y T1.</p>",
   formula="SG = ρ1 / ρ0, ρ0 = 999,1 kg/m³", tipicos="Agua 15 °C: 1,000. Agua 90 °C: 0,967. "
   "Gasolina: 0,72–0,76. Crudo: 0,80–0,95.", relacionadas=["rho"])
_e("trim", "Tipo de obturador (estilo de trim)",
   "<p>Pieza de los internos que define los factores del trim. Desde v0.13.1 depende del <b>tipo de trim</b> "
   "elegido arriba:</p><ul>"
   "<li><b>Sin jaula</b>: <b>contorneado</b> (perfilado, estándar), <b>en V</b> (V-port, guiado por el "
   "puerto; factores de IEC 60534-2-1 para 3 ranuras), <b>microcaudal</b> (aguja o ranurado, Cv de 0,001 a "
   "1, hasta 2\") y, en ángulo, <b>salida Venturi</b>. La lista depende de la guía elegida.</li>"
   "<li><b>Con jaula</b>: <b>cilíndrico</b>, un cilindro hueco sin perfil que abre las ventanas u orificios "
   "de la jaula; la característica la da la jaula. La fila queda fija.</li>"
   "<li><b>Rotativas</b>: el elemento de cierre (bola, mariposa, segmento o tapón excéntrico) con su "
   "característica propia.</li></ul>"
   "<p>Cada combinación trae sus factores típicos (FL, xT, Fd), su Kc y su capacidad típica (tabla de "
   "capacidad), que se cargan en las entradas y se pueden reemplazar por los certificados del fabricante. Los "
   "trims que IEC 60534-2-1 no publica llevan valores estimados, indicados en la descripción de cada opción.</p>"
   "<p>Proyectos de versiones anteriores: la doble guía superior pasa a ser una guía del obturador "
   "contorneado; el disco plano y la jaula de retención de asiento pasan a obturador contorneado; las jaulas "
   "de 60 y 120 orificios pasan a la jaula anticavitación de 1 etapa (líquidos) o a la multiorificio nivel 1 "
   "(gases), y los multietapa a 3 etapas.</p>",
   referencia="IEC 60534-2-1, Anexo A (tabla de factores típicos)",
   relacionadas=["tipo_trim", "guia_obturador", "clase_jaula", "nivel_etapas", "sentido_flujo", "Kc", "FL",
                 "Fd", "balance"])
_e("tipo_trim", "Tipo de trim",
   "<p>Primera elección de los internos de globo y ángulo; las filas siguientes muestran solo las opciones "
   "que corresponden.</p><ul><li><b>Sin jaula</b>: el obturador contorneado, en V o de microcaudal da la "
   "característica; el asiento va roscado o sujeto por el bonete o la brida, y la guía es un dato aparte "
   "(fila «Guía del obturador»). Suelen ser desbalanceados.</li><li><b>Con jaula</b>: la jaula guía al "
   "obturador cilíndrico, sujeta el asiento y da la característica con la forma de sus pasajes. Puede ser "
   "balanceado o desbalanceado. Se elige la jaula (estándar, anticavitación o antiruido) y, en las dos "
   "últimas, su config dinámica.</li></ul><p>En válvulas rotativas la fila no se muestra.</p>",
   relacionadas=["guia_obturador", "trim", "clase_jaula", "nivel_etapas"])
_e("clase_jaula", "Jaula",
   "<p>Solo con tipo de trim «Con jaula».</p><ul><li><b>Jaula estándar (caracterizada)</b>: ventanas "
   "perfiladas que dan la característica lineal, isoporcentual o de apertura rápida. Una sola etapa; la config "
   "dinámica queda bloqueada.</li><li><b>Jaula anticavitación</b>: solo con líquidos. Reparte la caída de "
   "presión en etapas para que la presión no baje de la de vapor.</li><li><b>Jaula antiruido</b>: solo con "
   "gas, vapor y steam. Divide el chorro en muchos chorros pequeños y, en las multietapa, reparte la caída "
   "en etapas para bajar el ruido aerodinámico.</li></ul>",
   relacionadas=["tipo_trim", "nivel_etapas", "anticav", "trim_ruido"])
_e("guia_obturador", "Guía del obturador",
   "<p>Cómo se guía el obturador en un trim sin jaula. No cambia los factores de IEC 60534-2-1; "
   "cambia la estabilidad del obturador frente a la ΔP y las vibraciones, y los obturadores que se ofrecen:</p>"
   "<ul><li><b>Superior reforzada</b> (heavy top guided): un buje largo por encima del obturador. Servicio "
   "general, fluidos sucios o viscosos. Obturador contorneado o microcaudal.</li>"
   "<li><b>Doble guía de vástago superior</b> (double top stem guided): dos puntos de guiado separados, ambos "
   "por encima de la corriente del fluido. Obturador contorneado.</li>"
   "<li><b>Superior e inferior</b> (top and bottom guided): bujes por encima y por debajo del obturador. "
   "Tamaños grandes, ΔP altas y doble asiento.</li>"
   "<li><b>Por el puerto</b> (port guided): faldas o aletas del obturador dentro del asiento. ΔP bajas y bajo "
   "costo; obturador en V. Con ΔP mayor de 1 000 kPa o 6\" y más el programa avisa.</li>"
   "<li><b>Por el bonete</b> (bonnet / stem guided): el buje del bonete guía al vástago. Válvulas chicas y de "
   "microcaudal; por encima de 2\" el programa avisa.</li></ul>",
   relacionadas=["tipo_trim", "trim", "balance"])
_e("nivel_etapas", "Config dinámica de la jaula",
   "<p>Con jaula anticavitación o antiruido, cada construcción y nivel se elige por separado, porque cada uno "
   "tiene su propia capacidad de mitigar el fenómeno para el que está diseñado. La lista va de la etapa más "
   "baja y la construcción más simple a la etapa más alta y la construcción más compleja, y junto al nombre se "
   "muestra lo que mitiga. Con jaula estándar queda bloqueada.</p><ul>"
   "<li><b>Jaula perforada</b> (anticavitación, líquidos): 1 etapa (Kc 0,85, FL 0,93) o 2, 3, 4 y 6 etapas, con el Kapp "
   "máximo sin cavitación de cada una.</li><li><b>Pasajes grandes</b> (líquidos con sólidos): 2, 3 o 4 "
   "etapas con pasajes del orden de 12 mm (Fd 0,25).</li><li><b>Discos apilados</b>: 4, 6, 8 o 10 etapas "
   "(giros del laberinto).</li><li><b>Multiorificio</b> (antiruido, gases): nivel 1 (≈ 50 "
   "orificios), 2 (≈ 200) o 3 (≈ 800), con la atenuación típica.</li><li><b>Multietapa multiorificio</b> "
   "(gases): 2, 3 o 4 etapas, con la atenuación típica.</li></ul>"
   "<p>Al elegir el nivel, FL, xT, Fd y Kc de las condiciones de operación toman sus valores (se pueden "
   "reemplazar por los certificados) y el Cv típico pasa a ser el de esa jaula: más etapas dan menos "
   "capacidad por pulgada y el diámetro automático puede subir.</p>"
   "<p><b>Multietapa en gases</b>: N etapas iguales con igual relación de presión, P_salida/P_entrada = "
   "(P2/P1)^(1/N). El ruido IEC 60534-8-3 se calcula con la última etapa, que descarga a la tubería, con su caída "
   "de presión y el Fd de sus orificios; el flujo se estrangula cuando se estrangula la última etapa, "
   "xT = [1 − (1 − Fγ·0,68)^N]/Fγ.</p><p>Las atenuaciones son rangos típicos de la literatura de válvulas; el "
   "programa calcula el ruido de cada caso. Ese cálculo no acredita la expansión de área entre etapas que "
   "agregan muchos diseños, por eso suele dar menos atenuación que el rango típico (lado seguro). Son "
   "valores genéricos, no de un fabricante.</p>",
   formula="Líquido: Kc = 1 − (1 − 0,70)^N;  Gas: P1,última = P2·(P1/P2)^(1/N)",
   referencia="IEC 60534-8-3:2010; IEC 60534-8-4:2015; ISA-RP75.23",
   relacionadas=["anticav", "trim_ruido", "nivel_trim", "trim"])
_e("sentido_flujo", "Sentido de flujo",
   "<p>Dice hacia dónde empuja el fluido al obturador. Es un dato propio, independiente del estilo de trim y de "
   "la característica, y es el único lugar donde se elige: la fila «Flow» de la solapa 4 (actuador) lo toma de "
   "aquí.</p><ul><li><b>Flujo tiende a abrir (Up)</b>: el fluido entra por debajo del asiento y empuja el "
   "obturador hacia arriba. En una jaula, de adentro hacia afuera. Es la dirección habitual; FL ≈ 0,90.</li>"
   "<li><b>Flujo tiende a cerrar (Down)</b>: el fluido entra por arriba y empuja el obturador contra el asiento. "
   "En una jaula, de afuera hacia adentro. Se usa con flashing y en trims anticavitación para que las burbujas "
   "colapsen lejos del asiento y de las paredes; FL menor (≈ 0,80–0,85) y puede dar golpe al cerrar.</li></ul>"
   "<p>Cambia FL, xT y Fd (IEC 60534-2-1, Tabla 2) y el sentido de la fuerza del fluido sobre el obturador en "
   "el cálculo del actuador. En los datos de los fabricantes el Cv nominal es el mismo en los dos sentidos. "
   "En válvulas rotativas que no tienen sentido preferente la fila muestra «No aplica».</p>",
   referencia="IEC 60534-2-1, Anexo A, Tabla 2",
   relacionadas=["trim", "FL", "balance", "caracteristica"])

_e("capacidad_trim", "Tabla de capacidad: Cv, puerto y carrera",
   "<p>Desde v0.12.0 el Cv típico de las válvulas de globo y ángulo no sale de una constante por d², sino de una "
   "tabla por familia de trim y tamaño, armada con unas 1 200 filas de tablas de «Cv y FL según la carrera» "
   "publicadas por tres fabricantes. El programa no guarda las tablas de ningún fabricante: guarda la "
   "<b>mediana</b> por tamaño y la <b>dispersión</b> entre ellos.</p><ul>"
   "<li><b>Trim pleno</b>: puerto, carrera y Cv lineal por diámetro nominal; entre tamaños se interpola en "
   "escala logarítmica.</li>"
   "<li><b>Característica</b>: factor sobre el Cv lineal medido en el mismo puerto (contorneado: iso 1,00; "
   "jaula: iso 0,89, apertura rápida 1,09; orificios: iso 0,75).</li>"
   "<li><b>Puerto o carrera distintos</b> (trim reducido o datos certificados): el asiento y el paso lateral "
   "del obturador se tratan como dos restricciones en serie, con coeficientes ajustados por familia; el "
   "resultado no supera el Cv del pleno del cuerpo.</li>"
   "<li><b>Jaulas de capacidad reducida</b>: los fabricantes ofrecen también jaulas de menor Cv con el mismo "
   "puerto y la misma carrera (por ejemplo, Cv 30, 40 y 55 en un puerto de 2 1/2\"). La geometría no las distingue: "
   "el modelo da la de mayor capacidad y el Cv de las otras se carga como certificado.</li>"
   "<li><b>Trims especiales</b>: el multietapa se corrige por el número de etapas; la rangeabilidad de los trims "
   "de orificios (≈ 15) y multietapa (≈ 33) sale del Cv mínimo controlable publicado.</li></ul>"
   "<p><b>Coherencia</b>: si el puerto, la carrera o el Cv cargados se apartan más de ±10 % del típico, el "
   "programa lo informa; si además el Cv cae fuera de la dispersión entre fabricantes, la alerta es una "
   "advertencia: puerto, carrera y Cv deben ser del mismo juego de trim.</p>"
   "<p>Cv lineal del trim pleno (mediana):</p><ul>"
   "<li>Contorneado: 1\" 12; 2\" 46; 3\" 110; 4\" 195; 6\" 400; 8\" 640.</li>"
   "<li>Jaula: 3\" 142; 4\" 218; 6\" 394; 8\" 585; 10\" 860.</li>"
   "<li>Jaula de orificios: 3\" 95; 4\" 168; 6\" 230; 8\" 410; 12\" 915.</li>"
   "<li>Multietapa (≈ 3 etapas): 3\" 70; 4\" 105; 6\" 150; 8\" 250; 12\" 620.</li></ul>"
   "<p>Comparado con la versión anterior (Cv ≈ Cd·d²), la jaula de 6\" y 8\" bajó de 504 y 896 a 394 y 585, y "
   "el multietapa de 3\" subió de 31 a 70.</p>",
   formula="1/Cv² = 1/(Kp·d²)² + 1/(Kh·π·d·h)²",
   referencia="Mediana de datos publicados de fabricantes (v0.12.0); IEC 60534-2-3 para el ensayo de Cv",
   relacionadas=["Kv_nominal", "trim_size", "carrera_nominal", "Cv_reducido", "caracteristica"])

from .estilos import ESTILOS as _ESTILOS, NOMBRE_CORTO as _NOMBRE_CORTO, CUERPOS as _CUERPOS  # noqa: E402

from .trims import claves_en_uso as _claves_en_uso  # noqa: E402

_EN_USO = _claves_en_uso()

A["trim"].texto += ("<p><b>Combinaciones que calcula el programa</b> (con su sentido de flujo):</p><ul>"
                    + "".join(f"<li>{e.nombre}.</li>" for k, e in _ESTILOS.items() if k in _EN_USO) + "</ul>")
_e("balance", "Obturador balanceado o desbalanceado",
   "<p><b>Desbalanceado</b>: la ΔP actúa sobre toda el área del puerto; el actuador debe vencer una "
   "fuerza F ≈ ΔP·π·d²/4. Es simple y cierra mejor (clase V o VI con asiento adecuado).</p>"
   "<p><b>Balanceado</b>: unos orificios en el obturador igualan la presión arriba y abajo, y un anillo "
   "de sello contra la jaula separa ambas zonas. La fuerza baja a una fracción y basta un actuador "
   "chico, pero el sello agrega una vía de fuga (clase IV habitual) y limita la temperatura (PTFE unos "
   "232 °C).</p><p>Orientativo: conviene balanceado con ΔP de cierre mayor que unos 10 bar en válvulas "
   "de 3\" o más. Requiere obturador guiado por jaula. No aplica a válvulas rotativas. No cambia el Cv: "
   "se informa en la hoja de datos y se verifica en las alertas.</p>",
   formula="F ≈ ΔP·π·d²/4 (obturador desbalanceado, d = diámetro del puerto)",
   referencia="Práctica de la industria (manuales de fabricantes)",
   relacionadas=["trim", "desbalance_fuerza", "balance_cierre", "clase_cierre"])
_e("Kc", "Coeficiente de cavitación de la construcción Kc",
   "<p>Valor de ΔP/(P1 − Pv) a partir del cual el trim cavita en forma sostenida y puede dañarse "
   "(régimen de cavitación constante de ISA-RP75.23, o límite del fabricante). Es el mismo criterio "
   "que usan los programas de los fabricantes para la ΔP de cavitación. Al elegir el trim se carga "
   "su valor típico; reemplácelo por el certificado.</p><p>Si se deja en blanco se usa la cavitación "
   "incipiente xFzp1 (conservador). La cavitación incipiente, que solo aumenta el ruido, se evalúa "
   "aparte con xFz. El ruido de IEC 60534-8-4 usa este Kc como inicio de cavitación.</p><ul><li>Kapp &lt; xFzp1: sin cavitación.</li><li>xFzp1 ≤ Kapp &lt; Kc: "
   "cavitación incipiente (ruido, sin daño esperado).</li><li>Kc ≤ Kapp &lt; FLp²: cavitación.</li>"
   "<li>Kapp ≥ FLp²: flujo estrangulado.</li></ul>",
   formula="ΔPcav = Kc·(P1 − Pv)", tipicos="Contorneado 0,55–0,65. Jaula 4 ventanas 0,65–0,70. Jaula de "
   "orificios 0,80–0,85. Multietapa 0,95. Rotativas 0,25–0,50.",
   referencia="ISA-RP75.23 (σc); práctica de fabricantes",
   relacionadas=["Kapp", "dPcav", "xFz", "cavitacion"], categoria="Coeficientes")
_e("Kapp", "Coeficiente de cavitación de la aplicación Kapp",
   "<p>Relación entre la caída de presión del servicio y la presión disponible sobre la de vapor. "
   "Describe cuán exigente es la aplicación, sin importar la válvula.</p><ul><li>Kapp &lt; xFzp1: sin "
   "cavitación.</li><li>xFzp1 ≤ Kapp &lt; Kc: cavitación incipiente (más ruido, sin daño esperado).</li>"
   "<li>Kc ≤ Kapp &lt; FLp²: cavitación (leve a severa).</li><li>Kapp ≥ FLp²: flujo estrangulado por "
   "cavitación plena.</li></ul>",
   formula="Kapp = ΔP / (P1 − Pv)", referencia="IEC 60534-8-4 (xF); ISA-RP75.23",
   relacionadas=["Kc", "xFz", "dPcav", "dPchoked"], categoria="Resultados")
_e("dPcav", "ΔP de inicio de cavitación (ΔP cav)",
   "<p>Caída de presión a partir de la cual el trim cavita en forma sostenida. Si la ΔP del servicio es "
   "mayor hay cavitación; compárela también con ΔP choked. La cavitación incipiente empieza antes, en "
   "xFzp1·(P1 − Pv), y solo aumenta el ruido.</p>",
   formula="ΔPcav = Kc·(P1 − Pv)", relacionadas=["Kc", "Kapp", "xFz"], categoria="Resultados")
_e("dP_P1", "Relación de caída de presión ΔP/P1",
   "<p>Fracción de la presión de entrada que se pierde en la válvula. Valores altos indican un "
   "servicio exigente (cavitación, ruido, erosión).</p>", formula="ΔP/P1", categoria="Resultados")
_e("D_interno", "Diámetro interno de tubería",
   "<p>Diámetro interior de la tubería aguas arriba y aguas abajo, obtenido de NPS y cédula según "
   "ASME B36.10M / B36.19M.</p>", formula="DI = OD − 2·t", relacionadas=["nps", "cedula"],
   categoria="Resultados")
_e("flujo_masico", "Flujo másico",
   "<p>Caudal másico del líquido: W = Q·ρ1.</p>", formula="W = Q·ρ1", categoria="Resultados")
_e("velocidad_tuberia", "Velocidad en tubería",
   "<p>Velocidad media del líquido en la tubería de entrada (aguas arriba) y de salida (aguas "
   "abajo): v = Q/A. La práctica habitual limita la velocidad de líquidos a unos 4,5 m/s (3 m/s con "
   "sólidos) para evitar erosión, ruido y golpe de ariete.</p>", formula="v = Q / (π·DI²/4)",
   relacionadas=["velocidad_liquido"], categoria="Resultados")
_e("velocidad_sonido", "Velocidad del sonido",
   "<p><b>Gas, vapor y vapor de agua:</b> c = √(γ·P/ρ) = √(γ·Z·R·T/M), aguas arriba con P1 y ρ1 y aguas "
   "abajo (y en la salida de la válvula) con P2 y ρ2. Se usa para el número de Mach y el ruido.</p>"
   "<p><b>Líquidos:</b> se usa en el ruido hidrodinámico (IEC 60534-8-4); con un fluido de la lista se "
   "calcula sola, si no se toma 1 400 m/s.</p>",
   relacionadas=["ruido"])
_e("Cv_nominal", "Cv nominal de la válvula",
   "<p>Cv de la válvula completamente abierta. En blanco se usa un valor típico del estilo "
   "(Cv ≈ Cd·d²). Para verificar la selección de un proveedor ingrese el Cv certificado y el "
   "diámetro de la válvula ofertada.</p>", relacionadas=["Kv_nominal", "apertura"],
   categoria="Coeficientes")
_e("entregables", "Entregables",
   "<p>El programa genera tres documentos que se ven en sus solapas y se exportan a Word editable "
   "(.docx) o se imprimen desde <b>Inicio → Entregables</b>, por separado o todos juntos:</p><ul>"
   "<li><b>Memoria de cálculo</b>: datos, ecuaciones esenciales con resultados, gráfico de Cv vs "
   "apertura y conclusión.</li><li><b>Hoja de datos</b>: condiciones de servicio, línea, cuerpo, "
   "internos, cierre y notas.</li><li><b>Informe técnico</b>: resultados completos, alertas con su "
   "intensidad, acciones de corrección, características recomendadas y recomendaciones "
   "finales.</li></ul><p>Todos usan las unidades elegidas en las entradas.</p>",
   relacionadas=["identificacion"], categoria="Conceptos")
_e("rating_referencial", "Rating verificado en forma referencial",
   "<p>El rating se comparó con la tabla de acero al carbono (grupo 1.1). Cuando se defina el "
   "material del cuerpo la verificación debe repetirse con su grupo.</p>", relacionadas=["rating"],
   categoria="Fenómenos")
_e("rating_fuera_tabla", "Temperatura fuera de la tabla de clase",
   "<p>La temperatura de diseño supera la tabla de referencia; el rating depende del material.</p>",
   relacionadas=["rating"], categoria="Fenómenos")
_e("conexion_incompatible", "Conexión poco habitual",
   "<p>La combinación de conexión, estilo, diámetro o rating no es la habitual. Revísela con la "
   "especificación de tuberías del proyecto.</p>", relacionadas=["conexion"], categoria="Fenómenos")
_e("conexion_info", "Conexión: observación",
   "<p>Observación sobre la conexión elegida; no impide la selección.</p>", relacionadas=["conexion"],
   categoria="Fenómenos")
_e("valvula_mayor_linea", "Válvula mayor que la tubería",
   "<p>La válvula resultó mayor que la tubería: la línea puede estar subdimensionada o el estilo "
   "tiene poca capacidad para el servicio.</p>", relacionadas=["tamano"], categoria="Fenómenos")
_e("valvula_chica_linea", "Válvula mucho menor que la tubería",
   "<p>Los reductores grandes reducen la capacidad y el FL efectivo; verifique velocidades y "
   "soportes.</p>", relacionadas=["FP", "FLP"], categoria="Fenómenos")
_e("tamano_estilo", "Diámetro poco habitual para el estilo",
   "<p>El diámetro está fuera del rango en que este estilo se fabrica habitualmente.</p>",
   relacionadas=["estilo_cuerpo"], categoria="Fenómenos")
_e("cierre_estilo", "Clase de cierre y estilo", "<p>El estilo elegido no suele alcanzar la clase "
   "pedida.</p>", relacionadas=["clase_cierre"], categoria="Fenómenos")
_e("cierre_info", "Clase de cierre: observación", "<p>Observación sobre la clase de cierre.</p>",
   relacionadas=["clase_cierre"], categoria="Fenómenos")
_e("cierre_temperatura", "Asiento blando fuera de temperatura",
   "<p>La clase de cierre pide un asiento blando o revestimiento cuyo límite de temperatura es "
   "menor que la de diseño. Use asiento metálico o un estilo con cierre metal-metal.</p>",
   relacionadas=["clase_cierre", "T_diseno"], categoria="Fenómenos")
_e("velocidad_tuberia_alta", "Velocidad alta en tubería", "<p>Ver «Velocidad en tubería».</p>",
   relacionadas=["velocidad_tuberia"], categoria="Fenómenos")

# ---------------------------------------------------------------------------
# Gas, vapor y vapor de agua (versión 2)
# ---------------------------------------------------------------------------
_e("T2", "Temperatura de salida T2",
   "<p>Temperatura aguas abajo de la válvula. Se usa para la densidad y la velocidad del sonido a la "
   "salida, que intervienen en el ruido aerodinámico, el número de Mach y la velocidad.</p>"
   "<p>Con un fluido de la lista y en vapor de agua se calcula por expansión isoentálpica (la entalpía "
   "se conserva en el estrangulamiento): así aparece el efecto Joule-Thomson y, en vapor de agua, el "
   "sobrecalentamiento a P2. Con un gas definido por el usuario, en blanco se toma T2 = T1 (gas ideal).</p>",
   formula="h(P2, T2) = h(P1, T1)", referencia="IEC 60534-8-3:2010",
   relacionadas=["rho2", "velocidad_sonido", "sobrecalentamiento"])
_e("rho2", "Densidad de salida ρ2",
   "<p>Densidad del fluido aguas abajo, a P2 y T2. Gas: ρ2 = P2·M/(Z2·R·T2). Vapor: dato del usuario o, en "
   "blanco, ρ1·(P2/P1)·(T1/T2). Vapor de agua: IAPWS-95.</p>",
   referencia="IEC 60534-8-3:2010", relacionadas=["T2", "Z", "velocidad_sonido"])
_e("anticav", "Trim anticavitación (por etapas)",
   "<p>Solo líquidos, cuerpos globo y angular. Desde v0.13.1 se elige en la solapa 2 con «Con jaula», "
   "«Jaula anticavitación» y su «Config dinámica de la jaula». Define con qué "
   "se calcula la cavitación, el ruido y el Cv por tamaño:</p><ul><li><b>Sin jaula especial</b>: el trim "
   "elegido, una etapa, con sus FL, Fd y Kc."
   "</li><li><b>Jaula anticavitación, 1 etapa</b>: FL 0,93, Fd 0,10, Kc 0,85.</li><li><b>Multietapa de "
   "2, 3, 4 o 6 etapas</b>: la caída se reparte en etapas en serie con igual Kapp por etapa, "
   "k = 1 − ((P2 − Pv)/(P1 − Pv))^(1/N): las primeras etapas toman la mayor parte de la caída y la última "
   "la menor. Cada etapa es un elemento de orificios con inicio de cavitación incipiente 0,50, Kc 0,70 y "
   "FL 0,90; los factores de la válvula completa son Kc = 1 − (1 − 0,70)^N, xFz = 1 − (1 − 0,50)^N y "
   "FL² = 1 − (1 − 0,81)^N.</li></ul><p>Al elegirlo, FL, Fd y Kc de las condiciones de operación toman "
   "esos valores (puede reemplazarlos por los certificados). El ruido IEC 60534-8-4 se calcula con la "
   "última etapa, que descarga a la tubería. Más etapas dan menos capacidad por pulgada: el diámetro "
   "automático puede subir.</p><p>Resultados: <b>Kapp por etapa</b> y <b>etapas recomendadas</b>, la "
   "menor cantidad sin cavitación (Kapp por etapa ≤ 0,50) y la mínima aceptando cavitación incipiente "
   "(Kapp por etapa ≤ 0,9·0,70 = 0,63).</p><p>Valores genéricos de referencia, no de un fabricante.</p>",
   formula="k = 1 − ((P2 − Pv)/(P1 − Pv))^(1/N);  Kc = 1 − (1 − Kc_etapa)^N",
   referencia="ISA-RP75.23; IEC 60534-8-4; manual de selección de trim, 5.4",
   relacionadas=["Kc", "Kapp", "cavitacion", "trim", "anticav_insuficiente"], categoria="Datos")
_e("anticav_insuficiente", "Trim anticavitación insuficiente",
   "<p>Con las etapas elegidas, el Kapp de cada etapa supera 0,9·Kc de la etapa (0,63): la válvula puede "
   "cumplir en conjunto pero cada etapa trabaja sin margen y puede cavitar con pequeños cambios de "
   "operación. El mensaje indica cuántas etapas hacen falta.</p>",
   relacionadas=["anticav", "anticav_etapas"], categoria="Fenómenos")
_e("anticav_etapas", "Etapas anticavitación recomendadas",
   "<p>Informa cuántas etapas hacen falta para operar sin cavitación y cuántas como mínimo aceptando "
   "cavitación incipiente, con el reparto de igual Kapp por etapa. Si la cantidad no está en la lista, se "
   "indica la siguiente disponible; si ninguna alcanza, conviene repartir la caída con una placa de "
   "restricción o dos válvulas en serie.</p>",
   relacionadas=["anticav", "anticav_insuficiente"], categoria="Fenómenos")
_e("anticav_rotativa", "Trim anticavitación no aplicable",
   "<p>Los trims anticavitación de la lista son de globo o angular. Con un cuerpo rotativo el cálculo usa "
   "el trim estándar.</p>", relacionadas=["anticav"], categoria="Fenómenos")
_e("trim_ruido", "Trim para ruido aerodinámico",
   "<p>Tipo de internos que se usa para estimar el ruido. Desde v0.13.1 se elige en la solapa 2 con «Con "
   "jaula», «Jaula antiruido» y su «Config dinámica de la jaula». <b>Estándar</b> es un pasaje único (obturador "
   "contorneado, jaula de ventanas, bola o mariposa), con el Fd de cada caso.</p><p>Las <b>jaulas "
   "multiorificio</b> dividen el chorro en muchos chorros pequeños: según IEC 60534-2-1 (Anexo A) su "
   "modificador de estilo es Fd = 1/√No, con No el número de orificios iguales. Con ese Fd la norma "
   "IEC 60534-8-3 da un chorro de menor diámetro y un ruido de mayor frecuencia, que la pared de la "
   "tubería atenúa más.</p><ul><li>Nivel 1: unos 50 orificios (Fd ≈ 0,14).</li>"
   "<li>Nivel 2: unos 200 orificios (Fd ≈ 0,071).</li><li>Nivel 3: unos 800 orificios (Fd ≈ 0,035).</li>"
   "</ul><p><b>Multietapa multiorificio</b> (2, 3 o 4 etapas) y <b>discos apilados</b> (4 a 10 etapas): el "
   "ruido se calcula con la última etapa (ver «Config dinámica de la jaula»).</p>",
   referencia="IEC 60534-8-3:2010; IEC 60534-2-1:2011 Anexo A",
   relacionadas=["nivel_trim", "ruido_componentes", "Fd"], categoria="Datos")
_e("nivel_trim", "Nivel de trim de bajo ruido requerido",
   "<p>El programa repite el cálculo de ruido con el trim estándar y con cada nivel, en orden: jaula "
   "multiorificio niveles 1 a 3, multietapa multiorificio de 2 a 4 etapas y discos apilados de 4 a 10 etapas, "
   "e informa el primero que deja el ruido de la válvula a 1 m por debajo del ruido permitido (1-Sistema). "
   "«No requerido» significa que el trim estándar ya cumple; «Silenciador o difusor», que ninguno alcanza. En "
   "cuerpos rotativos solo se evalúa el estándar.</p>",
   relacionadas=["trim_ruido", "limite_ruido"], categoria="Resultados")
_e("ruido_componentes", "Ruido del trim y de la salida",
   "<p>IEC 60534-8-3 separa dos fuentes:</p><ul><li><b>Trim</b>: el chorro que sale de la vena "
   "contracta, según el régimen de flujo (subsónico, sónico, choques).</li><li><b>Salida de la "
   "válvula</b>: la expansión del flujo en la salida del cuerpo; la norma la considera cuando el Mach en la "
   "tubería de salida supera 0,3. Si no corresponde se muestra «—».</li></ul><p>El ruido de la válvula "
   "es la suma energética de ambas, transmitida a través de la pared de la tubería y medida a 1 m.</p>",
   formula="LpA = 10·lg(10^(Ltrim/10) + 10^(Lsalida/10))", referencia="IEC 60534-8-3:2010",
   relacionadas=["ruido", "Rn", "mach"], categoria="Resultados")
_e("Rn", "Distancia Rn para el ruido",
   "<p>Distancia desde la pared exterior de la tubería a la que se desea conocer el nivel de ruido "
   "(por ejemplo, un puesto de trabajo). La norma da el nivel a 1 m; para otra distancia el programa "
   "aplica la atenuación de una fuente lineal (la tubería):</p>",
   formula="LpA(Rn) = LpA(1 m) − 10·lg((De + 2·Rn)/(De + 2)), De = Di + 2·tp",
   tipicos="1 m (valor de la norma)", referencia="IEC 60534-8-3:2010",
   relacionadas=["ruido_componentes"])
_e("area_salida", "Área de salida de la válvula",
   "<p>Área de paso en la brida de salida del cuerpo. Define la velocidad y el número de Mach en la "
   "salida de la válvula y el diámetro de salida que usa el ruido de salida de IEC 60534-8-3. En blanco "
   "se toma el área del diámetro nominal de la válvula. Las válvulas con salida expandida o reducida "
   "tienen otra área: tómela de los datos del fabricante.</p>",
   relacionadas=["mach", "ruido_componentes"])
_e("mach", "Número de Mach",
   "<p>Relación entre la velocidad del fluido y la velocidad del sonido local, Ma = v/c. Se informa "
   "aguas arriba, en la salida de la válvula y aguas abajo.</p><p>Práctica habitual: en la salida de "
   "la válvula Ma ≤ 0,3 para servicios sensibles al ruido y ≤ 0,5 como máximo; en tuberías Ma ≤ 0,3 "
   "(≤ 0,2 en vapor de agua). Valores mayores aumentan el ruido de salida, la vibración y la "
   "erosión.</p>", formula="Ma = v/c, c = √(γ·P/ρ)", referencia="IEC 60534-8-3:2010",
   relacionadas=["velocidad_sonido", "area_salida"], categoria="Resultados")
_e("sobrecalentamiento", "Sobrecalentamiento a P2",
   "<p>Diferencia entre la temperatura del vapor de agua a la salida (expansión isoentálpica) y la "
   "temperatura de saturación a P2. Un vapor saturado que se estrangula sale sobrecalentado; si el valor "
   "es cero el vapor sale húmedo y puede haber erosión por gotas.</p>",
   formula="ΔTsc = T2 − Tsat(P2)", referencia="IAPWS-95", relacionadas=["T2"], categoria="Resultados")
_e("tipo_calculo", "Tipo de cálculo",
   "<p>Resume las ecuaciones aplicadas en cada caso: tipo de fluido (y si el vapor de agua es saturado o "
   "sobrecalentado), si el flujo es subcrítico o crítico (x ≥ xchoked: el caudal ya no aumenta al bajar "
   "P2 y se dimensiona con x = xchoked e Y = 2/3) y el régimen de Reynolds.</p>",
   referencia="IEC 60534-2-1:2011 cláusulas 6 y 9", relacionadas=["xchoked", "Y", "Rev"],
   categoria="Resultados")


# Solapa 3-Materiales: parámetros, componentes, normas y alertas; agentes químicos.
from . import ayuda_mat_agentes as _AG, ayuda_mat_parametros as _MP  # noqa: E402

for _k, _d in _MP.ENTRADAS.items():
    if _k in A:
        raise KeyError(f"ayuda duplicada: {_k}")
    _e(_k, **_d)
for _k, _d in _AG.ENTRADAS.items():
    _e(_k, categoria="Agentes químicos", **_d)
GUIA.update(_MP.GUIA)
GUIA.update(_AG.GUIA)

# Solapas 4-Actuador, 5-Posicionador y 6-Accesorios
from . import ayuda_actuador as _AC  # noqa: E402

for _k, _d in _AC.ENTRADAS.items():
    if _k in A:
        raise KeyError(f"ayuda duplicada: {_k}")
    _e(_k, **_d)
GUIA.update(_AC.GUIA)


def obtener(clave: str) -> EntradaAyuda | None:
    if clave in A:
        return A[clave]
    if clave.startswith("dato_"):
        return EntradaAyuda("Dato de entrada inválido",
                            "<p>Uno de los datos ingresados está fuera del rango físico o es "
                            "incoherente con los demás. Revise el campo indicado en el mensaje y "
                            "sus unidades.</p>", categoria="Fenómenos")
    return None


# Colores de la guía: azul claro para el bloque didáctico y blanco para umbrales y ejemplo
_C_GUIA, _C_UMBRAL, _C_ACENTO, _C_TEXTO2 = "#eef2f6", "white", "#3d5a80", "#5b6b7d"


def _esc(t: str) -> str:
    """Escapa «<» y «&» del texto, salvo las etiquetas de subíndice y superíndice."""
    t = t.replace("&", "&amp;").replace("<", "&lt;")
    return re.sub(r"&lt;(/?su[bp])>", r"<\1>", t)


def _guia_html(g: dict) -> str:
    g = {k: [_esc(x) for x in v] if isinstance(v, list) else _esc(v) for k, v in g.items()}

    def bloque(titulo, cuerpo):
        return (f"<p style='margin:8px 0 2px 0;color:{_C_ACENTO};font-weight:700'>{titulo}</p>"
                f"<p style='margin:0'>{cuerpo}</p>")

    def caja(color, titulo, cuerpo, borde=_C_ACENTO):
        return (f"<table width='100%' cellspacing='0' cellpadding='7' style='margin-top:8px'><tr>"
                f"<td width='4' bgcolor='{borde}'></td><td bgcolor='{color}'>"
                f"<b style='color:{_C_ACENTO}'>{titulo}</b><br>{cuerpo}</td></tr></table>")

    lista = lambda xs: "".join(f"<li style='margin-bottom:2px'>{x}</li>" for x in xs)
    partes = [bloque("¿Qué es?", g["que_es"]), bloque("¿Para qué sirve en el cálculo?", g["que_hace"]),
              bloque("¿Qué nos dice su valor?", g["que_indica"]),
              caja(_C_UMBRAL, "Valores umbrales", g["umbrales"])]
    lados = [("▼ Por debajo del umbral", g["por_debajo"]), ("▲ Por encima del umbral", g["por_encima"])]
    lados = [(t, x) for t, x in lados if not x.startswith("No aplica")]
    if lados:
        celdas = "".join(f"<td width='{100 // len(lados)}%' valign='top' bgcolor='white'>"
                         f"<b style='color:{_C_ACENTO}'>{t}</b><br>{x}</td>" for t, x in lados)
        partes.append(f"<table width='100%' cellspacing='6' cellpadding='7' style='margin-top:4px'><tr>{celdas}"
                      "</tr></table>")
    partes += [bloque("Cálculos que afecta", " · ".join(g["afecta"])),
              bloque("Recomendaciones", f"<ul style='margin-top:0'>{lista(g['recomendaciones'])}</ul>"),
              caja("white", "Ejemplo", g["ejemplo"], borde="#7fa0c4")]
    return (f"<table width='100%' cellspacing='0' cellpadding='10' bgcolor='{_C_GUIA}' "
            f"style='border:1px solid #d3dce6'><tr><td>"
            f"<p style='margin:0 0 4px 0;color:{_C_TEXTO2};font-size:85%;font-weight:700;letter-spacing:1px'>"
            f"GUÍA PARA APRENDER</p>{''.join(partes)}</td></tr></table>")


def html(clave: str) -> str:
    e = obtener(clave)
    if e is None:
        return f"<h2>{clave}</h2><p>Sin ayuda disponible.</p>"
    partes = [f"<h2 style='color:{_C_ACENTO}'>{e.titulo}</h2>"]
    g = GUIA.get(clave)
    if g:
        partes += [_guia_html(g), f"<h3 style='color:{_C_ACENTO};margin-top:14px'>Fundamento técnico</h3>"]
    partes.append(e.texto)
    if e.formula:
        partes.append(f"<h4>Fórmula</h4><p style='font-family:monospace;font-size:110%'>{e.formula}</p>")
    if e.tipicos:
        partes.append(f"<h4>Valores típicos</h4><p>{e.tipicos}</p>")
    if e.referencia:
        partes.append(f"<h4>Referencia</h4><p>{e.referencia}</p>")
    if e.relacionadas:
        enlaces = " · ".join(f"<a href='ayuda:{r}'>{A[r].titulo}</a>" for r in e.relacionadas if r in A)
        partes.append(f"<h4>Vea también</h4><p>{enlaces}</p>")
    return "\n".join(partes)
