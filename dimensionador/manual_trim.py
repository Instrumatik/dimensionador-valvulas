"""Manual de selección de trim en PDF, con un capítulo inicial para el cálculo actual."""
from __future__ import annotations

import html as _html
import math
from datetime import date

from . import __version__, entregables as E, seleccion_trim as ST
from .manual_trim_texto import CAPITULOS

TITULO = "Manual técnico de selección de trim"
_AZUL, _CLARO, _ENC = "#0d3b66", "#eef2f6", "#dde5ee"


def _valor(pr, v, magnitud) -> str:
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "—"
    if magnitud == "dB(A)":
        return f"{E.fmt(v, 4)} dB(A)"
    if magnitud:
        return pr.vu(v, magnitud, 4)
    return E.fmt(v, 3)


def _nota(texto: str) -> str:
    return (f"<table width='100%' cellpadding='8' cellspacing='0'><tr><td bgcolor='{_CLARO}'>{texto}</td></tr>"
            "</table>")


def html_seleccion(res, pr) -> str:
    """Capítulo con la selección de trim para el cálculo actual."""
    e = _html.escape
    sel = ST.seleccionar(res)
    h = ["<h2>Parte A · Selección de trim para su válvula</h2>",
         f"<p><b>Tag:</b> {e(res.ident.tag or '—')} · <b>Servicio:</b> {e(res.ident.servicio or '—')} · "
         f"<b>Válvula:</b> {e(E._valvula_resumen(res))}</p>",
         _nota(f"<b>Trim recomendado:</b> {e(sel.trim)}<br><b>Materiales:</b> {e(sel.materiales)}")]
    casos = sel.casos
    etiquetas = [d[0] for d in casos[0].datos]
    filas = ["<tr><th align='left'>Dato</th>" + "".join(f"<th>{e(c.caso)}</th>" for c in casos) + "</tr>"]
    for i, et in enumerate(etiquetas):
        filas.append(f"<tr><td>{e(et)}</td>" + "".join(
            f"<td align='right'>{e(_valor(pr, c.datos[i][1], c.datos[i][2]))}</td>" for c in casos) + "</tr>")
    filas.append("<tr><td><b>Trim para el caso</b></td>" + "".join(
        f"<td>{e(c.trim)}{f' ({c.etapas} etapas)' if c.etapas > 1 else ''}</td>" for c in casos) + "</tr>")
    h.append("<h3>Datos del cálculo por caso</h3><table border='1' cellpadding='4' cellspacing='0' width='100%'>"
             + "".join(filas).replace("<th", f"<th bgcolor='{_ENC}'") + "</table>")
    h.append("<h3>Razonamiento paso a paso</h3><ol>" + "".join(f"<li>{e(p)}</li>" for p in sel.pasos) + "</ol>")
    if sel.complementos:
        h.append("<h3>Puntos a resolver con el fabricante o en la instalación</h3><ul>"
                 + "".join(f"<li>{e(a)}</li>" for a in sel.complementos) + "</ul>")
    h.append(_nota("Esta selección es orientativa: se basa en los factores típicos (FL, Kc, Fd, xT) del programa y "
                   "en criterios conservadores de práctica de la industria explicados en la Parte B. La selección "
                   "final debe confirmarse con los valores certificados del trim ofertado por el fabricante."))
    return "".join(h)


def html_documento(res=None, pr=None) -> str:
    e = _html.escape
    partes = [f"<p style='font-size:9pt;color:#5b6b7d'>{E.EMPRESA} · {E.PRODUCTO} · versión {__version__}</p>",
              f"<h1 style='color:{_AZUL}'>{TITULO}</h1>",
              "<p>Cómo elegir el trim correcto (estándar, jaula, multiorificio, multietapa, bajo ruido) a partir "
              "de los resultados del programa, para evitar daños y asegurar la vida útil de la válvula.</p>",
              f"<p style='color:#5b6b7d'>Emitido el {date.today():%d/%m/%Y}</p>"]
    if E.MARCA_AGUA:
        partes.append(f"<p align='center' style='color:#c0392b;font-weight:bold'>{e(E.MARCA_AGUA)}</p>")
    partes.append("<h3>Contenido</h3><ul>" + ("<li>Parte A · Selección de trim para su válvula</li>" if res else "")
                  + "".join(f"<li>{e(c['titulo'])}</li>" for c in CAPITULOS) + "</ul>")
    if res is not None:
        partes.append(f"<div style='page-break-before:always'>{html_seleccion(res, pr)}</div>")
    partes.append("<div style='page-break-before:always'><h2>Parte B · Manual</h2></div>" if res else "")
    for i, c in enumerate(CAPITULOS):
        salto = "page-break-before:always" if i or res is None else ""
        partes.append(f"<div style='{salto}'><h2 style='color:{_AZUL}'>{e(c['titulo'])}</h2>{c['html']}</div>")
    css = E.CSS + (f" h2{{color:{_AZUL}}} h3{{color:#3d5a80}} h4{{color:#3d5a80}} td,th{{font-size:9pt}}"
                   f" th{{background:{_ENC};color:#1b2a3a}}")
    return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(partes)}</body></html>"


def exportar_pdf(ruta: str, res=None, pr=None):
    """Escribe el manual (y la selección del cálculo actual, si se pasa) en un PDF A4."""
    from PySide6.QtCore import QMarginsF
    from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
    from PySide6.QtPrintSupport import QPrinter
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(ruta)
    printer.setPageLayout(QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(18, 16, 18, 16),
                                      QPageLayout.Millimeter))
    printer.setDocName(TITULO)
    doc = QTextDocument()
    doc.setHtml(html_documento(res, pr))
    doc.print_(printer)
