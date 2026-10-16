"""Textos de ayuda en español para cada dato, coeficiente, opción y fenómeno.

Cada entrada tiene: título, explicación (HTML simple), fórmula (opcional),
valores típicos (opcional), referencia normativa y entradas relacionadas.
La clave de cada entrada es la misma que usa la interfaz (campo) o el
código de la alerta (fenómeno).
"""
from __future__ import annotations

from dataclasses import dataclass, field


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
_e("tipo_fluido", "Tipo de servicio",
   "<p>Define qué ecuaciones se aplican:</p><ul>"
   "<li><b>Líquido</b>: fluido incompresible. Se evalúan flujo crítico por vaporización, "
   "cavitación y flashing.</li>"
   "<li><b>Gas</b>: fluido compresible. Se aplica el factor de expansión Y y se evalúa flujo "
   "crítico (sónico) y número de Mach.</li>"
   "<li><b>Vapor de agua</b>: es un gas; el programa obtiene sus propiedades de las tablas "
   "IAPWS-95, sobrecalentado o saturado seco.</li></ul>"
   "<p>Si el líquido entra ya parcialmente vaporizado (mezcla líquido-vapor a la entrada), es un "
   "servicio bifásico y requiere el módulo bifásico.</p>",
   relacionadas=["fluido", "flashing"])

_e("fluido", "Fluido",
   "<p>Seleccione el fluido de la lista para que el programa calcule automáticamente densidad, "
   "presión de vapor, presión crítica, viscosidad, masa molar, relación de calores "
   "específicos y factor de compresibilidad a las condiciones de entrada de cada caso.</p>"
   "<p>Elija <b>Definido por el usuario</b> para ingresar las propiedades a mano (mezclas, "
   "fluidos de proceso, datos de la hoja de datos del proyecto). Las propiedades provienen de "
   "la biblioteca CoolProp; para agua y vapor usa la formulación IAPWS-95.</p>",
   relacionadas=["rho", "Pv", "Pc", "viscosidad"])

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

_e("M", "Masa molar M",
   "<p>Masa de un kilomol del gas (kg/kmol). Para mezclas use el promedio ponderado por fracción "
   "molar. Se relaciona con la densidad relativa al aire: G = M / 28,96.</p>",
   tipicos="Aire 28,96; gas natural 16–20; vapor de agua 18,015; CO₂ 44,01",
   relacionadas=["rho", "Z"])

_e("gamma", "Relación de calores específicos γ",
   "<p>γ = cp / cv del gas a condiciones de entrada. Afecta la caída de presión a la que el gas "
   "llega a velocidad sónica a través del factor Fγ = γ / 1,40.</p>",
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

_e("xFz", "Relación de inicio de cavitación xFz",
   "<p>Valor de xF = ΔP/(P1 − Pv) a partir del cual comienza la cavitación (determinado por "
   "ensayos de ruido según IEC 60534-8-2). Si no se ingresa, el programa usa la estimación típica "
   "de IEC 60534-8-4, que depende del Kv, FL y Fd; luego se corrige por la presión de entrada "
   "(xFzp1).</p>",
   formula="xFz ≈ 0,90 / √(1 + 3·Fd·√(Kv/(N34·FL)));   xFzp1 = xFz·(6·10⁵ Pa / P1)^0,125",
   referencia="IEC 60534-8-4",
   relacionadas=["cavitacion", "sigma"], categoria="Coeficientes")

_e("tamano", "Diámetro de la válvula",
   "<p>Diámetro nominal de las conexiones de la válvula. Elija <b>Automático</b> para que el "
   "programa recorra los tamaños estándar y proponga el menor que cumpla el caso máximo con "
   "apertura ≤ 85 %, sin superar el diámetro de la línea. Con un diámetro fijo el programa "
   "verifica esa válvula.</p>",
   relacionadas=["apertura", "D1", "Kv_nominal"])

_e("D1", "Diámetro interior de la tubería",
   "<p>Diámetro interior de la tubería aguas arriba (D1) y aguas abajo (D2). Si son mayores que la "
   "válvula se consideran reductores concéntricos y se calculan FP, FLP y xTP. Dejar en blanco "
   "equivale a línea del mismo tamaño que la válvula.</p><p>El diámetro de salida también se "
   "usa para calcular velocidades y verificar API RP 14E.</p>",
   tipicos="DI cédula 40 (ASME B36.10M): 2\" 52,5 mm; 4\" 102,3 mm; 6\" 154,1 mm; 8\" 202,7 mm",
   relacionadas=["FP", "FLP", "xTP", "erosional_api14e"])

_e("Kv_nominal", "Capacidad nominal de la válvula",
   "<p>Kv (o Cv) de la válvula completamente abierta. Si se deja en blanco el programa usa un "
   "valor <b>típico</b> del estilo (Cv ≈ Cd·d², con d en pulgadas), suficiente para "
   "preseleccionar el tamaño. Para verificar una válvula ofertada, ingrese su valor "
   "certificado y fije el diámetro.</p>",
   relacionadas=["apertura", "kv_cv"])

_e("caracteristica", "Característica inherente",
   "<p>Relación entre la carrera y la capacidad a caída de presión constante.</p><ul>"
   "<li><b>Isoporcentual</b>: cada incremento igual de carrera aumenta la capacidad en el mismo "
   "porcentaje. Es la más usada cuando la caída de presión de la válvula disminuye al aumentar "
   "el caudal.</li><li><b>Lineal</b>: capacidad proporcional a la carrera. Apta cuando la "
   "válvula toma casi toda la pérdida del sistema (control de nivel, by-pass).</li>"
   "<li><b>Apertura rápida</b>: para servicios todo-nada.</li></ul>",
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
   "bloqueado o crítico). Si ΔP ≥ ΔPchoked, la válvula se dimensiona con ΔPchoked.</p>",
   formula="ΔPchoked = (FLP/FP)²·(P1 − FF·Pv)", referencia="IEC 60534-2-1 ec. (3)",
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
   "<p>Ajusta xT, que se determina con aire, al gas real.</p>", formula="Fγ = γ/1,40",
   relacionadas=["gamma"], categoria="Resultados")

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
   "<p>El servicio no cavita, pero está a menos del 20 % del inicio. Variaciones normales de "
   "operación (mayor temperatura, menor P2) pueden hacerlo cavitar.</p>",
   relacionadas=["cavitacion"], categoria="Fenómenos")

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


def obtener(clave: str) -> EntradaAyuda | None:
    if clave in A:
        return A[clave]
    if clave.startswith("dato_"):
        return EntradaAyuda("Dato de entrada inválido",
                            "<p>Uno de los datos ingresados está fuera del rango físico o es "
                            "incoherente con los demás. Revise el campo indicado en el mensaje y "
                            "sus unidades.</p>", categoria="Fenómenos")
    return None


def html(clave: str) -> str:
    e = obtener(clave)
    if e is None:
        return f"<h2>{clave}</h2><p>Sin ayuda disponible.</p>"
    partes = [f"<h2>{e.titulo}</h2>", e.texto]
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
