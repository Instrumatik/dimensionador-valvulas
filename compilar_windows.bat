@echo off
REM Compila Valveselect-N25.exe en una PC con Windows y Python 3.11 o posterior instalado.
REM Resultado: carpeta dist\Valveselect-N25 con Valveselect-N25.exe
cd /d "%~dp0"
python -m pip install -r requirements.txt || goto error
python -m pytest -q tests || goto error
python -m PyInstaller --noconfirm dimensionador.spec || goto error
dist\Valveselect-N25\Valveselect-N25.exe --prueba || goto error
echo.
echo Listo: dist\Valveselect-N25\Valveselect-N25.exe
pause
exit /b 0
:error
echo Hubo un error. Revise los mensajes de arriba.
pause
exit /b 1
