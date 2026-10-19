"""Ayuda de los agentes químicos de la solapa 3-Materiales.

Para cada agente: qué es, dónde aparece, cómo se detecta o confirma, en qué
unidades se informa y cómo las convierte el programa, valores típicos,
umbrales, mecanismos de daño y materiales que resisten o no. Los umbrales
citados son los que usan las reglas de ``quimica.py`` y
``seleccion_materiales.py``; son orientativos y de preselección.

ENTRADAS alimenta ``ayuda.A`` y GUIA alimenta ``ayuda_guia.GUIA``.
"""

ENTRADAS: dict = {}
GUIA: dict = {}

_REL_BASE = ["agente", "unidad_quimica", "concentracion_agente", "fase_agente", "compatibilidad_ad"]


def _ag(clave, titulo, texto, tipicos, referencia, relacionadas, que_es, que_hace, que_indica, umbrales,
        por_debajo, por_encima, afecta, recomendaciones, ejemplo, formula=""):
    k = "agente_" + clave
    ENTRADAS[k] = dict(titulo=titulo, texto=texto, formula=formula, tipicos=tipicos, referencia=referencia,
                       relacionadas=list(relacionadas) + [r for r in _REL_BASE if r not in relacionadas])
    GUIA[k] = dict(que_es=que_es, que_hace=que_hace, que_indica=que_indica, umbrales=umbrales,
                   por_debajo=por_debajo, por_encima=por_encima, afecta=list(afecta),
                   recomendaciones=list(recomendaciones), ejemplo=ejemplo)


_CONV_GAS = ("<p><b>Cómo lo convierte el programa.</b> La unidad base es la <b>presión parcial en kPa</b>. "
             "Con ppmv o % molar en gas se calcula p = (ppmv × 10⁻⁶) × P1 o p = (% molar / 100) × P1, con P1 "
             "absoluta máxima de operación. Si se informa disuelto en agua (mg/L, ppm masa, mol/L) se pasa a "
             "presión parcial equivalente con la ley de Henry a 25 °C (aproximada).</p>")
_CONV_MGL = ("<p><b>Cómo lo convierte el programa.</b> La unidad base es <b>mg/L</b> de la especie disuelta en el "
             "agua. ppm en masa × densidad relativa = mg/L; % p/p × 10.000 = mg/L; mol/L × masa molar × 1.000 = "
             "mg/L. ppmv y presiones parciales no tienen sentido para un ion disuelto.</p>")
_CONV_PCT = ("<p><b>Cómo lo convierte el programa.</b> La unidad base es el <b>% en masa (p/p)</b> en la fase "
             "acuosa: mg/L ÷ 10.000 ≈ % p/p (densidad ≈ 1); mol/L × masa molar ÷ 10 ≈ % p/p; el % molar se "
             "pasa a % en masa con las masas molares. Si se informa como gas (ppmv, kPa) y hay agua libre, se "
             "supone que condensa concentrado (valor conservador); sin agua se usan las reglas de gas seco.</p>")
_SIN_DATO = "Si no se ingresa concentración, el programa usa un valor alto conservador y lo avisa con una alerta."

# =====================================================================================
# GASES ÁCIDOS / REACTIVOS
# =====================================================================================
_ag("h2s", "H₂S — Sulfuro de hidrógeno",
    "<p>Gas ácido, incoloro, tóxico (olor a huevo podrido a muy baja concentración, que anestesia el olfato "
    "por encima de ~100 ppm), más pesado que el aire. Disuelto en agua forma un ácido débil y libera hidrógeno "
    "atómico en la superficie del acero: ese hidrógeno entra en el metal y lo fragiliza.</p>"
    "<p><b>Dónde aparece.</b> Gas natural y crudo «agrios» (sour), agua de producción, aguas ácidas de "
    "refinería (sour water), unidades de hidrotratamiento, aminas, gas de cola, geotermia, biogás de "
    "digestores anaeróbicos, rellenos sanitarios, pulpa kraft y aguas residuales.</p>"
    "<p><b>Cómo se detecta o confirma.</b> En gas: tubos colorimétricos (Dräger / Gastec, GPA 2377), "
    "cinta de acetato de plomo (ASTM D4084 / D4810) o cromatografía gaseosa con detector de azufre "
    "(ASTM D5504). En agua: titulación iodométrica o electrodo de ion sulfuro. Debe medirse en el punto de "
    "muestreo porque se pierde rápido de la muestra.</p>" + _CONV_GAS +
    "<p><b>Daños.</b> Agrietamiento por tensión en sulfuros (SSC) en materiales duros, agrietamiento inducido "
    "por hidrógeno (HIC / SOHIC) en chapas y tubos laminados, corrosión general por sulfuro de hierro. Por "
    "encima de ~260 °C sin agua, sulfidación del acero al carbono.</p>"
    "<p><b>Materiales.</b> Con agua libre y pH₂S ≥ 0,3 kPa el servicio es agrio y todos los materiales deben "
    "cumplir ISO 15156 (o ISO 17945 en refino): acero al carbono ≤ 22 HRC, 316 solo hasta 60 °C y 100 kPa, "
    "dúplex ≤ 10 kPa, superdúplex ≤ 20 kPa, 17-4PH solo H1150D y ≤ 3,4 kPa, aleaciones de níquel C-276/625 "
    "sin límites prácticos. No aceptables: 440C, 416, 17-4PH H900, 410 templado y aleaciones de cobre.</p>",
    "Gas dulce: < 4 ppmv. Gas agrio leve: 10–1.000 ppmv. Gas muy agrio: > 1 % molar. Agua ácida de "
    "refinería: 100–10.000 mg/L.", "ISO 15156-2 / -3 (NACE MR0175); ISO 17945 (NACE MR0103); API 571",
    ["nace_mr0175", "nace_mr0103", "ssc", "hic", "presion_parcial", "agente_sulfuros", "agente_azufre"],
    "Es un gas ácido tóxico (H₂S) que, con agua, inyecta hidrógeno en el acero y lo puede agrietar.",
    "Su presión parcial decide si el servicio es agrio y, en ese caso, qué norma (ISO 15156 o ISO 17945) y "
    "qué límites de dureza y de ambiente deben cumplir cuerpo, internos y vástago.",
    "pH₂S < 0,3 kPa: no es servicio agrio. ≥ 0,3 kPa con agua libre: servicio agrio. Cuanto mayor, menos "
    "materiales resistentes a la corrosión (CRA) quedan aptos por sus límites ambientales.",
    "Umbral de servicio agrio: pH₂S ≥ 0,3 kPa (0,05 psia) con agua libre. Límites de los materiales usados: "
    "17-4PH H1150D 3,4 kPa; dúplex 10 kPa; superdúplex 20 kPa; 316 100 kPa y 60 °C.",
    "Con pH₂S < 0,3 kPa o sin agua libre no se exigen materiales para servicio agrio; el H₂S solo cuenta como "
    "corrosión general (acero al carbono nivel B).",
    "Por encima de 0,3 kPa con agua se descartan materiales duros (440C, 416, 17-4PH H900) y se aplican los "
    "límites de dureza y ambiente de la norma; con presiones parciales altas solo quedan aleaciones de níquel.",
    ["Norma de servicio agrio", "Material del cuerpo y bonete", "Internos (obturador, asiento, jaula, guía)",
     "Vástago", "Alertas de servicio agrio"],
    ["Pida el H₂S en ppmv o % molar junto con la presión: sin la presión no hay presión parcial.",
     "Confirme si hay agua libre (aunque sea intermitente): sin agua no hay SSC.",
     "En servicio agrio exija certificados de dureza (MTR) y soldaduras con ZAC ≤ 250 HV.",
     "Pernos expuestos o aislados: ASTM A193 B7M / A194 2HM."],
    "Gas con 2.000 ppmv de H₂S a 50 bar a (5.000 kPa): pH₂S = 2.000 × 10⁻⁶ × 5.000 = 10 kPa ≥ 0,3 kPa → "
    "servicio agrio. El dúplex queda justo en su límite (10 kPa) y el 17-4PH H1150D (3,4 kPa) se descarta.",
    formula="pH₂S = y<sub>H₂S</sub> × P1")

_ag("co2", "CO₂ — Dióxido de carbono",
    "<p>Gas ácido incoloro e inodoro. Disuelto en agua forma ácido carbónico (H₂CO₃) y baja el pH; ataca al "
    "acero al carbono con la llamada corrosión «sweet» (dulce), que produce picaduras tipo «mesa» y pérdida "
    "de espesor rápida a velocidades altas.</p>"
    "<p><b>Dónde aparece.</b> Gas natural y crudo, agua de producción, recuperación mejorada con CO₂ (EOR), "
    "captura de carbono, gas de síntesis, condensado de vapor con alcalinidad del agua de reposición, "
    "fermentación y bebidas.</p>"
    "<p><b>Cómo se detecta o confirma.</b> Cromatografía de gases (ASTM D1945 / GPA 2261), tubos "
    "colorimétricos, analizadores infrarrojos; en agua, alcalinidad y CO₂ libre por titulación (APHA 4500-CO₂).</p>"
    + _CONV_GAS +
    "<p><b>Daños.</b> Corrosión general y localizada del acero al carbono y baja aleación cuando hay agua "
    "libre. En gas seco no ataca. Los aceros con 13 % Cr (410, CA6NM) y los inoxidables resisten.</p>"
    "<p><b>Reglas del programa (acero al carbono / Cr-Mo, con agua).</b> pCO₂ < 20 kPa: nivel B (apto con "
    "sobreespesor); 20 a 1.000 kPa: nivel C (no recomendado sin inhibidor); > 1.000 kPa: D. Los 9Cr soportan "
    "hasta 200 kPa (B). Martensíticos 13Cr y 17-4PH: A hasta 150 °C. Inoxidables y aleaciones de níquel: A.</p>",
    "Gas natural: 0,5–10 % molar. EOR / captura: 90–100 %. Gradación de severidad para el acero al carbono: "
    "< 20 kPa baja, 20–200 kPa moderada, > 200 kPa severa.",
    "NORSOK M-001 / M-506 (criterio); API 571; modelo de de Waard-Milliams",
    ["corrosion_co2", "presion_parcial", "agente_h2co3", "agente_h2s"],
    "Es un gas ácido (CO₂) que con agua libre forma ácido carbónico y corroe el acero al carbono.",
    "Su presión parcial define el nivel de compatibilidad del acero al carbono y de los aceros de baja "
    "aleación; empuja la selección hacia 13Cr, inoxidable o dúplex.",
    "Más presión parcial y más temperatura → más corrosión del acero al carbono. Sin agua no hay ataque.",
    "pCO₂ < 20 kPa: baja (acero al carbono B). 20–200 kPa: moderada. > 200 kPa: severa. El programa "
    "califica el acero al carbono C entre 20 y 1.000 kPa y D por encima de 1.000 kPa.",
    "Por debajo de 20 kPa el acero al carbono con sobreespesor de corrosión suele ser suficiente.",
    "Por encima de 20 kPa el cuerpo de acero al carbono queda C (inhibidor y sobreespesor obligatorios) y "
    "conviene inoxidable, 13Cr o dúplex en los internos.",
    ["Material del cuerpo y bonete", "Internos", "Mecanismo M06 (corrosión por CO₂)",
     "Alertas de compatibilidad química"],
    ["Informe el CO₂ en % molar del gas y verifique la presión de operación.",
     "Indique si hay agua libre: el CO₂ seco no corroe.",
     "Si también hay H₂S, cargue ambos: el H₂S decide la norma de servicio agrio."],
    "Gas con 5 % molar de CO₂ a 50 bar a: pCO₂ = 0,05 × 5.000 = 250 kPa con agua → corrosión severa; el "
    "acero al carbono queda nivel C y el programa busca un cuerpo inoxidable o dúplex.",
    formula="pCO₂ = y<sub>CO₂</sub> × P1")

_ag("so2", "SO₂ — Dióxido de azufre",
    "<p>Gas incoloro de olor picante, producto de la combustión de azufre. Con agua forma ácido sulfuroso "
    "(H₂SO₃), reductor y corrosivo; con oxígeno puede pasar a SO₃ y ácido sulfúrico.</p>"
    "<p><b>Dónde aparece.</b> Gases de combustión de carbón y fueloil, plantas de ácido sulfúrico, recuperación "
    "de azufre (Claus), tostación de minerales, pulpa al sulfito, conservantes de alimentos y vino.</p>"
    "<p><b>Cómo se detecta.</b> Analizadores UV / IR de chimenea, tubos colorimétricos, titulación con yodo "
    "en solución (método Monier-Williams en alimentos).</p>" + _CONV_GAS +
    "<p><b>Reglas del programa.</b> Húmedo: acero al carbono, 410 y bronce D; 304 C; 316/317 B hasta 60 °C; "
    "dúplex A hasta 60 °C; superdúplex, 6Mo, Aleación 20, 825, C-276 y titanio A hasta 100 °C. Seco: acero al "
    "carbono A hasta 300 °C. Elastómero NBR: D.</p>"
    "<p><b>Riesgo particular.</b> Punto de rocío ácido: si el gas se enfría por debajo de ~120–150 °C condensa "
    "ácido concentrado sobre las paredes.</p>",
    "Gases de combustión: 200–3.000 ppmv. Plantas de ácido: 7–12 % molar.", "API 571; tabla de resistencia "
    "química A–D", ["agente_so3", "agente_h2so4", "presion_parcial"],
    "Es un gas ácido (SO₂) que con agua forma ácido sulfuroso.",
    "Decide la compatibilidad de cuerpo e internos en servicios con gases de combustión o de plantas de ácido.",
    "Seco es poco agresivo; húmedo ataca al acero al carbono y a los inoxidables simples.",
    "Con agua: 316 B hasta 60 °C y C hasta 100 °C. Seco: acero al carbono A hasta 300 °C.",
    "Sin agua libre (gas por encima del punto de rocío) el acero al carbono es apto.",
    "Con condensación húmeda el acero al carbono se descarta y se necesitan 316L, dúplex o aleaciones superiores.",
    ["Material del cuerpo y bonete", "Internos", "Elastómeros y asientos blandos",
     "Alertas de compatibilidad química"],
    ["Verifique que la temperatura del gas quede siempre por encima del punto de rocío ácido.",
     "Si hay condensación, informe la fase del agente como «Acuosa».",
     "Evite NBR; use PTFE o FKM."],
    "Gas de combustión con 1.000 ppmv de SO₂ a 1,2 bar a y condensado presente: pSO₂ = 0,12 kPa; el "
    "programa califica el acero al carbono D y propone 316 o superior según la temperatura.")

_ag("so3", "SO₃ — Trióxido de azufre",
    "<p>Óxido de azufre muy reactivo; con la mínima humedad forma ácido sulfúrico concentrado y niebla ácida. "
    "En la industria se maneja como óleum (SO₃ disuelto en H₂SO₄).</p>"
    "<p><b>Dónde aparece.</b> Plantas de ácido sulfúrico (convertidor y torre de absorción), sulfonación de "
    "detergentes, gases de combustión de fueloil con vanadio.</p>"
    "<p><b>Cómo se detecta.</b> Método de condensación controlada (EPA 8A), titulación del óleum.</p>"
    + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Con agua libre se evalúa como ácido sulfúrico al 98 %. Seco: acero al "
    "carbono B hasta 300 °C; EPDM y NBR D.</p>",
    "Óleum: 20–65 % de SO₃ libre. Gases de combustión: 1–50 ppmv.", "Tabla de resistencia química A–D; "
    "guías del Nickel Institute para ácido sulfúrico", ["agente_h2so4", "agente_so2"],
    "Es el óxido de azufre que, con humedad, forma ácido sulfúrico concentrado.",
    "El programa lo trata como H₂SO₄ al 98 % cuando hay agua, y con reglas de gas seco cuando no la hay.",
    "Seco es manejable con acero al carbono; con humedad se comporta como sulfúrico concentrado.",
    "Ácido sulfúrico 93–99 % con acero al carbono: solo hasta 30 °C y baja velocidad (nivel C en el trim).",
    "Sin humedad, acero al carbono B hasta 300 °C.",
    "Con humedad, ataque fuerte a elastómeros y a la mayoría de los metales; usar Aleación 20, C-276 o PTFE.",
    ["Material del cuerpo y bonete", "Internos", "Asientos blandos"],
    ["Mantenga el sistema seco y caliente.", "Use PTFE como asiento y empaquetadura.",
     "Consulte curvas de isocorrosión del fabricante."],
    "Óleum con humedad: el programa evalúa H₂SO₄ 98 % y descarta EPDM, NBR y acero al carbono en internos.")

_ag("cl2", "Cl₂ — Cloro",
    "<p>Gas amarillo verdoso, oxidante fuerte y tóxico. Su comportamiento depende por completo del agua: "
    "<b>seco</b> se maneja en acero al carbono; <b>húmedo</b> forma HCl + HOCl y destruye casi todos los "
    "metales salvo el titanio.</p>"
    "<p><b>Dónde aparece.</b> Plantas cloro-álcali, potabilización y desinfección, fabricación de PVC, "
    "blanqueo de pulpa, química fina.</p>"
    "<p><b>Cómo se detecta.</b> Analizadores electroquímicos, tubos colorimétricos; en agua, cloro libre por "
    "DPD (APHA 4500-Cl G). La humedad del cloro seco se mide con higrómetros (debe ser < 50 ppm).</p>" + _CONV_GAS +
    "<p><b>Reglas del programa.</b> Húmedo: todos los metales D salvo titanio (A hasta 100 °C) y C-276 (B "
    "hasta 40 °C); PTFE A; FKM B. Seco: acero al carbono A hasta 120 °C y B hasta 200 °C; austeníticos A "
    "hasta 150 °C; <b>titanio D</b> (reacciona violentamente con cloro seco); EPDM y NBR D.</p>",
    "Cloro seco de proceso: 99,5 %. Agua potable: 0,2–2 mg/L de cloro libre.", "Euro Chlor GEST; tabla A–D",
    ["agente_hipoclorito", "agente_hcl"],
    "Es un gas halógeno oxidante (Cl₂) cuya agresividad cambia por completo si hay humedad.",
    "La fase acuosa elegida invierte la recomendación: titanio en cloro húmedo, acero al carbono en cloro seco.",
    "Con agua: casi todo se corroe salvo titanio. Sin agua: el titanio es peligroso y el acero al carbono es apto.",
    "Seco: humedad < 50 ppm y acero al carbono hasta 120 °C. Húmedo: titanio hasta 100 °C.",
    "En cloro seco frío el acero al carbono es la elección económica.",
    "Con humedad o temperatura alta solo resisten titanio (húmedo), aleaciones de níquel y PTFE.",
    ["Material del cuerpo y bonete", "Internos", "Asientos blandos", "Alertas de compatibilidad química"],
    ["Defina con precisión si hay agua libre: cambia el material de cuerpo.",
     "Nunca use titanio en cloro seco.", "Use asientos y empaquetaduras de PTFE."],
    "Cloro con 100 ppmv a 10 bar a: con agua el titanio queda A; marcando «Fase acuosa: No» el titanio pasa a "
    "D y el acero al carbono a A.")

_ag("o2", "O₂ — Oxígeno",
    "<p>Gas oxidante. Disuelto en agua es el motor de la corrosión del acero al carbono (cada mg/L acelera la "
    "pérdida de espesor) y de las picaduras de los inoxidables junto con los cloruros. Puro y a presión, es "
    "un riesgo de <b>ignición</b>: metales y elastómeros pueden arder por impacto de partículas o compresión "
    "adiabática.</p>"
    "<p><b>Dónde aparece.</b> Agua aireada (cruda, de enfriamiento, de mar: ~8 mg/L a 25 °C), agua de "
    "alimentación de calderas (desaireada a < 7–20 ppb), aire comprimido, oxígeno industrial y medicinal.</p>"
    "<p><b>Cómo se detecta.</b> Oxímetros de membrana u ópticos (ASTM D888), método Winkler; en gas, "
    "analizadores paramagnéticos o de zirconia.</p>" + _CONV_GAS +
    "<p>Henry a 25 °C: 1 kPa de O₂ ≈ 0,42 mg/L disueltos, de modo que el agua saturada con aire (8 mg/L) "
    "equivale a ~19 kPa.</p>"
    "<p><b>Reglas del programa (en agua).</b> Acero al carbono: A con < 0,05 kPa (≈ 20 ppb, agua desaireada); "
    "B hasta 0,5 kPa; B hasta 25 kPa y 120 °C (agua aireada); C por encima. Inoxidables y aleaciones: A; "
    "Hastelloy B-2 C con oxígeno. En oxígeno gaseoso: titanio D por encima de 50 kPa, NBR C.</p>",
    "Agua aireada: 6–9 mg/L. Calderas: < 0,007–0,02 mg/L. Aire: 21 % molar.",
    "ASTM D888; ASTM G88 / G94; CGA G-4.4; EIGA 13", ["agente_cloruros", "picaduras"],
    "Es el oxígeno disuelto o gaseoso; en agua corroe el acero y en gas puro puede provocar incendio metálico.",
    "Define si el acero al carbono es apto en agua y activa las alertas de servicio de oxígeno.",
    "Agua desaireada: acero al carbono excelente. Agua aireada caliente: acero al carbono regular.",
    "< 0,05 kPa (≈ 20 ppb): A para el acero al carbono. Agua aireada (≈ 19 kPa): B hasta 120 °C, C por encima.",
    "Con oxígeno muy bajo el acero al carbono dura décadas en agua.",
    "Con agua aireada caliente el acero al carbono pierde espesor; en oxígeno gaseoso a presión hay riesgo de "
    "ignición y se exige limpieza especial.",
    ["Material del cuerpo y bonete", "Internos", "Alerta de servicio de oxígeno"],
    ["Para agua de caldera informe el oxígeno en mg/L o ppb.",
     "Para oxígeno gaseoso elija «Oxígeno» como fluido: se activa la alerta de ignición (ASTM G88/G94).",
     "Evite titanio y NBR en oxígeno."],
    "Agua de enfriamiento con 8 mg/L de O₂ a 90 °C: el programa convierte a ≈ 19 kPa y califica el acero al "
    "carbono B (apto con sobreespesor).")

_ag("nh3", "NH₃ — Amoníaco",
    "<p>Gas alcalino de olor penetrante, muy soluble en agua (forma hidróxido de amonio). Se maneja también "
    "como líquido anhidro a presión o refrigerado (−33 °C).</p>"
    "<p><b>Dónde aparece.</b> Plantas de amoníaco y urea, refrigeración industrial, desnitrificación (SCR), "
    "aguas ácidas de refinería, fertilizantes, tratamiento de agua de calderas.</p>"
    "<p><b>Cómo se detecta.</b> Tubos colorimétricos, electrodos selectivos, titulación ácida, método de "
    "Nessler o fenato para trazas en agua.</p>" + _CONV_PCT +
    "<p><b>Daños.</b> Corrosión bajo tensión (SCC) de aleaciones de cobre (latón, bronce) incluso en trazas "
    "húmedas; SCC del acero al carbono de alta resistencia en amoníaco anhidro contaminado con aire y sin "
    "agua (se inhibe con ≥ 0,2 % de agua).</p>"
    "<p><b>Reglas del programa.</b> Aceros, inoxidables, aleaciones de níquel y titanio: A. Monel B hasta 3 % "
    "y 40 °C. Bronce D. FKM D (el amoníaco ataca el fluoroelastómero). EPDM y PTFE A.</p>",
    "Agua amoniacal: 1–30 % p/p. Amoníaco anhidro: 99,5 % con 0,2–0,5 % de agua como inhibidor.",
    "API 571; CGA G-2.1; tabla A–D", ["agente_nh4oh", "agente_aminas"],
    "Es una base gaseosa (NH₃) que ataca al cobre y puede agrietar al acero al carbono si está anhidro.",
    "Descarta bronce, latón y FKM y genera la alerta de SCC en amoníaco anhidro cuando no hay agua.",
    "Para aceros e inoxidables es benigno; para cobre y FKM es destructivo.",
    "Cualquier concentración: bronce D. Amoníaco anhidro sin agua: riesgo de SCC del acero al carbono.",
    "En trazas sigue siendo peligroso para el cobre.",
    "En concentración alta: elastómeros FKM inaceptables; use EPDM o PTFE.",
    ["Guía (bujes de bronce)", "Asientos blandos y elastómeros", "Mecanismo M24 (SCC en amoníaco anhidro)"],
    ["No use bronce ni latón en ningún componente mojado.",
     "En amoníaco anhidro verifique el contenido de agua (≥ 0,2 %).",
     "Prefiera EPDM o PTFE en asientos."],
    "Amoníaco anhidro con fase acuosa «No»: el programa agrega el mecanismo de SCC en amoníaco anhidro y "
    "descarta bujes de bronce.")

_ag("h2", "H₂ — Hidrógeno",
    "<p>Gas muy liviano, inflamable, que difunde dentro de los metales. A temperatura ambiente fragiliza aceros "
    "de muy alta resistencia; a alta temperatura y presión reacciona con el carbono del acero y forma metano "
    "en los bordes de grano (ataque por hidrógeno a alta temperatura, HTHA).</p>"
    "<p><b>Dónde aparece.</b> Hidrotratamiento e hidrocraqueo en refinería, reformado, síntesis de amoníaco y "
    "metanol, electrólisis, celdas de combustible y redes de hidrógeno verde.</p>"
    "<p><b>Cómo se detecta.</b> Cromatografía de gases (ASTM D1946), analizadores de conductividad térmica.</p>"
    + _CONV_GAS +
    "<p><b>Reglas del programa.</b> Con pH₂ ≥ 690 kPa y T > 200 °C se detecta HTHA y se pide verificar con "
    "las curvas de Nelson (API RP 941): Cr-Mo o inoxidable. Titanio: B hasta 10 kPa y 80 °C, D por encima "
    "(forma hidruros). Por debajo de esas condiciones se avisa evitar internos de dureza muy alta (> 38 HRC).</p>",
    "Hidrotratamiento: 30–200 bar de H₂ a 300–400 °C. Hidrógeno verde: 30–700 bar a temperatura ambiente.",
    "API RP 941 (curvas de Nelson); ASME B31.12; ISO 11114-4", ["htha", "presion_parcial"],
    "Es el gas hidrógeno; a alta temperatura daña el acero al carbono (HTHA) y a presión fragiliza aceros duros.",
    "Activa el mecanismo HTHA y su alerta crítica, y descarta titanio.",
    "La combinación presión parcial – temperatura decide el riesgo; ninguna de las dos sola.",
    "HTHA: pH₂ ≥ 690 kPa (≈ 100 psia) y T > 200 °C. Titanio: D con pH₂ > 10 kPa.",
    "A baja temperatura el acero al carbono es apto; solo se cuidan los internos de dureza muy alta.",
    "En la zona de HTHA el acero al carbono no es aceptable: Cr-Mo (WC6, WC9) o inoxidable según Nelson.",
    ["Material del cuerpo y bonete", "Mecanismo M22 y alerta HTHA", "Internos de alta dureza"],
    ["Informe el H₂ en % molar y la presión total.", "Revise las curvas de Nelson de API RP 941.",
     "Evite titanio en hidrógeno."],
    "Hidrotratadora con 80 % molar de H₂ a 60 bar a y 350 °C: pH₂ = 4.800 kPa > 690 kPa y T > 200 °C → "
    "alerta crítica de HTHA.")

# =====================================================================================
# HALOGENUROS / SALES
# =====================================================================================
_ag("cloruros", "Cl⁻ — Cloruros",
    "<p>Ion cloruro disuelto en agua. Es el enemigo principal de los aceros inoxidables: rompe la película "
    "pasiva y provoca <b>picaduras</b>, <b>corrosión en rendijas</b> y, por encima de ~60 °C, "
    "<b>corrosión bajo tensión por cloruros (Cl-SCC)</b> en los austeníticos 304/316.</p>"
    "<p><b>Dónde aparece.</b> Agua de mar (≈ 19.400 mg/L), agua producida (10.000–200.000 mg/L), salmueras, "
    "agua de enfriamiento concentrada, agua de pozo, condensados contaminados, procesos con HCl o sales "
    "cloradas, descongelantes.</p>"
    "<p><b>Cómo se detecta.</b> Titulación con nitrato de plata (método de Mohr, ASTM D512), cromatografía "
    "iónica (ASTM D4327), electrodo selectivo, conductividad como indicio.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa (agua neutra aireada).</b></p><ul>"
    "<li>304: A hasta 50 mg/L a cualquier temperatura o 200 mg/L hasta 60 °C; B hasta 200 mg/L y 100 °C o "
    "1.000 mg/L y 40 °C.</li>"
    "<li>316: A hasta 1.000 mg/L y 40 °C; B hasta 200 mg/L y 100 °C, 1.000 mg/L y 60 °C o 3.000 mg/L y 30 °C; "
    "C hasta 1.000 mg/L y 120 °C.</li>"
    "<li>Dúplex 2205: A hasta 1.000 mg/L y 150 °C o 3.600 mg/L y 80 °C; B hasta 10.000 mg/L y 40 °C.</li>"
    "<li>Superdúplex y 6Mo (PREN ≥ 40): A hasta 25.000 mg/L y 30 °C (agua de mar fría); B hasta 60 °C.</li>"
    "<li>Titanio: A hasta 80 °C a cualquier concentración. C-276: A hasta 150 °C.</li>"
    "<li>Acero al carbono: B hasta 1.000 mg/L y 100 °C; C por encima (la corrosión la gobierna sobre todo el "
    "oxígeno).</li></ul>"
    "<p>Con 50 mg/L o más y temperatura > 60 °C se detecta Cl-SCC.</p>",
    "Agua potable: 10–250 mg/L. Agua de enfriamiento: 200–2.000 mg/L. Agua de mar: 19.400 mg/L. Agua "
    "producida: 10.000–200.000 mg/L.", "ASTM D512; ISO 21457; guías del Nickel Institute; ASTM G48",
    ["scc_cloruros", "picaduras", "pren", "agente_nacl", "agente_bromuros", "agente_o2"],
    "Es el ion cloruro (Cl⁻) disuelto en agua, causa de picaduras y agrietamiento de los inoxidables.",
    "Define qué familia de inoxidable o aleación resiste (304, 316, dúplex, superdúplex, titanio) para cuerpo, "
    "internos y vástago, y detecta la Cl-SCC.",
    "Más cloruro y más temperatura → se necesita más PREN (Cr + 3,3 Mo + 16 N).",
    "316: 1.000 mg/L a 40 °C. Dúplex: 3.600 mg/L a 80 °C. Superdúplex: 25.000 mg/L a 30 °C. Cl-SCC: ≥ 50 mg/L "
    "y > 60 °C.",
    "Con cloruros bajos (< 50–200 mg/L) los austeníticos 304/316 son aptos incluso en caliente.",
    "Con cloruros altos o calientes el 316 sufre picaduras y SCC: dúplex, superdúplex, 6Mo o titanio.",
    ["Material del cuerpo y bonete", "Internos (obturador, asiento, jaula, guía)", "Vástago",
     "Mecanismos M02 y M03"],
    ["Pida el análisis de cloruros en mg/L y la temperatura máxima.",
     "Las zonas estancas y las rendijas concentran cloruros: considérelo en servicio intermitente.",
     "No confunda mg/L de Cl⁻ con mg/L de NaCl (NaCl contiene 60,7 % de Cl⁻)."],
    "Agua de mar a 25 °C (19.400 mg/L): 316 queda C, el programa elige CD3MWCuN (superdúplex) para el cuerpo; "
    "a 90 °C con 250 mg/L todos los austeníticos quedan C por riesgo de Cl-SCC.")

_ag("bromuros", "Br⁻ — Bromuros",
    "<p>Ion bromuro, de la misma familia que el cloruro pero algo más agresivo para la película pasiva de los "
    "inoxidables.</p><p><b>Dónde aparece.</b> Salmueras de completación (CaBr₂, ZnBr₂), agua de mar (≈ 65 mg/L), "
    "biocidas bromados en torres de enfriamiento, química del bromo.</p>"
    "<p><b>Cómo se detecta.</b> Cromatografía iónica (ASTM D4327), electrodo selectivo.</p>" + _CONV_MGL +
    "<p><b>Regla del programa.</b> Se evalúa como cloruros equivalentes: 1 mg/L de Br⁻ ≈ 1,5 mg/L de Cl⁻ "
    "(factor conservador por su mayor agresividad). Aplican entonces los límites de 316, dúplex y superdúplex "
    "de la ayuda de cloruros.</p>",
    "Agua de mar: 65 mg/L. Salmueras de completación: 100.000–500.000 mg/L.", "ISO 21457; API 571",
    ["agente_cloruros", "picaduras", "scc_cloruros"],
    "Es el ion bromuro (Br⁻), un halogenuro parecido al cloruro y algo más agresivo.",
    "Se suma a los cloruros con un factor 1,5 para elegir el inoxidable o la aleación.",
    "Mismo comportamiento que los cloruros: más concentración y temperatura exigen más PREN.",
    "Como cloruros × 1,5; por ejemplo 316 apto hasta ≈ 670 mg/L de Br⁻ a 40 °C.",
    "En trazas (agua de mar normal) su efecto queda cubierto por los cloruros.",
    "En salmueras de bromuro se requieren superdúplex, aleaciones de níquel o titanio.",
    ["Material del cuerpo y bonete", "Internos", "Mecanismo M02"],
    ["Informe bromuros por separado de los cloruros.", "En salmueras de completación consulte al fabricante."],
    "Salmuera con 2.000 mg/L de Br⁻: equivale a 3.000 mg/L de Cl⁻; a 50 °C el 316 queda C.")

_ag("fluoruros", "F⁻ — Fluoruros",
    "<p>Ion fluoruro disuelto. En medio ácido se convierte en ácido fluorhídrico y ataca titanio, vidrio, "
    "cerámicas y sílice incluso en ppm.</p><p><b>Dónde aparece.</b> Producción de ácido fosfórico y "
    "fertilizantes, aluminio (criolita), fluoración de agua potable (≈ 1 mg/L), grabado de semiconductores, "
    "alquilación con HF.</p><p><b>Cómo se detecta.</b> Electrodo selectivo de fluoruro (ASTM D1179), "
    "cromatografía iónica.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa.</b> Titanio: B hasta 10 mg/L y 60 °C, C hasta 100 mg/L y 40 °C, D por encima. "
    "Austeníticos: A hasta 100 mg/L y 60 °C, B hasta 1.000 mg/L. Aleaciones de níquel y Monel: A. Cerámica: B "
    "hasta 100 mg/L, C por encima. RPTFE con fibra de vidrio: B solo hasta 100 mg/L.</p>",
    "Agua potable: 0,7–1,5 mg/L. Ácido fosfórico de proceso: 0,5–2 % de F.", "ASTM D1179; API 571",
    ["agente_hf"], "Es el ion fluoruro (F⁻); en medio ácido equivale a ácido fluorhídrico.",
    "Descarta titanio, cerámicas y PTFE con vidrio cuando su concentración lo exige.",
    "Pocos mg/L ya afectan al titanio y a las cerámicas.",
    "Titanio: 10 mg/L a 60 °C. Austeníticos: 100 mg/L a 60 °C (A).",
    "En agua potable fluorada no tiene efecto práctico.",
    "Con fluoruros altos y pH ácido: Monel o aleaciones de níquel; nunca titanio ni cerámica.",
    ["Internos cerámicos", "Material del cuerpo (titanio)", "Asientos de RPTFE"],
    ["Si el pH es ácido, informe también HF.", "Evite internos cerámicos y titanio."],
    "Ácido fosfórico con 500 mg/L de F⁻: el titanio queda D y la cerámica C.")

_ag("nacl", "NaCl — Cloruro de sodio",
    "<p>Sal común disuelta; aporta iones cloruro. 1 mg/L de NaCl contiene 0,607 mg/L de Cl⁻.</p>"
    "<p><b>Dónde aparece.</b> Agua de mar (3,5 % ≈ 35.000 mg/L de sales), salmueras, agua producida, "
    "plantas cloro-álcali, alimentos, regeneración de ablandadores.</p>"
    "<p><b>Cómo se detecta.</b> Por cloruros (ASTM D512) o conductividad / salinidad (refractómetro, "
    "densímetro).</p>" + _CONV_MGL +
    "<p><b>Regla del programa.</b> Se convierte a cloruros: Cl⁻ = 0,607 × NaCl y se aplican las reglas de "
    "cloruros (316 A hasta 1.000 mg/L de Cl⁻ a 40 °C, dúplex A hasta 3.600 mg/L a 80 °C, etc.).</p>",
    "Agua de mar: 3,5 % p/p (≈ 35.000 mg/L). Salmuera saturada: 26 % p/p.", "ASTM D512; ISO 21457",
    ["agente_cloruros", "picaduras"], "Es la sal común disuelta, fuente de iones cloruro.",
    "El programa la pasa a cloruros (× 0,607) para elegir el inoxidable.",
    "Equivale a sus cloruros: 1 % de NaCl ≈ 6.070 mg/L de Cl⁻.",
    "Con 3,5 % (agua de mar) el 316 queda C y se requiere superdúplex o 6Mo.",
    "Con salinidad baja (< 0,15 % ≈ 1.000 mg/L Cl⁻) el 316 es apto en frío.",
    "Con salmuera concentrada: superdúplex, titanio o aleaciones de níquel.",
    ["Material del cuerpo y bonete", "Internos", "Mecanismo M02"],
    ["Use esta entrada si el análisis está en NaCl; si está en Cl⁻ use «Cloruros».",
     "No cargue ambos para la misma sal: se sumarían."],
    "Salmuera al 3,5 % p/p de NaCl a 25 °C → 35.000 mg/L × 0,607 = 21.245 mg/L de Cl⁻ → 316 C; superdúplex A.")

_ag("cacl2", "CaCl₂ — Cloruro de calcio",
    "<p>Sal muy soluble e higroscópica; aporta cloruros (0,639 mg/L de Cl⁻ por mg/L de CaCl₂).</p>"
    "<p><b>Dónde aparece.</b> Salmueras de refrigeración, fluidos de completación de pozos, descongelantes, "
    "agua producida, salmueras de secado.</p><p><b>Cómo se detecta.</b> Cloruros (ASTM D512) y dureza cálcica "
    "por EDTA; densidad de la salmuera.</p>" + _CONV_MGL +
    "<p><b>Regla del programa.</b> Se convierte a cloruros equivalentes (× 0,639) y se aplican las reglas de "
    "cloruros. Si no se informa la concentración se supone 30 % p/p (salmuera típica).</p>",
    "Salmuera de refrigeración: 20–30 % p/p. Completación: hasta 40 % p/p.", "ISO 21457",
    ["agente_cloruros"], "Es una sal de calcio que aporta cloruros en salmueras.",
    "Se suma a los cloruros para seleccionar la aleación.",
    "Las salmueras de CaCl₂ son muy concentradas: casi siempre exigen aleaciones de alto PREN.",
    "30 % p/p equivale a ≈ 190.000 mg/L de Cl⁻: 316 y dúplex D a cualquier temperatura.",
    "Diluida (< 0,15 %) se comporta como agua con pocos cloruros.",
    "Concentrada exige superdúplex en frío, titanio o C-276.",
    ["Material del cuerpo y bonete", "Internos"],
    ["Informe la concentración real; el valor por defecto es muy conservador.",
     "En salmueras de refrigeración controle el pH y el oxígeno."],
    "Salmuera de refrigeración al 25 % p/p a −10 °C: ≈ 160.000 mg/L de Cl⁻ → 316 D, superdúplex C, titanio A.")

_ag("mgcl2", "MgCl₂ — Cloruro de magnesio",
    "<p>Sal que aporta cloruros y que al hidrolizarse acidifica el medio: más agresiva que el NaCl a igual "
    "contenido de cloruro. Las soluciones calientes de MgCl₂ son el ensayo clásico de SCC de los "
    "inoxidables (ASTM G36).</p><p><b>Dónde aparece.</b> Agua de mar (≈ 0,5 %), salmueras de salinas, "
    "producción de magnesio, polvos antipolvo de caminos.</p><p><b>Cómo se detecta.</b> Cloruros y magnesio "
    "por EDTA o ICP.</p>" + _CONV_MGL +
    "<p><b>Regla del programa.</b> Se evalúa como cloruros con factor 0,90 (más que su contenido real de 0,745 "
    "por la acidificación).</p>",
    "Agua de mar: ≈ 5.000 mg/L. Salmueras residuales: 20–35 % p/p.", "ASTM G36; ISO 21457",
    ["agente_cloruros", "scc_cloruros"], "Es una sal que aporta cloruros y acidifica el agua al hidrolizarse.",
    "Se suma a los cloruros con factor 0,90 para elegir la aleación.",
    "Es especialmente peligrosa en caliente para los austeníticos (SCC).",
    "Como cloruros × 0,90.", "Diluida: como agua con cloruros bajos.",
    "Concentrada y caliente: SCC segura de 304/316; usar dúplex, superdúplex o aleaciones de níquel.",
    ["Material del cuerpo y bonete", "Internos", "Mecanismo M03"],
    ["Evite austeníticos en MgCl₂ caliente.", "Informe la concentración real."],
    "Solución con 1 % p/p de MgCl₂ a 70 °C: 10.000 mg/L × 0,90 = 9.000 mg/L de Cl⁻ → 316 D por Cl-SCC.")

_ag("fecl3", "FeCl₃ — Cloruro férrico",
    "<p>Sal oxidante y ácida: combina cloruros con el ion Fe³⁺, que eleva el potencial y provoca picaduras "
    "muy rápidas en inoxidables (es el reactivo del ensayo de picaduras ASTM G48).</p>"
    "<p><b>Dónde aparece.</b> Coagulante en tratamiento de agua, grabado de circuitos impresos, decapado, "
    "corrosión en procesos con HCl y hierro disuelto.</p><p><b>Cómo se detecta.</b> Hierro total y férrico "
    "por espectrofotometría (fenantrolina), cloruros, potencial redox.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa.</b> Acero al carbono, martensíticos, Monel, B-2 y bronce: D. 304/316: B solo "
    "hasta 100 mg/L y 40 °C. Superdúplex/6Mo: B hasta 5.000 mg/L y 40 °C. C-276: A hasta 60.000 mg/L y 60 °C. "
    "Titanio: A hasta 100 °C. PTFE, FKM y EPDM: A.</p>",
    "Coagulante comercial: 38–42 % p/p. En proceso: 50–5.000 mg/L.", "ASTM G48; tabla A–D",
    ["picaduras", "agente_cloruros", "agente_hcl"], "Es una sal de hierro oxidante y clorurada (FeCl₃).",
    "Restringe la selección a titanio, C-276 o polímeros.",
    "Incluso decenas de mg/L pican los inoxidables comunes.",
    "304/316: 100 mg/L a 40 °C. C-276: 60.000 mg/L a 60 °C. Titanio: hasta 100 °C.",
    "En trazas muy bajas y frío, 316 aceptable (B).",
    "En dosificación de coagulante: titanio, C-276, PTFE o PVDF; nunca B-2 ni Monel.",
    ["Material del cuerpo y bonete", "Internos", "Mecanismos M02 y M07"],
    ["Para dosificación de FeCl₃ comercial prefiera válvulas revestidas de PTFE/PFA o titanio.",
     "No use Hastelloy B-2: los iones férricos lo destruyen."],
    "Dosificación de FeCl₃ al 40 % a 25 °C: 400.000 mg/L → C-276 B y titanio A; 316 D.")

# =====================================================================================
# ÁCIDOS INORGÁNICOS
# =====================================================================================
_ag("hcl", "HCl — Ácido clorhídrico",
    "<p>Ácido fuerte reductor, el más agresivo de los ácidos comunes para los metales: combina acidez y "
    "cloruros. Ningún inoxidable común lo resiste.</p>"
    "<p><b>Dónde aparece.</b> Decapado de acero, regeneración de resinas, acidificación de pozos, "
    "condensados de cabeza de destilación de crudo (por hidrólisis de sales), producción de PVC y cloruros, "
    "neutralización de efluentes.</p><p><b>Cómo se detecta.</b> pH, titulación ácido-base, densidad (tablas de "
    "concentración), cloruros.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono, martensíticos, bronce: D (C solo < 0,05 % en frío). "
    "304/316: D (C solo < 0,1 % a 30 °C). Superdúplex/6Mo: B hasta 1 % y 30 °C. C-276: A hasta 2 % y 60 °C, "
    "B hasta 5 % y 80 °C o 20 % y 40 °C. <b>Hastelloy B-2/B-3: A a cualquier concentración hasta 100 °C</b> "
    "(solo sin oxidantes). Titanio: B hasta 3 % y 30 °C. Cerámica y PTFE: A.</p>"
    "<p>Gas seco (HCl anhidro): acero al carbono A hasta 200 °C.</p>",
    "Decapado: 5–18 %. Comercial: 32–37 %. Condensado de crudo: pH 2–5 con cientos de mg/L de Cl⁻.",
    "Fichas de Haynes (B-3, C-276); tabla A–D; API 571", ["agente_cloruros", "agente_fecl3"],
    "Es el ácido clorhídrico (HCl), ácido fuerte reductor que ataca a casi todos los metales.",
    "Define el cuerpo (C-276, B-2 o revestido) y suele llevar a internos cerámicos o de aleación de níquel.",
    "Hasta 1 % ya descarta los inoxidables comunes; por encima de 5 % solo quedan B-2, PTFE y cerámica.",
    "C-276: 2 % a 60 °C (A); B-2: cualquier concentración hasta 100 °C (A). 316: D.",
    "Por debajo de 0,1 % y en frío el 316 es apenas regular (C).",
    "Concentrado y caliente: B-2 (sin oxidantes), válvulas revestidas de PTFE/PFA o cerámica.",
    ["Material del cuerpo y bonete", "Internos", "Vástago", "Alertas de compatibilidad química"],
    ["Confirme que no haya oxidantes (Fe³⁺, Cu²⁺, cloro, aire) antes de usar Hastelloy B-2.",
     "Considere válvulas con revestimiento de PFA.", "Informe la concentración en % p/p."],
    "HCl al 10 % a 40 °C: C-276 B, B-2 A; el programa elige CW2M o N7M para el cuerpo e internos cerámicos "
    "si hay cavitación.")

_ag("h2so4", "H₂SO₄ — Ácido sulfúrico",
    "<p>Ácido fuerte cuyo comportamiento cambia con la concentración: diluido (< 70 %) es reductor y muy "
    "corrosivo; concentrado (93–99 %) forma una película de sulfato de hierro que protege al acero al carbono "
    "a baja velocidad y temperatura.</p>"
    "<p><b>Dónde aparece.</b> Plantas de ácido y fertilizantes, alquilación en refinería, minería "
    "(lixiviación de cobre), tratamiento de agua (ajuste de pH), baterías, decapado.</p>"
    "<p><b>Cómo se detecta.</b> Titulación ácido-base, densidad, conductividad.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono: C solo entre 93 y 99 % hasta 30 °C (la velocidad en el "
    "trim destruye la película). 316: B hasta 1 % y 40 °C o entre 93 y 99 % hasta 40 °C. Superaustenítico / "
    "superdúplex: A hasta 10 % y 50 °C. <b>Aleación 20: A a cualquier concentración hasta 50 °C</b>, B hasta "
    "80 °C. C-276: A hasta 66 °C. Cerámica y PTFE: A. EPDM B solo hasta 50 % y 40 °C.</p>",
    "Ajuste de pH: 1–10 %. Comercial: 93–98 %. Lixiviación: 10–200 g/L.",
    "Nickel Institute 10057 (selección de aleaciones en ácido sulfúrico); ficha Haynes C-276; tabla A–D",
    ["agente_so3"], "Es el ácido sulfúrico (H₂SO₄), cuya agresividad depende mucho de la concentración.",
    "Define el material de cuerpo e internos: Aleación 20 / CN7M es la referencia; el acero al carbono solo "
    "en concentrado frío.",
    "La zona más agresiva es la intermedia (10–80 %) y caliente.",
    "Aleación 20: A hasta 50 °C a cualquier concentración. Acero al carbono: 93–99 % hasta 30 °C (C).",
    "Muy diluido (< 1 %) y frío, el 316 es aceptable (B).",
    "Concentraciones medias o temperatura alta: Aleación 20, C-276, PTFE o cerámica.",
    ["Material del cuerpo y bonete", "Internos", "Asientos blandos"],
    ["Informe la concentración exacta: el comportamiento no es lineal.",
     "Evite el acero al carbono en internos aun en ácido concentrado (velocidad).",
     "Pida al fabricante curvas de isocorrosión."],
    "H₂SO₄ al 96 % a 30 °C: WCB queda C (solo cuerpo, baja velocidad) y el programa elige CN7M (Aleación 20).")

_ag("hno3", "HNO₃ — Ácido nítrico",
    "<p>Ácido fuerte <b>oxidante</b>. Al contrario que el HCl, refuerza la película pasiva de los inoxidables "
    "de bajo carbono: el 304L es el material clásico.</p><p><b>Dónde aparece.</b> Fertilizantes (nitrato de "
    "amonio), explosivos, pasivado de inoxidables, decapado, química fina, reprocesamiento nuclear.</p>"
    "<p><b>Cómo se detecta.</b> Titulación, densidad, nitratos por cromatografía iónica.</p>" + _CONV_PCT +
    "<p><b>Daños.</b> Corrosión intergranular de inoxidables sensibilizados (por eso grados L), ataque "
    "general a acero al carbono, cobre, Monel y B-2.</p>"
    "<p><b>Reglas del programa.</b> Acero al carbono, Monel, B-2, níquel químico, carburos y bronce: D. 304/"
    "304L: A hasta 65 % y 60 °C, B hasta 100 °C. 316: A hasta 50 % y 60 °C. Titanio: A hasta 70 % y 100 °C. "
    "C-276: solo B hasta 20 % (C-22 y 625 son mejores). PTFE A; NBR D.</p>",
    "Comercial: 55–68 %. Fumante: > 86 %.", "Tabla A–D; ASTM A262 (sensibilización)",
    ["agente_nitratos"], "Es el ácido nítrico (HNO₃), ácido oxidante.",
    "Lleva la selección a inoxidables L (CF3, F304L), titanio o PTFE.",
    "Oxidante: favorece a los inoxidables y destruye a los aceros al carbono y aleaciones Ni-Mo.",
    "304L: 65 % a 60 °C (A). Titanio: 70 % a 100 °C (A). Acero al carbono: D siempre.",
    "Diluido y frío: casi todos los inoxidables sirven.",
    "Concentrado (> 65 %) o caliente: titanio o grados especiales; cuidado con el ácido fumante.",
    ["Material del cuerpo y bonete", "Internos", "Elastómeros"],
    ["Prefiera grados L (CF3, CF3M) para evitar corrosión intergranular.",
     "No use Hastelloy B-2 ni Monel.", "Use PTFE en asientos y empaquetaduras."],
    "HNO₃ al 30 % a 50 °C: CF3 (304L) A; el programa lo elige frente a CF8M.")

_ag("h3po4", "H₃PO₄ — Ácido fosfórico",
    "<p>Ácido de fuerza media, poco oxidante. Puro es moderado; el ácido «de proceso» (vía húmeda) arrastra "
    "fluoruros, cloruros y sólidos que lo vuelven mucho más agresivo.</p><p><b>Dónde aparece.</b> "
    "Fertilizantes, alimentos y bebidas, tratamiento de superficies, detergentes.</p>"
    "<p><b>Cómo se detecta.</b> Titulación, densidad; impurezas (F⁻, Cl⁻) por cromatografía iónica.</p>"
    + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono D. 304: B hasta 20 % y 60 °C. 316: A hasta 40 % y 60 °C, "
    "B hasta 85 % y 60 °C. Aleación 20 / 825: A hasta 85 % y 90 °C. C-276: A hasta 100 °C. Titanio: solo B "
    "hasta 10 %. Cerámica y PTFE: A.</p>",
    "Grado alimenticio: 75–85 %. Vía húmeda: 28–54 % P₂O₅ con 1–2 % de F.",
    "Nickel Institute 1318; tabla A–D", ["agente_fluoruros"], "Es el ácido fosfórico (H₃PO₄).",
    "Define cuerpo e internos: 316 si es puro y moderado; Aleación 20 o 825 en concentrado caliente.",
    "Las impurezas mandan: informe también fluoruros y cloruros.",
    "316: 40 % a 60 °C (A). Aleación 20: 85 % a 90 °C (A).",
    "Diluido y frío: 316 apto.", "Concentrado, caliente o con fluoruros: Aleación 20, 825, C-276 o PTFE.",
    ["Material del cuerpo y bonete", "Internos"],
    ["Cargue fluoruros y cloruros del ácido de proceso como agentes adicionales.",
     "Evite titanio si hay fluoruros."],
    "H₃PO₄ al 50 % a 70 °C: 316 C; el programa elige CN7M (Aleación 20).")

_ag("hf", "HF — Ácido fluorhídrico",
    "<p>Ácido muy peligroso (penetra la piel y ataca huesos). Disuelve vidrio, sílice, cerámicas y titanio. "
    "El HF <b>anhidro</b> (≥ 70 %) se maneja en acero al carbono; el acuoso diluido requiere Monel.</p>"
    "<p><b>Dónde aparece.</b> Alquilación HF en refinería, producción de fluorocarbonos, grabado de vidrio y "
    "semiconductores, decapado de inoxidables (con HNO₃).</p><p><b>Cómo se detecta.</b> Titulación, electrodo "
    "de fluoruro.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono: B solo entre 70 y 100 % hasta 65 °C. <b>Monel 400: A "
    "hasta 100 °C</b> a cualquier concentración. C-276: B hasta 50 % y 60 °C. Inoxidables: D (C muy diluido). "
    "Titanio, martensíticos, Stellite, carburos, cerámica, vidrio y NBR: D. PTFE: A.</p>",
    "Alquilación: 85–95 % HF. Grabado: 5–50 %.", "API RP 751; Nickel Institute 10074; tabla A–D",
    ["agente_fluoruros"], "Es el ácido fluorhídrico (HF), que ataca metales, vidrio y cerámica.",
    "Lleva a Monel (o acero al carbono si es anhidro) y descarta cerámicas, titanio y PTFE con vidrio.",
    "Diluido es más corrosivo para el acero que el anhidro.",
    "Acero al carbono: ≥ 70 % hasta 65 °C (B). Monel: hasta 100 °C (A).",
    "Diluido: Monel o C-276; nunca acero al carbono.",
    "Anhidro y frío: acero al carbono controlado (API RP 751) o Monel.",
    ["Material del cuerpo y bonete", "Internos", "Asientos (RPTFE con vidrio)"],
    ["Use Monel en internos y vástago.", "Evite aire en el sistema: acelera el ataque al Monel.",
     "Siga API RP 751 en alquilación."],
    "HF al 20 % a 40 °C: acero al carbono D, Monel A; el programa elige M35-1 para el cuerpo.")

_ag("h2co3", "H₂CO₃ — Ácido carbónico",
    "<p>Ácido débil que se forma al disolver CO₂ en agua. Es la forma en que el CO₂ corroe el acero.</p>"
    "<p><b>Dónde aparece.</b> Condensado de vapor (retorno), bebidas carbonatadas, agua de pozo, agua "
    "producida con CO₂.</p><p><b>Cómo se detecta.</b> pH (4–6), CO₂ libre por titulación, alcalinidad.</p>"
    + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono y Cr-Mo: C hasta 60 °C y D por encima (corrosión de "
    "retorno de condensado). Inoxidables, martensíticos y aleaciones: A. Bronce y carburo de cobalto: B.</p>",
    "Condensado: pH 5–6 con 5–50 mg/L de CO₂ (≈ 0,0005–0,005 %).", "API 571",
    ["agente_co2", "corrosion_co2"], "Es el ácido débil formado por CO₂ disuelto en agua.",
    "Penaliza el acero al carbono en retornos de condensado y aguas carbonatadas.",
    "Aunque es débil, corroe el acero al carbono de forma continua, sobre todo en caliente.",
    "Acero al carbono: C hasta 60 °C, D por encima.",
    "En agua neutra sin CO₂ no aplica.", "En condensado caliente: inoxidable 316 o 410 en internos.",
    ["Material del cuerpo y bonete", "Internos"],
    ["Si conoce la presión parcial del CO₂, cárguelo como CO₂.", "En condensado use 316 en internos."],
    "Retorno de condensado a 90 °C con ácido carbónico: acero al carbono D; el programa elige un cuerpo "
    "inoxidable o Cr-Mo según el resto de los datos.")

_ag("hclo4", "HClO₄ — Ácido perclórico",
    "<p>Ácido muy fuerte; concentrado y caliente es un oxidante explosivo en contacto con materia orgánica.</p>"
    "<p><b>Dónde aparece.</b> Laboratorios analíticos, propelentes (perclorato de amonio), electropulido.</p>"
    "<p><b>Cómo se detecta.</b> Titulación; perclorato por cromatografía iónica (EPA 314).</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Casi todos los metales D. 304/316: B hasta 10 % y 40 °C. Titanio: A hasta "
    "70 % y 60 °C. C-276: B hasta 70 % y 40 °C. PTFE y vidrio: A.</p>",
    "Reactivo: 60–72 %.", "Tabla A–D", [], "Es el ácido perclórico (HClO₄), ácido fuerte y oxidante.",
    "Restringe la selección a titanio o PTFE.", "Concentrado, además de corrosivo, es un riesgo de explosión.",
    "Titanio: 70 % a 60 °C (A).", "Diluido y frío, inoxidable 316 aceptable (B).",
    "Concentrado: titanio o revestimiento de PTFE; sin lubricantes orgánicos.",
    ["Material del cuerpo y bonete", "Internos"],
    ["Evite cualquier lubricante orgánico en la válvula.", "Consulte al fabricante."],
    "HClO₄ al 60 % a 25 °C: el programa solo acepta titanio o PTFE.")

# =====================================================================================
# ÁCIDOS ORGÁNICOS
# =====================================================================================
_ORG = ("<p>Los ácidos orgánicos son ácidos débiles, pero calientes y concentrados atacan al acero al carbono "
        "y a los inoxidables simples. El molibdeno (316) mejora mucho la resistencia.</p>")
_ag("acetico", "CH₃COOH — Ácido acético",
    "<p>Ácido orgánico (el del vinagre). Glacial (≈ 100 %) y caliente es muy agresivo.</p>" + _ORG +
    "<p><b>Dónde aparece.</b> Producción de PTA, acetato de vinilo, acetatos, alimentos, farmacéutica.</p>"
    "<p><b>Cómo se detecta.</b> Titulación con NaOH, cromatografía.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono: D (C glacial hasta 40 °C). 304: A hasta 60 °C. 316: A "
    "hasta 80 °C, B hasta 118 °C (ebullición). Dúplex y aleaciones de níquel: A. Titanio: A. FKM: B hasta 20 % "
    "y 40 °C, C por encima. EPDM: A hasta 60 °C.</p>",
    "Vinagre: 4–8 %. Glacial: 99,5 %.", "Tabla A–D", ["agente_formico"],
    "Es el ácido acético, ácido orgánico débil.", "Define si basta 304/316 o se necesita dúplex o aleación.",
    "Concentrado y caliente es el caso más agresivo.", "316: A hasta 80 °C; B hasta 118 °C.",
    "Diluido y frío: 304 apto.", "Glacial hirviendo: dúplex, aleaciones de níquel o titanio.",
    ["Material del cuerpo y bonete", "Internos", "Asientos blandos (FKM)"],
    ["Use EPDM o PTFE, no FKM, en ácido acético concentrado.", "Informe la temperatura máxima."],
    "Ácido acético al 80 % a 100 °C: 316 B, dúplex A; el programa compara costos y elige.")

_ag("formico", "HCOOH — Ácido fórmico",
    "<p>El ácido orgánico más fuerte de los comunes; reductor.</p>" + _ORG +
    "<p><b>Dónde aparece.</b> Curtiembres, textiles, conservación de forrajes, química fina, caucho.</p>"
    "<p><b>Cómo se detecta.</b> Titulación, cromatografía.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono D. 304: B hasta 10 % y 40 °C. 316: A hasta 40 °C, B hasta "
    "80 °C. Dúplex: A hasta 60 °C. Superaustenítico y aleaciones de níquel: A hasta 100 °C. Titanio: A hasta 50 % "
    "y 60 °C. FKM: C; NBR: D; EPDM: A.</p>",
    "Comercial: 85–99 %.", "Tabla A–D", ["agente_acetico"], "Es el ácido fórmico, el ácido orgánico más fuerte "
    "de uso común.", "Lleva a 316 en frío y a dúplex o aleaciones en caliente.",
    "Más agresivo que el acético a igual temperatura.", "316: A hasta 40 °C. Dúplex: A hasta 60 °C.",
    "Diluido y frío: 316 apto.", "Caliente y concentrado: aleaciones de níquel o superaustenítico.",
    ["Material del cuerpo y bonete", "Internos", "Elastómeros"],
    ["Evite NBR y FKM.", "Prefiera EPDM o PTFE."],
    "Ácido fórmico al 85 % a 70 °C: 316 B, superaustenítico A.")

_ag("oxalico", "C₂H₂O₄ — Ácido oxálico",
    "<p>Ácido orgánico reductor que forma complejos con el hierro; se usa para limpiar óxidos.</p>" + _ORG +
    "<p><b>Dónde aparece.</b> Limpieza química, blanqueo, extracción de tierras raras, textiles.</p>"
    "<p><b>Cómo se detecta.</b> Titulación con permanganato.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono y carburo de cobalto D. 304: B hasta 10 % y 40 °C. 316: B "
    "hasta 10 % y 60 °C. Dúplex: A hasta 60 °C. Aleaciones de níquel: A. Titanio: C solo hasta 1 % (no apto).</p>",
    "Soluciones de limpieza: 2–10 %.", "Tabla A–D", [], "Es el ácido oxálico, ácido orgánico reductor.",
    "Descarta acero al carbono y titanio.", "Ataca más al titanio que otros ácidos orgánicos.",
    "316: B hasta 10 % y 60 °C. Titanio: no apto.", "Diluido y frío: 316 aceptable.",
    "Caliente: dúplex o aleaciones de níquel.", ["Material del cuerpo y bonete", "Internos"],
    ["No use titanio.", "Informe la concentración en % p/p."],
    "Ácido oxálico al 5 % a 50 °C: 316 B; titanio D.")

_ag("citrico", "C₆H₈O₇ — Ácido cítrico",
    "<p>Ácido orgánico débil, poco agresivo para inoxidables.</p>" + _ORG +
    "<p><b>Dónde aparece.</b> Alimentos y bebidas, farmacia, limpieza química y pasivado.</p>"
    "<p><b>Cómo se detecta.</b> Titulación, pH.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono D. 304: A hasta 50 % y 60 °C. 316, dúplex, aleaciones y "
    "titanio: A hasta 100 °C. Martensíticos: B hasta 50 % y 40 °C. Polímeros: A.</p>",
    "Bebidas: 0,1–1 %. Pasivado: 4–10 %.", "Tabla A–D", [], "Es el ácido cítrico, ácido orgánico débil.",
    "Confirma inoxidable 304/316 en servicios alimenticios.", "Con inoxidable el riesgo es bajo.",
    "316: A hasta 100 °C.", "Diluido: inoxidable 304 apto.", "Caliente y concentrado: 316.",
    ["Material del cuerpo y bonete", "Internos"], ["En alimentos use 316L con acabado sanitario."],
    "Jugo con 1 % de ácido cítrico a 80 °C: 316 A; acero al carbono D.")

_ag("lactico", "C₃H₆O₃ — Ácido láctico",
    "<p>Ácido orgánico de fermentación; en caliente ataca al 304.</p>" + _ORG +
    "<p><b>Dónde aparece.</b> Lácteos, fermentación, bioplásticos (PLA), farmacéutica.</p>"
    "<p><b>Cómo se detecta.</b> Titulación, HPLC.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono D. 304: A hasta 50 % y 40 °C, B hasta 60 °C. 316: A hasta "
    "60 °C, B hasta 100 °C. Dúplex, aleaciones y titanio: A hasta 100 °C.</p>",
    "Fermentación: 5–15 %. Comercial: 80–90 %.", "Tabla A–D", [], "Es el ácido láctico, ácido orgánico.",
    "Elige entre 304 y 316 según la temperatura.", "Caliente ataca al 304.", "316: A hasta 60 °C.",
    "Frío: 304 apto.", "Caliente y concentrado: 316 o dúplex.", ["Material del cuerpo y bonete", "Internos"],
    ["Use 316L en lácteos."], "Ácido láctico al 80 % a 80 °C: 316 B, dúplex A.")

# =====================================================================================
# ÁLCALIS / BASES
# =====================================================================================
_ag("naoh", "NaOH — Hidróxido de sodio (soda cáustica)",
    "<p>Base fuerte. Ataca poco a los aceros en frío, pero en caliente y concentrada provoca "
    "<b>agrietamiento cáustico</b> (caustic SCC) del acero al carbono, sobre todo en soldaduras sin "
    "alivio de tensiones.</p><p><b>Dónde aparece.</b> Plantas cloro-álcali, refinería (lavado cáustico, "
    "Merox), pulpa kraft (licor blanco), alúmina (Bayer), regeneración de resinas, neutralización.</p>"
    "<p><b>Cómo se detecta.</b> Titulación ácida, conductividad, densidad.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono: A hasta 10 % y 80 °C; B hasta 50 % y 50 °C; C hasta 50 % "
    "y 90 °C (requiere alivio de tensiones, NACE SP0403). Inoxidables 304/316: A hasta 50 % y 95 °C. Monel: A "
    "hasta 75 % y 150 °C. <b>Inconel 600: A hasta 300 °C</b>. Titanio: B hasta 50 % y 80 °C. Cerámica: C sobre "
    "10 %. FKM: C/D; EPDM: A.</p>",
    "Lavado cáustico: 5–20 %. Comercial: 50 %. Fundida: > 70 %.", "NACE SP0403; API 571; tabla A–D",
    ["agente_koh"], "Es la soda cáustica (NaOH), base fuerte.",
    "Decide si el acero al carbono es apto o si se necesita inoxidable, Monel o Inconel 600.",
    "Concentración y temperatura juntas determinan el agrietamiento cáustico.",
    "Acero al carbono: 10 % a 80 °C (A); 50 % a 50 °C (B).",
    "Diluida y fría: acero al carbono apto.",
    "Caliente y concentrada: agrietamiento cáustico; Monel, Inconel 600 o 316 según la temperatura.",
    ["Material del cuerpo y bonete", "Internos", "Elastómeros (FKM)", "Mecanismo M08"],
    ["Use EPDM en asientos; evite FKM.", "Si se usa acero al carbono en caliente, exija alivio de tensiones.",
     "Evite cerámica de alúmina en soda concentrada caliente."],
    "NaOH al 50 % a 90 °C: acero al carbono C (con alivio de tensiones), 316 A; el programa elige CF8M.")

_ag("koh", "KOH — Hidróxido de potasio",
    "<p>Base fuerte con un comportamiento frente a los materiales muy parecido a la soda cáustica.</p>"
    "<p><b>Dónde aparece.</b> Electrolizadores alcalinos (hidrógeno verde, 25–30 %), fertilizantes potásicos, "
    "biodiésel, jabones.</p><p><b>Cómo se detecta.</b> Titulación, densidad.</p>" + _CONV_PCT +
    "<p><b>Regla del programa.</b> Se evalúa con las reglas del NaOH a la misma concentración (acero al carbono "
    "A hasta 10 % y 80 °C, inoxidables A hasta 50 % y 95 °C, níquel 600 A).</p>",
    "Electrólisis: 25–30 %. Comercial: 45–50 %.", "NACE SP0403", ["agente_naoh"],
    "Es el hidróxido de potasio (KOH), base fuerte.", "Se evalúa igual que la soda cáustica.",
    "En caliente agrieta el acero al carbono.", "Como NaOH.", "Diluido y frío: acero al carbono apto.",
    "Concentrado y caliente: inoxidable o níquel.", ["Material del cuerpo y bonete", "Internos"],
    ["En electrolizadores use 316L o níquel.", "Evite FKM."],
    "KOH al 30 % a 50 °C: 316 B por la tabla A–D (conservador) y A por las reglas; se adopta B.")

_ag("nh4oh", "NH₄OH — Hidróxido de amonio (amoníaco acuoso)",
    "<p>Solución de amoníaco en agua; base débil. Muy agresiva para el cobre y sus aleaciones.</p>"
    "<p><b>Dónde aparece.</b> Limpieza, desnitrificación, control de pH de calderas, aguas ácidas de "
    "refinería.</p><p><b>Cómo se detecta.</b> Titulación ácida, electrodo de amonio.</p>" + _CONV_PCT +
    "<p><b>Regla del programa.</b> Se evalúa con las reglas del amoníaco: aceros, inoxidables y aleaciones de "
    "níquel A; Monel B hasta 3 %; bronce D; FKM D.</p>",
    "Comercial: 25–30 %. Control de pH: mg/L.", "API 571", ["agente_nh3"],
    "Es el amoníaco disuelto en agua.", "Descarta bronce y FKM.", "Benigno para aceros, destructivo para cobre.",
    "Bronce: D a cualquier concentración.", "En trazas sigue atacando al cobre.",
    "Concentrado: evitar Monel y FKM.", ["Guía (bujes de bronce)", "Elastómeros"],
    ["No use aleaciones de cobre.", "Use EPDM o PTFE."],
    "Amoníaco acuoso al 25 %: el programa descarta el buje de bronce y elige una guía de acero endurecido.")

# =====================================================================================
# AZUFRE / SULFUROS
# =====================================================================================
_ag("azufre", "S₈ — Azufre elemental",
    "<p>Azufre en estado elemental (sólido amarillo, fundido entre 115 y 160 °C, o disuelto en "
    "hidrocarburos). Con agua y H₂S es extremadamente corrosivo: provoca picaduras severas y anula los "
    "límites de servicio agrio de los inoxidables.</p><p><b>Dónde aparece.</b> Gas muy agrio de alta "
    "presión (se deposita al bajar la presión en la válvula), plantas Claus, azufre fundido, crudos "
    "pesados.</p><p><b>Cómo se detecta.</b> Análisis de depósitos, solubilidad en CS₂, GC-SCD en gas, "
    "inspección visual de depósitos amarillos.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa (con agua).</b> Austeníticos, dúplex, superdúplex y martensíticos: D. Acero al "
    "carbono, Aleación 20, 825, Monel: C hasta 120 °C. <b>C-276: A hasta 200 °C</b>. Sin agua (azufre fundido "
    "seco): acero al carbono A hasta 300 °C; bronce D. Además, en servicio agrio los materiales que no admiten "
    "azufre elemental según ISO 15156 se descartan.</p>",
    "Gas con azufre elemental: trazas a cientos de mg/m³. Azufre fundido: 100 %.", "ISO 15156-3; API 571",
    ["agente_h2s", "nace_mr0175"], "Es azufre en estado elemental (S₈), sólido, fundido o disuelto.",
    "Endurece los requisitos de servicio agrio y suele llevar a aleaciones Ni-Cr-Mo (C-276).",
    "Con agua y H₂S descarta la mayoría de los inoxidables.", "Con agua: inoxidables D; C-276 A hasta 200 °C.",
    "Sin agua: acero al carbono apto (azufre fundido en camisa de vapor).",
    "Con agua y H₂S: C-276 o equivalentes.",
    ["Material del cuerpo y bonete", "Internos", "Vástago", "Norma de servicio agrio"],
    ["Pregunte si hay depósitos de azufre aguas abajo de válvulas reductoras.",
     "En azufre fundido use camisa de calefacción y acero al carbono."],
    "Gas agrio con azufre elemental y agua: el 316 y el dúplex se descartan; el programa elige CW2M.")

_ag("sulfuros", "HS⁻ / S²⁻ — Sulfuros",
    "<p>Iones sulfuro disueltos en agua; en medio ácido liberan H₂S. Indican potencial de servicio agrio.</p>"
    "<p><b>Dónde aparece.</b> Aguas ácidas de refinería, licor kraft, aguas residuales, aguas de formación, "
    "lixiviados de minería.</p><p><b>Cómo se detecta.</b> Titulación iodométrica, método azul de metileno "
    "(APHA 4500-S²⁻), electrodo de sulfuro.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa.</b> Acero al carbono B hasta 100 mg/L y 80 °C, C por encima; inoxidables y "
    "aleaciones A; bronce D. Además se estima un pH₂S equivalente conservador = mg/L ÷ 34 (como si todo "
    "estuviera como H₂S): si supera 0,3 kPa con agua, el servicio se trata como agrio.</p>",
    "Agua ácida: 100–10.000 mg/L. Licor kraft: 10–40 g/L.", "APHA 4500-S²⁻; ISO 15156-2",
    ["agente_h2s", "agente_polisulfuros"], "Son iones sulfuro disueltos (HS⁻, S²⁻), que liberan H₂S.",
    "Se usan para estimar si el servicio es agrio y para la compatibilidad de acero al carbono y cobre.",
    "Pocos mg/L ya pueden equivaler a pH₂S > 0,3 kPa.",
    "pH₂S equivalente = mg/L ÷ 34; agrio con ≥ 0,3 kPa (≈ 10 mg/L).",
    "Por debajo de ~10 mg/L no se dispara el servicio agrio.",
    "Por encima, se aplican ISO 15156 / 17945 y se descartan materiales duros y cobre.",
    ["Norma de servicio agrio", "Material del cuerpo y bonete", "Internos"],
    ["Informe el pH: a pH > 8 casi todo el sulfuro está como HS⁻ y el valor es conservador.",
     "No use bronce ni latón."],
    "Agua con 340 mg/L de sulfuros: pH₂S equivalente = 10 kPa → servicio agrio.")

_ag("polisulfuros", "Sₓ²⁻ — Polisulfuros",
    "<p>Cadenas de azufre (polisulfuro de amonio o sodio) que se forman con sulfuros y oxígeno o azufre. Se "
    "inyectan como inhibidor de cianuros en unidades FCC.</p><p><b>Dónde aparece.</b> Aguas de lavado de FCC, "
    "licor verde de pulpa, aguas ácidas.</p><p><b>Cómo se detecta.</b> Análisis de azufre total y sulfuros, "
    "color amarillo-naranja.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa.</b> Acero al carbono C; inoxidables y aleaciones A; aleaciones de níquel B; "
    "bronce D.</p>", "Aguas de lavado: 100–2.000 mg/L.", "API 571", ["agente_sulfuros"],
    "Son cadenas de azufre disueltas (polisulfuros).", "Penaliza acero al carbono y descarta cobre.",
    "Corrosivos para acero al carbono incluso diluidos.", "Acero al carbono: C. Inoxidables: A.",
    "En trazas: efecto menor.", "En dosis altas: inoxidable 316 en internos.",
    ["Material del cuerpo y bonete", "Internos"], ["No use aleaciones de cobre."],
    "Agua de lavado con 500 mg/L de polisulfuros: acero al carbono C, 316 A.")

_ag("tiosulfatos", "S₂O₃²⁻ — Tiosulfatos",
    "<p>Iones de azufre de oxidación intermedia; en presencia de cloruros provocan picaduras en inoxidables "
    "de baja aleación aun en concentraciones bajas.</p><p><b>Dónde aparece.</b> Blanqueo de pulpa, minería "
    "del oro (lixiviación con tiosulfato), fotografía, decloración de agua.</p>"
    "<p><b>Cómo se detecta.</b> Titulación iodométrica, cromatografía iónica.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa.</b> Acero al carbono C. 304: B hasta 100 mg/L y 60 °C, C por encima. 316: A "
    "hasta 1.000 mg/L y 80 °C. Dúplex, superaustenítico, aleaciones y titanio: A. Bronce D.</p>",
    "Blanqueo: 10–1.000 mg/L. Lixiviación: 0,1–0,5 mol/L.", "API 571; tabla A–D", [],
    "Son iones tiosulfato (S₂O₃²⁻).", "Elige entre 304 y 316 o superior.", "Combinados con cloruros pican al 304.",
    "304: B hasta 100 mg/L. 316: A hasta 1.000 mg/L y 80 °C.", "En trazas: 304 aceptable.",
    "Concentrado: 316 o dúplex.", ["Material del cuerpo y bonete", "Internos"],
    ["Prefiera 316 o superior.", "Informe también los cloruros."],
    "Agua con 2.000 mg/L de tiosulfato a 50 °C: 304 C, 316 B.")

# =====================================================================================
# OXIDANTES
# =====================================================================================
_ag("hipoclorito", "OCl⁻ — Hipoclorito (cloro activo)",
    "<p>Oxidante fuerte (lavandina, hipoclorito de sodio o calcio). Pica a los inoxidables incluso en mg/L "
    "porque eleva el potencial y aporta cloruros.</p><p><b>Dónde aparece.</b> Desinfección de agua potable y "
    "de mar (cloración de tomas), blanqueo, limpieza CIP.</p><p><b>Cómo se detecta.</b> Cloro libre por DPD "
    "(APHA 4500-Cl G), titulación iodométrica, potencial ORP.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa (mg/L de cloro activo).</b> Acero al carbono C hasta 10 mg/L. 304: B hasta "
    "5 mg/L. 316: B hasta 10 mg/L y 40 °C. Dúplex: A hasta 10 mg/L y 40 °C. Superdúplex/6Mo: A hasta 20 mg/L y "
    "40 °C, B hasta 1.000 mg/L y 30 °C. C-276: A hasta 40 °C. <b>Titanio: A hasta 80 °C</b>. PTFE y FKM: A; NBR: C "
    "solo hasta 50 mg/L.</p>",
    "Agua potable: 0,2–2 mg/L. Cloración de agua de mar: 0,5–2 mg/L. Lavandina: 50.000–150.000 mg/L.",
    "APHA 4500-Cl; tabla A–D", ["agente_cl2", "picaduras"], "Es el hipoclorito (cloro activo), oxidante clorado.",
    "Limita los inoxidables y lleva a titanio o superdúplex en dosificación.",
    "Pocos mg/L ya pican los inoxidables comunes.", "316: 10 mg/L a 40 °C (B). Titanio: A hasta 80 °C.",
    "En agua potable clorada normal (< 2 mg/L) el 316 es apto.",
    "En dosificación de hipoclorito concentrado: titanio, PVC/PVDF o revestimiento de PTFE.",
    ["Material del cuerpo y bonete", "Internos", "Elastómeros"],
    ["En dosificación de hipoclorito use titanio o válvulas termoplásticas.", "Evite NBR."],
    "Agua de mar clorada con 2 mg/L a 25 °C: superdúplex A; 316 B (pero los cloruros lo dejan en C).")

_ag("h2o2", "H₂O₂ — Peróxido de hidrógeno",
    "<p>Oxidante fuerte que se descompone en agua y oxígeno; metales como cobre, hierro y cobalto catalizan "
    "esa descomposición (riesgo de sobrepresión).</p><p><b>Dónde aparece.</b> Blanqueo de pulpa y textiles, "
    "tratamiento de efluentes, semiconductores, esterilización aséptica.</p>"
    "<p><b>Cómo se detecta.</b> Titulación con permanganato, tiras reactivas.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono, bronce y carburos D. 304: A hasta 50 % y 40 °C. 316 y "
    "dúplex: A hasta 60 °C. Titanio: B hasta 30 % y 40 °C. Stellite: C (el cobalto cataliza). PTFE y FKM: A; "
    "NBR: D.</p>", "Blanqueo: 3–10 %. Comercial: 35–70 %.", "Tabla A–D", [],
    "Es el peróxido de hidrógeno (H₂O₂), oxidante.", "Lleva a 316L pasivado y descarta cobre y cobalto.",
    "Los metales catalíticos lo descomponen y pueden generar sobrepresión.", "316: A hasta 60 °C.",
    "Diluido: 304/316 aptos.", "Concentrado: 316L pasivado, PTFE; evite Stellite.",
    ["Material del cuerpo y bonete", "Internos (Stellite)", "Elastómeros"],
    ["Use 316L pasivado y electropulido.", "Evite cobre y cobalto (Stellite, WC-Co)."],
    "H₂O₂ al 35 % a 30 °C: 316 A, Stellite C; el programa evita el recargue de Stellite.")

_ag("nitratos", "NO₃⁻ — Nitratos",
    "<p>Sales oxidantes (sodio, amonio, calcio). Calientes y concentradas provocan corrosión bajo tensión del "
    "acero al carbono.</p><p><b>Dónde aparece.</b> Fertilizantes (nitrato de amonio), sales fundidas solares, "
    "explosivos, aguas subterráneas agrícolas.</p><p><b>Cómo se detecta.</b> Cromatografía iónica (ASTM D4327), "
    "electrodo de nitrato.</p>" + _CONV_MGL +
    "<p><b>Reglas del programa.</b> Acero al carbono: B hasta 10.000 mg/L y 60 °C, C hasta 80 °C, D por encima; "
    "por encima de 60 °C se agrega el mecanismo de SCC por nitratos. Inoxidables y aleaciones: A. Bronce: B "
    "hasta 10.000 mg/L. FKM y NBR: C.</p>", "Agua subterránea: 10–100 mg/L. Soluciones de fertilizante: 20–80 %.",
    "API 571", ["agente_hno3"], "Son sales de nitrato (NO₃⁻), oxidantes.",
    "Penaliza el acero al carbono en caliente.", "Calientes y concentrados agrietan el acero al carbono.",
    "Acero al carbono: B hasta 10.000 mg/L y 60 °C.", "Diluidos y fríos: acero al carbono apto.",
    "Concentrados y calientes: inoxidable 304L/316L.", ["Material del cuerpo y bonete", "Mecanismo M26"],
    ["Use inoxidable en soluciones calientes de nitrato de amonio."],
    "Solución de nitrato de amonio al 50 % a 90 °C: acero al carbono D, 304L A.")

# =====================================================================================
# OTROS
# =====================================================================================
_ag("aminas", "R-NH₂ — Aminas (MEA, DEA, MDEA)",
    "<p>Bases orgánicas usadas para absorber H₂S y CO₂ del gas. La amina pobre caliente agrieta el acero al "
    "carbono no aliviado de tensiones (SCC por aminas); la amina rica con gases ácidos es corrosiva.</p>"
    "<p><b>Dónde aparece.</b> Endulzamiento de gas natural y de refinería, captura de CO₂.</p>"
    "<p><b>Cómo se detecta.</b> Titulación ácida (fuerza de amina), carga de gas ácido, sales térmicamente "
    "estables.</p>" + _CONV_PCT +
    "<p><b>Reglas del programa.</b> Acero al carbono: A hasta 60 °C, B hasta 150 °C (alivio de tensiones "
    "obligatorio, API RP 945); inoxidables y aleaciones: A; bronce D; FKM D; NBR B; EPDM A.</p>",
    "MEA: 15–20 %. DEA: 25–35 %. MDEA: 35–50 %.", "API RP 945; API 571", ["agente_h2s", "agente_co2"],
    "Son aminas orgánicas para tratamiento de gas.", "Penaliza el acero al carbono caliente y descarta cobre y FKM.",
    "En caliente agrietan el acero al carbono sin alivio de tensiones.",
    "Acero al carbono: A hasta 60 °C; por encima, B con PWHT.", "Frío: acero al carbono apto.",
    "Caliente: PWHT obligatorio o inoxidable 316 en internos.",
    ["Material del cuerpo y bonete", "Elastómeros", "Mecanismo M25"],
    ["Exija PWHT en soldaduras de acero al carbono.", "Use 316 en internos de amina rica.",
     "Evite FKM y bronce."],
    "MDEA al 45 % a 110 °C: acero al carbono B con alivio de tensiones; el programa agrega el mecanismo de SCC "
    "por aminas.")

_ag("solidos", "Sólidos abrasivos",
    "<p>Partículas en suspensión (arena, catalizador, cenizas, cristales, óxidos) que erosionan las superficies "
    "por impacto. En la válvula el daño se concentra donde la velocidad es mayor: asiento, obturador y "
    "jaula.</p><p><b>Dónde aparece.</b> Producción con arena, slurries de minería, catalizador de FCC, "
    "cenizas, pulpa, agua cruda de río, cristalizadores.</p><p><b>Cómo se detecta.</b> Sólidos suspendidos "
    "totales (APHA 2540 D), detectores acústicos de arena, inspección de filtros, granulometría.</p>"
    + _CONV_MGL +
    "<p><b>Reglas del programa.</b> No afecta la compatibilidad química; actúa por el desplegable «Sólidos»: "
    "trazas → obturador y asiento ≥ 35 HRC; presentes → superficies ≥ 45 HRC y resistencia a la erosión ≥ 8/10 "
    "(Stellite, 440C, carburo de tungsteno, cerámica); slurry → ≥ 55 HRC y erosión 10/10. El cuerpo con "
    "resistencia a la erosión baja (acero al carbono) se penaliza.</p>",
    "Agua cruda: 10–500 mg/L. Producción con arena: 1–100 kg/día. Slurry: 5–60 % en peso.",
    "API RP 14E; DNV RP O501", ["erosion"], "Son partículas sólidas arrastradas por el fluido.",
    "Elevan la dureza mínima y la resistencia a la erosión exigidas a los internos.",
    "A más sólidos, mayor dureza; en slurries se requieren carburos o cerámica.",
    "Trazas: ≥ 35 HRC. Presentes: ≥ 45 HRC. Slurry: ≥ 55 HRC.",
    "Sin sólidos no se exige dureza por erosión.",
    "Con sólidos presentes el 316 se descarta en internos y el acero al carbono se penaliza en el cuerpo.",
    ["Dureza mínima de internos", "Internos (obturador, asiento, jaula)", "Material del cuerpo"],
    ["Use el desplegable «Sólidos» además de este agente.", "Limite la velocidad en la línea (≤ 3 m/s).",
     "Prefiera trims angulares y flujo que tiende a cerrar."],
    "Agua con arena («Sólidos: Presentes»): el programa exige ≥ 45 HRC y erosión ≥ 8/10 → obturador de 440C o "
    "Stellite.")

_ag("otro", "Otro agente (especificar)",
    "<p>Permite registrar una especie química que no está en la base del programa (por ejemplo cianuros, "
    "mercurio, fenoles, solventes clorados, cetonas). Se documenta en el informe, pero <b>su efecto no se "
    "evalúa</b>.</p><p><b>Cómo proceder.</b> Escriba el nombre exacto, la concentración y la fase; consulte "
    "curvas de corrosión del fabricante o una tabla de resistencia química; si el agente es crítico, use "
    "modo MANUAL con la justificación del especialista.</p>",
    "—", "Tablas de resistencia química de fabricantes; NACE Corrosion Data Survey", [],
    "Es un agente no catalogado que el usuario registra a mano.",
    "Queda en el informe y genera una alerta: el programa no evalúa su efecto.",
    "Su presencia indica que la selección automática puede estar incompleta.",
    "No hay umbrales en el programa.", "No aplica.", "No aplica.",
    ["Alertas de datos", "Informe técnico"],
    ["Consulte al especialista de corrosión.", "Si el agente es determinante, use modo MANUAL y documente."],
    "Se registra «Mercurio, 0,01 mg/L»: el programa agrega la alerta «Agente no catalogado» y recomienda "
    "verificar con el fabricante (el mercurio fragiliza aleaciones de aluminio y de cobre).")
