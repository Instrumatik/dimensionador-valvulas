"""Gráfico de Cv en función de la apertura (imagen PNG dibujada con Qt).

Se dibuja con QPainter para no agregar dependencias: la misma imagen se usa
en la vista previa, en la impresión y en los documentos Word.
"""
from __future__ import annotations

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen

from .entregables import fmt
from .proyecto import Resultado
from .tuberias import texto_nps

COLORES_CASO = ["#2f6fb0", "#2e7d32", "#c0392b", "#7d1f9e"]


def imagen_cv(res: Resultado, ancho: int = 1400, alto: int = 800) -> QImage:
    img = QImage(ancho, alto, QImage.Format_ARGB32)
    img.fill(QColor("white"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    f = QFont("Arial")
    f.setPixelSize(22)
    p.setFont(f)
    izq, der, arr, aba = 120, 40, 70, 100
    w, h = ancho - izq - der, alto - arr - aba
    cv_max = max([c for _, c in res.curva] + [x["Cv"] for x in res.salidas]) * 1.1
    paso = _paso(cv_max)
    cv_max = paso * (int(cv_max / paso) + 1)

    def X(pct):
        return izq + w * pct / 100

    def Y(cv):
        return arr + h * (1 - cv / cv_max)

    # Cuadrícula y ejes
    p.setPen(QPen(QColor("#d5dbe1"), 1))
    for pct in range(0, 101, 10):
        p.drawLine(QPointF(X(pct), arr), QPointF(X(pct), arr + h))
    v = 0.0
    while v <= cv_max + 1e-9:
        p.drawLine(QPointF(izq, Y(v)), QPointF(izq + w, Y(v)))
        v += paso
    p.setPen(QPen(QColor("#1d2733"), 2))
    p.drawRect(QRectF(izq, arr, w, h))
    p.setPen(QColor("#1d2733"))
    for pct in range(0, 101, 10):
        p.drawText(QRectF(X(pct) - 40, arr + h + 8, 80, 30), Qt.AlignCenter, f"{pct}")
    v = 0.0
    while v <= cv_max + 1e-9:
        p.drawText(QRectF(0, Y(v) - 15, izq - 12, 30), Qt.AlignRight | Qt.AlignVCenter, fmt(v, 3))
        v += paso
    p.drawText(QRectF(izq, alto - 45, w, 35), Qt.AlignCenter, "Apertura de la válvula [%]")
    p.save()
    p.translate(30, arr + h / 2)
    p.rotate(-90)
    p.drawText(QRectF(-h / 2, -20, h, 40), Qt.AlignCenter, "Cv")
    p.restore()
    fb = QFont(f)
    fb.setBold(True)
    fb.setPixelSize(26)
    p.setFont(fb)
    p.drawText(QRectF(izq, 15, w, 40), Qt.AlignLeft | Qt.AlignVCenter,
               f"Cv vs. apertura — válvula {texto_nps(res.nps_valvula)} (Cv nominal {fmt(res.Cv_nominal)})")
    p.setFont(f)

    # Curva inherente
    camino = QPainterPath()
    for k, (pct, cv) in enumerate(res.curva):
        pt = QPointF(X(pct), Y(cv))
        camino.moveTo(pt) if k == 0 else camino.lineTo(pt)
    p.setPen(QPen(QColor("#0d3b66"), 4))
    p.drawPath(camino)

    # Puntos de operación
    y_leyenda = arr + 15
    for k, (rc, s) in enumerate(zip(res.informe.casos, res.salidas)):
        col = QColor(COLORES_CASO[k % len(COLORES_CASO)])
        pct = min(s["apertura"], 1.0) * 100
        x, y = X(pct), Y(s["Cv"])
        p.setPen(QPen(col, 2, Qt.DashLine))
        p.drawLine(QPointF(x, arr + h), QPointF(x, y))
        p.drawLine(QPointF(izq, y), QPointF(x, y))
        p.setPen(QPen(col, 2))
        p.setBrush(col)
        p.drawEllipse(QPointF(x, y), 9, 9)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(izq + 25, y_leyenda + 12), 8, 8)
        p.setPen(QColor("#1d2733"))
        p.drawText(QRectF(izq + 42, y_leyenda, 520, 26), Qt.AlignLeft | Qt.AlignVCenter,
                   f"{rc.caso.nombre}: Cv {fmt(s['Cv'])} a {fmt(s['apertura'] * 100, 3)} %")
        y_leyenda += 32
    p.end()
    return img


def _paso(maximo: float) -> float:
    import math
    bruto = maximo / 8
    e = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * e:
            return m * e
    return 10 * e


def png_cv(res: Resultado) -> bytes:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    imagen_cv(res).save(buf, "PNG")
    buf.close()
    return bytes(ba)
