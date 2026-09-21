"""
Módulo de Razonamiento bajo Incertidumbre: Lógica Difusa Mamdani.
Responsable: André (ndrz) - Grupo 5
"""

from typing import List, Dict, Any
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


class LomasFuzzySystem:
    """Encapsula el motor de inferencia difusa Mamdani para Lomas de Lima."""

    def __init__(self):
        # 1. Definición del Universo de Discurso
        self.saturacion = ctrl.Antecedent(np.linspace(0.0, 1.0, 101), 'saturacion')
        self.seguridad = ctrl.Antecedent(np.linspace(0.0, 10.0, 101), 'seguridad')
        self.clima = ctrl.Antecedent(np.linspace(0.0, 10.0, 101), 'clima')
        self.accesibilidad = ctrl.Antecedent(np.linspace(0.0, 10.0, 101), 'accesibilidad')
        
        # Consequent: 'centroid' es el método por defecto en skfuzzy
        self.recomendacion = ctrl.Consequent(np.linspace(0.0, 10.0, 101), 'recomendacion')
        self.recomendacion.defuzzify_method = 'centroid'

        # 2. Funciones de Membresía
        # Saturación (Baja, Media, Alta)
        self.saturacion['Baja'] = fuzz.trapmf(self.saturacion.universe, [0.0, 0.0, 0.20, 0.40])
        self.saturacion['Media'] = fuzz.trimf(self.saturacion.universe, [0.25, 0.50, 0.75])
        self.saturacion['Alta'] = fuzz.trapmf(self.saturacion.universe, [0.60, 0.80, 1.0, 1.0])

        # Seguridad (Riesgoso, Moderado, Seguro)
        self.seguridad['Riesgoso'] = fuzz.trapmf(self.seguridad.universe, [0.0, 0.0, 2.5, 4.5])
        self.seguridad['Moderado'] = fuzz.trimf(self.seguridad.universe, [3.5, 6.0, 8.0])
        self.seguridad['Seguro'] = fuzz.trapmf(self.seguridad.universe, [7.0, 8.5, 10.0, 10.0])

        # Clima / Verdor (Seco, Favorable, Optimo_Garua)
        self.clima['Seco'] = fuzz.trapmf(self.clima.universe, [0.0, 0.0, 2.0, 4.5])
        self.clima['Favorable'] = fuzz.trimf(self.clima.universe, [3.5, 6.0, 8.0])
        self.clima['Optimo_Garua'] = fuzz.trapmf(self.clima.universe, [7.0, 8.5, 10.0, 10.0])

        # Accesibilidad (Dificil, Media, Facil)
        self.accesibilidad['Dificil'] = fuzz.trapmf(self.accesibilidad.universe, [0.0, 0.0, 2.5, 4.5])
        self.accesibilidad['Media'] = fuzz.trimf(self.accesibilidad.universe, [3.5, 6.0, 8.0])
        self.accesibilidad['Facil'] = fuzz.trapmf(self.accesibilidad.universe, [7.0, 8.5, 10.0, 10.0])

        # Salida: Recomendación (Muy_Baja, Baja, Media, Alta, Muy_Alta)
        self.recomendacion['Muy_Baja'] = fuzz.trimf(self.recomendacion.universe, [0.0, 0.0, 2.5])
        self.recomendacion['Baja'] = fuzz.trimf(self.recomendacion.universe, [1.5, 3.5, 5.0])
        self.recomendacion['Media'] = fuzz.trimf(self.recomendacion.universe, [4.0, 5.5, 7.0])
        self.recomendacion['Alta'] = fuzz.trimf(self.recomendacion.universe, [6.0, 7.5, 9.0])
        self.recomendacion['Muy_Alta'] = fuzz.trapmf(self.recomendacion.universe, [7.5, 9.0, 10.0, 10.0])

        # 3. Base de Reglas Mamdani (20 reglas calibradas)
        reglas = [
            # Óptimas
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Seguro'] & self.clima['Optimo_Garua'] & self.accesibilidad['Facil'], self.recomendacion['Muy_Alta']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Seguro'] & self.clima['Optimo_Garua'] & self.accesibilidad['Media'], self.recomendacion['Muy_Alta']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Moderado'] & self.clima['Optimo_Garua'] & self.accesibilidad['Facil'], self.recomendacion['Muy_Alta']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Seguro'] & self.clima['Optimo_Garua'] & self.accesibilidad['Facil'], self.recomendacion['Muy_Alta']),

            # Favorables
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Seguro'] & self.clima['Favorable'] & self.accesibilidad['Facil'], self.recomendacion['Alta']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Moderado'] & self.clima['Favorable'] & self.accesibilidad['Media'], self.recomendacion['Alta']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Seguro'] & self.clima['Optimo_Garua'] & self.accesibilidad['Dificil'], self.recomendacion['Alta']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Seguro'] & self.clima['Optimo_Garua'] & self.accesibilidad['Media'], self.recomendacion['Alta']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Moderado'] & self.clima['Optimo_Garua'] & self.accesibilidad['Facil'], self.recomendacion['Alta']),

            # Medias
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Moderado'] & self.clima['Favorable'] & self.accesibilidad['Media'], self.recomendacion['Media']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Moderado'] & self.clima['Seco'] & self.accesibilidad['Facil'], self.recomendacion['Media']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Seguro'] & self.clima['Optimo_Garua'] & self.accesibilidad['Facil'], self.recomendacion['Media']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Seguro'] & self.clima['Seco'] & self.accesibilidad['Media'], self.recomendacion['Media']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Riesgoso'] & self.clima['Optimo_Garua'] & self.accesibilidad['Facil'], self.recomendacion['Media']),

            # Bajas
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Moderado'] & self.clima['Favorable'] & self.accesibilidad['Media'], self.recomendacion['Baja']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Riesgoso'] & self.clima['Favorable'] & self.accesibilidad['Media'], self.recomendacion['Baja']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Moderado'] & self.clima['Seco'] & self.accesibilidad['Dificil'], self.recomendacion['Baja']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Seguro'] & self.clima['Seco'] & self.accesibilidad['Dificil'], self.recomendacion['Baja']),

            # Críticas
            ctrl.Rule(self.seguridad['Riesgoso'] & self.accesibilidad['Dificil'], self.recomendacion['Muy_Baja']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Riesgoso'] & self.clima['Seco'], self.recomendacion['Muy_Baja'])
        ]

        # 4. Sistema de Control y Simulación
        sistema_control = ctrl.ControlSystem(reglas)
        self.simulador = ctrl.ControlSystemSimulation(sistema_control)

    def evaluar(self, saturacion: float, seguridad: float, clima: float, accesibilidad: float) -> float:
        """Evalúa las 4 variables crisp y defusifica por centroide."""
        try:
            self.simulador.input['saturacion'] = float(np.clip(saturacion, 0.0, 1.0))
            self.simulador.input['seguridad'] = float(np.clip(seguridad, 0.0, 10.0))
            self.simulador.input['clima'] = float(np.clip(clima, 0.0, 10.0))
            self.simulador.input['accesibilidad'] = float(np.clip(accesibilidad, 0.0, 10.0))
            
            self.simulador.compute()
            score = self.simulador.output['recomendacion']
            return round(float(np.clip(score, 0.0, 10.0)), 2)
        except Exception:
            # Fallback seguro en caso de corte extremo o valor no mapeado
            score_fallback = (seguridad * 0.35) + ((1.0 - saturacion) * 10.0 * 0.25) + (clima * 0.25) + (accesibilidad * 0.15)
            return round(float(np.clip(score_fallback, 0.0, 10.0)), 2)


# Instancia singleton para reutilización eficiente
_FUZZY_ENGINE = None

def _get_fuzzy_engine() -> LomasFuzzySystem:
    global _FUZZY_ENGINE
    if _FUZZY_ENGINE is None:
        _FUZZY_ENGINE = LomasFuzzySystem()
    return _FUZZY_ENGINE


def evaluar_destino_difuso(saturacion: float, seguridad: float, clima: float, accesibilidad: float) -> float:
    """Función de interfaz compatible con la arquitectura del proyecto."""
    motor = _get_fuzzy_engine()
    return motor.evaluar(saturacion, seguridad, clima, accesibilidad)


def calcular_scores_todos_destinos(destinos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calcula el Score Difuso para cada una de las 15 lomas del catálogo."""
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
