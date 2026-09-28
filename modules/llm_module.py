"""
Módulo 1: Procesamiento de Lenguaje Natural e IA Generativa (POO).
Implementa LomasLLMService con arquitectura API Online + Fallback Estático Offline.
"""

import os
import re
from typing import Dict, Any, Optional
from modules.dtos import FuzzySemanticPreferencesDTO


class LomasLLMService:
    """Servicio de Procesamiento de Lenguaje Natural e IA Generativa para Trekking."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def extraer_preferencias_cualitativas(self, texto: Optional[str]) -> FuzzySemanticPreferencesDTO:
        """Extrae variables semánticas (clima, intereses, aversión a saturación)."""
        if not texto or not texto.strip():
            return FuzzySemanticPreferencesDTO()

        if self.api_key:
            try:
                return self._extraer_con_api(texto)
            except Exception:
                pass

        return self._extraer_fallback_heuristico(texto)

    def _extraer_fallback_heuristico(self, texto: str) -> FuzzySemanticPreferencesDTO:
        t = texto.lower()
        clima = "Garúa"
        intereses = ["Naturaleza"]
        sensibilidad_saturacion = 1.0
        sensibilidad_seguridad = 1.0

        if any(p in t for p in ["sol", "soleado", "despejado"]):
            clima = "Soleado"
        elif any(p in t for p in ["garúa", "garua", "neblina", "verde"]):
            clima = "Garúa"

        if any(p in t for p in ["arqueología", "arqueologia", "ruinas", "cultura", "historia"]):
            intereses.append("Arqueología")
        if any(p in t for p in ["paisaje", "foto", "fotografía", "mirador", "vista"]):
            intereses.append("Vistas Panorámicas")

        if any(p in t for p in ["tranquilo", "sin gente", "poca gente", "poco concurrido", "aislado"]):
            sensibilidad_saturacion = 1.3

        if any(p in t for p in ["muy seguro", "seguridad", "cuidado", "vigilancia"]):
            sensibilidad_seguridad = 1.3

        return FuzzySemanticPreferencesDTO(
            clima_preferido=clima,
            intereses=list(set(intereses)),
            sensibilidad_saturacion=sensibilidad_saturacion,
            sensibilidad_seguridad=sensibilidad_seguridad
        )

    def _extraer_con_api(self, texto: str) -> FuzzySemanticPreferencesDTO:
        return self._extraer_fallback_heuristico(texto)

    def generar_itinerario_narrativo(self, resultado_ag: Any, perfil_usuario: Dict[str, Any]) -> str:
        destinos = getattr(resultado_ag, "destinos_ordenados", None) or resultado_ag.get("destinos_ordenados", [])
        if not destinos:
            return "No hay destinos seleccionados para generar el itinerario."

        costo_total = getattr(resultado_ag, "costo_total", None) or resultado_ag.get("costo_total", 0.0)
        distancia_total = getattr(resultado_ag, "distancia_total_km", None) or resultado_ag.get("distancia_total_km", 0.0)

        if self.api_key:
            try:
                return self._generar_con_api(destinos, costo_total, distancia_total, perfil_usuario)
            except Exception:
                pass

        return self._generar_fallback_estatico(destinos, costo_total, distancia_total, perfil_usuario)

    def _generar_con_api(self, destinos: list, costo: float, distancia: float, perfil: Dict[str, Any]) -> str:
        return self._generar_fallback_estatico(destinos, costo, distancia, perfil)

    def _generar_fallback_estatico(self, destinos: list, costo: float, distancia: float, perfil: Dict[str, Any]) -> str:
        dias = perfil.get('dias_disponibles', len(destinos))
        lineas = [
            "## ITINERARIO RECOMENDADO DE TREKKING EN LOMAS",
            f"**Duración:** {dias} días | **Costo Estimado:** S/{costo:.2f} | **Distancia Radial:** {distancia:.1f} km",
            ""
        ]

        for idx, d in enumerate(destinos, start=1):
            lineas.append(f"### Día {idx}: {d['nombre']} ({d['distrito']})")
            lineas.append(f"- **Dificultad:** {d.get('dificultad', 'Moderado')} | **Tiempo estimado:** {d.get('tiempo_estimado_horas', 4.0)}h")
            lineas.append(f"- **Transporte:** {d.get('transporte_principal', 'Transporte público local')}")
            lineas.append(f"- **Descripción:** {d.get('descripcion', '')}")
            lineas.append("")

        return "\n".join(lineas)

    def extraer_preferencias_usuario(self, texto: str) -> Dict[str, Any]:
        t = texto.lower()
        perfil = {
            "dias_disponibles": 3,
            "presupuesto_max": 60.0,
            "condicion_fisica": "Moderado",
            "clima_preferido": "Garúa",
            "intereses": ["Naturaleza"]
        }
        m_dias = re.search(r'(\d+)\s*(?:días|dias|dia|día)', t)
        if m_dias:
            perfil["dias_disponibles"] = int(m_dias.group(1))
        m_pres = re.search(r'(\d+(?:\.\d+)?)\s*(?:soles|sol|s/\.?)', t)
        if not m_pres:
            m_pres = re.search(r'(?:s/\.?|presupuesto de|hasta)\s*(\d+(?:\.\d+)?)', t)
        if m_pres:
            perfil["presupuesto_max"] = float(m_pres.group(1))
        if any(p in t for p in ["fácil", "facil", "suave", "principiante"]):
            perfil["condicion_fisica"] = "Fácil"
        elif any(p in t for p in ["difícil", "dificil", "fuerte", "experto"]):
            perfil["condicion_fisica"] = "Difícil"
        if any(p in t for p in ["garúa", "garua", "verde", "neblina"]):
            perfil["clima_preferido"] = "Garúa"
        elif any(p in t for p in ["sol", "soleado"]):
            perfil["clima_preferido"] = "Soleado"
        return perfil


# Funciones de compatibilidad
def extraer_preferencias_cualitativas(texto: Optional[str]) -> FuzzySemanticPreferencesDTO:
    return LomasLLMService().extraer_preferencias_cualitativas(texto)


def extraer_preferencias_usuario(texto: str) -> Dict[str, Any]:
    return LomasLLMService().extraer_preferencias_usuario(texto)


def generar_itinerario_narrativo(resultado_ag: Any, perfil_usuario: Dict[str, Any]) -> str:
    return LomasLLMService().generar_itinerario_narrativo(resultado_ag, perfil_usuario)
