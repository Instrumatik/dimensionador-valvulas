"""Iconos de la barra de herramientas del encabezado: dibujos de línea en SVG, blancos sobre el azul."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_A = ('xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.8" '
      'stroke-linecap="round" stroke-linejoin="round"')

SVG = {
    # flechas en sentidos opuestos
    "conversor": '<path d="M4 8h13l-3-3"/><path d="M20 16H7l3 3"/>',
    # símbolo de válvula de control: dos triángulos, vástago y diafragma
    "cv": '<path d="M3 10v8l9-4z"/><path d="M21 10v8l-9-4z"/><path d="M12 14V7"/><path d="M7.5 7a4.5 3 0 0 1 9 0z"/>',
    # «N» dentro de una tabla
    "constantes": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 16V8l8 8V8"/>',
    # gota con brillo
    "fluidos": '<path d="M12 3c3 4 6 7.5 6 11a6 6 0 0 1-12 0c0-3.5 3-7 6-11z"/><path d="M9 15a3 3 0 0 0 3 3"/>',
    # tramo de caño con dos bridas
    "tuberia": '<rect x="2.5" y="5" width="3.5" height="14" rx="0.8"/><rect x="18" y="5" width="3.5" height="14" rx="0.8"/>'
               '<path d="M6 9h12M6 15h12"/><path d="M4.25 7.5v.01M4.25 16.5v.01M19.75 7.5v.01M19.75 16.5v.01" stroke-width="2.2"/>',
    # manómetro
    "rating": '<path d="M4.5 17a8.5 8.5 0 1 1 15 0"/><path d="M12 13l4-4"/><circle cx="12" cy="13" r="1.3"/><path d="M7 17h10"/>',
    # capas
    "materiales": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 12l9 5 9-5"/><path d="M3 16l9 5 9-5"/>',
    # calculadora
    "calculadoras": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8"/>'
                    '<path d="M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01M8.5 15h.01M12 15h.01M15.5 15h.01M8.5 18h.01M12 18h.01M15.5 18h.01" stroke-width="2.4"/>',
    # marcador de libro (enlaces guardados)
    "enlaces": '<path d="M6 3h12v18l-6-4.5L6 21z"/><path d="M9.5 8h5"/>',
    # globo de diálogo con auricular
    "whatsapp": '<path d="M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.2A8 8 0 1 1 20 11.5z"/>'
                '<path d="M9 9.2c0 3 2.6 5.6 5.6 5.6l1.1-1.4-1.8-.9-.9.8a4 4 0 0 1-2.5-2.5l.8-.9-.9-1.8L9 9.2z" stroke-width="1.2"/>',
    # cuadrado redondeado con «in»
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10.5V17"/><path d="M8 7.3v.01" stroke-width="2.4"/>'
                '<path d="M12 17v-6.5M12 13.5a2.8 2.8 0 0 1 5.5 0V17"/>',
    # globo terráqueo
    "web": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.8 2.6 2.8 15.4 0 18M12 3c-2.8 2.6-2.8 15.4 0 18"/>',
}


def svg(nombre: str, color: str = "white") -> str:
    return f'<svg {_A.format(c=color)}>{SVG[nombre]}</svg>'


def icono(nombre: str, color: str = "white", px: int = 48) -> QIcon:
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    QSvgRenderer(QByteArray(svg(nombre, color).encode())).render(p)
    p.end()
    return QIcon(pm)
