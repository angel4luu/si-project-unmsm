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
            dias_disponibles=4,
            generaciones=25,
            tam_poblacion=20,
            semilla=42
        )

        ruta = res["ruta_ids"]
        self.assertEqual(len(ruta), k)
        self.assertEqual(len(set(ruta)), k, "El fenotipo activo no debe contener destinos duplicados")
        self.assertEqual(len(res["destinos_ordenados"]), k)
        # Validar que el genotipo completo tenga los 15 alelos
        self.assertEqual(len(res["cromosoma_completo"]), 15)
        self.assertEqual(len(set(res["cromosoma_completo"])), 15)

    def test_crossover_ox_validez(self):
        """Valida que el operador Order Crossover produzca descendientes de 15 alelos sin duplicados."""
        opt = LomasGeneticOptimizer(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=3,
            presupuesto=100.0,
            dias_disponibles=3,
            semilla=10
        )

        padre1 = opt._generar_individuo()
        padre2 = opt._generar_individuo()

        hijo1, hijo2 = opt._crossover_ox(padre1, padre2)

        self.assertEqual(len(hijo1), 15)
        self.assertEqual(len(set(hijo1)), 15, "Hijo 1 debe ser una permutacion de 15 elementos")
        self.assertEqual(len(hijo2), 15)
        self.assertEqual(len(set(hijo2)), 15, "Hijo 2 debe ser una permutacion de 15 elementos")

    def test_mutaciones_generan_cromosomas_validos(self):
        """Valida que la mutacion conserve los 15 alelos y la unicidad en la ventana activa."""
        opt = LomasGeneticOptimizer(
            destinos=self.destinos,
            scores_difusos=self.scores,
            k=3,
            presupuesto=80.0,
            dias_disponibles=3,
            prob_mutacion=1.0,
            semilla=99
        )
        individuo = opt._generar_individuo()
        mutado = opt._mutar(individuo)

        self.assertEqual(len(mutado), 15)
        self.assertEqual(len(set(mutado)), 15, "El cromosoma mutado debe conservar los 15 alelos")
        ruta_activa = opt.obtener_ruta_activa(mutado)
        self.assertEqual(len(ruta_activa), 3)
        self.assertEqual(len(set(ruta_activa)), 3)

    def test_penalizacion_relativa_presupuesto_en_fitness(self):
        """Valida que un presupuesto insuficiente penalice el valor del fitness de forma relativa."""
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

    def test_penalizacion_relativa_tiempo_en_fitness(self):
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

    def test_atajo_determinista_k1(self):
        """Valida el atajo determinista para K=1 (distancia 0 km, un solo destino, metodo atajo)."""
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
        self.assertEqual(res["metodo"], "atajo_determinista")

    def test_reproducibilidad_con_semilla(self):
        """Valida que fijar la semilla genere exactamente el mismo resultado."""
        res1 = optimizar_ruta_lomas(
            destinos=self.destinos, scores_difusos=self.scores, k=3,
            presupuesto=60.0, dias_disponibles=3, generaciones=20, tam_poblacion=20, semilla=777
        )
        res2 = optimizar_ruta_lomas(
            destinos=self.destinos, scores_difusos=self.scores, k=3,
            presupuesto=60.0, dias_disponibles=3, generaciones=20, tam_poblacion=20, semilla=777
        )
        self.assertEqual(res1["ruta_ids"], res2["ruta_ids"])
        self.assertEqual(res1["fitness"], res2["fitness"])


if __name__ == "__main__":
    unittest.main()
