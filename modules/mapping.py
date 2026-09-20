"""
Módulo de Mapeo Determinista (Días Disponibles -> K Destinos).
"""

import math


def dias_a_k(dias_disponibles: int, k_max: int = 8, dias_por_destino: float = 4.0) -> int:
    """
    Calcula el número de destinos K a visitar según los días disponibles del turista.
    
    Fundamentación:
        K = ceil(dias_disponibles / 4.0), con cota superior K_max = 8 y mínima K_min = 1.
        Un destino promedio requiere traslado, trekking y descanso.
    
    Args:
        dias_disponibles (int): Días de viaje disponibles declarados por el usuario.
        k_max (int): Número máximo de destinos visitables en una ruta (por defecto 8).
        dias_por_destino (float): Tasa de días requeridos por destino (por defecto 4.0).
        
    Returns:
        int: Número de destinos K para la optimización del Algoritmo Genético.
    """
    if dias_disponibles <= 0:
        return 1
    
    k_calculado = math.ceil(dias_disponibles / dias_por_destino)
    return max(1, min(k_calculado, k_max))
