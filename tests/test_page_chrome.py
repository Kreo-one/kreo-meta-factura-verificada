"""Chrome localizado de la pagina demo: idioma ES/EN autodetectado + identidad.

La pagina servida en GET / debe traer:
- toggle de idioma ES/EN con deteccion automatica (navigator.language)
  y preferencia persistida (localStorage),
- diccionario de textos en ambos idiomas,
- favicon inline y marca SVG (cero archivos nuevos, stdlib-only).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402


class LocalizedChromeTest(unittest.TestCase):
    def test_page_ships_i18n_toggle_and_identity(self) -> None:
        page = server.PAGE
        self.assertIn('id="langBtn"', page, "falta el boton ES/EN")
        self.assertIn("navigator.language", page, "falta autodeteccion de idioma")
        self.assertIn("localStorage", page, "la preferencia de idioma debe persistir")
        self.assertIn('"es"', page, "falta diccionario en espanol")
        self.assertIn('"en"', page, "falta diccionario en ingles")
        self.assertIn("Fiscal Shield", page, "falta la marca en ingles")
        self.assertIn('rel="icon"', page, "falta el favicon")
        self.assertIn("<svg", page, "falta la marca SVG inline")


class WizardChromeTest(unittest.TestCase):
    def test_page_ships_guided_steps_semaforo_and_advanced(self) -> None:
        page = server.PAGE
        self.assertIn('id="stepLine"', page, "falta el indicador de paso")
        self.assertIn('"step_of"', page, "falta la etiqueta Paso N de 3")
        self.assertIn('id="verdict-light"', page, "falta la luz del semáforo")
        self.assertIn("<details", page, "la suite debe ir tras un desplegable Avanzado")
        self.assertIn('id="advanced"', page, "falta el bloque Avanzado")
        self.assertIn('"go_word"', page, "falta la palabra llana del verde")
        self.assertIn('"stop_word"', page, "falta la palabra llana del rojo")
        self.assertIn(".primary{", page, "falta el estilo del botón principal")
        self.assertIn('class="primary"', page, "el envío debe ser el botón principal")
        self.assertIn("chatLog", page, "el historial debe re-renderizarse al cambiar idioma")
        self.assertLess(page.index('id="stepLine"'), page.index('id="chat"'), "el paso va arriba del chat")
        self.assertLess(page.index('id="advanced"'), page.index('onclick="sabotage()"'), "sabotaje vive en Avanzado")
        self.assertIn("#059669", page, "falta la esmeralda §5")
        self.assertIn("ui-monospace", page, "falta la pila mono del sistema")


if __name__ == "__main__":
    unittest.main()
