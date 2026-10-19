"""Ayuda de la solapa 3-Materiales: parámetros del servicio, componentes, normas, mecanismos y alertas.

ENTRADAS: clave -> datos de la entrada de ayuda (título, fundamento técnico en HTML simple, fórmula,
valores típicos, referencia, entradas relacionadas y categoría).
GUIA: clave -> guía didáctica (qué es, qué hace, qué indica, umbrales, por debajo / por encima,
cálculos que afecta, recomendaciones y ejemplo), igual que ayuda_guia.GUIA.

Los textos describen el comportamiento real de seleccion_materiales.py, materiales.py y quimica.py.
"""

ENTRADAS: dict[str, dict] = {}
GUIA: dict[str, dict] = {}

MAT, NOR, FEN = "Materiales", "Normas y mecanismos", "Fenómenos"


def _e(clave, titulo, texto, categoria, formula="", tipicos="", referencia="", relacionadas=(), guia=None):
    ENTRADAS[clave] = dict(titulo=titulo, texto=texto, formula=formula, tipicos=tipicos, referencia=referencia,
                           relacionadas=list(relacionadas), categoria=categoria)
    GUIA[clave] = guia


def _g(que_es, que_hace, que_indica, umbrales, por_debajo, por_encima, afecta, recomendaciones, ejemplo):
    return dict(que_es=que_es, que_hace=que_hace, que_indica=que_indica, umbrales=umbrales,
                por_debajo=por_debajo, por_encima=por_encima, afecta=list(afecta),
                recomendaciones=list(recomendaciones), ejemplo=ejemplo)


# =====================================================================================
# PARÁMETROS DEL SERVICIO
# =====================================================================================
_e("mat_industria", "Industria / proceso",
   "<p>Indica en qué tipo de planta trabaja la válvula. Además de describir el servicio, decide qué norma de "
   "servicio agrio (H₂S) se aplica cuando el usuario deja «Norma servicio agrio» en «Por determinar»:</p><ul>"
   "<li><b>O&amp;G Upstream</b> (pozos, baterías, plantas de tratamiento de gas y crudo en yacimiento, "
   "inyección de agua) y <b>O&amp;G Midstream (transporte)</b> (gasoductos, oleoductos, estaciones de compresión "
   "y medición): <b>ISO 15156 / NACE MR0175</b>.</li>"
   "<li><b>Refinería</b> y <b>Petroquímica</b>: <b>ISO 17945 / NACE MR0103</b>, escrita para los ambientes "
   "de refino (aguas agrias, unidades de hidrotratamiento, aminas).</li>"
   "<li><b>Generación eléctrica</b> (vapor, agua de alimentación, condensado, refrigeración), <b>Química</b>, "
   "<b>Minería</b> (pulpas, lixiviación, relaves), <b>Tratamiento de agua</b>, <b>Pulpa y papel</b> "
   "(licores, blanqueo con cloro), <b>Alimentos / farmacéutica</b> (limpieza CIP, higiene) y <b>Otra</b>: si "
   "aparece H₂S se aplica ISO 15156 / MR0175 por ser la más restrictiva.</li></ul>"
   "<p>El dato sale de la hoja de datos de la válvula o del alcance del proyecto.</p>",
   MAT, referencia="ISO 15156 (MR0175); ISO 17945 (MR0103)",
   relacionadas=["mat_norma_agrio", "nace_mr0175", "nace_mr0103"],
   guia=_g("Es el sector industrial o el proceso donde se instala la válvula.",
           "Elige automáticamente la norma de servicio agrio cuando el usuario no la fija: upstream y midstream "
           "usan ISO 15156 / MR0175; refinería y petroquímica usan ISO 17945 / MR0103; el resto, ISO 15156.",
           "Anticipa los contaminantes habituales: H₂S y CO₂ en petróleo y gas, aguas agrias y aminas en "
           "refinería, sólidos en minería, cloro y oxidantes en pulpa y papel o tratamiento de agua.",
           "No tiene umbral numérico. La norma de servicio agrio solo se aplica si además hay pH₂S ≥ 0,3 kPa "
           "con agua libre (o si se declara servicio agrio).",
           "No aplica.", "No aplica.",
           ["Norma de servicio agrio aplicada", "Límites de dureza y ambientales de cada material"],
           ["Elegir la industria del dueño de la planta, no la del fabricante de la válvula.",
            "Una planta de gas en yacimiento es «O&G Upstream» aunque tenga equipos de proceso.",
            "Si la especificación del cliente exige una norma distinta, elíjala en «Norma servicio agrio»."],
           "Separador de producción con gas agrio: «O&G Upstream» → ISO 15156 / MR0175. La misma corriente "
           "dentro de una refinería → ISO 17945 / MR0103, que admite aceros al carbono P-No. 1 sin límite de "
           "dureza del metal base."))

_e("mat_composicion", "Estado de la composición",
   "<p>Cuánto se sabe de la composición del fluido:</p><ul>"
   "<li><b>Confirmada por análisis</b>: análisis de laboratorio (cromatografía de gases, análisis de agua, "
   "Draeger / tubos colorimétricos para H₂S).</li>"
   "<li><b>Confirmada por simulación</b>: balance de materia del proceso (simulador).</li>"
   "<li><b>Parcialmente conocida</b>: se conocen algunos componentes.</li>"
   "<li><b>Sin contaminantes conocidos</b>: el proceso declara fluido limpio.</li>"
   "<li><b>Desconocida</b>.</li></ul>"
   "<p>Con «Desconocida» o «Parcialmente conocida» y sin agentes cargados el programa emite la alerta "
   "<i>Composición del fluido incompleta</i>: la selección se basa solo en el fluido definido en la solapa 2.</p>",
   MAT, relacionadas=["agente", "agua_libre"],
   guia=_g("Es el grado de confianza en la composición química del fluido.",
           "Determina si el programa advierte que la selección puede no cubrir contaminantes.",
           "Cuanto menos confirmada la composición, más conservadora debe ser la elección.",
           "Desconocida o Parcialmente conocida sin agentes → alerta de advertencia.",
           "No aplica.", "No aplica.",
           ["Alerta de composición incompleta", "Confianza del resultado"],
           ["Pida al proceso: H₂S, CO₂, cloruros, pH, oxígeno, sólidos y contenido de agua.",
            "Si no hay análisis, cargue valores conservadores y déjelo escrito en el informe."],
           "Crudo «Parcialmente conocida» sin agentes: el programa avisa y selecciona solo por temperatura, "
           "presión y cavitación."))

_e("mat_regimen", "Régimen operativo",
   "<p><b>Continuo</b>: operación permanente. <b>Intermitente</b>, <b>Batch</b> (por lotes) y "
   "<b>Emergencia</b> (opera solo en eventos, como una válvula de alivio o de despresurización): en paradas el "
   "fluido queda estanco, entra oxígeno, condensa agua y se forman depósitos; esto favorece picaduras y "
   "corrosión bajo depósitos y el programa lo anota en el informe recomendando drenaje o purga. "
   "<b>Desconocido</b>.</p>",
   MAT, relacionadas=["picaduras", "agua_libre"],
   guia=_g("Es la forma en que opera la válvula a lo largo del tiempo.",
           "Agrega una nota de corrosión en paradas cuando el régimen no es continuo.",
           "Los servicios intermitentes suelen corroer más que los continuos con el mismo fluido.",
           "No tiene umbral numérico.",
           "No aplica.", "No aplica.",
           ["Notas del informe", "Recomendaciones de operación"],
           ["En servicios batch con limpieza química, cargue también los agentes de limpieza.",
            "Para válvulas de emergencia priorice materiales que no se agarroten estando quietos (galling)."],
           "Válvula de despresurización de gas húmedo: «Emergencia» → nota de corrosión por fluido estanco."))

_e("mat_medio", "Medio esperado (mecanismos de falla)",
   "<p>Es el tipo de deterioro que el ingeniero espera en el servicio. El programa también lo detecta a "
   "partir de los datos y, si no coincide, emite una alerta informativa. Las cuatro familias de mecanismos "
   "de falla son:</p><ul>"
   "<li><b>Servicio corrosivo</b>: pérdida de metal por reacción química o electroquímica con el fluido: "
   "corrosión general por ácidos, picaduras y rendijas por cloruros, corrosión bajo tensión (SCC) por "
   "cloruros o cáusticos, corrosión por CO₂, oxidantes, fluoruros, azufre.</li>"
   "<li><b>Servicio agrio</b> (sour): fluido con H₂S y agua libre (pH₂S ≥ 0,3 kPa). El hidrógeno atómico "
   "que libera la corrosión entra en el acero y lo fisura sin pérdida visible de metal (SSC, HIC, SOHIC). "
   "Exige materiales según ISO 15156 / MR0175 o ISO 17945 / MR0103, con dureza limitada.</li>"
   "<li><b>Servicio erosivo</b>: desgaste mecánico por partículas, gotas, burbujas de cavitación o mezcla "
   "líquido-vapor de flashing a alta velocidad. Se combate con dureza y materiales resistentes al desgaste "
   "(Stellite, 440C, carburo, cerámica).</li>"
   "<li><b>Servicio mixto</b>: dos o más de los anteriores a la vez (por ejemplo agrio + erosivo, o "
   "corrosivo + cavitación). Es el caso más exigente porque los requisitos se suman y a veces chocan "
   "(un material duro puede no ser aceptable en servicio agrio).</li></ul>"
   "<p><b>Sin mecanismo confirmado</b>: el servicio parece limpio. <b>Por evaluar</b>: el usuario deja "
   "que el programa lo determine (no genera alerta de discrepancia). Si se elige «Servicio agrio» sin "
   "H₂S informado, el programa evalúa con pH₂S = 100 kPa (conservador).</p>",
   MAT, relacionadas=["mecanismos_falla", "servicio_agrio", "erosion", "mat_medio_distinto"],
   guia=_g("Es la clase de daño que se espera en el servicio: corrosivo, agrio, erosivo o mixto.",
           "Se compara con el medio detectado a partir de agentes, cavitación, flashing y sólidos. «Servicio "
           "agrio» declarado fuerza las reglas de servicio agrio aunque no se haya cargado H₂S.",
           "Ayuda a detectar datos faltantes: si espera servicio agrio pero no cargó H₂S, el resultado avisa.",
           "Agrio: pH₂S ≥ 0,3 kPa con agua. Erosivo: cavitación, flashing o sólidos detectados.",
           "No aplica.", "No aplica.",
           ["Mecanismos de deterioro", "Servicio agrio", "Alerta de medio distinto"],
           ["Deje «Por evaluar» si no tiene experiencia previa con el servicio.",
            "Declare «Servicio agrio» si el cliente lo especifica aunque no tenga el análisis de H₂S."],
           "Agua producida con 2.000 ppmv de H₂S y cavitación moderada: el programa detecta «Servicio mixto "
           "(corrosivo, agrio, erosivo)»."))

_e("mat_norma_agrio", "Norma de servicio agrio",
   "<p>Norma con la que se califican los materiales en presencia de H₂S húmedo:</p><ul>"
   "<li><b>Por determinar</b>: la elige el programa según la industria (upstream y midstream → ISO 15156; "
   "refinería y petroquímica → ISO 17945; otras → ISO 15156).</li>"
   "<li><b>No aplica (confirmado)</b>: el usuario declara que no hay servicio agrio. Si los datos indican "
   "pH₂S ≥ 0,3 kPa con agua, el programa aplica igual la norma por seguridad y emite la alerta "
   "<i>Servicio agrio y norma «No aplica»</i>.</li>"
   "<li><b>ISO 15156 / MR0175</b>: producción de petróleo y gas.</li>"
   "<li><b>ISO 17945 / MR0103</b>: refino.</li>"
   "<li><b>Otra</b>: especificación propia del cliente; se trata como «Por determinar».</li></ul>"
   "<p>Si el usuario elige una de las dos normas y hay algo de H₂S (aunque menos de 0,3 kPa), el programa "
   "aplica la norma.</p>",
   MAT, relacionadas=["nace_mr0175", "nace_mr0103", "mat_industria", "servicio_agrio"],
   guia=_g("Es la norma que define qué materiales y durezas se admiten con H₂S.",
           "Fija los límites que se comparan con cada material: estado (aceptable, con límites, no aceptable), "
           "dureza máxima, pH₂S máximo, temperatura máxima, pH mínimo y si admite azufre elemental.",
           "ISO 15156 tiene límites ambientales para aleaciones resistentes a la corrosión; ISO 17945 es más "
           "permisiva con aceros al carbono en refinería.",
           "Servicio agrio: pH₂S ≥ 0,3 kPa (0,05 psia) con agua libre.",
           "No aplica.", "No aplica.",
           ["Descarte de materiales por servicio agrio", "Alertas de servicio agrio"],
           ["Use la norma que exige la especificación del cliente.",
            "No declare «No aplica» sin un análisis de H₂S que lo respalde."],
           "Refinería, agua agria con pH₂S = 50 kPa: «Por determinar» → ISO 17945; el WCB es aceptable y el "
           "17-4PH debe estar en condición H1150D ≤ 33 HRC."))

_e("mat_solidos", "Sólidos",
   "<p>Presencia de partículas sólidas (arena, óxidos, catalizador, cenizas, mineral):</p><ul>"
   "<li><b>Ausentes confirmados</b>: sin requisito por sólidos.</li>"
   "<li><b>Trazas</b>: obturador y asiento ≥ 35 HRC.</li>"
   "<li><b>Presentes</b>: obturador, asiento y jaula ≥ 45 HRC y resistencia a la erosión ≥ 8/10; el cuerpo "
   "con resistencia a la erosión menor que 4/10 se penaliza.</li>"
   "<li><b>Desconocido</b>: sin requisito; conviene confirmarlo.</li></ul>"
   "<p>Con familia «Slurry» el requisito sube a 55 HRC y erosión 10/10. Cómo confirmarlo: filtros "
   "aguas arriba, análisis de sólidos suspendidos (mg/L), producción de arena del pozo, historial de "
   "desgaste.</p>",
   MAT, relacionadas=["erosion", "dureza", "agente_solidos"],
   guia=_g("Es la existencia de partículas arrastradas por el fluido.",
           "Fija dureza y resistencia a la erosión mínimas de los internos y penaliza cuerpos blandos.",
           "Los sólidos a alta velocidad cortan las superficies de cierre (wire-drawing) y destruyen la "
           "estanqueidad.",
           "Trazas → 35 HRC. Presentes → 45 HRC y erosión 8/10. Slurry → 55 HRC y erosión 10/10.",
           "No aplica.", "No aplica.",
           ["Dureza requerida", "Resistencia a la erosión requerida", "Puntaje del cuerpo"],
           ["Instale filtros aguas arriba cuando sea posible.",
            "Con arena de pozo use insertos de carburo de tungsteno."],
           "Gas con arena del pozo: «Presentes» → el programa descarta 316 y 410 y elige Stellite 6, 440C o "
           "carburo."))

_e("mat_pH", "pH",
   "<p>Acidez de la fase acuosa (0 a 14; 7 neutro). Es opcional. Se usa para los límites ambientales de "
   "servicio agrio: por ejemplo el 17-4PH H1150D requiere pH ≥ 4,5 y el 410 / CA6NM pH ≥ 3,5. Si no se "
   "informa, esos límites de pH no se verifican.</p><p>Dónde obtenerlo: análisis del agua (medición in situ, "
   "porque el pH cambia al despresurizar y liberar CO₂ y H₂S) o cálculo por simulación. Agua producida con "
   "CO₂ suele tener pH 4 a 6; agua de mar 8,1; condensado de vapor 8,5 a 9,5 (con tratamiento).</p>",
   MAT, tipicos="Agua de mar 8,1 · Agua producida con CO₂ 4–6 · Condensado tratado 8,5–9,5",
   relacionadas=["nace_mr0175", "ssc"],
   guia=_g("Es la medida de acidez o alcalinidad del agua del proceso.",
           "Se compara con el pH mínimo que exigen algunos materiales en servicio agrio.",
           "Cuanto más bajo el pH, mayor la severidad del servicio agrio y de la corrosión ácida.",
           "17-4PH H1150D: pH ≥ 4,5. 410 / CA6NM: pH ≥ 3,5.",
           "Por debajo del mínimo el material se descarta en servicio agrio.",
           "Un pH alto (alcalino) reduce la severidad del H₂S, pero cuidado con el agrietamiento cáustico.",
           ["Límites ambientales de servicio agrio"],
           ["Mida el pH in situ o use el valor calculado a presión de operación.",
            "Si no lo conoce, déjelo en blanco: no lo invente."],
           "Servicio agrio con pH 4,0: un vástago 17-4PH H1150D se descarta (requiere pH ≥ 4,5) y el programa "
           "elige otra aleación, como Inconel 718 o Monel."))

_e("familia_quimica", "Familia química",
   "<p>Agrupa los agentes de la tabla para facilitar su búsqueda; al elegir la familia, el desplegable de "
   "agentes muestra solo los de esa familia:</p><ul>"
   "<li><b>Gases ácidos / reactivos</b>: H₂S, CO₂, SO₂, SO₃, Cl₂, O₂, NH₃, H₂.</li>"
   "<li><b>Halogenuros / sales</b>: cloruros (Cl⁻), bromuros (Br⁻), fluoruros (F⁻), NaCl, CaCl₂, MgCl₂, "
   "FeCl₃.</li>"
   "<li><b>Ácidos inorgánicos</b>: HCl, H₂SO₄, HNO₃, H₃PO₄, HF, H₂CO₃, HClO₄.</li>"
   "<li><b>Ácidos orgánicos</b>: acético, fórmico, oxálico, cítrico, láctico.</li>"
   "<li><b>Álcalis / bases</b>: NaOH, KOH, NH₄OH.</li>"
   "<li><b>Azufre / sulfuros</b>: azufre elemental, sulfuros, polisulfuros, tiosulfatos.</li>"
   "<li><b>Oxidantes</b>: hipoclorito, peróxido de hidrógeno, nitratos.</li>"
   "<li><b>Otros</b>: aminas, sólidos abrasivos, otro (especificar).</li></ul>",
   MAT, relacionadas=["agente", "unidad_quimica"],
   guia=_g("Es la categoría química del contaminante que se quiere cargar.",
           "Filtra la lista de agentes; no cambia el cálculo por sí misma.",
           "Cada familia ataca de forma distinta: los ácidos disuelven el metal, los halogenuros pican, los "
           "oxidantes rompen o fortalecen la capa pasiva según la aleación, el H₂S fisura.",
           "No tiene umbral numérico.",
           "No aplica.", "No aplica.",
           ["Lista de agentes disponible"],
           ["Si no encuentra el agente, revise las otras familias antes de usar «Otro».",
            "Cargue cada contaminante en una fila distinta."],
           "Para cargar cloruros de un análisis de agua: familia «Halogenuros / sales», agente «Cloruros»."))

_e("agente", "Agente / especie",
   "<p>Es la sustancia química, ion o contaminante presente en el fluido que puede deteriorar los "
   "materiales. Se cargan hasta seis filas. Cada agente tiene su propia ayuda detallada (qué es, en qué "
   "fluidos aparece, cómo detectarlo y qué materiales ataca) que se abre con el botón «Ver» de su fila.</p>"
   "<p>Para cada agente el programa usa reglas por familia de material con rangos de concentración y "
   "temperatura que dan un nivel A (excelente), B (bueno), C (regular) o D (no usar), y consulta además "
   "la tabla cualitativa A–D a temperatura ambiente; si ambas difieren, adopta la más conservadora. Con "
   "varios agentes el material toma el peor nivel.</p>"
   "<p>Si se elige «Otro (especificar)», el programa no puede evaluar su efecto y emite una alerta.</p>",
   MAT, relacionadas=["concentracion_agente", "unidad_quimica", "fase_agente", "compatibilidad_ad",
                      "agente_cloruros", "agente_h2s"],
   guia=_g("Es cada sustancia del fluido que puede atacar los metales o elastómeros de la válvula.",
           "Es la entrada principal de la compatibilidad química: cada agente evalúa a todos los materiales "
           "candidatos y descarta los de nivel D.",
           "Un solo agente agresivo (por ejemplo 1 % de HCl) puede descartar todos los aceros inoxidables.",
           "A excelente · B bueno · C regular (no recomendado para servicio continuo) · D no usar.",
           "No aplica.", "No aplica.",
           ["Compatibilidad química", "Mecanismos detectados", "Servicio agrio (H₂S)"],
           ["Cargue todos los contaminantes del análisis, también los minoritarios.",
            "Lea la ayuda de cada agente para saber cómo confirmarlo en el campo."],
           "Agua de proceso con 2.000 mg/L de cloruros a 50 °C: el 316 queda en C y el dúplex 2205 en A."))

_e("unidad_quimica", "Unidad química del agente",
   "<p>Unidad en que se expresa la concentración ingresada:</p><ul>"
   "<li><b>mg/L</b>: miligramos de la especie por litro de agua (análisis de agua).</li>"
   "<li><b>ppm masa</b>: mg por kg; en agua ≈ mg/L (el programa multiplica por la densidad relativa).</li>"
   "<li><b>ppmv</b>: partes por millón en volumen de un gas (= ppm molar); típico de H₂S y CO₂ en gas.</li>"
   "<li><b>% p/p</b>: porcentaje en masa (ácidos y bases comerciales: «HCl al 32 %»).</li>"
   "<li><b>% molar</b>: en gas da la presión parcial; en líquido se convierte a % p/p con la masa molar.</li>"
   "<li><b>mol/L</b>: molaridad; se convierte con la masa molar.</li>"
   "<li><b>bar(a) parcial</b> y <b>kPa parcial</b>: presión parcial del gas.</li></ul>"
   "<p>Cada agente tiene una unidad base en la que están escritas sus reglas: mg/L para iones y sales, "
   "% p/p para ácidos, bases y oxidantes líquidos, kPa de presión parcial para gases. El programa convierte "
   "lo ingresado a esa base; entre gas y líquido usa la ley de Henry a 25 °C (aproximada).</p>",
   MAT, formula="p = y·P (y = ppmv·10⁻⁶ o % molar/100) · mg/L = % p/p × 10.000 × SG · "
                "mg/L = mol/L × M × 1.000 · C disuelta = p × H",
   relacionadas=["concentracion_agente", "presion_parcial"],
   guia=_g("Es la unidad del número que se carga en «Concentración».",
           "Permite cargar el dato tal como viene del análisis; el programa lo lleva a la unidad base del "
           "agente antes de compararlo con las reglas.",
           "La misma cantidad puede verse muy distinta según la unidad: 1 % p/p = 10.000 mg/L.",
           "Gases: ppmv, % molar, bar(a) o kPa parcial. Iones en agua: mg/L. Ácidos y bases: % p/p.",
           "No aplica.", "No aplica.",
           ["Conversión a la unidad base", "Presión parcial de H₂S y CO₂"],
           ["Use la unidad del informe de laboratorio; no convierta a mano.",
            "No confunda mg/L de Cl⁻ con % p/p de HCl: son especies distintas."],
           "H₂S = 200 ppmv en un gas a 70 bar a: p = 200·10⁻⁶ × 7.000 kPa = 1,4 kPa ≥ 0,3 kPa → servicio "
           "agrio si hay agua."))

_e("concentracion_agente", "Concentración del agente",
   "<p>Celda numérica de ingreso manual (no es un desplegable). Después de elegir el agente y su unidad se "
   "escribe aquí el valor medido o especificado. <b>Impacta directamente en la selección</b>: las reglas de "
   "compatibilidad de cada material tienen rangos de concentración y temperatura, y al cruzar un umbral el "
   "nivel pasa de A a B, C o D, lo que cambia el material elegido.</p>"
   "<p>Si se deja en blanco, el programa usa un valor alto conservador propio del agente (por ejemplo "
   "20.000 mg/L de cloruros, 20 % de HCl, 100 kPa de H₂S) y emite la alerta <i>sin concentración</i>.</p>"
   "<p>Use punto o coma decimal. Debe ser el valor máximo esperado en operación, no el promedio.</p>",
   MAT, relacionadas=["unidad_quimica", "agente", "mat_sin_concentracion"],
   guia=_g("Es la cantidad del agente en el fluido, en la unidad elegida.",
           "Se convierte a la unidad base del agente y se compara con las filas de concentración-temperatura "
           "de las reglas de cada material.",
           "Valores bajos permiten materiales económicos; al aumentar, se descartan los menos resistentes.",
           "Ejemplos de umbrales del programa: cloruros a ≤ 40 °C: 316 excelente hasta 1.000 mg/L; H₂S: "
           "servicio agrio desde 0,3 kPa; CO₂ en acero al carbono con agua: B hasta 20 kPa, C hasta 1.000 kPa.",
           "Con concentraciones menores el programa puede proponer materiales más económicos.",
           "Con concentraciones mayores se descartan materiales y puede no quedar ninguno apto.",
           ["Compatibilidad química", "Presión parcial de H₂S y CO₂", "Material recomendado y costo"],
           ["Ingrese el valor máximo esperado, incluidos transitorios.",
            "Si el dato es incierto, prefiera el valor alto."],
           "Cloruros 500 mg/L a 30 °C: 316 nivel A. Cloruros 5.000 mg/L a 30 °C: 316 nivel C y el programa "
           "pasa a dúplex o superdúplex."))

_e("fase_agente", "Fase del agente",
   "<p>Dónde está el agente: <b>Acuosa</b> (disuelto en agua), <b>Orgánica líquida</b> (disuelto en "
   "hidrocarburo: sin agua libre no ataca, por eso se evalúa con las reglas sin agua), <b>Gas / vapor</b> "
   "(en la fase gaseosa: las unidades ppmv o % molar se interpretan como presión parcial), <b>Sólida</b> "
   "(partículas, depósitos) o <b>Desconocida</b>.</p>"
   "<p>Un ácido informado en fase gas (por ejemplo HCl en ppmv) se evalúa, si hay agua, como condensado "
   "ácido de concentración alta, porque al condensar se concentra en las primeras gotas.</p>",
   MAT, relacionadas=["unidad_quimica", "presion_parcial", "agua_libre"],
   guia=_g("Es la fase física en la que se encuentra el agente químico.",
           "Define la interpretación de la unidad y si se aplican las reglas con agua o sin agua.",
           "Los agentes solo atacan cuando llegan al metal disueltos en agua.",
           "Orgánica líquida → reglas sin agua libre. Gas con agua → condensado ácido concentrado.",
           "No aplica.", "No aplica.",
           ["Conversión de unidades", "Compatibilidad química"],
           ["H₂S y CO₂ de un gas: «Gas / vapor» en ppmv o % molar.",
            "Cloruros de un análisis de agua: «Acuosa» en mg/L."],
           "HCl 50 ppmv en un gas con agua libre: se evalúa como ácido condensado concentrado y descarta los "
           "aceros inoxidables."))

_e("mat_modo", "Modo AUTOMÁTICO / MANUAL",
   "<p>Cada componente tiene un modo:</p><ul>"
   "<li><b>AUTOMÁTICO</b> (recomendado): el programa elige el material apto de menor costo ponderado por "
   "durabilidad y lo muestra en la celda.</li>"
   "<li><b>MANUAL</b>: el usuario elige cualquier material de la biblioteca para ese componente. El "
   "programa lo evalúa igual (temperatura, química, servicio agrio, dureza, presión-temperatura, galling) y "
   "muestra las alertas, pero <b>la selección manual no es recomendada y deja fuera de responsabilidad al "
   "programa por la elección</b>. La recomendación automática sigue visible debajo de la celda.</li></ul>"
   "<p>El bonete sigue al cuerpo salvo que se ponga en MANUAL.</p>",
   MAT, relacionadas=["mat_recomendacion", "mat_manual", "mat_biblioteca"],
   guia=_g("Es la forma de definir el material de cada componente: lo elige el programa o el usuario.",
           "En AUTOMÁTICO aplica el motor de selección; en MANUAL evalúa la elección del usuario y alerta si "
           "no es apta.",
           "Un material manual con alerta crítica no cumple alguna condición del servicio.",
           "No tiene umbral numérico.",
           "No aplica.", "No aplica.",
           ["Material del componente", "Alertas", "Informe técnico"],
           ["Use MANUAL solo para reflejar un material exigido por el cliente o ya instalado.",
            "Revise siempre el análisis de la recomendación antes de apartarse de ella."],
           "El cliente exige cuerpo CF8M en agua de mar: en MANUAL el programa lo acepta, avisa «selección "
           "manual» y «compatibilidad química regular» y recomienda CD3MWCuN."))

_e("mat_biblioteca", "Biblioteca de materiales",
   "<p>Catálogo de los materiales del programa con su ficha completa: designación, familia, UNS, "
   "especificación ASTM, forma de producto, equivalente fundido / forjado, grupo de ASME B16.34, rango de "
   "temperatura, composición nominal, resistencia a la tracción y fluencia, dureza típica, PREN, índice de "
   "costo, componentes en que se usa, resistencia relativa a cavitación y erosión, situación en ISO 15156 y "
   "en ISO 17945, notas y fuentes. Se busca por clave, nombre, UNS, ASTM o familia.</p>"
   "<p>Incluye cuerpos fundidos y forjados (aceros al carbono, de baja temperatura, Cr-Mo, inoxidables, "
   "dúplex, superdúplex, aleaciones de níquel, titanio), internos (316, Stellite, 410, 416, 440C, 17-4PH, "
   "Nitronic 60, dúplex, aleaciones de níquel, carburos, cerámica, bronce) e insertos blandos (PTFE, RPTFE, "
   "PEEK, FKM, EPDM, NBR). Los valores son típicos: la aceptación final requiere el certificado (MTR).</p>",
   MAT, relacionadas=["uns_astm", "b16_34_grupos", "pren", "costo_material"],
   guia=_g("Es la base de datos de materiales que usa el programa.",
           "Provee los datos con los que se evalúa cada candidato y permite consultar la ficha de cualquiera.",
           "La ficha resume para qué sirve y cuáles son las limitaciones de cada material.",
           "No tiene umbral numérico.",
           "No aplica.", "No aplica.",
           ["Selección automática", "Modo manual", "Ficha del informe"],
           ["Consulte la ficha antes de elegir un material en modo manual.",
            "Verifique que el UNS del certificado coincida con el de la ficha."],
           "Buscar «S32760» muestra la barra superdúplex y la fundición CD3MWCuN con sus límites de servicio "
           "agrio (pH₂S ≤ 20 kPa, ≤ 232 °C)."))

_e("mat_recomendacion", "Recomendación y análisis",
   "<p>Debajo de cada celda se muestra el material recomendado por el programa y el botón <b>Análisis…</b> "
   "abre la justificación completa: temperatura, compatibilidad química por agente (regla y tabla A–D), "
   "verificación de ASME B16.34, situación frente a la norma de servicio agrio, dureza requerida y "
   "ofrecida, índice de costo, alternativas aptas y materiales descartados con su motivo.</p>"
   "<p>La regla de elección: se descartan los materiales que no cumplen temperatura, química (nivel D), "
   "servicio agrio, dureza, resistencia a cavitación / erosión o presión-temperatura; entre los aptos se "
   "prefieren los de nivel A o B frente a C y se elige el menor puntaje = índice de costo × factor químico "
   "× factor de erosión (y penalidades de resistencia mecánica del vástago). Las parejas deslizantes con "
   "riesgo alto de galling se evitan.</p>",
   MAT, relacionadas=["costo_material", "mat_modo", "compatibilidad_ad", "galling"],
   guia=_g("Es el material que el programa considera óptimo y su justificación.",
           "Documenta en pantalla y en el informe por qué se eligió y por qué se descartaron los demás.",
           "Si un material se descarta, el motivo indica qué dato del servicio lo excluye.",
           "Factor químico del cuerpo: A 1,0 · B 1,15 · C 2,5. De los internos: A 1,0 · B 1,5 · C 3,0.",
           "No aplica.", "No aplica.",
           ["Informe técnico", "Memoria de cálculo", "Hoja de datos"],
           ["Lea los descartes: muestran qué condición del servicio es la más exigente.",
            "Si la recomendación es muy cara, revise si los datos de entrada son realmente los máximos."],
           "Cuerpo en agua de mar: WCB descartado o en C, CF8M en C; el análisis muestra CD3MWCuN con "
           "cloruros nivel A y CL300 verificada en el grupo 2.8."))

# =====================================================================================
# COMPONENTES
# =====================================================================================
_e("comp_cuerpo", "Cuerpo",
   "<p>Es la envolvente a presión de la válvula: contiene el fluido, tiene las conexiones a la tubería y "
   "aloja los internos. Está mojado por el fluido en toda su superficie interior y recibe la erosión aguas "
   "abajo del asiento (flashing, colapso de burbujas de cavitación, sólidos).</p>"
   "<p>El programa lo elige verificando: rango de temperatura del material, compatibilidad química con cada "
   "agente (salvo en cuerpos con liner, donde la superficie mojada es el PFA/PTFE), norma de servicio "
   "agrio, rating de ASME B16.34 en la clase elegida a la temperatura de diseño con el grupo del material, "
   "fin del rating de válvulas bridadas a 538 °C y resistencia a la erosión (con flashing un cuerpo con "
   "erosión &lt; 4/10, como el acero al carbono, se penaliza ×2,5 y se prefiere Cr-Mo WC9 / C5 o "
   "inoxidable). El grupo del cuerpo elegido se usa también para la verificación de rating de la "
   "solapa 2.</p><p>Materiales típicos: WCB (general), LCC (baja temperatura), WC6 / WC9 (vapor y alta "
   "temperatura), CF8M (corrosivo), dúplex / superdúplex (cloruros), aleaciones de níquel (ácidos).</p>",
   MAT, relacionadas=["b16_34_grupos", "rating", "comp_bonete", "erosion", "grafitizacion"],
   guia=_g("Es la carcasa a presión de la válvula.",
           "Su material define la clase de presión admisible (ASME B16.34) y la resistencia a la corrosión "
           "de la parte más grande y cara.",
           "Un cuerpo mal elegido puede perder espesor o fisurarse y provocar una fuga al ambiente.",
           "Rating: presión de diseño ≤ presión admisible del grupo a la temperatura de diseño. Bridadas: "
           "hasta 538 °C.",
           "No aplica.", "No aplica.",
           ["Verificación de rating", "Bonete", "Costo de la válvula"],
           ["En acero al carbono, considere sobreespesor de corrosión si la química es B.",
            "Con flashing prefiera WC9 o inoxidable antes que WCB."],
           "Vapor a 450 °C, CL600: WCB descartado por grafitización (> 425 °C) y el programa elige WC9 "
           "(grupo 1.10)."))

_e("comp_bonete", "Bonete",
   "<p>Tapa del cuerpo por la que pasa el vástago; aloja la empaquetadura (y en algunos diseños la guía del "
   "obturador). Es parte de la envolvente a presión. El programa lo especifica <b>del mismo material que el "
   "cuerpo o de su equivalente forjado</b>, con el mismo grupo de ASME B16.34 y la misma resistencia "
   "química, salvo que el usuario lo ponga en modo MANUAL; en ese caso verifica su rating con su propio "
   "grupo. En válvulas rotativas corresponde a la tapa / brida del eje.</p>",
   MAT, relacionadas=["comp_cuerpo", "b16_34_grupos"],
   guia=_g("Es la tapa del cuerpo que sella el paso del vástago.",
           "Sigue al cuerpo: hereda su material y su verificación de presión-temperatura.",
           "Un bonete de material distinto al cuerpo puede limitar la clase de presión o crear un par "
           "galvánico.",
           "Mismo grupo de B16.34 que el cuerpo.",
           "No aplica.", "No aplica.",
           ["Rating de la válvula", "Hoja de datos"],
           ["Mantenga el mismo material que el cuerpo salvo motivo justificado.",
            "En alta temperatura considere bonete extendido para proteger la empaquetadura."],
           "Cuerpo CF8M fundido: bonete CF8M o F316 forjado."))

_e("comp_asiento", "Asiento",
   "<p>Anillo contra el que cierra el obturador. Recibe la mayor velocidad del fluido cerca del cierre, "
   "la cavitación y el wire-drawing (erosión filiforme por fugas a alta ΔP). El programa le exige dureza "
   "según la severidad: con ΔP &gt; 10 bar, asiento ≥ 38 HRC (recargue duro); con cavitación, flashing o "
   "sólidos los valores de la tabla de dureza. Se evita una pareja obturador–asiento con riesgo alto de "
   "galling.</p><p>Si la clase de cierre requiere asiento blando (clase VI en globo, ángulo y bola; clase V "
   "o mayor en mariposa concéntrica; clase VI en doble excéntrica; siempre en globo con liner) se agrega un "
   "inserto (PTFE, RPTFE, PEEK, FKM, EPDM o NBR) apto en temperatura y química; con ΔP &gt; 10 bar el PTFE "
   "virgen se penaliza por fluencia en frío. En rotativas corresponde al anillo de asiento.</p>",
   MAT, relacionadas=["hardfacing", "dureza", "clase_cierre", "mat_inserto"],
   guia=_g("Es la superficie de cierre fija de la válvula.",
           "Determina la estanqueidad y su duración; su material debe resistir erosión y cavitación.",
           "Un asiento erosionado deja pasar fluido aun con la válvula cerrada.",
           "ΔP > 10 bar → ≥ 38 HRC. Incipiente 25, moderada 35, severa 40, extrema 55 HRC.",
           "No aplica.", "No aplica.",
           ["Clase de cierre", "Galling con el obturador", "Inserto blando"],
           ["El recargue de Stellite 6 es la solución estándar en ΔP altas.",
            "Verifique que el inserto blando soporte la temperatura de diseño."],
           "Agua a 25 bar de ΔP sin cavitación: asiento 316 con recargue de Stellite 6 (40 HRC)."))

_e("comp_jaula", "Jaula caracterizada",
   "<p>Cilindro con ventanas u orificios que rodea al obturador; define la característica de caudal y, en "
   "trims de orificios o multietapa, reduce cavitación y ruido. Guía al obturador, por lo que tiene "
   "<b>contacto deslizante con él</b>: el programa evita la pareja obturador–jaula con riesgo alto de "
   "galling. Solo aplica cuando el trim elegido en la solapa 2 lleva jaula (jaula de ventanas, de orificios "
   "o multietapa); si no, figura «No aplica».</p><p>Materiales típicos: 416 o 410 templado, 17-4PH, "
   "CB7Cu-1 fundido, 316 con níquel químico (ENC), y para cavitación o erosión severas Stellite, 440C o "
   "carburo.</p>",
   MAT, relacionadas=["comp_obturador", "galling", "trim", "comp_guia"],
   guia=_g("Es el elemento con ventanas que guía al obturador y modela el caudal.",
           "Sufre la cavitación en sus orificios y el roce con el obturador.",
           "Una jaula blanda frente a un obturador blando del mismo material se agarrota (galling).",
           "Misma dureza mínima que el obturador según la cavitación; con flashing ≥ 38 HRC.",
           "No aplica.", "No aplica.",
           ["Galling obturador–jaula", "Dureza requerida"],
           ["Busque ≥ 10 HRC de diferencia con el obturador o ambas superficies ≥ 38 HRC.",
            "En cavitación severa considere trim multietapa además del material."],
           "Obturador 316 y jaula 316: riesgo alto de galling; el programa propone una jaula 316 ENC o 416 "
           "templada."))

_e("comp_guia", "Guía",
   "<p>Buje o casquillo que guía al obturador (o al vástago) cuando el trim no tiene jaula, como en el globo "
   "de obturador contorneado guiado arriba. Tiene contacto deslizante con el obturador y con el vástago, "
   "por eso el programa evalúa las parejas obturador–guía y vástago–guía y descarta las de riesgo alto de "
   "galling. Solo aplica sin jaula; con jaula figura «No aplica» porque la jaula hace de guía. En válvulas "
   "rotativas corresponde a los <b>cojinetes del eje</b>.</p><p>Materiales típicos: Stellite 6, 440C, "
   "17-4PH, Nitronic 60 (antigalling), bronce al aluminio (agua y aceite, sin H₂S), 316 con recargue.</p>",
   MAT, relacionadas=["galling", "comp_vastago", "comp_obturador", "comp_jaula"],
   guia=_g("Es el buje que mantiene alineado al obturador o al vástago.",
           "Sufre roce permanente; su material se elige para no soldarse en frío con la pieza que guía.",
           "Una guía agarrotada traba la válvula y produce histéresis y pérdida de control.",
           "Galling bajo: superficie ≥ 38 HRC, diferencia ≥ 10 HRC, o Stellite, Nitronic 60, bronce, ENC.",
           "No aplica.", "No aplica.",
           ["Galling obturador–guía y vástago–guía"],
           ["Nitronic 60 es una buena guía frente a vástagos de 316.",
            "No use bronce con H₂S, amoníaco o aminas."],
           "Vástago 2205 y guía 2205: riesgo alto (dúplex contra dúplex); el programa elige otra guía, por "
           "ejemplo Inconel 718 o Stellite."))

_e("comp_obturador", "Obturador",
   "<p>Pieza móvil que regula el paso del fluido (tapón en globo; bola, disco u obturador excéntrico en "
   "rotativas). Es la pieza más expuesta: soporta la mayor velocidad, la cavitación y el flashing, y roza "
   "contra el asiento y la jaula o guía. El programa la elige primero, exigiendo la dureza y la "
   "resistencia a la cavitación y a la erosión que fija el servicio; luego elige asiento, jaula y guía "
   "compatibles con ella para evitar galling.</p><p>Materiales típicos: 316 (servicio limpio), 416 / 410 "
   "templado, 17-4PH, 316 con Stellite, Stellite macizo, 440C, carburo de tungsteno, cerámica.</p>",
   MAT, relacionadas=["dureza", "cavitacion_dureza", "galling", "comp_asiento"],
   guia=_g("Es el elemento móvil que abre y cierra el paso.",
           "Define la dureza de referencia del trim y el punto de partida de las parejas de galling.",
           "Un obturador blando en cavitación se pica en semanas; uno frágil (cerámica) puede romperse por "
           "impacto.",
           "Incipiente 25 · moderada 35 · severa 40 · extrema 55 HRC; flashing 40 HRC (55 con ΔP > 20 bar).",
           "No aplica.", "No aplica.",
           ["Dureza requerida", "Galling con asiento, jaula y guía", "Vida útil del trim"],
           ["En cavitación extrema el material no alcanza: use trim multietapa.",
            "Con H₂S verifique que el material duro sea aceptable (440C y 17-4 H900 no lo son)."],
           "Cavitación severa en agua: obturador 440C (58 HRC) o 316 con Stellite 6."))

_e("comp_vastago", "Vástago",
   "<p>Barra que transmite la fuerza del actuador al obturador (eje en rotativas). Está mojado por el fluido "
   "y pasa por la empaquetadura. Se elige por compatibilidad química, servicio agrio y resistencia "
   "mecánica: con ΔP &gt; 10 bar o clase ≥ CL600 los materiales con límite de fluencia &lt; 400 MPa se "
   "penalizan (×1,5). Se evalúa la pareja vástago–guía cuando el trim no tiene jaula.</p>"
   "<p>Materiales típicos: 316, 17-4PH H1150D (estándar también en servicio agrio, ≤ 33 HRC), Nitronic 60, "
   "dúplex, Inconel 718 y Monel K-500 (alta resistencia en servicio agrio severo).</p>",
   MAT, relacionadas=["comp_guia", "nace_mr0175", "galling"],
   guia=_g("Es la barra que une el actuador con el obturador.",
           "Transmite el empuje; su rotura deja la válvula sin control.",
           "Un vástago débil se pandea o se tuerce; uno susceptible a SCC o SSC se fisura en servicio.",
           "Fluencia ≥ 400 MPa con ΔP > 10 bar o clase ≥ CL600.",
           "No aplica.", "No aplica.",
           ["Galling vástago–guía", "Servicio agrio", "Empuje del actuador"],
           ["En servicio agrio el 17-4PH solo en condición H1150D.",
            "Evite vástago y guía del mismo material austenítico o dúplex."],
           "Clase CL900 con agua: el 316 (fluencia 205 MPa) se penaliza y se elige 17-4PH o 410 templado."))

# =====================================================================================
# NORMAS Y MECANISMOS
# =====================================================================================
_e("nace_mr0175", "NACE MR0175 / ISO 15156",
   "<p>Norma internacional para materiales en ambientes con H₂S de la <b>producción de petróleo y gas</b> "
   "(pozos, cabezas de pozo, líneas de flujo, plantas de tratamiento en yacimiento, transporte). Tiene tres "
   "partes: principios generales (-1), aceros al carbono y de baja aleación (-2) y aleaciones resistentes a "
   "la corrosión, CRA (-3).</p><ul>"
   "<li>Se aplica cuando hay agua libre y pH₂S ≥ 0,3 kPa (0,05 psia).</li>"
   "<li>Aceros al carbono y baja aleación: dureza ≤ 22 HRC (≈ 237 HB) en el metal base; soldaduras y zona "
   "afectada por el calor ≤ 250 HV10. Los aceros con más de 1 % de Ni requieren calificación.</li>"
   "<li>CRA (inoxidables, dúplex, níquel, titanio): cada familia tiene límites ambientales de temperatura, "
   "pH₂S, cloruros, pH y azufre elemental. Ejemplos usados por el programa: austeníticos 300 hasta 60 °C y "
   "pH₂S ≤ 100 kPa; dúplex ≤ 10 kPa y 232 °C; superdúplex ≤ 20 kPa; 17-4PH H1150D ≤ 33 HRC, pH₂S ≤ "
   "3,4 kPa, pH ≥ 4,5; 410 ≤ 22 HRC, pH₂S ≤ 10 kPa.</li>"
   "<li>Los recubrimientos no protegen contra el agrietamiento; el recargue Co-Cr-W (Stellite) es "
   "aceptable.</li><li>Los pernos expuestos se cambian de ASTM A193 B7 a B7M (dureza limitada).</li></ul>",
   NOR, referencia="ISO 15156-1/-2/-3; NACE MR0175",
   relacionadas=["nace_mr0103", "ssc", "hic", "servicio_agrio", "mat_norma_agrio"],
   guia=_g("Es la norma que define qué materiales resisten el H₂S en la producción de petróleo y gas.",
           "El programa compara cada material con sus límites (estado, dureza, pH₂S, temperatura, pH, azufre) "
           "y descarta los que no cumplen.",
           "Un material «aceptable con límites» solo vale dentro de su ventana ambiental.",
           "pH₂S ≥ 0,3 kPa con agua. Acero al carbono ≤ 22 HRC; soldadura ≤ 250 HV.",
           "Con pH₂S < 0,3 kPa no se exige la norma (salvo que el usuario la elija).",
           "A mayor pH₂S se descartan dúplex, 17-4PH y martensíticos y quedan aleaciones de níquel.",
           ["Descarte por servicio agrio", "Dureza admisible", "Pernería"],
           ["Exija certificados con dureza (MTR) y procedimientos de soldadura calificados.",
            "Verifique la edición vigente de la norma que pide el cliente."],
           "Gas con pH₂S = 15 kPa: dúplex 2205 descartado (> 10 kPa), superdúplex aceptable (≤ 20 kPa)."))

_e("nace_mr0103", "NACE MR0103 / ISO 17945",
   "<p>Norma para materiales resistentes al agrietamiento por H₂S en <b>refinerías y plantas "
   "petroquímicas</b> (aguas agrias, hidrotratamiento, aminas). Es menos restrictiva que ISO 15156 en "
   "aceros al carbono porque los ambientes de refino son, en general, menos severos:</p><ul>"
   "<li>Aceros P-No. 1 (WCB, WCC, LCC, A105, LF2) aceptables sin límite de dureza del metal base; "
   "soldaduras ≤ 200 HBW.</li><li>Cr-Mo con límites de dureza (≈ 225–235 HBW).</li>"
   "<li>Austeníticos 300 solubilizados ≤ 22 HRC; dúplex ≤ 28 HRC; 17-4PH H1150D ≤ 33 HRC sin límite "
   "ambiental propio; 440C y 416 no aceptables.</li></ul>"
   "<p>El programa la aplica con industria Refinería o Petroquímica y «Norma: Por determinar».</p>",
   NOR, referencia="ISO 17945; NACE MR0103", relacionadas=["nace_mr0175", "servicio_agrio", "mat_industria"],
   guia=_g("Es la norma de materiales para servicio agrio en refinería.",
           "Define estados y durezas admisibles distintos de ISO 15156; el programa usa la ficha ISO 17945 de "
           "cada material.",
           "Un mismo material puede ser aceptable en refinería y tener límites en upstream.",
           "Servicio agrio: pH₂S ≥ 0,3 kPa con agua. Soldaduras de acero al carbono ≤ 200 HBW.",
           "No aplica.", "No aplica.",
           ["Descarte por servicio agrio", "Dureza admisible"],
           ["No mezcle normas: use la que pide la especificación del proyecto.",
            "Controle dureza de soldaduras en reparaciones."],
           "Agua agria de refinería: cuerpo WCB aceptable sin límite de dureza del metal base, vástago 17-4PH "
           "H1150D."))

_e("b16_34_grupos", "Grupos de materiales de ASME B16.34",
   "<p>ASME B16.34 agrupa los materiales de cuerpo y bonete según su resistencia en función de la "
   "temperatura y da, para cada grupo y clase (CL150 a CL2500), la presión de trabajo máxima "
   "(rating presión-temperatura). El programa tiene las tablas de clase estándar de la edición 2017 para los "
   "49 grupos:</p><ul><li><b>Grupos 1.x</b>: aceros al carbono (1.1 WCB/A105, 1.2 WCC/LCC, 1.3 LCB), "
   "C-Mo, Cr-Mo (1.9 WC6, 1.10 WC9, 1.13 C5, 1.15 C12A/F91).</li>"
   "<li><b>Grupos 2.x</b>: inoxidables (2.1 304/CF8, 2.2 316/CF8M, 2.3 304L/316L, 2.8 dúplex, superdúplex "
   "y 6Mo).</li><li><b>Grupos 3.x</b>: aleaciones de níquel (3.1 Aleación 20, 3.4 Monel, 3.5 Inconel 600, "
   "3.7 Hastelloy B, 3.8 C-276/C-22/625/825, 3.17 CN7M).</li></ul>"
   "<p>La presión se interpola linealmente entre temperaturas. Las válvulas bridadas terminan su rating a "
   "538 °C. Algunas fundiciones de níquel (CW2M, CX2MW, CW6MC, CU5MCuC, CY40, N7M) no figuran en la "
   "norma: el programa usa el grupo del forjado equivalente y lo avisa. El titanio no está incluido.</p>",
   NOR, referencia="ASME B16.34-2017, Tabla 1 y Tabla 2",
   relacionadas=["rating", "comp_cuerpo", "mat_fuera_pt", "mat_grupo_equivalente", "clase_insuficiente"],
   guia=_g("Es la clasificación de los materiales de válvulas por su resistencia frente a la temperatura.",
           "Con el grupo del cuerpo, la clase y la temperatura de diseño se obtiene la presión admisible; se "
           "compara con la presión de diseño.",
           "Un mismo CL300 admite distinta presión según el material: a 38 °C, 51,1 bar g en grupo 1.1 y "
           "49,6 bar g en grupo 2.2.",
           "Diseño ≤ rating a la temperatura de diseño. Bridadas ≤ 538 °C.",
           "Si el rating sobra, podría usarse una clase menor (verificar la tubería).",
           "Si la presión supera el rating se requiere una clase mayor o un material más resistente.",
           ["Verificación de rating", "Selección del cuerpo", "Clase mínima"],
           ["Use siempre la temperatura de diseño, no la de operación.",
            "Confirme la edición de B16.34 que exige el proyecto."],
           "WCB CL150 a 200 °C admite 13,8 bar g; con diseño 15 bar g se requiere CL300 (43,8 bar g)."))

_e("dureza", "Dureza (HB, HRC, HV)",
   "<p>Resistencia de un material a ser penetrado; se relaciona con su resistencia al desgaste, a la "
   "cavitación y al galling, y en servicio agrio con su susceptibilidad al agrietamiento.</p><ul>"
   "<li><b>HB (Brinell)</b>: huella de una bola de 10 mm; para materiales blandos y medios (aceros al "
   "carbono ≈ 150–180 HB, 316 ≈ 150 HB).</li>"
   "<li><b>HRC (Rockwell C)</b>: cono de diamante; para materiales endurecidos (410 templado ≈ 40 HRC, "
   "Stellite 6 ≈ 40 HRC, 440C ≈ 58 HRC).</li>"
   "<li><b>HV (Vickers)</b>: pirámide de diamante; se usa en soldaduras y recubrimientos (ZAC ≤ 250 HV en "
   "servicio agrio).</li></ul>"
   "<p>El programa convierte HRC ↔ HB con una tabla aproximada de ASTM E140 para aceros (22 HRC ≈ 237 HB, "
   "35 HRC ≈ 327 HB, 40 HRC ≈ 371 HB, 55 HRC ≈ 545 HB). La conversión es orientativa y no vale como "
   "criterio de aceptación en servicio agrio. Dureza mínima de los internos por cavitación: incipiente "
   "25 HRC, moderada 35 HRC, severa 40 HRC, extrema 55 HRC.</p>",
   NOR, referencia="ASTM E10 (Brinell), E18 (Rockwell), E92/E384 (Vickers), E140 (conversión)",
   relacionadas=["cavitacion_dureza", "hardfacing", "galling", "nace_mr0175"],
   guia=_g("Es la capacidad de una superficie para resistir la penetración y el desgaste.",
           "Se compara con la dureza mínima que exige el servicio para obturador, asiento y jaula, y con la "
           "dureza máxima que permite la norma de servicio agrio.",
           "Alta dureza resiste cavitación y erosión, pero puede ser frágil y no aceptable con H₂S.",
           "Cavitación: 25 / 35 / 40 / 55 HRC. Servicio agrio acero al carbono: ≤ 22 HRC.",
           "Por debajo del mínimo el material se desgasta rápido.",
           "Por encima del máximo NACE el material puede fisurarse por H₂S.",
           ["Dureza requerida", "Servicio agrio", "Galling"],
           ["Pida la dureza en el certificado del material o del recargue.",
            "No use conversiones de dureza para aceptar materiales en servicio agrio."],
           "Cavitación severa: se exigen 40 HRC; el 316 (≈ 150 HB, por debajo de la escala HRC) se descarta y "
           "Stellite 6 (40 HRC) cumple."))

_e("galling", "Galling (soldadura en frío)",
   "<p>Daño por adhesión entre dos superficies metálicas que deslizan con carga: las asperezas se sueldan "
   "en frío, se arrancan y transfieren material, hasta agarrotar las piezas. Es típico de aceros "
   "inoxidables austeníticos, dúplex, aleaciones de níquel y titanio, cuya capa pasiva se rompe con el "
   "roce. En válvulas aparece en obturador–jaula, obturador–asiento y vástago/obturador–guía.</p>"
   "<p>Reglas del programa: riesgo <b>bajo</b> si una superficie es no metálica, Stellite / carburo / "
   "cerámica, Nitronic 60, bronce o níquel químico (ENC); o si ambas están a ≥ 38 HRC; o si difieren "
   "≥ 10 HRC con la más dura ≥ 30 HRC. Riesgo <b>alto</b>: parejas blandas de austeníticos, níquel, dúplex "
   "o titanio entre sí, y 17-4PH contra 17-4PH en la misma condición. Por encima de 316 °C el riesgo sube "
   "un nivel. En automático se descartan las parejas de riesgo alto.</p>",
   NOR, referencia="ASTM G98 (ensayo de umbral de galling)",
   relacionadas=["dureza", "hardfacing", "comp_jaula", "comp_guia"],
   guia=_g("Es la soldadura en frío de dos metales que rozan entre sí.",
           "El programa evalúa cada pareja deslizante y elige materiales que no se agarroten.",
           "Riesgo alto significa que la válvula puede trabarse en las primeras carreras.",
           "Bajo: ≥ 38 HRC ambas, Δ ≥ 10 HRC, Stellite, Nitronic 60, bronce, ENC. Más de 316 °C sube un nivel.",
           "No aplica.", "No aplica.",
           ["Asiento, jaula y guía", "Alertas de galling"],
           ["Nunca use 316 contra 316 en superficies deslizantes.",
            "Ante la duda pida al fabricante el ensayo ASTM G98 de la pareja."],
           "Obturador 316 (≈ 150 HB) y jaula 416 templada (40 HRC): diferencia > 10 HRC → riesgo bajo."))

_e("pren", "PREN (resistencia a las picaduras)",
   "<p>Número equivalente de resistencia a las picaduras: índice que compara la resistencia de los aceros "
   "inoxidables a la corrosión localizada por cloruros según su composición. Cuanto mayor, más cloruros y "
   "más temperatura tolera.</p>",
   NOR, formula="PREN = %Cr + 3,3·%Mo + 16·%N",
   tipicos="304 ≈ 19 · 316 ≈ 24 · 317 ≈ 29 · 2205 ≈ 35 · Superdúplex ≈ 41 · 6Mo ≈ 43 · C-276 ≈ 68",
   referencia="Práctica de la industria; ISO 21457", relacionadas=["picaduras", "scc_cloruros", "agente_cloruros"],
   guia=_g("Es un número que estima la resistencia de un inoxidable a las picaduras por cloruros.",
           "Se muestra en la ficha de cada material; las reglas de cloruros del programa crecen con la "
           "familia (304 < 316 < 317 < dúplex < superdúplex / 6Mo < níquel).",
           "PREN ≥ 40 es la referencia habitual para agua de mar.",
           "PREN < 25: agua dulce. 30–40: salobre. ≥ 40: agua de mar.",
           "Con PREN bajo el material pica en aguas con cloruros.",
           "Con PREN alto la resistencia mejora, pero no es inmune en rendijas calientes.",
           ["Ficha del material", "Compatibilidad con cloruros"],
           ["Use PREN para comparar, no como garantía.",
            "Verifique la composición real del certificado para calcularlo."],
           "Superdúplex 25Cr-3,5Mo-0,25N: PREN = 25 + 3,3×3,5 + 16×0,25 = 40,6."))

_e("ssc", "SSC (agrietamiento por H₂S bajo tensión)",
   "<p>Sulfide Stress Cracking: fisuración frágil de metales duros o de alta resistencia expuestos a H₂S "
   "húmedo y a una tensión (de servicio o residual). La corrosión por H₂S libera hidrógeno atómico que "
   "penetra el acero; el sulfuro impide que se recombine y salga. Ocurre sin pérdida visible de metal y "
   "puede ser repentina. Se controla limitando la dureza (≤ 22 HRC en acero al carbono, 250 HV en "
   "soldaduras) y usando materiales calificados.</p>",
   NOR, referencia="ISO 15156-2", relacionadas=["nace_mr0175", "hic", "agente_h2s", "servicio_agrio"],
   guia=_g("Es la fisuración de metales duros por H₂S húmedo.",
           "Activa el mecanismo M04 y las reglas de servicio agrio.",
           "Es más severo a pH bajo, alta pH₂S y temperatura ambiente.",
           "Detectado con pH₂S ≥ 0,3 kPa y agua libre.",
           "Por debajo de 0,3 kPa se considera potencial, no detectado.",
           "Por encima, solo materiales calificados por la norma.",
           ["Servicio agrio", "Vástago y pernos", "Internos endurecidos"],
           ["Los internos muy duros (440C, 17-4 H900) no son aceptables con H₂S.",
            "Controle la dureza de soldaduras y reparaciones."],
           "Vástago 17-4PH H900 (44 HRC) en gas agrio: riesgo de SSC; se reemplaza por H1150D (≤ 33 HRC)."))

_e("hic", "HIC / SOHIC (agrietamiento inducido por hidrógeno)",
   "<p>Hydrogen Induced Cracking: el hidrógeno del H₂S húmedo se acumula en inclusiones alargadas de aceros "
   "laminados (chapas, tubos con costura) y forma ampollas y fisuras escalonadas, sin tensión aplicada. "
   "SOHIC es la variante orientada por tensión cerca de soldaduras. Afecta principalmente a productos "
   "laminados; los cuerpos fundidos y forjados de válvulas no requieren ensayo HIC. El programa lo marca "
   "como mecanismo potencial cuando el servicio es agrio.</p>",
   NOR, referencia="ISO 15156-2; NACE TM0284 (ensayo HIC)", relacionadas=["ssc", "nace_mr0175"],
   guia=_g("Es el agrietamiento interno del acero laminado por hidrógeno del H₂S.",
           "Se informa como mecanismo potencial (M05) en servicio agrio.",
           "Es relevante para la tubería y los recipientes; en válvulas fundidas no suele gobernar.",
           "Servicio agrio: pH₂S ≥ 0,3 kPa con agua.",
           "No aplica.", "No aplica.",
           ["Mecanismos del informe"],
           ["Si la válvula tiene partes de chapa soldada, pida aceros resistentes a HIC.",
            "Coordine con el especialista de corrosión de la tubería."],
           "Válvula fundida WCB en gas agrio: HIC potencial, sin ensayo requerido para la fundición."))

_e("scc_cloruros", "SCC por cloruros",
   "<p>Corrosión bajo tensión por cloruros: fisuras ramificadas en aceros inoxidables austeníticos (304, "
   "316) expuestos a cloruros a temperatura con tensión residual o aplicada. Se vuelve probable por encima "
   "de unos 60 °C, aun con pocos cloruros si hay evaporación o rendijas. Los dúplex, superdúplex, "
   "superausteníticos y aleaciones de níquel son mucho más resistentes. El programa detecta el mecanismo "
   "M03 con Cl⁻ ≥ 50 mg/L y más de 60 °C.</p>",
   NOR, relacionadas=["picaduras", "pren", "agente_cloruros"],
   guia=_g("Es la fisuración de inoxidables austeníticos por cloruros y temperatura.",
           "Baja el nivel químico del 304 y 316 al subir la temperatura en las reglas de cloruros.",
           "Una fisura de SCC puede atravesar la pared sin corrosión visible alrededor.",
           "Riesgo con Cl⁻ ≥ 50 mg/L y T > 60 °C.",
           "Por debajo de 60 °C el riesgo es bajo.",
           "Por encima, preferir dúplex o aleaciones de níquel.",
           ["Compatibilidad con cloruros", "Mecanismos detectados"],
           ["En agua caliente con cloruros prefiera dúplex 2205.",
            "Evite zonas de evaporación (venteos, aislaciones mojadas)."],
           "Agua con 250 mg/L de Cl⁻ a 90 °C: 316 nivel C por SCC; dúplex 2205 nivel A."))

_e("picaduras", "Picaduras y corrosión en rendijas",
   "<p>Corrosión localizada que perfora la capa pasiva de los inoxidables en puntos (picaduras) o en zonas "
   "estancas como juntas, roscas y bajo depósitos (rendijas, más severa). La provocan cloruros, bromuros y "
   "oxidantes (cloro, hipoclorito, cloruro férrico) y se agrava con temperatura y pH bajo. Se mide con la "
   "temperatura crítica de picadura (CPT) y se compara con el PREN.</p>",
   NOR, referencia="ASTM G48 (ensayo de picaduras y rendijas)", relacionadas=["pren", "scc_cloruros"],
   guia=_g("Es la corrosión en puntos o en zonas estancas de los aceros inoxidables.",
           "Gobierna las reglas de cloruros y oxidantes de los inoxidables.",
           "Pocas picaduras pueden perforar una pieza aunque el resto esté intacto.",
           "Agua de mar a 25 °C: requiere PREN ≥ 40 aproximadamente.",
           "Con pocos cloruros y baja temperatura el 316 es adecuado.",
           "Con cloruros altos, oxidantes o calor se requieren superdúplex, 6Mo o níquel.",
           ["Compatibilidad química", "Mecanismo M02"],
           ["Evite zonas estancas y drene en paradas.",
            "La cloración del agua de mar aumenta el riesgo."],
           "Agua de mar con 1 mg/L de cloro libre: 316 descartado; superdúplex aceptable a temperatura "
           "ambiente."))

_e("corrosion_co2", "Corrosión por CO₂ (sweet corrosion)",
   "<p>El CO₂ disuelto en agua forma ácido carbónico que corroe el acero al carbono, a veces muy rápido y "
   "en forma localizada (mesa). Depende de la presión parcial de CO₂, la temperatura, el pH y la velocidad. "
   "El programa clasifica para el acero al carbono con agua: pCO₂ &lt; 20 kPa B (baja), 20 a 1.000 kPa C, "
   "&gt; 1.000 kPa D; los aceros 13Cr (410, CA6NM), los inoxidables y las aleaciones de níquel son "
   "resistentes.</p>",
   NOR, formula="pCO₂ = y(CO₂) · P", tipicos="Baja < 20 kPa · Moderada 20–200 kPa · Severa > 200 kPa",
   relacionadas=["agente_co2", "presion_parcial"],
   guia=_g("Es la corrosión del acero por el ácido carbónico del CO₂ húmedo.",
           "Fija el nivel químico del acero al carbono y del Cr-Mo frente al CO₂.",
           "Con pCO₂ alta el acero al carbono necesita sobreespesor e inhibidor o un material resistente.",
           "20 kPa y 200 kPa como límites de severidad (mecanismo M06).",
           "Por debajo de 20 kPa el acero al carbono suele ser adecuado con sobreespesor.",
           "Por encima de 200 kPa la corrosión puede superar varios mm por año sin inhibidor.",
           ["Compatibilidad química", "Mecanismo M06"],
           ["Combine con el análisis de H₂S: ambos gases se evalúan juntos.",
            "Para internos use 13Cr, dúplex o inoxidable."],
           "Gas al 3 % molar de CO₂ a 50 bar a: pCO₂ = 150 kPa → acero al carbono nivel C."))

_e("htha", "HTHA (ataque por hidrógeno a alta temperatura)",
   "<p>A alta temperatura y presión parcial de hidrógeno, el H₂ difunde en el acero y reacciona con los "
   "carburos formando metano: fisuras internas y pérdida de resistencia (descarburación). Se evalúa con las "
   "curvas de Nelson de API RP 941. El programa lo marca como detectado con pH₂ ≥ 690 kPa y temperatura "
   "&gt; 200 °C; en otro caso advierte el riesgo de fragilización de internos muy duros en hidrógeno.</p>",
   NOR, referencia="API RP 941", relacionadas=["agente_h2", "mat_htha"],
   guia=_g("Es el daño interno del acero por hidrógeno caliente a presión.",
           "Genera una alerta crítica y orienta a Cr-Mo o inoxidable.",
           "Es invisible desde la superficie y puede producir roturas.",
           "pH₂ ≥ 690 kPa (≈ 100 psia) y T > 200 °C (criterio del programa).",
           "Por debajo, solo se advierte la fragilización de materiales muy duros.",
           "Por encima, verificar con las curvas de Nelson.",
           ["Alertas", "Selección del cuerpo"],
           ["Use la edición vigente de API RP 941.",
            "Los aceros C-½Mo no deben considerarse seguros frente a HTHA."],
           "Hidrógeno a 30 bar y 300 °C: HTHA detectado; verificar WC6/WC9 con las curvas de Nelson."))

_e("erosion", "Erosión",
   "<p>Desgaste mecánico de las superficies por partículas sólidas, gotas a alta velocidad, mezcla "
   "líquido-vapor (flashing) o colapso de burbujas (cavitación). Si además el fluido es corrosivo, ambos "
   "efectos se potencian (erosión-corrosión). La biblioteca asigna a cada material una resistencia relativa "
   "a la erosión y a la cavitación de 0 a 10 (por ejemplo WCB 2, WC9 4, 316 2, 410 templado 5, Stellite 6 "
   "9, 440C 8, carburo 10, cerámica 10 en erosión).</p><p>Requisitos del programa: flashing → obturador y "
   "asiento con erosión ≥ 8 y jaula ≥ 5; sólidos presentes → ≥ 8; slurry → 10. Cavitación: incipiente ≥ 3, "
   "moderada ≥ 5, severa ≥ 7, extrema ≥ 8 en resistencia a cavitación.</p>",
   NOR, relacionadas=["mat_solidos", "flashing", "cavitacion", "cavitacion_dureza", "hardfacing"],
   guia=_g("Es el desgaste por impacto o roce del fluido y lo que arrastra.",
           "Fija resistencias mínimas a la erosión y la cavitación de los internos y penaliza cuerpos poco "
           "resistentes.",
           "Una resistencia baja significa vida corta del trim.",
           "Flashing 8 · sólidos 8 · slurry 10 (erosión). Cavitación 3 / 5 / 7 / 8.",
           "No aplica.", "No aplica.",
           ["Selección de internos", "Puntaje del cuerpo"],
           ["Reduzca la velocidad (válvula mayor o trim de baja velocidad) además de endurecer.",
            "En flashing use cuerpo angular con salida directa."],
           "Condensado con flashing: obturador y asiento 440C o Stellite; cuerpo WC9."))

_e("hardfacing", "Recargue duro (hardfacing) y recubrimientos",
   "<p>Capa dura aplicada sobre un material base para resistir desgaste: el más usado es el recargue de "
   "<b>Stellite 6</b> (aleación Co-Cr-W, 38–45 HRC) soldado sobre 316 en asientos y obturadores. También "
   "existen recubrimientos delgados como el níquel químico (ENC, ≈ 50 HRC) para evitar galling en jaulas, y "
   "proyecciones de carburo (HVOF). La dureza está solo en la capa: el sustrato conserva sus propiedades y "
   "su resistencia química, por eso el programa evalúa la química de ambos (el peor manda).</p>"
   "<p>En servicio agrio, los recargues Co-Cr-W son aceptables, pero los recubrimientos no protegen contra "
   "el agrietamiento del metal base.</p>",
   NOR, referencia="AWS A5.21 (ERCoCr-A); ASTM B733 (ENC)", relacionadas=["dureza", "galling", "comp_asiento"],
   guia=_g("Es una capa dura agregada sobre la superficie de trabajo.",
           "Permite cumplir la dureza requerida con un material base económico y resistente a la corrosión.",
           "Un recargue cumple dureza, pero la química del sustrato también cuenta.",
           "Stellite 6: 38–45 HRC. ENC: ≈ 50 HRC, capa de 25–75 µm.",
           "No aplica.", "No aplica.",
           ["Dureza de los internos", "Galling", "Servicio agrio"],
           ["El ENC no reemplaza al Stellite en cavitación: puede desprenderse.",
            "Pida el procedimiento de recargue y la dureza medida."],
           "Asiento 316 con Stellite 6: 40 HRC en la cara de cierre, química de 316 en el resto."))

_e("uns_astm", "UNS y ASTM",
   "<p><b>UNS</b> (Unified Numbering System) es un código único por composición química: una letra de "
   "familia y cinco dígitos (J = aceros fundidos, K = aceros forjados al carbono y aleados, S = inoxidables, "
   "N = níquel, R = metales reactivos y cobalto, C = cobre). Ej.: S31600 (316), J92900 (CF8M), N10276 "
   "(C-276).</p><p><b>ASTM</b> es la especificación de producto que fija composición, propiedades y "
   "ensayos para una forma concreta: A216 (fundiciones de acero al carbono), A351 (fundiciones inoxidables), "
   "A182 (forjas), A479 / A276 (barras), A494 (fundiciones de níquel). Un mismo UNS puede tener varias "
   "especificaciones según sea fundición, forja o barra, y un grado fundido no equivale exactamente al "
   "forjado (CF3M no es S31603).</p>",
   NOR, relacionadas=["mat_biblioteca", "b16_34_grupos"],
   guia=_g("Son los sistemas de designación de materiales: por composición (UNS) y por producto (ASTM).",
           "Identifican sin ambigüedad cada material de la biblioteca y del informe.",
           "Dos materiales con nombre comercial parecido pueden tener UNS distintos.",
           "No tiene umbral numérico.",
           "No aplica.", "No aplica.",
           ["Ficha del material", "Hoja de datos"],
           ["Especifique siempre ASTM y grado, y verifique el UNS en el certificado.",
            "No confunda S32750 con S32760 (superdúplex distintos)."],
           "Cuerpo «316»: debe especificarse ASTM A351 CF8M (fundición, UNS J92900) o A182 F316 (forja, "
           "UNS S31600)."))

_e("presion_parcial", "Presión parcial",
   "<p>En una mezcla de gases, presión que ejercería cada componente solo; es la que gobierna la corrosión "
   "por H₂S y CO₂ y los límites de las normas de servicio agrio. Se calcula con la fracción molar y la "
   "presión absoluta. El programa usa la presión de entrada máxima de los casos de la solapa 2. Para pasar "
   "de concentración disuelta (mg/L) a presión parcial usa la ley de Henry a 25 °C (aproximada): H₂S "
   "≈ 34 mg/L por kPa, CO₂ ≈ 15, O₂ ≈ 0,42.</p>",
   NOR, formula="p_i = y_i · P_abs (y_i = ppmv·10⁻⁶ o % molar/100)",
   relacionadas=["unidad_quimica", "agente_h2s", "agente_co2", "corrosion_co2"],
   guia=_g("Es la parte de la presión total que corresponde a un gas de la mezcla.",
           "Convierte ppmv y % molar en kPa para compararlos con 0,3 kPa (servicio agrio) y con los límites "
           "de cada material.",
           "La misma concentración es más severa a mayor presión.",
           "pH₂S ≥ 0,3 kPa con agua → servicio agrio.",
           "No aplica.", "No aplica.",
           ["Servicio agrio", "Corrosión por CO₂"],
           ["Use la presión absoluta máxima de operación.",
            "En líquidos, informe el gas disuelto en mg/L o la presión parcial de equilibrio."],
           "50 ppmv de H₂S a 10 bar a: 0,05 kPa (no agrio); a 100 bar a: 0,5 kPa (agrio)."))

_e("compatibilidad_ad", "Compatibilidad química A–D",
   "<p>Escala de resistencia de un material a un agente: <b>A</b> excelente (sin efecto, &lt; 0,05 mm/año), "
   "<b>B</b> bueno (efecto menor; apto con sobreespesor o vigilancia), <b>C</b> regular (no recomendado "
   "para servicio continuo), <b>D</b> no usar.</p><p>El programa obtiene el nivel de dos fuentes: sus "
   "reglas por familia de material con rangos de concentración y temperatura (construidas con guías públicas "
   "de Nickel Institute, fichas de productores de aleaciones, NACE SP0403, API 571 y manuales de "
   "fabricantes) y una tabla cualitativa A–D de resistencia química a temperatura ambiente (Mettler-Toledo / "
   "Little Giant). Si difieren se adopta la más conservadora. Un material con nivel D se descarta; con C solo "
   "se elige si no hay alternativa A o B.</p>",
   NOR, relacionadas=["agente", "concentracion_agente", "mat_quimica_regular", "mat_incompatible"],
   guia=_g("Es la calificación de cuánto resiste un material a un producto químico.",
           "Decide el descarte (D), la penalización (B y C) y el orden de preferencia de los materiales.",
           "A y B son aptos; C reduce la vida; D destruye el material.",
           "A < 0,05 mm/año. C: no recomendado. D: descarte.",
           "No aplica.", "No aplica.",
           ["Compatibilidad química", "Puntaje", "Alertas"],
           ["Para servicios críticos pida curvas de isocorrosión del fabricante de la aleación.",
            "Las reglas no cubren mezclas complejas: revise con el especialista."],
           "HCl 10 % a 40 °C: 316 D, C-276 B, Hastelloy B-2 A."))

_e("mecanismos_falla", "Mecanismos de deterioro",
   "<p>Lista de mecanismos que el programa revisa con los datos (presencia de un agente o condición → "
   "potencial o detectado; nunca confirma la falla): M01 corrosión por ácidos, M02 picaduras por cloruros, "
   "M03 SCC por cloruros, M04 SSC por H₂S, M05 HIC / SOHIC, M06 corrosión por CO₂, M07 oxidantes, M08 "
   "cáusticos, M09 HF / fluoruros, M10 azufre / sulfuros, M14 erosión por partículas, M16 cavitación, M17 "
   "flashing, M19 galling, M21 grafitización / creep, M22 HTHA o fragilización por hidrógeno, M24 SCC en "
   "amoníaco anhidro, M25 SCC por aminas, M26 SCC por nitratos, M27 ignición en oxígeno.</p>"
   "<p>A partir de ellos clasifica el medio en corrosivo, agrio, erosivo o mixto.</p>",
   NOR, relacionadas=["mat_medio", "ssc", "scc_cloruros", "erosion", "galling"],
   guia=_g("Son las formas en que el fluido y la operación pueden dañar la válvula.",
           "Se muestran en el informe y definen el medio detectado.",
           "«Detectado» indica que los datos cumplen la condición; «Potencial», que hay que vigilarlo.",
           "Cada mecanismo tiene su condición (por ejemplo M04 con pH₂S ≥ 0,3 kPa y agua).",
           "No aplica.", "No aplica.",
           ["Medio detectado", "Informe técnico"],
           ["La ausencia de un mecanismo no demuestra que no ocurra: depende de los datos cargados.",
            "Revise los potenciales con el especialista de corrosión."],
           "Agua de mar con cavitación: M02 picaduras (detectado), M16 cavitación (detectado), M19 galling "
           "(potencial)."))

_e("costo_material", "Índice de costo",
   "<p>Valor relativo del costo de cada material para ordenar las opciones: en cuerpos, WCB = 1 (por ejemplo "
   "WC9 2, CF8M 3, superdúplex 6, C-276 14); en internos, 316 = 1 (410 0,8, 316 con Stellite 2,2, Stellite "
   "macizo 6, carburo 10). Es orientativo y no reemplaza una cotización. El programa elige el material "
   "apto con menor puntaje = costo × factor químico × factor de erosión, de modo que un material barato "
   "con compatibilidad pobre puede perder frente a uno algo más caro y durable.</p>",
   NOR, relacionadas=["mat_recomendacion", "mat_biblioteca"],
   guia=_g("Es una medida relativa del costo de cada material.",
           "Junto con los factores de durabilidad ordena los candidatos aptos.",
           "Ayuda a elegir el material suficiente, no el más caro.",
           "Cuerpo WCB = 1; internos 316 = 1.",
           "No aplica.", "No aplica.",
           ["Material recomendado", "Alternativas"],
           ["Use las alternativas para negociar con el fabricante.",
            "Cuando la alternativa económica tiene nivel C, solo con sobreespesor, inhibidor y aval del "
            "especialista."],
           "WCB con química C (puntaje 2,5) frente a CF8M con química A (puntaje 3): el programa prefiere el "
           "CF8M por ser A."))

# =====================================================================================
# FLUIDO ÚNICO (desde 0.7.1 se define solo en 2-Cálculos Válvula)
# =====================================================================================
_e("variante_fluido", "Calidad / variante del fluido",
   "<p>Completa la definición del fluido en la solapa <b>2-Cálculos Válvula</b>. Es la única pregunta sobre "
   "qué fluido es: la solapa 3-Materiales la toma de aquí y no la repite. Aparece solo cuando el nombre del "
   "fluido no alcanza:</p><ul>"
   "<li><b>Agua / vapor de agua (líquido)</b>: agua industrial o de enfriamiento, potable, desmineralizada, de "
   "alimentación de caldera, condensado, agua de mar, agua producida (yacimiento) o salmuera.</li>"
   "<li><b>Definido por el usuario</b>: crudo, diésel, naftas, aceite térmico, ácido, alcalino, solvente, "
   "slurry (líquidos); gas natural, gas combustible, gas ácido o gas de proceso (gases); vapor de "
   "hidrocarburo o de proceso (vapores).</li></ul>"
   "<p>Impacta en los dos cálculos:</p><ul>"
   "<li><b>Válvula</b>: en agua de mar, agua producida y salmuera la densidad, la viscosidad y la presión de "
   "vapor del agua pura se corrigen por salinidad (3,5 %, 10 % y 20 % de NaCl equivalente, o la que resulte de "
   "los cloruros informados en la tabla de agentes). Cambian Cv, ΔP de bloqueo y cavitación.</li>"
   "<li><b>Materiales</b>: define la familia del fluido y los agentes típicos que se agregan si no se informan "
   "(agua de mar 19.400 mg/L de Cl⁻ y 8 mg/L de O₂; agua industrial 250 mg/L de Cl⁻; potable 100 mg/L; "
   "producida 60.000 mg/L; salmuera 140.000 mg/L). Slurry exige internos ≥ 55 HRC; ácido, alcalino y solvente "
   "piden el agente químico.</li></ul>",
   MAT, formula="ρ/ρw ≈ 1 + 0,0073·w ; μ/μw ≈ 1 + 0,021·w + 0,00037·w² ; Pv/Pvw = x agua (Raoult, i = 2)",
   tipicos="Agua de mar: w = 3,5 % → ρ ×1,026, μ ×1,08, Pv ×0,98. Salmuera 20 %: ρ ×1,15, μ ×1,57, Pv ×0,87.",
   referencia="Propiedades de soluciones de NaCl (correlaciones orientativas); IEC 60534-2-1 para el efecto en Cv",
   relacionadas=["fluido", "agua_libre", "mat_fluido_heredado", "agente_cloruros", "SG", "Pv"],
   guia=_g("Es la calidad del fluido: qué agua es, o qué tipo de hidrocarburo, ácido o gas cuando sus "
           "propiedades las carga el usuario.",
           "Corrige las propiedades de las aguas salinas para el cálculo de la válvula y define la familia y los "
           "agentes típicos para elegir materiales.",
           "Dos aguas con la misma presión y temperatura pueden necesitar materiales muy distintos: el agua "
           "desmineralizada admite acero al carbono o 316; el agua de mar exige dúplex o superdúplex.",
           "Salinidad > 0 en agua de mar, producida y salmuera: se corrigen SG, μ y Pv.",
           "Sin sales (desmineralizada, caldera, condensado): propiedades del agua pura y sin cloruros implícitos.",
           "Con sales: SG mayor (más ΔP por el mismo caudal), Pv menor (algo menos de cavitación) y cloruros que "
           "descartan aceros inoxidables comunes.",
           ["SG, μ y Pv (solapa 2)", "Cv y cavitación", "Familia y agentes implícitos (solapa 3)",
            "Dureza y erosión (slurry)"],
           ["Elija la calidad real del agua: es la decisión que más cambia el material.",
            "Si conoce los cloruros, cárguelos en 3-Materiales: corrigen también las propiedades.",
            "Para crudo o gas natural cargue H₂S, CO₂ y cloruros del agua asociada."],
           "Agua de mar a 25 °C: SG 1,02 (en lugar de 1,00) y Cl⁻ 19.400 mg/L → cuerpo superdúplex CD3MWCuN."))

_e("agua_libre", "Agua libre (fase acuosa)",
   "<p>Indica si hay <b>agua líquida</b> en contacto con el metal. Se define en 2-Cálculos Válvula porque es "
   "una característica del fluido. Es la condición más importante para la corrosión: la corrosión por CO₂, el "
   "agrietamiento por H₂S (SSC), las picaduras por cloruros y el ataque de ácidos necesitan agua.</p><ul>"
   "<li><b>Fija</b> cuando el fluido la impone: «Sí» en agua líquida, salmuera, ácidos, álcalis y slurry; "
   "«Según el cálculo» en vapor de agua (saturado → intermitente por condensado; sobrecalentado en todos "
   "los casos → no).</li>"
   "<li><b>Sí</b> e <b>Intermitente</b>: se evalúa con agua (intermitente incluye arranques, paradas y "
   "condensación).</li><li><b>No</b>: reglas «sin agua libre» y el servicio no puede ser agrio.</li>"
   "<li><b>Desconocida</b>: se supone agua, salvo en fluidos normalmente secos (aire, nitrógeno, oxígeno, "
   "hidrógeno, gas combustible, diésel, vapor sobrecalentado).</li></ul>"
   "<p>Cómo confirmarlo: punto de rocío de agua del gas, BS&amp;W del crudo, drenajes de condensado, "
   "temperatura de la línea frente al punto de rocío. Si en 3-Materiales se cargan agentes «Acuosa» con agua "
   "libre «No», el programa avisa y evalúa con agua (conservador).</p>",
   MAT, relacionadas=["variante_fluido", "servicio_agrio", "nace_mr0175", "corrosion_co2",
                      "mat_agua_libre_contradiccion"],
   guia=_g("Es la presencia de agua líquida en el fluido, aunque sea en pequeña cantidad.",
           "Decide si se aplican las reglas químicas con agua o sin agua y si el servicio puede ser agrio: el "
           "servicio agrio exige pH₂S ≥ 0,3 kPa con agua libre. Sin agua libre el pH no se usa.",
           "Sin agua libre la mayoría de los gases ácidos no corroen; con agua, una traza basta.",
           "Sí / Intermitente / Desconocida (salvo fluidos secos) → con agua.",
           "Servicio seco: se aceptan materiales más económicos y no se aplica NACE.",
           "Con agua: se aplican cloruros, CO₂, H₂S y pH; puede exigirse NACE MR0175 / MR0103.",
           ["Compatibilidad química", "Determinación de servicio agrio", "Mecanismos detectados", "Uso del pH"],
           ["Ante la duda deje «Desconocida» o «Intermitente»: es la opción conservadora.",
            "Gas deshidratado (TEG) a punto de rocío controlado puede declararse «No»."],
           "Gas con 500 ppmv de H₂S a 50 bar: pH₂S = 2,5 kPa. Con agua → servicio agrio; con «No» → no es "
           "agrio y no se exigen materiales NACE."))

_e("mat_fluido_heredado", "Fluido definido en 2-Cálculos Válvula",
   "<p>El recuadro superior de 3-Materiales muestra el fluido tal como se definió en la solapa 2 (tipo, "
   "fluido, calidad / variante y agua libre) y lo que el programa deduce para materiales:</p><ul>"
   "<li><b>Familia</b>: agua, salmuera, vapor, gas, hidrocarburo, ácido, alcalino, solvente, slurry.</li>"
   "<li><b>Fase</b>: líquido o gas según el tipo; «gas-líquido» si algún caso tiene flashing; "
   "«líquido-sólido» en slurry.</li>"
   "<li><b>Agua libre</b>: la elegida o la que impone el fluido.</li></ul>"
   "<p>Así no hay dos respuestas distintas para la misma pregunta. Para cambiar el fluido use el botón "
   "«Cambiar en 2-Cálculos Válvula». En 3-Materiales solo se agregan datos complementarios: industria, "
   "composición, régimen, medio esperado, norma de servicio agrio, sólidos, pH y agentes químicos.</p>",
   MAT, relacionadas=["variante_fluido", "agua_libre", "tipo_fluido", "fluido"],
   guia=_g("Es el resumen, de solo lectura, del fluido elegido en la solapa 2.",
           "Garantiza que el cálculo de la válvula y la selección de materiales usen el mismo fluido.",
           "La fase y el agua libre que ve aquí son las que usa la selección de materiales.",
           "No tiene umbral numérico.", "No aplica.", "No aplica.",
           ["Selección de materiales", "Informe técnico", "Memoria de cálculo"],
           ["Verifique el recuadro antes de interpretar la recomendación de materiales.",
            "Si el fluido no es correcto, cámbielo en la solapa 2 y recalcule."],
           "Agua / vapor de agua — Agua de mar · Líquido · agua libre Sí · cavitación moderada."))


# =====================================================================================
# ALERTAS
# =====================================================================================
def _alerta(clave, titulo, texto, umbral, accion, ejemplo, relacionadas=(), referencia=""):
    _e(clave, titulo, texto, FEN, referencia=referencia, relacionadas=relacionadas,
       guia=_g(f"Es la alerta «{titulo}» de la solapa 3-Materiales.",
               "Señala una condición de la selección de materiales que el usuario debe revisar; se muestra "
               "en la lista de alertas y en el informe técnico.",
               texto.replace("<p>", "").replace("</p>", " ").replace("<b>", "").replace("</b>", "").strip(),
               umbral, "No aplica.", "No aplica.",
               ["Selección de materiales", "Informe técnico"], accion, ejemplo))


_alerta("mat_incompatible", "Material no apto",
        "<p>El material elegido en modo manual no cumple alguna condición: temperatura, compatibilidad química "
        "(nivel D), servicio agrio, dureza, resistencia a cavitación o erosión, o presión-temperatura. El mensaje "
        "enumera los motivos y propone el material recomendado. Es una alerta crítica.</p>",
        "Se emite cuando el material manual queda descartado por cualquier criterio.",
        ["Volver a modo AUTOMÁTICO o elegir el material recomendado.",
         "Si el material es exigido por el cliente, documente la desviación."],
        "Obturador manual 316 con cavitación severa: dureza insuficiente (40 HRC requeridos).",
        ["mat_modo", "mat_manual"])
_alerta("mat_quimica_regular", "Compatibilidad química regular",
        "<p>El material elegido (o el mejor disponible) tiene nivel C frente a algún agente: funciona, pero con "
        "vida reducida y no se recomienda para servicio continuo.</p>",
        "Nivel C en la escala A–D.",
        ["Consultar aleaciones especiales o revestimientos.",
         "Si se acepta, prever sobreespesor, inspección y repuestos."],
        "Cuerpo CF8M en agua de mar a 25 °C: cloruros nivel C.", ["compatibilidad_ad"])
_alerta("mat_fuera_pt", "Fuera de los límites presión-temperatura",
        "<p>El material del cuerpo (o del bonete en manual) no alcanza la presión de diseño en la clase "
        "elegida a la temperatura de diseño según ASME B16.34, o la temperatura está fuera de la tabla del "
        "grupo, o la válvula es bridada por encima de 538 °C. Propone la clase mínima.</p>",
        "Presión de diseño > rating del grupo a la temperatura de diseño; bridadas > 538 °C.",
        ["Subir la clase de presión en la solapa 1.", "Elegir un material de mayor resistencia.",
         "Con más de 538 °C usar extremos soldados."],
        "CF8M CL150 a 300 °C admite 10,2 bar g; con diseño 15 bar g se requiere CL300.",
        ["b16_34_grupos", "rating", "clase_insuficiente"], "ASME B16.34")
_alerta("mat_no_b1634", "Material fuera de ASME B16.34",
        "<p>El material del cuerpo no figura en las tablas de ASME B16.34 (por ejemplo titanio): el rating "
        "presión-temperatura lo debe fijar el fabricante según ASME B31.3 o la Sección VIII.</p>",
        "Material sin grupo de B16.34.",
        ["Pedir al fabricante el rating y su base de cálculo."],
        "Cuerpo de titanio grado 2 para cloro húmedo.", ["b16_34_grupos"])
_alerta("mat_grupo_equivalente", "Rating por el forjado equivalente",
        "<p>La fundición elegida (por ejemplo CW2M, CX2MW, CW6MC, CU5MCuC, CY40, N7M) no figura en la "
        "Tabla 1 de B16.34; el programa usó el grupo de su forjado equivalente. Es informativa: el fabricante "
        "debe confirmar el rating.</p>",
        "Fundición no listada con grupo tomado del forjado.",
        ["Confirmar con el fabricante el rating de la fundición."],
        "CW2M (Hastelloy C fundido): se usa el grupo 3.8 de N10276.", ["b16_34_grupos"])
_alerta("mat_manual", "Selección manual",
        "<p>El material del componente fue elegido manualmente. La selección manual no es recomendada y deja "
        "fuera de responsabilidad al programa por la elección; el mensaje muestra la recomendación "
        "automática para comparar.</p>",
        "Siempre que un componente está en modo MANUAL.",
        ["Justificar la elección en el informe.", "Comparar con el análisis de la recomendación."],
        "Cuerpo manual CF8M cuando el programa recomienda CD3MWCuN.", ["mat_modo"])
_alerta("mat_sin_candidato", "Sin material apto",
        "<p>Ningún material de la biblioteca cumple a la vez temperatura, química, servicio agrio, dureza y "
        "presión-temperatura para el componente. La justificación lista las causas de descarte más "
        "frecuentes.</p>",
        "Cero candidatos aptos.",
        ["Revisar los datos del servicio y la clase de presión.",
         "Consultar al fabricante por una aleación o recubrimiento especial."],
        "Obturador en HCl 20 % caliente con cavitación extrema: ninguna aleación dura resiste el ácido.",
        ["mat_recomendacion"])
_alerta("mat_inserto", "Sin inserto blando apto",
        "<p>La clase de cierre exige asiento blando pero ningún inserto (PTFE, RPTFE, PEEK, FKM, EPDM, NBR) "
        "resiste la temperatura o el fluido con nivel A o B.</p>",
        "Temperatura fuera de rango o química C/D para todos los insertos.",
        ["Usar cierre metal-metal clase V.", "Revisar la clase de cierre requerida."],
        "Clase VI a 300 °C: supera los 260 °C del PEEK.", ["comp_asiento", "clase_cierre"])
_alerta("mat_norma_conflicto", "Servicio agrio y norma «No aplica»",
        "<p>El usuario declaró que la norma de servicio agrio no aplica, pero los datos dan pH₂S ≥ 0,3 kPa con "
        "agua libre. Por seguridad el programa aplica igual la norma.</p>",
        "pH₂S ≥ 0,3 kPa con agua y norma «No aplica (confirmado)».",
        ["Confirmar el contenido de H₂S y la presencia de agua.",
         "Si el servicio no es agrio, corregir la concentración informada."],
        "Gas con 300 ppmv de H₂S a 20 bar a (6 kPa) y norma «No aplica»: se aplica ISO 15156.",
        ["mat_norma_agrio", "nace_mr0175"])
_alerta("mat_sin_agente", "Indique el agente químico",
        "<p>La familia de fluido es Ácido, Alcalino o Solvente y no se informó ningún agente: no se puede "
        "evaluar la compatibilidad química.</p>",
        "Familia Ácido / Alcalino / Solvente sin agentes.",
        ["Cargar el agente, su unidad y concentración."],
        "Familia «Ácido» sin agente: cargar «HCl, % p/p, 15».", ["agente", "variante_fluido"])
_alerta("mat_sin_concentracion", "Agente sin concentración",
        "<p>Se cargó un agente sin concentración; el programa lo evaluó con un valor alto conservador propio "
        "del agente.</p>",
        "Celda de concentración vacía.",
        ["Ingresar la concentración medida para afinar la selección."],
        "Cloruros sin valor: se evalúa con 20.000 mg/L y el 316 queda descartado.", ["concentracion_agente"])
_alerta("mat_agente_otro", "Agente no catalogado",
        "<p>Se eligió «Otro (especificar)»: el agente no está en la base química del programa y su efecto no "
        "se evalúa.</p>",
        "Agente «Otro» en la tabla.",
        ["Consultar curvas de corrosión del fabricante.", "Describir el agente en el informe."],
        "Benceno clorado como contaminante: verificar con tablas del fabricante.", ["agente"])
_alerta("mat_medio_distinto", "Medio declarado distinto del detectado",
        "<p>El medio esperado elegido por el usuario no coincide con el que el programa detecta con los datos "
        "(agentes, cavitación, flashing, sólidos). Es informativa.</p>",
        "Medio declarado distinto del detectado (salvo «Por evaluar»).",
        ["Revisar los datos cargados o el medio declarado."],
        "Declarado «Sin mecanismo confirmado» pero hay cavitación severa: detectado «Servicio erosivo».",
        ["mat_medio", "mecanismos_falla"])
_alerta("mat_oxigeno", "Servicio de oxígeno",
        "<p>El oxígeno a presión puede encender metales y elastómeros por impacto de partículas o compresión "
        "adiabática. Requiere limpieza especial y materiales resistentes a la ignición (Monel, bronce, "
        "aleaciones de níquel) en zonas de alta velocidad; evitar titanio y NBR.</p>",
        "Fluido Oxígeno (solapa 2).",
        ["Limpieza para servicio de oxígeno (ASTM G93).", "Consultar ASTM G88 / G94 y CGA G-4.4."],
        "Válvula de control de O₂ a 30 bar: cuerpo y trim de Monel en la zona de alta velocidad.",
        ["agente_o2"], "ASTM G88 / G94; CGA G-4.4")
_alerta("mat_htha", "Ataque por hidrógeno a alta temperatura",
        "<p>La presión parcial de hidrógeno y la temperatura están en la zona donde el acero al carbono sufre "
        "descarburación interna (HTHA). Es crítica.</p>",
        "pH₂ ≥ 690 kPa y T > 200 °C.",
        ["Verificar con las curvas de Nelson (API RP 941) y usar Cr-Mo o inoxidable."],
        "Hidrógeno a 40 bar y 350 °C.", ["htha", "agente_h2"], "API RP 941")
_alerta("servicio_agrio", "Servicio agrio (H₂S)",
        "<p>pH₂S ≥ 0,3 kPa con agua libre (o servicio agrio declarado): los materiales se califican según la "
        "norma aplicada; los pernos de cuerpo-bonete expuestos o aislados pasan a ASTM A193 B7M / A194 2HM. Se "
        "deben exigir certificados con dureza y procedimientos de soldadura con ZAC ≤ 250 HV.</p>",
        "pH₂S ≥ 0,3 kPa con agua libre.",
        ["Exigir MTR con dureza.", "Pernería B7M / 2HM.", "Procedimientos de soldadura calificados."],
        "Gas con 2.000 ppmv de H₂S a 50 bar a: pH₂S = 10 kPa → servicio agrio.",
        ["nace_mr0175", "nace_mr0103", "ssc"])
_alerta("cavitacion_dureza", "Dureza mínima de los internos",
        "<p>Resume la dureza mínima exigida a obturador, asiento y jaula por la severidad de la cavitación "
        "(incipiente 25 HRC, moderada 35, severa 40, extrema 55 y trim multietapa), el flashing (40 HRC; 55 "
        "con ΔP &gt; 20 bar; jaula 38), los sólidos (trazas 35; presentes 45; slurry 55) y la caída de "
        "presión (ΔP &gt; 10 bar asiento 38; &gt; 20 bar obturador y asiento 38). La severidad se obtiene de "
        "la solapa 2: incipiente si xFz ≤ Kapp &lt; Kc; moderada si Kc ≤ Kapp &lt; (Kc + FL²)/2; severa "
        "hasta FL²; extrema con Kapp ≥ FL² o flujo bloqueado.</p>",
        "Se emite cuando hay algún requisito de dureza.",
        ["Verificar que el material ofrecido por el fabricante tenga la dureza indicada.",
         "En cavitación extrema el material solo no alcanza: usar trim multietapa."],
        "Kapp = 0,75 con Kc = 0,6 y FL² = 0,81: cavitación severa → 40 HRC.",
        ["dureza", "cavitacion", "flashing", "erosion"], "ISA-RP75.23; práctica de fabricantes")
_alerta("rating_verificado", "Rating verificado con el material del cuerpo",
        "<p>La clase de presión elegida se verificó con el grupo de ASME B16.34 del material del cuerpo "
        "seleccionado en la solapa 3, a la temperatura de diseño, y alcanza la presión de diseño. Reemplaza a "
        "la verificación referencial con acero al carbono.</p>",
        "Presión de diseño ≤ rating del grupo del cuerpo.",
        ["Mantener la clase o evaluar una menor si la tubería lo permite."],
        "CF8M CL300 a 100 °C admite 42,2 bar g; diseño 30 bar g → verificado.",
        ["b16_34_grupos", "rating", "rating_referencial"], "ASME B16.34")
_alerta("mat_agua_libre_contradiccion", "Agentes en fase acuosa sin agua libre",
        "<p>En 2-Cálculos Válvula se indicó que no hay agua libre, pero en 3-Materiales hay agentes informados "
        "disueltos en fase acuosa. Las dos cosas no pueden ser ciertas a la vez: el programa evalúa con agua "
        "(opción conservadora) hasta que se corrija uno de los datos.</p>",
        "Agua libre «No» y algún agente con fase «Acuosa».",
        ["Indicar «Sí» o «Intermitente» en «Agua libre» (solapa 2) si hay agua o condensado.",
         "Si el servicio es seco, informar los agentes en fase «Gas / vapor»."],
        "Gas seco con cloruros cargados en mg/L «Acuosa»: alerta y evaluación con agua.",
        ["agua_libre", "fase_agente"])
_alerta("mat_calidad_agua", "Calidad del agua contradictoria",
        "<p>La calidad declarada en la solapa 2 es un agua sin sales ni ácidos (desmineralizada, alimentación "
        "de caldera o condensado), pero se informaron sales o ácidos inorgánicos. La selección usa los agentes "
        "informados.</p>",
        "Agua pura declarada y halogenuros, sales o ácidos > 1 mg/L.",
        ["Corregir la calidad / variante del fluido (agua industrial, de mar o producida).",
         "Revisar las concentraciones del análisis."],
        "Condensado con 500 mg/L de cloruros: probablemente es agua industrial o hay contaminación.",
        ["variante_fluido", "agente_cloruros"])
_alerta("mat_pH_familia", "pH incoherente con el fluido",
        "<p>El pH informado no corresponde al tipo de fluido: un ácido con pH mayor que 7 o un álcali con pH "
        "menor que 7.</p>",
        "Ácido con pH > 7 o alcalino con pH < 7.",
        ["Revisar el pH o la calidad / variante del fluido."],
        "Soda cáustica con pH 4: dato mal cargado.", ["mat_pH", "variante_fluido"])
_alerta("mat_pH_sin_agua", "pH sin fase acuosa",
        "<p>Se informó pH pero el fluido no tiene agua libre: el pH solo existe en fase acuosa y no se usa.</p>",
        "pH informado y agua libre «No».",
        ["Borrar el pH o corregir el agua libre en la solapa 2."],
        "Nitrógeno seco con pH 6: el pH se ignora.", ["mat_pH", "agua_libre"])
_alerta("mat_slurry_solidos", "Slurry sin sólidos",
        "<p>El fluido es un slurry (líquido con sólidos) y en 3-Materiales se declararon sólidos ausentes. Se "
        "evalúa con sólidos presentes.</p>",
        "Variante slurry y «Sólidos: Ausentes confirmados».",
        ["Indicar «Presentes» en «Sólidos»."],
        "Pulpa minera declarada sin sólidos: se corrige a presentes.", ["variante_fluido", "mat_solidos"])
_alerta("mat_composicion_contradiccion", "Contaminantes informados",
        "<p>Se declaró «Sin contaminantes conocidos» pero hay agentes en la tabla. El programa evalúa los agentes "
        "informados.</p>",
        "Composición «Sin contaminantes conocidos» y agentes cargados.",
        ["Corregir el estado de la composición o quitar los agentes."],
        "Agua industrial «sin contaminantes» con 300 mg/L de cloruros: se evalúan los cloruros.",
        ["mat_composicion", "agente"])
