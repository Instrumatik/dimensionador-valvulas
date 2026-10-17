# Valveselect-N25 — INSTRUMATIK S.A.S.

Programa independiente de marcas para dimensionar y verificar válvulas de control
según IEC 60534-2-1 / ANSI/ISA-75.01.01, con cavitación y ruido IEC 60534-8-4,
tuberías ASME B36.10M / B36.19M, rating ASME B16.34 (referencial) y clases de
cierre ANSI/FCI 70-2. La versión 2 trabaja **solo con líquidos**; el núcleo de
cálculo de gases, vapor y bifásico se conserva para versiones futuras. Ver
[ARQUITECTURA.md](ARQUITECTURA.md).

## Flujo de trabajo

1. **Inst-Valve-Data**: identificación del proyecto, estilo de válvula, rating, diámetros y
   cédulas de tubería de entrada y salida, ruido permitido, conexión a proceso, presión y
   temperatura de diseño y clase de cierre.
2. **Dim-Valve-Data**: fluido, caudal volumétrico o másico, P1, P2, T1, gravedad específica,
   viscosidad, Pv y Pc para los casos mínimo, normal y máximo; tipo de trim con sus factores
   típicos FL, Fd y Kc (editables), diámetro de válvula y Cv nominal. Los diámetros y cédulas
   de tubería se copian desde Inst-Valve-Data.
3. **Calcular**: los resultados aparecen debajo de las entradas (celdas verdes) con las
   alertas, su intensidad y las soluciones posibles.
4. **Memoria de cálculo**, **Hoja de datos** e **Informe técnico**: vistas previas que se
   exportan a Word editable o se imprimen desde *Inicio → Entregables*, por separado o todos
   juntos.

«Ir» o F1 sobre cualquier dato abre su explicación. El selector de unidades (SI / Imperial)
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
* Windows local: `compilar_windows.bat`. Resultado: `dist\Valveselect-N25\Valveselect-N25.exe`.
* macOS / Linux local: `./compilar.sh`.
* `Valveselect-N25 --prueba` verifica el ejecutable con el ejemplo 1 de IEC 60534-2-1.

## Licencias y demo

* Al abrirse, el programa pide un código de licencia (`VS1-…`) firmado con la clave privada de
  INSTRUMATIK (Ed25519). El programa solo contiene la clave pública (`dimensionador/licencia.py`).
* Tipos: **demo** (30 días, marca de agua con el nombre del usuario en todos los documentos),
  **anual** (365 días) y **propietaria** (sin vencimiento).
* El vencimiento se controla contra la fecha del equipo; si el reloj se atrasa respecto del último
  uso, el programa se bloquea hasta corregir la fecha.
* Los códigos se crean con `generador_codigos.py` (compilado aparte como
  «Generador-codigos-Valveselect»), que necesita la clave privada y anota cada código en
  `registro_codigos.csv`. La clave privada nunca se sube al repositorio (`*.pem` está ignorado).
