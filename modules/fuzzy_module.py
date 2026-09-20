"""
Módulo de Razonamiento bajo Incertidumbre (Lógica Difusa Mamdani).
"""

from typing import List, Dict, Any


def evaluar_destino_difuso(
    saturacion: float,
    seguridad: float,
    clima: float,
    accesibilidad: float
) -> float:
    """
    Evalúa una loma según 4 variables de incertidumbre y retorna un Score [0.0, 10.0].
    
    # TODO (Integrante 1):
    # 1. Importar skfuzzy y skfuzzy.control.
    # 2. Definir Antecedents: saturacion [0,1], seguridad [0,10], clima [0,10], accesibilidad [0,10].
    # 3. Definir Consequent: recomendacion [0,10] con defuzzificación por centroide.
    # 4. Implementar las 20 reglas Mamdani descritas en el README.md.
    """
    # Clamp de valores a sus rangos válidos
    sat = max(0.0, min(1.0, float(saturacion)))
    seg = max(0.0, min(10.0, float(seguridad)))
    cli = max(0.0, min(10.0, float(clima)))
    acc = max(0.0, min(10.0, float(accesibilidad)))

    # Línea base provisional (simula el centroide Mamdani para que el sistema funcione ya):
    # Ponderación: Seguridad (35%), Desaturación (25%), Verdor/Clima (25%), Acceso (15%)
    score = (seg * 0.35) + ((1.0 - sat) * 10.0 * 0.25) + (cli * 0.25) + (acc * 0.15)
    return round(max(0.0, min(10.0, score)), 2)


def calcular_scores_todos_destinos(destinos: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calcula el Score Difuso para cada una de las lomas del catálogo.
    """
    scores = {}
    for d in destinos:
        did = d['id']
        scores[did] = evaluar_destino_difuso(
            saturacion=d.get('saturacion_base', 0.5),
            seguridad=d.get('seguridad_base', 5.0),
            clima=d.get('clima_verdor_base', 5.0),
            accesibilidad=d.get('accesibilidad_base', 5.0)
        )
    return scores
