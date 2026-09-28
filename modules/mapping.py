"""
Módulo de Mapeo Determinista Urbano (POO).
"""


class LomasMappingService:
    """Servicio para mapear los días disponibles al número de destinos K."""

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


# Función para compatibilidad con código existente
def dias_a_k(dias: int) -> int:
    return LomasMappingService.dias_a_k(dias)


__all__ = ["LomasMappingService", "dias_a_k"]

