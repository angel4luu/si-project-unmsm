"""
Pruebas Unitarias para el Módulo de Lógica Difusa.
"""

import os
import json
import math
import unittest
from modules.fuzzy_module import evaluar_destino_difuso, calcular_scores_todos_destinos


class TestFuzzyModule(unittest.TestCase):

    def test_evaluar_destino_difuso_rango(self):
        """Valida que el score difuso siempre esté dentro del rango [0.0, 10.0]."""
        score = evaluar_destino_difuso(saturacion=0.15, seguridad=8.0, clima=9.0, accesibilidad=7.0)
        self.assertTrue(0.0 <= score <= 10.0)
        self.assertFalse(math.isnan(score))

    def test_evaluar_destino_difuso_condicion_ideal(self):
        """Valida que condiciones óptimas (baja saturación, seguro, garúa, fácil) arrojen un score alto."""
        score_ideal = evaluar_destino_difuso(saturacion=0.10, seguridad=9.0, clima=9.5, accesibilidad=8.5)
        self.assertGreaterEqual(score_ideal, 6.5)

    def test_evaluar_destino_difuso_condicion_critica(self):
        """Valida que condiciones desfavorables (alta saturación, riesgoso, seco, difícil) arrojen un score bajo."""
        score_critico = evaluar_destino_difuso(saturacion=0.90, seguridad=1.5, clima=2.0, accesibilidad=2.0)
        self.assertLessEqual(score_critico, 4.5)

    def test_calcular_scores_todos_destinos(self):
        """Valida que el catálogo de 15 destinos se procese íntegro sin errores."""
        ruta_json = os.path.join(os.path.dirname(__file__), "..", "data", "destinos.json")
        with open(ruta_json, "r", encoding="utf-8") as f:
            destinos = json.load(f)

        scores = calcular_scores_todos_destinos(destinos)
        self.assertEqual(len(scores), 15)
        for d in destinos:
            did = d['id']
            self.assertIn(did, scores)
            self.assertTrue(0.0 <= scores[did] <= 10.0)


if __name__ == "__main__":
    unittest.main()
