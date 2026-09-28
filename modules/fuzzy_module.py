"""
Modulo de Razonamiento bajo Incertidumbre: Logica Difusa Mamdani.
Responsable: Andre (ndrz) - Grupo 5

Contiene dos sistemas difusos independientes:
  1. RiesgoFuzzySystem    - Evalua el nivel de riesgo de una loma (Componente 2).
  2. ExigenciaFuzzySystem - Evalua el nivel de exigencia de exploracion (Componente 1).
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


class RiesgoFuzzySystem:
    """
    Sistema difuso Mamdani para evaluar el nivel de riesgo de una loma.
    Entradas: saturacion [0.0, 1.0], seguridad [0.0, 10.0], accesibilidad [0.0, 10.0].
    Salida: nivel_riesgo [0.0, 10.0].
    Semantica: un puntaje de riesgo alto indica condiciones desfavorables o peligrosas.
    """

    def __init__(self):
        # 1. Definicion del Universo de Discurso
        self.saturacion = ctrl.Antecedent(np.linspace(0.0, 1.0, 101), 'saturacion')
        self.seguridad = ctrl.Antecedent(np.linspace(0.0, 10.0, 101), 'seguridad')
        self.accesibilidad = ctrl.Antecedent(np.linspace(0.0, 10.0, 101), 'accesibilidad')

        self.nivel_riesgo = ctrl.Consequent(np.linspace(0.0, 10.0, 101), 'nivel_riesgo')
        self.nivel_riesgo.defuzzify_method = 'centroid'

        # 2. Funciones de Membresia
        # Saturacion: Baja, Media, Alta
        self.saturacion['Baja'] = fuzz.trapmf(self.saturacion.universe, [0.0, 0.0, 0.20, 0.40])
        self.saturacion['Media'] = fuzz.trimf(self.saturacion.universe, [0.25, 0.50, 0.75])
        self.saturacion['Alta'] = fuzz.trapmf(self.saturacion.universe, [0.60, 0.80, 1.0, 1.0])

        # Seguridad: Riesgoso, Moderado, Seguro
        self.seguridad['Riesgoso'] = fuzz.trapmf(self.seguridad.universe, [0.0, 0.0, 2.5, 4.5])
        self.seguridad['Moderado'] = fuzz.trimf(self.seguridad.universe, [3.5, 6.0, 8.0])
        self.seguridad['Seguro'] = fuzz.trapmf(self.seguridad.universe, [7.0, 8.5, 10.0, 10.0])

        # Accesibilidad: Dificil, Media, Facil
        self.accesibilidad['Dificil'] = fuzz.trapmf(self.accesibilidad.universe, [0.0, 0.0, 2.5, 4.5])
        self.accesibilidad['Media'] = fuzz.trimf(self.accesibilidad.universe, [3.5, 6.0, 8.0])
        self.accesibilidad['Facil'] = fuzz.trapmf(self.accesibilidad.universe, [7.0, 8.5, 10.0, 10.0])

        # Salida: Nivel de Riesgo (Muy_Bajo, Bajo, Medio, Alto, Muy_Alto)
        self.nivel_riesgo['Muy_Bajo'] = fuzz.trimf(self.nivel_riesgo.universe, [0.0, 0.0, 2.5])
        self.nivel_riesgo['Bajo'] = fuzz.trimf(self.nivel_riesgo.universe, [1.5, 3.5, 5.0])
        self.nivel_riesgo['Medio'] = fuzz.trimf(self.nivel_riesgo.universe, [4.0, 5.5, 7.0])
        self.nivel_riesgo['Alto'] = fuzz.trimf(self.nivel_riesgo.universe, [6.0, 7.5, 9.0])
        self.nivel_riesgo['Muy_Alto'] = fuzz.trapmf(self.nivel_riesgo.universe, [7.5, 9.0, 10.0, 10.0])

        # 3. Base de Reglas Mamdani (16 reglas calibradas)
        reglas = [
            # Nivel Muy_Alto (4 reglas)
            ctrl.Rule(self.seguridad['Riesgoso'] & self.accesibilidad['Dificil'],
                      self.nivel_riesgo['Muy_Alto']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Riesgoso'],
                      self.nivel_riesgo['Muy_Alto']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Moderado'] & self.accesibilidad['Dificil'],
                      self.nivel_riesgo['Muy_Alto']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Riesgoso'] & self.accesibilidad['Dificil'],
                      self.nivel_riesgo['Muy_Alto']),

            # Nivel Alto (4 reglas)
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Moderado'] & self.accesibilidad['Media'],
                      self.nivel_riesgo['Alto']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Riesgoso'] & self.accesibilidad['Media'],
                      self.nivel_riesgo['Alto']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Riesgoso'] & self.accesibilidad['Dificil'],
                      self.nivel_riesgo['Alto']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Moderado'] & self.accesibilidad['Dificil'],
                      self.nivel_riesgo['Alto']),

            # Nivel Medio (4 reglas)
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Moderado'] & self.accesibilidad['Media'],
                      self.nivel_riesgo['Medio']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Seguro'] & self.accesibilidad['Facil'],
                      self.nivel_riesgo['Medio']),
            ctrl.Rule(self.saturacion['Alta'] & self.seguridad['Seguro'] & self.accesibilidad['Media'],
                      self.nivel_riesgo['Medio']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Moderado'] & self.accesibilidad['Media'],
                      self.nivel_riesgo['Medio']),

            # Nivel Bajo (3 reglas)
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Moderado'] & self.accesibilidad['Facil'],
                      self.nivel_riesgo['Bajo']),
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Seguro'] & self.accesibilidad['Media'],
                      self.nivel_riesgo['Bajo']),
            ctrl.Rule(self.saturacion['Media'] & self.seguridad['Seguro'] & self.accesibilidad['Facil'],
                      self.nivel_riesgo['Bajo']),

            # Nivel Muy_Bajo (1 regla)
            ctrl.Rule(self.saturacion['Baja'] & self.seguridad['Seguro'] & self.accesibilidad['Facil'],
                      self.nivel_riesgo['Muy_Bajo']),
        ]

        # 4. Sistema de Control y Simulacion
        sistema_control = ctrl.ControlSystem(reglas)
        self.simulador = ctrl.ControlSystemSimulation(sistema_control)

    def evaluar(self, saturacion: float, seguridad: float, accesibilidad: float) -> float:
        """Evalua las 3 variables crisp y defusifica por centroide. Retorna nivel de riesgo en [0.0, 10.0]."""
        try:
            self.simulador.reset()
            self.simulador.input['saturacion'] = float(np.clip(saturacion, 0.0, 1.0))
            self.simulador.input['seguridad'] = float(np.clip(seguridad, 0.0, 10.0))
            self.simulador.input['accesibilidad'] = float(np.clip(accesibilidad, 0.0, 10.0))

            self.simulador.compute()
            riesgo = self.simulador.output['nivel_riesgo']
            return round(float(np.clip(riesgo, 0.0, 10.0)), 2)
        except Exception:
            # Fallback seguro ponderado en caso de indeterminacion numerica
            riesgo_fallback = (saturacion * 10.0 * 0.30) + ((10.0 - seguridad) * 0.40) + ((10.0 - accesibilidad) * 0.30)
            return round(float(np.clip(riesgo_fallback, 0.0, 10.0)), 2)


class ExigenciaFuzzySystem:
    """
    Sistema difuso Mamdani para modelar el nivel de exigencia de exploracion.
    Entradas: horas [1.0, 6.0], cobertura [0.0, 1.0], extension [1.0, 10.0].
    Salida: nivel_exigencia [0.0, 1.0].
    Se alimenta directamente de los genes reales contenidos en el cromosoma del AG.
    """

    def __init__(self):
        # 1. Definicion del Universo de Discurso
        self.horas = ctrl.Antecedent(np.linspace(1.0, 6.0, 101), 'horas')
        self.cobertura = ctrl.Antecedent(np.linspace(0.0, 1.0, 101), 'cobertura')
        self.extension = ctrl.Antecedent(np.linspace(1.0, 10.0, 101), 'extension')

        self.nivel_exigencia = ctrl.Consequent(np.linspace(0.0, 1.0, 101), 'nivel_exigencia')
        self.nivel_exigencia.defuzzify_method = 'centroid'

        # 2. Funciones de Membresia
        # Horas de recorrido: Corto, Moderado, Extenso
        self.horas['Corto'] = fuzz.trapmf(self.horas.universe, [1.0, 1.0, 1.5, 3.0])
        self.horas['Moderado'] = fuzz.trimf(self.horas.universe, [2.0, 3.5, 5.0])
        self.horas['Extenso'] = fuzz.trapmf(self.horas.universe, [4.0, 5.0, 6.0, 6.0])

        # Cobertura de zona: Parcial, Intermedia, Completa
        self.cobertura['Parcial'] = fuzz.trapmf(self.cobertura.universe, [0.0, 0.0, 0.15, 0.35])
        self.cobertura['Intermedia'] = fuzz.trimf(self.cobertura.universe, [0.25, 0.50, 0.75])
        self.cobertura['Completa'] = fuzz.trapmf(self.cobertura.universe, [0.60, 0.80, 1.0, 1.0])

        # Extension del circuito: Corto, Medio, Largo
        self.extension['Corto'] = fuzz.trapmf(self.extension.universe, [1.0, 1.0, 2.0, 4.5])
        self.extension['Medio'] = fuzz.trimf(self.extension.universe, [3.0, 5.5, 8.0])
        self.extension['Largo'] = fuzz.trapmf(self.extension.universe, [6.5, 8.5, 10.0, 10.0])

        # Salida: Nivel de Exigencia (Relajado, Moderado, Intenso)
        self.nivel_exigencia['Relajado'] = fuzz.trapmf(self.nivel_exigencia.universe, [0.0, 0.0, 0.15, 0.35])
        self.nivel_exigencia['Moderado'] = fuzz.trimf(self.nivel_exigencia.universe, [0.25, 0.50, 0.75])
        self.nivel_exigencia['Intenso'] = fuzz.trapmf(self.nivel_exigencia.universe, [0.65, 0.85, 1.0, 1.0])

        # 3. Base de Reglas Mamdani (12 reglas calibradas)
        reglas = [
            # Nivel Intenso (4 reglas)
            ctrl.Rule(self.horas['Extenso'] & self.cobertura['Completa'] & self.extension['Largo'],
                      self.nivel_exigencia['Intenso']),
            ctrl.Rule(self.horas['Extenso'] & self.cobertura['Completa'] & self.extension['Medio'],
                      self.nivel_exigencia['Intenso']),
            ctrl.Rule(self.horas['Extenso'] & self.cobertura['Intermedia'] & self.extension['Largo'],
                      self.nivel_exigencia['Intenso']),
            ctrl.Rule(self.horas['Moderado'] & self.cobertura['Completa'] & self.extension['Largo'],
                      self.nivel_exigencia['Intenso']),

            # Nivel Moderado (4 reglas)
            ctrl.Rule(self.horas['Moderado'] & self.cobertura['Intermedia'] & self.extension['Medio'],
                      self.nivel_exigencia['Moderado']),
            ctrl.Rule(self.horas['Extenso'] & self.cobertura['Parcial'] & self.extension['Medio'],
                      self.nivel_exigencia['Moderado']),
            ctrl.Rule(self.horas['Corto'] & self.cobertura['Completa'] & self.extension['Medio'],
                      self.nivel_exigencia['Moderado']),
            ctrl.Rule(self.horas['Moderado'] & self.cobertura['Completa'] & self.extension['Corto'],
                      self.nivel_exigencia['Moderado']),

            # Nivel Relajado (4 reglas)
            ctrl.Rule(self.horas['Corto'] & self.cobertura['Parcial'] & self.extension['Corto'],
                      self.nivel_exigencia['Relajado']),
            ctrl.Rule(self.horas['Corto'] & self.cobertura['Parcial'] & self.extension['Medio'],
                      self.nivel_exigencia['Relajado']),
            ctrl.Rule(self.horas['Corto'] & self.cobertura['Intermedia'] & self.extension['Corto'],
                      self.nivel_exigencia['Relajado']),
            ctrl.Rule(self.horas['Moderado'] & self.cobertura['Parcial'] & self.extension['Corto'],
                      self.nivel_exigencia['Relajado']),
        ]

        # 4. Sistema de Control y Simulacion
        sistema_control = ctrl.ControlSystem(reglas)
        self.simulador = ctrl.ControlSystemSimulation(sistema_control)

    def evaluar(self, horas: float, cobertura: float, extension: float) -> float:
        """Evalua los 3 genes reales y defusifica por centroide. Retorna nivel de exigencia en [0.0, 1.0]."""
        try:
            self.simulador.reset()
            self.simulador.input['horas'] = float(np.clip(horas, 1.0, 6.0))
            self.simulador.input['cobertura'] = float(np.clip(cobertura, 0.0, 1.0))
            self.simulador.input['extension'] = float(np.clip(extension, 1.0, 10.0))

            self.simulador.compute()
            exigencia = self.simulador.output['nivel_exigencia']
            return round(float(np.clip(exigencia, 0.0, 1.0)), 4)
        except Exception:
            # Fallback ponderado normalizado
            h_norm = (horas - 1.0) / 5.0
            c_norm = cobertura
            e_norm = (extension - 1.0) / 9.0
            return round(float(np.clip(0.4 * h_norm + 0.3 * c_norm + 0.3 * e_norm, 0.0, 1.0)), 4)


# --- Instancias Singleton para Reutilizacion Eficiente ---
_RIESGO_ENGINE = None
_EXIGENCIA_ENGINE = None


def _get_riesgo_engine() -> RiesgoFuzzySystem:
    global _RIESGO_ENGINE
    if _RIESGO_ENGINE is None:
        _RIESGO_ENGINE = RiesgoFuzzySystem()
    return _RIESGO_ENGINE


def _get_exigencia_engine() -> ExigenciaFuzzySystem:
    global _EXIGENCIA_ENGINE
    if _EXIGENCIA_ENGINE is None:
        _EXIGENCIA_ENGINE = ExigenciaFuzzySystem()
    return _EXIGENCIA_ENGINE


def evaluar_riesgo_loma(saturacion: float, seguridad: float, accesibilidad: float) -> float:
    """Calcula el nivel de riesgo de una loma. Retorna valor en [0.0, 10.0]."""
    motor = _get_riesgo_engine()
    return motor.evaluar(saturacion, seguridad, accesibilidad)


def evaluar_exigencia(horas: float, cobertura: float, extension: float) -> float:
    """Calcula el nivel de exigencia a partir de los genes reales. Retorna valor en [0.0, 1.0]."""
    motor = _get_exigencia_engine()
    return motor.evaluar(horas, cobertura, extension)


def calcular_riesgos_todos_destinos(destinos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calcula el nivel de riesgo difuso para cada una de las lomas del catalogo."""
    riesgos = {}
    for d in destinos:
        did = d['id']
        riesgos[did] = evaluar_riesgo_loma(
            saturacion=d.get('saturacion_base', 0.5),
            seguridad=d.get('seguridad_base', 5.0),
            accesibilidad=d.get('accesibilidad_base', 5.0)
        )
    return riesgos


# --- Funciones de Compatibilidad hacia atras temporal ---
def evaluar_destino_difuso(saturacion: float, seguridad: float, clima: float, accesibilidad: float) -> float:
    """Compatibilidad temporal con interfaces anteriores."""
    return evaluar_riesgo_loma(saturacion, seguridad, accesibilidad)


def calcular_scores_todos_destinos(destinos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compatibilidad temporal con interfaces anteriores."""
    return calcular_riesgos_todos_destinos(destinos)
