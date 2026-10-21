"""Ayuda de las solapas 4-Actuador, 5-Posicionador y 6-Accesorios: datos, resultados y alertas.

ENTRADAS y GUIA con la misma forma que ayuda_mat_parametros. Los textos describen el comportamiento real
de actuadores.py.
"""

ENTRADAS: dict[str, dict] = {}
GUIA: dict[str, dict] = {}

ACT, POS, ACC, FEN = "Actuador", "Posicionador", "Accesorios", "Fenómenos"
REF_F = "Método de fuerzas A + B + C + D (práctica de la industria de válvulas de control); ANSI/FCI 70-2"
REF_T = "Método de pares TB = A·ΔP + B, TD = C·ΔPef (práctica de la industria de válvulas de control)"


def _e(clave, titulo, texto, categoria, formula="", tipicos="", referencia="", relacionadas=(), guia=None):
    ENTRADAS[clave] = dict(titulo=titulo, texto=texto, formula=formula, tipicos=tipicos, referencia=referencia,
                           relacionadas=list(relacionadas), categoria=categoria)
    GUIA[clave] = guia


def _g(que_es, que_hace, que_indica, umbrales, por_debajo, por_encima, afecta, recomendaciones, ejemplo):
    return dict(que_es=que_es, que_hace=que_hace, que_indica=que_indica, umbrales=umbrales,
                por_debajo=por_debajo, por_encima=por_encima, afecta=list(afecta),
                recomendaciones=list(recomendaciones), ejemplo=ejemplo)


def _alerta(clave, titulo, texto, que_indica, umbral, recomendaciones, ejemplo, relacionadas=(), referencia=REF_F):
    """Entrada de ayuda de una alerta, con su guía."""
    _e(clave, titulo, texto, FEN, referencia=referencia, relacionadas=relacionadas,
       guia=_g(f"Es una alerta del dimensionamiento del actuador: {titulo.lower()}.",
               "Avisa una condición del actuador, del posicionador o de los accesorios que conviene resolver antes de "
               "emitir la hoja de datos.",
               que_indica, umbral, "No aplica.", "No aplica.",
               ["Selección del actuador", "Hoja de datos", "Informe técnico"], recomendaciones, ejemplo))


# =====================================================================================
# 4-ACTUADOR: DATOS
# =====================================================================================
_e("act_tipo", "Tipo de actuador",
   "<p>Elige la tecnología del actuador. El programa aplica el método que corresponde a la válvula (fuerzas en "
   "globo y ángulo, pares en rotativas) y busca el menor tamaño de una serie genérica que cumple:</p><ul>"
   "<li><b>Diafragma y resorte</b>: simple efecto; el resorte da la posición de falla. Carcasa de baja presión "
   "(unos 2,8 a 3,4 bar). Es el más usado en control por su simpleza y respuesta.</li>"
   "<li><b>Multiresorte y diafragma</b>: varios resortes cortos alrededor del vástago; más compacto y admite "
   "alimentación de hasta unos 6 bar.</li>"
   "<li><b>Pistón doble acción con resorte</b>: aire a ambos lados del pistón para modular con mucha rigidez y "
   "un resorte que lleva a la falla. El resorte se elige con un ajuste de banco de al menos 5 psi.</li>"
   "<li><b>Pistón doble acción sin resorte</b>: el de mayor empuje para su tamaño; sin aire queda donde está, "
   "por lo que la falla abre o cierra requiere tanque de reserva y válvula de cambio.</li>"
   "<li><b>Pistón retorno por resorte</b>: aire de un lado y resorte del otro, con alimentación de hasta unos "
   "10 bar.</li>"
   "<li><b>Eléctrico</b>: motor y reductor; queda en la última posición salvo que lleve módulo de falla "
   "segura.</li>"
   "<li><b>Electrohidráulico</b>: bomba y cilindro hidráulico propios; mucho empuje o par y falla por resorte.</li>"
   "<li><b>Piñón y cremallera</b> y <b>yugo escocés</b>: cuarto de vuelta, solo para rotativas. El primero da "
   "par constante; el segundo da par máximo en los extremos (arranque y asiento) y mínimo en la mitad.</li>"
   "<li><b>Manual</b>: volante o reductor.</li></ul>"
   "<p>La lista se ajusta a la válvula de 1-Sistema: con globo o ángulo quedan bloqueados piñón y cremallera y yugo "
   "escocés; con mariposa, bola o tapón excéntrico quedan bloqueados el diafragma y los pistones. Eléctrico, "
   "electrohidráulico y manual sirven para las dos. Las opciones bloqueadas se ven con el motivo al pasar el "
   "mouse.</p>",
   ACT, referencia=REF_F, relacionadas=["act_falla", "act_metodo", "act_tamano"],
   guia=_g("Es la tecnología que mueve el vástago o el eje de la válvula.",
           "Define la serie de tamaños, la presión máxima admisible y cómo se obtiene la posición de falla.",
           "Un tipo mal elegido se ve en el resultado: tamaños enormes, aire insuficiente o una falla imposible.",
           "Diafragma: hasta unos 3,4 bar en carcasa. Multiresorte: hasta unos 6 bar. Pistón: hasta unos 10 bar. "
           "Piñón y cremallera y yugo escocés: solo rotativas. Diafragma y pistones: solo vástago deslizante.",
           "No aplica.", "No aplica.",
           ["Fuerza o par disponible", "Ajuste de banco y resorte", "Señales del posicionador", "Accesorios"],
           ["Use diafragma y resorte en control con ΔP moderada: es simple y a prueba de fallas.",
            "Pase a pistón o multiresorte cuando el diafragma resulta muy grande.",
            "En rotativas grandes de cierre por par prefiera yugo escocés: su par es máximo en el asiento."],
           "Globo de 3\" con ΔP de cierre de 75 bar sin balancear: el diafragma resulta de 450 in²; un pistón de "
           "retorno por resorte con 6 bar lo resuelve con un cilindro de 8\"."))

_e("act_falla", "Modo de falla",
   "<p>Posición que debe tomar la válvula al perder el aire o la señal:</p><ul>"
   "<li><b>Cierra (FC)</b>: el resorte cierra; el aire abre (actuador de acción inversa en válvulas que cierran "
   "empujando el vástago hacia abajo). El resorte debe dar por sí solo la fuerza de cierre completa.</li>"
   "<li><b>Abre (FO)</b>: el resorte abre; el aire cierra (acción directa). El aire disponible, menos la fuerza "
   "del resorte comprimido, debe dar la fuerza de cierre.</li>"
   "<li><b>Última posición (FL)</b>: la válvula queda donde está. En actuadores de resorte requiere una válvula de "
   "bloqueo neumático; en eléctricos y pistones sin resorte es natural.</li></ul>"
   "<p>La falla la define el análisis de riesgos del proceso (HAZOP): qué posición lleva la planta a un estado "
   "seguro.</p>",
   ACT, referencia="IEC 61511 (posición segura); práctica de la industria", relacionadas=["act_tipo", "acc_solenoide"],
   guia=_g("Es la posición segura de la válvula ante la pérdida de energía.",
           "Decide qué fuerza hace el resorte y qué fuerza hace el aire, y con eso el ajuste de banco y la presión "
           "requerida.",
           "Con falla cierra, el resorte debe asentar la válvula; con falla abre, el aire debe hacerlo.",
           "No tiene umbral numérico.", "No aplica.", "No aplica.",
           ["Ajuste de banco", "Presión requerida", "Acción del posicionador", "Solenoide"],
           ["Tome la falla del HAZOP o de la filosofía de control.",
            "Con falla cierra y alta ΔP el resorte resulta grande: evalúe balancear el obturador."],
           "Válvula de alimentación de combustible a un horno: falla cierra. Válvula de alivio a antorcha: falla abre."))

_e("act_volante", "Volante",
   "<p>Mando manual montado en el actuador para mover la válvula sin aire o sin energía (puesta en marcha, "
   "emergencias). El programa calcula el empuje o par que debe vencer el volante: el resorte comprimido más la "
   "fuerza del proceso, y sugiere un diámetro de volante para no superar unos 360 N en el aro. Si no alcanza, "
   "indica un reductor.</p>",
   ACT, referencia="EN 12570 (fuerza en el aro de volantes)", relacionadas=["act_tipo"],
   guia=_g("Es un mando manual del actuador.", "Agrega el cálculo de empuje y diámetro del volante.",
           "Un empuje de volante alto indica que hará falta un reductor.",
           "Fuerza en el aro habitual ≤ 360 N.", "No aplica.", "Por encima de 360 N se agrega reductor.",
           ["Empuje requerido del volante", "Volante sugerido"],
           ["Pida volante en válvulas sin bypass que deban operarse en emergencia.",
            "En actuadores de resorte el volante debe vencer el resorte completo."],
           "Actuador con resorte de 23 kN: el volante lateral necesita un reductor; uno directo de 600 mm no alcanza."))

_e("act_aire", "Aire de instrumentos disponible",
   "<p>Presiones mínima y máxima garantizadas del aire de instrumentos en el punto de instalación, en la unidad "
   "elegida (manométrica o absoluta; el programa trabaja con presión manométrica).</p><ul>"
   "<li>La <b>mínima</b> dimensiona: el actuador debe cumplir con la peor presión disponible.</li>"
   "<li>La <b>máxima</b> verifica la carcasa del actuador y la carga del vástago. Si supera el límite del "
   "actuador, el set de aire debe regularla.</li></ul>"
   "<p>Al abrir el programa se proponen 4 y 7 bar g, valores típicos de planta: reemplácelos por los del "
   "proyecto. Los actuadores eléctricos, electrohidráulicos y manuales no los usan.</p>",
   ACT, tipicos="Aire de planta habitual: 4 a 7 bar g (60 a 100 psig).", referencia="ISA-7.0.01 (calidad del aire)",
   relacionadas=["act_P_req", "pos_set", "act_presion_carcasa"],
   guia=_g("Es la presión del aire con que se alimenta el actuador.",
           "La mínima fija el tamaño del actuador; la máxima verifica carcasa y vástago.",
           "Si la presión requerida por el actuador supera la mínima, el actuador no cumple.",
           "Típico 4 a 7 bar g. Carcasa de diafragma: unos 3,4 bar.",
           "Con aire bajo el actuador resulta más grande.", "Con aire alto hace falta regulador.",
           ["Tamaño del actuador", "Ajuste de banco", "Señales del posicionador", "Set de aire"],
           ["Use la mínima garantizada por la red, no la nominal del compresor.",
            "Considere la caída en la tubería de aire y en el filtro-regulador."],
           "Red de 4 a 7 bar g y diafragma de 3,4 bar máx.: se dimensiona con 3,4 bar y el set de aire regula."))

_e("act_flujo", "Flow (sentido del flujo)",
   "<p>Sentido del flujo. Las opciones se habilitan según la válvula elegida en 1-Sistema; las demás se ven pero "
   "quedan bloqueadas:</p><ul>"
   "<li><b>Up</b> (globo y ángulo): el fluido entra por debajo del asiento y empuja el obturador hacia arriba: la "
   "presión tiende a abrir. Es lo habitual.</li>"
   "<li><b>Down</b> (globo y ángulo): el fluido entra por arriba: la presión tiende a cerrar. Se usa en flashing y "
   "algunos trims anticavitación.</li>"
   "<li><b>Unidireccional</b> (rotativas): la válvula cierra con presión en el sentido marcado en el cuerpo.</li>"
   "<li><b>Bidireccional</b> (solo bola flotante o trunnion): cierra con presión desde cualquiera de los dos lados; "
   "el par de arranque se toma con la ΔP de cierre máxima en el sentido más desfavorable.</li></ul>"
   "<p>En vástago deslizante cambia el término A de la fuerza. Al elegir el trim en la solapa 2 el programa propone "
   "Up o Down según corresponda; si se cambia, se avisa la diferencia.</p>",
   ACT, referencia=REF_F, relacionadas=["act_metodo", "act_obturador", "act_gradiente"],
   guia=_g("Es la dirección del flujo a través del asiento.", "Cambia el signo y el valor del desbalance estático A.",
           "Con flujo hacia abajo la presión ayuda a cerrar pero puede generar inestabilidad (gradiente negativo).",
           "No tiene umbral.", "No aplica.", "No aplica.",
           ["Fuerza de cierre", "Fuerza de apertura", "Gradiente negativo"],
           ["Use el mismo sentido que el trim de la solapa 2."],
           "Puerto de 2,625\" y ΔP de 75 bar con flujo Up: A ≈ 1088 psi × 5,41 in² ≈ 5900 lbf (26 kN)."))

_e("act_vastago", "Diámetro del vástago",
   "<p>Diámetro del vástago de la válvula. En blanco se estima por el diámetro nominal (3/8\" hasta 1\", 1/2\" hasta "
   "2\", 3/4\" hasta 4\", 1\" hasta 6\", 1 1/4\" hasta 10\" y 2\" más arriba; una medida más desde CL900).</p>"
   "<p>Interviene en tres lugares: el área sobre la que la presión empuja el vástago hacia afuera (término A), la "
   "fricción de la empaquetadura (C) y la carga máxima admisible del vástago (pandeo). La carga admisible es la de "
   "un vástago de inoxidable 316 endurecido con relación largo/diámetro de hasta 12,5, reducida por "
   "temperatura.</p>",
   ACT, tipicos="3/8, 1/2, 3/4, 1, 1 1/4 y 2 in.", referencia=REF_F, relacionadas=["act_friccion", "act_metodo"],
   guia=_g("Es el diámetro de la pieza que une el obturador con el actuador.",
           "Fija el área del vástago, la fricción y la carga admisible.",
           "Si la carga del vástago supera la admisible, hay riesgo de pandeo o de doblarlo.",
           "Carga admisible a 38 °C: 1/2\" ≈ 22 kN, 3/4\" ≈ 50 kN, 1\" ≈ 72 kN; baja un 40 % a 427 °C.",
           "Un vástago fino reduce fricción pero admite menos carga.", "Uno grueso aumenta la fricción.",
           ["Fuerza A", "Fricción C", "Carga del vástago"],
           ["Cargue el diámetro certificado cuando tenga la hoja del fabricante."],
           "Globo de 3\" CL600: vástago estimado 3/4\" (19 mm)."))

# =====================================================================================
# 4-ACTUADOR: RESULTADOS
# =====================================================================================
_e("act_metodo", "Método de cálculo del actuador",
   "<p><b>Válvulas de vástago deslizante</b> (globo y ángulo): <i>F = A + B + C + D</i>.</p><ul>"
   "<li><b>A, desbalance estático</b>: la presión sobre el área desbalanceada del obturador más la presión que "
   "empuja el vástago hacia afuera. Desbalanceado con flujo Up: A = ΔP·A<sub>puerto</sub> + P2·A<sub>vástago</sub>; "
   "con flujo Down: A = −(ΔP·A<sub>puerto</sub> − P1·A<sub>vástago</sub>). Balanceado: la presión actúa solo sobre "
   "la corona entre el diámetro del sello y la línea de asiento (≈ 0,037·π·d in²). Con fuelle, el área efectiva "
   "del fuelle reemplaza a la del vástago.</li>"
   "<li><b>B, carga de asiento</b>: fuerza por pulgada de perímetro del puerto que garantiza la clase de cierre "
   "(ANSI/FCI 70-2): 20 lbf/in clase II, 40 clase III, 40 u 80 clase IV, (100 + 0,122·ΔP) clase V metálica, "
   "300 clase VI metal blando, A·ΔP + B con asiento de PTFE.</li>"
   "<li><b>C, fricción de empaquetadura</b>: según tipo (PTFE, grafito, con carga viva), diámetro del vástago y "
   "clase de presión.</li>"
   "<li><b>D, fuerzas adicionales</b>: rigidez del fuelle, sellos especiales; cero si no se declaran.</li></ul>"
   "<p>La fuerza de apertura no lleva carga de asiento. Se aplica un margen de diseño de 1,10.</p>"
   "<p><b>Válvulas rotativas</b>: par de arranque TB = A·ΔP<sub>cierre</sub> + B y par dinámico TD = C(θ)·ΔPef, "
   "con factores típicos del estilo y del diámetro, interpolados. ΔPef es la menor entre la ΔP del caso y la ΔP de "
   "flujo bloqueado. Se dimensiona con el mayor por 1,25.</p>",
   ACT, formula="F = A + B + C + D;  TB = A·ΔP + B;  TD = C(θ)·ΔPef", referencia=REF_F + "; " + REF_T,
   relacionadas=["act_obturador", "act_friccion", "clase_cierre", "act_requerido"],
   guia=_g("Es el procedimiento con que se calcula la fuerza o el par que la válvula pide al actuador.",
           "Suma cada efecto físico por separado para que se vea de dónde viene la fuerza.",
           "Si A domina, conviene balancear; si B domina, revise la clase de cierre; si C domina, la empaquetadura.",
           "Margen de diseño: 1,10 en vástago deslizante y 1,25 en rotativas.",
           "No aplica.", "No aplica.",
           ["Tamaño del actuador", "Resorte y ajuste de banco", "Presión requerida", "Señales del posicionador"],
           ["Cargue el caso Tight Shutoff con la presión real de cierre: es la base de A y B.",
            "Cargue puerto y carrera certificados cuando los tenga."],
           "Globo de 2\" balanceado, flujo Down, clase II, PTFE simple, vástago 1/2\", ΔP 200 psi: A = 54 lbf, "
           "B = 20 × 7,26 = 145 lbf, C = 50 lbf; F = 249 lbf (1,11 kN)."))

_e("act_obturador", "Obturador balanceado o desbalanceado",
   "<p>Se toma de la solapa 2. En «Automático» el programa supone balanceado si el trim es de jaula, la válvula "
   "tiene 3\" o más y la ΔP de cierre supera 10 bar. El balanceo reduce mucho el término A pero el sello de "
   "balanceo agrega carga de asiento (150 a 210 lbf/in según clase) y limita temperatura.</p>",
   ACT, referencia=REF_F, relacionadas=["balance", "act_metodo"],
   guia=_g("Es si el obturador tiene o no orificios y sello que igualan la presión arriba y abajo.",
           "Cambia el área sobre la que actúa la ΔP: puerto completo o corona de balanceo.",
           "Con desbalanceado y ΔP alta, el actuador resulta grande.",
           "Conviene balanceado con ΔP de cierre > 10 bar y 3\" o más.",
           "No aplica.", "No aplica.", ["Fuerza A", "Carga de asiento", "Gradiente negativo"],
           ["Balancee las válvulas grandes de alta ΔP.", "Verifique la clase de cierre del sello de balanceo."],
           "Puerto de 4 3/8\": área de puerto 15 in², corona balanceada 0,51 in²: A baja unas 30 veces."))

_e("act_friccion", "Empaquetadura considerada (fricción C)",
   "<p>Tipo de empaquetadura elegido en la solapa 3; sin selección de materiales se supone PTFE simple. La "
   "fricción típica es: PTFE simple ≈ 100 lbf por pulgada de vástago; PTFE doble ≈ 150; PTFE con carga viva "
   "≈ 60 a 725 lbf según vástago; grafito simple 190 a 3245 lbf según vástago y clase; grafito de alta "
   "hermeticidad 420 a 6790 lbf. El grafito llega a 10 veces el PTFE: en válvulas chicas puede ser la fuerza "
   "dominante.</p>",
   ACT, referencia=REF_F, relacionadas=["empaquetadura", "act_vastago"],
   guia=_g("Es la fricción que la empaquetadura opone al movimiento del vástago.",
           "Se suma en el cierre y en la apertura.", "Fricción alta empeora la resolución y la banda muerta.",
           "PTFE: ≈ 100 lbf/in de vástago. Grafito: 3 a 10 veces más.",
           "No aplica.", "No aplica.", ["Fuerza de cierre y apertura", "Resorte", "Resolución del control"],
           ["Use PTFE cuando la temperatura lo permite.", "Con grafito, prefiera la versión de baja fricción con carga viva."],
           "Vástago de 3/4\" CL600: PTFE simple 75 lbf; grafito simple 660 lbf."))

_e("act_tamano", "Tamaño del actuador (serie genérica)",
   "<p>Menor tamaño de una serie genérica que cumple todos los chequeos con el aire mínimo:</p><ul>"
   "<li>Diafragma: áreas efectivas de 46 a 450 in² (297 a 2903 cm²).</li>"
   "<li>Multiresorte: 35 a 279 in² con hasta unos 6 bar.</li>"
   "<li>Pistón: cilindros de 3 a 24\" de diámetro con hasta unos 10 bar.</li>"
   "<li>Piñón y cremallera y yugo escocés: par de doble efecto a 5,5 bar.</li>"
   "<li>Eléctricos: empuje de 0,6 a 250 kN o par de 35 a 40 000 N·m.</li></ul>"
   "<p>Los nombres (D-069, "
   "P-08…) son del programa y no corresponden a ningún fabricante.</p>",
   ACT, referencia="Práctica de la industria de válvulas de control", relacionadas=["act_tipo", "act_banco"],
   guia=_g("Es el tamaño sugerido del actuador.", "Resume la selección para la hoja de datos.",
           "Un tamaño en el extremo de la serie indica que conviene otra tecnología.", "Ver series.",
           "No aplica.", "No aplica.", ["Hoja de datos", "Costo y peso"],
           ["Confirme el modelo y el resorte con el fabricante del actuador.",
            "Si sale el mayor tamaño, evalúe balancear o cambiar de tecnología."],
           "D-156: diafragma de 156 in² (1006 cm²) con carrera de hasta 2\"."))

_e("act_banco", "Ajuste de banco (bench set)",
   "<p>Rango de presión que mueve el actuador en banco (sin válvula ni proceso) de una punta a la otra de la "
   "carrera: de la presión inferior Pbl, donde comienza a moverse, a la superior Pbu, donde completa la "
   "carrera.</p><ul>"
   "<li>Falla cierra: Pbl = fuerza de cierre × margen / área; el resorte asienta solo.</li>"
   "<li>Falla abre: Pbl = fricción / área (mínimo 3 psi); Pbu queda limitada por el aire disponible menos la "
   "fuerza de cierre.</li>"
   "<li>Rango (Pbu − Pbl) ≥ un tercio de la presión de operación y ≥ Kn·ΔP·L/A para la estabilidad.</li>"
   "<li>Pistones con resorte: ajuste de banco del resorte ≥ 5 psi.</li></ul>"
   "<p>Es el dato de calibración que el taller ajusta con el tornillo del resorte.</p>",
   ACT, formula="Pbl = F/A;  Ks = (Pbu − Pbl)·A / L", referencia=REF_F, relacionadas=["act_resorte", "act_P_req"],
   guia=_g("Es la calibración del resorte expresada en presión de aire.",
           "Define cuánta fuerza da el resorte en cada punta de la carrera.",
           "Un rango muy estrecho deja poca rigidez; uno muy ancho pide mucho aire.",
           "No más de 2/3 del rango de operación se usa para equilibrio estático.",
           "Pbl bajo con falla cierra: el resorte no asienta.", "Pbu alto: falta aire para completar la carrera.",
           ["Resorte", "Presión requerida", "Señales del posicionador"],
           ["Use el ajuste de banco calculado en la orden de compra del actuador."],
           "Diafragma de 69 in², fuerza de cierre 274 lbf: Pbl = 274/69 ≈ 4 psig; con rango de 12 psi, 4–16 psig."))

_e("act_resorte", "Resorte del actuador",
   "<p>Constante del resorte Ks, compresión inicial y carga máxima. La constante resulta del ajuste de banco: "
   "Ks = (Pbu − Pbl)·A / L. La compresión inicial es Pbl·A / Ks. En cuarto de vuelta se informa el par del resorte "
   "al comienzo y al final de su recorrido (relación típica 1,45).</p>",
   ACT, formula="Ks = (Pbu − Pbl)·A / L", referencia=REF_F, relacionadas=["act_banco", "act_gradiente"],
   guia=_g("Es el resorte que da la fuerza de falla.", "Fija la fuerza en el asiento y la rigidez del conjunto.",
           "Un resorte más rígido mejora la estabilidad pero pide más aire.",
           "Debe cumplir Ks ≥ Kn·ΔP (gradiente negativo).", "Resorte blando: inestabilidad cerca del asiento.",
           "Resorte rígido: más aire.", ["Estabilidad", "Presión requerida", "Carga del vástago"],
           ["Pida al fabricante el resorte con la constante más cercana sin superarla y ajuste el banco."],
           "Ks = (16 − 4) × 69 / 1,125 ≈ 736 lbf/in (129 N/mm)."))

_e("act_P_req", "Presión de aire requerida",
   "<p>Presión que necesita el actuador para cumplir en el extremo más exigente: con falla cierra, Pbu más la "
   "fuerza de apertura dividida por el área; con falla abre, Pbu más la fuerza de cierre dividida por el área. "
   "Debe ser menor que el aire mínimo disponible y que la presión máxima del actuador.</p>"
   "<p>Este valor bloquea en la solapa 5 las señales neumáticas que no lo alcanzan y sugiere el set de aire.</p>",
   ACT, formula="P = Pbu + F / A", referencia=REF_F, relacionadas=["act_aire", "pos_senal", "pos_set"],
   guia=_g("Es la presión de aire que el actuador necesita.", "Se compara con el aire disponible y limita señales.",
           "Si supera el aire mínimo, el actuador no cumple.", "Margen recomendado ≥ 0,3 bar.",
           "Con margen grande se puede elegir un actuador menor.", "Sin margen, crecer un tamaño.",
           ["Señales habilitadas", "Set de aire", "Margen de presión"],
           ["Deje margen frente a caídas de la red de aire."],
           "Pbu = 16 psig y fuerza de apertura 115 lbf en 69 in²: P = 16 + 1,7 ≈ 17,7 psig: la señal 3-15 psi "
           "queda bloqueada."))

_e("act_empuje", "Empuje o par disponible",
   "<p>Fuerza o par que el actuador entrega en cada sentido con el aire mínimo, para comparar con lo requerido. "
   "En pistones se aplica un rendimiento de 0,95 por los sellos.</p>",
   ACT, referencia=REF_F, relacionadas=["act_requerido", "act_tamano"],
   guia=_g("Es la capacidad real del actuador elegido.", "Permite ver el margen frente a la fuerza o par requerido.",
           "Un empuje apenas mayor que el requerido deja poco margen.", "Margen de diseño incluido: 1,10 / 1,25.",
           "No aplica.", "No aplica.", ["Selección del actuador"],
           ["Verifique ambos sentidos: cerrar y abrir."], "Empuje de cierre 276 lbf frente a 274 lbf requeridos."))

_e("act_gradiente", "Gradiente negativo (estabilidad)",
   "<p>Cerca del asiento la fuerza del fluido puede crecer al cerrar más rápido que la del resorte: el obturador "
   "se acelera hacia el asiento y golpetea. Se evita con un resorte cuya constante supere Kn·ΔP con caudal. Kn es "
   "0 en desbalanceados que tienden a abrir, 2·A<sub>puerto</sub>/carrera en desbalanceados que tienden a cerrar y "
   "un valor típico creciente con el puerto en balanceados (0,4 a 6 in).</p>",
   ACT, formula="Ks ≥ Kn·ΔP(máx con caudal)", referencia=REF_F, relacionadas=["act_resorte", "act_flujo"],
   guia=_g("Es la variación de la fuerza del fluido con la carrera.", "Fija la constante mínima del resorte.",
           "Si el resorte es más blando, el control es inestable cerca del cierre.", "Ks ≥ Kn·ΔP.",
           "No aplica.", "Resorte por debajo del mínimo: alerta.", ["Resorte", "Estabilidad"],
           ["Aumente el rango de banco o la presión de aire.", "Evite operar cerca del asiento."],
           "Kn = 0,42 in y ΔP con caudal 150 psi: Ks ≥ 63 lbf/in."))

_e("act_requerido", "Fuerza o par requerido con margen",
   "<p>Mayor de las fuerzas (o pares) de cierre y apertura multiplicada por el margen de diseño: 1,10 en vástago "
   "deslizante, 1,25 en rotativas y en actuadores eléctricos y electrohidráulicos.</p>",
   ACT, referencia=REF_F, relacionadas=["act_metodo", "act_empuje"],
   guia=_g("Es el requerimiento final que debe superar el actuador.", "Sirve para elegir el tamaño.",
           "Compárelo con el empuje o par del modelo ofertado.", "Margen 1,10 / 1,25.", "No aplica.", "No aplica.",
           ["Tamaño del actuador"], ["Pida al fabricante el empuje o par a la presión mínima."],
           "TB = 1412 lbf·in: par requerido 1,25 × 1412 = 1765 lbf·in (199 N·m)."))

# =====================================================================================
# 5-POSICIONADOR
# =====================================================================================
_e("pos_tag", "Tag del posicionador",
   "<p>Identificación del posicionador en el plano de instrumentos (por ejemplo ZY-101 o FY-101). Se copia a la "
   "hoja de datos.</p>", POS, relacionadas=["pos_tipo"],
   guia=_g("Es el código del instrumento.", "Se imprime en la hoja de datos.", "No aplica.", "No aplica.",
           "No aplica.", "No aplica.", ["Hoja de datos"], ["Use el tag del P&ID."], "FY-101."))

_e("pos_tipo", "Tipo de posicionador",
   "<p>Tecnología del posicionador. Define las señales posibles: neumático (señales en psi), electroneumático y "
   "digital HART (corriente de 4-20 mA y rangos partidos) o Foundation Fieldbus (señal digital). Los de "
   "diagnóstico avanzado registran firma de la válvula, fricción y desvíos para mantenimiento predictivo.</p>",
   POS, relacionadas=["pos_senal", "pos_accion"],
   guia=_g("Es el instrumento que lleva la válvula a la posición que pide la señal.",
           "Limita las señales de entrada y la acción.", "Un posicionador neumático no admite mA ni Fieldbus.",
           "No aplica.", "No aplica.", "No aplica.", ["Señales habilitadas", "Acción"],
           ["Prefiera digital con diagnóstico en válvulas críticas."], "Digital-HART con señal 4-20 mA dc."))

_e("pos_senal", "Señal de entrada",
   "<p>Señal del sistema de control. El programa bloquea:</p><ul>"
   "<li>las que no corresponden al tipo de posicionador;</li>"
   "<li>las señales neumáticas cuyo máximo no alcanza la presión que necesita el actuador o su ajuste de banco "
   "superior (por ejemplo, si hacen falta más de 15 psi quedan bloqueadas 3-15, 3-9 y 9-15 psi), porque con "
   "señal neumática directa o relé 1:1 el actuador no recibe más presión que la de la señal;</li>"
   "<li>todas las neumáticas si el actuador no es neumático.</li></ul>"
   "<p>Las bloqueadas se ven en gris y el motivo aparece al pasar el mouse.</p>",
   POS, relacionadas=["act_P_req", "pos_tipo"],
   guia=_g("Es la señal que comanda la posición.", "Se compara con la presión requerida por el actuador.",
           "Una señal bloqueada no alcanza para mover el actuador completo.",
           "3-15 psi: hasta 15 psi. 6-30 psi: hasta 30 psi.", "No aplica.", "No aplica.",
           ["Hoja de datos del posicionador"], ["Si se bloquea 3-15 psi, use 6-30 psi o un posicionador electrónico."],
           "Actuador que requiere 17,7 psig: 3-15, 3-9 y 9-15 psi bloqueadas."))

_e("pos_accion", "Acción del posicionador",
   "<p>Directa: al subir la señal sube la presión de salida. Inversa: al subir la señal baja. Doble: dos salidas "
   "para actuadores de doble efecto. Configurable: los digitales eligen la acción por software. El programa "
   "sugiere la acción según la falla y el actuador y avisa las incompatibles.</p>",
   POS, relacionadas=["act_falla", "act_tipo"],
   guia=_g("Es la relación entre la señal y la salida neumática.", "Debe ser coherente con la falla.",
           "Doble efecto necesita salida doble.", "No aplica.", "No aplica.", "No aplica.",
           ["Hoja de datos"], ["Use «Configurable» con posicionadores digitales."],
           "Falla cierra y señal creciente para abrir: acción directa."))

_e("pos_manometros", "Manómetros",
   "<p>Manómetros de alimentación y de salida en el posicionador. Ayudan a diagnosticar en campo.</p>", POS,
   relacionadas=["pos_set"],
   guia=_g("Son indicadores de presión del posicionador.", "Se informan en la hoja de datos.", "No aplica.",
           "No aplica.", "No aplica.", "No aplica.", ["Hoja de datos"], ["Pídalos siempre en neumáticos."],
           "Manómetros de 0-60 psi en alimentación y salida."))

_e("pos_set", "Set de aire de instrumentos (filtro-regulador)",
   "<p>Filtro-regulador que alimenta posicionador y actuador. Con un actuador que necesita hasta unos 27 psi se "
   "sugiere 0-30 psi; hasta unos 75 psi, 0-80 psi. El programa avisa si el rango no alcanza la presión requerida y "
   "lo usa para limitar la carga del vástago.</p>",
   POS, relacionadas=["act_P_req", "act_aire"],
   guia=_g("Es el filtro-regulador del aire.", "Limita la presión que llega al actuador.",
           "Sin regulador la carcasa y el vástago ven la presión de la red.",
           "0-30 psi hasta ≈ 27 psi requeridos; 0-80 psi hasta ≈ 75 psi.",
           "Rango menor que la presión requerida: no cumple.", "Rango muy amplio: regula con menos precisión.",
           ["Carga del vástago", "Presión en la carcasa"], ["Regule a la presión requerida más un margen."],
           "Actuador de 40 psig: set 0-80 psi regulado a unos 45 psig."))

# =====================================================================================
# 6-ACCESORIOS
# =====================================================================================
for _k, _t, _x in (
        ("acc_boosters", "Boosters (amplificadores de volumen)",
         "Relés de gran caudal que multiplican el aire del posicionador para mover rápido actuadores grandes."),
        ("acc_quick_exhaust", "Quick exhaust (escape rápido)",
         "Válvulas que ventean el actuador directamente a la atmósfera para cerrar o abrir rápido en un disparo."),
        ("acc_bloqueo", "Válvulas de bloqueo neumático (lock-up)",
         "Atrapan el aire del actuador al caer la alimentación para que la válvula quede en la última posición."),
        ("acc_cambio", "Válvula de cambio (switching valve)",
         "Conmuta el aire de un tanque de reserva al lado correcto del pistón al perder la alimentación, para dar "
         "una falla abre o cierra a un actuador de doble efecto sin resorte.")):
    _e(_k, _t, f"<p>{_x}</p><p>Celda de texto libre (modelo, cantidad, conexión). Si queda vacía no aparece en los "
               "documentos entregables.</p>", ACC, relacionadas=["act_falla", "act_tipo"],
       guia=_g(f"Es un accesorio neumático: {_t.lower()}.", "Se informa en la hoja de datos cuando tiene texto.",
               "Su ausencia puede generar una alerta si la falla o la velocidad lo requieren.", "No aplica.",
               "No aplica.", "No aplica.", ["Hoja de datos", "Alertas de accesorios"],
               ["Indique cantidad, conexión y caudal (Cv) del accesorio."], f"{_t}: 1 unidad, 1/2\" NPT."))

_e("acc_solenoide", "Válvula solenoide",
   "<p>Válvula eléctrica que ventea o presuriza el actuador por orden del sistema de seguridad o de control.</p><ul>"
   "<li><b>Tipo de acción</b>: «desenergiza para…» es a prueba de fallas (un corte de energía lleva a la posición "
   "segura); «energiza para…» no lo es.</li>"
   "<li><b>Vías</b>: 3 vías para actuadores de resorte (presuriza o ventea un lado), 4 vías para doble efecto, 2 "
   "vías solo para usos especiales.</li>"
   "<li><b>Material</b>: latón para ambientes limpios; inoxidable en ambientes corrosivos, agrios o costa afuera.</li>"
   "<li><b>Puertos y voltaje</b>: el puerto se elige por el volumen del actuador; potencia en texto libre "
   "(vacía no se informa).</li></ul>"
   "<p>Elija «No requerido» si la válvula no lleva solenoide.</p>",
   ACC, referencia="IEC 61508 / IEC 61511 (falla segura)", relacionadas=["act_falla", "acc_sol_falla"],
   guia=_g("Es la válvula eléctrica de disparo del actuador.", "Se verifica contra la falla y el actuador.",
           "Una acción contraria a la falla impide llevar la válvula a la posición segura.", "No aplica.",
           "No aplica.", "No aplica.", ["Hoja de datos", "Alertas"],
           ["Use desenergiza para la posición de falla.", "En actuadores grandes use puerto 1/2\" o escape rápido."],
           "Falla cierra: desenergiza para cerrar, 3 vías, inoxidable, 1/4\", 24 Vdc."))

_e("acc_limites", "Límites de carrera",
   "<p>Interruptores que indican válvula abierta y cerrada: mecánicos, de proximidad inductiva o magnéticos. "
   "Contactos SPST, SPDT o DPDT. Voltaje y corriente en texto libre (vacíos no se informan); la frecuencia solo se "
   "informa en corriente alterna o si no se indicó el voltaje.</p>", ACC, relacionadas=["acc_solenoide"],
   guia=_g("Son indicadores de posición final.", "Se informan en la hoja de datos.", "No aplica.", "No aplica.",
           "No aplica.", "No aplica.", ["Hoja de datos"], ["Use proximidad en ambientes con vibración."],
           "Proximidad, SPDT, 24 Vdc."))

# =====================================================================================
# ALERTAS
# =====================================================================================
_alerta("act_no_alcanza", "El actuador no alcanza", "<p>Ningún tamaño de la serie genérica del tipo elegido da la "
        "fuerza o el par con el aire mínimo.</p>", "La tecnología o el aire no alcanzan para la válvula.",
        "Fuerza requerida mayor que la del mayor tamaño.",
        ["Subir el aire mínimo o usar booster.", "Balancear el obturador.", "Cambiar a pistón o electrohidráulico."],
        "Diafragma en globo de 3\" desbalanceado con 75 bar: no alcanza; pistón sí.", ["act_tipo", "act_tamano"])
_alerta("act_aire_insuficiente", "Aire de instrumentos insuficiente", "<p>La presión requerida por el actuador "
        "supera el aire mínimo disponible.</p>", "El actuador no completa la carrera o no asienta.",
        "Presión requerida > aire mínimo.", ["Elegir un actuador mayor.", "Subir el aire mínimo garantizado."],
        "Requiere 5 bar g con red de 4 bar g mínima.", ["act_aire", "act_P_req"])
_alerta("act_presion_carcasa", "Aire máximo sobre el límite del actuador", "<p>La presión máxima de la red supera la "
        "presión admisible de la carcasa o del cilindro.</p>", "Hace falta regular la alimentación.",
        "Aire máximo > presión máxima del actuador (diafragma ≈ 3,4 bar).",
        ["Regular con el set de aire por debajo del límite."], "Red de 7 bar g con diafragma de 3,4 bar.",
        ["pos_set", "act_aire"])
_alerta("act_vastago", "Carga del vástago excesiva", "<p>La fuerza que el actuador aplica sobre el vástago en el "
        "asiento supera la admisible por pandeo a la temperatura de diseño.</p>", "Riesgo de doblar el vástago.",
        "Carga > admisible (316 endurecido, L/D ≤ 12,5).",
        ["Vástago mayor o de 17-4PH / S20910.", "Regular el aire.", "Actuador más chico."],
        "Resorte de 39 kN con vástago de 3/4\" a 110 °C (admisible 42 kN): al límite.", ["act_vastago"])
_alerta("act_fl_resorte", "Última posición con actuador de resorte", "<p>El resorte lleva la válvula a su posición al "
        "perder aire: para la última posición se requiere bloqueo neumático.</p>", "Falta un accesorio.",
        "Falla FL con actuador de resorte.", ["Agregar válvula de bloqueo neumático."], "Diafragma con lock-up.",
        ["acc_bloqueo"])
_alerta("act_falla_electrico", "Falla de un actuador eléctrico", "<p>El actuador eléctrico queda en la última "
        "posición si no lleva resorte o reserva de energía.</p>", "La falla pedida no se cumple.",
        "Falla FC o FO con eléctrico.", ["Módulo de falla segura.", "Cambiar a FL."], "Eléctrico con supercapacitor.",
        ["act_falla"])
_alerta("act_manual_falla", "Actuador manual sin falla", "<p>Un actuador manual no tiene posición de falla.</p>",
        "La falla pedida no se cumple.", "Falla FC o FO con manual.", ["Elegir FL."], "Volante en bypass.",
        ["act_falla"])
_alerta("act_factores_par", "Factores de par estimados", "<p>Se ajustaron los factores típicos del estilo (asiento "
        "elastomérico, bola flotante o triple excéntrica).</p>", "El par real puede ser mayor.", "No aplica.",
        ["Confirmar el par con el fabricante."], "Triple excéntrica: B × 1,5.", ["act_metodo"], REF_T)
_alerta("act_sin_aire", "Falta el aire de instrumentos", "<p>No se cargó la presión mínima del aire.</p>",
        "No se puede dimensionar un actuador neumático.", "Aire mínimo vacío.", ["Cargar el aire en 4-Actuador."],
        "4 a 7 bar g.", ["act_aire"])
_alerta("act_aire_rango", "Aire máximo menor que el mínimo", "<p>Los valores de aire están invertidos.</p>",
        "Error de carga.", "Máx < mín.", ["Corregir los valores."], "Mín 4, máx 7 bar g.", ["act_aire"])
_alerta("act_cierre_supuesto", "ΔP de cierre supuesta", "<p>Sin caso Tight Shutoff se supone cierre contra la "
        "presión de entrada máxima con salida atmosférica.</p>", "El actuador puede quedar sobredimensionado.",
        "Caso Tight Shutoff vacío.", ["Cargar el caso Tight Shutoff."], "P1 máx 10 bar g: ΔP de cierre 10 bar.",
        ["act_metodo"])
_alerta("act_incompatible", "Actuador incompatible", "<p>Un actuador de cuarto de vuelta no mueve una válvula de "
        "vástago deslizante, y un diafragma o un pistón lineal no mueven el eje de una rotativa.</p>",
        "Elección imposible.", "Piñón y cremallera o yugo en globo; diafragma o pistón en mariposa o bola.",
        ["Elegir un actuador habilitado para la válvula."], "Mariposa con diafragma y resorte.", ["act_tipo"])
_alerta("act_flujo_trim", "Sentido del flujo distinto del trim", "<p>El sentido elegido no coincide con el del trim "
        "de la solapa 2.</p>", "FL, xT y la fuerza quedan incoherentes.", "Flow ≠ sentido del trim.",
        ["Elegir el mismo sentido."], "Trim que tiende a cerrar con Flow Up.", ["act_flujo"])
_alerta("act_flujo_valvula", "Flow no corresponde a la válvula", "<p>Up y Down aplican solo a globo y ángulo; "
        "Unidireccional a rotativas y Bidireccional solo a bola flotante o trunnion. Si un proyecto anterior trae "
        "una opción que no corresponde, el cálculo usa la que sí aplica.</p>", "El sentido elegido no se usó.",
        "Opción de Flow bloqueada para la válvula.", ["Elegir una opción habilitada en Flow."],
        "Mariposa con Flow Up.", ["act_flujo"])
_alerta("act_asiento_blando_dp", "ΔP sobre el límite del PTFE", "<p>El asiento blando de PTFE admite hasta unos "
        "99 bar de ΔP de cierre.</p>", "El inserto se extruye.", "ΔP > 1440 psi.", ["Usar asiento metálico clase V."],
        "ΔP 120 bar con clase VI blanda.", ["clase_cierre"])
_alerta("act_clase_v", "Vida del cierre clase V", "<p>Con asiento metálico clase V, una carga de asiento de unas "
        "800 lbf/in de perímetro prolonga la vida del cierre.</p>", "Oportunidad de mejora.", "Clase V metálica.",
        ["Evaluar mayor carga de asiento si el cierre es crítico."], "Puerto 4\": 800 × 12,6 ≈ 10 000 lbf.",
        ["clase_cierre"])
_alerta("act_balance_cierre", "Sello de balanceo y cierre alto", "<p>Con balanceado y clase V o superior el sello "
        "también debe cerrar.</p>", "Se usa la carga de asiento del sello.", "Balanceado con clase ≥ V.",
        ["Verificar con el fabricante."], "Sello de grafito clase V.", ["act_obturador"])
_alerta("act_balance_supuesto", "Obturador balanceado supuesto", "<p>Sin dato de balanceo se supuso balanceado "
        "(jaula, 3\" o más, ΔP > 10 bar).</p>", "Supuesto del programa.", "Balanceo en Automático.",
        ["Indicar el balanceo en la solapa 2."], "Globo de jaula de 6\" con 20 bar.", ["act_obturador"])
_alerta("pos_senal_bloqueada", "Señal de entrada no apta", "<p>La señal elegida no corresponde al posicionador o no "
        "alcanza la presión del actuador.</p>", "El actuador no completa la carrera con esa señal.",
        "Máximo de la señal < presión requerida.", ["Elegir una señal habilitada."],
        "3-15 psi con 17,7 psig requeridos.", ["pos_senal"], REF_F)
_alerta("pos_set_rango", "Rango del set de aire", "<p>El rango del regulador no es el adecuado para la presión "
        "requerida.</p>", "No regula o regula con poca precisión.", "Rango < presión requerida.",
        ["Elegir el set sugerido."], "Set 0-30 psi con 40 psig requeridos.", ["pos_set"])
_alerta("pos_sin_set", "Sin set de aire", "<p>Sin filtro-regulador el actuador ve la presión de la red sin "
        "filtrar.</p>", "Riesgo para carcasa, vástago y posicionador.", "Set de aire = No.", ["Agregar set de aire."],
        "Red de 7 bar g sin regulador.", ["pos_set"])
_alerta("acc_sol_falla", "Solenoide contraria a la falla", "<p>La solenoide ventea el actuador y lo lleva a la "
        "falla, que es la posición opuesta a la que se pide.</p>", "La función de disparo no se cumple.",
        "Acción contraria a la falla.", ["Elegir «Desenergiza para» la posición de falla."],
        "Falla cierra con «Desenergiza para abrir».", ["acc_solenoide", "act_falla"])
_alerta("acc_sol_energiza", "Solenoide energiza para actuar", "<p>La función depende de la energía eléctrica.</p>",
        "No es a prueba de fallas.", "Acción «Energiza para…».", ["Preferir desenergiza para actuar."],
        "Disparo de seguridad con bobina normalmente desenergizada.", ["acc_solenoide"])
_alerta("acc_sol_vias", "Vías de la solenoide", "<p>3 vías para simple efecto y 4 vías para doble efecto.</p>",
        "La solenoide no puede ventear o conmutar el actuador.", "Vías incompatibles.", ["Elegir las vías indicadas."],
        "Pistón de doble efecto con solenoide de 3 vías.", ["acc_solenoide"])
_alerta("acc_sol_material", "Solenoide de latón en ambiente agrio", "<p>El latón se corroe con H₂S y amoníaco.</p>",
        "Corrosión de la solenoide.", "Servicio agrio.", ["Usar acero inoxidable."], "Planta de gas agrio.",
        ["acc_solenoide"])
_alerta("acc_sol_puerto", "Puerto de solenoide chico", "<p>Un puerto de 1/4\" ventea lento un actuador grande.</p>",
        "Tiempo de carrera largo.", "Área ≥ 220 in² con 1/4\".", ["Puerto 1/2\" o escape rápido."],
        "Diafragma de 300 in² con solenoide de 1/4\".", ["acc_solenoide", "acc_quick_exhaust"])
_alerta("acc_lockup", "Falta la válvula de bloqueo neumático", "<p>La falla en última posición con resorte requiere "
        "bloqueo neumático.</p>", "La falla pedida no se cumple.", "FL con resorte y bloqueo vacío.",
        ["Completar «Válvulas de bloqueo neumático»."], "Lock-up en la salida del posicionador.", ["acc_bloqueo"])
_alerta("acc_switching", "Falta tanque y válvula de cambio", "<p>Un pistón de doble acción sin resorte necesita "
        "tanque de reserva y válvula de cambio para la falla abre o cierra.</p>", "La falla pedida no se cumple.",
        "FC o FO con pistón sin resorte.", ["Completar «Válvula de cambio» y dimensionar el tanque."],
        "Tanque de 20 l con válvula de cambio.", ["acc_cambio"])
