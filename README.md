# Dimensionador de válvulas de control

Programa independiente de marcas para dimensionar válvulas de control según
IEC 60534-2-1 / ANSI/ISA-75.01.01, con detección de cavitación, flashing,
flujo crítico y velocidades excesivas. Ver [ARQUITECTURA.md](ARQUITECTURA.md)
para el plan completo.

## Uso (versión de desarrollo)

```
python -m pip install -r requirements.txt
python -m pytest tests          # validación contra los ejemplos de la norma
python -m dimensionador         # abre el programa
python demo_consola.py          # tres casos de ejemplo por consola
```

## Cómo se usa

1. Elegí el tipo de servicio (líquido, gas o vapor de agua), el fluido y el sistema de unidades.
2. Cargá caudal, P1, P2 y T1 para los casos mínimo, normal y máximo. Con un fluido de la lista
   las propiedades se calculan solas; con «Definido por el usuario» se cargan a mano.
3. Elegí el estilo de válvula, el diámetro (o «Automático») y la tubería.
4. Presioná **Calcular**. Las pestañas muestran resultados, alertas con intensidad y
   soluciones, memoria de cálculo paso a paso y la tabla de selección de tamaño.
5. «?» o F1 sobre cualquier dato abre su explicación. Doble clic sobre un resultado también.
6. Archivo → Guardar proyecto (.valvula) / Exportar informe PDF o HTML.

Capturas en [capturas/](capturas/).

## Compilar el ejecutable

* Windows: doble clic en `compilar_windows.bat` (requiere Python 3.11 o posterior). Resultado:
  `dist\Dimensionador\Dimensionador.exe`.
* macOS / Linux: `./compilar.sh`.
* Automático: subir esta carpeta a un repositorio de GitHub; el flujo
  `.github/workflows/compilar.yml` genera los tres ejecutables.
* `Dimensionador --prueba` verifica el ejecutable con el ejemplo 1 de IEC 60534-2-1.
