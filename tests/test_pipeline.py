"""
Prueba de Integración End-to-End del Pipeline Completo.
"""

import unittest
from modules.mapping import dias_a_k
from modules.llm_module import extraer_preferencias_usuario, generar_itinerario_narrativo
from main import ejecutar_pipeline


class TestPipeline(unittest.TestCase):

    def test_mapping_dias_a_k(self):
        """Valida la función de mapeo determinista."""
        self.assertEqual(dias_a_k(0), 1)
        self.assertEqual(dias_a_k(1), 1)
        self.assertEqual(dias_a_k(3), 1)
        self.assertEqual(dias_a_k(4), 1)
        self.assertEqual(dias_a_k(5), 2)
        self.assertEqual(dias_a_k(8), 2)
        self.assertEqual(dias_a_k(12), 3)
        self.assertEqual(dias_a_k(16), 4)
        self.assertEqual(dias_a_k(30), 8)  # Cota máxima K=8
        self.assertEqual(dias_a_k(100), 8)

    def test_llm_extractor_preferencias(self):
        """Valida la extracción de entidades desde texto libre."""
        texto = "Quiero viajar 4 días con 80 soles a lugares fáciles con garúa y vistas"
        perfil = extraer_preferencias_usuario(texto)

        self.assertIn("dias_disponibles", perfil)
        self.assertEqual(perfil["dias_disponibles"], 4)
        self.assertEqual(perfil["presupuesto_max"], 80.0)
        self.assertEqual(perfil["condicion_fisica"], "Fácil")
        self.assertEqual(perfil["clima_preferido"], "Garúa")

    def test_pipeline_completo_end_to_end(self):
        """Valida la ejecución del pipeline coordinado de principio a fin sin excepciones."""
        texto_entrada = "Quiero hacer trekking 2 días con 40 soles en senderos tranquilos"
        salida = ejecutar_pipeline(texto_entrada, verbose=False)

        self.assertIn("perfil", salida)
        self.assertIn("k", salida)
        self.assertTrue(salida["k"] in (1, 2))
        self.assertIn("scores_difusos", salida)
        self.assertEqual(len(salida["scores_difusos"]), 15)
        self.assertIn("resultado_ag", salida)
        self.assertEqual(len(salida["resultado_ag"]["ruta_ids"]), salida["k"])
        self.assertIn("itinerario", salida)
        self.assertGreater(len(salida["itinerario"]), 50)
        self.assertIn("guias_transporte", salida)


if __name__ == "__main__":
    unittest.main()
