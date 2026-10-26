# N25 Valves Sizing — INSTRUMATIK S.A.S.

Programa independiente de marcas para dimensionar y verificar válvulas de control
según IEC 60534-2-1 / ANSI/ISA-75.01.01, con cavitación y ruido IEC 60534-8-4,
tuberías ASME B36.10M / B36.19M, rating ASME B16.34 con el material del cuerpo, selección de materiales y clases de
cierre ANSI/FCI 70-2. La versión 2 trabaja **solo con líquidos**; el núcleo de
cálculo de gases, vapor y bifásico se conserva para versiones futuras. Ver
[ARQUITECTURA.md](ARQUITECTURA.md).

## Flujo de trabajo

1. **1-Sistema**: identificación del proyecto, estilo de válvula (globo, ángulo, mariposa, bola de paso
   completo o reducido, bola trunnion / Bola-T, bola segmentada con corte en V de 90°, 60° o 30° y tapón
   excéntrico, cada uno con sus factores FL, xT, Fd y Kc), rating, diámetros y
   cédulas de tubería de entrada y salida, ruido permitido, conexión a proceso, presión y
   temperatura de diseño y clase de cierre.
2. **2-Cálculos Válvula**: fluido, caudal volumétrico o másico, P1, P2, T1, gravedad específica,
   viscosidad, Pv y Pc para los casos mínimo, normal y máximo; calidad / variante del fluido (por ejemplo,
   agua de mar, que corrige SG, μ y Pv por salinidad) y agua libre, que también usa la selección de materiales; tipo de trim con sus factores
   típicos FL, Fd y Kc (editables), diámetro de válvula y Cv nominal. **Gas natural** (v0.11.0) con composición
   molar editable: M, μ, κ, Z1, T2 y Z2 salen de la ecuación de estado multicomponente. Trim «Doble guía de vástago
   - superior». Desde v0.12.0 el trim se elige en tres datos independientes: **estilo de trim** (geometría),
   **sentido de flujo** (tiende a abrir o a cerrar; la fila Flow del actuador lo toma de aquí) y **característica**.
   El Cv típico, el puerto y la carrera de globo y ángulo salen de una **tabla de capacidad** por familia
   (contorneado, jaula, jaula de orificios, multietapa), mediana de datos publicados de fabricantes, y van ligados
   entre sí; el programa avisa si el puerto, la carrera o el Cv cargados se apartan más de ±10 % del típico. Los diámetros y cédulas
   de tubería se copian desde 1-Sistema. El programa informa el tamaño del trim (diámetro del puerto) en
   pulgadas y milímetros, la carrera nominal del vástago y la carrera de operación de cada caso (en las
   rotativas, la rotación del eje); si se cargan el puerto y la carrera certificados, reemplazan a los estimados.
   Un puerto certificado menor que el del trim completo se trata como **trim reducido**: el programa muestra el
   puerto y el Cv típicos del trim completo, el puerto reducido y el Cv con el puerto reducido (el certificado o,
   en blanco, el típico de ese puerto y esa carrera según la tabla de capacidad), y usa ese Cv en la apertura, la carrera, la curva y el actuador.
3. **3-Materiales**: el fluido llega definido desde la solapa 2 (tipo, fluido, calidad / variante y agua
   libre); aquí solo se agregan los datos complementarios: industria, agentes químicos con su
   concentración, sólidos, pH y norma de servicio agrio. El programa recomienda el material de cuerpo, bonete, asiento, jaula, guía,
   obturador y vástago (modo AUTOMÁTICO) o verifica el elegido por el usuario (MANUAL, no
   recomendado), con galling, dureza por cavitación, ISO 15156 / ISO 17945 y límites P-T de ASME B16.34.
   Evalúa además 17 juegos de internos estándar (asiento, jaula y obturador compatibles, con código propio
   N25-T01 a N25-T17), informa el que coincide con la selección o el apto más económico y permite elegir
   uno completo. También elige la empaquetadura del vástago (15 opciones: PTFE en V simple o doble para
   presión o vacío, trenzada, con carga viva, grafito simple, grafito de alta hermeticidad con resortes de
   17-7PH o Inconel 718, o fuelle; con carga viva, guía de temperatura y tipo) y el tipo de bonete
   según temperatura, presión, química, vacío y emisión fugitiva (ISO 15848-1, API 622 / 624 / 641).
4. **4-Actuador**, **5-Posicionador** y **6-Accesorios** (v0.9.0): con el tipo de actuador, el modo de
   falla, el volante, el aire de instrumentos disponible (mínimo y máximo) y el sentido del flujo, el
   programa calcula la fuerza (vástago deslizante: desbalance + carga de asiento por clase de cierre +
   fricción de la empaquetadura elegida) o el par (rotativas: arranque y dinámico), elige el tamaño de
   actuador genérico, el banco de resorte, la constante del resorte y la presión de aire necesaria, y
   verifica el vástago, el aire y el volante. En el posicionador bloquea las señales de entrada que no
   alcanzan la presión necesaria; en accesorios revisa la coherencia de la solenoide con el modo de falla.
   Las celdas de texto que quedan vacías no aparecen en los entregables. En modo **MANUAL** (v0.10.0) se
   cargan los datos certificados del actuador ofertado (área, banco, carrera, presión máxima, pares o empuje
   nominal) y el programa lo verifica con CUMPLE / NO CUMPLE y su margen; la fricción certificada de la
   empaquetadura reemplaza la típica en los dos modos.
   La sección **Datos para verificación con software de fabricante** (v0.10.2) entrega los datos de la
   válvula en el orden y las unidades que piden las herramientas de actuadores de los fabricantes (rango de
   operación, puerto, área desbalanceada, vástago, fricción, carga de asiento, presiones de cierre, gradiente
   negativo…), con cómo obtuvo N25 cada uno, y compara lo que devuelven (área, banco, fuerza) con su lectura.
   **Operating Range** (v0.10.3): AUTOMÁTICO, los rangos estándar 0,5–18, 0,5–33, 3–15, 6–30, 0–18, 0–33,
   0–40 y 0–50 psig, u Optimized con Pa y Pb a mano. Pb limita el aire del actuador y Pa, que queda aplicada
   con la señal mínima, resta fuerza al resorte en la posición de falla.
5. **Calcular**: los resultados aparecen debajo de las entradas (celdas verdes) con las
   alertas, su intensidad y las soluciones posibles.
6. **Memoria de cálculo**, **Hoja de datos** e **Informe técnico**: vistas previas que se
   exportan a Word editable o se imprimen desde *Inicio → Entregables*, por separado o todos
   juntos.

«Ver» o F1 sobre cualquier dato abre su explicación. El buscador del encabezado encuentra datos, opciones de
las listas y temas de ayuda y lleva a cada uno. El selector de unidades (SI / Imperial)
cambia todo el programa, incluidos los documentos; cada dato además tiene su propia unidad.

## Uso (versión de desarrollo)

```
python -m pip install -r requirements.txt
python -m pytest tests          # validación
python -m dimensionador         # abre el programa
```

## Compilar el ejecutable

* Automático: flujo `.github/workflows/compilar.yml` (pestaña Actions → «Compilar ejecutables»),
  genera Windows, macOS y Linux y prueba que la ventana abre.
* Windows local: `compilar_windows.bat`. Resultado: `dist\N25-Valves-Sizing\N25-Valves-Sizing.exe`.
* macOS / Linux local: `./compilar.sh`.
* `N25-Valves-Sizing --prueba` verifica el ejecutable con el ejemplo 1 de IEC 60534-2-1.

## Selección de trim

En líquidos, «Datos para cavitación hidrodinámica» (2-Cálculos Válvula) elige el trim anticavitación:
estándar, jaula de orificios chicos de una etapa o multietapa de 2, 3, 4 o 6 etapas. La caída se reparte
con igual Kapp por etapa; cambian FL, Fd, Kc, la ΔP de cavitación y de bloqueo, el Cv por tamaño y el ruido
(IEC 60534-8-4 con la última etapa), y el programa informa las etapas necesarias sin cavitación y aceptando
cavitación incipiente.

Con cada cálculo el tablero de resultados muestra el trim recomendado (estándar, jaula caracterizada,
jaula de 60 o 120 orificios, multietapa con número orientativo de etapas, o angular para flashing).
«Selección de trim y manual (PDF)…» (en el tablero, en Inicio > Entregables o en Ayuda) genera un PDF
con el razonamiento para la válvula calculada y el manual técnico completo de selección de trim. Los
criterios están en `dimensionador/seleccion_trim.py` y el texto del manual en
`dimensionador/manual_trim_texto.py`.

## Licencias y demo

* Al abrirse, el programa pide un código de licencia (`VS1-…`) firmado con la clave privada de
  INSTRUMATIK (Ed25519). El programa solo contiene la clave pública (`dimensionador/licencia.py`).
* Tipos: **demo** (30 días, marca de agua con el nombre del usuario en todos los documentos),
  **anual** (365 días) y **propietaria** (sin vencimiento).
* El vencimiento se controla contra la fecha del equipo; si el reloj se atrasa respecto del último
  uso, el programa se bloquea hasta corregir la fecha.
* Los códigos se crean con `generador_codigos.py` (compilado aparte como
  «Generador-codigos-N25»), que necesita la clave privada y anota cada código en
  `registro_codigos.csv`. La clave privada nunca se sube al repositorio (`*.pem` está ignorado).
