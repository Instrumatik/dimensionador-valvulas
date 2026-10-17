"""Códigos de licencia firmados: autenticidad, vencimiento, reloj atrasado y marca de agua."""
from datetime import date, timedelta

import pytest

from dimensionador import licencia as L


@pytest.fixture
def claves():
    k, _ = L.nueva_clave()
    return k, k.public_key()


def _lic(tipo="demo", dias=30, nombre="Juan Pérez", emision=date(2026, 10, 17)):
    return L.Licencia(tipo, nombre, "Ingeniería SRL", "contacto@ejemplo.com", emision,
                      None if dias is None else emision + timedelta(days=dias), 123456)


def test_ida_y_vuelta_y_formato(claves):
    k, pub = claves
    codigo = L.firmar(_lic(), k)
    assert codigo.startswith("VS1-") and len(codigo) < 260
    lic = L.leer(codigo.lower().replace("-", " "), pub)   # tolera minúsculas y separadores
    assert (lic.nombre, lic.empresa, lic.vence, lic.tipo) == ("Juan Pérez", "Ingeniería SRL", date(2026, 11, 16), "demo")
    assert "DEMO – Juan Pérez" in lic.marca_agua


def test_codigo_alterado_o_de_otra_clave(claves):
    k, pub = claves
    codigo = L.firmar(_lic(), k)
    i = codigo.index("-", 5) + 1
    alterado = codigo[:i] + ("A" if codigo[i] != "A" else "B") + codigo[i + 1:]
    with pytest.raises(L.CodigoInvalido):
        L.leer(alterado, pub)
    otra, _ = L.nueva_clave()
    with pytest.raises(L.CodigoInvalido):
        L.leer(L.firmar(_lic(), otra), pub)
    with pytest.raises(L.CodigoInvalido):
        L.leer("hola", pub)


def test_vencimiento_y_reloj_atrasado(claves, tmp_path):
    k, pub = claves
    codigo = L.firmar(_lic(), k)
    d = str(tmp_path)
    assert L.activar(codigo, date(2026, 10, 20), d, pub).ok
    assert L.guardada(d)
    assert L.verificar(codigo, date(2026, 11, 16), d, pub).ok          # último día incluido
    v = L.verificar(codigo, date(2026, 11, 17), d, pub)
    assert not v.ok and "venció" in v.motivo
    assert L.activar(codigo, date(2026, 11, 10), d, pub).ok
    v = L.verificar(codigo, date(2026, 10, 25), d, pub)                 # reloj atrasado
    assert not v.ok and "fecha del equipo" in v.motivo
    v = L.verificar(L.firmar(_lic(emision=date(2026, 12, 1)), k), date(2026, 11, 10), str(tmp_path / "x"), pub)
    assert not v.ok


def test_propietaria_sin_vencimiento_ni_marca(claves, tmp_path):
    k, pub = claves
    lic = L.leer(L.firmar(_lic("propietaria", None), k), pub)
    assert lic.vence is None and lic.marca_agua is None
    assert L.verificar(lic.codigo, date(2099, 1, 1), str(tmp_path), pub).ok


def test_clave_publica_del_programa_es_valida():
    assert L._clave_publica() is not None


def test_marca_de_agua_en_documentos(tmp_path):
    import docx
    from dimensionador import entregables as E
    from tests.test_compresible import TRIM, _co2
    from dimensionador.proyecto import Dimensionamiento, Identificacion, Instalacion, calcular
    r = calcular(Identificacion(), Instalacion(nps_entrada=4, nps_salida=4),
                 Dimensionamiento([_co2()], None, TRIM, nps_valvula=4, tipo="gas"))
    pr = E.Presentacion()
    try:
        E.MARCA_AGUA = "DEMO – Juan Pérez – Solo para validación"
        doc = E.memoria(r, pr)
        assert "DEMO – Juan Pérez" in E.a_html(doc)
        ruta = str(tmp_path / "m.docx")
        E.a_docx([doc], ruta)
        d = docx.Document(ruta)
        assert any("DEMO – Juan Pérez" in p.text for p in d.sections[0].header.paragraphs)
    finally:
        E.MARCA_AGUA = None
    assert "DEMO" not in E.a_html(E.memoria(r, pr))


def test_clave_privada_como_archivo_o_texto(claves):
    k, pub = claves
    pem = L.clave_privada_pem(k)
    cuerpo = "".join(pem.decode().splitlines()[1:-1])
    for entrada in (pem, cuerpo, "  " + cuerpo + "\n"):
        assert L.leer(L.firmar(_lic(), L.cargar_clave_privada(entrada)), pub).nombre == "Juan Pérez"
    with pytest.raises(L.CodigoInvalido):
        L.cargar_clave_privada("no es una clave")
