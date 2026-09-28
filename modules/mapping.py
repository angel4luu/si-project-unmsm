"""
Módulo de Mapeo y Adaptación de Parámetros de Dominio (POO).
"""

from typing import Tuple, Dict, Any, Optional
from modules.dtos import UserPreferencesDTO, FuzzySemanticPreferencesDTO, CoordenadasDTO


class LomasMappingService:
    """
    Servicio de dominio para validar, mapear y adaptar las preferencias del usuario
    a la configuración matemática requerida por el Algoritmo Genético y el Motor Difuso.
    """

    @staticmethod
    def dias_a_k(dias: int) -> int:
        """
        Mapea el número de días disponibles al parámetro K de destinos activos.
        - Días <= 1: Retorna K=1 (atajo determinista).
        - Días >= 2: Retorna K = clamp(días, 2, 6).
        """
        if dias <= 1:
            return 1
        return min(max(2, int(dias)), 6)

    @classmethod
    def mapear_pesos_condicion(
        cls,
        condicion_fisica: str,
        sensibilidad_seguridad: float = 1.0
    ) -> Tuple[float, float]:
        """
        Traduce la condición física cualitativa a los hiperparámetros del AG:
        - delta_exigencia: Recompensa por nivel de esfuerzo físico exploratorio.
        - gamma_riesgo: Penalización por riesgo difuso acumulado (modulada por sensibilidad).
        """
        cond = (condicion_fisica or "Moderado").lower().strip()
        if "fácil" in cond or "facil" in cond:
            delta_base, gamma_base = 1.0, 2.0
        elif "difícil" in cond or "dificil" in cond or "fuerte" in cond:
            delta_base, gamma_base = 3.0, 1.0
        else:
            delta_base, gamma_base = 2.0, 1.5

        gamma_ajustado = round(gamma_base * float(sensibilidad_seguridad), 3)
        return delta_base, gamma_ajustado

    @classmethod
    def mapear_restricciones_presupuesto(
        cls,
        presupuesto_max: float,
        k: int
    ) -> Dict[str, float]:
        """
        Calcula las bandas de tolerancia y métricas de presupuesto por destino.
        """
        p_val = max(10.0, float(presupuesto_max))
        k_val = max(1, int(k))
        return {
            "presupuesto_total": p_val,
            "presupuesto_por_destino": round(p_val / k_val, 2),
            "umbral_minimo_viable": round(k_val * 8.0, 2)
        }

    @classmethod
    def preparar_configuracion_ag(
        cls,
        user_prefs: UserPreferencesDTO,
        fuzzy_prefs: FuzzySemanticPreferencesDTO
    ) -> Dict[str, Any]:
        """
        Consolida y adapta todas las preferencias del usuario para instanciar LomasGeneticOptimizer.
        """
        k = cls.dias_a_k(user_prefs.dias_disponibles)
        delta_exigencia, gamma_riesgo = cls.mapear_pesos_condicion(
            user_prefs.condicion_fisica,
            fuzzy_prefs.sensibilidad_seguridad
        )
        nodo_dict = user_prefs.nodo_base.to_dict() if isinstance(user_prefs.nodo_base, CoordenadasDTO) else user_prefs.nodo_base

        return {
            "k": k,
            "presupuesto": float(user_prefs.presupuesto_max),
            "dias_disponibles": int(user_prefs.dias_disponibles),
            "nodo_base": nodo_dict,
            "delta_exigencia": delta_exigencia,
            "gamma_riesgo": gamma_riesgo
        }


# Función para compatibilidad con código existente
def dias_a_k(dias: int) -> int:
    return LomasMappingService.dias_a_k(dias)


__all__ = ["LomasMappingService", "dias_a_k"]
