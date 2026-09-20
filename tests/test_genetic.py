"""
Pruebas Unitarias para el Algoritmo Genético.
"""

import os
import json
import unittest
from modules.genetic_algorithm import LomasGeneticOptimizer, distancia_haversine, optimizar_ruta_lomas


class TestGeneticAlgorithm(unittest.TestCase):

    def setUp(self):
        ruta_json = os.path.join(os.path.dirname(__file__), "..", "data", "destinos.json")
        with open(ruta_json, "r", encoding="utf-8") as f:
            self.destinos = json.load(f)
        self.scores = {d['id']: 7.5 for d in self.destinos}

    def test_distancia_haversine(self):
        """Valida el cálculo de distancia Haversine entre dos puntos conocidos en Lima."""
        dist = distancia_haversine(-12.1111, -77.0336, -12.1697, -76.9234)
        self.assertTrue(10.0 <= dist <= 20.0)

    def test_unicidad_cromosoma_y_tamano_k(self):
        """Valida que la mejor ruta generada tenga exactamente K destinos y ningún duplicado."""
        k = 4
        res = optimizar_ruta_lomas(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=k,
            presupuesto=100.0,
            dias_disponibles=3,
            generaciones=30,
            tam_poblacion=20
        )

        ruta = res['ruta_ids']
        self.assertEqual(len(ruta), k)
        self.assertEqual(len(set(ruta)), k, "El cromosoma no debe contener destinos duplicados")

    def test_penalizacion_presupuesto_en_fitness(self):
        """Valida que un presupuesto insuficiente penalice el valor del fitness."""
        k = 3
        opt_holgado = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=k,
            presupuesto=200.0, dias_disponibles=3, generaciones=10, tam_poblacion=10
        )
        opt_restringido = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=k,
            presupuesto=1.0, dias_disponibles=3, generaciones=10, tam_poblacion=10
        )

        ruta_test = [self.destinos[0]['id'], self.destinos[1]['id'], self.destinos[2]['id']]
        fit_holgado = opt_holgado.fitness(ruta_test)
        fit_restringido = opt_restringido.fitness(ruta_test)

        self.assertGreater(fit_holgado, fit_restringido, "El fitness con exceso de presupuesto debe ser severamente penalizado")


if __name__ == "__main__":
    unittest.main()
