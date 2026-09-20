"""
Orquestador CLI del Sistema Inteligente de Lomas de Lima.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

# Compatibilidad UTF-8 en consola de Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from modules.mapping import dias_a_k
from modules.fuzzy_module import calcular_scores_todos_destinos
from modules.genetic_algorithm import optimizar_ruta_lomas
from modules.llm_module import extraer_preferencias_usuario, generar_itinerario_narrativo
from modules.access_module import obtener_guia_acceso


def cargar_destinos() -> list:
    """Carga los 15 destinos desde data/destinos.json."""
    ruta_json = os.path.join(os.path.dirname(__file__), "data", "destinos.json")
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def ejecutar_pipeline(texto_usuario: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo:
    1. NLP/LLM -> 2. Mapeo K -> 3. Lógica Difusa -> 4. Algoritmo Genético -> 5. Itinerario
    """
    if verbose:
        print("\nSISTEMA INTELIGENTE DE RUTAS: LOMAS DE LIMA ")

    # Paso 0: Catálogo
    destinos = cargar_destinos()

    # Paso 1: Extracción de preferencias (NLP / LLM)
    perfil = extraer_preferencias_usuario(texto_usuario)
    dias = perfil.get("dias_disponibles", 3)
    presupuesto = perfil.get("presupuesto_max", 60.0)

    # Paso 2: Mapeo de días a K destinos
    k = dias_a_k(dias)

    # Paso 3: Evaluación de incertidumbre (Lógica Difusa)
    scores = calcular_scores_todos_destinos(destinos)

    # Paso 4: Optimización de ruta (Algoritmo Genético)
    resultado_ag = optimizar_ruta_lomas(
        destinos=destinos,
        scores_difusos=scores,
        k=k,
        presupuesto=presupuesto,
        dias_disponibles=dias,
        generaciones=50,
        tam_poblacion=40
    )

    # Paso 5: Itinerario narrativo y guías de transporte
    itinerario = generar_itinerario_narrativo(resultado_ag, perfil)
    guias_transporte = {did: obtener_guia_acceso(did) for did in resultado_ag["ruta_ids"]}

    if verbose:
        print(f"\n[1] Preferencias extraídas: {dias} días | Presupuesto: S/{presupuesto:.2f} | Condición: {perfil.get('condicion_fisica')}")
        print(f"[2] Mapeo: {dias} días -> K = {k} destinos")
        print(f"[3] Lógica Difusa: Evaluadas {len(scores)} lomas")
        print(f"[4] Ruta AG óptima: {' -> '.join(resultado_ag['ruta_ids'])} | Fitness: {resultado_ag['fitness']:.3f}")
        print(f"    Costo total: S/{resultado_ag['costo_total']:.2f} | Distancia: {resultado_ag['distancia_total_km']:.1f} km\n")
        print(itinerario)
        print("\nGUÍA BÁSICA DE TRANSPORTE")
        for did, guia in guias_transporte.items():
            print(f"- {guia['nombre']}: {guia['medio_transporte']} (~{guia['tiempo_total_min']} min)")
        print("\n[OK] Pipeline finalizado con éxito.\n")

    return {
        "perfil": perfil,
        "k": k,
        "scores_difusos": scores,
        "resultado_ag": resultado_ag,
        "itinerario": itinerario,
        "guias_transporte": guias_transporte
    }


def main():
    parser = argparse.ArgumentParser(description="Pipeline CLI de Rutas en Lomas de Lima")
    parser.add_argument("--texto", type=str, default=None, help="Texto con preferencias del usuario")
    parser.add_argument("--demo", action="store_true", help="Ejecuta demostración de prueba")
    args = parser.parse_args()

    texto = args.texto or "Quiero viajar 3 días con 60 soles por senderos verdes de dificultad moderada."
    ejecutar_pipeline(texto, verbose=True)


if __name__ == "__main__":
    main()
