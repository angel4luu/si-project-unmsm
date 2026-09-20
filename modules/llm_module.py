"""
Módulo 1: Procesamiento de Lenguaje Natural e IA Generativa.
"""

import re
from typing import Dict, Any

# TODO (Integrante 3): Si desean conectar una API real de OpenAI o Gemini,
# agregar aquí la llamada al cliente (usando OPENAI_API_KEY o GEMINI_API_KEY).
# Por ahora, usamos un extractor heurístico rápido offline.


def extraer_preferencias_usuario(texto: str) -> Dict[str, Any]:
    """
    Extrae entidades estructuradas (días, presupuesto, condición, clima) desde texto libre.
    TODO (Integrante 3): Reemplazar o complementar estas regex con llamada a un LLM en formato JSON.
    """
    t = texto.lower()
    perfil = {
        "dias_disponibles": 3,
        "presupuesto_max": 60.0,
        "condicion_fisica": "Moderado",
        "clima_preferido": "Garúa",
        "intereses": ["Naturaleza"]
    }

    # Extraer días (ej. '4 días', '2 dias')
    m_dias = re.search(r'(\d+)\s*(?:días|dias|dia|día)', t)
    if m_dias:
        perfil["dias_disponibles"] = int(m_dias.group(1))

    # Extraer presupuesto (ej. '80 soles', 's/ 50')
    m_pres = re.search(r'(\d+(?:\.\d+)?)\s*(?:soles|sol|s/\.?)', t)
    if not m_pres:
        m_pres = re.search(r'(?:s/\.?|presupuesto de|hasta)\s*(\d+(?:\.\d+)?)', t)
    if m_pres:
        perfil["presupuesto_max"] = float(m_pres.group(1))

    # Condición física
    if any(p in t for p in ["fácil", "facil", "suave", "principiante"]):
        perfil["condicion_fisica"] = "Fácil"
    elif any(p in t for p in ["difícil", "dificil", "fuerte", "experto"]):
        perfil["condicion_fisica"] = "Difícil"

    # Clima preferido
    if any(p in t for p in ["garúa", "garua", "verde", "neblina"]):
        perfil["clima_preferido"] = "Garúa"
    elif any(p in t for p in ["sol", "soleado"]):
        perfil["clima_preferido"] = "Soleado"

    return perfil


def generar_itinerario_narrativo(resultado_ag: Dict[str, Any], perfil_usuario: Dict[str, Any]) -> str:
    """
    Genera una descripción narrativa del itinerario a partir de la ruta del AG.
    TODO (Integrante 3): Reemplazar con llamada a LLM para enriquecer la narrativa turística.
    """
    destinos = resultado_ag.get("destinos_ordenados", [])
    if not destinos:
        return "No hay destinos seleccionados para generar el itinerario."

    lineas = [
        "## ITINERARIO RECOMENDADO DE TREKKING EN LOMAS",
        f"**Duración:** {perfil_usuario.get('dias_disponibles', len(destinos))} días | "
        f"**Costo Estimado:** S/{resultado_ag.get('costo_total', 0):.2f} | "
        f"**Distancia:** {resultado_ag.get('distancia_total_km', 0):.1f} km",
        ""
    ]

    for idx, d in enumerate(destinos, start=1):
        lineas.append(f"### Día {idx}: {d['nombre']} ({d['distrito']})")
        lineas.append(f"- **Dificultad:** {d['dificultad']} | **Tiempo estimado:** {d['tiempo_estimado_horas']}h")
        lineas.append(f"- **Transporte:** {d.get('transporte_principal', 'Transporte público local')}")
        lineas.append(f"- **Descripción:** {d.get('descripcion', '')}")
        lineas.append("")

    return "\n".join(lineas)
