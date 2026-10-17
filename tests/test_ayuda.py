from dimensionador import ayuda
from dimensionador.ayuda_guia import GUIA

CAMPOS = {"que_es", "que_hace", "que_indica", "umbrales", "por_debajo", "por_encima", "afecta",
          "recomendaciones", "ejemplo"}


def test_cada_tema_tiene_guia_completa():
    assert set(GUIA) == set(ayuda.A)
    for clave, g in GUIA.items():
        assert set(g) == CAMPOS, clave
        assert all(g[c] for c in CAMPOS), clave
        assert isinstance(g["afecta"], list) and isinstance(g["recomendaciones"], list), clave


def test_html_muestra_guia_y_fundamento():
    h = ayuda.html("xT")
    for t in ("GUÍA PARA APRENDER", "Valores umbrales", "Por debajo", "Ejemplo", "Fundamento técnico"):
        assert t in h
