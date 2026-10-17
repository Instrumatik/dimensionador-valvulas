"""Códigos de licencia firmados (Ed25519).

Un código contiene el tipo de licencia (demo, anual o propietaria), las fechas de emisión y de
vencimiento, el nombre del usuario, su empresa y un contacto para comentarios, firmados con la
clave privada de INSTRUMATIK. El programa solo lleva la clave pública: puede verificar un código
pero no fabricarlo. Los códigos se crean con «generador_codigos.py», que usa la clave privada.

Formato: «VS1-» seguido de los bytes (datos + firma de 64 bytes) en base 32, en grupos de 6.
"""
from __future__ import annotations

import base64
import json
import os
import struct
import sys
from dataclasses import dataclass
from datetime import date, timedelta

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

PREFIJO = "VS1"
VERSION = 1
EPOCA = date(2025, 1, 1)
SIN_VENCIMIENTO = 0xFFFF
TIPOS = {"demo": 1, "anual": 2, "propietaria": 3}
NOMBRE_TIPO = {"demo": "Demo de validación", "anual": "Licencia anual", "propietaria": "Licencia propietaria"}
DIAS_TIPO = {"demo": 30, "anual": 365, "propietaria": None}
# Tolerancia para cambios de huso horario al comparar con la última fecha de uso
TOLERANCIA_RELOJ = timedelta(days=1)

# Clave pública de INSTRUMATIK S.A.S. (la privada no forma parte del programa)
CLAVE_PUBLICA = "j0r879xYdK5VfHHCVTZe235d8BTYmFRBSw8Ak14LZWw"

TERMINOS_DEMO = (
    "Esta es una versión de demostración de Valveselect-N25, de INSTRUMATIK S.A.S., entregada "
    "en forma personal para validar el software. Al usarla usted acepta que:\n"
    "• La licencia es personal e intransferible; no puede copiar ni redistribuir el programa ni su código.\n"
    "• Los resultados y documentos generados son solo para validación y no pueden usarse en proyectos, "
    "compras ni documentos comerciales.\n"
    "• El software se entrega «tal cual», sin garantía; las decisiones de ingeniería son responsabilidad "
    "del usuario.\n"
    "• La demo vence en la fecha indicada en su código.\n"
    "• Sus comentarios y observaciones pueden ser usados por INSTRUMATIK para mejorar el producto."
)


class CodigoInvalido(ValueError):
    pass


@dataclass(frozen=True)
class Licencia:
    tipo: str
    nombre: str
    empresa: str
    contacto: str
    emision: date
    vence: date | None
    id: int
    codigo: str = ""

    @property
    def es_demo(self) -> bool:
        return self.tipo == "demo"

    def dias_restantes(self, hoy: date) -> int | None:
        return None if self.vence is None else (self.vence - hoy).days

    def vigente(self, hoy: date) -> bool:
        return self.vence is None or hoy <= self.vence

    @property
    def marca_agua(self) -> str | None:
        if not self.es_demo:
            return None
        return f"DEMO – {self.nombre} – Solo para validación, no válido para uso comercial"

    def descripcion(self) -> str:
        quien = self.nombre + (f" ({self.empresa})" if self.empresa else "")
        hasta = "sin vencimiento" if self.vence is None else f"válida hasta el {self.vence:%d/%m/%Y}"
        return f"{NOMBRE_TIPO[self.tipo]} a nombre de {quien}, {hasta}."


# ---------------------------------------------------------------------------
# Codificación
# ---------------------------------------------------------------------------
def _txt(s: str) -> bytes:
    b = s.strip().encode("utf-8")[:255]
    return bytes([len(b)]) + b


def _datos(lic: Licencia) -> bytes:
    vence = SIN_VENCIMIENTO if lic.vence is None else (lic.vence - EPOCA).days
    return (struct.pack(">BBHHI", VERSION, TIPOS[lic.tipo], (lic.emision - EPOCA).days, vence, lic.id)
            + _txt(lic.nombre) + _txt(lic.empresa) + _txt(lic.contacto))


def _formatear(b: bytes) -> str:
    s = base64.b32encode(b).decode().rstrip("=")
    return PREFIJO + "-" + "-".join(s[i:i + 6] for i in range(0, len(s), 6))


def firmar(lic: Licencia, clave_privada: Ed25519PrivateKey) -> str:
    datos = _datos(lic)
    return _formatear(datos + clave_privada.sign(datos))


def _clave_publica() -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(CLAVE_PUBLICA + "="))


def leer(codigo: str, clave_publica: Ed25519PublicKey | None = None) -> Licencia:
    """Verifica la firma y devuelve la licencia; CodigoInvalido si el código no es auténtico."""
    s = "".join(ch for ch in codigo.upper() if ch.isalnum())
    if not s.startswith(PREFIJO):
        raise CodigoInvalido("El código debe comenzar con «VS1-».")
    s = s[len(PREFIJO):]
    try:
        b = base64.b32decode(s + "=" * (-len(s) % 8))
    except Exception:
        raise CodigoInvalido("El código está incompleto o tiene caracteres inválidos.") from None
    if len(b) < 10 + 3 + 64:
        raise CodigoInvalido("El código está incompleto.")
    datos, firma = b[:-64], b[-64:]
    try:
        (clave_publica or _clave_publica()).verify(firma, datos)
    except InvalidSignature:
        raise CodigoInvalido("El código no es válido: verifique que lo copió completo.") from None
    ver, tipo, emision, vence, ident = struct.unpack(">BBHHI", datos[:10])
    if ver != VERSION:
        raise CodigoInvalido("El código corresponde a otra versión del programa.")
    textos, i = [], 10
    for _ in range(3):
        n = datos[i]
        textos.append(datos[i + 1:i + 1 + n].decode("utf-8"))
        i += 1 + n
    tipo_txt = {v: k for k, v in TIPOS.items()}[tipo]
    return Licencia(tipo_txt, *textos, EPOCA + timedelta(days=emision),
                    None if vence == SIN_VENCIMIENTO else EPOCA + timedelta(days=vence), ident,
                    _formatear(b))


def nueva_clave() -> tuple[Ed25519PrivateKey, str]:
    """Par de claves nuevo: la privada (objeto) y la pública en base64url para CLAVE_PUBLICA."""
    k = Ed25519PrivateKey.generate()
    pub = k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return k, base64.urlsafe_b64encode(pub).decode().rstrip("=")


def clave_privada_pem(k: Ed25519PrivateKey) -> bytes:
    return k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                           serialization.NoEncryption())


def cargar_clave_privada(pem: bytes | str) -> Ed25519PrivateKey:
    """Acepta el archivo .pem completo o solo su texto en base 64 (sin las líneas BEGIN/END)."""
    texto = pem.decode("ascii", "ignore") if isinstance(pem, bytes) else pem
    if "BEGIN" not in texto:
        cuerpo = "".join(texto.split())
        texto = f"-----BEGIN PRIVATE KEY-----\n{cuerpo}\n-----END PRIVATE KEY-----\n"
    try:
        k = serialization.load_pem_private_key(texto.encode("ascii"), None)
    except ValueError:
        raise CodigoInvalido("El texto no corresponde a una clave privada válida.") from None
    if not isinstance(k, Ed25519PrivateKey):
        raise CodigoInvalido("El archivo no contiene una clave Ed25519.")
    return k


# ---------------------------------------------------------------------------
# Estado guardado en el equipo del usuario
# ---------------------------------------------------------------------------
def carpeta_config() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "Valveselect-N25")


def _ruta(carpeta: str | None) -> str:
    return os.path.join(carpeta or carpeta_config(), "licencia.json")


def _leer_estado(carpeta=None) -> dict:
    try:
        with open(_ruta(carpeta), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _guardar_estado(estado: dict, carpeta=None):
    ruta = _ruta(carpeta)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(estado, f)


@dataclass
class Verificacion:
    licencia: Licencia | None
    motivo: str = ""          # vacío si la licencia está vigente

    @property
    def ok(self) -> bool:
        return self.licencia is not None and not self.motivo


def verificar(codigo: str, hoy: date | None = None, carpeta: str | None = None,
              clave_publica: Ed25519PublicKey | None = None) -> Verificacion:
    """Comprueba firma, vencimiento y que el reloj del equipo no haya sido atrasado."""
    hoy = hoy or date.today()
    try:
        lic = leer(codigo, clave_publica)
    except CodigoInvalido as e:
        return Verificacion(None, str(e))
    estado = _leer_estado(carpeta)
    ultimo = estado.get("ultimo_uso")
    try:
        ultimo = date.fromisoformat(ultimo) if ultimo else None
    except ValueError:
        ultimo = None
    if hoy + TOLERANCIA_RELOJ < lic.emision or (ultimo and hoy + TOLERANCIA_RELOJ < ultimo):
        return Verificacion(lic, "La fecha del equipo es anterior a la de un uso previo del programa. "
                                 "Corrija la fecha y la hora del sistema.")
    if not lic.vigente(hoy):
        return Verificacion(lic, f"La {NOMBRE_TIPO[lic.tipo].lower()} venció el {lic.vence:%d/%m/%Y}.")
    return Verificacion(lic)


def activar(codigo: str, hoy: date | None = None, carpeta: str | None = None,
            clave_publica: Ed25519PublicKey | None = None) -> Verificacion:
    """Verifica el código y, si es válido, lo guarda y registra la fecha de uso."""
    v = verificar(codigo, hoy, carpeta, clave_publica)
    if v.ok:
        hoy = hoy or date.today()
        estado = _leer_estado(carpeta)
        ultimo = estado.get("ultimo_uso") or hoy.isoformat()
        estado.update(codigo=v.licencia.codigo, ultimo_uso=max(ultimo, hoy.isoformat()))
        _guardar_estado(estado, carpeta)
    return v


def guardada(carpeta: str | None = None) -> str:
    return _leer_estado(carpeta).get("codigo", "")
