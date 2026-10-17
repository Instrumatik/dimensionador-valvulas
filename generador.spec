# -*- mode: python ; coding: utf-8 -*-
# Generador de códigos de licencia (uso interno de INSTRUMATIK; no se distribuye con el programa)
a = Analysis(["generador_codigos.py"], pathex=["."],
             excludes=["tkinter", "matplotlib", "scipy", "pandas", "CoolProp", "docx",
                       "PySide6.QtWebEngineCore", "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml"])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Generador-codigos-Valveselect", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="Generador-codigos-Valveselect")
