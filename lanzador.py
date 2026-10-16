"""Lanzador para el ejecutable empaquetado."""
import os
import sys

if getattr(sys, "frozen", False):
    # Variables de Qt heredadas de otros programas instalados (Anaconda, QGIS, etc.)
    # pueden apuntar a complementos incompatibles y provocar «no Qt platform plugin
    # could be initialized». Se usan siempre los complementos incluidos en el ejecutable.
    for _var in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "QT_QPA_PLATFORM", "QML2_IMPORT_PATH"):
        os.environ.pop(_var, None)
    _base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    for _plugins in (os.path.join(_base, "PySide6", "plugins"),          # Windows, macOS
                     os.path.join(_base, "PySide6", "Qt", "plugins")):   # Linux
        if os.path.isdir(os.path.join(_plugins, "platforms")):
            break
    else:
        _plugins = None
    if _plugins:
        os.environ["QT_PLUGIN_PATH"] = _plugins
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(_plugins, "platforms")

from dimensionador.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
