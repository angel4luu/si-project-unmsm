"""
Pruebas Unitarias para el Modulo Heuristico de Algoritmo Genetico.
"""

import os
import json
import unittest
from modules.genetic_algorithm import (
    LomasGeneticOptimizer,
    distancia_haversine,
    optimizar_ruta_lomas
)


class TestGeneticAlgorithm(unittest.TestCase):

    def setUp(self):
        ruta_json = os.path.join(os.path.dirname(__file__), "..", "data", "destinos.json")
        with open(ruta_json, "r", encoding="utf-8") as f:
            self.destinos = json.load(f)
        self.scores = {d["id"]: 7.5 for d in self.destinos}

    def test_distancia_haversine(self):
        """Valida precision, simetria y caso distancia cero de la formula Haversine."""
        # 1. Distancia de un punto a si mismo debe ser exactamente 0.0
        self.assertEqual(distancia_haversine(-12.0, -77.0, -12.0, -77.0), 0.0)

        # 2. Distancia entre dos puntos conocidos en Lima (Miraflores a VMT)
        dist1 = distancia_haversine(-12.1111, -77.0336, -12.1697, -76.9234)
        dist2 = distancia_haversine(-12.1697, -76.9234, -12.1111, -77.0336)
        self.assertTrue(10.0 <= dist1 <= 20.0)
        self.assertAlmostEqual(dist1, dist2, places=4, msg="La distancia debe ser simetrica")

    def test_unicidad_cromosoma_y_tamano_k(self):
        """Valida que la mejor ruta generada tenga exactamente K destinos y ningun duplicado."""
        k = 4
        res = optimizar_ruta_lomas(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=k,
            presupuesto=100.0,
            dias_disponibles=3,
            generaciones=25,
            tam_poblacion=20,
            semilla=42
        )

        ruta = res["ruta_ids"]
        self.assertEqual(len(ruta), k)
        self.assertEqual(len(set(ruta)), k, "El cromosoma no debe contener destinos duplicados")
        self.assertEqual(len(res["destinos_ordenados"]), k)

    def test_crossover_ox_validez(self):
        """Valida que el operador Order Crossover produzca descendientes validos de tamano K sin duplicados."""
        opt = LomasGeneticOptimizer(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=5,
            presupuesto=100.0,
            dias_disponibles=3,
            semilla=10
        )

        padre1 = ["L0", "L1", "L2", "L3", "L4"]
        padre2 = ["L3", "L4", "L5", "L6", "L7"]

        hijo1, hijo2 = opt._crossover_ox(padre1, padre2)

        self.assertEqual(len(hijo1), 5)
        self.assertEqual(len(set(hijo1)), 5, "Hijo 1 no debe tener duplicados")
        self.assertEqual(len(hijo2), 5)
        self.assertEqual(len(set(hijo2)), 5, "Hijo 2 no debe tener duplicados")

    def test_mutaciones_generan_cromosomas_validos(self):
        """Valida que swap, reemplazo e inversion conserven la longitud K y la unicidad."""
        opt = LomasGeneticOptimizer(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=4,
            presupuesto=80.0,
            dias_disponibles=2,
            semilla=99
        )
        individuo = ["L0", "L1", "L2", "L3"]

        # 1. Mutacion Swap
        mut_swap = opt._mutacion_swap(individuo)
        self.assertEqual(len(mut_swap), 4)
        self.assertEqual(len(set(mut_swap)), 4)
        self.assertEqual(set(mut_swap), set(individuo))

        # 2. Mutacion Reemplazo
        mut_rep = opt._mutacion_reemplazo(individuo)
        self.assertEqual(len(mut_rep), 4)
        self.assertEqual(len(set(mut_rep)), 4)

        # 3. Mutacion Inversion (2-Opt)
        mut_inv = opt._mutacion_inversion(individuo)
        self.assertEqual(len(mut_inv), 4)
        self.assertEqual(len(set(mut_inv)), 4)

    def test_penalizacion_presupuesto_en_fitness(self):
        """Valida que un presupuesto insuficiente penalice el valor del fitness cuadraticamente."""
        k = 3
        opt_holgado = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=k,
            presupuesto=200.0, dias_disponibles=3, generaciones=5, tam_poblacion=10
        )
        opt_restringido = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=k,
            presupuesto=1.0, dias_disponibles=3, generaciones=5, tam_poblacion=10
        )

        ruta_test = [self.destinos[0]["id"], self.destinos[1]["id"], self.destinos[2]["id"]]
        fit_holgado = opt_holgado.fitness(ruta_test)
        fit_restringido = opt_restringido.fitness(ruta_test)

        self.assertGreater(fit_holgado, fit_restringido, "El fitness con exceso de presupuesto debe ser penalizado")

    def test_penalizacion_tiempo_en_fitness(self):
        """Valida que una ruta que sobrepase las horas utiles disponibles sea penalizada."""
        k = 3
        opt_mucho_tiempo = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=k,
            presupuesto=200.0, dias_disponibles=5, generaciones=5, tam_poblacion=10
        )
        opt_poco_tiempo = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=k,
            presupuesto=200.0, dias_disponibles=1, generaciones=5, tam_poblacion=10
        )

        ruta_test = [self.destinos[0]["id"], self.destinos[1]["id"], self.destinos[2]["id"]]
        fit_tiempo_ok = opt_mucho_tiempo.fitness(ruta_test)
        fit_tiempo_exceso = opt_poco_tiempo.fitness(ruta_test)

        self.assertGreater(fit_tiempo_ok, fit_tiempo_exceso)

    def test_penalizacion_distancia_en_fitness(self):
        """Valida que una ruta con mayor distancia geografica obtenga menor fitness a igualdad de scores."""
        opt = LomasGeneticOptimizer(
            destinos=self.destinos, scores_difusos=self.scores, k=2,
            presupuesto=200.0, dias_disponibles=3, beta_distancia=2.0
        )
        # L0 (VMT) y L3 (Manchay/Ate) estan cerca (~7.5 km)
        # L0 (VMT) y L6 (Lachay/Huacho) estan muy lejos (>100 km)
        ruta_corta = ["L0", "L3"]
        ruta_larga = ["L0", "L6"]

        self.assertGreater(opt.fitness(ruta_corta), opt.fitness(ruta_larga))

    def test_elitismo_no_regresion_fitness(self):
        """Valida que con elitismo el mejor fitness historico sea monotonicamente no decreciente."""
        opt = LomasGeneticOptimizer(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=3,
            presupuesto=80.0,
            dias_disponibles=3,
            generaciones=30,
            tam_poblacion=30,
            semilla=123
        )
        res = opt.optimizar()
        historial = res["historial"]

        for i in range(len(historial) - 1):
            fit_actual = historial[i]["mejor_fitness"]
            fit_siguiente = historial[i + 1]["mejor_fitness"]
            self.assertGreaterEqual(
                fit_siguiente, fit_actual,
                f"Elitismo violado: Gen {i+1} ({fit_siguiente}) < Gen {i} ({fit_actual})"
            )

    def test_caso_borde_k1(self):
        """Valida el caso borde K=1 (distancia 0 km, un solo destino)."""
        res = optimizar_ruta_lomas(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=1,
            presupuesto=50.0,
            dias_disponibles=1,
            generaciones=10,
            tam_poblacion=15
        )
        self.assertEqual(len(res["ruta_ids"]), 1)
        self.assertEqual(res["distancia_total_km"], 0.0)
        self.assertEqual(len(res["tramos"]), 0)

    def test_reproducibilidad_con_semilla(self):
        """Valida que fijar la semilla genere exactamente el mismo resultado."""
        res1 = optimizar_ruta_lomas(
            destinos=self.destinos, scores_difusos=self.scores, k=3,
            presupuesto=60.0, dias_disponibles=2, generaciones=20, tam_poblacion=20, semilla=777
        )
        res2 = optimizar_ruta_lomas(
            destinos=self.destinos, scores_difusos=self.scores, k=3,
            presupuesto=60.0, dias_disponibles=2, generaciones=20, tam_poblacion=20, semilla=777
        )
        self.assertEqual(res1["ruta_ids"], res2["ruta_ids"])
        self.assertEqual(res1["fitness"], res2["fitness"])


if __name__ == "__main__":
    unittest.main()
