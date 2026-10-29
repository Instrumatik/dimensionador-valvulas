"""Guía didáctica de cada tema de ayuda, pensada para quien se inicia en el dimensionamiento.

Por tema: qué es, qué hace, qué indica, umbrales, qué pasa por debajo y por encima, qué cálculos
afecta, recomendaciones y un ejemplo numérico. ayuda.html() la muestra antes del fundamento técnico.
"""

GUIA = {
    'sistema_unidades': {
        'que_es': ('Es la elección de las unidades con que se ingresan y se muestran los datos: '
                   'Sistema Internacional (SI) o sistema imperial (EE. UU.).'),
        'que_hace': ('Permite trabajar con las unidades de la hoja de datos del proyecto sin '
                     'convertir a mano. Internamente el programa pasa todo a kPa absolutos, K, '
                     'm³/h, kg/h y mm antes de calcular.'),
        'que_indica': ('No cambia el resultado físico: una misma válvula da el mismo Cv en '
                       'cualquier sistema. Solo cambia cómo se leen los números en pantalla y en '
                       'los entregables.'),
        'umbrales': ('No hay umbrales numéricos. Buena práctica: usar el sistema de la hoja de '
                     'datos del cliente y revisar que cada campo tenga la unidad correcta (en '
                     'especial presiones absolutas frente a manométricas y caudal normal frente a '
                     'real).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Una hoja de datos indica P1 = 100 psig. Si se elige psig en el selector, el '
                    'programa la convierte a 689,5 + 101,3 = 790,8 kPa a. Si por error se carga '
                    'como 100 psia (689,5 kPa a), la presión usada sería un 13 % menor y el Cv '
                    'calculado cambiaría.'),
        'afecta': [
            'Conversión de todas las entradas',
            'Presentación de resultados y entregables',
            'Cv/Kv mostrado',
        ],
        'recomendaciones': [
            'Antes de cargar datos, verifique la unidad de cada campo contra la hoja de datos.',
            ('Si los datos vienen mezclados (por ejemplo presión en psig y caudal en m³/h), use el'
             ' selector de unidad de cada campo en lugar de convertir a mano.'),
            ('Preste especial atención a las presiones: confundir barg con bar a es el error más '
             'frecuente.'),
            'Revise el entregable en el sistema que pide el cliente antes de emitirlo.',
        ],
    },
    'presion_abs_man': {
        'que_es': ('La presión absoluta se mide desde el vacío total; la manométrica se mide desde'
                   ' la presión atmosférica local. Se relacionan con P<sub>abs</sub> = '
                   'P<sub>man</sub> + P<sub>atm</sub>.'),
        'que_hace': ('Todas las ecuaciones de dimensionamiento usan presiones absolutas. El '
                     'programa suma la presión atmosférica (101,325 kPa por defecto) cuando se '
                     'ingresa una unidad manométrica.'),
        'que_indica': ('Una presión absoluta nunca puede ser negativa; una manométrica negativa '
                       'indica vacío. La diferencia entre ambas pesa mucho cuando la presión de '
                       'servicio es baja.'),
        'umbrales': ('La presión atmosférica estándar es 101,325 kPa (1,01325 bar; 14,696 psi) a '
                     'nivel del mar; en altura es menor (por ejemplo unos 75 kPa a 2 500 m). El '
                     'error de confusión es relevante cuando P1 es menor que unos 10 bar a '
                     '(práctica habitual de criterio).'),
        'por_debajo': ('Si se carga una presión manométrica como absoluta, el programa usa una '
                       'presión menor que la real: puede predecir flujo crítico, cavitación o '
                       'flashing que no existen, o un Cv excesivo.'),
        'por_encima': ('Si se carga una absoluta como manométrica, se suma la atmósfera dos veces:'
                       ' se subestima el riesgo de cavitación y flujo crítico.'),
        'ejemplo': ('Un vapor llega a 0,5 barg y descarga a la atmósfera (0 barg). En absoluto son'
                    ' 1,513 bar a y 1,013 bar a: x = ΔP/P1 = 0,33. Si se cargara 0,5 bar como '
                    'absoluto, P1 sería menor que P2 y el cálculo no tendría sentido físico.'),
        'afecta': [
            'Cv requerido',
            'Factor de expansión Y',
            'Flujo crítico (choked)',
            'Alerta de cavitación',
            'Alerta de flashing',
            'Densidad del gas',
        ],
        'recomendaciones': [
            ('Confirme en la hoja de datos si la presión está en «g» (manométrica) o «a» '
             '(absoluta).'),
            'Si la planta está en altura, ingrese la presión atmosférica local real.',
            'Use siempre el selector de unidad con «g» o «a» explícito en lugar de restar a mano.',
            'En servicios de vacío, trabaje directamente en presión absoluta.',
        ],
    },
    'kv_cv': {
        'que_es': ('Es el número que mide la capacidad de paso de una válvula. Kv es el caudal de '
                   'agua en m³/h que pasa con 1 bar de caída; Cv es el caudal en galones US por '
                   'minuto que pasa con 1 psi de caída.'),
        'que_hace': ('El programa calcula el Cv (o Kv) requerido por el proceso en cada caso; '
                     'luego se compara con el Cv nominal de cada tamaño de válvula para elegir el '
                     'diámetro y estimar la apertura.'),
        'que_indica': ('Cuanto mayor es el Cv requerido, más grande o más abierta debe estar la '
                       'válvula. La relación entre Cv requerido y Cv nominal indica qué tan '
                       'abierta trabajará la válvula.'),
        'umbrales': ('Práctica habitual: la válvula debe operar entre aproximadamente 20 % y 80 % '
                     'de apertura en el rango de casos (el programa usa como límite 85 % en el '
                     'caso máximo). Conversión: Cv = 1,156·Kv.'),
        'por_debajo': ('Si la apertura en el caso mínimo queda por debajo de 10–20 %, la válvula '
                       'trabaja cerca del asiento: control inestable, erosión del obturador y peor'
                       ' rangeabilidad.'),
        'por_encima': ('Si la apertura en el caso máximo supera 80–85 %, la válvula queda sin '
                       'margen para absorber perturbaciones y la ganancia se vuelve muy baja; '
                       'conviene el tamaño siguiente.'),
        'ejemplo': ('Agua a 15 °C, Q = 50 m³/h, ΔP = 2 bar: Kv = 50·√(1/2) = 35,4 m³/h, es decir '
                    'Cv = 40,9. Si la válvula de 2" elegida tiene Cv nominal 60, con '
                    'característica isoporcentual trabajará alrededor del 85–90 % de carrera; '
                    'conviene evaluar la de 3".'),
        'afecta': [
            'Selección del tamaño de válvula',
            'Apertura estimada por caso',
            'Rangeabilidad',
            'Velocidades en la válvula',
            'Ruido',
        ],
        'recomendaciones': [
            'No sume márgenes en caudal, ΔP y Cv a la vez; aplique un margen único y razonado.',
            ('Si el caso mínimo queda muy cerrado, considere internos de Cv reducido o dos '
             'válvulas en paralelo (split range).'),
            ('Si el caso máximo queda muy abierto, pase al tamaño siguiente o a un estilo de mayor'
             ' capacidad.'),
            ('Use la característica de la válvula (isoporcentual o lineal) para estimar la '
             'apertura, no una regla proporcional.'),
        ],
    },
    'tipo_fluido': {
        'que_es': ('Es la clasificación del fluido que pasa por la válvula: líquido, gas, vapor de'
                   ' proceso o vapor de agua. Cada tipo tiene ecuaciones distintas en la norma.'),
        'que_hace': ('Selecciona qué ecuaciones de IEC 60534-2-1 se aplican, qué datos se piden y '
                     'qué verificaciones se hacen (cavitación y flashing en líquidos; factor Y, '
                     'flujo sónico y ruido aerodinámico en compresibles).'),
        'que_indica': ('Indica si el fluido cambia o no de densidad al pasar por la válvula. Un '
                       'líquido se trata como incompresible; un gas o vapor se expande al bajar la'
                       ' presión.'),
        'umbrales': ('No hay umbral numérico. Criterio: líquido si está por debajo de su punto de '
                     'burbuja en toda la válvula aguas arriba; gas si está lejos de condensar (Z '
                     'cercano a 1); vapor de proceso si está cerca de la saturación; vapor de agua'
                     ' para steam (IAPWS-95).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Agua a 25 °C y 8 bar a es claramente líquido. El mismo sistema con agua a 180'
                    ' °C y 8 bar a ya es vapor sobrecalentado (Tsat a 8 bar a ≈ 170 °C), y se debe'
                    ' dimensionar como vapor de agua con factor Y.'),
        'afecta': [
            'Ecuaciones de Cv utilizadas',
            'Factor de expansión Y',
            'Flujo crítico',
            'Alertas de cavitación y flashing',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Ruido aerodinámico IEC 60534-8-3',
            'Números de Mach',
        ],
        'recomendaciones': [
            ('Si el líquido entra a la válvula ya con vapor (bifásico), las ecuaciones de la norma'
             ' no aplican directamente; consulte métodos para flujo bifásico.'),
            'Para vapor de agua use siempre la opción específica (steam) en lugar de «gas».',
            ('Para hidrocarburos cerca de la saturación prefiera «vapor» e ingrese la densidad '
             'real.'),
            'Revise que el estado del fluido sea coherente con P1 y T1 en todos los casos.',
        ],
    },
    'fluido': {
        'que_es': ('Es la sustancia concreta que circula (agua, aire, propano, amoníaco, etc.) o '
                   'la opción de ingresar las propiedades a mano.'),
        'que_hace': ('Con un fluido de la lista, el programa calcula automáticamente densidad, '
                     'presión de vapor, presión crítica, viscosidad, masa molar, γ y Z a las '
                     'condiciones de entrada de cada caso.'),
        'que_indica': ('Las propiedades calculadas dependen de P1 y T1: el mismo fluido tiene '
                       'distinta densidad o presión de vapor en cada caso.'),
        'umbrales': ('No hay umbral. Buena práctica: usar un fluido de la lista cuando es un '
                     'componente puro, y «Definido por el usuario» para mezclas, con los datos de '
                     'la hoja de datos o del simulador de procesos.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Si se elige propano a 20 °C, el programa obtiene una densidad de unos 500 '
                    'kg/m³ y una presión de vapor de unos 836 kPa a. Con P2 = 700 kPa a habría '
                    'flashing, algo que pasaría inadvertido si se usara la densidad de un «aceite '
                    'genérico».'),
        'afecta': [
            'Densidad',
            'Presión de vapor y crítica',
            'Viscosidad y número de Reynolds',
            'Factor de compresibilidad Z',
            'Relación γ / exponente isoentrópico',
            'Cv requerido',
        ],
        'recomendaciones': [
            ('Para mezclas de hidrocarburos no use un componente puro como sustituto; ingrese las '
             'propiedades de la mezcla.'),
            ('Compare las propiedades calculadas con las de la hoja de datos; si difieren más de '
             'unos pocos por ciento, investigue el motivo.'),
            'En agua y vapor confíe en IAPWS-95, que es la referencia industrial.',
            ('Si el fluido tiene sólidos o es muy viscoso, anótelo: afecta la elección del estilo '
             'de válvula.'),
        ],
    },
    'composicion_gn': {
        'que_es': ('Es la cromatografía del gas natural: el % molar de metano, etano, propano, '
                   'nitrógeno, CO₂ y demás componentes de la mezcla.'),
        'que_hace': ('Con «Gas natural» en la lista, N25 calcula con ella la masa molar, la '
                     'viscosidad, el exponente isoentrópico y Z1 a la entrada, y T2 y Z2 a la salida '
                     'por expansión isoentálpica (ecuación de estado multicomponente HEOS de '
                     'CoolProp).'),
        'que_indica': ('Más etano, propano y butanos suben la masa molar y bajan Z; más N₂ y CO₂ '
                       'reducen el poder calorífico pero cambian poco la hidráulica.'),
        'umbrales': ('La suma debe ser 100 %; entre 95 y 105 % se normaliza. Gas de gasoducto '
                     'típico: metano 85–96 %, etano 2–8 %, propano 0,5–3 %.'),
        'por_debajo': ('Si falta un componente pesado de la cromatografía, M y la densidad salen '
                       'bajas y el Cv requerido algo menor que el real.'),
        'por_encima': ('Si se sobrestiman los pesados, M y la densidad salen altas y el Cv '
                       'requerido algo mayor.'),
        'ejemplo': ('90 % metano, 5 % etano, 2 % propano, 1 % butanos, 1 % N₂ y 1 % CO₂, de 70 a '
                    '20 bar a desde 27 °C: Z1 ≈ 0,86, T2 ≈ 2 °C y Z2 ≈ 0,94. Con metano puro T2 '
                    'sería ≈ 5 °C.'),
        'afecta': [
            'Masa molar y densidad',
            'Viscosidad y número de Reynolds',
            'Exponente isoentrópico y flujo crítico',
            'Z1, T2 y Z2',
            'Ruido aerodinámico y velocidades',
        ],
        'recomendaciones': [
            'Cargue la cromatografía del proyecto; la composición por defecto es solo típica.',
            'Si hay H₂S o CO₂, declárelos además como agentes en 3-Materiales (ISO 15156).',
            ('Con gas húmedo o cerca del punto de rocío use «Definido por el usuario» con los datos '
             'del simulador: N25 trata la mezcla como gas.'),
        ],
    },
    'caudal': {
        'que_es': ('Es la cantidad de fluido por unidad de tiempo que la válvula debe dejar pasar '
                   'en cada caso. Puede expresarse en volumen (m³/h, gpm), en masa (kg/h, lb/h) o '
                   'en volumen normal/estándar para gases (Nm³/h, Sm³/h, scfh).'),
        'que_hace': ('Es, junto con la caída de presión, el dato principal para calcular el Cv '
                     'requerido. El caso de caudal máximo define el tamaño y el mínimo verifica '
                     'que la válvula no quede casi cerrada.'),
        'que_indica': ('El Cv requerido es proporcional al caudal: duplicar el caudal duplica el '
                       'Cv. En gases, un caudal normal mal interpretado introduce un error '
                       'sistemático.'),
        'umbrales': ('No hay umbral de norma. Práctica habitual: relación caudal máximo/mínimo '
                     'dentro de la rangeabilidad de la válvula (típicamente 20:1 a 50:1) y un '
                     'margen único de 10–25 % sobre el caudal normal para el caso máximo. Nm³/h (0'
                     ' °C) y Sm³/h (15 °C) difieren un 5,5 %.'),
        'por_debajo': ('Si el caudal mínimo es muy bajo frente al máximo, la válvula trabaja casi '
                       'cerrada: mala controlabilidad y erosión del asiento.'),
        'por_encima': ('Si el caudal máximo está inflado por márgenes sucesivos, la válvula queda '
                       'sobredimensionada y controla mal en operación normal.'),
        'ejemplo': ('Una hoja de datos indica 10 000 Nm³/h de gas natural y el ingeniero lo carga '
                    'como Sm³/h. El caudal real es 10 000·288,15/273,15 = 10 549 Sm³/h, por lo que'
                    ' el Cv quedaría subestimado un 5 %.'),
        'afecta': [
            'Cv requerido',
            'Selección del tamaño de válvula',
            'Apertura estimada',
            'Velocidades y números de Mach',
            'Ruido aerodinámico e hidrodinámico',
            'Rangeabilidad',
        ],
        'recomendaciones': [
            'En gases y vapor ingrese caudal másico siempre que sea posible.',
            'Confirme la condición de referencia del caudal normal (0 °C o 15 °C; 1,01325 bar).',
            'Cargue los tres casos (mínimo, normal, máximo) con sus propias presiones.',
            ('Si la rangeabilidad requerida supera la de una válvula, considere dos válvulas en '
             'split range.'),
        ],
    },
    'casos': {
        'que_es': ('Son las distintas condiciones de proceso (caudal, presiones, temperatura) en '
                   'que la válvula debe trabajar: típicamente mínimo, normal y máximo.'),
        'que_hace': ('Cada caso se calcula por separado. El máximo define el tamaño; el mínimo '
                     'verifica la controlabilidad a baja apertura; el normal muestra dónde '
                     'trabajará la mayor parte del tiempo.'),
        'que_indica': ('La dispersión de aperturas entre casos indica si una sola válvula puede '
                       'cubrir todo el rango con buen control.'),
        'umbrales': ('Criterio del programa: el menor tamaño cuya apertura en el caso máximo no '
                     'supere 85 %. Práctica habitual: caso normal entre 50 % y 70 % y caso mínimo '
                     'por encima de 10–20 % de apertura.'),
        'por_debajo': ('Si el caso mínimo queda por debajo de 10 % de apertura, el control es '
                       'pobre y el asiento se erosiona por alta velocidad.'),
        'por_encima': ('Si el caso máximo supera 85 % de apertura, no queda capacidad de reserva; '
                       'el programa elige el tamaño siguiente.'),
        'ejemplo': ('Caso máximo 120 m³/h y mínimo 15 m³/h de agua. Con una válvula de 4" el '
                    'máximo queda al 75 % y el mínimo al 25 %: buen diseño. Con una de 6", el '
                    'máximo bajaría al 50 % pero el mínimo quedaría al 8 %: sobredimensionada.'),
        'afecta': [
            'Selección del tamaño de válvula',
            'Apertura estimada por caso',
            'Alertas por caso (cavitación, flashing, ruido)',
            'Entregables y hoja de datos',
        ],
        'recomendaciones': [
            ('Cargue cada caso con su propio P1 y P2: con caudal bajo, la bomba entrega más '
             'presión y la tubería pierde menos.'),
            'Evite apilar márgenes en caudal, ΔP y Cv.',
            'Incluya casos especiales (arranque, purga) si imponen condiciones severas.',
            ('Si los casos no caben en una válvula, evalúe internos de característica distinta o '
             'split range.'),
        ],
    },
    'P1': {
        'que_es': ('Es la presión estática del fluido en la tubería justo antes de la válvula, '
                   'medida a unos 2 diámetros de la brida de entrada, con el caudal circulando.'),
        'que_hace': ('Es la referencia para casi todos los cálculos: caída de presión, densidad '
                     'del gas, relación x = ΔP/P1, flujo crítico, cavitación y ruido.'),
        'que_indica': ('Una P1 más alta da más energía disponible; en gases aumenta la densidad y '
                       'la capacidad másica. La relación entre P1 y Pv (líquidos) o entre ΔP y P1 '
                       '(gases) define la severidad del servicio.'),
        'umbrales': ('No hay umbral único: debe ser coherente con el balance hidráulico (P1 > P2 '
                     'siempre) y con la clase de presión de la válvula según ASME B16.34 a la '
                     'temperatura de diseño.'),
        'por_debajo': ('Si P1 es menor que la real, se sobrestima el Cv y pueden aparecer falsas '
                       'alertas de flujo crítico.'),
        'por_encima': ('Si P1 supera la presión admisible de la clase seleccionada a la '
                       'temperatura de diseño, el cuerpo no es apto; si es mayor que la real, el '
                       'Cv queda subestimado.'),
        'ejemplo': ('Una bomba entrega 12 barg con caudal máximo y 15 barg con caudal mínimo. En '
                    'el caso mínimo debe ingresarse P1 = 15 barg (16,0 bar a), no 12 barg; de lo '
                    'contrario se subestima la ΔP y la válvula parece necesitar más apertura de la'
                    ' real.'),
        'afecta': [
            'Cv requerido',
            'ΔP y ΔP choked',
            'Densidad del gas',
            'Factor de expansión Y',
            'Alertas de cavitación y flashing',
            'Ruido',
            'Clase de presión ASME B16.34',
        ],
        'recomendaciones': [
            ('Use la presión con caudal, obtenida del balance hidráulico, no la de cierre de la '
             'bomba.'),
            'Ingrese P1 en absoluta o con la unidad manométrica correcta.',
            ('Para la clase de presión use la presión de diseño (cierre de bomba, ajuste de '
             'válvula de seguridad), no la de operación.'),
            'Cargue un P1 distinto para cada caso de operación.',
        ],
    },
    'P2': {
        'que_es': ('Es la presión estática en la tubería después de la válvula, medida a unos 6 '
                   'diámetros de la brida de salida.'),
        'que_hace': ('Con P1 define la caída de presión ΔP = P1 − P2 que la válvula debe absorber,'
                     ' y se compara con la presión de vapor para detectar flashing.'),
        'que_indica': ('Cuanto más baja es P2 respecto de P1, mayor es la caída y menor el Cv '
                       'requerido, pero más severas las condiciones (cavitación, flashing, ruido, '
                       'flujo sónico).'),
        'umbrales': ('En líquidos: P2 ≤ Pv indica flashing. En gases: si ΔP/P1 ≥ Fγ·xT el flujo es'
                     ' crítico (sónico). Práctica habitual: ΔP de la válvula de al menos 1/3 de la'
                     ' pérdida dinámica del sistema.'),
        'por_debajo': ('Si P2 cae por debajo de Pv (líquidos), hay flashing: el líquido sale '
                       'parcialmente vaporizado, con alta velocidad y erosión aguas abajo.'),
        'por_encima': ('Si P2 es muy cercana a P1, la ΔP es pequeña: la válvula necesita mucho Cv '
                       'y tiene poca autoridad de control.'),
        'ejemplo': ('Agua a 120 °C (Pv ≈ 198,5 kPa a) entra a 600 kPa a y descarga a un tanque a '
                    '150 kPa a. Como P2 < Pv, el programa avisa flashing y el caudal queda '
                    'limitado por ΔP choked, no por la ΔP total.'),
        'afecta': [
            'ΔP',
            'Cv requerido',
            'Alerta de flashing',
            'Flujo crítico',
            'Factor de expansión Y',
            'Ruido aerodinámico e hidrodinámico',
            'Velocidad de salida',
        ],
        'recomendaciones': [
            ('Obtenga P2 del balance hidráulico aguas abajo (pérdidas de tubería, alturas y '
             'presión del recipiente receptor).'),
            ('Si hay flashing, prefiera válvulas angulares con descarga directa al recipiente y '
             'materiales endurecidos.'),
            ('Si la caída es muy grande, evalúe reducción en etapas (internos multietapa u '
             'orificio aguas abajo).'),
            'Cargue P2 propio para cada caso.',
        ],
    },
    'dP': {
        'que_es': ('Es la diferencia entre la presión de entrada y la de salida de la válvula: ΔP '
                   '= P1 − P2.'),
        'que_hace': ('Es la «fuerza» que impulsa el caudal: el Cv requerido en líquidos es '
                     'proporcional a Q/√ΔP. Si ΔP supera el límite de flujo crítico, se usa ΔP '
                     'choked para dimensionar.'),
        'que_indica': ('Una ΔP grande permite una válvula más chica, pero aumenta el riesgo de '
                       'cavitación, ruido y desgaste. Una ΔP pequeña da poca autoridad de control.'),
        'umbrales': ('Práctica habitual: ΔP de la válvula ≥ 1/3 de la pérdida dinámica total del '
                     'sistema, o un mínimo de unos 0,7 bar (10 psi). Límite físico en líquidos: ΔP'
                     ' choked = FL²·(P1 − FF·Pv); en gases x choked = Fγ·xT.'),
        'por_debajo': ('Con ΔP muy baja (autoridad menor a 0,25–0,33), la válvula necesita mucho '
                       'Cv, queda grande y su efecto sobre el caudal es débil: control lento e '
                       'impreciso.'),
        'por_encima': ('Si ΔP supera ΔP choked, el caudal no aumenta más (flujo crítico) y '
                       'aparecen cavitación severa o flashing en líquidos, o flujo sónico y ruido '
                       'alto en gases.'),
        'ejemplo': ('Agua a 20 °C, P1 = 10 bar a, Pv = 0,023 bar a, FF ≈ 0,96. Con una válvula '
                    'globo FL = 0,90: ΔP choked = 0,81·(10 − 0,022) ≈ 8,1 bar. Con una mariposa FL'
                    ' = 0,65 el límite baja a unos 4,2 bar: si la ΔP real es 6 bar, la mariposa '
                    'trabajaría con flujo crítico.'),
        'afecta': [
            'Cv requerido',
            'Flujo crítico (choked)',
            'Factor de expansión Y',
            'Alerta de cavitación',
            'Ruido IEC 60534-8-3 / 8-4',
            'Autoridad de control',
        ],
        'recomendaciones': [
            ('Asigne la ΔP de la válvula en el balance hidráulico desde el inicio del proyecto, no'
             ' al final.'),
            ('Si la ΔP es excesiva, use internos multietapa o reparta la caída con un orificio '
             'restrictor.'),
            'Verifique que la ΔP de cada caso sea coherente con la curva de la bomba.',
            'No dimensione con ΔP mayor que ΔP choked: el caudal real no aumentaría.',
        ],
    },
    'T1': {
        'que_es': ('Es la temperatura del fluido justo antes de la válvula en cada caso de '
                   'operación.'),
        'que_hace': ('En líquidos fija la presión de vapor y la viscosidad; en gases y vapores '
                     'define la densidad y el estado (sobrecalentado o saturado).'),
        'que_indica': ('En líquidos, una T1 más alta acerca el fluido a su punto de ebullición y '
                       'aumenta el riesgo de cavitación o flashing. En gases, a mayor T1 menor '
                       'densidad y mayor caudal volumétrico.'),
        'umbrales': ('No hay umbral único. Debe estar dentro del rango de temperatura del material'
                     ' del cuerpo y de la empaquetadura (ASME B16.34), y en líquidos conviene un '
                     'margen de subenfriamiento respecto de la saturación a P1.'),
        'por_debajo': ('En gases, una T1 subestimada da densidad mayor y Cv menor al real. En '
                       'vapor de agua, por debajo de la saturación hay condensado, lo que invalida'
                       ' el cálculo como gas.'),
        'por_encima': ('En líquidos, una T1 subestimada oculta el riesgo de flashing. Por encima '
                       'de los límites del material se requieren otros materiales, bonete '
                       'extendido o empaquetadura especial.'),
        'ejemplo': ('Agua a 80 °C tiene Pv ≈ 47,4 kPa a; a 90 °C, Pv ≈ 70,1 kPa a. Con P2 = 60 kPa'
                    ' a, el mismo servicio no tiene flashing a 80 °C pero sí a 90 °C: 10 °C de '
                    'diferencia cambian el diagnóstico.'),
        'afecta': [
            'Presión de vapor Pv',
            'Densidad',
            'Viscosidad y Reynolds',
            'Alertas de cavitación y flashing',
            'Clase de presión-temperatura ASME B16.34',
            'Ruido aerodinámico',
        ],
        'recomendaciones': [
            'Use la temperatura real en la entrada de la válvula, no la del equipo lejano.',
            'En vapor de agua, deje T1 en blanco solo si realmente es vapor saturado seco.',
            ('Para servicios por encima de unos 230 °C o criogénicos, revise bonete extendido y '
             'materiales.'),
            'Cargue T1 propia por caso (arranque, operación normal).',
        ],
    },
    'rho': {
        'que_es': ('Es la masa por unidad de volumen del fluido a las condiciones de entrada (P1, '
                   'T1), en kg/m³.'),
        'que_hace': ('En líquidos se usa como densidad relativa ρ1/ρ0 (ρ0 = 999,1 kg/m³) en la '
                     'ecuación de Cv; en gases convierte caudal másico en volumétrico y entra en '
                     'el cálculo de Cv y de velocidades.'),
        'que_indica': ('Un fluido más denso necesita más Cv para el mismo caudal volumétrico con '
                       'igual ΔP (Cv ∝ √ρ). En gases, la densidad crece casi en proporción a la '
                       'presión absoluta.'),
        'umbrales': ('Valores de referencia: agua 15 °C 999 kg/m³; gasolina 720–760; crudo liviano'
                     ' 820–870; aire a 1 bar a y 20 °C 1,19 kg/m³. No hay umbral; debe ser '
                     'coherente con el fluido y las condiciones.'),
        'por_debajo': ('Una densidad subestimada da un Cv menor al real en líquidos (la válvula '
                       'queda chica).'),
        'por_encima': ('Una densidad sobrestimada da un Cv mayor al real (válvula '
                       'sobredimensionada).'),
        'ejemplo': ('Gas natural con M = 18 kg/kmol, P1 = 5 000 kPa a, T1 = 300 K y Z = 0,90: ρ1 ='
                    ' 5 000·18/(0,90·8,314·300) ≈ 40,1 kg/m³. Con Z = 1 se obtendría 36,1 kg/m³, '
                    'un 10 % menos.'),
        'afecta': [
            'Cv requerido',
            'Velocidades y números de Mach',
            'Ruido aerodinámico e hidrodinámico',
            'Conversión de caudales',
        ],
        'recomendaciones': [
            ('Use la densidad a las condiciones de entrada de la válvula, no a condiciones '
             'estándar.'),
            'En gases, si no tiene la densidad, deje que el programa la calcule con M, Z y T1.',
            ('En vapores cerca de la saturación, ingrese la densidad real del simulador en vez de '
             'confiar en Z.'),
            ('Compare la densidad calculada con la de la hoja de datos; diferencias mayores a 2–3 '
             '% merecen revisión.'),
        ],
    },
    'Pv': {
        'que_es': 'Es la presión a la cual el líquido hierve a la temperatura de entrada T1.',
        'que_hace': ('Se compara con las presiones dentro y a la salida de la válvula para '
                     'detectar cavitación y flashing, y entra en el cálculo de ΔP choked = FL²·(P1'
                     ' − FF·Pv).'),
        'que_indica': ('Cuanto más cerca está Pv de P2 (o de la presión mínima interna), más fácil'
                       ' es que el líquido vaporice. Si P2 ≤ Pv hay flashing.'),
        'umbrales': ('Referencias de agua: 2,34 kPa a a 20 °C; 101,3 kPa a a 100 °C; 476 kPa a a '
                     '150 °C. Condición de flashing: P2 ≤ Pv. Inicio de cavitación: ΔP/(P1 − Pv) ≥'
                     ' xFz.'),
        'por_debajo': ('Si se ingresa una Pv menor que la real, se subestima el riesgo de '
                       'cavitación y flashing, y se sobrestima ΔP choked.'),
        'por_encima': ('Si Pv es mayor que la real, el programa dará alertas de cavitación o '
                       'flashing más conservadoras y una ΔP choked menor.'),
        'ejemplo': ('Agua a 150 °C (Pv = 476 kPa a) con P1 = 1 000 kPa a y P2 = 400 kPa a: como P2'
                    ' < Pv hay flashing. Si la misma agua estuviera a 120 °C (Pv ≈ 199 kPa a), no '
                    'habría flashing, aunque habría que verificar cavitación.'),
        'afecta': [
            'ΔP choked',
            'Factor FF',
            'Alerta de cavitación',
            'Alerta de flashing',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Cv requerido en flujo crítico',
        ],
        'recomendaciones': [
            'Use la Pv a la temperatura real de entrada; varía mucho con T1.',
            'En mezclas de hidrocarburos use la presión de burbuja de la mezcla.',
            ('Si hay riesgo de cavitación, aumente P2 (ubicando la válvula más abajo o con '
             'contrapresión) o elija internos anticavitación.'),
            ('Si hay flashing inevitable, use válvula angular, materiales endurecidos y descarga '
             'directa al recipiente.'),
        ],
    },
    'Pc': {
        'que_es': ('Es la presión del punto crítico termodinámico del fluido: por encima de ella '
                   'no existe diferencia entre líquido y vapor.'),
        'que_hace': ('Con Pv se calcula el factor de relación de presión crítica del líquido FF = '
                     '0,96 − 0,28·√(Pv/Pc), que estima la presión en la vena contracta en flujo '
                     'crítico.'),
        'que_indica': ('Por sí sola no indica la severidad del servicio; lo importante es la '
                       'relación Pv/Pc. Cuanto mayor es Pv/Pc, menor es FF y mayor la ΔP choked.'),
        'umbrales': ('Valores de referencia: agua 22 064 kPa a; propano 4 251 kPa a; amoníaco 11 '
                     '333 kPa a. FF varía entre 0,96 (Pv/Pc → 0) y unos 0,68 (Pv/Pc = 1).'),
        'por_debajo': ('Un Pc subestimado reduce FF y aumenta ΔP choked calculada (resultado algo '
                       'menos conservador).'),
        'por_encima': ('Un Pc sobrestimado acerca FF a 0,96 (resultado algo más conservador). El '
                       'efecto suele ser pequeño salvo en líquidos calientes o hidrocarburos '
                       'livianos.'),
        'ejemplo': ('Agua a 150 °C: Pv/Pc = 476/22 064 = 0,0216; √0,0216 = 0,147; FF = 0,96 − '
                    '0,28·0,147 ≈ 0,92. Para agua a 20 °C, FF ≈ 0,96: la diferencia en ΔP choked '
                    'es de pocos por ciento.'),
        'afecta': [
            'Factor FF',
            'ΔP choked',
            'Cv requerido en flujo crítico',
        ],
        'recomendaciones': [
            'Use el Pc del componente puro o el pseudocrítico de la mezcla.',
            ('Su influencia es mayor cuando Pv es una fracción importante de Pc (líquidos '
             'calientes, GLP).'),
            'Con un fluido de la lista, deje que el programa lo tome automáticamente.',
        ],
    },
    'viscosidad': {
        'que_es': ('Es la resistencia del fluido a fluir. La dinámica μ se mide en cP o Pa·s; la '
                   'cinemática ν = μ/ρ en cSt o m²/s.'),
        'que_hace': ('Se usa para calcular el número de Reynolds de la válvula Re<sub>v</sub>; si '
                     'el flujo no es completamente turbulento, se aplica el factor de corrección '
                     'FR < 1, que aumenta el Cv requerido.'),
        'que_indica': ('Una viscosidad alta, sobre todo en válvulas chicas o con poco caudal, '
                       'indica flujo laminar o de transición y necesidad de más capacidad.'),
        'umbrales': ('Re<sub>v</sub> ≥ 10 000: flujo turbulento, FR = 1. Por debajo, flujo de '
                     'transición o laminar (FR < 1). Valores típicos: agua 20 °C 1 cP; aceite '
                     'liviano 10–50 cP; gases 0,01–0,03 cP.'),
        'por_debajo': ('Con viscosidad baja (agua, solventes) el flujo es turbulento y su valor no'
                       ' influye en el Cv.'),
        'por_encima': ('Con viscosidad alta (aceites pesados, polímeros), Re<sub>v</sub> cae por '
                       'debajo de 10 000 y el Cv requerido puede aumentar 20 % a más del 100 %.'),
        'ejemplo': ('Un aceite de 500 cP a 30 m³/h en una válvula de 2" puede tener Re<sub>v</sub>'
                    ' del orden de unos pocos miles. El programa obtendría FR < 1 y un Cv '
                    'requerido mayor que el calculado como si fuera agua; con agua el mismo '
                    'servicio sería plenamente turbulento.'),
        'afecta': [
            'Número de Reynolds de la válvula',
            'Factor FR',
            'Cv requerido',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            ('Ingrese la viscosidad a la temperatura real de entrada; en aceites varía mucho con '
             'T1.'),
            'Si FR es bajo, verifique también el caso mínimo, que es el más afectado.',
            ('Para fluidos muy viscosos prefiera estilos de pasaje directo (bola segmentada, '
             'angular).'),
            'No confunda cP con cSt: para pasar de uno a otro se necesita la densidad.',
        ],
    },
    'M': {
        'que_es': ('Es la masa de un kilomol de gas, en kg/kmol. La gravedad específica SG es la '
                   'relación entre la masa molar del gas y la del aire: SG = M/28,96.'),
        'que_hace': ('Permite calcular la densidad del gas con ρ1 = P1·M/(Z·R·T1) y convertir '
                     'caudales normales a másicos.'),
        'que_indica': ('Un gas de mayor masa molar es más denso: a igual caudal másico ocupa menos'
                       ' volumen y requiere menos Cv; a igual caudal volumétrico requiere más.'),
        'umbrales': ('Valores de referencia: aire 28,96; gas natural 16–20; vapor de agua 18,015; '
                     'CO<sub>2</sub> 44,01; hidrógeno 2,016 kg/kmol. No hay umbral de norma.'),
        'por_debajo': 'Una M subestimada da densidad baja y, con caudal másico, Cv mayor al real.',
        'por_encima': ('Una M sobrestimada da densidad alta y, con caudal másico, Cv menor al real'
                       ' (válvula chica).'),
        'ejemplo': ('Un gas natural con SG = 0,62 tiene M = 0,62·28,96 ≈ 17,96 kg/kmol. Un error '
                    'de 0,05 en SG (por ejemplo usar 0,57) cambia la densidad un 8 % y el Cv '
                    'aproximadamente un 4 %.'),
        'afecta': [
            'Densidad del gas',
            'Cv requerido',
            'Conversión de caudal normal a másico',
            'Velocidades y números de Mach',
            'Ruido aerodinámico',
        ],
        'recomendaciones': [
            ('Para mezclas, calcule el promedio ponderado por fracción molar a partir de la '
             'cromatografía.'),
            'Si la hoja de datos da SG, use la unidad «SG (aire = 1)».',
            'Si la composición varía entre casos, cargue la M de cada caso.',
        ],
    },
    'gamma': {
        'que_es': ('Es la relación entre los calores específicos a presión constante y a volumen '
                   'constante del gas, γ = c<sub>p</sub>/c<sub>v</sub>. Para gases reales el '
                   'programa usa el exponente isoentrópico κ.'),
        'que_hace': ('Se usa en el factor Fγ = γ/1,40, que ajusta la relación de caídas a la que '
                     'el gas alcanza flujo crítico (x choked = Fγ·xT) y el factor de expansión Y.'),
        'que_indica': ('Un γ menor hace que el flujo se vuelva crítico con una caída de presión '
                       'relativa menor.'),
        'umbrales': ('Valores de referencia: aire 1,40; gas natural 1,27–1,31; vapor de agua '
                     '1,30–1,33; CO<sub>2</sub> 1,30. No hay umbral; debe ser coherente con el gas'
                     ' y sus condiciones.'),
        'por_debajo': ('Un γ subestimado adelanta el flujo crítico en el cálculo (resultado algo '
                       'conservador).'),
        'por_encima': ('Un γ sobrestimado (por ejemplo usar c<sub>p</sub>/c<sub>v</sub> cerca de '
                       'la saturación) retrasa el flujo crítico en el cálculo y puede subestimar '
                       'el Cv.'),
        'ejemplo': ('Vapor saturado a 10 bar: con κ = 1,29, Fγ = 0,921 y, con xT = 0,70, x choked '
                    '= 0,645. Si se usara c<sub>p</sub>/c<sub>v</sub> = 1,41, x choked sería 0,705'
                    ' y se subestimaría la cercanía al flujo crítico.'),
        'afecta': [
            'Factor Fγ',
            'Flujo crítico (choked)',
            'Factor de expansión Y',
            'Cv requerido',
            'Ruido aerodinámico IEC 60534-8-3',
        ],
        'recomendaciones': [
            ('Con un fluido de la lista o vapor de agua, deje que el programa use κ '
             'automáticamente.'),
            'Para mezclas, use el valor del simulador de procesos a las condiciones de entrada.',
            'Si no tiene datos, 1,30 es un valor razonable para hidrocarburos livianos y vapor.',
        ],
    },
    'Z': {
        'que_es': ('Es el factor que corrige la ley de gases ideales: P·v = Z·R·T. Vale 1 para gas'
                   ' ideal.'),
        'que_hace': 'Se usa para calcular la densidad del gas a la entrada: ρ1 = P1·M/(Z·R·T1).',
        'que_indica': ('Z cercano a 1 indica comportamiento casi ideal; Z menor que 1 indica que '
                       'el gas es más denso de lo que predice la ley ideal (alta presión o cerca '
                       'de la condensación).'),
        'umbrales': ('Gases a baja presión: 0,98–1,00. Gas natural a 70 bar: 0,85–0,90. Práctica '
                     'habitual: si Z está fuera de 0,95–1,05, no conviene asumir gas ideal.'),
        'por_debajo': ('Un Z subestimado da densidad mayor a la real: con caudal másico, Cv menor '
                       'al necesario.'),
        'por_encima': ('Un Z sobrestimado (por ejemplo usar 1 a alta presión) da densidad menor a '
                       'la real y Cv mayor; el error porcentual en densidad es igual al de Z.'),
        'ejemplo': ('Gas natural a 70 bar a y 15 °C tiene Z ≈ 0,87. Usar Z = 1 subestimaría la '
                    'densidad un 13 %; con caudal másico fijo el Cv calculado resultaría alrededor'
                    ' de un 7 % más alto.'),
        'afecta': [
            'Densidad del gas',
            'Cv requerido',
            'Velocidades y números de Mach',
            'Ruido aerodinámico',
        ],
        'recomendaciones': [
            'Use un fluido de la lista o el Z del simulador a P1 y T1.',
            'No use Z = 1 por defecto en gases de alta presión.',
            'Cerca de la condensación, prefiera ingresar la densidad real.',
            'Recalcule Z en cada caso si cambian P1 o T1.',
        ],
    },
    'mu': {
        'que_es': 'Es la viscosidad dinámica del gas, en cP o Pa·s.',
        'que_hace': ('Solo se usa para calcular el número de Reynolds de la válvula y verificar si'
                     ' el flujo es turbulento.'),
        'que_indica': ('En casi todos los servicios de gas el Reynolds es muy alto y su valor '
                       'exacto no cambia el Cv.'),
        'umbrales': ('Valores típicos: 0,01–0,03 cP (1–3·10<sup>-5</sup> Pa·s). Re<sub>v</sub> ≥ '
                     '10 000 significa flujo turbulento y FR = 1.'),
        'por_debajo': 'No aplica: valores bajos simplemente confirman flujo turbulento.',
        'por_encima': ('Solo influye si Re<sub>v</sub> cae por debajo de 10 000, lo que ocurre en '
                       'caudales muy pequeños o válvulas de laboratorio.'),
        'ejemplo': ('Aire a 0,018 cP pasando 500 Nm³/h por una válvula de 1" tiene un '
                    'Re<sub>v</sub> del orden de 10<sup>5</sup>: FR = 1 y la viscosidad no '
                    'influye. Solo en microcaudales de unos pocos Nm³/h podría acercarse a 10 000.'),
        'afecta': [
            'Número de Reynolds de la válvula',
            'Factor FR',
            'Cv requerido (solo en flujo no turbulento)',
        ],
        'recomendaciones': [
            'Si no tiene el dato, use 0,015 cP para hidrocarburos livianos o 0,018 cP para aire.',
            'Revise el Reynolds solo en válvulas muy chicas o caudales muy bajos.',
            'No dedique tiempo a precisar este dato salvo que FR resulte menor que 1.',
        ],
    },
    'estilo': {
        'que_es': ('Es el tipo constructivo de la válvula y sus internos: globo, angular, '
                   'mariposa, bola, jaula multiorificio, multietapa, etc.'),
        'que_hace': ('Determina los factores FL, xT y Fd y la característica inherente que usa el '
                     'programa; con ellos se calculan el flujo crítico, la cavitación, el ruido y '
                     'la apertura.'),
        'que_indica': ('El estilo indica qué tan bien resiste la válvula la cavitación y el ruido '
                       '(FL y xT altos) y cuánta capacidad tiene por diámetro.'),
        'umbrales': ('No hay umbral único. Valores típicos según IEC 60534-2-1 Tabla 2: globo FL '
                     '0,80–0,90 y xT 0,55–0,75; mariposa FL 0,62–0,70 y xT 0,35–0,42; bola FL '
                     '0,60–0,74.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Un servicio de agua con ΔP = 6 bar y P1 = 10 bar a cavita con una mariposa '
                    '(FL ≈ 0,65; ΔP choked ≈ 4,2 bar), pero no llega a flujo crítico con una globo'
                    ' (FL ≈ 0,90; ΔP choked ≈ 8,1 bar). Cambiar de estilo resuelve el problema sin'
                    ' cambiar el proceso.'),
        'afecta': [
            'FL, xT y Fd',
            'ΔP choked y x choked',
            'Alerta de cavitación',
            'Ruido IEC 60534-8-3 / 8-4',
            'Apertura estimada',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            'Use globo para control preciso y ΔP moderada.',
            'Use angular para flashing, sólidos o descarga a recipiente.',
            'Use mariposa o bola en diámetros grandes con ΔP baja.',
            'Para cavitación o ruido elevados use jaulas multiorificio o multietapa.',
            ('Reemplace los factores genéricos por los certificados del proveedor cuando los '
             'tenga.'),
        ],
    },
    'FL': {
        'que_es': ('Es el factor de recuperación de presión del líquido. Indica cuánto se recupera'
                   ' la presión entre la vena contracta (punto de menor presión dentro de la '
                   'válvula) y la salida.'),
        'que_hace': ('Define la caída de presión máxima útil en líquidos, ΔP choked = FL²·(P1 − '
                     'FF·Pv), y participa en la evaluación de cavitación y ruido.'),
        'que_indica': ('FL cercano a 1 significa poca recuperación: la presión interna no baja '
                       'mucho por debajo de P2 y la válvula resiste mejor la cavitación. FL bajo '
                       'significa mucha recuperación y cavitación más temprana.'),
        'umbrales': ('Valores típicos: globo 0,80–0,90; multietapa 0,97; mariposa 0,62–0,70; bola '
                     '0,60–0,74. Práctica habitual: en servicios con riesgo de cavitación preferir'
                     ' FL ≥ 0,85.'),
        'por_debajo': ('Con FL bajo (menor a unos 0,7), la válvula llega antes a flujo crítico y '
                       'cavitación; el caudal puede quedar limitado.'),
        'por_encima': ('FL alto es favorable; no hay problema técnico por FL alto, aunque suele '
                       'venir con menor capacidad por diámetro.'),
        'ejemplo': ('Con P1 = 10 bar a y agua fría: una válvula con FL = 0,9 admite ΔP choked ≈ '
                    '8,1 bar; con FL = 0,6 solo ≈ 3,6 bar. Para el mismo servicio de ΔP = 5 bar, '
                    'la segunda estaría en flujo crítico.'),
        'afecta': [
            'ΔP choked',
            'Cv requerido en flujo crítico',
            'Alerta de cavitación',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Factor FLP con reductores',
        ],
        'recomendaciones': [
            'Si hay cavitación, elija un estilo de FL mayor (globo o multietapa).',
            'Use los FL certificados del proveedor, no solo los genéricos.',
            ('Recuerde que con reductores de tubería el factor efectivo es FLP, que suele ser '
             'menor.'),
            ('FL varía con la apertura; en válvulas rotativas revise el valor al porcentaje de '
             'apertura de trabajo.'),
        ],
    },
    'xT': {
        'que_es': ('Es el factor de caída de presión crítica para gases: la relación ΔP/P1 a la '
                   'cual un gas con γ = 1,40 alcanza flujo crítico (sónico) en la válvula sin '
                   'reductores.'),
        'que_hace': ('Con Fγ define el límite de flujo crítico x choked = Fγ·xT y entra en el '
                     'factor de expansión Y = 1 − x/(3·Fγ·xT).'),
        'que_indica': ('Un xT alto indica que la válvula aprovecha más caída de presión antes de '
                       'bloquearse; un xT bajo indica que el flujo se vuelve crítico con caídas '
                       'relativas menores.'),
        'umbrales': ('Valores típicos: globo 0,55–0,75; mariposa 0,35–0,42; bola segmentada 0,30. '
                     'El flujo es crítico cuando x = ΔP/P1 ≥ Fγ·xT, y entonces Y alcanza su mínimo'
                     ' de 2/3 (0,667).'),
        'por_debajo': ('Con xT bajo, el flujo se vuelve crítico con poca caída: más capacidad '
                       'necesaria y mayor ruido.'),
        'por_encima': ('xT alto es favorable para la capacidad; no hay problema técnico por xT '
                       'alto.'),
        'ejemplo': ('Aire con P1 = 10 bar a en una globo con xT = 0,70: el flujo es crítico si ΔP '
                    '≥ 7 bar. Con ΔP = 3,5 bar, x = 0,35 e Y = 1 − 0,35/(3·0,70) = 0,833.'),
        'afecta': [
            'Factor de expansión Y',
            'Flujo crítico (sónico)',
            'Cv requerido',
            'Ruido aerodinámico IEC 60534-8-3',
            'Factor xTP con reductores',
        ],
        'recomendaciones': [
            'Use los xT certificados del proveedor para la apertura de trabajo.',
            'Con reductores de tubería, el programa usa xTP en lugar de xT.',
            ('Si el flujo es crítico y el ruido es alto, considere internos de baja emisión de '
             'ruido o reducción en etapas.'),
        ],
    },
    'Fd': {
        'que_es': ('Es el modificador de estilo de válvula: relación entre el diámetro hidráulico '
                   'de un pasaje y el diámetro de un orificio circular de igual área.'),
        'que_hace': ('Interviene en el cálculo del número de Reynolds de la válvula (y por lo '
                     'tanto en FR) y en la estimación del inicio de cavitación xFz y del ruido.'),
        'que_indica': ('Fd cercano a 1 indica un solo pasaje grande; Fd bajo indica muchos pasajes'
                       ' pequeños, típicos de jaulas multiorificio, que retrasan el inicio de '
                       'cavitación y reducen el ruido.'),
        'umbrales': ('Valores típicos: un solo pasaje 1,0; doble asiento 0,7; jaula de 60 '
                     'orificios 0,13 (IEC 60534-2-1 Anexo A). No es un parámetro de diseño libre '
                     'sino una propiedad del estilo.'),
        'por_debajo': ('Un Fd bajo reduce Re<sub>v</sub>: en fluidos viscosos puede aparecer flujo'
                       ' no turbulento antes, pero mejora el comportamiento frente a cavitación y '
                       'ruido.'),
        'por_encima': ('Un Fd alto (cercano a 1) da Re<sub>v</sub> mayor, pero la cavitación '
                       'comienza antes (xFz menor).'),
        'ejemplo': ('Con Kv = 100 m³/h y FL = 0,90: con Fd = 1,0 se obtiene xFz ≈ 0,16; con Fd = '
                    '0,13 (jaula multiorificio), xFz ≈ 0,41. La jaula admite unas 2,5 veces más de'
                    ' caída relativa antes de empezar a cavitar.'),
        'afecta': [
            'Número de Reynolds de la válvula',
            'Factor FR',
            'Relación de inicio de cavitación xFz',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            ('Use el valor del proveedor o el genérico del estilo; no lo ajuste para «mejorar» '
             'resultados.'),
            ('Para servicios con cavitación incipiente, internos multiorificio (Fd bajo) son una '
             'solución habitual.'),
            'En fluidos viscosos con internos de Fd bajo, verifique el factor FR.',
        ],
    },
    'xFz': {
        'que_es': ('Es la relación de cavitación incipiente: el valor de xF = ΔP/(P1 − Pv) a '
                   'partir del cual pueden aparecer las primeras burbujas (régimen incipiente de '
                   'ISA-RP75.23). Normalmente no daña.'),
        'que_hace': ('El programa la estima con la expresión típica de IEC 60534-8-4, corregida '
                     'por presión (xFzp1), y la informa como resultado para marcar la «cavitación '
                     'incipiente». El ruido se calcula con el Kc del trim; solo si Kc está en '
                     'blanco usa este xFz típico.'),
        'que_indica': ('Si Kapp supera xFzp1 pero no Kc hay cavitación incipiente: burbujas '
                       'aisladas, sin daño esperado. Algunas especificaciones conservadoras ya '
                       'piden trim anticavitación en este régimen.'),
        'umbrales': ('Típico 0,15–0,35 en trims de un pasaje; mayor en jaulas de orificios. En '
                     'multietapa se toma igual a Kc. xFzp1 = xFz·(6·10<sup>5</sup> '
                     'Pa/P1)<sup>0,125</sup>.'),
        'por_debajo': 'Si Kapp es menor que xFzp1 no se esperan burbujas.',
        'por_encima': ('Entre xFzp1 y Kc, cavitación incipiente; desde Kc, cavitación que puede '
                       'dañar.'),
        'ejemplo': ('Agua con Kv = 100 m³/h, FL = 0,90 y Fd = 0,46: xFz ≈ 0,23. Con P1 = 10 '
                    'bar(a), xFzp1 ≈ 0,22. Si Kapp = 0,40 y el Kc del trim es 0,65, el programa '
                    'informa cavitación incipiente, sin alerta de cavitación.'),
        'afecta': [
            'Condición «cavitación incipiente»',
            'Ruido IEC 60534-8-4 solo si Kc está en blanco',
        ],
        'recomendaciones': [
            'Revise si la especificación del cliente admite cavitación incipiente.',
            ('En servicio continuo con ΔP alta, considere internos endurecidos aunque no se supere'
             ' Kc.'),
        ],
    },
    'tamano': {
        'que_es': ('Es el diámetro nominal (DN o NPS) de las bridas o extremos de la válvula, por '
                   'ejemplo DN 80 (3"). No es lo mismo que el diámetro del orificio interno '
                   '(asiento), que suele ser menor.'),
        'que_hace': ('Define qué válvula se está evaluando: su Kv/Cv nominal, sus factores FL y '
                     'xT, y si hay reductores respecto de la tubería. En modo Automático el '
                     'programa prueba los tamaños estándar de menor a mayor y elige el primero que'
                     ' cumple.'),
        'que_indica': ('Un tamaño correcto deja la válvula controlando en la zona media de su '
                       'carrera. Si el programa necesita un tamaño igual al de la línea o no '
                       'encuentra ninguno, el caso máximo exige mucha capacidad o la caída de '
                       'presión disponible es muy baja.'),
        'umbrales': ('Criterio del programa: el menor tamaño con apertura ≤ 85 % en el caso máximo'
                     ' y sin superar el diámetro de la línea. Práctica habitual: la válvula queda '
                     'igual o una a dos medidas menor que la línea (p. ej. válvula de 3" en línea '
                     'de 4"); una válvula menor que la mitad de la línea es inusual.'),
        'por_debajo': ('Una válvula demasiado chica no alcanza el caudal máximo (apertura > 90 %),'
                       ' puede quedar en flujo bloqueado y genera altas velocidades, ruido y '
                       'erosión.'),
        'por_encima': ('Una válvula demasiado grande trabaja casi cerrada (apertura < 10-15 %), '
                       'controla mal por la ganancia excesiva y el juego mecánico, y desgasta el '
                       'asiento por alta velocidad cerca del cierre; además cuesta más.'),
        'ejemplo': ('Agua a 120 m³/h con ΔP = 1,5 bar requiere Kv ≈ 98 (Cv ≈ 113). Una globo de 3"'
                    ' con Cv nominal ≈ 130 quedaría cerca del 96 % de apertura, así que el '
                    'programa propone la de 4" (Cv ≈ 235), que trabaja alrededor del 81 % en '
                    'isoporcentual con R = 50, instalada en una línea de 4" o 6".'),
        'afecta': [
            'Selección del tamaño de válvula',
            'Kv/Cv nominal típico',
            'Apertura requerida',
            'Factores FP, FLP y xTP (reductores)',
            'Velocidad en la salida de la válvula',
            'Ruido aerodinámico IEC 60534-8-3 e hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            ('Use Automático en la etapa de preselección y fije el diámetro solo para verificar '
             'una válvula ofertada.'),
            ('Defina bien los casos mínimo, normal y máximo: el tamaño se decide con el máximo, '
             'pero la controlabilidad se verifica con el mínimo.'),
            ('No sobredimensione «por las dudas»: aplique márgenes razonables al caudal (10-25 %, '
             'práctica habitual) y no sobre todos los datos a la vez.'),
            ('Si la válvula resulta del tamaño de la línea con apertura alta, revise la caída de '
             'presión asignada a la válvula antes de agrandarla.'),
        ],
    },
    'D1': {
        'que_es': ('Es el diámetro interior real de la tubería conectada a la válvula, aguas '
                   'arriba (D1) y aguas abajo (D2). Depende del diámetro nominal y de la cédula '
                   '(espesor) del tubo.'),
        'que_hace': ('Permite calcular el efecto de los reductores concéntricos cuando la línea es'
                     ' mayor que la válvula (factores FP, FLP, xTP) y las velocidades del fluido '
                     'en la tubería, usadas para la verificación de API RP 14E y para el ruido.'),
        'que_indica': ('Si D1 o D2 son mayores que el diámetro de la válvula, hay reductores que '
                       'consumen parte de la presión y modifican la capacidad. Si son iguales (o '
                       'en blanco), no hay corrección por geometría de tubería.'),
        'umbrales': ('No es un dato con umbral: debe ser el DI real. Valores de referencia cédula '
                     '40 (ASME B36.10M): 2" 52,5 mm; 4" 102,3 mm; 6" 154,1 mm; 8" 202,7 mm. '
                     'Práctica habitual: velocidad en línea de líquido 1-3 m/s (3-10 ft/s) y en '
                     'gases hasta 20-40 m/s según el ruido.'),
        'por_debajo': ('Si se ingresa un DI menor que el real, el programa sobreestima la '
                       'velocidad y puede disparar alertas falsas de erosión o ruido.'),
        'por_encima': ('Si se ingresa un DI mayor que el real, se subestima la velocidad y se '
                       'exagera el efecto de los reductores (FP menor), lo que agranda el Cv '
                       'requerido.'),
        'ejemplo': ('Una válvula de 3" instalada en tubería de 4" cédula 40 lleva D1 = D2 = 102,3 '
                    'mm. Con 100 m³/h de agua la velocidad en la línea es 100/3600/(π·0,1023²/4) ≈'
                    ' 3,4 m/s, algo alta para una línea de líquido según la práctica habitual.'),
        'afecta': [
            'Factor de geometría de tubería FP',
            'FLP y ΔPchoked',
            'xTP y xchoked',
            'Velocidad de salida y verificación API RP 14E',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            ('Tome el DI de la cédula real del isométrico o de la especificación de tuberías, no '
             'el diámetro nominal.'),
            ('Si la salida tiene expansión (p. ej. en servicios con flashing o gas a alta caída), '
             'ingrese el D2 de la tubería mayor para ver la velocidad real.'),
            'Si no conoce la línea aún, deje en blanco y vuelva a verificar cuando esté definida.',
        ],
    },
    'Kv_nominal': {
        'que_es': ('Es el coeficiente de caudal de la válvula totalmente abierta: Kv en m³/h de '
                   'agua con 1 bar de caída, o Cv en gpm de agua con 1 psi. Se cumple Cv ≈ '
                   '1,156·Kv.'),
        'que_hace': ('Es la capacidad máxima de la válvula y se compara con el Kv requerido por '
                     'cada caso para estimar la apertura. También interviene en FP, FLP y xTP a '
                     'través del término C/d².'),
        'que_indica': ('Cuanto más se acerque el Kv requerido al Kv nominal, más abierta trabaja '
                       'la válvula. Un valor típico solo sirve para preseleccionar; el valor '
                       'certificado del fabricante (ensayado según IEC 60534-2-3) es el que vale '
                       'para verificar.'),
        'umbrales': ('Práctica habitual: el Kv requerido en el caso máximo entre el 70 % y el 90 %'
                     ' del Kv nominal en isoporcentual (o según la curva), y el Kv requerido '
                     'mínimo por encima de Kv nominal/R. Orden de magnitud para globo: Cv ≈ '
                     '10-14·d² (d en pulgadas).'),
        'por_debajo': ('Si el Kv nominal es poco mayor que el requerido (o menor), la válvula no '
                       'tiene margen y queda casi abierta o no pasa el caudal máximo.'),
        'por_encima': ('Si el Kv nominal es muchas veces mayor que el requerido, la válvula queda '
                       'sobredimensionada y trabaja cerca del asiento.'),
        'ejemplo': ('Un caso requiere Kv = 40 m³/h. Una válvula con Kv nominal 63 queda con '
                    'relación 0,63; en isoporcentual con R = 50 eso corresponde a una apertura de '
                    '1 + ln(0,63)/ln(50) ≈ 88 %. Con un Kv nominal 100 la apertura baja a ≈ 77 %.'),
        'afecta': [
            'Apertura requerida',
            'Factor FP',
            'FLP y ΔPchoked',
            'xTP y xchoked',
            'Número de Reynolds Rev',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            ('Para verificar una oferta use el Cv/Kv certificado del tamaño y tipo de internos '
             'exactos (trim reducido cambia mucho el valor).'),
            ('Si la válvula queda sobredimensionada, considere un trim de capacidad reducida antes'
             ' de cambiar el cuerpo.'),
            'No mezcle unidades: confirme si el dato está en Kv o en Cv.',
        ],
    },
    'caracteristica': {
        'que_es': ('Es la forma en que cambia la capacidad de la válvula (Kv) con la carrera, '
                   'medida a caída de presión constante. Las más comunes son isoporcentual, lineal'
                   ' y apertura rápida.'),
        'que_hace': ('Se usa para convertir la relación Kv requerido/Kv nominal en una apertura '
                     'estimada y para evaluar si la válvula controlará con ganancia razonable en '
                     'todo el rango. No repite el «Estilo de trim»: el estilo da la geometría y los factores '
                     'FL, xT, Fd y Kc, el sentido de flujo se elige en su propia fila, y la característica da '
                     'la curva de apertura y corrige el Cv nominal según la familia. En válvulas de vástago se '
                     'elige lineal, isoporcentual o apertura rápida para cualquier estilo; en rotativas la '
                     'fija el elemento de cierre.'),
        'que_indica': ('Indica cómo responderá el lazo: en isoporcentual la ganancia crece con la '
                       'apertura y compensa la caída de ΔP del sistema al subir el caudal; en '
                       'lineal la ganancia es constante si el ΔP de la válvula es casi constante.'),
        'umbrales': ('No tiene umbral numérico. Práctica habitual: isoporcentual si la válvula '
                     'toma menos de ~50 % de la pérdida del sistema a caudal máximo (autoridad '
                     'baja); lineal si toma la mayor parte (autoridad alta, ΔP casi constante); '
                     'apertura rápida solo para todo-nada.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Con R = 50 y Kv requerido = 25 % del nominal, la apertura isoporcentual es h '
                    '= 1 + ln(0,25)/ln(50) ≈ 65 %, mientras que en lineal es h = (0,25 − 0,02)/(1 '
                    '− 0,02) ≈ 23 %. El mismo caudal ubica a la válvula en puntos muy distintos de'
                    ' la carrera.'),
        'afecta': [
            'Apertura requerida',
            'Controlabilidad / ganancia instalada',
            'Rangeabilidad utilizable',
        ],
        'recomendaciones': [
            'En sistemas de bombeo con mucha fricción en la tubería elija isoporcentual.',
            ('En control de nivel con ΔP casi constante o by-pass de bomba, la lineal suele dar '
             'mejor resultado.'),
            ('Revise la apertura en el caso mínimo y máximo: deben caer en la zona útil de la '
             'curva elegida.'),
            ('Las válvulas rotativas tienen curvas propias (a menudo «isoporcentual modificada»); '
             'use la curva del fabricante si la tiene.'),
        ],
    },
    'rangeabilidad': {
        'que_es': ('Es el cociente entre el máximo y el mínimo coeficiente de caudal que la '
                   'válvula puede controlar siguiendo su característica, por ejemplo R = 50 '
                   'significa Kv máximo/Kv mínimo = 50.'),
        'que_hace': ('El programa la usa en la fórmula de la característica para estimar la '
                     'apertura y para comprobar si el caso mínimo queda dentro de lo controlable.'),
        'que_indica': ('Un R alto permite controlar caudales muy bajos sin salir de la curva. Es '
                       'una propiedad inherente; la rangeabilidad instalada suele ser menor porque'
                       ' el ΔP de la válvula cambia con el caudal.'),
        'umbrales': ('Valores típicos: globo 30-50; rotativas (bola segmentada, mariposa de alto '
                     'rendimiento) 50-100 o más. Práctica habitual: el cociente Kv requerido '
                     'máximo/Kv requerido mínimo del proceso debería ser claramente menor que R.'),
        'por_debajo': ('Con R bajo y un proceso de gran rango, el caso mínimo cae por debajo del '
                       'Kv mínimo controlable y la válvula opera cerca del asiento, con control '
                       'pobre (ciclado, desgaste).'),
        'por_encima': ('Un R mayor que el real ingresado hace que el programa estime aperturas '
                       'mínimas optimistas.'),
        'ejemplo': ('Un proceso requiere Kv = 40 a caudal máximo y Kv = 2 a mínimo (relación 20). '
                    'Una globo con R = 50 y Kv nominal 63 cubre ese rango; si el mínimo fuera Kv ='
                    ' 0,5 (relación 80), quedaría por debajo de 63/50 ≈ 1,3 y la válvula no '
                    'controlaría bien.'),
        'afecta': [
            'Apertura requerida',
            'Verificación del caso mínimo',
            'Controlabilidad',
        ],
        'recomendaciones': [
            ('Use el R declarado por el fabricante para el estilo y trim exactos, no el valor más '
             'alto del catálogo.'),
            ('Si el rango de proceso supera la rangeabilidad, considere dos válvulas en paralelo '
             '(split range) o una válvula rotativa.'),
            ('No confunda rangeabilidad inherente con rangeabilidad instalada: verifique la '
             'apertura en el caso mínimo real.'),
        ],
    },
    'C_api14e': {
        'que_es': ('Es la constante empírica de API RP 14E para calcular la velocidad erosional Ve'
                   ' = C/√ρm, con Ve en ft/s y ρm en lb/ft³. Representa cuán agresivo se admite el'
                   ' servicio.'),
        'que_hace': ('El programa la usa para calcular la velocidad erosional de referencia en la '
                     'tubería de salida y compararla con la velocidad real del fluido '
                     '(especialmente mezclas líquido-vapor).'),
        'que_indica': ('Un C más alto permite velocidades mayores antes de considerar riesgo de '
                       'erosión. No es un dato físico del fluido sino un criterio de diseño '
                       'elegido por el ingeniero.'),
        'umbrales': ('Según API RP 14E: C = 100 servicio continuo, C = 125 intermitente; 150-200 '
                     'en servicio continuo sin sólidos y con corrosión controlada o materiales '
                     'resistentes, si se justifica. La alerta aparece cuando la velocidad real '
                     'supera Ve.'),
        'por_debajo': ('Un C bajo (más conservador) da una Ve menor y puede indicar diámetros de '
                       'salida mayores de lo necesario.'),
        'por_encima': ('Un C alto sin justificación (sólidos, fluido corrosivo) subestima el '
                       'riesgo y puede llevar a erosión acelerada de la tubería de salida.'),
        'ejemplo': ('Para agua (ρ = 1000 kg/m³ = 62,4 lb/ft³) con C = 100: Ve = 100/√62,4 ≈ 12,7 '
                    'ft/s ≈ 3,9 m/s. Para una mezcla con flashing de ρm = 50 kg/m³ (3,1 lb/ft³), '
                    'Ve ≈ 57 ft/s ≈ 17 m/s.'),
        'afecta': [
            'Velocidad erosional API RP 14E',
            'Alerta de velocidad excesiva',
            'Verificación del diámetro de salida D2',
        ],
        'recomendaciones': [
            'Mantenga C = 100 salvo que tenga justificación documentada.',
            ('Si hay arena o sólidos, no use valores mayores que 100 y considere criterios de '
             'erosión específicos.'),
            ('Si la velocidad supera Ve, aumente el diámetro de salida o reduzca la fracción '
             'vaporizada aguas abajo.'),
        ],
    },
    'FF': {
        'que_es': ('Es un factor adimensional que estima qué presión tiene la vena contracta del '
                   'líquido cuando el flujo está bloqueado, como fracción de la presión de vapor '
                   'Pv.'),
        'que_hace': ('Interviene en el cálculo de la caída de presión de flujo bloqueado ΔPchoked:'
                     ' la presión mínima efectiva en la vena contracta es FF·Pv.'),
        'que_indica': ('Si FF es cercano a 0,96 el líquido está lejos de su punto crítico (Pv '
                       'pequeña frente a Pc); valores menores indican líquidos calientes cerca del'
                       ' punto crítico, donde el bloqueo ocurre antes.'),
        'umbrales': ('Por la ecuación de la norma FF varía entre 0,96 (Pv/Pc → 0) y 0,68 (Pv = '
                     'Pc). Agua a 20 °C ≈ 0,96; agua a 150 °C ≈ 0,92; GLP o hidrocarburos livianos'
                     ' calientes pueden bajar a 0,75-0,85.'),
        'por_debajo': ('Un FF bajo reduce el término FF·Pv y aumenta algo ΔPchoked; es '
                       'característico de líquidos cercanos al punto crítico, donde el cálculo es '
                       'más incierto.'),
        'por_encima': 'No aplica (el máximo es 0,96).',
        'ejemplo': ('Agua a 150 °C: Pv = 4,76 bar, Pc = 220,6 bar. FF = 0,96 − 0,28·√(4,76/220,6) '
                    '= 0,96 − 0,28·0,147 ≈ 0,92, y la presión efectiva en la vena contracta es '
                    '0,92·4,76 ≈ 4,38 bar.'),
        'afecta': [
            'ΔPchoked',
            'Detección de flujo bloqueado',
            'Cv requerido en líquidos',
        ],
        'recomendaciones': [
            'Verifique que la Pv corresponda a la temperatura de entrada real.',
            'Ingrese bien la presión crítica Pc del fluido; para mezclas use la Pc pseudocrítica.',
            ('En líquidos muy cerca del punto crítico trate el resultado con prudencia y consulte '
             'datos de ensayo.'),
        ],
    },
    'dPchoked': {
        'que_es': ('Es la caída de presión máxima que todavía aumenta el caudal. En líquidos, al '
                   'superarla la vena contracta ya está a la presión de vaporización y el caudal '
                   'no crece aunque baje P2. En gases es ΔPchoked = Fγ·xTP·P1, la caída a la que el '
                   'gas llega a velocidad sónica: es una presión, mientras que xT es la relación '
                   'ΔP/P1 (sin unidades) que la define.'),
        'que_hace': ('El programa compara el ΔP real con ΔPchoked: si ΔP ≥ ΔPchoked, usa ΔPchoked '
                     'para calcular el Cv requerido y señala flujo bloqueado (cavitación plena o '
                     'flashing).'),
        'que_indica': ('Si el ΔP real está muy por debajo de ΔPchoked, el flujo es normal; si se '
                       'acerca o lo supera, la válvula está en o cerca del bloqueo y aparecen '
                       'daños por cavitación o flashing.'),
        'umbrales': ('Condición de bloqueo: ΔP ≥ ΔPchoked. Práctica habitual: mantener ΔP por '
                     'debajo de ~70-80 % de ΔPchoked salvo que se usen internos o diseños '
                     'específicos.'),
        'por_debajo': ('Con ΔP < ΔPchoked el caudal sigue la ley cuadrática normal; si además ΔP '
                       'está cerca del inicio de cavitación pueden aparecer alertas de cavitación '
                       'incipiente.'),
        'por_encima': ('Con ΔP ≥ ΔPchoked el caudal queda limitado, hay cavitación plena o '
                       'flashing, ruido y erosión; el exceso de ΔP no aporta caudal y se disipa '
                       'aguas abajo.'),
        'ejemplo': ('Agua a 20 °C (Pv = 0,023 bar), P1 = 10 bar abs, FL = 0,9 y sin reductores: '
                    'ΔPchoked = 0,81·(10 − 0,96·0,023) ≈ 8,1 bar. Si P2 = 1 bar (ΔP = 9 bar), el '
                    'programa dimensiona con 8,1 bar y avisa de flujo bloqueado.'),
        'afecta': [
            'Cv requerido',
            'Alerta de flujo bloqueado',
            'Alerta de cavitación',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            ('Elija un estilo con FL más alto (globo ≈ 0,9 frente a mariposa ≈ 0,6) para elevar '
             'ΔPchoked.'),
            ('Reparta la caída en varias etapas (internos multietapa, orificio de contrapresión o '
             'válvulas en serie).'),
            'Ubique la válvula donde P1 sea mayor o enfríe el líquido para bajar Pv.',
            ('Si el bloqueo es inevitable por P2 < Pv (flashing), diseñe para él con materiales '
             'duros y salida amplia.'),
        ],
    },
    'FP': {
        'que_es': ('Es un factor de corrección (adimensional, ≤ 1) que tiene en cuenta los '
                   'reductores y expansiones cuando la válvula es más chica que la tubería.'),
        'que_hace': ('Divide la capacidad efectiva de la válvula: el Cv requerido se calcula como '
                     'si la válvula tuviera capacidad FP·Cv. Así el programa considera que los '
                     'reductores consumen parte de la caída de presión.'),
        'que_indica': ('FP = 1 indica que no hay reductores o que su efecto es despreciable; '
                       'cuanto menor, más capacidad se pierde en los accesorios. El efecto crece '
                       'con válvulas de alta capacidad (C/d² grande) como bola o mariposa.'),
        'umbrales': ('FP = 1 sin reductores. Práctica habitual: 0,95-1 para globo una medida menor'
                     ' que la línea; 0,85-0,95 en rotativas de alta capacidad con reductores; '
                     'valores por debajo de ~0,8 indican una diferencia de tamaños grande.'),
        'por_debajo': ('Un FP bajo aumenta el Cv requerido y puede hacer que el tamaño elegido no '
                       'alcance; señala una instalación con reductores muy marcados.'),
        'por_encima': 'No aplica (FP no puede superar 1).',
        'ejemplo': ('Una válvula de bola de 4" con Cv = 800 en línea de 6" puede tener FP ≈ 0,90. '
                    'Si el caso requiere Cv = 500 sin reductores, con ellos requiere 500/0,90 ≈ '
                    '556, y la apertura aumenta.'),
        'afecta': [
            'Cv requerido',
            'FLP y ΔPchoked',
            'xTP y xchoked',
            'Apertura requerida',
        ],
        'recomendaciones': [
            ('Ingrese D1 y D2 reales para que el programa calcule FP; no lo suponga igual a 1 si '
             'hay reductores.'),
            'Si FP es muy bajo, pruebe un tamaño de válvula mayor (más cercano a la línea).',
            'En válvulas rotativas de paso total considere instalarlas al tamaño de línea.',
        ],
    },
    'FLP': {
        'que_es': ('Es el factor de recuperación de presión del líquido para el conjunto válvula +'
                   ' reductores de entrada. Reemplaza a FL cuando la válvula se monta entre '
                   'reductores.'),
        'que_hace': ('Se usa en lugar de FL para calcular ΔPchoked y el límite de flujo bloqueado,'
                     ' y en las evaluaciones de cavitación.'),
        'que_indica': ('Un FLP alto (cercano a 1) indica poca recuperación de presión aguas abajo '
                       'de la vena contracta y, por lo tanto, mayor resistencia a la cavitación y '
                       'al bloqueo; un FLP bajo indica alta recuperación.'),
        'umbrales': ('FL típicos (sin reductores): globo 0,85-0,95; bola segmentada 0,6-0,8; '
                     'mariposa 0,55-0,7; bola de paso total 0,55-0,6. FLP sale algo menor o '
                     'similar a FL según los reductores.'),
        'por_debajo': ('Un FLP bajo reduce ΔPchoked (proporcional a FLP²) y adelanta la cavitación'
                       ' y el flujo bloqueado.'),
        'por_encima': ('Un FLP alto es favorable: retrasa el bloqueo, aunque suele ir asociado a '
                       'válvulas de menor capacidad por tamaño.'),
        'ejemplo': ('Una mariposa con FL = 0,65 en P1 = 8 bar abs de agua fría tiene ΔPchoked ≈ '
                    '0,42·8 ≈ 3,4 bar; con reductores su FLP puede bajar a 0,62 y ΔPchoked a ≈ 3,1'
                    ' bar. Una globo con FL = 0,9 llegaría a ≈ 6,5 bar.'),
        'afecta': [
            'ΔPchoked',
            'Alerta de flujo bloqueado',
            'Intensidad de cavitación',
            'Cv requerido en líquidos con bloqueo',
        ],
        'recomendaciones': [
            'En servicios de líquido con ΔP alto prefiera estilos con FL alto (globo).',
            'Use el FL del fabricante a la carrera de operación si está disponible.',
            ('Si FLP resulta mucho menor que FL, revise si conviene una válvula más cercana al '
             'tamaño de línea.'),
        ],
    },
    'x': {
        'que_es': ('Es la relación de caída de presión de un gas o vapor: x = (P1 − P2)/P1, con '
                   'presiones absolutas. Va de 0 (sin caída) a 1 (descarga al vacío).'),
        'que_hace': ('Junto con xchoked determina el factor de expansión Y, si el flujo es crítico'
                     ' (sónico) y la caída de presión efectiva para calcular el Cv requerido.'),
        'que_indica': ('Un x pequeño indica caída suave y gas casi incompresible; un x grande '
                       'indica gran expansión, alta velocidad y riesgo de flujo crítico y ruido.'),
        'umbrales': ('El umbral es xchoked = Fγ·xTP (típicamente 0,15-0,75 según el estilo). Si x '
                     '≥ xchoked el flujo está bloqueado y el programa usa xchoked en lugar de x.'),
        'por_debajo': 'Con x < xchoked el flujo es subcrítico: el caudal aumenta al bajar P2.',
        'por_encima': ('Con x ≥ xchoked el caudal no aumenta aunque baje P2, la velocidad es '
                       'sónica en la vena contracta y el ruido aerodinámico suele ser alto.'),
        'ejemplo': ('Vapor con P1 = 10 bar abs y P2 = 6 bar abs: x = 4/10 = 0,40. Con una globo de'
                    ' xT = 0,72 y Fγ = 0,94 (xchoked ≈ 0,68) el flujo es subcrítico.'),
        'afecta': [
            'Factor de expansión Y',
            'Cv requerido en gases',
            'Alerta de flujo crítico',
            'Ruido aerodinámico IEC 60534-8-3',
        ],
        'recomendaciones': [
            'Use siempre presiones absolutas.',
            ('Con x alto, verifique ruido y velocidad de salida; considere internos de baja '
             'emisión sonora o expansión a tubería mayor.'),
            'Si el proceso lo permite, reparta la caída en dos etapas para bajar x por válvula.',
        ],
    },
    'xchoked': {
        'que_es': ('Es el valor de x a partir del cual el gas alcanza velocidad sónica en la vena '
                   'contracta y el caudal ya no aumenta al bajar P2.'),
        'que_hace': ('Es el límite que usa el programa para decidir si el flujo de gas es crítico;'
                     ' cuando x ≥ xchoked, el cálculo usa x = xchoked e Y = 2/3.'),
        'que_indica': ('Cuanto mayor es xchoked, más caída de presión admite la válvula antes de '
                       'bloquear. Depende del estilo de válvula (xT), de los reductores (xTP) y '
                       'del gas (Fγ).'),
        'umbrales': ('xT típicos: globo 0,65-0,80; bola segmentada 0,3-0,5; mariposa 0,2-0,45; '
                     'bola de paso total 0,15-0,3. xchoked = Fγ·xTP.'),
        'por_debajo': ('Un xchoked bajo hace que la válvula entre en flujo crítico con caídas '
                       'moderadas; el Cv requerido es mayor y el ruido aumenta.'),
        'por_encima': ('Un xchoked alto permite más caída antes del bloqueo (favorable para '
                       'servicios de alta caída de presión).'),
        'ejemplo': ('Gas natural (γ = 1,31, Fγ = 0,94) en una globo con xTP = 0,72: xchoked ≈ '
                    '0,67. Con P1 = 40 bar abs, el flujo se vuelve crítico cuando P2 ≤ 40·(1 − '
                    '0,67) ≈ 13 bar abs.'),
        'afecta': [
            'Factor de expansión Y',
            'Cv requerido en gases',
            'Alerta de flujo crítico',
            'Ruido aerodinámico IEC 60534-8-3',
        ],
        'recomendaciones': [
            'Para caídas grandes en gas prefiera estilos de xT alto (globo).',
            ('Use el xT del fabricante para el trim exacto; los internos de baja emisión sonora '
             'tienen xT propios.'),
            ('No intente pasar más caudal bajando P2 si ya está en flujo crítico: aumente P1 o el '
             'tamaño.'),
        ],
    },
    'xTP': {
        'que_es': ('Es el factor de relación de caída de presión crítica del conjunto válvula + '
                   'reductores, el equivalente de xT cuando la válvula está entre accesorios.'),
        'que_hace': ('Reemplaza a xT para calcular xchoked y el factor de expansión Y en gases y '
                     'vapores.'),
        'que_indica': ('Indica cuánta caída relativa admite la instalación completa antes de '
                       'bloquear. Si no hay reductores, xTP = xT.'),
        'umbrales': ('Sin reductores xTP = xT (globo 0,65-0,80; rotativas 0,15-0,5). Con '
                     'reductores xTP suele diferir poco de xT, aunque en rotativas de alta '
                     'capacidad el cambio puede ser apreciable.'),
        'por_debajo': 'Un xTP menor adelanta el flujo crítico y baja Y.',
        'por_encima': 'Un xTP mayor retrasa el flujo crítico.',
        'ejemplo': ('Una globo con xT = 0,72 en línea del mismo tamaño tiene xTP = 0,72. Una bola '
                    'de 4" con xT = 0,25 entre reductores de 6" puede quedar con un xTP distinto '
                    '(por ejemplo 0,27), lo que el programa refleja en xchoked.'),
        'afecta': [
            'xchoked',
            'Factor de expansión Y',
            'Cv requerido en gases',
            'Ruido aerodinámico IEC 60534-8-3',
        ],
        'recomendaciones': [
            'Ingrese D1 y D2 reales para que el programa calcule xTP correctamente.',
            'Use el xT del fabricante para el trim y carrera de operación.',
            'Si xTP resulta bajo para la caída requerida, evalúe un estilo de xT mayor.',
        ],
    },
    'Fgamma': {
        'que_es': ('Es el cociente entre la relación de calores específicos del gas (γ = cp/cv) y '
                   'la del aire (1,40). Corrige xT, que se mide con aire, para el gas real.'),
        'que_hace': ('Multiplica a xTP para obtener xchoked e interviene en el factor de expansión'
                     ' Y.'),
        'que_indica': ('Fγ > 1 indica un gas que tolera más caída relativa antes de bloquear '
                       '(monoatómicos como helio); Fγ < 1 indica un gas que bloquea antes (vapor, '
                       'hidrocarburos pesados).'),
        'umbrales': ('Valores típicos: aire, N<sub>2</sub>, H<sub>2</sub> ≈ 1,0; vapor de agua ≈ '
                     '0,93-0,95; gas natural ≈ 0,93; CO<sub>2</sub> ≈ 0,92; propano ≈ 0,81; helio '
                     '≈ 1,19.'),
        'por_debajo': 'Un Fγ bajo reduce xchoked: el gas alcanza flujo crítico con menor caída.',
        'por_encima': 'Un Fγ alto aumenta xchoked.',
        'ejemplo': ('Para metano γ = 1,31: Fγ = 1,31/1,40 ≈ 0,94. Con xT = 0,72, xchoked = '
                    '0,94·0,72 ≈ 0,67; para aire sería 0,72.'),
        'afecta': [
            'xchoked',
            'Factor de expansión Y',
            'Cv requerido en gases',
        ],
        'recomendaciones': [
            ('Use γ a las condiciones de entrada (presión y temperatura), no a condiciones '
             'estándar si difieren mucho.'),
            'Para mezclas calcule γ con la composición; el programa lo hace si conoce el fluido.',
            'En vapor de agua use γ ≈ 1,3 (sobrecalentado) en lugar de 1,4.',
        ],
    },
    'Y': {
        'que_es': ('Es un factor adimensional que corrige el cálculo del gas por el cambio de '
                   'densidad entre la entrada y la vena contracta, ya que el gas se expande al '
                   'acelerarse.'),
        'que_hace': ('Multiplica la ecuación de caudal de gases; el programa la usa para obtener '
                     'el Cv requerido a partir de x, xchoked y las condiciones de entrada.'),
        'que_indica': ('Y = 1 significa gas casi sin expansión (caída muy pequeña); Y = 2/3 '
                       '(0,667) indica flujo crítico. Valores intermedios muestran cuánta '
                       'capacidad se pierde por la compresibilidad.'),
        'umbrales': ('Rango por norma: 0,667 ≤ Y ≤ 1. Y cerca de 0,667 indica flujo crítico (x ≥ '
                     'xchoked).'),
        'por_debajo': 'No puede quedar por debajo de 0,667: en flujo crítico se limita a 2/3.',
        'por_encima': 'No aplica (el máximo es 1, con caída nula).',
        'ejemplo': ('Con x = 0,40 y xchoked = 0,67: Y = 1 − 0,40/(3·0,67) ≈ 0,80. Es decir, la '
                    'válvula pasa alrededor de un 20 % menos de lo que daría la ecuación '
                    'incompresible sin corregir.'),
        'afecta': [
            'Cv requerido en gases',
            'Caudal máximo de la válvula en gas',
        ],
        'recomendaciones': [
            'No use la ecuación de líquidos para gases: subestimaría el Cv al ignorar Y.',
            'Si Y está en 0,667, verifique ruido y velocidad: la válvula está en flujo crítico.',
            'Revise que las presiones sean absolutas; con manométricas Y sale mal.',
        ],
    },
    'Rev': {
        'que_es': ('Es el número de Reynolds en la válvula: compara las fuerzas de inercia con las'
                   ' viscosas del fluido que pasa por ella. Es adimensional.'),
        'que_hace': ('Determina si hay que corregir el cálculo por viscosidad mediante el factor '
                     'FR; con Rev alto se usa la ecuación turbulenta normal.'),
        'que_indica': ('Rev ≥ 10 000 indica flujo turbulento (caso habitual en agua, vapor y '
                       'gases); valores menores indican flujo de transición o laminar, típico de '
                       'aceites viscosos, polímeros o caudales muy bajos.'),
        'umbrales': ('Según IEC 60534-2-1: Rev ≥ 10 000 flujo turbulento, sin corrección (FR = 1).'
                     ' Por debajo, transición; con Rev muy bajo (orden de 10 o menos) el flujo es '
                     'laminar.'),
        'por_debajo': ('Por debajo de 10 000 la viscosidad reduce la capacidad: FR < 1 y el Cv '
                       'requerido aumenta, a veces mucho.'),
        'por_encima': 'Por encima de 10 000 no hay corrección por viscosidad.',
        'ejemplo': ('Agua a 50 m³/h en una válvula de 3" da Rev del orden de '
                    '10<sup>5</sup>-10<sup>6</sup>: turbulento. Un aceite de 500 cSt al mismo '
                    'caudal da un Rev unas 500 veces menor, del orden de 1 000, y el programa aplica FR.'),
        'afecta': [
            'Factor de Reynolds FR',
            'Cv requerido',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            ('Ingrese la viscosidad a la temperatura de operación; en aceites cambia mucho con la '
             'temperatura.'),
            'Verifique también el caso de caudal mínimo, donde Rev es menor.',
            ('Si Rev es bajo, prefiera válvulas de paso amplio y revise que el tamaño no quede '
             'corto.'),
        ],
    },
    'FR': {
        'que_es': ('Es el factor de corrección por número de Reynolds: reduce la capacidad '
                   'efectiva de la válvula cuando el flujo no es plenamente turbulento.'),
        'que_hace': ('El Kv/Cv requerido se divide por FR; así el programa aumenta la capacidad '
                     'necesaria en fluidos viscosos o caudales bajos.'),
        'que_indica': ('FR = 1 indica flujo turbulento (sin efecto viscoso). Cuanto menor sea FR, '
                       'más pesa la viscosidad y más grande debe ser la válvula.'),
        'umbrales': ('0 < FR ≤ 1. FR = 1 con Rev ≥ 10 000. Práctica habitual: FR < 0,9 ya merece '
                     'revisar los datos de viscosidad y el tamaño; FR < 0,5 indica flujo muy '
                     'viscoso.'),
        'por_debajo': ('Un FR bajo aumenta mucho el Cv requerido (p. ej. FR = 0,5 duplica el Cv) y'
                       ' la válvula puede quedar chica.'),
        'por_encima': 'No aplica (el máximo es 1).',
        'ejemplo': ('Un caso de aceite requiere Cv = 40 en régimen turbulento; con Rev ≈ 2 000 el '
                    'programa obtiene FR ≈ 0,8 y el Cv requerido pasa a 40/0,8 = 50.'),
        'afecta': [
            'Cv requerido',
            'Apertura requerida',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            ('Confirme la viscosidad y su variación con la temperatura; un error en ν cambia mucho'
             ' FR.'),
            ('Si el fluido puede calentarse, dimensione con el caso de mayor viscosidad (más '
             'frío).'),
            ('Considere calefaccionar la línea (tracing) si el proceso lo permite, para bajar la '
             'viscosidad.'),
        ],
    },
    'xF': {
        'que_es': ('Es la relación diferencial de presión del líquido: xF = ΔP/(P1 − Pv). Compara '
                   'la caída de presión real con la máxima caída que podría tener antes de '
                   'vaporizarse.'),
        'que_hace': ('Es la variable con la que IEC 60534-8-4 evalúa la cavitación y el ruido '
                     'hidrodinámico: se compara con xFz (inicio de cavitación) y con FL² '
                     '(cavitación plena / bloqueo).'),
        'que_indica': ('Un xF pequeño indica que el líquido está lejos de cavitar; a medida que se'
                       ' acerca a xFz empieza la cavitación incipiente y al llegar a FL² hay '
                       'cavitación plena.'),
        'umbrales': ('Sin cavitación: xF < xFzp1 (xFz corregido por la presión P1; xFz típico '
                     '0,15-0,5 para internos simples y mayor para internos anticavitación). '
                     'Cavitación plena: xF ≥ FL² (≈ 0,81 para FL = 0,9).'),
        'por_debajo': ('Por debajo de xFzp1 no hay cavitación y el ruido es de flujo turbulento '
                       'normal.'),
        'por_encima': ('Por encima de xFzp1 hay cavitación creciente; por encima de FL² el flujo '
                       'está bloqueado y el daño puede ser severo.'),
        'ejemplo': ('Agua a 80 °C (Pv = 0,47 bar), P1 = 8 bar abs, P2 = 3 bar abs: xF = 5/(8 − '
                    '0,47) ≈ 0,66. Con xFz ≈ 0,4 y FL² = 0,81 la válvula está cavitando sin llegar'
                    ' al bloqueo.'),
        'afecta': [
            'Alerta de cavitación',
            'Intensidad de cavitación',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Índice σ',
        ],
        'recomendaciones': [
            'Reduzca ΔP por válvula repartiéndolo en etapas o con orificio de contrapresión.',
            ('Aumente P1 (ubicar la válvula más baja o cerca de la bomba) o baje la temperatura '
             'para reducir Pv.'),
            'Use internos anticavitación con xFz alto si la cavitación es inevitable.',
        ],
    },
    'sigma': {
        'que_es': ('Es el índice de cavitación σ = (P1 − Pv)/(P1 − P2), el inverso de xF. Mide '
                   'cuánta «reserva» de presión tiene el líquido frente a la caída de presión de '
                   'la válvula.'),
        'que_hace': ('Se usa para comparar el servicio con los niveles de cavitación del método '
                     'ISA-RP75.23 (σi, σc, σmv, σch), normalmente obtenidos por ensayo del '
                     'fabricante.'),
        'que_indica': ('Cuanto mayor es σ, menos riesgo de cavitación; cuanto menor, más intensa. '
                       'Al llegar a σch ≈ 1/FL² hay flujo bloqueado.'),
        'umbrales': ('Orden de magnitud: σch = 1/FL² (≈ 1,23 para FL = 0,9). Práctica habitual, '
                     'solo orientativa: σ > 2-3 suele ser seguro para internos estándar; el umbral'
                     ' real de cada válvula se define con sus datos de ensayo (σi, σmv).'),
        'por_debajo': ('Por debajo de σi comienza la cavitación; por debajo de σmv aparecen '
                       'vibración y daño importantes; por debajo de σch hay bloqueo.'),
        'por_encima': 'Por encima de σi no se espera cavitación.',
        'ejemplo': ('Con P1 = 8 bar abs, P2 = 3 bar abs y Pv = 0,47 bar: σ = 7,53/5 ≈ 1,5. Para '
                    'una globo con FL = 0,9 (σch ≈ 1,23) está cerca del bloqueo y conviene un trim'
                    ' anticavitación.'),
        'afecta': [
            'Alerta de cavitación',
            'Comparación con niveles ISA-RP75.23',
            'Selección de internos',
        ],
        'recomendaciones': [
            ('Pida al fabricante los valores σ de ensayo del trim propuesto y compárelos con el σ '
             'calculado.'),
            ('Recuerde que los niveles σ escalan con tamaño y presión; ISA-RP75.23 da '
             'correcciones.'),
            'Para subir σ: aumente P1, baje Pv (enfriar) o reduzca la caída por etapa.',
        ],
    },
    'apertura': {
        'que_es': ('Es la posición estimada del obturador para cada caso, de 0 % (cerrada) a 100 %'
                   ' (totalmente abierta).'),
        'que_hace': ('Permite verificar que la válvula elegida controla bien en todos los casos y '
                     'es la base del criterio de selección automática del tamaño.'),
        'que_indica': ('Una apertura en la zona media indica buen tamaño. Muy alta: la válvula '
                       'queda chica; muy baja: sobredimensionada. Es una estimación con la '
                       'característica inherente y FL y xT a carrera nominal.'),
        'umbrales': ('Criterios orientativos (práctica habitual): isoporcentual 15-85 %; lineal '
                     '10-80 %. El programa elige el tamaño con apertura ≤ 85 % en el caso máximo.'),
        'por_debajo': ('Por debajo de ~10 % la válvula trabaja cerca del asiento: control '
                       'inestable, mala resolución y erosión del asiento por alta velocidad.'),
        'por_encima': ('Por encima de ~90 % no queda margen para perturbaciones y el caudal máximo'
                       ' puede no alcanzarse.'),
        'ejemplo': ('Isoporcentual R = 50, Kv nominal 100: un caso con Kv requerido 70 da 1 + '
                    'ln(0,7)/ln(50) ≈ 91 % (chica), y uno con Kv 5 da ≈ 23 %. Con Kv nominal 160 '
                    'las aperturas pasan a ≈ 79 % y ≈ 11 %.'),
        'afecta': [
            'Selección del tamaño de válvula',
            'Alerta de válvula sobredimensionada o subdimensionada',
            'Controlabilidad',
        ],
        'recomendaciones': [
            ('Si la apertura máxima es alta, pruebe el tamaño siguiente o revise la caída de '
             'presión asignada a la válvula.'),
            ('Si la apertura mínima es baja, use un trim reducido o una válvula más chica, o dos '
             'válvulas en split range.'),
            ('Revise la característica: cambiar de lineal a isoporcentual desplaza mucho las '
             'aperturas.'),
        ],
    },
    'memoria': {
        'que_es': ('Es el reporte detallado que muestra, en orden, todos los valores intermedios '
                   'del cálculo de cada caso, con la fórmula usada y la cláusula de la norma.'),
        'que_hace': ('Sirve para revisar, auditar y documentar el dimensionamiento; permite que '
                     'otro ingeniero repita el cálculo a mano y lo apruebe.'),
        'que_indica': ('No es un valor numérico: indica la trazabilidad del resultado. Si un '
                       'número final parece raro, la memoria permite encontrar en qué paso se '
                       'origina.'),
        'umbrales': ('No tiene umbrales. Buena práctica: adjuntarla a la hoja de datos de la '
                     'válvula y revisar que unidades, presiones absolutas y propiedades del fluido'
                     ' sean las correctas.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Si un caso de agua resulta con Cv inesperadamente bajo, la memoria muestra '
                    'que se usó ΔPchoked = 8,1 bar en lugar del ΔP de 9 bar: el caso está en flujo'
                    ' bloqueado y el resultado es correcto.'),
        'afecta': [
            'Documentación del proyecto',
            'Revisión de Cv requerido y factores intermedios',
        ],
        'recomendaciones': [
            ('Verifique primero los datos de entrada (P1, P2, T, densidad, Pv) antes que los '
             'resultados.'),
            ('Siga la secuencia FP → FLP/xTP → ΔPchoked/xchoked → Y → Rev/FR → Cv para entender '
             'cada resultado.'),
            'Archive la memoria junto con la revisión de la hoja de datos.',
        ],
    },
    'cavitacion': {
        'que_es': ('Es la formación de burbujas de vapor en la vena contracta, donde la presión '
                   'cae por debajo de Pv, y su colapso violento aguas abajo cuando la presión se '
                   'recupera por encima de Pv.'),
        'que_hace': ('El programa la detecta comparando xF con xFzp1 y FL² y clasifica la '
                     'intensidad, para alertar sobre daño, ruido y necesidad de internos '
                     'especiales.'),
        'que_indica': ('Indica que la válvula sufrirá erosión, ruido (como grava) y vibración, con'
                       ' mayor gravedad cuanto mayor es la intensidad y la presión de colapso (P2 '
                       '− Pv).'),
        'umbrales': ('La alerta se dispara con xF ≥ xFzp1 y P2 > Pv. Intensidad del programa: 0-33'
                     ' % leve, 33-66 % moderada, > 66 % severa; con xF ≥ FL² cavitación plena y '
                     'flujo bloqueado.'),
        'por_debajo': 'Por debajo de xFzp1 no hay cavitación.',
        'por_encima': ('Por encima la intensidad crece hasta FL², donde hay cavitación plena y '
                       'caudal limitado. Si P2 ≤ Pv deja de ser cavitación y pasa a ser flashing.'),
        'ejemplo': ('Agua a 80 °C, P1 = 8 bar abs, P2 = 3 bar abs: xF ≈ 0,66 con xFzp1 ≈ 0,40 y '
                    'FL² = 0,81. La intensidad es (0,66 − 0,40)/(0,81 − 0,40) ≈ 63 %, moderada '
                    'cerca de severa: conviene un trim anticavitación.'),
        'afecta': [
            'Alerta de cavitación',
            'Ruido hidrodinámico IEC 60534-8-4',
            'ΔPchoked y Cv requerido',
            'Selección de internos y materiales',
        ],
        'recomendaciones': [
            'Leve: internos endurecidos (estelita) y estilo con FL alto suelen bastar.',
            'Moderada o severa: internos anticavitación multiorificio o multietapa.',
            'Reparta la caída con orificio de contrapresión o válvulas en serie.',
            'Reubique la válvula a un punto de mayor presión o enfríe el líquido para bajar Pv.',
        ],
    },
    'cavitacion_proxima': {
        'que_es': ('Es un aviso preventivo: el servicio todavía no cavita, pero xF está a menos '
                   'del 20 % del inicio de cavitación xFzp1.'),
        'que_hace': ('Advierte que pequeños cambios de operación pueden llevar la válvula a '
                     'cavitar, para que el ingeniero lo considere antes de elegir internos '
                     'estándar.'),
        'que_indica': ('Indica poco margen: un aumento de temperatura (mayor Pv), una baja de P1 o'
                       ' de P2, o un caso de operación no previsto puede iniciar la cavitación.'),
        'umbrales': 'Se dispara cuando 0,8·xFzp1 ≤ xF < xFzp1.',
        'por_debajo': 'Por debajo de 0,8·xFzp1 hay margen suficiente y no se emite aviso.',
        'por_encima': 'Al llegar a xFzp1 el aviso pasa a la alerta de cavitación.',
        'ejemplo': ('Con xFzp1 = 0,40 y xF = 0,35 el servicio está 12,5 % por debajo del inicio. '
                    'Si la temperatura del agua sube de 80 °C a 100 °C, Pv pasa de 0,47 a 1,01 bar'
                    ' y xF aumenta, pudiendo superar 0,40.'),
        'afecta': [
            'Alerta de cavitación',
            'Selección de internos',
        ],
        'recomendaciones': [
            'Revise los casos extremos de operación (arranque, temperatura máxima, P2 mínima).',
            'Considere internos endurecidos como medida preventiva de bajo costo.',
            'Si el servicio es continuo y crítico, evalúe un trim con xFz más alto.',
        ],
    },
    'flashing': {
        'que_es': ('Es la vaporización parcial del líquido que ocurre cuando la presión de salida '
                   'P2 es igual o menor que la presión de vapor Pv: el vapor formado no vuelve a '
                   'condensar aguas abajo.'),
        'que_hace': ('El programa lo detecta, trata el caso como flujo bloqueado y estima la '
                     'fracción vaporizada con un balance de entalpía para evaluar velocidad y '
                     'erosión aguas abajo.'),
        'que_indica': ('Indica que aguas abajo circula una mezcla bifásica de alta velocidad que '
                       'erosiona con aspecto liso y pulido; la intensidad crece con la fracción '
                       'vaporizada.'),
        'umbrales': ('La alerta se dispara con P2 ≤ Pv. Práctica habitual: limitar la velocidad de'
                     ' la mezcla a la salida (ver API RP 14E) y considerar severa una fracción '
                     'vaporizada de varios por ciento en masa.'),
        'por_debajo': 'Con P2 > Pv no hay flashing (puede haber cavitación).',
        'por_encima': ('Cuanto más baja P2 respecto de Pv, mayor la fracción vaporizada, la '
                       'velocidad y el daño.'),
        'ejemplo': ('Agua a 150 °C (Pv = 4,76 bar abs) descargando a un tanque a 2 bar abs: P2 < '
                    'Pv, hay flashing. Por balance de entalpía vaporiza alrededor del 6 % de la '
                    'masa y la densidad de la mezcla cae a unos 19 kg/m³, por lo que la velocidad '
                    'a la salida aumenta mucho.'),
        'afecta': [
            'Alerta de flashing',
            'ΔPchoked y Cv requerido',
            'Velocidad de salida y API RP 14E',
            'Selección de materiales y estilo de válvula',
        ],
        'recomendaciones': [
            ('Use válvula angular flujo-cierra descargando a recipiente o a tubería de mayor '
             'diámetro.'),
            ('Elija materiales duros (Cr-Mo, estelita, carburo de tungsteno) para internos y '
             'cuerpo.'),
            'Agrande el diámetro de salida para bajar la velocidad de la mezcla.',
            ('Si es posible, evítelo elevando P2 o subenfriando el líquido; los internos '
             'anticavitación no lo resuelven.'),
        ],
    },
    'gas_bloqueado': {
        'que_es': ('Es el régimen en el que el gas llega a la velocidad del sonido (Mach 1) en la '
                   'vena contracta, la sección más estrecha del chorro dentro de la válvula. A '
                   'partir de ahí el caudal ya no crece aunque baje la presión de salida.'),
        'que_hace': ('Le dice al cálculo que debe limitar la relación de caídas de presión x al '
                     'valor x<sub>choked</sub> = F<sub>γ</sub>·x<sub>T</sub> y usar Y = 0,667 para'
                     ' obtener el Cv. Usar la caída real en lugar de la límite daría un Cv '
                     'demasiado chico.'),
        'que_indica': ('Si la alerta aparece, toda la caída de presión adicional por encima del '
                       'límite se disipa fuera de la vena contracta (ondas de choque, expansión en'
                       ' la tubería) y no aporta caudal. Es una condición de alta energía '
                       'acústica, no un error de cálculo.'),
        'umbrales': ('La alerta se dispara cuando x = ΔP/P<sub>1</sub> ≥ '
                     'F<sub>γ</sub>·x<sub>T</sub>, con F<sub>γ</sub> = γ/1,40. Valores típicos de '
                     'x<sub>T</sub>: globo 0,65-0,75; bola segmentada 0,25-0,55; mariposa '
                     '0,20-0,45. Como guía rápida, con aire (F<sub>γ</sub> = 1) y una válvula '
                     'globo el bloqueo empieza hacia ΔP ≈ 0,7·P<sub>1</sub>.'),
        'por_debajo': ('Por debajo del límite el flujo es subsónico: el caudal depende de la caída'
                       ' de presión y Y varía entre 1 y 0,667 según la ecuación de la norma.'),
        'por_encima': ('Por encima del límite el caudal queda fijado por P<sub>1</sub> y '
                       'x<sub>choked</sub>; el exceso de caída genera ruido aerodinámico '
                       '(regímenes III a V) y vibración.'),
        'ejemplo': ('Aire a P<sub>1</sub> = 10 bar abs y P<sub>2</sub> = 2 bar abs en una válvula '
                    'globo con x<sub>T</sub> = 0,72: x = 8/10 = 0,80, mayor que x<sub>choked</sub>'
                    ' = 1,0·0,72 = 0,72. El flujo está bloqueado y el programa dimensiona con x = '
                    '0,72 e Y = 0,667. Bajar P<sub>2</sub> a 1 bar abs no aumentaría el caudal.'),
        'afecta': [
            'Cv requerido',
            'Factor de expansión Y',
            'Ruido aerodinámico IEC 60534-8-3',
            'Mach a la salida de la válvula',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            'Verifique siempre el nivel de ruido y el Mach de salida cuando aparezca esta alerta.',
            ('Si el ruido es alto, use internos de bajo ruido o multietapa, que reparten la caída '
             'en varias restricciones.'),
            ('Considere repartir la caída de presión entre la válvula y un restrictor o placa '
             'aguas abajo (práctica habitual).'),
            ('Use el x<sub>T</sub> certificado del fabricante para el estilo y tamaño reales; el '
             'típico puede adelantar o atrasar el bloqueo.'),
        ],
    },
    'mach_salida': {
        'que_es': ('El número de Mach es la velocidad del gas dividida por la velocidad del sonido'
                   ' en ese gas. Aquí se evalúa en la conexión de salida de la válvula.'),
        'que_hace': ('Se usa para verificar que el gas no salga demasiado rápido de la válvula, ya'
                     ' que la velocidad de salida es una fuente importante de ruido y vibración; '
                     'IEC 60534-8-3 la usa también en el cálculo del ruido.'),
        'que_indica': ('Un Mach cercano a 0 indica salida tranquila; a medida que se acerca a 1 el'
                       ' chorro se vuelve muy ruidoso y la energía cinética que recibe la tubería '
                       'crece con el cuadrado de la velocidad.'),
        'umbrales': ('Práctica habitual: Mach ≤ 0,3 en servicios de bajo ruido y Mach ≤ 0,5 como '
                     'límite general. Referencia: el sonido en aire a 20 °C viaja a unos 343 m/s, '
                     'así que Mach 0,3 ≈ 103 m/s (338 ft/s).'),
        'por_debajo': ('Por debajo de 0,3 la velocidad de salida no suele ser el problema '
                       'dominante; si hay ruido alto, su origen está en la caída de presión dentro'
                       ' de la válvula.'),
        'por_encima': ('Por encima de 0,5 aumentan el ruido, la vibración y el riesgo de fatiga en'
                       ' la tubería, soportes e instrumentos cercanos; cerca de 1 la salida se '
                       'vuelve sónica.'),
        'ejemplo': ('Gas natural sale de una válvula DN100 a 5 bar abs: con la densidad de salida '
                    'resulta v = 180 m/s y c = 420 m/s, es decir Mach ≈ 0,43. Está bajo 0,5 pero '
                    'sobre 0,3; para un servicio de bajo ruido conviene pasar a DN150, con lo que '
                    'la velocidad cae a unos 80 m/s (Mach ≈ 0,19).'),
        'afecta': [
            'Ruido aerodinámico IEC 60534-8-3',
            'Velocidad de salida',
            'Selección del tamaño de válvula',
            'Alerta de flujo sónico en la salida',
        ],
        'recomendaciones': [
            'Elija un diámetro de válvula mayor o una válvula con conexión de salida expandida.',
            'Aumente el diámetro de la tubería aguas abajo con un expansor cerca de la válvula.',
            ('Reparta la caída de presión en etapas (internos multietapa o restrictor aguas abajo)'
             ' para que P<sub>2</sub> local sea mayor y el gas tenga menor volumen específico.'),
            'Revise que el área de salida ingresada tenga la unidad correcta.',
        ],
    },
    'salida_sonica': {
        'que_es': ('Es la situación en que el gas, con la presión P<sub>2</sub> y el área de '
                   'salida disponibles, necesitaría ir más rápido que el sonido para pasar; como '
                   'eso no es posible, la salida de la válvula se bloquea a Mach 1.'),
        'que_hace': ('Le avisa que la conexión de salida es demasiado chica para ese caudal: el '
                     'programa informa Mach 1 y v = c, y calcula el área mínima para que la salida'
                     ' sea subsónica.'),
        'que_indica': ('Indica que la presión real en la brida de salida es mayor que '
                       'P<sub>2</sub> y que el gas termina de expandirse dentro de la tubería, con'
                       ' ruido y vibración intensos. Es una señal de diseño inadecuado de la '
                       'salida.'),
        'umbrales': ('La alerta se dispara cuando la velocidad calculada en la salida alcanza o '
                     'supera la velocidad del sonido (Mach ≥ 1). Como objetivo de diseño se busca '
                     'Mach ≤ 0,5 y, en servicios de bajo ruido, ≤ 0,3 (práctica habitual).'),
        'por_debajo': ('Por debajo de Mach 1 la salida es subsónica y no aplica esta alerta, '
                       'aunque puede seguir activa la de Mach alto.'),
        'por_encima': ('En Mach 1 no se puede pasar más caudal por esa área: aparecen ondas de '
                       'choque en la salida y el nivel de ruido puede superar fácilmente 110 '
                       'dB(A), con riesgo de daño por vibración.'),
        'ejemplo': ('Vapor que sale a 1,5 bar abs por una salida DN50 requeriría 600 m/s, pero la '
                    'velocidad del sonido en ese vapor es unos 480 m/s. El programa informa Mach 1'
                    ' y un área mínima de, por ejemplo, 2 500 mm²; una salida DN80 (unos 4 800 '
                    'mm²) ya sería subsónica.'),
        'afecta': [
            'Mach a la salida de la válvula',
            'Velocidad de salida',
            'Ruido aerodinámico IEC 60534-8-3',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            'Verifique primero la unidad del área de salida si la ingresó a mano.',
            ('Aumente el diámetro de la válvula o use una válvula con salida expandida, al menos '
             'hasta el área mínima que informa el programa.'),
            ('Reparta la caída de presión en varias etapas para elevar la presión de salida de '
             'cada etapa.'),
            'Instale un expansor y tubería de mayor diámetro inmediatamente aguas abajo.',
        ],
    },
    'area_salida_rango': {
        'que_es': ('Es una alerta de coherencia: el área de salida ingresada es muy distinta del '
                   'área que corresponde al diámetro nominal de la válvula.'),
        'que_hace': ('Protege el cálculo de la velocidad y del Mach de salida, que dependen '
                     'directamente del área; un error de unidad cambia esos resultados por un '
                     'factor grande.'),
        'que_indica': ('Una relación área ingresada / área nominal cercana a 1 es lo normal; '
                       'valores muy lejanos casi siempre son un error de unidad o de diámetro.'),
        'umbrales': ('La alerta se dispara si el área ingresada es menor que 0,2 o mayor que 1,6 '
                     'veces el área del diámetro nominal. Recuerde que 1 in² = 645,16 mm².'),
        'por_debajo': ('Por debajo de 0,2 la velocidad y el Mach de salida salen exagerados, y '
                       'pueden aparecer falsas alertas de salida sónica y ruido.'),
        'por_encima': ('Por encima de 1,6 la velocidad y el Mach se subestiman y el ruido '
                       'calculado puede resultar optimista.'),
        'ejemplo': ('Una válvula DN100 (4") tiene un área nominal de π·100²/4 ≈ 7 854 mm². Si se '
                    'ingresa 12,7 con la unidad mm² cuando el dato era 12,7 in² (unos 8 190 mm²), '
                    'la relación es 0,0016 y la velocidad calculada sería unas 600 veces mayor. '
                    'Corrigiendo la unidad, la relación pasa a 1,04.'),
        'afecta': [
            'Velocidad de salida',
            'Mach a la salida de la válvula',
            'Ruido aerodinámico IEC 60534-8-3',
            'Alerta de flujo sónico en la salida',
        ],
        'recomendaciones': [
            'Revise la unidad seleccionada (mm², cm², in²) y el valor ingresado.',
            ('Si no tiene el dato del fabricante, deje el campo vacío para que el programa use el '
             'área del diámetro nominal.'),
            'Compruebe que el diámetro nominal seleccionado coincida con el de la válvula real.',
        ],
    },
    'velocidad_liquido': {
        'que_es': ('Es la velocidad media del líquido en la conexión de salida de la válvula, '
                   'calculada con el caudal y el área de salida.'),
        'que_hace': ('Sirve para verificar que el tamaño elegido no provoque erosión, vibración ni'
                     ' golpe de ariete al cerrar la válvula.'),
        'que_indica': ('A mayor velocidad, mayor energía cinética: más desgaste de internos y '
                       'cuerpo, más ruido y mayores sobrepresiones en un cierre rápido.'),
        'umbrales': ('Práctica habitual: hasta unos 9 m/s (30 ft/s) en la conexión de la válvula '
                     'para líquidos limpios; valores menores, del orden de 3-5 m/s, con sólidos en'
                     ' suspensión, flashing o cavitación. En la tubería suele buscarse 1-3 m/s.'),
        'por_debajo': ('Velocidades bajas no causan problemas de erosión; sólo en servicios con '
                       'sólidos una velocidad muy baja puede favorecer la sedimentación.'),
        'por_encima': ('Por encima del límite aumentan la erosión, la vibración y el riesgo de '
                       'golpe de ariete, y se acorta la vida de asiento y obturador.'),
        'ejemplo': ('Agua a 150 m³/h por una salida DN80 (área ≈ 0,00503 m²): v = '
                    '(150/3600)/0,00503 ≈ 8,3 m/s, justo bajo el límite de 9 m/s. Con DN100 '
                    '(0,00785 m²) baja a 5,3 m/s, más adecuado si el agua lleva arena.'),
        'afecta': [
            'Velocidad de salida',
            'Selección del tamaño de válvula',
            'Alerta de erosión',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            'Elija un diámetro de válvula mayor o una conexión de salida más grande.',
            ('Con sólidos o flashing, use materiales endurecidos (por ejemplo, recubrimientos de '
             'estelita o carburo de tungsteno) y estilos de paso recto.'),
            'Limite la velocidad de cierre del actuador para reducir el golpe de ariete.',
            'Evite reducciones bruscas inmediatamente aguas abajo de la válvula.',
        ],
    },
    'erosional_api14e': {
        'que_es': ('Es la velocidad máxima recomendada por API RP 14E para evitar erosión excesiva'
                   ' en tuberías con flujo bifásico o con partículas: V<sub>e</sub> = '
                   'C/√ρ<sub>m</sub>, con V<sub>e</sub> en ft/s y ρ<sub>m</sub> en lb/ft³.'),
        'que_hace': ('El programa la compara con la velocidad de la mezcla a la salida de la '
                     'válvula, calculada con la densidad homogénea de la mezcla.'),
        'que_indica': ('Si la velocidad real supera V<sub>e</sub>, la pérdida de espesor en codos,'
                       ' tes y reducciones aguas abajo será acelerada.'),
        'umbrales': ('API RP 14E indica C = 100 para servicio continuo y C = 125 para servicio '
                     'intermitente en fluidos sin sólidos; admite valores de 150 a 200 en servicio'
                     ' continuo sin sólidos cuando la corrosión está controlada o se usan '
                     'materiales resistentes. Con arena se requiere un estudio específico y '
                     'valores menores.'),
        'por_debajo': ('Por debajo de V<sub>e</sub> la erosión por velocidad se considera '
                       'aceptable según la práctica de la RP.'),
        'por_encima': ('Por encima de V<sub>e</sub> se esperan desgaste rápido, fugas y posibles '
                       'fallas en accesorios aguas abajo de la válvula.'),
        'ejemplo': ('Mezcla de crudo y gas con ρ<sub>m</sub> = 160 kg/m³ (10 lb/ft³) y C = 100: '
                    'V<sub>e</sub> = 100/√10 ≈ 31,6 ft/s (9,6 m/s). Si la mezcla sale de la '
                    'válvula a 14 m/s, supera el límite y conviene aumentar la salida hasta que la'
                    ' velocidad quede bajo 9,6 m/s.'),
        'afecta': [
            'Alerta de erosión',
            'Velocidad de salida',
            'Selección del tamaño de válvula',
            'Dimensionamiento bifásico',
        ],
        'recomendaciones': [
            'Aumente el diámetro de salida de la válvula y de la tubería aguas abajo.',
            'Use materiales resistentes a la erosión en internos y en el primer tramo de tubería.',
            ('Evite codos cercanos a la salida; si los hay, use radio largo o tes ciegas (práctica'
             ' habitual).'),
            ('Si hay arena, aplique un criterio de erosión específico y considere desarenadores '
             'aguas arriba.'),
        ],
    },
    'flujo_no_turbulento': {
        'que_es': ('Es el flujo en el que la viscosidad del fluido pesa mucho frente a su inercia,'
                   ' típicamente con líquidos muy viscosos o caudales muy pequeños. Se mide con el'
                   ' número de Reynolds de la válvula Re<sub>v</sub>.'),
        'que_hace': ('Cuando Re<sub>v</sub> < 10 000 el programa aplica el factor de número de '
                     'Reynolds F<sub>R</sub> de IEC 60534-2-1, que aumenta el Cv requerido.'),
        'que_indica': ('Indica que la válvula pasará menos caudal del que predicen las ecuaciones '
                       'turbulentas; cuanto menor es F<sub>R</sub>, mayor es la corrección.'),
        'umbrales': ('La alerta se dispara con Re<sub>v</sub> < 10 000 (límite de la norma para '
                     'flujo turbulento). Con Re<sub>v</sub> cercano a 10 000, F<sub>R</sub> ≈ 1; '
                     'en flujo laminar profundo (Re<sub>v</sub> del orden de 10 o menos) '
                     'F<sub>R</sub> puede bajar mucho, a 0,1 o menos.'),
        'por_debajo': ('Cuanto más bajo es Re<sub>v</sub>, menor es F<sub>R</sub> y mayor la '
                       'válvula necesaria; un error en la viscosidad se traduce directamente en '
                       'error de capacidad.'),
        'por_encima': ('Con Re<sub>v</sub> ≥ 10 000 el flujo es turbulento, F<sub>R</sub> = 1 y no'
                       ' se corrige.'),
        'ejemplo': ('Un aceite de 500 cSt a 5 m³/h en una válvula DN25 da Re<sub>v</sub> ≈ 1 500 y'
                    ' F<sub>R</sub> ≈ 0,7. El Cv requerido sube de 2,0 (turbulento) a unos 2,9, lo'
                    ' que puede obligar a cambiar el trim o el tamaño.'),
        'afecta': [
            'Factor F<sub>R</sub>',
            'Cv requerido',
            'Apertura calculada',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            ('Use la viscosidad a la temperatura mínima de operación, que suele ser el caso más '
             'exigente.'),
            'Verifique la unidad de viscosidad (cP es dinámica; cSt es cinemática).',
            ('Considere calefacción o aislamiento de la línea si la viscosidad cambia mucho con la'
             ' temperatura.'),
            'Evite válvulas muy sobredimensionadas: aperturas bajas reducen aún más el Reynolds.',
        ],
    },
    'subdimensionada': {
        'que_es': ('Es la condición en que el Cv requerido supera el Cv nominal de la válvula: ni '
                   'totalmente abierta puede pasar el caudal pedido.'),
        'que_hace': ('Detiene una selección que no cumple el proceso y obliga a elegir un tamaño o'
                     ' estilo de mayor capacidad.'),
        'que_indica': ('Indica que la apertura calculada sería mayor que 100 %: el caudal máximo '
                       'del caso no se alcanzará con las presiones dadas.'),
        'umbrales': ('La alerta se dispara cuando Cv requerido > Cv nominal (apertura > 100 %). '
                     'Práctica habitual: que el caudal máximo quede en 80-90 % de apertura.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Con la válvula al 100 % el caudal será menor que el requerido, o la caída '
                       'de presión real deberá ser mayor que la prevista.'),
        'ejemplo': ('Se requiere Cv = 62 y la válvula DN50 elegida tiene Cv nominal 48: la '
                    'apertura sería 129 %. Una válvula DN80 con Cv 110 quedaría al 56 % para ese '
                    'mismo caudal, un punto cómodo.'),
        'afecta': [
            'Apertura calculada',
            'Selección del tamaño de válvula',
            'Cv requerido frente a Cv nominal',
        ],
        'recomendaciones': [
            ('Elija el siguiente diámetro o un estilo con mayor Cv por diámetro (por ejemplo, de '
             'globo reducido a globo de paso total).'),
            'Revise los datos del caso máximo: caudal, P<sub>1</sub> y P<sub>2</sub>.',
            'Revise si se puede asignar más caída de presión a la válvula.',
            'Cargue el Cv certificado si estaba usando un valor típico.',
        ],
    },
    'apertura_alta': {
        'que_es': ('Es la alerta que aparece cuando, para el caudal del caso, la válvula debe '
                   'trabajar casi totalmente abierta.'),
        'que_hace': ('Avisa que la válvula tiene poco margen de capacidad para absorber aumentos '
                     'de caudal o perturbaciones del proceso.'),
        'que_indica': ('Una apertura alta indica que la válvula está justa; además, cerca del tope'
                       ' la ganancia (cambio de caudal por cada % de carrera) suele ser baja y el '
                       'lazo responde peor.'),
        'umbrales': ('La alerta se dispara con aperturas mayores que 90 %. Práctica habitual: '
                     'caudal máximo entre 70 y 90 % y caudal normal entre 50 y 80 % de apertura.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Por encima de 90 % no hay margen para perturbaciones ni para errores en '
                       'los datos, y el controlador puede saturar la salida.'),
        'ejemplo': ('Con Cv requerido 46 y Cv nominal 50, la apertura es 92 %. Si el caudal sube '
                    '10 %, la válvula ya no alcanza. Con un trim de Cv 70, la apertura baja a unos'
                    ' 66 %.'),
        'afecta': [
            'Apertura calculada',
            'Selección del tamaño de válvula',
            'Margen de capacidad',
        ],
        'recomendaciones': [
            'Elija un tamaño mayor o un trim de mayor capacidad.',
            'Verifique que el caudal máximo y las presiones del caso sean realistas.',
            ('Considere una característica de igual porcentaje si la caída de presión disponible '
             'varía mucho con el caudal.'),
        ],
    },
    'apertura_baja': {
        'que_es': ('Es la alerta que aparece cuando la válvula trabaja casi cerrada para el caudal'
                   ' del caso, lo que indica que es demasiado grande.'),
        'que_hace': ('Avisa que el control será difícil y el desgaste mayor, porque el obturador '
                     'trabaja muy cerca del asiento.'),
        'que_indica': ('Una apertura baja indica sobredimensionamiento: un pequeño movimiento del '
                       'vástago produce un cambio grande de caudal y la fricción de la '
                       'empaquetadura domina el movimiento.'),
        'umbrales': ('La alerta se dispara con aperturas menores que 10 %. Práctica habitual: '
                     'caudal mínimo por encima de 10-20 % de apertura.'),
        'por_debajo': ('Por debajo de 10 % el control es inestable (oscilaciones), el desgaste por'
                       ' alta velocidad en el asiento es mayor y pueden aparecer golpeteo y '
                       'vibración.'),
        'por_encima': 'No aplica.',
        'ejemplo': ('Con Cv requerido 4 y una válvula de Cv 100, la apertura es 4 %. Un trim '
                    'reducido de Cv 25 la llevaría al 16 % y una válvula de Cv 12 al 33 %, con un '
                    'control mucho más estable.'),
        'afecta': [
            'Apertura calculada',
            'Selección del tamaño de válvula',
            'Rangeabilidad',
        ],
        'recomendaciones': [
            'Elija un tamaño menor o un trim reducido en el mismo cuerpo.',
            ('Use característica de igual porcentaje para mejorar la controlabilidad a bajos '
             'caudales.'),
            ('Si el rango de caudales es muy amplio, considere dos válvulas en paralelo (split '
             'range).'),
            'Revise si los caudales de diseño incluyen márgenes excesivos.',
        ],
    },
    'kv_tipico': {
        'que_es': ('Es un aviso de que la capacidad nominal (Kv o Cv a apertura total) usada para '
                   'calcular la apertura es un valor típico del estilo genérico, no el dato '
                   'certificado de un producto.'),
        'que_hace': ('Permite estimar la apertura y elegir el tamaño en etapas tempranas sin datos'
                     ' de fabricante.'),
        'que_indica': ('La apertura calculada es aproximada; con la válvula real puede ser algo '
                       'mayor o menor según el diseño concreto.'),
        'umbrales': ('No hay un umbral numérico: el aviso aparece siempre que se use un valor '
                     'típico. Entre productos del mismo estilo y tamaño, la capacidad puede variar'
                     ' del orden de ±20-30 % (práctica habitual). Recuerde: Kv = 0,865·Cv.'),
        'por_debajo': ('Si el Kv real es menor que el típico, la apertura real será mayor y la '
                       'válvula podría quedar justa o subdimensionada.'),
        'por_encima': ('Si el Kv real es mayor que el típico, la apertura real será menor y la '
                       'válvula podría quedar sobredimensionada.'),
        'ejemplo': ('Una válvula globo DN50 genérica se toma con Cv típico 50 y la apertura '
                    'resulta 70 %. El producto elegido tiene Cv certificado 40: la apertura real '
                    'sube a unos 85 %, todavía aceptable pero con menos margen.'),
        'afecta': [
            'Apertura calculada',
            'Alerta de válvula subdimensionada',
            'Alerta de apertura baja o alta',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            'Para la verificación final, cargue el Kv o Cv certificado y fije el diámetro.',
            'Use también los factores F<sub>L</sub> y x<sub>T</sub> del producto concreto.',
            'Deje un margen de capacidad mientras use valores típicos.',
        ],
    },
    'ruido': {
        'que_es': ('Es el sonido que genera la válvula al disipar energía cuando reduce la '
                   'presión. En gases y vapor es ruido aerodinámico y en líquidos es ruido '
                   'hidrodinámico, que crece mucho si hay cavitación.'),
        'que_hace': ('El programa estima el nivel sonoro ponderado A a 1 m aguas abajo y a 1 m de '
                     'la pared de la tubería (L<sub>pAe,1m</sub>) con IEC 60534-8-3 (gases) o IEC '
                     '60534-8-4 (líquidos) y lo compara con el límite del proyecto.'),
        'que_indica': ('Un valor alto indica riesgo para la audición del personal y, por encima de'
                       ' unos 110 dB(A), riesgo de daño por vibración en tubería e instrumentos. '
                       'La exactitud típica de la norma es ±5 dB.'),
        'umbrales': ('Límite habitual de especificación: 85 dB(A) a 1 m. El programa avisa desde 5'
                     ' dB por debajo del límite (80 dB(A) por defecto). Sobre unos 110 dB(A), '
                     'riesgo de daño mecánico.'),
        'por_debajo': ('Por debajo del límite el servicio es aceptable acústicamente; si está a '
                       'menos de 5 dB del límite, considérelo marginal por la incertidumbre de ±5 '
                       'dB.'),
        'por_encima': ('Por encima del límite se requieren protección auditiva o medidas de '
                       'reducción; sobre 110 dB(A) hay riesgo de fatiga en la tubería, soportes y '
                       'accesorios.'),
        'ejemplo': ('Una válvula de gas con flujo bloqueado da 98 dB(A) frente a un límite de 85 '
                    'dB(A): faltan 13 dB. Pasar de cédula 40 a cédula 80 aporta sólo unos pocos '
                    'dB, así que se requieren internos de bajo ruido (típicamente 10-20 dB de '
                    'reducción) o un silenciador.'),
        'afecta': [
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Alerta de ruido',
            'Selección del tipo de internos',
        ],
        'recomendaciones': [
            'Trate primero la fuente: internos de bajo ruido o multietapa, difusores aguas abajo.',
            'Reduzca la velocidad de salida con una válvula o tubería de salida más grande.',
            ('Trate el camino: silenciador en línea, tubería de mayor espesor o aislamiento '
             'acústico.'),
            ('En líquidos, elimine la cavitación con internos anticavitación o repartiendo la '
             'caída de presión.'),
        ],
    },
    'ruido_no_calculado': {
        'que_es': 'Es el aviso de que el programa no estimó el nivel de ruido para este caso.',
        'que_hace': ('Evita mostrar un valor de ruido que no sería válido, porque las condiciones '
                     'están fuera del alcance de IEC 60534-8-3 o 8-4, o porque faltan datos.'),
        'que_indica': ('No significa que la válvula sea silenciosa: sólo que el ruido no se puede '
                       'estimar con estas normas. Casos típicos: flashing en líquidos, flujo '
                       'bifásico o datos faltantes.'),
        'umbrales': ('No aplica un umbral numérico. Revise la causa: la condición de flashing '
                     '(P<sub>2</sub> ≤ p<sub>v</sub>) y el flujo bifásico quedan fuera del alcance'
                     ' de las normas de ruido usadas.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Agua a 180 °C con P<sub>2</sub> menor que su presión de vapor (unos 10 bar '
                    'abs) produce flashing: el programa no calcula el ruido. La válvula puede ser '
                    'ruidosa igual, y el riesgo principal es la erosión por la mezcla a alta '
                    'velocidad.'),
        'afecta': [
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Alerta de ruido',
        ],
        'recomendaciones': [
            ('Complete los datos que falten (diámetro y espesor de tubería, área de salida, '
             'propiedades del fluido).'),
            'En flashing o bifásico, pida la estimación al fabricante o use métodos específicos.',
            ('Con flashing, aplique prácticas de diseño reconocidas: salida expandida, materiales '
             'endurecidos y tubería de salida corta y recta.'),
        ],
    },
    'espesor_pared': {
        'que_es': ('Es el espesor de la pared de la tubería inmediatamente aguas abajo de la '
                   'válvula.'),
        'que_hace': ('Se usa en la pérdida de transmisión (TL) del ruido a través de la pared: una'
                     ' pared más gruesa deja pasar menos sonido hacia el exterior.'),
        'que_indica': ('A mayor espesor, menor ruido exterior calculado. Si se deja en blanco se '
                       'toma la cédula 40 de ASME B36.10M para el diámetro interior.'),
        'umbrales': ('Cédula 40: 4" 6,02 mm; 6" 7,11 mm; 8" 8,18 mm. Cédula 80: 4" 8,56 mm; 6" '
                     '10,97 mm; 8" 12,70 mm. Use el espesor real de la línea.'),
        'por_debajo': ('Si el espesor ingresado es menor que el real, el ruido calculado resulta '
                       'pesimista (mayor).'),
        'por_encima': ('Si el espesor ingresado es mayor que el real, el ruido calculado resulta '
                       'optimista; un error de unidad (in en vez de mm) puede bajar el ruido de '
                       'forma irreal.'),
        'ejemplo': ('Tubería de 6" aguas abajo de una válvula de gas: con cédula 40 (7,11 mm) el '
                    'programa da 89 dB(A). Con cédula 80 (10,97 mm) el resultado baja a unos 86 '
                    'dB(A), todavía sobre 85 dB(A): hace falta otra medida además del espesor.'),
        'afecta': [
            'Pérdida de transmisión TL',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            'Tome el espesor de la especificación de tubería del proyecto (clase de línea).',
            'Verifique la unidad (mm o in).',
            ('Aumentar la cédula es una medida de camino útil para pocos dB; como orden de '
             'magnitud, duplicar el espesor reduce unos 5-6 dB (práctica habitual).'),
            ('Si la tubería tiene aislamiento acústico, considérelo aparte, porque no es parte del'
             ' espesor de acero.'),
        ],
    },
    'limite_ruido': {
        'que_es': ('Es el nivel de ruido máximo admisible para la válvula, en dB(A) a 1 m, según '
                   'la especificación del proyecto o la legislación laboral.'),
        'que_hace': ('El programa compara el ruido calculado con este límite y emite una alerta si'
                     ' se acerca o lo supera.'),
        'que_indica': ('Define qué tan exigente es el servicio acústico: un límite más bajo obliga'
                       ' a soluciones de reducción de ruido más costosas.'),
        'umbrales': ('Valor por defecto: 85 dB(A). Algunas especificaciones usan 80 dB(A) en zonas'
                     ' con presencia permanente de personal y valores mayores en áreas sin '
                     'personal (práctica habitual). El programa avisa desde 5 dB por debajo del '
                     'límite.'),
        'por_debajo': ('Un límite muy bajo (por ejemplo, menos de 75 dB(A)) puede ser difícil de '
                       'cumplir con medidas razonables en servicios de gas con alta caída de '
                       'presión.'),
        'por_encima': ('Un límite muy alto (sobre unos 110 dB(A)) no protege contra daños por '
                       'vibración en tubería e instrumentos, aunque el área no tenga personal.'),
        'ejemplo': ('Con límite 85 dB(A), un ruido calculado de 82 dB(A) genera aviso (está a '
                    'menos de 5 dB) y uno de 79 dB(A) no. Si la planta exige 80 dB(A), el caso de '
                    '82 dB(A) pasa a estar sobre el límite.'),
        'afecta': [
            'Alerta de ruido',
            'Selección del tipo de internos',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            'Tome el valor de la especificación del proyecto o de la legislación local.',
            ('Considere la incertidumbre de ±5 dB de la norma: diseñe con margen si el valor queda'
             ' cerca del límite.'),
            ('Tenga en cuenta que varias fuentes cercanas suman ruido: dos fuentes de 85 dB(A) dan'
             ' unos 88 dB(A).'),
        ],
    },
    'bifasico': {
        'que_es': ('Es un servicio en el que a la entrada de la válvula ya circulan juntas una '
                   'fase líquida y una gaseosa, por ejemplo crudo con gas o agua saturada con '
                   'vapor.'),
        'que_hace': ('El programa dimensiona la válvula con el método de suma de fases separadas: '
                     'calcula la demanda de capacidad del líquido y del gas, cada una con su caída'
                     ' de presión límite, y las combina. También verifica la velocidad erosional '
                     'según API RP 14E.'),
        'que_indica': ('El Cv obtenido es una estimación conservadora, menos exacta que las '
                       'ecuaciones de IEC 60534-2-1 para una sola fase, que no cubren este caso.'),
        'umbrales': ('No hay un umbral de la norma. Práctica habitual: agregar un margen de '
                     'capacidad adicional (por ejemplo 10-25 %) y verificar que la velocidad de la'
                     ' mezcla a la salida no supere la velocidad erosional de API RP 14E.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Crudo de 850 kg/m³ con 5 % en masa de gas de 40 kg/m³: aunque el gas es poca '
                    'masa, ocupa más de la mitad del volumen. Con la suma de fases, la demanda del'
                    ' gas puede ser comparable a la del líquido y el Cv total resulta, por '
                    'ejemplo, 1,6 veces el de sólo el líquido.'),
        'afecta': [
            'Cv requerido',
            'Velocidad erosional API RP 14E',
            'Velocidad de salida',
            'Selección del tamaño de válvula',
        ],
        'recomendaciones': [
            'Use datos fiables de fracción másica y densidad de cada fase.',
            'Agregue margen de capacidad y verifique la apertura en los casos mínimo y máximo.',
            'Elija estilos de paso recto y materiales resistentes a la erosión.',
            'Si es posible, separe las fases aguas arriba y controle cada una por separado.',
        ],
    },
    'bifasico_metodo': {
        'que_es': ('Es el aviso de que el resultado bifásico se obtuvo con un método fuera de la '
                   'norma IEC 60534-2-1, que sólo cubre flujos de una fase.'),
        'que_hace': ('Recuerda al usuario que el Cv es una estimación y que debe aplicar márgenes '
                     'y verificaciones adicionales.'),
        'que_indica': ('No es un error: indica mayor incertidumbre en el Cv y en la apertura '
                       'calculados.'),
        'umbrales': ('Se muestra siempre que el cálculo sea bifásico. Práctica habitual: margen de'
                     ' capacidad adicional de 10-25 % y verificación de la velocidad erosional de '
                     'API RP 14E.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('El método da Cv = 80 para una mezcla de agua y vapor. Con un margen de 20 % '
                    'se selecciona una válvula que permita Cv ≈ 96 a una apertura de 80-90 %, por '
                    'ejemplo una de Cv nominal 115.'),
        'afecta': [
            'Cv requerido',
            'Apertura calculada',
            'Velocidad erosional API RP 14E',
        ],
        'recomendaciones': [
            'Use un margen de capacidad adicional y verifique la apertura resultante.',
            'Verifique la erosión con la velocidad de la mezcla a la salida.',
            'Valide el dimensionamiento con el fabricante para servicios críticos.',
        ],
    },
    'xg': {
        'que_es': ('Es la parte del caudal másico total que es gas o vapor a la entrada de la '
                   'válvula; también se llama calidad o título. 0 % es líquido puro y 100 % es gas'
                   ' puro.'),
        'que_hace': ('Reparte el caudal total entre la fase líquida y la gaseosa para calcular la '
                     'demanda de capacidad de cada una en el método bifásico.'),
        'que_indica': ('Valores pequeños en masa pueden significar mucho volumen de gas, porque el'
                       ' gas es mucho menos denso: incluso 1-5 % en masa puede dominar el volumen.'),
        'umbrales': ('Rango válido: 0-100 %. Conversión desde volumen: x<sub>g</sub> = '
                     'Q<sub>g</sub>·ρ<sub>g</sub>/(Q<sub>g</sub>·ρ<sub>g</sub> + '
                     'Q<sub>l</sub>·ρ<sub>l</sub>), con caudales volumétricos a condiciones de '
                     'entrada.'),
        'por_debajo': ('Con x<sub>g</sub> cercano a 0 el servicio es casi líquido; conviene '
                       'verificar si en realidad se puede tratar como líquido (con verificación de'
                       ' flashing).'),
        'por_encima': ('Con x<sub>g</sub> cercano a 100 % el servicio es casi gas; puede ser más '
                       'exacto dimensionarlo como gas con IEC 60534-2-1.'),
        'ejemplo': ('En un caudal total de 10 000 kg/h circulan 9 500 kg/h de líquido y 500 kg/h '
                    'de gas: x<sub>g</sub> = 500/10 000 = 5 %. Con ρ<sub>l</sub> = 850 kg/m³ y '
                    'ρ<sub>g</sub> = 40 kg/m³, el gas ocupa 12,5 m³/h frente a 11,2 m³/h de '
                    'líquido, más de la mitad del volumen.'),
        'afecta': [
            'Cv requerido',
            'Densidad de la mezcla',
            'Velocidad erosional API RP 14E',
            'Velocidad de salida',
        ],
        'recomendaciones': [
            ('Use caudales y densidades a condiciones de entrada (P<sub>1</sub>, T<sub>1</sub>), '
             'no a condiciones estándar.'),
            ('Si tiene la relación gas-petróleo (GOR) en condiciones estándar, conviértala primero'
             ' a condiciones reales.'),
            ('Evalúe los casos mínimo y máximo de x<sub>g</sub>, ya que la capacidad requerida '
             'cambia mucho.'),
        ],
    },
    'rho_l': {
        'que_es': ('Son las densidades de la fase líquida (ρ<sub>l</sub>) y de la fase gaseosa '
                   '(ρ<sub>g</sub>) a las condiciones de entrada, ingresadas por separado.'),
        'que_hace': ('Cada fase se dimensiona con su propia densidad en el método bifásico; '
                     'también se usan para calcular la densidad homogénea de la mezcla en la '
                     'verificación de erosión.'),
        'que_indica': ('La diferencia entre ambas indica cuánto volumen ocupa cada fase: a menor '
                       'ρ<sub>g</sub>, más volumen de gas y mayor capacidad requerida.'),
        'umbrales': ('Valores típicos de ρ<sub>l</sub>: agua a 20 °C 998 kg/m³; crudos 800-950 '
                     'kg/m³; GLP 500-580 kg/m³. ρ<sub>g</sub> suele estar entre 1 y 100 kg/m³ '
                     'según presión y composición. Si ρ<sub>g</sub> resulta comparable a '
                     'ρ<sub>l</sub>, revise los datos.'),
        'por_debajo': ('Si ρ<sub>l</sub> o ρ<sub>g</sub> se subestiman, el volumen de cada fase se'
                       ' sobreestima y el Cv sale mayor del necesario.'),
        'por_encima': ('Si se sobreestiman, el Cv sale menor y la válvula puede quedar '
                       'subdimensionada.'),
        'ejemplo': ('Agua saturada a 10 bar abs (unos 180 °C): ρ<sub>l</sub> ≈ 887 kg/m³ y '
                    'ρ<sub>g</sub> ≈ 5,1 kg/m³. El vapor es unas 170 veces menos denso, por lo que'
                    ' con sólo 5 % en masa de vapor éste ocupa casi el 90 % del volumen.'),
        'afecta': [
            'Cv requerido',
            'Densidad de la mezcla',
            'Velocidad erosional API RP 14E',
            'Velocidad de salida',
        ],
        'recomendaciones': [
            'Use densidades a P<sub>1</sub> y T<sub>1</sub>, no a condiciones estándar.',
            'Verifique la unidad (kg/m³ o lb/ft³; 1 lb/ft³ = 16,02 kg/m³).',
            'Con fluidos de la lista, deje que el programa calcule ambas densidades a saturación.',
        ],
    },
    'rho_g': {
        'que_es': ('Es la densidad de la fase gaseosa o vapor a la presión P<sub>1</sub> y '
                   'temperatura T<sub>1</sub> de entrada.'),
        'que_hace': ('Se usa para calcular la demanda de capacidad de la fase gaseosa en el método'
                     ' bifásico y la densidad de la mezcla para la verificación de erosión.'),
        'que_indica': ('Indica cuánto volumen ocupa el gas por kilogramo: un valor bajo significa '
                       'mucho volumen y, por lo tanto, mayor Cv y mayor velocidad.'),
        'umbrales': ('Para gas ideal: ρ<sub>g</sub> = P<sub>1</sub>·M/(Z·R·T<sub>1</sub>), con R ='
                     ' 8 314 J/(kmol·K), P en Pa y T en K. Valores usuales: aire a 1 bar abs y 20 '
                     '°C ≈ 1,19 kg/m³; gas natural a 50 bar abs ≈ 35-45 kg/m³.'),
        'por_debajo': ('Si se subestima, el Cv de la fase gaseosa sale mayor y el cálculo resulta '
                       'conservador.'),
        'por_encima': ('Si se sobreestima, el Cv sale menor y la válvula puede quedar '
                       'subdimensionada; además la velocidad de salida se subestima.'),
        'ejemplo': ('Gas natural con M = 17,4 kg/kmol a 50 bar abs y 30 °C (303 K), con Z = 0,90: '
                    'ρ<sub>g</sub> = 50·10<sup>5</sup>·17,4/(0,90·8 314·303) ≈ 38,4 kg/m³. Con Z ='
                    ' 1 resultaría 34,5 kg/m³, unos 10 % menos.'),
        'afecta': [
            'Cv requerido',
            'Densidad de la mezcla',
            'Velocidad erosional API RP 14E',
            'Velocidad de salida',
        ],
        'recomendaciones': [
            'Use presión absoluta y temperatura absoluta en la fórmula.',
            ('Use el factor de compresibilidad Z a alta presión; con Z = 1 se puede cometer un '
             'error de 10 % o más.'),
            'Verifique la unidad (kg/m³ o lb/ft³).',
        ],
    },
    'material': {
        'que_es': ('Es el material del cuerpo y del bonete de la válvula según especificación '
                   'ASTM, por ejemplo A216 WCB (acero al carbono fundido) o A351 CF8M (inoxidable '
                   '316 fundido).'),
        'que_hace': ('Define el grupo de materiales de ASME B16.34 y, con él, la presión admisible'
                     ' de cada clase a cada temperatura; también condiciona la resistencia a '
                     'corrosión y el rango de temperatura.'),
        'que_indica': ('Indica para qué temperaturas y fluidos es apto el cuerpo y cuánta presión '
                       'soporta: a igual clase, distintos grupos de material tienen distintas '
                       'presiones admisibles.'),
        'umbrales': ('Guía de rangos: A216 WCB / A105 (grupo 1.1) de −29 °C a 425 °C en servicio '
                     'continuo; A352 LCC/LCB o A350 LF2 hasta −46 °C; A351 CF8M / A182 F316 (grupo'
                     ' 2.2) para corrosión y criogenia (hasta −196 °C); A217 WC6/WC9 para alta '
                     'temperatura, hasta unos 540-590 °C según el material y la especificación.'),
        'por_debajo': ('Por debajo de la temperatura mínima del material (por ejemplo −29 °C para '
                       'WCB) hay riesgo de fractura frágil: se requieren aceros de baja '
                       'temperatura con ensayo de impacto o inoxidables austeníticos.'),
        'por_encima': ('Por encima del rango recomendado (por ejemplo 425 °C para WCB en servicio '
                       'continuo) hay riesgo de grafitización y pérdida de resistencia: use aceros'
                       ' de cromo-molibdeno o inoxidables.'),
        'ejemplo': ('Una línea de propano que puede enfriarse a −40 °C por despresurización no '
                    'puede usar WCB (mínimo −29 °C). Se elige A352 LCC, apto hasta −46 °C con '
                    'ensayo de impacto, y se verifica la clase con el grupo de materiales '
                    'correspondiente.'),
        'afecta': [
            'Verificación de clase de presión ASME B16.34',
            'Presión admisible a la temperatura de diseño',
            'Alerta de clase de presión insuficiente',
        ],
        'recomendaciones': [
            ('Use el mismo material, o uno compatible, que la especificación de tubería de la '
             'línea.'),
            'Para temperatura mínima de diseño bajo −29 °C, use LCC/LCB/LF2 o inoxidable.',
            'Para fluidos corrosivos, verifique la compatibilidad química y no sólo la presión.',
            'Para servicio continuo sobre 425 °C, use WC6, WC9 o inoxidable.',
        ],
    },
    'clase_presion': {
        'que_es': ('Es la designación de presión de la válvula según ASME B16.34 (150, 300, 600, '
                   '900, 1500, 2500), que fija la presión máxima de trabajo según el material y la'
                   ' temperatura.'),
        'que_hace': ('El programa la compara con la presión y temperatura de diseño; con '
                     '«Automática» propone la menor clase que las soporta.'),
        'que_indica': ('Una clase mayor soporta más presión, pero el número no es una presión en '
                       'bar ni en psi: la presión admisible baja al subir la temperatura.'),
        'umbrales': ('Presión admisible del grupo 1.1 (WCB) entre −29 y 38 °C, clase estándar: 150'
                     ' → 19,6 bar; 300 → 51,1 bar; 600 → 102,1 bar; 900 → 153,2 bar; 1500 → 255,3 '
                     'bar; 2500 → 425,5 bar. A 200 °C la clase 150 baja a 13,8 bar y la 300 a 43,8'
                     ' bar.'),
        'por_debajo': ('Si la clase seleccionada es menor que la necesaria, la válvula no es apta:'
                       ' el programa emite la alerta de clase insuficiente.'),
        'por_encima': ('Una clase innecesariamente alta encarece la válvula y puede no coincidir '
                       'con las bridas de la línea.'),
        'ejemplo': ('Diseño a 40 bar g y 200 °C con WCB: la clase 150 admite 13,8 bar y no sirve; '
                    'la clase 300 admite 43,8 bar y cumple. Si la línea es clase 300, la válvula '
                    'también debe ser clase 300.'),
        'afecta': [
            'Verificación de clase de presión ASME B16.34',
            'Alerta de clase de presión insuficiente',
            'Selección de la válvula',
        ],
        'recomendaciones': [
            ('Haga coincidir la clase de la válvula con la de las bridas de la línea (ASME B16.5),'
             ' salvo justificación.'),
            'Verifique la clase a la temperatura de diseño, no sólo a temperatura ambiente.',
            ('Use «Automática» como punto de partida y luego ajuste a la clase de la '
             'especificación de tubería.'),
        ],
    },
    'P_diseno': {
        'que_es': ('Son la presión y la temperatura de diseño de la línea donde se instala la '
                   'válvula, tomadas de la lista de líneas o del P&ID. Normalmente son mayores que'
                   ' las de operación.'),
        'que_hace': ('Se usan para verificar que la clase de presión y el material de la válvula '
                     'sean adecuados (ASME B16.34). No intervienen en el cálculo del Cv.'),
        'que_indica': ('Indican las condiciones más severas que la válvula debe soportar '
                       'mecánicamente, incluidas las sobrepresiones previstas por el diseño del '
                       'sistema.'),
        'umbrales': ('Si se dejan en blanco se usan la máxima P<sub>1</sub> y la máxima '
                     'T<sub>1</sub> de los casos, con un aviso. Práctica habitual en la definición'
                     ' de la línea: presión de diseño igual a la máxima de operación más 10 % o '
                     'más 1,7 bar (25 psi), lo que sea mayor, y temperatura de diseño 15-30 °C por'
                     ' encima de la máxima de operación.'),
        'por_debajo': ('Si se ingresan valores menores que los reales de diseño, se puede elegir '
                       'una clase insuficiente para las sobrepresiones del sistema.'),
        'por_encima': ('Valores exagerados llevan a clases y materiales más caros que lo '
                       'necesario.'),
        'ejemplo': ('La operación máxima es 30 bar g y 150 °C; la lista de líneas indica diseño a '
                    '35 bar g y 180 °C. Con WCB, la clase 150 (unos 14,6 bar a 180 °C) no cumple y'
                    ' la clase 300 (unos 44,3 bar a 180 °C) sí.'),
        'afecta': [
            'Verificación de clase de presión ASME B16.34',
            'Alerta de clase de presión insuficiente',
            'Selección de la clase automática',
        ],
        'recomendaciones': [
            'Use siempre los valores de la lista de líneas del proyecto, no los de operación.',
            'Verifique si la presión es manométrica o absoluta.',
            'Considere la temperatura mínima de diseño para elegir el material.',
        ],
    },
    'clase_insuficiente': {
        'que_es': ('Es la alerta que indica que la presión de diseño supera la presión admisible '
                   'de la clase y el material elegidos, a la temperatura de diseño.'),
        'que_hace': ('Impide aceptar una válvula que mecánicamente no soporta las condiciones de '
                     'la línea según ASME B16.34.'),
        'que_indica': ('La válvula no es apta: el cuerpo trabajaría por encima de su presión '
                       'admisible, con riesgo de falla de la envolvente a presión.'),
        'umbrales': ('La alerta se dispara cuando la presión de diseño es mayor que la presión '
                     'admisible de la tabla de ASME B16.34 para el grupo de material, la clase y '
                     'la temperatura de diseño.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Diseño a 45 bar g y 200 °C con WCB clase 300: la presión admisible es 43,8 '
                    'bar, menor que 45 bar, y se dispara la alerta. Con clase 600 la admisible es '
                    '87,6 bar y la válvula cumple.'),
        'afecta': [
            'Verificación de clase de presión ASME B16.34',
            'Selección de la válvula',
            'Clase automática',
        ],
        'recomendaciones': [
            'Elija la clase inmediatamente superior.',
            ('O cambie a un material de mayor resistencia a esa temperatura (por ejemplo, de WCB a'
             ' WC6 en alta temperatura).'),
            ('Verifique que la presión y la temperatura de diseño estén bien ingresadas '
             '(manométrica o absoluta, °C o °F).'),
            'Coordine el cambio con la clase de bridas de la línea.',
        ],
    },
    'material_baja_temperatura': {
        'que_es': ('Alerta que aparece cuando la temperatura mínima de servicio o de diseño está '
                   'por debajo del límite inferior del material del cuerpo. El acero al carbono '
                   'fundido común (p. ej. WCB) pierde tenacidad y puede romperse en forma frágil, '
                   'sin deformarse antes.'),
        'que_hace': ('Verifica que el material del cuerpo y bonete pueda trabajar a la temperatura'
                     ' más baja que verá la válvula, incluida la autorrefrigeración por '
                     'despresurización (gases que se expanden, GLP, venteos).'),
        'que_indica': ('Si aparece, el material referencial no es seguro a esa temperatura: hay '
                       'riesgo de fractura frágil ante un golpe, una sobrepresión o un cambio '
                       'brusco de temperatura.'),
        'umbrales': ('La alerta se dispara por debajo de −29 °C (−20 °F), límite inferior habitual'
                     ' del acero al carbono sin ensayo de impacto. Referencias de práctica '
                     'habitual: LCB/LCC hasta −46 °C, LC3 (3,5 % Ni) hasta −101 °C, inoxidables '
                     'austeníticos (CF8M, CF3M) hasta −196 °C (criogenia).'),
        'por_debajo': ('Por debajo de −29 °C con acero al carbono común existe riesgo de fractura '
                       'frágil; es una condición de seguridad, no solo de vida útil.'),
        'por_encima': ('Por encima de −29 °C el acero al carbono es aceptable desde el punto de '
                       'vista de la tenacidad; la alerta no se activa.'),
        'ejemplo': ('Una válvula de GLP opera a 15 °C, pero en un venteo de emergencia el propano '
                    'puede bajar a −42 °C. Con cuerpo WCB (límite −29 °C) aparece la alerta. Se '
                    'cambia a LCC con ensayo Charpy a −46 °C y la condición queda cubierta.'),
        'afecta': [
            'Alerta de material del cuerpo',
            'Verificación de rating ASME B16.34',
            'Hoja de datos (material de cuerpo y bonete)',
        ],
        'recomendaciones': [
            ('Especificar acero al carbono con ensayo de impacto Charpy (LCB/LCC) para servicio '
             'hasta −46 °C.'),
            ('Usar acero al níquel (LC3) o inoxidable austenítico (CF8M/CF3M) para temperaturas '
             'más bajas.'),
            ('Para servicio criogénico (< −100 °C) pedir bonete extendido para que la '
             'empaquetadura quede lejos del frío.'),
            ('Considerar la temperatura mínima por despresurización o arranque en frío, no solo la'
             ' normal de operación.'),
        ],
    },
    'material_alta_temperatura': {
        'que_es': ('Alerta que indica que la temperatura de diseño supera la máxima que cubre la '
                   'tabla presión-temperatura del material elegido en ASME B16.34.'),
        'que_hace': ('Impide aceptar un rating cuya presión admisible no está definida por la '
                     'norma a esa temperatura.'),
        'que_indica': ('Si aparece, el programa no puede garantizar la resistencia del cuerpo: el '
                       'material trabajaría en zona de fluencia lenta (creep) o fuera de lo '
                       'tabulado.'),
        'umbrales': ('Para acero al carbono grupo 1.1 (WCB) la tabla de B16.34 llega hasta 538 °C '
                     '(1000 °F), aunque no se recomienda el servicio prolongado por encima de 425 '
                     '°C. Aceros Cr-Mo (WC6, WC9, C12A) e inoxidables austeníticos admiten '
                     'temperaturas mayores según su grupo. Asientos blandos y revestimientos '
                     'tienen límites mucho menores (PTFE ≈ 200–230 °C, práctica habitual).'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Por encima de la máxima tabulada el material puede deformarse por creep, '
                       'perder resistencia o romperse; la clase de presión deja de ser válida.'),
        'ejemplo': ('Una válvula de vapor sobrecalentado tiene T de diseño 565 °C. Con WCB (tabla '
                    'hasta 538 °C) aparece la alerta. Se elige WC9 (2¼Cr-1Mo), cuya tabla cubre '
                    'esa temperatura, y se recalcula la presión admisible.'),
        'afecta': [
            'Verificación de rating ASME B16.34',
            'Presión admisible a la temperatura de diseño',
            'Alerta de material del cuerpo',
        ],
        'recomendaciones': [
            ('Cambiar a un material apto: Cr-Mo (WC6, WC9, C12A) o inoxidable austenítico según la'
             ' temperatura.'),
            'Revisar que la temperatura de diseño sea realista y no un margen excesivo.',
            ('Para alta temperatura pedir bonete extendido o con aletas para proteger la '
             'empaquetadura.'),
            'Verificar también asiento, juntas y empaquetadura (grafito en lugar de PTFE).',
        ],
    },
    'grafitizacion': {
        'que_es': ('Es la degradación del acero al carbono cuando trabaja mucho tiempo a alta '
                   'temperatura: los carburos de hierro se descomponen en nódulos de grafito, que '
                   'dejan el acero más frágil y débil.'),
        'que_hace': ('El programa advierte cuando el material de carbono se usaría en la zona '
                     'donde este daño es probable, para que se considere un material aleado.'),
        'que_indica': ('Si aparece, la válvula podría cumplir el rating hoy, pero su material se '
                       'degradará con los años de servicio continuo.'),
        'umbrales': ('La alerta corresponde a servicio prolongado por encima de 425 °C (800 °F) '
                     'con acero al carbono, como advierte ASME B16.34. Los aceros con Cr-Mo (p. '
                     'ej. WC6 con 1¼Cr-½Mo) resisten este mecanismo.'),
        'por_debajo': ('Por debajo de 425 °C la grafitización no es una preocupación práctica para'
                       ' acero al carbono.'),
        'por_encima': ('Por encima de 425 °C en servicio continuo hay riesgo de grafitización y '
                       'creep; puede causar fisuras, sobre todo cerca de soldaduras.'),
        'ejemplo': ('Una válvula de vapor a 440 °C de operación continua con cuerpo WCB activa la '
                    'alerta aunque la presión esté dentro del CL300. Se especifica WC6, que es la '
                    'práctica habitual para vapor entre 425 y 540 °C.'),
        'afecta': [
            'Alerta de material del cuerpo',
            'Verificación de rating ASME B16.34',
            'Hoja de datos (material)',
        ],
        'recomendaciones': [
            'Usar acero Cr-Mo (WC6, WC9) o inoxidable para servicio continuo sobre 425 °C.',
            ('Distinguir picos breves (arranques, purgas) de la operación continua al evaluar la '
             'alerta.'),
            ('Si se mantiene acero al carbono por excepción, documentarlo y prever inspección '
             'periódica.'),
        ],
    },
    'diseno_por_operacion': {
        'que_es': ('Aviso de que no se cargaron la presión y la temperatura de diseño, por lo que '
                   'la clase de presión se verificó con los valores máximos de operación.'),
        'que_hace': ('Informa que la verificación del rating es menos conservadora de lo habitual,'
                     ' porque usa la operación y no el diseño de la línea.'),
        'que_indica': ('Indica una verificación provisoria: el resultado puede cambiar al cargar '
                       'los datos de diseño reales de la línea.'),
        'umbrales': ('Las condiciones de diseño se toman de la lista de líneas o de la '
                     'especificación de tuberías. Como práctica habitual, la presión de diseño es '
                     'la máxima de operación más 10 % (o al menos 1,7 bar) y la temperatura de '
                     'diseño la máxima de operación más unos 25–30 °C.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Una válvula opera a 18 bar(g) y 120 °C máximos. Sin diseño, CL150 de WCB (≈ '
                    '16 bar a 120 °C, valor aproximado) ya no alcanza y el programa pide CL300. Si'
                    ' la línea se diseñó a 25 bar(g) y 150 °C, la verificación correcta debe '
                    'hacerse con esos valores.'),
        'afecta': [
            'Verificación de rating ASME B16.34',
            'Verificación de temperatura del asiento blando o revestimiento',
            'Hoja de datos (condiciones de diseño)',
        ],
        'recomendaciones': [
            ('Pedir a proceso o tuberías la presión y temperatura de diseño de la línea y '
             'cargarlas.'),
            ('Usar la misma clase de presión que la especificación de tuberías (las bridas deben '
             'coincidir).'),
            ('Considerar condiciones de bloqueo aguas abajo o presión de cierre de bomba '
             '(shut-off) como presión de diseño.'),
        ],
    },
    'identificacion': {
        'que_es': ('Son los datos que identifican la válvula y el documento: proyecto, cliente, '
                   'tag, servicio, número de documento, revisión, autor y fecha.'),
        'que_hace': ('Aparecen en el encabezado de la memoria de cálculo, la hoja de datos y el '
                     'informe técnico, y permiten rastrear cada documento.'),
        'que_indica': ('No es un valor de cálculo; indica a qué instrumento y a qué versión '
                       'corresponde el documento.'),
        'umbrales': ('No hay umbrales numéricos. Buenas prácticas: tag según ISA-5.1 (p. ej. '
                     'FV-1101, PV-2003), número de documento según el sistema del proyecto y '
                     'revisión correlativa (A, B, C para emisiones preliminares; 0, 1, 2 para '
                     'emisiones aprobadas, práctica habitual).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Proyecto «Ampliación planta de agua», tag LV-1203, servicio «Control de nivel'
                    ' tanque T-12», documento HD-IN-1203, revisión B, autor y fecha de emisión. Si'
                    ' luego cambia el caudal máximo, se emite la revisión C con la nueva fecha.'),
        'afecta': [
            'Encabezado de memoria de cálculo',
            'Encabezado de hoja de datos',
            'Encabezado de informe técnico',
        ],
        'recomendaciones': [
            'Usar el tag exacto del P&ID y de la lista de instrumentos.',
            'Actualizar revisión y fecha en cada emisión y registrar el cambio.',
            'Describir el servicio con claridad (p. ej. «Control de nivel del separador V-101»).',
        ],
    },
    'flujo_trabajo': {
        'que_es': ('Es la secuencia recomendada para usar el programa: datos de instalación, '
                   'condiciones de operación, cálculo y exportación de entregables.'),
        'que_hace': ('Ordena la carga para que los datos dependientes (diámetros, cédulas, '
                     'factores del trim) se completen solos y los resultados sean coherentes.'),
        'que_indica': ('No es un valor; seguir el orden evita resultados incompletos o basados en '
                       'datos por defecto.'),
        'umbrales': ('No hay umbrales. Buena práctica: cargar las tres condiciones de operación '
                     '(mínima, normal y máxima) para verificar la apertura y la rangeabilidad, y '
                     'revisar los factores típicos del trim antes de calcular.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Se carga una válvula globo CL300 en tubería de 4" Sch 40, luego agua a 20, 50'
                    ' y 80 m³/h con sus presiones. Al presionar Calcular aparecen Cv, apertura y '
                    'alertas en celdas verdes, y desde Inicio → Entregables se exporta la hoja de '
                    'datos a Word.'),
        'afecta': [
            'Todos los resultados del dimensionamiento',
            'Memoria de cálculo',
            'Hoja de datos',
            'Informe técnico',
        ],
        'recomendaciones': [
            'Completar primero 1-Sistema (estilo, rating, tuberías) y después 2-Cálculos Válvula.',
            ('Reemplazar los factores típicos (FL, Fd, xT) por los certificados del fabricante '
             'cuando se tengan.'),
            'Recalcular después de cualquier cambio de datos antes de exportar.',
            'Revisar las alertas antes de emitir los entregables.',
        ],
    },
    'estilo_cuerpo': {
        'que_es': ('Es el tipo de cuerpo de la válvula: globo, globo con liner, ángulo, bola o '
                   'mariposa (concéntrica, doble o triple excentricidad).'),
        'que_hace': ('Define los internos disponibles, los factores típicos (FL, xT, Fd), la '
                     'capacidad por tamaño y el coeficiente acústico usado en el ruido.'),
        'que_indica': ('El estilo indica cuán bien tolera la válvula caídas de presión altas: un '
                       'FL alto (globo ≈ 0,9) retrasa la cavitación y el estrangulamiento; un FL '
                       'bajo (bola o mariposa ≈ 0,55–0,75) da más capacidad pero cavita antes.'),
        'umbrales': ('Valores típicos orientativos (IEC 60534-2-1, Anexo): globo contorneado FL ≈ '
                     '0,9 y xT ≈ 0,72; bola segmentada FL ≈ 0,6 y xT ≈ 0,3; mariposa a 60–70° FL ≈'
                     ' 0,6–0,7 y xT ≈ 0,4. Práctica habitual: globo hasta 12–16" y mariposa en '
                     'diámetros grandes con ΔP moderada.'),
        'por_debajo': ('Un estilo de FL bajo con ΔP alta lleva a cavitación o flujo estrangulado '
                       'en líquidos y a mayor ruido en gases.'),
        'por_encima': ('Un estilo de mucha capacidad elegido para poco caudal queda trabajando '
                       'casi cerrado, con mal control.'),
        'ejemplo': ('Agua con P1 = 10 bar(a), Pv ≈ 0 y ΔP = 6 bar. Con mariposa (FL ≈ 0,6) la ΔP '
                    'choked es 0,36·10 = 3,6 bar: el flujo está estrangulado. Con globo (FL ≈ 0,9)'
                    ' es 0,81·10 = 8,1 bar y el flujo no se estrangula.'),
        'afecta': [
            'Cv requerido',
            'Factor FL y ΔP choked',
            'Alerta de cavitación',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Ruido aerodinámico IEC 60534-8-3',
            'Selección del tamaño de válvula',
            'Trims disponibles',
        ],
        'recomendaciones': [
            'Usar globo para servicios con ΔP alta, cavitación o necesidad de buen control.',
            ('Usar ángulo para flashing, fluidos erosivos o con sólidos, descargando directo a un '
             'recipiente.'),
            ('Usar bola o mariposa para caudales grandes con ΔP baja o fluidos con sólidos y '
             'viscosos.'),
            ('Usar globo con liner solo para corrosivos dentro del límite de temperatura del '
             'revestimiento.'),
        ],
    },
    'rating': {
        'que_es': ('Es la clase de presión-temperatura del cuerpo según ASME B16.34 (CL150 a '
                   'CL2500). Cada clase define la presión máxima admisible a cada temperatura para'
                   ' cada grupo de material.'),
        'que_hace': ('Verifica que el cuerpo resista la presión de diseño a la temperatura de '
                     'diseño; también define las bridas y dimensiones cara a cara.'),
        'que_indica': ('Si la presión admisible a la temperatura de diseño es mayor que la presión'
                       ' de diseño, la clase es suficiente; si es menor, hay que subir de clase o '
                       'cambiar material.'),
        'umbrales': ('Valores referenciales para acero al carbono grupo 1.1 (WCB) a 38 °C: CL150 ≈'
                     ' 19,6 bar (285 psig), CL300 ≈ 51,1 bar (740 psig), CL600 ≈ 102,1 bar, CL900 '
                     '≈ 153,2 bar, CL1500 ≈ 255,3 bar, CL2500 ≈ 425,5 bar. La admisible baja con '
                     'la temperatura (CL150 WCB ≈ 5,5 bar a 425 °C).'),
        'por_debajo': ('Si la presión admisible queda por debajo de la de diseño, el cuerpo no '
                       'cumple la norma y hay riesgo de falla; debe subirse la clase.'),
        'por_encima': ('Una clase muy superior a la necesaria encarece la válvula y puede no '
                       'coincidir con las bridas de la línea.'),
        'ejemplo': ('Línea de vapor a 20 bar(g) y 250 °C. CL150 WCB admite solo ≈ 12,1 bar a 250 '
                    '°C, así que no alcanza. CL300 admite ≈ 41,7 bar a 250 °C y la válvula queda '
                    'verificada.'),
        'afecta': [
            'Verificación de rating ASME B16.34',
            'Presión admisible a la temperatura de diseño',
            'Tipo de conexión (alertas de combinación)',
            'Hoja de datos',
        ],
        'recomendaciones': [
            'Usar la misma clase que la especificación de tuberías de la línea.',
            'Verificar a la temperatura de diseño, no solo a temperatura ambiente.',
            ('Repetir la verificación con el material real cuando se defina (esta versión usa WCB '
             'como referencia).'),
            ('Considerar la presión de cierre de la bomba o del compresor como posible presión de '
             'diseño.'),
        ],
    },
    'nps': {
        'que_es': ('Es el tamaño nominal de la tubería en pulgadas (NPS). No es el diámetro real: '
                   'el diámetro interior depende también de la cédula.'),
        'que_hace': ('Con la cédula define el diámetro interior, que se usa en los factores de '
                     'reductores (Fp, FLp), las velocidades en tubería y el cálculo de ruido.'),
        'que_indica': ('Si la válvula es menor que la tubería, el programa supone reductores '
                       'concéntricos, que reducen la capacidad efectiva (Fp < 1) y modifican FL.'),
        'umbrales': ('Práctica habitual: la válvula de control suele ser igual o un tamaño menor '
                     'que la tubería, y no menor que la mitad del diámetro de la línea. El NPS de '
                     'la tubería debe dar velocidades de líquido de 1–3 m/s (máximo ≈ 4,5 m/s).'),
        'por_debajo': ('Una tubería chica genera velocidades altas: erosión, ruido, golpe de '
                       'ariete y pérdida de presión excesiva.'),
        'por_encima': ('Una tubería mucho mayor que la válvula obliga a reductores grandes, baja '
                       'el factor Fp y puede indicar una válvula mal dimensionada.'),
        'ejemplo': ('Una válvula de 3" en tubería de 4" usa reductores concéntricos 4"×3". El '
                    'programa calcula Fp algo menor que 1, por lo que el Cv requerido sube unos '
                    'pocos por ciento respecto a la instalación sin reductores.'),
        'afecta': [
            'Diámetro interno de tubería',
            'Factor de geometría de tubería Fp',
            'Factor FLp',
            'Velocidad en tubería',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            'Cargar el NPS real de las tuberías de entrada y salida según el P&ID o isométrico.',
            'Evitar válvulas menores que la mitad del diámetro de la línea (práctica habitual).',
            ('En gases con expansión, la tubería de salida suele ser mayor que la de entrada para '
             'limitar Mach y ruido.'),
        ],
    },
    'cedula': {
        'que_es': ('Es la designación del espesor de pared de la tubería (Sch 10, 40, 80, STD, XS,'
                   ' 10S, 40S, etc.).'),
        'que_hace': ('Junto con el NPS define el diámetro interior (DI = OD − 2·t); el espesor de '
                     'la tubería de salida además atenúa el ruido transmitido al exterior.'),
        'que_indica': ('Una cédula mayor significa pared más gruesa: menor diámetro interior (más '
                       'velocidad) y mayor atenuación de ruido.'),
        'umbrales': ('Práctica habitual: acero al carbono Sch 40/STD para servicios generales '
                     'hasta 10", Sch 80/XS para presiones altas o diámetros chicos; inoxidable Sch'
                     ' 10S o 40S. La cédula la fija la especificación de tuberías del proyecto.'),
        'por_debajo': ('Una pared fina transmite más ruido al exterior (menor pérdida de '
                       'transmisión) y tiene menos margen de corrosión y presión.'),
        'por_encima': ('Una pared gruesa reduce el diámetro interior y aumenta la velocidad; '
                       'también encarece la línea.'),
        'ejemplo': ('Tubería de 4": OD = 114,3 mm. Con Sch 40 (t = 6,02 mm) el DI es 102,3 mm; con'
                    ' Sch 80 (t = 8,56 mm) el DI baja a 97,2 mm, la velocidad sube cerca de 11 % y'
                    ' la atenuación de ruido mejora unos pocos dB.'),
        'afecta': [
            'Diámetro interno de tubería',
            'Velocidad en tubería',
            'Factores Fp y FLp',
            'Pérdida de transmisión del ruido IEC 60534-8-3/8-4',
            'Nivel de ruido a 1 m',
        ],
        'recomendaciones': [
            'Tomar la cédula de la especificación de tuberías, no suponerla.',
            'Usar cédulas «S» solo con tubería inoxidable (ASME B36.19M).',
            ('Si el ruido supera el límite, una pared más gruesa aguas abajo puede ayudar, aunque '
             'no reemplaza un trim de bajo ruido.'),
        ],
    },
    'conexion': {
        'que_es': ('Es la forma en que los extremos de la válvula se unen a la tubería: soldada a '
                   'tope (BWE), soldada de enchufe (SWE), bridada (RF, FF, RTJ), sin bridas, wafer'
                   ' o roscada (NPT).'),
        'que_hace': ('Define dimensiones y compatibilidad con la tubería; el programa avisa las '
                     'combinaciones poco habituales con el estilo, diámetro y rating.'),
        'que_indica': ('Indica cómo se monta y mantiene la válvula y qué presiones y temperaturas '
                       'tolera la unión.'),
        'umbrales': ('Práctica habitual: bridada RF para la mayoría de los servicios; RTJ en CL900'
                     ' y mayores o en servicios críticos; BWE en alta presión/temperatura y vapor;'
                     ' SWE y NPT solo hasta 2" (NPT normalmente no por encima de CL600); FF solo '
                     'con CL150 contra bridas de fundición o no metálicas; wafer solo en '
                     'mariposas.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Usar roscas o SWE por encima de 2", o FF por encima de CL150, se aparta de'
                       ' la práctica habitual y genera una alerta.'),
        'ejemplo': ('Válvula de 6" CL300 para hidrocarburo: se elige bridada RF según ASME B16.5. '
                    'Si se pidiera 6" NPT, el programa avisa porque la rosca por encima de 2" no '
                    'es práctica habitual.'),
        'afecta': [
            'Alerta de combinación de conexión',
            'Hoja de datos',
            'Dimensiones cara a cara',
        ],
        'recomendaciones': [
            'Usar el mismo tipo de cara que las bridas de la tubería (RF con RF, RTJ con RTJ).',
            'Preferir bridado si la válvula debe desmontarse para mantenimiento.',
            'Evitar roscas en fluidos tóxicos, inflamables o con vibración.',
            'Usar BWE en vapor de alta presión o donde se exige cero fugas por juntas.',
        ],
    },
    'T_diseno': {
        'que_es': ('Es la temperatura máxima (o mínima) que la línea debe soportar según su '
                   'diseño, normalmente tomada de la lista de líneas.'),
        'que_hace': ('Se usa para verificar el rating del cuerpo y comprobar que el asiento blando'
                     ' o el revestimiento soportan la temperatura. Si se deja vacía se usa la '
                     'máxima T1 de operación.'),
        'que_indica': ('Cuanto mayor es la temperatura de diseño, menor es la presión admisible '
                       'del cuerpo y más limitados quedan los materiales blandos.'),
        'umbrales': ('Práctica habitual: la temperatura de diseño es la máxima de operación más '
                     'unos 25–30 °C. Límites orientativos: PTFE ≈ 200–230 °C, PFA ≈ 200–260 °C, '
                     'acero al carbono hasta 425 °C en servicio continuo y −29 °C como mínimo.'),
        'por_debajo': ('Una temperatura de diseño inferior a −29 °C con acero al carbono dispara '
                       'la alerta de baja temperatura.'),
        'por_encima': ('Una temperatura alta reduce la presión admisible, puede exigir subir de '
                       'clase y descalificar asientos blandos o revestimientos.'),
        'ejemplo': ('Agua caliente a 140 °C máximos de operación; la lista de líneas indica 170 °C'
                    ' de diseño. Con PTFE (≈ 200 °C) el asiento blando aún es aceptable, pero si '
                    'el diseño fuera 250 °C el programa avisaría que se necesita asiento metálico.'),
        'afecta': [
            'Verificación de rating ASME B16.34',
            'Alerta de asiento blando o revestimiento',
            'Alerta de material (baja o alta temperatura)',
            'Alerta de grafitización',
        ],
        'recomendaciones': [
            'Tomarla de la lista de líneas en lugar de estimarla.',
            ('No sobredimensionar el margen: subir mucho la temperatura puede forzar una clase '
             'mayor sin necesidad.'),
            ('Considerar también la temperatura mínima (arranque, despresurización) para el '
             'material.'),
        ],
    },
    'clase_cierre': {
        'que_es': ('Es la fuga máxima admitida con la válvula cerrada, según ANSI/FCI 70-2 (IEC '
                   '60534-4), desde Clase I (sin ensayo) hasta Clase VI (asiento blando, burbujas '
                   'por minuto).'),
        'que_hace': ('Define el tipo de asiento y obturador y la fuerza que el actuador debe '
                     'aplicar para cerrar.'),
        'que_indica': ('Una clase mayor indica menor fuga admitida, pero exige más fuerza de '
                       'asiento, asientos más delicados y mayor costo.'),
        'umbrales': ('Clase IV: 0,01 % de la capacidad nominal (asiento metálico estándar). Clase '
                     'V: 5·10⁻⁴ ml/min de agua por pulgada de puerto y por psi de ΔP. Clase VI '
                     '(ensayo con aire o nitrógeno): p. ej. 1" → 1 burbuja/min (0,15 ml/min); 4" →'
                     ' 11 burbujas/min (1,7 ml/min). Práctica habitual: Clase IV para control '
                     'general; V o VI cuando la fuga cuesta dinero o afecta la seguridad.'),
        'por_debajo': ('Una clase baja (II–III) puede dejar pasar fluido con la válvula cerrada y '
                       'no sirve si la válvula debe aislar.'),
        'por_encima': ('Una clase alta encarece la válvula; la Clase VI requiere asiento blando, '
                       'limitado en temperatura, lo que el programa verifica.'),
        'ejemplo': ('Válvula con puerto de 4" y ΔP de cierre de 100 psi (6,9 bar) en Clase V: fuga'
                    ' admisible = 5·10⁻⁴ × 4 × 100 = 0,2 ml/min de agua. En Clase IV, si la '
                    'capacidad nominal es 100 m³/h, la fuga admisible sería 0,01 m³/h, unas 50 '
                    'veces más.'),
        'afecta': [
            'Selección de asiento y obturador',
            'Fuerza de asiento del actuador',
            'Alerta de asiento blando vs temperatura de diseño',
            'Hoja de datos',
        ],
        'recomendaciones': [
            ('No usar la válvula de control como válvula de bloqueo; si se requiere aislación, '
             'agregar una válvula de bloqueo.'),
            'Pedir Clase IV salvo que el proceso justifique una mejor.',
            ('Para alta temperatura con baja fuga, usar Clase V con asiento metálico en lugar de '
             'VI.'),
            'Verificar que el actuador tenga la fuerza de cierre para la clase y la ΔP de cierre.',
        ],
    },
    'tipo_caudal': {
        'que_es': ('Indica si el caudal se ingresa como volumétrico (m³/h, gpm, L/min) a '
                   'condiciones de entrada, o como másico (kg/h, lb/h, t/h).'),
        'que_hace': ('El programa calcula el otro tipo con la densidad de entrada y usa el '
                     'adecuado en las ecuaciones de IEC 60534-2-1.'),
        'que_indica': ('No es un valor a interpretar; asegura que el caudal se lea con la base '
                       'correcta.'),
        'umbrales': ('No hay umbrales. Buena práctica: usar la base del balance de masa o de la '
                     'hoja de proceso. Los balances suelen darse en masa (kg/h); las bombas y '
                     'caudalímetros de líquidos en volumen (m³/h).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Proceso entrega 36 000 kg/h de agua a 60 °C (ρ ≈ 983 kg/m³). El programa lo '
                    'convierte a 36 000 / 983 ≈ 36,6 m³/h para calcular velocidades y Cv.'),
        'afecta': [
            'Cv requerido',
            'Flujo másico',
            'Velocidad en tubería',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            ('Usar el caudal en la misma base en que lo entrega proceso para no introducir errores'
             ' de conversión.'),
            ('Si es volumétrico, confirmar que está a condiciones de entrada (P1, T1) y no a '
             'condiciones estándar.'),
            'Verificar la densidad usada en la conversión.',
        ],
    },
    'SG': {
        'que_es': ('La gravedad específica es la densidad del líquido a condiciones de entrada '
                   'dividida por la del agua a 15 °C (999,1 kg/m³). Es un número sin unidades.'),
        'que_hace': ('Aparece como ρ1/ρ0 en la ecuación de líquidos de IEC 60534-2-1: el Cv '
                     'requerido es proporcional a √SG.'),
        'que_indica': ('SG > 1 indica un líquido más pesado que el agua (pide más Cv para el mismo'
                       ' caudal volumétrico); SG < 1, más liviano.'),
        'umbrales': ('Valores típicos: agua a 15 °C 1,000; agua a 90 °C 0,967; gasolina 0,72–0,76;'
                     ' crudo 0,80–0,95; ácido sulfúrico concentrado ≈ 1,83. No hay un umbral '
                     'normativo; debe corresponder a la temperatura real de entrada.'),
        'por_debajo': ('Si se usa una SG menor que la real, el Cv requerido sale subestimado y la '
                       'válvula puede quedar chica.'),
        'por_encima': ('Si se usa una SG mayor que la real, el Cv sale sobreestimado y la válvula '
                       'puede quedar grande, trabajando casi cerrada.'),
        'ejemplo': ('Agua a 15 °C con Q = 50 m³/h y ΔP = 1 bar requiere Kv ≈ 50 (Cv ≈ 58). Con un '
                    'líquido de SG = 1,44 el Cv requerido sube √1,44 = 1,2 veces, a Cv ≈ 69.'),
        'afecta': [
            'Cv requerido',
            'Flujo másico',
            'Velocidad en tubería (conversión másico-volumétrico)',
            'Apertura de la válvula',
        ],
        'recomendaciones': [
            'Usar la densidad a la temperatura de entrada, no a 15 °C.',
            'Elegir el fluido de la lista para que el programa la calcule a P1 y T1.',
            'Para mezclas o soluciones, pedir la densidad medida o del simulador de proceso.',
        ],
    },
    'trim': {
        'que_es': ('Son los internos de la válvula (obturador, asiento y jaula). Cada opción trae '
                   'sus factores típicos FL y Fd, su Kc y su característica, y además indica el '
                   'sentido en que el fluido atraviesa los internos.'),
        'que_hace': ('Determina cuánta caída de presión tolera la válvula antes de cavitar o '
                     'estrangularse, cuánto ruido genera y si el fluido tiende a abrir o a cerrar '
                     'el obturador.'),
        'que_indica': ('Sentido de flujo, la parte que más confunde. «Tiende a abrir» (flujo bajo '
                       'el obturador): el fluido entra por debajo del asiento y empuja el '
                       'obturador hacia arriba, en el sentido de apertura. «Tiende a cerrar» '
                       '(flujo sobre el obturador): entra por arriba y empuja el obturador contra '
                       'el asiento. En una jaula, «de adentro hacia afuera» significa que el '
                       'fluido sube por el asiento, llena el interior de la jaula y sale por las '
                       'ventanas hacia el cuerpo: es flujo bajo el obturador (tiende a abrir), la '
                       'dirección habitual. «De afuera hacia adentro» significa que el fluido '
                       'rodea la jaula, entra por las ventanas y baja por el asiento: es flujo '
                       'sobre el obturador (tiende a cerrar).'),
        'umbrales': ('Orientativo: contorneado o jaula de 4 ventanas mientras Kapp < 0,9·Kc del '
                     'trim (Kc típico 0,55–0,70); jaula anticavitación de 1 etapa para cavitación '
                     'moderada (Kc 0,85); multietapa para cavitación severa (Kc ≈ 0,95). El '
                     'sentido de flujo cambia FL: de adentro hacia afuera FL ≈ 0,90; de afuera '
                     'hacia adentro FL ≈ 0,85.'),
        'por_debajo': ('Un trim insuficiente para el servicio produce cavitación, erosión, '
                       'vibración y ruido.'),
        'por_encima': ('Un trim más complejo que lo necesario encarece la válvula, reduce la '
                       'capacidad por tamaño y puede taparse con fluidos sucios.'),
        'ejemplo': ('Agua con Kapp = 0,6. Un contorneado tiende a abrir (Kc 0,65) queda justo: 0,9'
                    ' × 0,65 = 0,585 < 0,6, así que conviene la jaula anticavitación de 1 etapa (Kc 0,85). '
                    'Con flashing, en cambio, se prefiere flujo que tiende a cerrar (de afuera '
                    'hacia adentro en una jaula, o angular) para que el vapor se forme lejos del '
                    'asiento.'),
        'afecta': [
            'Factores FL, Fd y Kc',
            'Alerta de cavitación',
            'ΔP choked',
            'Cv requerido y apertura',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Estabilidad cerca del asiento y empuje del actuador',
        ],
        'recomendaciones': [
            'Comparar Kapp con el Kc de cada trim antes de elegir.',
            ('Doble guía de vástago - superior: diseño de válvula de globo en el que el obturador o '
             'el vástago se apoya y se alinea en dos puntos de guiado separados, ubicados en la parte '
             'superior del conjunto (por encima de la corriente del fluido). Da buena alineación sin '
             'guías dentro de la zona de flujo; usa los factores del obturador contorneado.'),
            ('Usar flujo que tiende a abrir (de adentro hacia afuera en jaulas) salvo que haya '
             'flashing o un motivo del fabricante.'),
            ('Flujo que tiende a cerrar: más estable con ΔP baja pero puede producir golpe al '
             'cerrar («bathtub stopper»): verificar el actuador.'),
            'Reemplazar los factores típicos por los certificados del fabricante.',
            'Evitar trims de orificios pequeños en fluidos con sólidos.',
        ],
    },
    'Kc': {
        'que_es': ('Es el valor de ΔP/(P1 − Pv) a partir del cual el trim cavita en forma '
                   'sostenida y puede dañarse (régimen de cavitación constante de ISA-RP75.23, o '
                   'límite recomendado por el fabricante). Es el mismo concepto que usan los '
                   'programas de los fabricantes para la ΔP de cavitación: ΔPcav = Kc·(P1 − Pv).'),
        'que_hace': ('Se compara con Kapp para disparar la alerta de cavitación (con daño posible)'
                     ' y para elegir el trim. La cavitación incipiente, que solo aumenta el ruido,'
                     ' se evalúa aparte con xFz.'),
        'que_indica': ('Cuanto mayor es Kc, más caída de presión admite el trim sin cavitar en '
                       'forma dañina.'),
        'umbrales': ('Valores típicos del programa: contorneado 0,55–0,65; jaula de 4 ventanas '
                     '0,65–0,70; 60 orificios 0,80; 120 orificios 0,85; multietapa 0,95; rotativas'
                     ' 0,25–0,50. Al elegir el trim se cargan solos. Si se deja vacío se usa la '
                     'cavitación incipiente xFzp1 (criterio conservador). Siempre es menor que '
                     'FL².'),
        'por_debajo': ('Un Kc bajo frente al servicio indica que la válvula cavitará aun con ΔP '
                       'moderadas.'),
        'por_encima': 'Un Kc alto se logra con trims más complejos y costosos.',
        'ejemplo': ('Trim con Kc = 0,65, P1 = 10 bar(a) y Pv = 0,1 bar(a): ΔPcav = 0,65 × 9,9 = '
                    '6,4 bar. Con ΔP de servicio de 5 bar no hay cavitación dañina; si xFzp1 = '
                    '0,25 (ΔP incipiente 2,5 bar) sí hay cavitación incipiente y el ruido '
                    'calculado sube.'),
        'afecta': [
            'ΔP de inicio de cavitación',
            'Alerta de cavitación',
            'Selección del trim',
        ],
        'recomendaciones': [
            'Usar el valor del fabricante a las condiciones de servicio cuando esté disponible.',
            'Si Kapp ≥ Kc, elegir un trim de mayor Kc (orificios o multietapa).',
            'No confundir Kc con xFz (incipiente, ruido) ni con FL² (estrangulamiento).',
        ],
    },
    'Kapp': {
        'que_es': ('Es la relación entre la caída de presión del servicio y la presión disponible '
                   'sobre la de vapor: Kapp = ΔP/(P1 − Pv). Describe la exigencia de la aplicación'
                   ' sin importar qué válvula se use.'),
        'que_hace': ('Se compara con Kc y FLp² para clasificar el servicio: sin cavitación, con '
                     'cavitación o estrangulado.'),
        'que_indica': ('Un Kapp alto indica que el líquido se acerca mucho a su presión de vapor '
                       'dentro de la válvula.'),
        'umbrales': ('Kapp < Kc: sin cavitación. Kc ≤ Kapp < FLp²: cavitación (leve a severa). '
                     'Kapp ≥ FLp²: flujo estrangulado. Como referencia, con FL = 0,9 el límite de '
                     'estrangulamiento es ≈ 0,81.'),
        'por_debajo': ('Por debajo de Kc el servicio es tranquilo y un trim estándar es '
                       'suficiente.'),
        'por_encima': ('Por encima de Kc hay cavitación (ruido, vibración, erosión); por encima de'
                       ' FLp² el caudal deja de crecer con la ΔP.'),
        'ejemplo': ('Agua a 25 °C (Pv ≈ 0,03 bar(a)) con P1 = 10 bar(a) y ΔP = 4 bar: Kapp = '
                    '4/9,97 ≈ 0,40. Con un trim de Kc = 0,35 hay cavitación; como FL² = 0,81, el '
                    'flujo no está estrangulado.'),
        'afecta': [
            'Alerta de cavitación',
            'Alerta de flujo estrangulado',
            'Selección del trim',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            ('Reducir Kapp ubicando la válvula donde P1 sea mayor (más abajo o más cerca de la '
             'bomba).'),
            'Repartir la ΔP con un orificio de restricción o una segunda válvula en serie.',
            'Si no se puede cambiar el servicio, elegir un trim de Kc mayor que Kapp.',
            'Revisar Kapp en las tres condiciones de operación, no solo en la normal.',
        ],
    },
    'dPcav': {
        'que_es': ('Es la caída de presión a partir de la cual el trim cavita en forma sostenida: '
                   'ΔPcav = Kc·(P1 − Pv).'),
        'que_hace': ('Permite comparar directamente en bar la ΔP del servicio con la que tolera la'
                     ' válvula sin cavitación dañina.'),
        'que_indica': ('Si la ΔP de servicio es menor que ΔPcav no hay cavitación dañina (puede '
                       'haber incipiente, que solo suma ruido); si es mayor, sí. Si además supera '
                       'ΔP choked, el flujo está estrangulado.'),
        'umbrales': ('La condición de alerta es ΔP ≥ ΔPcav. Siempre se cumple ΔPcav < ΔP choked '
                     '(porque Kc < FL²).'),
        'por_debajo': ('Si la ΔP de servicio queda por debajo de ΔPcav el trim no sufre cavitación'
                       ' sostenida.'),
        'por_encima': ('Si la ΔP de servicio queda por encima de ΔPcav hay cavitación, con riesgo '
                       'de erosión, ruido y vibración.'),
        'ejemplo': ('P1 = 8 bar(a), Pv = 0,1 bar(a) y Kc = 0,4: ΔPcav = 0,4 × 7,9 = 3,16 bar. Con '
                    'ΔP de servicio de 5 bar hay cavitación; con un trim multietapa de Kc = 0,9, '
                    'ΔPcav sube a 7,1 bar y el problema desaparece.'),
        'afecta': [
            'Alerta de cavitación',
            'Selección del trim',
        ],
        'recomendaciones': [
            'Si ΔP > ΔPcav, elegir un trim de mayor Kc.',
            'Aumentar P1 relocalizando la válvula o subir la contrapresión aguas abajo.',
            'Dividir la caída de presión en etapas (multietapa o restricción en serie).',
        ],
    },
    'dP_P1': {
        'que_es': ('Es la fracción de la presión de entrada que se pierde en la válvula (ΔP/P1, '
                   'ambas en presión absoluta).'),
        'que_hace': ('Sirve como indicador rápido de cuán exigente es el servicio; en gases se '
                     'relaciona con la relación x usada en el factor de expansión Y.'),
        'que_indica': ('Valores bajos indican un servicio suave; valores altos anticipan '
                       'cavitación o flashing en líquidos y ruido y flujo crítico en gases.'),
        'umbrales': ('Orientativo (práctica habitual): por debajo de 0,1 servicio suave; entre 0,1'
                     ' y 0,5 moderado; por encima de 0,5 exigente. En gases el flujo se estrangula'
                     ' cuando x ≥ Fγ·xT (p. ej. ≈ 0,72 para globo con aire).'),
        'por_debajo': ('Un valor muy bajo puede indicar poca autoridad de la válvula sobre el '
                       'sistema y control pobre.'),
        'por_encima': ('Un valor alto anticipa cavitación, ruido, erosión y vibración; requiere '
                       'revisar el trim y los materiales.'),
        'ejemplo': ('Gas con P1 = 20 bar(a) y P2 = 8 bar(a): ΔP/P1 = 12/20 = 0,6. Es un servicio '
                    'exigente: con xT = 0,72 está cerca del flujo crítico y conviene revisar el '
                    'ruido.'),
        'afecta': [
            'Factor de expansión Y (gases)',
            'Alerta de cavitación',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
        ],
        'recomendaciones': [
            'Si es alto, revisar Kapp (líquidos) o x frente a xT (gases).',
            'Considerar trims de reducción de ruido o anticavitación.',
            ('Para buen control, que la válvula se lleve una parte apreciable de la pérdida del '
             'sistema (práctica habitual: 25–35 % de la pérdida dinámica).'),
        ],
    },
    'D_interno': {
        'que_es': ('Es el diámetro interior real de la tubería de entrada y de salida, calculado '
                   'con el NPS y la cédula: DI = OD − 2·t.'),
        'que_hace': ('Se usa para las velocidades en tubería, los factores de reductores (Fp, FLp)'
                     ' y el cálculo de ruido.'),
        'que_indica': ('Un DI menor implica mayor velocidad para el mismo caudal; la relación '
                       'entre DI y tamaño de válvula define los reductores.'),
        'umbrales': ('No tiene umbral propio; debe dar velocidades razonables (líquidos 1–3 m/s, '
                     'máximo ≈ 4,5 m/s, práctica habitual). Ejemplos: 2" Sch 40 → 52,5 mm; 4" Sch '
                     '40 → 102,3 mm; 6" Sch 40 → 154,1 mm.'),
        'por_debajo': ('Un DI chico eleva la velocidad, la pérdida de carga y el riesgo de '
                       'erosión.'),
        'por_encima': 'Un DI muy grande respecto a la válvula exige reductores mayores y baja Fp.',
        'ejemplo': ('Tubería de 6" (OD 168,3 mm) Sch 40 con t = 7,11 mm: DI = 168,3 − 2 × 7,11 = '
                    '154,1 mm. Ese valor se usa para calcular la velocidad y Fp con una válvula de'
                    ' 4".'),
        'afecta': [
            'Velocidad en tubería',
            'Factores Fp y FLp',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Número de Mach (gases)',
        ],
        'recomendaciones': [
            'Verificar que NPS y cédula sean los de la especificación de tuberías.',
            'Si la velocidad sale alta, revisar el NPS antes de cambiar la cédula.',
            'En inoxidable usar cédulas S (B36.19M), cuyo DI difiere de las de acero al carbono.',
        ],
    },
    'flujo_masico': {
        'que_es': 'Es la masa de líquido que pasa por unidad de tiempo: W = Q·ρ1.',
        'que_hace': ('Expresa el caudal en masa para la memoria de cálculo y el ruido, y permite '
                     'cotejar con el balance de masa del proceso.'),
        'que_indica': ('No depende de la temperatura como el volumétrico; es el dato más estable '
                       'para comparar con proceso.'),
        'umbrales': ('No hay umbral propio; debe coincidir con el balance de masa de proceso. '
                     'Diferencias mayores a unos pocos por ciento indican un error de densidad o '
                     'de base de caudal.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Agua a 20 °C (ρ ≈ 998 kg/m³) con Q = 50 m³/h: W = 50 × 998 ≈ 49 900 kg/h (≈ '
                    '13,9 kg/s, unas 110 000 lb/h).'),
        'afecta': [
            'Memoria de cálculo',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Hoja de datos',
            'Conversión de caudal volumétrico',
        ],
        'recomendaciones': [
            'Verificar que la densidad ρ1 corresponda a P1 y T1.',
            'Comparar con el balance de masa para detectar errores de unidades.',
            'Cargar caudal mínimo, normal y máximo para cada caso.',
        ],
    },
    'velocidad_tuberia': {
        'que_es': ('Es la velocidad media del líquido en la tubería de entrada y de salida: v = '
                   'Q/A, con A = π·DI²/4.'),
        'que_hace': ('Verifica que las tuberías estén bien dimensionadas para el caudal y detecta '
                     'riesgo de erosión, ruido o golpe de ariete.'),
        'que_indica': ('Velocidades altas indican una línea chica para el caudal; muy bajas, una '
                       'línea grande o riesgo de sedimentación.'),
        'umbrales': ('Práctica habitual para líquidos: 1–3 m/s típico, máximo ≈ 4,5 m/s (≈ 15 '
                     'ft/s); con sólidos o fluidos erosivos ≈ 3 m/s. En succión de bombas suele '
                     'limitarse a ≈ 1–1,5 m/s. Para flujo bifásico, API RP 14E define una '
                     'velocidad erosional.'),
        'por_debajo': 'Por debajo de ≈ 0,9–1 m/s pueden depositarse sólidos en fluidos sucios.',
        'por_encima': ('Por encima de ≈ 4,5 m/s aumentan la erosión, el ruido, la vibración y el '
                       'golpe de ariete al cerrar la válvula.'),
        'ejemplo': ('100 m³/h de agua en 4" Sch 40 (DI = 102,3 mm): A = 0,00822 m², Q = 0,0278 '
                    'm³/s y v ≈ 3,4 m/s, aceptable. En 3" Sch 40 (DI = 77,9 mm) subiría a ≈ 5,8 '
                    'm/s, por encima del límite habitual.'),
        'afecta': [
            'Alerta de velocidad en tubería',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Selección del tamaño de tubería y válvula',
        ],
        'recomendaciones': [
            'Si la velocidad es alta, aumentar el NPS de la tubería.',
            'Usar tiempos de cierre del actuador más lentos si hay riesgo de golpe de ariete.',
            'Con sólidos, limitar a ≈ 3 m/s y elegir materiales resistentes a la erosión.',
        ],
    },
    'velocidad_sonido': {
        'que_es': ('Es la velocidad con que se propaga una onda de presión en el fluido. En gases '
                   'depende de γ, Z, T y M; en líquidos es mucho mayor (agua ≈ 1 480 m/s).'),
        'que_hace': ('En gases se usa para calcular el número de Mach en entrada, salida de '
                     'válvula y tubería de salida, y el ruido aerodinámico; en líquidos, el ruido '
                     'hidrodinámico.'),
        'que_indica': ('Una velocidad del fluido cercana a la del sonido (Mach alto) indica ruido '
                       'elevado y posibles vibraciones.'),
        'umbrales': ('Valores típicos: aire a 20 °C ≈ 343 m/s; gas natural ≈ 400–450 m/s; vapor de'
                     ' agua saturado ≈ 450–500 m/s; agua ≈ 1 400–1 500 m/s (si no hay dato, el '
                     'programa usa 1 400 m/s). Práctica habitual: Mach en la tubería de salida de '
                     'gases ≤ 0,3 (≤ 0,2 donde el ruido es crítico).'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Si la velocidad del gas en la salida se acerca a la del sonido (Mach > '
                       '0,3–0,5), el ruido sube fuertemente y la predicción de ruido pierde '
                       'exactitud.'),
        'ejemplo': ('Aire a 20 °C (γ = 1,4, R = 287 J/kg·K): c = √(1,4 × 287 × 293) ≈ 343 m/s. Si '
                    'el gas sale a 120 m/s, el Mach es 0,35, por encima de la práctica habitual de'
                    ' 0,3, y conviene agrandar la tubería de salida.'),
        'afecta': [
            'Número de Mach',
            'Ruido aerodinámico IEC 60534-8-3',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Alerta de velocidad en salida',
        ],
        'recomendaciones': [
            'Si el Mach de salida es alto, aumentar el diámetro de la tubería de salida.',
            ('Usar un expansor inmediatamente después de la válvula en servicios de gas con gran '
             'expansión.'),
            'Verificar la velocidad del sonido aguas abajo con P2 y T2, no con las de entrada.',
        ],
    },
    'Cv_nominal': {
        'que_es': ('Es la capacidad de paso de la válvula cuando está 100 % abierta: los galones '
                   'US por minuto de agua a 15,6 °C que pasan con una caída de 1 psi. Es un dato '
                   'de catálogo del tamaño y del trim elegidos.'),
        'que_hace': ('Se compara con el Cv requerido por el proceso para saber en qué apertura '
                     'trabajará la válvula y si el tamaño es adecuado. Si se deja en blanco, el '
                     'programa lo estima con Cv ≈ Cd·d<sup>2</sup> (d en pulgadas) según el '
                     'estilo.'),
        'que_indica': ('La relación Cv requerido / Cv nominal dice cuánta reserva tiene la '
                       'válvula: un valor cercano a 1 indica que está casi al límite; uno muy bajo'
                       ' indica que está sobredimensionada y regulará casi cerrada.'),
        'umbrales': ('Práctica habitual (no es requisito de norma): Cv requerido a caudal máximo '
                     'entre ~50 % y 85-90 % del Cv nominal, y el caudal mínimo por encima de ~10 %'
                     ' de apertura. Valores típicos de Cd: globo ≈ 10-14, bola segmentada ≈ 20-30,'
                     ' mariposa ≈ 20-40.'),
        'por_debajo': ('Si el Cv nominal es mucho mayor que el requerido (relación < ~0,3), la '
                       'válvula regula cerca del asiento: pierde resolución, hay erosión del '
                       'asiento por alta velocidad y riesgo de inestabilidad del lazo.'),
        'por_encima': ('Si el Cv requerido supera ~90 % del nominal, no queda margen para aumentos'
                       ' de caudal o errores en los datos; si lo supera, la válvula no puede pasar'
                       ' el caudal pedido.'),
        'ejemplo': ('Una válvula globo de 2 in con Cd ≈ 12 tiene Cv ≈ 12·2<sup>2</sup> = 48. Si el'
                    ' proceso pide Cv = 35 a caudal máximo, la relación es 35/48 ≈ 0,73: hay '
                    'reserva razonable. Si pidiera Cv = 45 (0,94), convendría pasar a 3 in.'),
        'afecta': [
            'Apertura a caudal mínimo, normal y máximo',
            'Selección del tamaño de válvula',
            'Gráfico Cv vs apertura',
            'Rangeabilidad',
            'Alerta de válvula sobredimensionada o subdimensionada',
            'Factor de geometría de tubería Fp',
        ],
        'recomendaciones': [
            ('Para verificar una oferta, ingrese el Cv certificado del proveedor junto con el '
             'diámetro y el trim ofertados.'),
            ('Si la válvula queda sobredimensionada, pruebe un trim reducido en el mismo cuerpo '
             'antes de reducir el tamaño del cuerpo.'),
            ('Si queda al límite, suba un tamaño o elija un estilo de mayor Cd (bola, mariposa) si'
             ' el servicio lo permite.'),
            ('Revise el margen con la característica inherente: con igual porcentaje el Cv crece '
             'rápido en la última parte de la carrera.'),
        ],
    },
    'entregables': {
        'que_es': ('Son los tres documentos que produce el programa: memoria de cálculo, hoja de '
                   'datos e informe técnico. Se ven en sus solapas y se exportan a Word (.docx) o '
                   'se imprimen.'),
        'que_hace': ('Sirven para dejar constancia del dimensionamiento: la memoria justifica los '
                     'cálculos, la hoja de datos sirve para pedir cotización y el informe resume '
                     'alertas y recomendaciones.'),
        'que_indica': ('Lo que muestran es el estado de los datos y resultados en el momento de '
                       'exportar; si un dato está en blanco o es un valor típico, el documento lo '
                       'reflejará así.'),
        'umbrales': ('No hay umbrales numéricos. Buena práctica: exportar solo cuando no queden '
                     'alertas graves sin resolver y revisar que las unidades elegidas sean las del'
                     ' proyecto.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Un ingeniero dimensiona una válvula de gas, ve en el informe técnico una '
                    'alerta de ruido de 92 dBA a 1 m, selecciona el trim de bajo ruido indicado y '
                    'recién entonces exporta la hoja de datos a .docx para enviarla a cotizar con '
                    'el trim correcto.'),
        'afecta': [
            'Memoria de cálculo',
            'Hoja de datos',
            'Informe técnico',
            'Unidades de presentación',
        ],
        'recomendaciones': [
            ('Revise el informe técnico antes de emitir la hoja de datos: las alertas indican qué '
             'corregir.'),
            ('Complete los datos de cuerpo, internos y cierre; los campos vacíos quedan vacíos en '
             'la hoja de datos.'),
            ('Use la memoria de cálculo como respaldo ante la revisión del cliente o del '
             'proveedor.'),
            ('Guarde la versión exportada junto con el archivo de datos para poder rehacer el '
             'cálculo.'),
        ],
    },
    'rating_referencial': {
        'que_es': ('Es un aviso de que la clase de presión (rating) se verificó con la tabla del '
                   'acero al carbono, grupo de materiales 1.1 de ASME B16.34 (por ejemplo A216 WCB'
                   ' o A105), porque todavía no se definió el material del cuerpo.'),
        'que_hace': ('Permite tener una verificación preliminar de la clase (150, 300, 600...) '
                     'aunque falte el material; la verificación definitiva debe hacerse con la '
                     'tabla del grupo del material real.'),
        'que_indica': ('Indica que el resultado de rating es provisional: con otro material la '
                       'presión admisible a la temperatura de diseño puede ser mayor o menor.'),
        'umbrales': ('La alerta aparece siempre que el material del cuerpo no está definido. '
                     'Referencia ASME B16.34, grupo 1.1, clase 150: 19,6 bar a 38 °C y 13,8 bar a '
                     '200 °C; clase 300: 51,1 bar a 38 °C y 43,8 bar a 200 °C.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Diseño: 40 bar a 200 °C. Con el grupo 1.1, clase 300 admite 43,8 bar a 200 '
                    '°C, así que cumple en forma referencial. Si luego se elige inoxidable CF8M '
                    '(grupo 2.2), su admisible a 200 °C en clase 300 es menor y puede no cumplir: '
                    'hay que repetir la verificación.'),
        'afecta': [
            'Verificación de la clase de presión (rating)',
            'Hoja de datos (material y clase)',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Defina el material del cuerpo según la especificación de tuberías del proyecto y '
             'repita la verificación.'),
            ('Tenga en cuenta que el acero inoxidable (grupo 2.2) tiene a veces menor presión '
             'admisible que el acero al carbono a la misma clase y temperatura.'),
            ('Si la presión de diseño está cerca del límite de la clase, prevea la clase '
             'siguiente.'),
        ],
    },
    'rating_fuera_tabla': {
        'que_es': ('Es un aviso de que la temperatura de diseño está fuera del rango de la tabla '
                   'de presión-temperatura que usa el programa, por lo que no puede asignar la '
                   'presión admisible de la clase.'),
        'que_hace': ('Evita aceptar una clase de presión sin respaldo: a temperaturas extremas la '
                     'presión admisible depende fuertemente del material.'),
        'que_indica': ('Indica que el servicio es de alta temperatura (o de baja, criogénico) y '
                       'que el material del cuerpo pasa a ser una decisión de diseño, no un '
                       'detalle.'),
        'umbrales': ('Referencia ASME B16.34: el grupo 1.1 (acero al carbono) llega a 538 °C, pero'
                     ' el acero al carbono no se recomienda para uso prolongado por encima de ~425'
                     ' °C (grafitización). Los aceros Cr-Mo y los inoxidables austeníticos tienen '
                     'tablas hasta mayores temperaturas; por debajo de −29 °C se requieren aceros '
                     'para baja temperatura (por ejemplo LCB/LCC hasta −46 °C) o inoxidables.'),
        'por_debajo': ('Por debajo del rango (servicio criogénico) el acero al carbono puede '
                       'fallar por fractura frágil; se necesitan materiales con ensayo de impacto '
                       'o inoxidables.'),
        'por_encima': ('Por encima del rango la resistencia del material cae y aparece fluencia '
                       'lenta (creep): la clase elegida puede no soportar la presión de diseño.'),
        'ejemplo': ('Una válvula de vapor sobrecalentado a 560 °C supera los 538 °C de la tabla '
                    'del grupo 1.1. Hay que pasar a un acero aleado Cr-Mo o a un inoxidable y '
                    'verificar su presión admisible a 560 °C, que será mucho menor que la nominal '
                    'a 38 °C.'),
        'afecta': [
            'Verificación de la clase de presión (rating)',
            'Selección del material del cuerpo',
            'Hoja de datos',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Defina un material apto para la temperatura (por ejemplo Cr-Mo tipo WC9/C12A o '
             'inoxidable) y verifique con su tabla en ASME B16.34.'),
            'Revise también los límites de temperatura de empaquetadura, juntas y asiento.',
            ('Para alta temperatura considere bonete extendido o con aletas; para criogenia, '
             'bonete extendido criogénico.'),
            'Confirme que la temperatura de diseño no esté sobrestimada con márgenes acumulados.',
        ],
    },
    'conexion_incompatible': {
        'que_es': ('Es un aviso de que la combinación elegida de tipo de conexión (bridada, '
                   'soldada, roscada, wafer, lug), estilo de válvula, diámetro o clase no es la '
                   'que se encuentra habitualmente en el mercado o en las especificaciones de '
                   'tuberías.'),
        'que_hace': ('Ayuda a detectar a tiempo una conexión difícil de conseguir, cara o no '
                     'permitida por la especificación de tuberías del proyecto.'),
        'que_indica': ('Indica que conviene revisar la conexión, no que el cálculo hidráulico esté'
                       ' mal.'),
        'umbrales': ('Práctica habitual: roscado (NPT) y soldadura a enchufe (SW) solo hasta ~2 in'
                     ' (DN 50); wafer y lug típicos de válvulas mariposa; bridas RF habituales '
                     'hasta clase 600 y RTJ frecuentes en clase 900 y superiores; soldadura a tope'
                     ' (BW) en alta presión o servicios críticos.'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Se elige una válvula globo de 6 in clase 600 con conexión roscada: es una '
                    'combinación muy poco habitual. Lo normal sería bridada RF clase 600 o soldada'
                    ' a tope, según la especificación de tuberías.'),
        'afecta': [
            'Hoja de datos (conexiones)',
            'Informe técnico',
            'Selección de estilo y tamaño',
        ],
        'recomendaciones': [
            'Contraste la conexión con la especificación de tuberías (piping class) del proyecto.',
            'En diámetros mayores a 2 in prefiera bridas o soldadura a tope en lugar de roscas.',
            ('Evite cuerpos wafer en servicios inflamables o de alta temperatura si la '
             'especificación lo prohíbe; use lug o bridado.'),
            'Consulte a más de un proveedor si la combinación es realmente necesaria.',
        ],
    },
    'conexion_info': {
        'que_es': ('Es una observación informativa sobre la conexión elegida (por ejemplo, el tipo'
                   ' de cara de brida o una limitación de montaje). No impide la selección.'),
        'que_hace': ('Llama la atención sobre un detalle de la conexión que conviene confirmar al '
                     'emitir la hoja de datos.'),
        'que_indica': 'Indica un punto a revisar, no un error.',
        'umbrales': ('No hay umbral numérico: la observación aparece por combinaciones típicas que'
                     ' merecen confirmación. Buena práctica: que la conexión de la válvula '
                     'coincida exactamente con la de la tubería (tipo, clase, cara y norma de '
                     'brida).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Se elige una mariposa wafer de 8 in: el programa observa que queda montada '
                    'entre bridas con espárragos pasantes, por lo que no permite desmontar la '
                    'tubería aguas abajo con la línea presurizada. Si se necesita, conviene un '
                    'cuerpo lug.'),
        'afecta': [
            'Hoja de datos (conexiones)',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Verifique la cara de brida (RF, FF, RTJ) y la norma de bridas (por ejemplo ASME '
             'B16.5) con la tubería.'),
            'Confirme la longitud entre caras si la válvula reemplaza a otra existente.',
            'Para wafer o lug, revise los espárragos y el centrado entre bridas.',
        ],
    },
    'valvula_mayor_linea': {
        'que_es': ('Es una alerta de que el diámetro de válvula calculado es mayor que el diámetro'
                   ' de la tubería donde se instala.'),
        'que_hace': ('Detecta datos de proceso o de línea inconsistentes: en una instalación '
                     'normal la válvula es igual o menor que la tubería.'),
        'que_indica': ('Indica que la tubería es chica para el caudal (velocidad alta) o que el '
                       'estilo elegido tiene poca capacidad (Cd bajo) para la caída de presión '
                       'disponible.'),
        'umbrales': ('La alerta aparece cuando el diámetro de la válvula supera el de la tubería. '
                     'Práctica habitual: válvula igual a la línea o hasta 1-2 tamaños menor.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Una válvula mayor que la línea obliga a expansiones, encarece la '
                       'instalación y suele revelar una caída de presión asignada a la válvula '
                       'demasiado baja.'),
        'ejemplo': ('Agua a 200 m³/h en una línea de 4 in con solo 0,2 bar disponibles para la '
                    'válvula da Cv ≈ 520, que exige una globo de 6 in. La línea de 4 in lleva unos'
                    ' 6,8 m/s, muy alta: lo correcto es revisar la tubería o asignar más ΔP a la '
                    'válvula.'),
        'afecta': [
            'Selección del tamaño de válvula',
            'Factor de geometría de tubería Fp',
            'Velocidad en tubería',
            'Hoja de datos',
        ],
        'recomendaciones': [
            ('Revise la caída de presión asignada a la válvula: con muy poco ΔP el Cv requerido se'
             ' dispara.'),
            ('Verifique el diámetro de la tubería y la velocidad; puede que la línea esté '
             'subdimensionada.'),
            'Pruebe un estilo de mayor capacidad (bola o mariposa) si el servicio lo permite.',
            ('Confirme las unidades del caudal y la densidad: un error de unidades produce este '
             'síntoma.'),
        ],
    },
    'valvula_chica_linea': {
        'que_es': ('Es una alerta de que la válvula es mucho menor que la tubería, con reductores '
                   'grandes a la entrada y a la salida.'),
        'que_hace': ('Advierte que los reductores modifican el comportamiento: bajan la capacidad '
                     'efectiva (Fp) y el FL efectivo (FLP), y la válvula queda con alta velocidad '
                     'interna.'),
        'que_indica': ('Indica que la válvula trabaja con mucha caída propia o que la línea está '
                       'sobredimensionada respecto del caudal.'),
        'umbrales': ('Práctica habitual: válvula no menor que la mitad del diámetro de la línea '
                     '(d/D ≥ ~0,5). Con d/D más chico los efectos de los reductores crecen y '
                     'conviene verificar velocidades, soportes y vibración.'),
        'por_debajo': ('Por debajo de d/D ≈ 0,5 crecen las pérdidas en reductores, el ruido de '
                       'salida por alta velocidad y las cargas sobre la válvula, que queda como '
                       'punto débil y sin soporte propio.'),
        'por_encima': 'No aplica.',
        'ejemplo': ('Una válvula de 2 in en una línea de 8 in tiene d/D = 0,25. Los reductores '
                    'bajan el Cv efectivo con el factor Fp y el gas sale de la válvula a velocidad'
                    ' mucho mayor que en la tubería; una válvula de 4 in con trim reducido suele '
                    'ser mejor elección.'),
        'afecta': [
            'Factor de geometría de tubería Fp',
            'FL efectivo con reductores (FLP)',
            'xTP con reductores',
            'Velocidad y Mach en la salida',
            'Ruido aerodinámico IEC 60534-8-3',
            'Cv requerido',
        ],
        'recomendaciones': [
            'Confirme que la velocidad en la salida de la válvula esté dentro de lo recomendado.',
            'Use reductores concéntricos cortos y prevea soportes cercanos a la válvula.',
            ('Si la línea está sobredimensionada solo para este tramo, evalúe reducir la línea '
             'alrededor de la válvula.'),
            ('Considere un estilo de menor capacidad específica (globo) en un tamaño mayor, con '
             'trim reducido.'),
        ],
    },
    'tamano_estilo': {
        'que_es': ('Es un aviso de que el diámetro elegido está fuera del rango en que ese estilo '
                   'de válvula se fabrica habitualmente.'),
        'que_hace': ('Evita especificar una válvula que pocos o ningún proveedor fabrica, con '
                     'plazos y costos altos.'),
        'que_indica': ('Indica que conviene cambiar de estilo o de tamaño, no que el cálculo '
                       'hidráulico sea incorrecto.'),
        'umbrales': ('Práctica habitual aproximada: globo de 1/2 in a ~16-24 in (DN 15 a 400-600);'
                     ' bola de 1 in a 24 in o más; mariposa de alto rendimiento desde 2-3 in hasta'
                     ' 48 in o más; angulares y de microcaudal en tamaños pequeños.'),
        'por_debajo': ('Por debajo del rango típico del estilo (por ejemplo una mariposa de 1 in) '
                       'el estilo pierde sus ventajas y puede no existir.'),
        'por_encima': ('Por encima del rango típico (por ejemplo una globo de 30 in) la válvula es'
                       ' muy pesada, cara y requiere actuadores muy grandes.'),
        'ejemplo': ('Se pide una válvula mariposa de 1 in para un caudal pequeño de aire: es poco '
                    'habitual. Una globo de 1 in con trim reducido resuelve el mismo servicio con '
                    'mejor control.'),
        'afecta': [
            'Selección del estilo y tamaño',
            'Cd típico del estilo (Cv estimado)',
            'Hoja de datos',
        ],
        'recomendaciones': [
            'Para diámetros grandes con poca caída de presión, considere mariposa o bola.',
            ('Para caudales pequeños use globo o válvulas de microcaudal en lugar de bola o '
             'mariposa.'),
            ('Si el estilo es obligatorio, consulte disponibilidad con varios fabricantes antes de'
             ' fijarlo.'),
        ],
    },
    'cierre_estilo': {
        'que_es': ('Es una alerta de que la clase de fuga en cierre pedida (ANSI/FCI 70-2, clases '
                   'II a VI) no la alcanza normalmente el estilo de válvula elegido.'),
        'que_hace': ('Señala que la combinación estilo-clase de cierre puede ser inviable o '
                     'requerir internos especiales y costosos.'),
        'que_indica': ('Indica que hay que revisar si la clase pedida es realmente necesaria o '
                       'cambiar de estilo o de tipo de asiento.'),
        'umbrales': ('ANSI/FCI 70-2: clase IV admite 0,01 % del Cv nominal; clase V, '
                     '5·10<sup>−4</sup> mL/min de agua por pulgada de diámetro de puerto y por '
                     'psi; clase VI, burbujas por minuto según el diámetro (por ejemplo 1 '
                     'burbuja/min en 1 in). Práctica habitual: globo metal-metal clase IV (V con '
                     'diseños especiales); clase VI normalmente con asiento blando.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Si se pide una clase más estricta que la que el estilo logra, la válvula '
                       'no pasará la prueba de fuga en fábrica o necesitará un diseño especial.'),
        'ejemplo': ('Se pide clase VI en una bola segmentada metal-metal de 4 in: lo habitual en '
                    'ese estilo es clase IV (fuga ≤ 0,01 % del Cv nominal, por ejemplo 0,04 gpm '
                    'con Cv = 400 en la prueba). Para clase VI se requiere otro estilo o asiento '
                    'blando.'),
        'afecta': [
            'Clase de cierre en hoja de datos',
            'Selección de estilo e internos',
            'Fuerza del actuador (carga de asiento)',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Pida solo la clase que el proceso necesita: una válvula de control no reemplaza a '
             'una válvula de bloqueo.'),
            ('Si se necesita clase VI, use asiento blando dentro de su límite de temperatura, o un'
             ' diseño metal-metal especial.'),
            ('Para clase V en metal-metal, prevea mayor carga de asiento y por lo tanto un '
             'actuador mayor.'),
            'Si el cierre hermético es crítico, considere una válvula de bloqueo en serie.',
        ],
    },
    'cierre_info': {
        'que_es': ('Es una observación informativa sobre la clase de cierre elegida, por ejemplo '
                   'sobre su costo, la carga de asiento necesaria o el método de prueba.'),
        'que_hace': ('Recuerda detalles de la clase de fuga (ANSI/FCI 70-2) que conviene tener en '
                     'cuenta al especificar, sin bloquear la selección.'),
        'que_indica': 'Indica un punto a confirmar, no un error.',
        'umbrales': ('No hay umbral: aparece con clases que tienen implicancias prácticas. '
                     'Referencia: clases II (0,5 % Cv), III (0,1 % Cv), IV (0,01 % Cv), V (agua, '
                     'por pulgada de puerto y psi) y VI (burbujas/min con aire o nitrógeno).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Se elige clase V en una globo de 3 in: el programa observa que requiere mayor'
                    ' carga de asiento. La fuga admisible es 5·10<sup>−4</sup> mL/min por pulgada '
                    'y por psi, es decir con 3 in y 100 psi unos 0,15 mL/min de agua.'),
        'afecta': [
            'Clase de cierre en hoja de datos',
            'Fuerza del actuador',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Verifique que la clase de cierre sea coherente con la función (control o control con'
             ' cierre).'),
            'Recuerde que una clase más estricta pide más fuerza de actuador y aumenta el costo.',
            ('Indique en la hoja de datos el fluido y la presión de prueba si difieren de los de '
             'la norma.'),
        ],
    },
    'cierre_temperatura': {
        'que_es': ('Es una alerta de que la clase de cierre requiere un asiento blando o un '
                   'revestimiento (por ejemplo PTFE o elastómero) cuyo límite de temperatura es '
                   'menor que la temperatura de diseño.'),
        'que_hace': ('Evita especificar un asiento que se deformará o degradará en servicio y '
                     'perderá el cierre.'),
        'que_indica': ('Indica que el asiento blando no es apto a esa temperatura y hay que pasar '
                       'a un cierre metal-metal.'),
        'umbrales': ('Límites aproximados (práctica habitual, dependen del fabricante y la '
                     'presión): NBR ~100 °C, EPDM ~120-150 °C, PTFE ~200-230 °C, PTFE cargado '
                     '~230-260 °C, PEEK ~260-300 °C. La alerta se dispara cuando la temperatura de'
                     ' diseño supera el límite del material blando.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Por encima del límite el material blando fluye en frío, se endurece o se '
                       'degrada, y la fuga aumenta rápidamente.'),
        'ejemplo': ('Vapor a 250 °C con clase VI y asiento de PTFE: el PTFE no es apto por encima '
                    'de ~230 °C. La solución típica es asiento metálico con clase V, o un diseño '
                    'metal-metal especial si se necesita clase VI.'),
        'afecta': [
            'Clase de cierre en hoja de datos',
            'Material del asiento',
            'Selección de estilo',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Use asiento metálico o un estilo con cierre metal-metal y acepte clase IV o V si el '
             'proceso lo permite.'),
            ('Si se necesita alta estanqueidad a alta temperatura, consulte diseños metal-metal '
             'especiales o válvulas de bloqueo adicionales.'),
            'Confirme que la temperatura de diseño no esté sobrestimada.',
            'Revise también los límites de empaquetadura y juntas.',
        ],
    },
    'velocidad_tuberia_alta': {
        'que_es': ('Es una alerta de que la velocidad del fluido en la tubería de entrada o de '
                   'salida supera los valores recomendados.'),
        'que_hace': ('Detecta líneas subdimensionadas o caudales mayores que los previstos, que '
                     'causan ruido, vibración, erosión y caída de presión excesiva.'),
        'que_indica': ('Indica que el problema puede estar en la tubería más que en la válvula; '
                       'ver también «Velocidad en tubería».'),
        'umbrales': ('Práctica habitual: líquidos 1-3 m/s (3-10 ft/s), hasta ~4,5 m/s en '
                     'descargas; gases ~20-30 m/s o Ma ≤ 0,3; vapor saturado ~25-35 m/s y '
                     'sobrecalentado ~35-60 m/s. En flujo bifásico API RP 14E fija la velocidad '
                     'erosional Ve = C/√ρ<sub>m</sub> (unidades imperiales, C ≈ 100 en servicio '
                     'continuo).'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Por encima de lo recomendado aumentan el ruido, la vibración, la erosión '
                       '(sobre todo con gotas o sólidos) y las pérdidas de carga.'),
        'ejemplo': ('Agua a 100 m³/h en una línea de 3 in (Di ≈ 78 mm) tiene v ≈ 5,8 m/s, '
                    'demasiado alta. Pasando a 4 in (Di ≈ 102 mm) baja a ≈ 3,4 m/s, dentro de lo '
                    'habitual.'),
        'afecta': [
            'Velocidad en tubería',
            'Número de Mach aguas arriba y aguas abajo',
            'Ruido aerodinámico IEC 60534-8-3',
            'Factor Fp (cuando se aumenta la línea)',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Aumente el diámetro de la tubería, especialmente aguas abajo en gases, donde la '
             'densidad cae.'),
            'Verifique que el caudal máximo y las unidades sean correctos.',
            ('En vapor húmedo o fluidos con sólidos, use límites más bajos y materiales '
             'resistentes a la erosión.'),
            ('Coloque expansiones aguas abajo cerca de la válvula en servicios de gas con gran '
             'caída de presión.'),
        ],
    },
    'T2': {
        'que_es': ('Es la temperatura del fluido aguas abajo de la válvula, en la tubería de '
                   'salida.'),
        'que_hace': ('Se usa para calcular la densidad y la velocidad del sonido a la salida, que '
                     'intervienen en el número de Mach, la velocidad y el ruido aerodinámico. En '
                     'fluidos de la lista se calcula con h(P2,T2) = h(P1,T1); con gas definido por'
                     ' el usuario, en blanco se toma T2 = T1.'),
        'que_indica': ('Si T2 es menor que T1 en un gas, muestra el enfriamiento Joule-Thomson; en'
                       ' vapor de agua, si T2 queda por encima de la saturación a P2, el vapor '
                       'sale sobrecalentado.'),
        'umbrales': ('No hay un umbral de norma; es un resultado termodinámico. Orden de magnitud:'
                     ' en gas natural el enfriamiento Joule-Thomson es de ~0,4-0,6 °C por bar de '
                     'caída; en aire ~0,25 °C/bar; un gas ideal no cambia de temperatura.'),
        'por_debajo': ('Una T2 muy baja puede formar hidratos en gas natural, condensar líquidos o'
                       ' bajar del límite de temperatura mínima del material (por ejemplo −29 °C '
                       'para acero al carbono).'),
        'por_encima': ('Una T2 alta es poco común en el estrangulamiento; si aparece, revise los '
                       'datos (en algunos gases como el hidrógeno la temperatura sube levemente).'),
        'ejemplo': ('Gas natural a 70 bar y 20 °C que se reduce a 20 bar: con ~0,5 °C/bar se '
                    'enfría unos 25 °C y sale a ≈ −5 °C. Esa temperatura puede formar hidratos y '
                    'debe considerarse para el material y para un posible calentador aguas arriba.'),
        'afecta': [
            'Densidad de salida ρ2',
            'Velocidad del sonido a la salida',
            'Número de Mach',
            'Ruido aerodinámico IEC 60534-8-3',
            'Sobrecalentamiento a P2',
            'Verificación de temperatura mínima del material',
        ],
        'recomendaciones': [
            ('Use un fluido de la lista cuando exista, para que T2 incluya el efecto '
             'Joule-Thomson.'),
            ('En gas natural con gran caída de presión verifique riesgo de hidratos y, si hace '
             'falta, precaliente aguas arriba.'),
            'Confirme que el material del cuerpo y de la tubería aguas abajo admita la T2 mínima.',
            ('Con gas definido por el usuario y caídas grandes, ingrese T2 si la conoce de un '
             'simulador de procesos.'),
        ],
    },
    'rho2': {
        'que_es': ('Es la densidad del fluido aguas abajo de la válvula, evaluada a la presión P2 '
                   'y la temperatura T2.'),
        'que_hace': ('Se usa para calcular la velocidad del fluido en la salida de la válvula y en'
                     ' la tubería de salida, el número de Mach y el ruido aerodinámico según IEC '
                     '60534-8-3.'),
        'que_indica': ('Una densidad de salida mucho menor que la de entrada indica gran expansión'
                       ' del gas: el mismo caudal másico ocupa más volumen y se mueve más rápido '
                       'aguas abajo.'),
        'umbrales': ('No tiene umbral propio; es un resultado. En gas ideal ρ2/ρ1 ≈ '
                     '(P2/P1)·(T1/T2): si la presión baja a la mitad, la densidad baja '
                     'aproximadamente a la mitad.'),
        'por_debajo': ('Una ρ2 baja eleva la velocidad y el Mach de salida, y con ellos el ruido y'
                       ' la vibración.'),
        'por_encima': 'No aplica.',
        'ejemplo': ('Aire a 7 bar(a) y 20 °C tiene ρ1 ≈ 8,3 kg/m³. Si sale a 3 bar(a) con T2 ≈ T1,'
                    ' ρ2 ≈ 3,6 kg/m³: el caudal volumétrico aguas abajo es unas 2,3 veces mayor '
                    'que aguas arriba, y la velocidad crece en la misma proporción.'),
        'afecta': [
            'Velocidad en la salida de la válvula y aguas abajo',
            'Número de Mach',
            'Ruido aerodinámico IEC 60534-8-3',
            'Alerta de velocidad alta en tubería',
        ],
        'recomendaciones': [
            ('Use un fluido de la lista o IAPWS-95 en vapor de agua para obtener ρ2 real con su '
             'factor Z.'),
            ('Si la densidad cae mucho, aumente el diámetro de la tubería de salida para controlar'
             ' la velocidad.'),
            ('En vapores definidos por el usuario, ingrese ρ2 si la conoce en lugar de usar la '
             'aproximación.'),
        ],
    },
    'anticav': {
        'que_es': ('Es el trim que se usa en líquidos para controlar la cavitación: el estándar elegido, una '
                   'jaula de orificios chicos de una etapa, o un multietapa de 2, 3, 4 o 6 etapas.'),
        'que_hace': ('Reemplaza FL, Fd y Kc de las condiciones de operación, reparte la caída en etapas con '
                     'igual Kapp por etapa, calcula el ruido con la última etapa y cambia el Cv por tamaño.'),
        'que_indica': ('Con el Kapp por etapa y las etapas recomendadas se ve si el trim elegido alcanza, '
                       'cuántas etapas hacen falta sin cavitación y cuántas aceptando cavitación incipiente.'),
        'umbrales': ('Por etapa: sin cavitación Kapp ≤ 0,50; cavitación incipiente aceptada Kapp ≤ 0,63 '
                     '(0,9·Kc de etapa 0,70); cavitación constante a partir de 0,70.'),
        'por_debajo': 'Menos etapas que las recomendadas: cada etapa cavita o queda sin margen.',
        'por_encima': ('Más etapas que las necesarias: más costo y menos capacidad por pulgada (válvula '
                       'más grande).'),
        'ejemplo': ('P1 = 40 bar a, P2 = 4 bar a, Pv ≈ 0,07 bar a: Kapp = 0,90. Con 3 etapas cada una toma '
                    'k = 1 − (3,93/39,93)^(1/3) = 0,54 (incipiente); con 4 etapas k = 0,44 (sin '
                    'cavitación). El programa recomienda 4, mínimo 3.'),
        'afecta': [
            'Kc, FL y Fd de cada caso',
            'ΔP de cavitación y ΔP de flujo estrangulado',
            'Ruido hidrodinámico IEC 60534-8-4',
            'Cv nominal por tamaño y diámetro automático',
            'Selección de trim y recomendaciones',
        ],
        'recomendaciones': [
            'Empiece con el estándar y siga la alerta de etapas recomendadas.',
            'Elija la cantidad sin cavitación en servicio continuo con agua y ΔP alta.',
            'Reemplace FL, Fd y Kc por los certificados del trim ofertado.',
            ('Si ninguna cantidad de la lista alcanza, reparta la caída con una placa de restricción o dos '
             'válvulas en serie.'),
        ],
    },
    'anticav_insuficiente': {
        'que_es': 'Es la alerta de que el trim multietapa elegido tiene menos etapas que las necesarias.',
        'que_hace': 'Compara el Kapp por etapa con 0,9·Kc de etapa (0,63) en cada caso.',
        'que_indica': 'Cada etapa trabaja sin margen: puede cavitar con pequeños cambios de operación.',
        'umbrales': 'Advertencia con Kapp por etapa entre 0,63 y 0,70; crítica desde 0,70.',
        'por_debajo': 'Por debajo de 0,63 por etapa la alerta no aparece.',
        'por_encima': 'Desde 0,70 por etapa hay cavitación constante en cada etapa.',
        'ejemplo': 'Kapp 0,90 con 2 etapas: k = 0,69 por etapa; hacen falta al menos 3.',
        'afecta': ['Selección del trim anticavitación', 'Vida útil de los internos'],
        'recomendaciones': ['Suba a la cantidad de etapas que indica la alerta.',
                            'Confirme con el fabricante el Kc certificado.'],
    },
    'anticav_etapas': {
        'que_es': 'Es el aviso con las etapas anticavitación necesarias para el servicio.',
        'que_hace': ('Calcula la menor cantidad de etapas con Kapp por etapa ≤ 0,50 (sin cavitación) y ≤ 0,63 '
                     '(incipiente aceptada).'),
        'que_indica': 'Cuántas etapas pedir al fabricante.',
        'umbrales': 'Una etapa alcanza si Kapp ≤ 0,50 (sin cavitación) o ≤ 0,63 (incipiente).',
        'por_debajo': 'Con Kapp bajo no hace falta multietapa.',
        'por_encima': 'Si la cantidad supera 6, conviene repartir la caída fuera de la válvula.',
        'ejemplo': 'Kapp 0,90: sin cavitación 4 etapas, mínimo 3.',
        'afecta': ['Selección del trim anticavitación', 'Recomendaciones'],
        'recomendaciones': ['Elija el trim en «Datos para cavitación hidrodinámica».'],
    },
    'anticav_rotativa': {
        'que_es': 'Es el aviso de que el trim anticavitación elegido no corresponde a un cuerpo rotativo.',
        'que_hace': 'El cálculo vuelve al trim estándar.',
        'que_indica': 'Para usar un trim anticavitación hay que cambiar el cuerpo a globo o angular.',
        'umbrales': 'No aplica.',
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': 'Mariposa con «Multietapa, 3 etapas»: se calcula con el trim estándar.',
        'afecta': ['Cálculo de cavitación y ruido'],
        'recomendaciones': ['Cambie el cuerpo a globo o angular en 1-Sistema.'],
    },
    'trim_ruido': {
        'que_es': ('Es el tipo de internos (trim) que el programa considera para estimar el ruido '
                   'aerodinámico: estándar de un solo pasaje, o jaula multiorificio de nivel 1, 2 '
                   'o 3.'),
        'que_hace': ('Define el modificador de estilo Fd, que fija el diámetro del chorro en IEC '
                     '60534-8-3: chorros más chicos generan ruido de mayor frecuencia, que la '
                     'pared de la tubería atenúa más.'),
        'que_indica': ('Cuanto mayor el nivel (más orificios, menor Fd), menor el ruido esperado '
                       'fuera de la tubería, a costa de mayor costo y de trim más sensible a la '
                       'suciedad.'),
        'umbrales': ('Según IEC 60534-2-1 Anexo A, Fd = 1/√No. Niveles del programa: nivel 1 ≈ 50 '
                     'orificios (Fd ≈ 0,14), nivel 2 ≈ 200 (Fd ≈ 0,071), nivel 3 ≈ 800 (Fd ≈ '
                     '0,035). El trim estándar usa el Fd del estilo (del orden de 0,3 a 1).'),
        'por_debajo': 'No aplica.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Una jaula con 200 orificios iguales tiene Fd = 1/√200 ≈ 0,071. Frente a un '
                    'trim estándar con Fd ≈ 0,4, el chorro es mucho más fino, el pico de ruido '
                    'sube de frecuencia y la pared de la tubería lo atenúa más; con datos típicos '
                    'la reducción puede ser del orden de 10 dBA.'),
        'afecta': [
            'Ruido aerodinámico IEC 60534-8-3',
            'Frecuencia pico del ruido',
            'Pérdida de transmisión de la pared',
            'Nivel de trim de bajo ruido requerido',
        ],
        'recomendaciones': [
            'Empiece con trim estándar y suba de nivel solo si el ruido supera el límite.',
            ('En fluidos sucios o con sólidos, evite orificios muy pequeños o prevea filtros aguas'
             ' arriba.'),
            ('Si ningún nivel cumple, use trim multietapa, silenciador en línea o placa difusora '
             'aguas abajo.'),
            ('Combine el trim con una tubería de mayor espesor o aislación acústica si falta poco '
             'para cumplir.'),
        ],
    },
    'nivel_trim': {
        'que_es': ('Es el primer trim de bajo ruido de la lista (jaula multiorificio nivel 1 a 3, '
                   'multietapa multiorificio de 2 a 4 etapas, discos apilados de 4 a 10 etapas) '
                   'que deja el ruido de la válvula a 1 m por debajo del ruido permitido.'),
        'que_hace': ('El programa repite el cálculo de ruido con trim estándar y con cada nivel, y'
                     ' sugiere el mínimo necesario para cumplir el límite.'),
        'que_indica': ('«No requerido» significa que el trim estándar ya cumple; un nivel alto '
                       'indica un servicio ruidoso; «Silenciador o difusor» indica que ningún trim '
                       'de la lista alcanza.'),
        'umbrales': ('El umbral es el ruido permitido ingresado. Práctica habitual: 85 dBA a 1 m '
                     'en áreas de proceso (muchas especificaciones de proyecto), 80 dBA o menos '
                     'cerca de oficinas o salas de control.'),
        'por_debajo': 'No aplica.',
        'por_encima': ('Si ni los discos apilados de 10 etapas cumplen, el exceso de ruido debe '
                       'resolverse con difusor, silenciador, aislación acústica o repartiendo la '
                       'caída de presión.'),
        'ejemplo': ('Valores ilustrativos: con límite de 85 dBA, el trim estándar da 98 dBA, el '
                    'nivel 1 da 90 dBA y el nivel 2 da 83 dBA. El programa informa «Nivel 2».'),
        'afecta': [
            'Selección de internos',
            'Ruido aerodinámico IEC 60534-8-3',
            'Hoja de datos (tipo de trim)',
            'Informe técnico',
        ],
        'recomendaciones': [
            ('Elija el nivel sugerido, no uno mayor: más orificios implica más costo y más riesgo '
             'de taponamiento.'),
            ('Si hace falta multietapa, reparta la caída de presión en etapas o en dos válvulas en'
             ' serie.'),
            ('Aumentar el espesor de la tubería de salida (schedule) o aislarla acústicamente suma'
             ' atenuación.'),
            'Revise que el límite ingresado sea el del proyecto y a la distancia correcta.',
        ],
    },
    'ruido_componentes': {
        'que_es': ('Son las dos fuentes de ruido aerodinámico que separa IEC 60534-8-3: el ruido '
                   'del trim (chorro tras la vena contracta) y el ruido de la salida de la válvula'
                   ' (expansión del flujo en la salida del cuerpo).'),
        'que_hace': ('Permiten saber cuál de las dos fuentes domina para elegir la solución '
                     'correcta: un trim de bajo ruido no reduce el ruido de salida.'),
        'que_indica': ('Si domina el trim, la solución es el trim; si domina la salida, el '
                       'problema es la velocidad en la salida del cuerpo y la tubería aguas abajo.'
                       ' Se suman en energía: LpA = 10·lg(10<sup>Ltrim/10</sup> + '
                       '10<sup>Lsalida/10</sup>).'),
        'umbrales': ('La norma considera el ruido de salida cuando el Mach en la tubería de salida'
                     ' supera 0,3; si no, se muestra «—». Dos fuentes iguales suman +3 dB; si una '
                     'es 10 dB menor, aporta solo ~0,4 dB.'),
        'por_debajo': ('Si el Mach de salida es ≤ 0,3, el ruido de salida no se considera y todo '
                       'el ruido proviene del trim.'),
        'por_encima': ('Si el ruido de salida es comparable o mayor que el del trim, mejorar el '
                       'trim sirve poco: hay que bajar la velocidad de salida.'),
        'ejemplo': ('Ltrim = 88 dBA y Lsalida = 85 dBA dan LpA = 10·lg(10<sup>8,8</sup> + '
                    '10<sup>8,5</sup>) ≈ 89,8 dBA. Aunque se elimine todo el ruido del trim, '
                    'quedarían 85 dBA de la salida.'),
        'afecta': [
            'Ruido aerodinámico total LpA a 1 m',
            'Nivel de trim de bajo ruido requerido',
            'Alerta de ruido',
            'Selección de diámetro de salida',
        ],
        'recomendaciones': [
            'Identifique la fuente dominante antes de elegir la solución.',
            ('Si domina la salida, aumente el diámetro de la válvula o de la tubería de salida '
             '(salida expandida).'),
            'Si domina el trim, use jaula multiorificio o multietapa.',
            'Mantenga el Mach de la tubería de salida por debajo de 0,3 en servicios sensibles.',
        ],
    },
    'Rn': {
        'que_es': ('Es la distancia desde la pared exterior de la tubería hasta el punto donde se '
                   'quiere conocer el ruido, por ejemplo un puesto de trabajo.'),
        'que_hace': ('La norma da el nivel a 1 m; para otra distancia el programa corrige como '
                     'fuente lineal: LpA(Rn) = LpA(1 m) − 10·lg((De + 2·Rn)/(De + 2)).'),
        'que_indica': ('Al alejarse de la tubería el ruido baja aproximadamente 3 dB cada vez que '
                       'se duplica la distancia (fuente lineal), menos que una fuente puntual (6 '
                       'dB).'),
        'umbrales': ('Valor típico de la norma: 1 m. Práctica habitual: usar la distancia real del'
                     ' puesto de trabajo o del límite especificado (normalmente 1 m).'),
        'por_debajo': ('Una Rn menor que 1 m da un nivel mayor que el valor a 1 m; acercarse mucho'
                       ' no es representativo del método.'),
        'por_encima': ('Una Rn grande da un nivel menor, pero no debe usarse para "cumplir" un '
                       'límite que el proyecto exige a 1 m.'),
        'ejemplo': ('Tubería de 8 in con De ≈ 0,219 m y 90 dBA a 1 m. A Rn = 3 m: 10·lg((0,219 + '
                    '6)/(0,219 + 2)) ≈ 4,5 dB, así que el nivel es ≈ 85,5 dBA.'),
        'afecta': [
            'Ruido aerodinámico a la distancia Rn',
            'Alerta de ruido',
            'Nivel de trim de bajo ruido requerido',
        ],
        'recomendaciones': [
            'Use 1 m salvo que la especificación pida otra distancia.',
            'Compare siempre con el límite expresado a la misma distancia.',
            ('Recuerde que la corrección no incluye reflexiones de paredes cercanas, que pueden '
             'aumentar el nivel.'),
        ],
    },
    'area_salida': {
        'que_es': 'Es el área de paso en la brida de salida del cuerpo de la válvula.',
        'que_hace': ('Define la velocidad y el número de Mach en la salida de la válvula y el '
                     'diámetro de salida que usa el cálculo de ruido de salida de IEC 60534-8-3. '
                     'En Automático sale de la tabla ASME B36.10M / B36.19M con el diámetro de la válvula '
                     'y la cédula de salida; en Manual se carga el área certificada.'),
        'que_indica': ('Un área chica implica velocidad y Mach altos en la salida; un área mayor '
                       '(salida expandida) los reduce.'),
        'umbrales': ('No tiene umbral propio; su efecto se juzga por el Mach de salida resultante.'
                     ' Práctica habitual: Ma ≤ 0,3 en la salida para servicios sensibles al ruido '
                     'y ≤ 0,5 como máximo.'),
        'por_debajo': ('Si se ingresa un área menor que la real, el programa sobrestimará la '
                       'velocidad y el ruido de salida.'),
        'por_encima': ('Si se ingresa un área mayor que la real, subestimará la velocidad, el Mach'
                       ' y el ruido.'),
        'ejemplo': ('Una válvula de 4 in (salida ≈ 102 mm, A ≈ 8,2·10<sup>−3</sup> m²) con 1,2 '
                    'm³/s de gas a la salida tiene v ≈ 146 m/s y Ma ≈ 0,43 (c ≈ 343 m/s). Con '
                    'salida expandida a 6 in (A ≈ 1,86·10<sup>−2</sup> m²) baja a v ≈ 64 m/s y Ma '
                    '≈ 0,19.'),
        'afecta': [
            'Velocidad en la salida de la válvula',
            'Número de Mach en la salida',
            'Ruido de salida IEC 60534-8-3',
            'Ruido aerodinámico total',
        ],
        'recomendaciones': [
            ('Tome el área de los datos del fabricante en válvulas con salida expandida o '
             'reducida.'),
            ('Si el Mach de salida es alto, evalúe una válvula con salida expandida o un tamaño '
             'mayor.'),
            'Deje el campo en blanco solo si la salida coincide con el diámetro nominal.',
        ],
    },
    'mach': {
        'que_es': ('Es la relación entre la velocidad del fluido y la velocidad del sonido en ese '
                   'punto: Ma = v/c. El programa lo informa aguas arriba, en la salida de la '
                   'válvula y aguas abajo.'),
        'que_hace': ('Se usa para juzgar si las velocidades de gas o vapor son aceptables y para '
                     'decidir si se considera el ruido de salida de IEC 60534-8-3.'),
        'que_indica': ('Valores bajos (< 0,3) indican flujo tranquilo; al acercarse a 1 el flujo '
                       'se vuelve sónico, con fuerte ruido, vibración y erosión.'),
        'umbrales': ('Práctica habitual: en la salida de la válvula Ma ≤ 0,3 para servicios '
                     'sensibles al ruido y ≤ 0,5 como máximo; en tuberías Ma ≤ 0,3 (≤ 0,2 en vapor'
                     ' de agua). IEC 60534-8-3 considera el ruido de salida cuando el Mach en la '
                     'tubería de salida supera 0,3.'),
        'por_debajo': ('Por debajo de los límites no hay problema de velocidad; un Mach muy bajo '
                       'puede indicar tubería sobredimensionada (más costo).'),
        'por_encima': ('Por encima aumentan el ruido de salida, la vibración de la tubería, la '
                       'erosión y la caída de presión.'),
        'ejemplo': ('Aire a 3 bar(a) y 20 °C tiene c = √(1,4·287·293) ≈ 343 m/s. Si en la salida '
                    'de la válvula circula a 120 m/s, Ma ≈ 0,35: aceptable como máximo, pero por '
                    'encima de 0,3 recomendado para servicios sensibles al ruido.'),
        'afecta': [
            'Ruido de salida IEC 60534-8-3',
            'Ruido aerodinámico total',
            'Alerta de velocidad alta',
            'Selección del diámetro de válvula y de tubería de salida',
        ],
        'recomendaciones': [
            'Aumente el diámetro de la tubería de salida o use una válvula con salida expandida.',
            ('Reparta grandes caídas de presión en dos etapas para no tener gas muy expandido en '
             'una sola salida.'),
            'En vapor de agua aplique el límite más bajo (≈ 0,2) por erosión y ruido.',
            'Verifique que P2 y T2 sean correctos, ya que definen ρ2 y c.',
        ],
    },
    'sobrecalentamiento': {
        'que_es': ('Es la diferencia entre la temperatura del vapor de agua a la salida de la '
                   'válvula y la temperatura de saturación a la presión de salida: ΔTsc = T2 − '
                   'Tsat(P2).'),
        'que_hace': ('Indica si el vapor sale seco (sobrecalentado) o húmedo después del '
                     'estrangulamiento, calculado con IAPWS-95 por expansión isoentálpica.'),
        'que_indica': ('Un valor positivo significa vapor seco; cero significa que el vapor sale '
                       'húmedo (con gotas), con riesgo de erosión en los internos y la tubería.'),
        'umbrales': ('No hay umbral de norma. Práctica habitual: considerar seguro un '
                     'sobrecalentamiento de al menos algunos °C (por ejemplo ≥ 5-10 °C) a la '
                     'salida; con 0 °C el vapor contiene líquido.'),
        'por_debajo': ('Con ΔTsc = 0 el vapor sale húmedo: erosión por gotas, ruido distinto al '
                       'previsto y posible golpe de ariete si se acumula condensado.'),
        'por_encima': ('Un sobrecalentamiento alto no es un problema para la válvula, pero puede '
                       'requerir desobrecalentar aguas abajo si el usuario necesita vapor '
                       'saturado.'),
        'ejemplo': ('Vapor saturado seco a 10 bar(a) (Tsat ≈ 180 °C, h ≈ 2778 kJ/kg) se estrangula'
                    ' a 2 bar(a) (Tsat ≈ 120 °C). Con la misma entalpía sale a ≈ 154 °C, es decir '
                    'con unos 34 °C de sobrecalentamiento: sale seco.'),
        'afecta': [
            'Tipo de cálculo (vapor saturado o sobrecalentado)',
            'Densidad de salida ρ2',
            'Velocidad y Mach de salida',
            'Ruido aerodinámico IEC 60534-8-3',
            'Alerta de erosión',
        ],
        'recomendaciones': [
            ('Verifique el título (calidad) del vapor a la entrada: un vapor húmedo a la entrada '
             'puede seguir húmedo a la salida.'),
            'Instale separadores y purgadores aguas arriba si el vapor de entrada no es seco.',
            ('Con vapor húmedo use internos endurecidos (por ejemplo estelitados) y velocidades '
             'más bajas.'),
            'Si se necesita vapor saturado aguas abajo, prevea un desobrecalentador.',
        ],
    },
    'tipo_calculo': {
        'que_es': ('Es un resumen de qué ecuaciones aplicó el programa: tipo de fluido (líquido, '
                   'gas, vapor de agua saturado o sobrecalentado), régimen subcrítico o crítico '
                   '(estrangulado) y régimen de Reynolds.'),
        'que_hace': ('Permite verificar que el cálculo se hizo con el modelo correcto de IEC '
                     '60534-2-1 (cláusulas 6 y 9) antes de confiar en el Cv.'),
        'que_indica': ('«Crítico» significa que el caudal ya no aumenta al bajar P2: en gases x ≥ '
                       'xchoked = Fγ·xT y se dimensiona con x = xchoked e Y = 2/3. «Laminar o '
                       'transicional» indica que se aplica el factor de Reynolds FR < 1.'),
        'umbrales': ('Gases: flujo crítico cuando x = ΔP/P1 ≥ Fγ·xT, con Fγ = γ/1,4. Líquidos: '
                     'estrangulado cuando ΔP ≥ FL<sup>2</sup>·(P1 − FF·Pv). Reynolds: con Rev ≥ 10'
                     ' 000 el flujo es turbulento y FR = 1.'),
        'por_debajo': ('En régimen subcrítico el caudal sigue respondiendo a P2 y el Cv se calcula'
                       ' con el ΔP real; Reynolds bajos (fluidos muy viscosos o caudales muy '
                       'pequeños) requieren más Cv.'),
        'por_encima': ('En régimen crítico, bajar más P2 no aumenta el caudal; en líquidos suele '
                       'implicar cavitación o flashing, y en gases ruido alto.'),
        'ejemplo': ('Gas con γ = 1,3 y xT = 0,72: Fγ = 1,3/1,4 ≈ 0,93 y xchoked ≈ 0,67. Con P1 = '
                    '10 bar(a) y P2 = 2 bar(a), x = 0,8 > 0,67: el flujo es crítico, se usa x = '
                    '0,67 e Y = 2/3.'),
        'afecta': [
            'Cv requerido',
            'Factor de expansión Y',
            'Factor de Reynolds FR',
            'Alerta de cavitación y flashing',
            'Ruido aerodinámico e hidrodinámico',
            'Memoria de cálculo',
        ],
        'recomendaciones': [
            ('Si el flujo es crítico en líquidos, evalúe internos anticavitación o materiales '
             'endurecidos.'),
            'En gases con flujo crítico, verifique el ruido y considere trim de bajo ruido.',
            ('Si aparece régimen laminar, confirme la viscosidad y considere un tamaño de válvula '
             'mayor.'),
            'Revise que el estado del vapor (saturado o sobrecalentado) coincida con lo esperado.',
        ],
    },
    'cavitacion_incipiente': {
        'que_es': ('Es el primer régimen de cavitación (ISA-RP75.23): pueden aparecer burbujas '
                   'aisladas en la vena contracta que colapsan aguas abajo.'),
        'que_hace': ('El programa la informa cuando Kapp supera xFzp1 (típico de IEC 60534-8-4) '
                     'pero no el Kc del trim.'),
        'que_indica': ('Normalmente no hay daño. Con ΔP mayor que 10 bar la alerta pasa a '
                       'advertencia: muchas especificaciones piden trim anticavitación ya en este '
                       'régimen.'),
        'umbrales': 'xFzp1 ≤ Kapp < Kc. Desde Kc se emite la alerta de cavitación.',
        'por_debajo': 'Por debajo de xFzp1 el flujo es solo turbulento, sin burbujas.',
        'por_encima': ('Al llegar a Kc la cavitación es sostenida y puede erosionar internos y '
                       'cuerpo.'),
        'ejemplo': ('Kapp = 0,46, xFzp1 = 0,24 y Kc = 0,65: cavitación incipiente. Una hoja de '
                    'datos con criterio conservador puede pedir trim anticavitación aunque el '
                    'programa del fabricante no marque cavitación.'),
        'afecta': [
            'Condición del caso',
            'Selección de internos y materiales',
        ],
        'recomendaciones': [
            'Confirme con el fabricante el Kc certificado del trim.',
            ('En servicio continuo con agua y ΔP alta, internos endurecidos o jaula de etapa '
             'simple.'),
            ('Revise el criterio de la especificación del cliente: algunas no admiten cavitación '
             'incipiente.'),
        ],
    },
    'balance': {
        'que_es': ('Indica si el obturador es balanceado o desbalanceado. En uno balanceado, unos '
                   'orificios en el obturador igualan la presión arriba y abajo, y un anillo de '
                   'sello contra la jaula separa ambas zonas. En uno desbalanceado la ΔP actúa '
                   'sobre toda el área del puerto.'),
        'que_hace': ('El programa lo informa en la hoja de datos y verifica su compatibilidad: '
                     'fuerza de desbalance alta con trim desbalanceado; clase de cierre, '
                     'temperatura del sello y tipo de trim con trim balanceado. No cambia el Cv.'),
        'que_indica': ('Balanceado: actuador mucho más chico con ΔP alta, pero el sello agrega una'
                       ' vía de fuga y limita temperatura. Desbalanceado: cierre más hermético y '
                       'simple, pero el empuje crece con ΔP·área del puerto.'),
        'umbrales': ('Orientativo: conviene balanceado con ΔP de cierre mayor que unos 10 bar en '
                     'válvulas de 3" o más. El sello de PTFE llega a unos 232 °C; con trim '
                     'balanceado la clase de cierre habitual es IV. No aplica a válvulas '
                     'rotativas.'),
        'por_debajo': ('Con ΔP baja o diámetro chico el desbalanceado es la opción normal: más '
                       'simple y mejor cierre.'),
        'por_encima': ('Con ΔP alta y diámetro grande el desbalanceado exige un actuador muy '
                       'grande y pierde estabilidad cerca del asiento.'),
        'ejemplo': ('Válvula de 6" con ΔP de cierre de 20 bar: F ≈ 2000 kPa × π/4 × (0,152 m)² ≈ '
                    '36 kN (unas 8 200 lbf) sobre un obturador desbalanceado. Balanceado, la '
                    'fuerza baja a una fracción y basta un actuador estándar.'),
        'afecta': [
            'Hoja de datos',
            'Alertas de balanceo',
            'Tipo de guía y obturador (recomendaciones)',
        ],
        'recomendaciones': [
            ('Para clase V o VI con trim balanceado pida al fabricante un sello de balanceo '
             'especial.'),
            'Por encima de unos 232 °C especifique sello de grafito o metálico.',
            'El balanceo requiere obturador guiado por jaula.',
        ],
    },
    'desbalance_fuerza': {
        'que_es': 'Aviso de que el obturador desbalanceado recibe una fuerza del fluido grande.',
        'que_hace': ('Estima F ≈ ΔP·π·d²/4 con la ΔP máxima (cierre incluido) y el puerto igual al'
                     ' diámetro de la válvula.'),
        'que_indica': ('El actuador debe vencer esa fuerza para cerrar y modular: resulta grande y'
                       ' menos estable cerca del asiento.'),
        'umbrales': 'Se emite con trim desbalanceado, ΔP mayor que 10 bar y válvula de 3" o más.',
        'por_debajo': 'Con ΔP o diámetro menores la fuerza es manejable con actuadores estándar.',
        'por_encima': ('Cuanto mayor la ΔP y el diámetro, mayor el actuador y el riesgo de '
                       'inestabilidad.'),
        'ejemplo': ('Válvula de 4" y ΔP de 15 bar: F ≈ 1500 kPa × π/4 × (0,1016 m)² ≈ 12 kN (unas '
                    '2 700 lbf).'),
        'afecta': [
            'Dimensionamiento del actuador',
            'Elección del trim',
        ],
        'recomendaciones': [
            'Elegir trim balanceado.',
            'Confirmar el diámetro de puerto real con el fabricante.',
        ],
    },
    'balance_sin_jaula': {
        'que_es': 'Aviso de que se eligió trim balanceado con un obturador contorneado.',
        'que_hace': ('Advierte que el balanceo se fabrica casi siempre en obturadores guiados por '
                     'jaula.'),
        'que_indica': 'La combinación puede no estar disponible o requerir un diseño especial.',
        'umbrales': 'Se emite con trim balanceado y un trim que no es de jaula ni multietapa.',
        'por_debajo': 'Con un trim de jaula no se emite.',
        'por_encima': 'No aplica.',
        'ejemplo': ('Obturador contorneado tiende a abrir marcado como balanceado: cambie a jaula '
                    'de 4 ventanas.'),
        'afecta': [
            'Hoja de datos',
            'Elección del trim',
        ],
        'recomendaciones': [
            'Elegir un trim de jaula.',
            'O confirmar con el fabricante.',
        ],
    },
    'balance_cierre': {
        'que_es': 'Aviso de que el trim balanceado se combinó con clase de cierre V o VI.',
        'que_hace': ('Recuerda que el sello de balanceo es una segunda vía de fuga además del '
                     'asiento.'),
        'que_indica': ('La clase pedida solo se logra con sellos de balanceo especiales o asiento '
                       'blando.'),
        'umbrales': 'Se emite con trim balanceado y clase V o superior.',
        'por_debajo': 'Hasta clase IV el trim balanceado estándar es suficiente.',
        'por_encima': 'Clase VI con balanceado requiere confirmación expresa del fabricante.',
        'ejemplo': ('Válvula de 3" balanceada con clase V: pida un sello de balanceo de alta '
                    'prestación.'),
        'afecta': [
            'Clase de cierre',
            'Hoja de datos',
        ],
        'recomendaciones': [
            'Pedir la clase garantizada con el sello elegido.',
            'Si la ΔP lo permite, usar desbalanceado.',
        ],
    },
    'balance_temperatura': {
        'que_es': 'Aviso de que la temperatura supera el límite del sello de balanceo de PTFE.',
        'que_hace': 'Compara la temperatura de diseño con unos 232 °C.',
        'que_indica': ('Se necesita un sello de grafito o metálico, que puede reducir la clase de '
                       'cierre.'),
        'umbrales': 'Temperatura de diseño mayor que 232 °C con trim balanceado.',
        'por_debajo': 'Con menor temperatura el sello de PTFE es adecuado.',
        'por_encima': 'El PTFE pierde resistencia y el sello fuga.',
        'ejemplo': ('Agua de alimentación de caldera a 250 °C con trim balanceado: sello de '
                    'grafito.'),
        'afecta': [
            'Materiales del trim',
            'Clase de cierre',
        ],
        'recomendaciones': [
            'Especificar sello de grafito o metálico.',
            'Confirmar la clase de cierre con el fabricante.',
        ],
    },
}


GUIA["trim_size"] = {
    'que_es': 'Es el diámetro del orificio del asiento por el que pasa el fluido (tamaño del trim).',
    'que_hace': ('Define, junto con la carrera, la capacidad del trim. Es el dato con que el fabricante identifica '
                 'el juego de internos y el que se pide en la hoja de datos.'),
    'que_indica': ('Un puerto menor que el pleno indica un trim reducido: la válvula tiene más capacidad de la que '
                   'el servicio necesita y se achica el paso para controlar mejor.'),
    'umbrales': ('Puerto pleno típico (tabla de capacidad, mediana de fabricantes). Contorneado: 2" → 1 5/8", '
                 '3" → 2 5/8", 4" → 3 1/2", 6" → 5", 8" → 6 1/4". Jaula: 3" → 3 7/16", 4" → 4 3/8", 6" → 6", '
                 '8" → 7 1/4". El programa redondea al 1/16 in y lo informa también en mm.'),
    'por_debajo': 'Un puerto mucho menor que el pleno (trim reducido) aumenta la velocidad en el asiento.',
    'por_encima': 'No puede superar el puerto pleno del cuerpo.',
    'afecta': ['Carrera nominal estimada', 'Cv del trim reducido', 'Apertura estimada', 'Actuador', 'Hoja de datos',
               'Memoria de cálculo'],
    'recomendaciones': [
        'Cargue el puerto certificado cuando tenga la hoja del fabricante.',
        'Si el Cv nominal es mucho menor que el típico, verifique que el fabricante ofrezca ese trim reducido.',
    ],
    'ejemplo': ('Globo de 3" de jaula: pleno típico puerto 3 7/16 in, carrera 1 1/2 in, Cv 142 lineal. Con un '
                'Cv nominal de 67 el programa propone el puerto de 2 5/16 in con carrera 1 1/8 in (puerto, carrera '
                'y Cv van juntos).'),
}
GUIA["Cv_reducido"] = {
    'que_es': 'Es el Cv nominal del trim reducido: el de un asiento con puerto menor que el del trim completo del cuerpo.',
    'que_hace': ('Reemplaza al Cv típico del cuerpo en la apertura estimada, la carrera de operación, la curva de Cv, '
                 'las alertas de tamaño y los documentos.'),
    'que_indica': ('Cuánta capacidad queda con el puerto reducido. Si es cercano al Cv máximo requerido, la válvula '
                   'trabaja en la zona media de la carrera y controla mejor.'),
    'umbrales': ('Sin Cv certificado se estima con el puerto y la carrera (tabla de capacidad, dos restricciones en '
                 'serie). Se considera trim reducido cuando el puerto certificado es menor que el 97 % del típico.'),
    'por_debajo': 'Si el Cv reducido es menor que el requerido, la válvula queda subdimensionada (alerta crítica).',
    'por_encima': 'Si sigue muy por encima del requerido, la apertura queda baja: conviene un puerto aún menor.',
    'afecta': ['Apertura estimada', 'Carrera de operación', 'Curva de Cv', 'Alertas de tamaño', 'Hoja de datos'],
    'recomendaciones': [
        'Cargue el Cv certificado del fabricante: el Cv de un reducido varía mucho entre fabricantes.',
        'Busque que el caso máximo quede entre 70 % y 85 % de apertura y el mínimo por encima de 10 %.',
    ],
    'ejemplo': ('Globo de 3" de jaula con puerto reducido de 2 5/16" y carrera 1 1/8": Cv típico ≈ 67 (la relación '
                'de áreas daba 49; los fabricantes publican de ≈ 40 a 102 para ese puerto).'),
}
GUIA["carrera_nominal"] = {
    'que_es': 'Es el recorrido total del vástago entre la válvula cerrada y abierta del todo (rated travel).',
    'que_hace': ('Fija la carrera del actuador y la calibración del posicionador. La carrera de operación de cada '
                 'caso es la apertura × la carrera nominal.'),
    'que_indica': ('La carrera de operación dice cuántos milímetros se mueve el vástago en cada caso: sirve para '
                   'verificar la resolución del posicionador a aperturas bajas.'),
    'umbrales': ('Serie normalizada habitual: 3/4, 1 1/8, 1 1/2, 2, 3 y 4 in. Los trims de orificios llevan la '
                 'medida siguiente.'),
    'por_debajo': 'Con carreras de operación de pocos milímetros el control pierde resolución.',
    'por_encima': 'Una carrera mayor necesita un actuador de más carrera y más volumen de aire.',
    'afecta': ['Carrera de operación por caso', 'Hoja de datos', 'Memoria de cálculo'],
    'recomendaciones': [
        'Cargue la carrera certificada del fabricante cuando la tenga.',
        'En válvulas rotativas la carrera es la rotación del eje (60°, 70° o 90°).',
    ],
    'ejemplo': ('Globo de 4" con carrera nominal de 2 in (50,8 mm) y apertura de 62 %: carrera de operación '
                '0,62 × 50,8 = 31,5 mm (1,24 in).'),
}

GUIA["sentido_flujo"] = {
    'que_es': 'Es hacia dónde empuja el fluido al obturador: tiende a abrir (Up) o tiende a cerrar (Down).',
    'que_hace': ('Elige los factores FL, xT y Fd del trim para ese sentido y fija el sentido de la fuerza del fluido '
                 'en el cálculo del actuador. La fila «Flow» de la solapa 4 lo toma de aquí.'),
    'que_indica': ('Con flujo que tiende a cerrar las burbujas de cavitación o flashing colapsan lejos del asiento, '
                   'pero FL baja y el obturador puede golpear al cerrar.'),
    'umbrales': 'Tiende a abrir: FL ≈ 0,90. Tiende a cerrar: FL ≈ 0,80–0,85 (IEC 60534-2-1, Tabla 2).',
    'por_debajo': 'No aplica.',
    'por_encima': 'No aplica.',
    'afecta': ['FL, xT y Fd', 'ΔP choked y cavitación', 'Fuerza del fluido sobre el obturador', 'Flow del actuador'],
    'recomendaciones': [
        'Use tiende a abrir salvo flashing, cavitación o indicación del fabricante.',
        'Con tiende a cerrar verifique el actuador: la fuerza del fluido ayuda a cerrar y puede dar golpe.',
    ],
    'ejemplo': ('Globo contorneado con flujo que tiende a cerrar: FL 0,80 en lugar de 0,90, así que la ΔP choked de '
                'un líquido baja a (0,80/0,90)² ≈ 79 % de la del otro sentido.'),
}
GUIA["capacidad_trim"] = {
    'que_es': ('Es la tabla con la que N25 estima el Cv típico, el puerto y la carrera de las válvulas de globo y '
               'ángulo, por familia de trim y tamaño, a partir de datos publicados de varios fabricantes.'),
    'que_hace': ('Da el Cv nominal típico cuando no se carga el certificado, liga el puerto y la carrera con el Cv, '
                 'estima el Cv de un trim reducido y compara los datos certificados con los típicos (±10 %).'),
    'que_indica': ('La banda entre fabricantes muestra cuánto puede variar el Cv real de un mismo tamaño: es chica '
                   'en el trim pleno (±5 a ±25 %) y grande en los reducidos de jaula (de 0,5 a 1,5 veces).'),
    'umbrales': 'Tolerancia de coherencia: ±10 % respecto del típico del puerto y la carrera.',
    'por_debajo': 'Un Cv certificado mucho menor que el típico puede indicar un trim reducido o de baja capacidad.',
    'por_encima': 'Un Cv mucho mayor puede indicar un trim de alta capacidad o un dato de otro juego de trim.',
    'afecta': ['Cv nominal típico', 'Puerto y carrera estimados', 'Cv del trim reducido', 'Alerta de coherencia',
               'Selección del tamaño con trims especiales'],
    'recomendaciones': [
        'Use la tabla para preseleccionar; verifique con el Cv certificado del fabricante.',
        'Si la alerta de coherencia aparece, confirme que puerto, carrera y Cv sean del mismo juego de trim.',
    ],
    'ejemplo': ('Jaula de 6": típico 394 lineal (fabricantes 370 a 417). Un Cv certificado de 430 difiere +9 % '
                '(coherente); uno de 520, +32 % y fuera de la banda: advertencia.'),
}

GUIA["bajo_cv_minimo"] = {
    'que_es': ('Es la alerta que aparece cuando el Cv que pide un caso es menor que el Cv mínimo que la '
               'válvula puede regular (Cv nominal dividido por su rangeabilidad).'),
    'que_hace': ('Reemplaza la apertura y la carrera de ese caso por «< Cv mín.», para que no se lea un 0 % '
                 'como si fuera un resultado válido.'),
    'que_indica': ('La válvula es demasiado grande para ese caudal: no tiene una posición que dé ese Cv y '
                   'trabajaría abriendo y cerrando sobre el asiento.'),
    'umbrales': 'Cv requerido < Cv nominal / R (R ≈ 50 globo estándar; 15 orificios; 33 multietapa).',
    'por_debajo': 'Control de dos posiciones, golpeteo del obturador y erosión rápida del asiento.',
    'por_encima': 'No aplica.',
    'afecta': ['Apertura y carrera del caso', 'Selección del tamaño', 'Rangeabilidad'],
    'recomendaciones': [
        'Seleccionar un diámetro menor o un trim reducido.',
        'Para caudales muy distintos, dos válvulas en paralelo (split range).',
        'Un trim isoporcentual da más resolución a caudal bajo.',
    ],
    'ejemplo': ('Jaula de 3" lineal, Cv 142, R 50: el Cv mínimo es 2,8. Un caso con Cv 2,5 queda por debajo; '
                'con un trim reducido de Cv 40 el mínimo baja a 0,8 y el caso se puede regular.'),
}


GUIA["tipo_trim"] = {
    'que_es': ('Es la primera elección de los internos de globo y ángulo: sin jaula o con jaula.'),
    'que_hace': ('Muestra en las filas siguientes solo las opciones de ese tipo: la guía y el tipo de obturador, '
                 'o el obturador cilíndrico, la jaula y su config dinámica.'),
    'que_indica': ('Sin jaula: la característica la da el perfil del obturador. Con jaula: la jaula guía al '
                   'obturador cilíndrico, sujeta el asiento y da la característica.'),
    'umbrales': 'Las jaulas antiruido y anticavitación son siempre trims con jaula.',
    'por_debajo': 'No aplica.',
    'por_encima': 'No aplica.',
    'afecta': ['Opciones de obturador y jaula', 'Factores FL, xT, Fd y Kc', 'Capacidad típica'],
    'recomendaciones': [
        'Use un trim sin jaula en servicio general y tamaños chicos.',
        'Use un trim con jaula con ΔP altas, cuando hace falta balancear el obturador o mitigar cavitación o ruido.',
    ],
    'ejemplo': ('Agua con cavitación severa: con jaula, jaula anticavitación, jaula perforada de 3 etapas.'),
}

GUIA["clase_jaula"] = {
    'que_es': ('Es la clase de jaula de un trim con jaula: estándar (caracterizada), anticavitación o antiruido.'),
    'que_hace': ('Con jaula estándar bloquea la config dinámica. Con anticavitación o antiruido habilita la lista '
                 'de construcciones y niveles de esa clase.'),
    'que_indica': ('Qué fenómeno se busca mitigar: ninguno (estándar), la cavitación de un líquido o el ruido '
                   'aerodinámico de un gas o vapor.'),
    'umbrales': 'Anticavitación solo aparece con líquidos; antiruido solo con gas, vapor y steam.',
    'por_debajo': 'No aplica.',
    'por_encima': 'No aplica.',
    'afecta': ['Config dinámica disponible', 'Factores FL, xT, Fd y Kc', 'Capacidad típica'],
    'recomendaciones': [
        'Empiece con la jaula estándar y pase a la especial si el programa avisa cavitación o ruido.',
    ],
    'ejemplo': ('Vapor con 102 dB(A) y límite 85: jaula antiruido.'),
}

GUIA["guia_obturador"] = {
    'que_es': ('Es cómo se guía el obturador cuando el trim es sin jaula: superior reforzada, doble '
               'guía superior, superior e inferior, por el puerto o por el bonete.'),
    'que_hace': ('Filtra los obturadores que se ofrecen y entra en el informe. No cambia los factores de cálculo.'),
    'que_indica': ('Cuánto apoyo tiene el obturador frente a la fuerza del fluido y a las vibraciones.'),
    'umbrales': ('Por el puerto: ΔP hasta unos 1 000 kPa y menos de 6". Por el bonete: hasta 2". Por encima, el '
                 'programa avisa.'),
    'por_debajo': 'No aplica.',
    'por_encima': 'Una guía débil para la ΔP o el tamaño hace vibrar el obturador y desgasta el asiento.',
    'afecta': ['Obturadores disponibles', 'Avisos de guía', 'Informe de internos'],
    'recomendaciones': [
        'Superior reforzada para servicio general y fluidos sucios.',
        'Superior e inferior para tamaños grandes y ΔP altas.',
        'Confirme la guía con la hoja de datos del fabricante.',
    ],
    'ejemplo': ('Válvula de 1" de microcaudal: guía por el bonete con obturador de aguja.'),
}

GUIA["nivel_etapas"] = {
    'que_es': ('Es la construcción y el nivel o la cantidad de etapas de una jaula anticavitación (perforada, '
               'pasajes grandes, discos apilados) o antiruido (multiorificio, multietapa multiorificio, discos).'),
    'que_hace': ('Carga en las condiciones de operación los FL, xT, Fd y Kc de ese nivel, cambia el Cv típico y '
                 'define cómo se calcula el ruido.'),
    'que_indica': ('Junto al nombre se muestra cuánto mitiga: en líquidos, el Kapp máximo sin cavitación; en '
                   'gases, la atenuación típica de ruido.'),
    'umbrales': ('Líquido: 1 etapa Kc 0,85; 2 etapas sin cavitación hasta Kapp 0,75; 3 hasta 0,875; 4 hasta '
                 '0,938. Gas: nivel 1 a 3 de 5 a 20 dB(A); multietapa de 15 a 35 dB(A).'),
    'por_debajo': 'Un nivel insuficiente deja cavitación o ruido por encima del límite.',
    'por_encima': 'Un nivel de más reduce la capacidad por pulgada, encarece la válvula y se tapa con sólidos.',
    'afecta': ['FL, xT, Fd y Kc', 'Cv típico y diámetro automático', 'Ruido y cavitación'],
    'recomendaciones': [
        'La lista va de la opción más simple y de menos etapas a la más compleja: elija la primera que cumple; '
        'el programa la indica en las recomendaciones.',
        'Reemplace los valores por los certificados del trim ofertado.',
    ],
    'ejemplo': ('Vapor con 102 dB(A) y límite 85: multiorificio nivel 3 deja 88, multietapa multiorificio de 4 '
                'etapas deja 83: se elige la de 4 etapas.'),
}

GUIA["pernos_bonete"] = {
    'que_es': ('Es el material de los espárragos (o tornillos) y tuercas que unen el cuerpo con el bonete de la '
               'válvula.'),
    'que_hace': ('Queda en la hoja de datos y el programa verifica la temperatura de uso de cada pieza y, en '
                 'servicio agrio, si la combinación es aceptable según ISO 15156.'),
    'que_indica': ('Cada opción nombra el espárrago y la tuerca (por ejemplo B7 / 2H); «lubricados» indica montaje '
                   'con antiagarrotante; «NACE» marca las combinaciones para servicio agrio.'),
    'umbrales': ('B7 / 2H de −48 °C a unos 450 °C; B16 y A453 660 hasta unos 593 °C; B8M / 8M Clase 1 de −196 °C '
                 'a 816 °C; servicio agrio con pernos expuestos: ≤ 22 HRC (B7M / 2HM, B8M Cl. 1 / 8M).'),
    'por_debajo': ('Por debajo de su temperatura mínima el acero pierde tenacidad y el perno puede romperse de '
                   'forma frágil.'),
    'por_encima': ('Por encima de su temperatura máxima el perno se relaja, pierde precarga y la junta '
                   'cuerpo-bonete fuga.'),
    'afecta': ['Hoja de datos', 'Alertas de temperatura y servicio agrio', 'Estanqueidad del bonete'],
    'recomendaciones': [
        'Use «Estándar del fabricante» si la especificación del cliente no pide un grado.',
        'En servicio agrio con aislación térmica elija una combinación NACE.',
        'La junta (cantidad, diámetro y torque de los pernos) la define el fabricante.',
    ],
    'ejemplo': ('Vapor a 480 °C: B7 / 2H queda fuera de temperatura; B16 / grado 7 cumple.'),
}

GUIA["pernos_prensa"] = {
    'que_es': ('Es el material de los espárragos y tuercas de la brida prensaempaques, que comprime la empaquetadura '
               'del vástago, y en algunas opciones también el de la brida.'),
    'que_hace': ('Queda en la hoja de datos y se verifica con la temperatura de diseño y el servicio agrio, igual '
                 'que los pernos cuerpo-bonete.'),
    'que_indica': ('Indica de qué material son las piezas que aprietan la empaquetadura y que quedan mojadas si la '
                   'empaquetadura fuga.'),
    'umbrales': ('Los mismos de cada material de pernos; en servicio agrio, combinaciones NACE si pueden quedar '
                 'expuestos.'),
    'por_debajo': 'Fuera de temperatura los espárragos pierden tenacidad o precarga y la empaquetadura fuga.',
    'por_encima': 'Un material de más encarece sin mejorar la estanqueidad.',
    'afecta': ['Hoja de datos', 'Alertas de temperatura y servicio agrio', 'Emisiones por el vástago'],
    'recomendaciones': [
        'En fluidos corrosivos use el mismo nivel de material que el vástago.',
        'Con tuerca prensaempaques roscada elija CF10SMnN para evitar el agarrotamiento.',
    ],
    'ejemplo': 'Servicio agrio con aislación térmica: SA-193 B7M espárragos / tuercas 2HM, NACE.',
}
