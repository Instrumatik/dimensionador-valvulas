# -*- mode: python ; coding: utf-8 -*-
# Empaquetado con PyInstaller:  pyinstaller dimensionador.spec
# Genera dist/Dimensionador/ (Windows: Dimensionador.exe; macOS: Dimensionador.app; Linux: binario)
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

hidden = collect_submodules("CoolProp")
binarios = collect_dynamic_libs("CoolProp")

a = Analysis(
    ["lanzador.py"],
    pathex=["."],
    binaries=binarios,
    datas=[("LICENCIAS_TERCEROS.md", ".")],
    hiddenimports=hidden,
    excludes=["tkinter", "matplotlib", "scipy", "pandas", "PySide6.QtWebEngineCore",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Dimensionador",
          console=False, icon=None)
coll = COLLECT(exe, a.binaries, a.datas, name="Dimensionador")
if sys.platform == "darwin":
    app = BUNDLE(coll, name="Dimensionador.app", bundle_identifier="ar.dimensionador.valvulas")
