# N25 Valves Sizing (INSTRUMATIK S.A.S.): plan y arquitectura

Software independiente de marcas para EPC, plantas industriales e ingenieros
revisores. Todo en español, sin "caja negra": cada dato tiene ayuda y cada
resultado muestra la fórmula y la cláusula de la norma que lo produce.

## Tecnología elegida

| Necesidad | Elección | Motivo |
|---|---|---|
| Lenguaje | Python 3.11+ | Cálculo numérico claro y verificable, gran ecosistema técnico. |
| Interfaz | PySide6 (Qt 6, licencia LGPL) | Aspecto nativo en Windows, macOS y Linux; apto para venta comercial. |
| Propiedades de fluidos | CoolProp (licencia MIT) | Agua y vapor IAPWS-95 y más de 100 fluidos; uso comercial permitido. |
| Ejecutable | PyInstaller | `.exe` en Windows, `.app` en macOS, binario/AppImage en Linux. |
| Pruebas | pytest | Validación contra los ejemplos resueltos de las normas. |

## Módulos

```
dimensionador/
  unidades.py       Conversión SI ⇄ imperial (presión abs/man, T, caudales, viscosidad...)
  modelos.py        Alertas (severidad, intensidad, remedios) y memoria de cálculo paso a paso
  iec60534_2_1.py   Ecuaciones de dimensionamiento: líquidos, gases y vapores, FP, FLP, xTP, Reynolds, FR
  fenomenos.py      Cavitación, flashing, flujo crítico, Mach, velocidad, API RP 14E, apertura
  propiedades.py    Propiedades termofísicas (CoolProp): densidad, Pv, Pc, viscosidad, γ, Z, calidad
  estilos.py        Estilos genéricos de válvula (FL, xT, Fd típicos de IEC 60534-2-1) y tamaños
  servicio.py       Varios casos de operación (mín/normal/máx), selección de tamaño, informe
  ruido.py          Ruido aerodinámico IEC 60534-8-3 e hidrodinámico IEC 60534-8-4
  asme_b16_34.py    Clases de presión-temperatura ASME B16.34 por grupo de material
  datos_b16_34.py   Tablas numéricas de B16.34-2017 (49 grupos, clases 150 a 2500), generadas
  fluido_servicio.py  Definición única del fluido: variantes, agua libre, corrección salina y datos para materiales
  materiales.py     Biblioteca de materiales por componente (ASTM/UNS, dureza, PREN, NACE, costo)
  quimica.py        Agentes químicos, normalización de unidades y compatibilidad A–D por material
  seleccion_materiales.py  Selección por componente: química, P-T, cavitación/dureza, galling,
                    servicio agrio (ISO 15156 / ISO 17945), modo manual y alertas
  juegos_trim.py    Juegos de internos estándar (N25-T01…T17): asiento, jaula y obturador compatibles
  geometria.py      Tamaño del trim (puerto) y carrera del vástago, estimados o certificados
  anticavitacion.py Trims anticavitación por etapas (líquidos): reparto de igual Kapp por etapa,
                    factores equivalentes FL, Kc y xFz, y etapas recomendadas
  empaquetaduras.py Empaquetadura del vástago y tipo de bonete: temperatura, presión, química,
                    vacío y emisión fugitiva (ISO 15848-1, API 622 / 624 / 641)
  tuberias.py       Diámetro exterior y espesor por NPS y cédula (ASME B36.10M / B36.19M)
  proyecto.py       Versión 2 (líquidos): datos de instalación y de dimensionamiento, Kapp/Kc,
                    verificaciones de rating, conexión, cierre y velocidad, recomendaciones
  entregables.py    Memoria de cálculo, hoja de datos e informe técnico (HTML y Word .docx)
  grafico.py        Gráfico de Cv vs. apertura (PNG con Qt)
  ayuda.py          Textos de ayuda en español por dato, coeficiente, fenómeno y opción
  ayuda_mat_*.py    Ayuda de la solapa 3-Materiales (parámetros, componentes, alertas y agentes)
  gui/ventana.py    Interfaz PySide6: 1-Sistema, 2-Cálculos Válvula, 3-Materiales y entregables
  gui/solapa_materiales.py  Solapa 3-Materiales, análisis por componente y biblioteca
  actuadores.py     Fuerzas (A+B+C+D) y pares de cierre, resorte y banco, tamaños genéricos de actuador
                    (AUTOMÁTICO) o verificación del actuador certificado (MANUAL), fricción certificada,
                    vástago, aire, volante, bloqueo de señales del posicionador y coherencia de accesorios
  ayuda_actuador.py Ayuda de las solapas 4-Actuador, 5-Posicionador y 6-Accesorios
  gui/solapa_actuador.py  Solapas 4-Actuador, 5-Posicionador y 6-Accesorios
  gui/botones.py    Estilo y animación de los botones (hover, presionado y brillo de «Calcular»)
  gui/buscador.py   Buscador del encabezado: datos, opciones de las listas y temas de ayuda
tests/              Validación contra ejemplos de las normas
```

## Estado

| Fase | Estado |
|---|---|
| 1. Núcleo IEC 60534-2-1 / ISA-75.01.01: líquidos, gases, vapor, flujo crítico, reductores, flujo no turbulento | Hecho y validado |
| Cavitación (IEC 60534-8-4 / ISA-RP75.23), flashing con % de vapor, Mach, velocidad, API RP 14E, apertura | Hecho |
| 2. Interfaz en español: SI/imperial, ayuda «?»/F1 en cada dato (74 temas), alertas con intensidad y remedios, memoria de cálculo, proyectos `.valvula`, informe PDF/HTML | Hecho (primera versión) |
| 3. Ruido IEC 60534-8-3 (gases) e IEC 60534-8-4 (líquidos) | Hecho y validado |
| 4. Bifásico (método de suma de fases), ASME B16.34 grupos 1.1 y 2.2 con materiales ASTM | Hecho |
| 5. Ejecutables Windows, macOS y Linux por GitHub Actions, con prueba de cálculo y de ventana | Hecho |
| 7. Materiales (v0.7.0): selección por componente, galling, NACE, dureza por cavitación, biblioteca y ayuda | Hecho, en validación |
| 8. Actuador, posicionador y accesorios (v0.9.0): fuerza/par, resorte, aire, vástago, señales y solenoide | Hecho, en validación |
| 6. Versión 2 (solo líquidos): flujo 1-Sistema → 2-Cálculos Válvula, tuberías por cédula, Kc/Kapp, entregables Word e impresión, marca N25 Valves Sizing | Hecho, en validación |

## Próximos pasos sugeridos

* Datos certificados del actuador ofertado (área efectiva, resorte) para reemplazar los tamaños genéricos.
* Volver a habilitar gases, vapor y bifásico en la interfaz de la versión 2.
* Variación de FL y xT con la carrera (hoy se usan valores a carrera nominal).
* Hoja de datos de válvula en formato IEC 60534-7 / ISA-20.
* Ruido para internos multietapa y multiorificio (anexos de IEC 60534-8-3).
* Instalador firmado, licencias por cliente y manual de usuario.

## Neutralidad de marca

No se usa ningún dato de fabricante. FL, xT y Fd son los valores típicos
publicados en la Tabla 2 de IEC 60534-2-1:2011. La capacidad nominal por
tamaño (Cv/d²) es un valor representativo del estilo, rotulado como "típico"
en el programa, y el usuario puede reemplazar cualquier factor por los datos
certificados de la válvula ofertada.

## Validación actual

`python -m pytest tests` (35 pruebas, incluidas pruebas de la interfaz y de los documentos Word). Ejemplos resueltos del Anexo de
IEC 60534-2-1:2011 reproducidos:

| Ejemplo | Norma | Programa |
|---|---|---|
| 1. Líquido turbulento, no crítico (agua 90 °C, globo DN150) | Kv 165, Rev 2,967·10⁶ | Kv 164,9, Rev 2,968·10⁶ |
| 2. Líquido con flujo crítico (bola segmentada DN100) | Kv 238 | Kv 237,9 |
| 3. Gas no crítico (CO₂, rotativa excéntrica DN100) | Y 0,674, Kv 62,7 | Y 0,674, Kv 62,7 |

Ruido: los 6 ejemplos de IEC 60534-8-3 y los 3 de IEC 60534-8-4 coinciden
con diferencias menores a 0,01 dB (valores de referencia según la biblioteca
de código abierto «fluids», que los reproduce de las normas).

Pendiente de validar contra la norma: el ejemplo de flujo no turbulento
(cláusula 9 de IEC 60534-2-1) y las tablas de ASME B16.34 contra la edición
que use el cliente. El método bifásico no está normalizado por IEC.
