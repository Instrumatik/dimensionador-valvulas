# Valveselect-N25 (INSTRUMATIK S.A.S.): plan y arquitectura

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
  asme_b16_34.py    Clases de presión-temperatura y materiales ASTM
  tuberias.py       Diámetro exterior y espesor por NPS y cédula (ASME B36.10M / B36.19M)
  proyecto.py       Versión 2 (líquidos): datos de instalación y de dimensionamiento, Kapp/Kc,
                    verificaciones de rating, conexión, cierre y velocidad, recomendaciones
  entregables.py    Memoria de cálculo, hoja de datos e informe técnico (HTML y Word .docx)
  grafico.py        Gráfico de Cv vs. apertura (PNG con Qt)
  ayuda.py          Textos de ayuda en español por dato, coeficiente, fenómeno y opción
  gui/ventana.py    Interfaz PySide6: Inst-Valve-Data, Dim-Valve-Data y vistas de entregables
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
| 6. Versión 2 (solo líquidos): flujo Inst-Valve-Data → Dim-Valve-Data, tuberías por cédula, Kc/Kapp, entregables Word e impresión, marca Valveselect-N25 | Hecho, en validación |

## Próximos pasos sugeridos

* Fuerza y par del actuador para la clase de cierre (anunciado en el informe técnico).
* Materiales de cuerpo e internos (las entradas se quitaron en la versión 2).
* Volver a habilitar gases, vapor y bifásico en la interfaz de la versión 2.
* Más grupos de materiales ASME B16.34 (1.2 LCC, 1.3 LCB, 1.9 WC6, 1.10 WC9, 2.1 CF8) verificados
  contra la edición vigente de la norma.
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
