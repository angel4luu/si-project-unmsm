"""
Módulo de Acceso y Transporte Público (Esqueleto).
"""

import os
import json
from typing import Dict, Any

# Cargar catálogo de lomas para autogenerar guías de acceso
_CATALOGO_CACHE = None


def _obtener_catalogo() -> dict:
    global _CATALOGO_CACHE
    if _CATALOGO_CACHE is None:
        ruta = os.path.join(os.path.dirname(__file__), "..", "data", "destinos.json")
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                _CATALOGO_CACHE = {d["id"]: d for d in json.load(f)}
        else:
            _CATALOGO_CACHE = {}
    return _CATALOGO_CACHE


def obtener_guia_acceso(id_destino: str) -> Dict[str, Any]:
    """
    Retorna la información logística de transporte para una loma determinada.
    TODO (Integrante 4): Ampliar los pasos de conexión con estaciones de Metro/Metropolitano.
    """
    catalogo = _obtener_catalogo()
    d = catalogo.get(id_destino, {})
    nombre = d.get("nombre", f"Destino {id_destino}")
    transporte = d.get("transporte_principal", "Transporte público urbano hacia la zona.")
    tiempo = d.get("distancia_centro_min", 60)
    costo = d.get("costo_estimado", 5.0)

    return {
        "nombre": nombre,
        "punto_partida_recomendado": f"Estación central o alimentador hacia {d.get('distrito', 'Lima')}",
        "medio_transporte": transporte,
        "tiempo_total_min": tiempo,
        "costo_total_soles": costo,
        "pasos": [
            f"1. Abordar transporte público hacia {d.get('distrito', 'el distrito de destino')}.",
            f"2. Tomar conexión local indicada: {transporte}.",
            "3. Llegar al punto de control e inicio de senderos."
        ],
        "recomendaciones": "Llevar efectivo para pasajes locales e iniciar el recorrido por la mañana."
    }
