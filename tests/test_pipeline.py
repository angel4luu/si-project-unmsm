"""
Prueba de Integración End-to-End del Pipeline Completo.
"""

import unittest
from modules.dtos import UserPreferencesDTO, FuzzySemanticPreferencesDTO, CoordenadasDTO
from modules.mapping import LomasMappingService, dias_a_k
from modules.llm_module import extraer_preferencias_usuario, generar_itinerario_narrativo
from main import ejecutar_pipeline


class TestPipeline(unittest.TestCase):

    def test_mapping_dias_a_k(self):
        """Valida la funcion de mapeo determinista urbano."""
        self.assertEqual(dias_a_k(0), 1)
        self.assertEqual(dias_a_k(1), 1)
        self.assertEqual(dias_a_k(2), 2)
        self.assertEqual(dias_a_k(3), 3)
        self.assertEqual(dias_a_k(4), 4)
        self.assertEqual(dias_a_k(5), 5)
        self.assertEqual(dias_a_k(6), 6)
        self.assertEqual(dias_a_k(7), 6)  # Cota maxima K=6
        self.assertEqual(dias_a_k(30), 6)

    def test_mapping_service_pesos_condicion(self):
        """Valida el mapeo de condición física a pesos delta y gamma."""
        delta_f, gamma_f = LomasMappingService.mapear_pesos_condicion("Fácil", 1.0)
        self.assertEqual(delta_f, 1.0)
        self.assertEqual(gamma_f, 2.0)

        delta_d, gamma_d = LomasMappingService.mapear_pesos_condicion("Difícil", 1.2)
        self.assertEqual(delta_d, 3.0)
        self.assertEqual(gamma_d, 1.2)

        delta_m, gamma_m = LomasMappingService.mapear_pesos_condicion("Moderado", 1.0)
        self.assertEqual(delta_m, 2.0)
        self.assertEqual(gamma_m, 1.5)

    def test_mapping_service_restricciones_presupuesto(self):
        """Valida el cálculo de bandas y límites presupuestales."""
        b = LomasMappingService.mapear_restricciones_presupuesto(50.0, 2)
        self.assertEqual(b["presupuesto_total"], 50.0)
        self.assertEqual(b["presupuesto_por_destino"], 25.0)
        self.assertGreaterEqual(b["umbral_minimo_viable"], 16.0)

    def test_mapping_service_preparar_configuracion_ag(self):
        """Valida la consolidación completa de configuración para el AG."""
        u_dto = UserPreferencesDTO(
            dias_disponibles=3,
            presupuesto_max=75.0,
            condicion_fisica="Fácil",
            nodo_base=CoordenadasDTO(lat=-12.05, lon=-77.05)
        )
        f_dto = FuzzySemanticPreferencesDTO(sensibilidad_seguridad=1.3)
        cfg = LomasMappingService.preparar_configuracion_ag(u_dto, f_dto)

        self.assertEqual(cfg["k"], 3)
        self.assertEqual(cfg["presupuesto"], 75.0)
        self.assertEqual(cfg["delta_exigencia"], 1.0)
        self.assertEqual(cfg["gamma_riesgo"], 2.6)
        self.assertEqual(cfg["nodo_base"], {"lat": -12.05, "lon": -77.05})

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
