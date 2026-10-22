"""Buscador del encabezado: encuentra datos, opciones de las listas y temas de ayuda.

Los resultados se muestran en una ventanita desplegable bajo la barra. Al elegir uno se va a la
solapa del dato (o de la opción) y se muestra su explicación en el panel de la derecha; un tema de
ayuda se abre directamente en el panel.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from PySide6.QtCore import QStringListModel, Qt, QTimer
from PySide6.QtWidgets import (QAbstractButton, QComboBox, QCompleter, QGridLayout, QGroupBox, QLabel,
                               QLineEdit, QScrollArea, QTableWidget, QWidget)

from .. import ayuda

MAX_RESULTADOS = 25


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para que «cavitacion» encuentre «cavitación»."""
    t = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in t if unicodedata.category(c) != "Mn").lower()


def _plano(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or ""))


@dataclass
class Resultado:
    texto: str            # lo que se ve en la lista
    orden: int            # menor = más relevante
    pagina: int = -1      # solapa a la que hay que ir (-1: ninguna)
    widget: QWidget | None = None
    clave: str = ""       # tema de ayuda a mostrar
    opcion: str = ""      # opción de la lista a señalar
    fila: int = -1        # fila de la tabla a seleccionar


def _etiqueta_fila(grid: QGridLayout, r: int) -> tuple[QLabel | None, QWidget | None]:
    lbl, destino = None, None
    for c in range(grid.columnCount()):
        it = grid.itemAtPosition(r, c)
        w = it.widget() if it is not None else None
        if w is None:
            continue
        if lbl is None and isinstance(w, QLabel) and c == 0:
            lbl = w
        elif destino is None and not isinstance(w, (QLabel, QAbstractButton)):
            destino = w
    return lbl, destino


class Buscador(QLineEdit):
    def __init__(self, ventana):
        super().__init__()
        self.v = ventana
        self.resultados: list[Resultado] = []
        self.setPlaceholderText("Buscar dato, opción o tema…")
        self.setClearButtonEnabled(True)
        self.setFixedWidth(230)
        self.setToolTip("Escriba al menos 2 letras: se listan los datos, las opciones de las listas y "
                        "los temas de ayuda que coinciden. Elija uno para ir a él.")
        self.setStyleSheet("QLineEdit{border:1px solid #9fb9d6;border-radius:4px;padding:3px 6px;"
                           "background:white;color:#1f3550}")
        self.modelo = QStringListModel(self)
        self.comp = QCompleter(self.modelo, self)
        self.comp.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.comp.setCaseSensitivity(Qt.CaseInsensitive)
        self.comp.setMaxVisibleItems(12)
        self.comp.setWidget(self)
        self.comp.activated[str].connect(self._elegido)
        self.comp.popup().setMinimumWidth(460)
        self.textEdited.connect(self._buscar)
        self.returnPressed.connect(self._primero)

    # ------------------------------------------------------------------ búsqueda
    def buscar(self, texto: str) -> list[Resultado]:
        q = normalizar(texto.strip())
        if len(q) < 2:
            return []
        palabras = q.split()

        def coincide(t: str) -> bool:
            n = normalizar(t)
            return all(p in n for p in palabras)

        res: list[Resultado] = []
        vistos: set[int] = set()
        tabs = self.v.tabs
        for i in range(tabs.count()):
            pagina = tabs.widget(i)
            nombre = tabs.tabText(i)
            if not hasattr(pagina, "findChildren"):
                continue
            for g in pagina.findChildren(QGroupBox):
                if g.title() and g.isVisibleTo(pagina) and coincide(g.title()):
                    res.append(Resultado(f"Sección · {nombre} · {g.title()}", 1, i, g))
            for grid in pagina.findChildren(QGridLayout):
                for r in range(grid.rowCount()):
                    lbl, w = _etiqueta_fila(grid, r)
                    if lbl is None or not lbl.isVisibleTo(pagina):
                        continue
                    texto_lbl = _plano(lbl.text()).strip()
                    if texto_lbl and coincide(texto_lbl):
                        destino = w or lbl
                        vistos.add(id(destino))
                        clave = (w.property("ayuda") if w is not None else "") or ""
                        res.append(Resultado(f"Dato · {nombre} · {texto_lbl}", 0, i, destino, clave))
            for cb in pagina.findChildren(QComboBox):
                if not cb.isVisibleTo(pagina):
                    continue
                for k in range(cb.count()):
                    op = cb.itemText(k)
                    item = cb.model().item(k) if hasattr(cb.model(), "item") else None
                    if op and coincide(op) and (item is None or item.isEnabled()):
                        res.append(Resultado(f"Opción · {nombre} · {op}", 2, i, cb,
                                             cb.property("ayuda") or "", op))
            for t in pagina.findChildren(QTableWidget):
                if not t.isVisibleTo(pagina):
                    continue
                for f in range(t.rowCount()):
                    it = t.item(f, 0)
                    if it is not None and it.text() and coincide(it.text()):
                        res.append(Resultado(f"Fila · {nombre} · {it.text()}", 1, i, t,
                                             t.property("ayuda") or "", fila=f))
        for clave, e in ayuda.A.items():
            if coincide(e.titulo):
                res.append(Resultado(f"Ayuda · {e.titulo}", 1, clave=clave))
            elif coincide(_plano(e.texto)):
                res.append(Resultado(f"Ayuda (texto) · {e.titulo}", 3, clave=clave))
        res.sort(key=lambda r: r.orden)
        unicos, textos = [], set()
        for r in res:
            if r.texto not in textos:
                textos.add(r.texto)
                unicos.append(r)
        return unicos[:MAX_RESULTADOS]

    def _buscar(self, texto: str):
        self.resultados = self.buscar(texto)
        if not self.resultados:
            self.modelo.setStringList(["Sin coincidencias"] if len(texto.strip()) >= 2 else [])
            if len(texto.strip()) < 2:
                self.comp.popup().hide()
                return
        else:
            self.modelo.setStringList([r.texto for r in self.resultados])
        self.comp.complete()

    def _primero(self):
        if self.resultados:
            self.ir(self.resultados[0])

    def _elegido(self, texto: str):
        for r in self.resultados:
            if r.texto == texto:
                self.ir(r)
                break
        # El completador escribe el texto elegido en la barra; se deja lo que había escrito
        QTimer.singleShot(0, self.selectAll)

    # ------------------------------------------------------------------ ir al resultado
    def ir(self, r: Resultado):
        if r.pagina >= 0:
            self.v.tabs.setCurrentIndex(r.pagina)
        w = r.widget
        if w is not None:
            p = w.parentWidget()
            while p is not None:
                if isinstance(p, QScrollArea):
                    p.ensureWidgetVisible(w, 50, 80)
                    break
                p = p.parentWidget()
            # Se difiere: el completador devuelve el foco a la barra al cerrarse
            QTimer.singleShot(0, lambda: self._enfocar(w, r))
        if r.clave:
            self.v.abrir_ayuda(r.clave)

    def _enfocar(self, w: QWidget, r: Resultado):
        w.setFocus()
        if isinstance(w, QTableWidget) and r.fila >= 0:
            w.selectRow(r.fila)
            w.scrollToItem(w.item(r.fila, 0))
        elif r.opcion and isinstance(w, QComboBox):
            w.showPopup()
            k = w.findText(r.opcion)
            if k >= 0:
                w.view().setCurrentIndex(w.model().index(k, 0))
        else:
            self._resaltar(w)

    @staticmethod
    def _resaltar(w: QWidget):
        previo = w.styleSheet()
        w.setStyleSheet(previo + f"\n{w.metaObject().className()}{{background:#fff3b0}}")
        QTimer.singleShot(1500, lambda: w.setStyleSheet(previo))
