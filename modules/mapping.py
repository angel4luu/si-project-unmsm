"""
Modulo de Mapeo Determinista (Dias Disponibles -> K Destinos).
"""


def dias_a_k(dias_disponibles: int, k_min: int = 2, k_max: int = 6) -> int:
    """
    Calcula el numero de destinos K a visitar segun los dias disponibles del turista.

    Regla de Asignacion Urbana:
    - 1 dia disponible: Retorna K = 1 (horizonte unitario para atajo determinista).
    - 2 o mas dias: Asigna 1 destino por dia, acotado entre k_min (2) y k_max (6).
      Garantiza un espacio combinatorio formal para el Algoritmo Genetico.

    Args:
        dias_disponibles (int): Dias de trekking declarados por el usuario.
        k_min (int): Numero minimo de destinos para optimizacion combinatoria (default 2).
        k_max (int): Cota maxima de destinos para itinerario en Lima (default 6).

    Returns:
        int: Numero de destinos K a seleccionar y ordenar.
    """
    dias = int(dias_disponibles)
    if dias <= 1:
        return 1
    return min(max(k_min, dias), k_max)
