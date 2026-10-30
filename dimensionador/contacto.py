"""Datos de contacto de la barra de herramientas del encabezado.

Todos los destinos están acá, en un solo lugar: para cambiar el WhatsApp, la página o el perfil de
LinkedIn alcanza con editar estas constantes y compilar una versión nueva.
"""
from __future__ import annotations

from urllib.parse import quote

from . import __version__

WHATSAPP = "5493513213210"           # formato internacional, sin «+» ni espacios
LINKEDIN = "https://www.linkedin.com/company/instrumatiksite/"
WEB = "https://instrumatik.com.ar"

# WhatsApp no permite bloquear el texto: el enlace lo deja escrito y el usuario puede cambiarlo.
# El código «N25-…» al final identifica que la consulta salió del programa.
MENSAJE_WHATSAPP = ("Hola INSTRUMATIK, les escribo desde N25 Valves Sizing para hacer una consulta. "
                    "[Código N25-{version}]")


def mensaje_whatsapp(version: str = __version__) -> str:
    return MENSAJE_WHATSAPP.format(version=version)


def url_whatsapp(version: str = __version__) -> str:
    return f"https://wa.me/{WHATSAPP}?text={quote(mensaje_whatsapp(version))}"


# (clave, texto del globo de ayuda, url): en el orden en que aparecen los botones
DESTINOS = (
    ("whatsapp", "Contacto por WhatsApp", url_whatsapp),
    ("linkedin", "INSTRUMATIK en LinkedIn", lambda: LINKEDIN),
    ("web", "Página web de INSTRUMATIK", lambda: WEB),
)
