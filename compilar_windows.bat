@echo off
REM Compila Dimensionador.exe en una PC con Windows y Python 3.11 o posterior instalado.
REM Resultado: carpeta dist\Dimensionador con Dimensionador.exe
cd /d "%~dp0"
python -m pip install -r requirements.txt || goto error
python -m pytest -q tests || goto error
python -m PyInstaller --noconfirm dimensionador.spec || goto error
dist\Dimensionador\Dimensionador.exe --prueba || goto error
echo.
echo Listo: dist\Dimensionador\Dimensionador.exe
pause
exit /b 0
:error
echo Hubo un error. Revise los mensajes de arriba.
pause
exit /b 1
