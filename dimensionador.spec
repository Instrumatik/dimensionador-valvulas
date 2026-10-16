# -*- mode: python ; coding: utf-8 -*-
# Empaquetado con PyInstaller:  pyinstaller dimensionador.spec
# Genera dist/Dimensionador/ (Windows: Dimensionador.exe; macOS: Dimensionador.app; Linux: binario)
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

# CoolProp tiene módulos compilados y bibliotecas propias: se incluyen completos
cp_datas, cp_binarios, cp_hidden = collect_all("CoolProp")
hidden = cp_hidden
binarios = cp_binarios

# En Windows la rueda de CoolProp trae su runtime (msvcp140-*.dll) en la carpeta
# hermana «coolprop.libs», que collect_all no incluye.
import glob, os, CoolProp
_libs = os.path.join(os.path.dirname(os.path.dirname(CoolProp.__file__)), "coolprop.libs")
binarios += [(f, "coolprop.libs") for f in glob.glob(os.path.join(_libs, "*"))]

a = Analysis(
    ["lanzador.py"],
    pathex=["."],
    binaries=binarios,
    datas=[("LICENCIAS_TERCEROS.md", "."), *cp_datas, *collect_data_files("docx")],
    hiddenimports=hidden,
    excludes=["tkinter", "matplotlib", "scipy", "pandas", "PySide6.QtWebEngineCore",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Valveselect-N25",
          console=False, icon=None)
coll = COLLECT(exe, a.binaries, a.datas, name="Valveselect-N25")
if sys.platform == "darwin":
    app = BUNDLE(coll, name="Valveselect-N25.app", bundle_identifier="com.instrumatik.valveselect")
