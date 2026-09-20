"""
Módulo de Optimización Heurística.
"""

import math
import random
from typing import List, Dict, Any


def distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia en km entre dos coordenadas geográficas."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class LomasGeneticOptimizer:
    """
    Optimizador de rutas turísticas mediante Algoritmo Genético.
    # TODO (Tú):
    # 1. Experimentar con cruce Order Crossover (OX) vs otros operadores.
    # 2. Ajustar la tasa de mutación (swap vs inserción) y tamaño de torneo.
    # 3. Guardar el historial de fitness para generar las gráficas de convergencia.
    """

    def __init__(self, destinos: List[Dict[str, Any]], scores_difusos: Dict[str, float],
                 k: int, presupuesto: float, dias_disponibles: int,
                 generaciones: int = 50, tam_poblacion: int = 30):
        self.destinos = destinos
        self.destinos_dict = {d['id']: d for d in destinos}
        self.scores_difusos = scores_difusos
        self.k = min(k, len(destinos))
        self.presupuesto = float(presupuesto)
        self.dias = int(dias_disponibles)
        self.generaciones = generaciones
        self.tam_poblacion = tam_poblacion

    def _generar_individuo(self) -> List[str]:
        """Cromosoma de permutación pura: K destinos aleatorios sin repetir."""
        todos_ids = [d['id'] for d in self.destinos]
        return random.sample(todos_ids, self.k)

    def fitness(self, ruta: List[str]) -> float:
        """
        Función de aptitud: Suma de scores difusos - penalización por exceso de presupuesto.
        """
        # 1. Beneficio de los destinos elegidos (Score Difuso)
        beneficio = sum(self.scores_difusos.get(did, 5.0) for did in ruta)

        # 2. Costo total de pasajes e ingresos
        costo_total = sum(self.destinos_dict[did].get('costo_estimado', 15.0) for did in ruta)

        # 3. Penalización cuadrática si excede el presupuesto del turista
        penalizacion_presupuesto = max(0.0, costo_total - self.presupuesto) ** 2

        # 4. Castigo severo si hay destinos repetidos
        penalizacion_unicidad = 1000.0 if len(set(ruta)) != len(ruta) else 0.0

        return beneficio - (1.0 * penalizacion_presupuesto) - penalizacion_unicidad

    def optimizar(self) -> Dict[str, Any]:
        """Bucle evolutivo básico del Algoritmo Genético."""
        poblacion = [self._generar_individuo() for _ in range(self.tam_poblacion)]
        mejor_historico = None
        mejor_fit = -float('inf')

        for gen in range(self.generaciones):
            # Evaluar y ordenar por fitness
            poblacion = sorted(poblacion, key=self.fitness, reverse=True)
            if self.fitness(poblacion[0]) > mejor_fit:
                mejor_fit = self.fitness(poblacion[0])
                mejor_historico = list(poblacion[0])

            # Elitismo: conservar los 2 mejores
            nueva_pob = [list(poblacion[0]), list(poblacion[1])]

            # Generar resto de la población (selección por torneo simple + mutación swap)
            while len(nueva_pob) < self.tam_poblacion:
                # Torneo k=3
                candidato = max(random.sample(poblacion, 3), key=self.fitness)
                hijo = list(candidato)

                # Mutación Swap (intercambiar dos lomas con 20% de probabilidad)
                if random.random() < 0.20 and len(hijo) >= 2:
                    i1, i2 = random.sample(range(len(hijo)), 2)
                    hijo[i1], hijo[i2] = hijo[i2], hijo[i1]

                nueva_pob.append(hijo)

            poblacion = nueva_pob

        # Calcular métricas finales de la ruta óptima
        costo_final = sum(self.destinos_dict[did].get('costo_estimado', 15.0) for did in mejor_historico)
        horas_final = sum(self.destinos_dict[did].get('tiempo_estimado_horas', 3.5) for did in mejor_historico)
        dist_final = 0.0
        for i in range(len(mejor_historico) - 1):
            c1 = self.destinos_dict[mejor_historico[i]]['coordenadas']
            c2 = self.destinos_dict[mejor_historico[i + 1]]['coordenadas']
            dist_final += distancia_haversine(c1['lat'], c1['lon'], c2['lat'], c2['lon'])

        return {
            'ruta_ids': mejor_historico,
            'destinos_ordenados': [self.destinos_dict[did] for did in mejor_historico],
            'fitness': round(mejor_fit, 2),
            'costo_total': round(costo_final, 2),
            'distancia_total_km': round(dist_final, 2),
            'tiempo_estimado_horas': round(horas_final, 2)
        }


def optimizar_ruta_lomas(destinos, scores_difusos, k, presupuesto, dias_disponibles,
                         generaciones=50, tam_poblacion=30) -> Dict[str, Any]:
    """Acceso directo para ejecutar la optimización."""
    opt = LomasGeneticOptimizer(destinos, scores_difusos, k, presupuesto, dias_disponibles,
                                generaciones, tam_poblacion)
    return opt.optimizar()
