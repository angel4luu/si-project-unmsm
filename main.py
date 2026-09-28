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
from modules.fuzzy_module import calcular_riesgos_todos_destinos
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
    1. NLP/LLM -> 2. Mapeo K -> 3. Evaluacion Base -> 4. Algoritmo Genetico Hibrido -> 5. Itinerario
    """
    if verbose:
        print("\nSISTEMA INTELIGENTE DE RUTAS: LOMAS DE LIMA")

    # Paso 0: Catalogo
    destinos = cargar_destinos()

    # Paso 1: Extraccion de preferencias (NLP / LLM)
    perfil = extraer_preferencias_usuario(texto_usuario)
    dias = perfil.get("dias_disponibles", 3)
    presupuesto = perfil.get("presupuesto_max", 60.0)

    # Paso 2: Mapeo de dias a K destinos
    k = dias_a_k(dias)

    # Paso 3: Evaluacion de incertidumbre (Logica Difusa de Riesgo) y Beneficios Base
    scores_difusos = calcular_riesgos_todos_destinos(destinos)
    beneficios_base = {}
    for d in destinos:
        did = d['id']
        base = 7.0
        if d.get("patrimonio", False):
            base += 1.0
        beneficios_base[did] = round(base, 2)

    # Paso 4: Optimizacion de ruta (Algoritmo Genetico Hibrido con Logica Difusa Dual)
    resultado_ag = optimizar_ruta_lomas(
        destinos=destinos,
        beneficios_base=beneficios_base,
        k=k,
        presupuesto=presupuesto,
        dias_disponibles=dias,
        generaciones=50,
        tam_poblacion=40
    )

    # Paso 5: Itinerario narrativo y guias de transporte
    itinerario = generar_itinerario_narrativo(resultado_ag, perfil)
    guias_transporte = {did: obtener_guia_acceso(did) for did in resultado_ag["ruta_ids"]}

    if verbose:
        print(f"\n[1] Preferencias extraidas: {dias} dias | Presupuesto: S/{presupuesto:.2f} | Condicion: {perfil.get('condicion_fisica')}")
        print(f"[2] Mapeo: {dias} dias -> K = {k} destinos")
        metodo = resultado_ag.get("metodo", "algoritmo_genetico")
        desc_metodo = "Atajo Determinista K=1" if metodo == "atajo_determinista" else "Algoritmo Genetico Hibrido"
        print(f"[4] Ruta Optima ({desc_metodo}): {' -> '.join(resultado_ag['ruta_ids'])} | Fitness: {resultado_ag['fitness']:.3f}")
        print(f"    Costo total: S/{resultado_ag['costo_total']:.2f} | Distancia: {resultado_ag['distancia_total_km']:.1f} km")

        # Detalles de logica difusa integrada
        nivel_exig = resultado_ag.get("nivel_exigencia", 0.0)
        genes_reales = resultado_ag.get("genes_reales", {})
        print(f"\n[Componentes Difusos Integrados]")
        print(f"- Componente 1 (Exigencia en Cromosoma): {nivel_exig:.2f}")
        print(f"  (Horas: {genes_reales.get('horas_recorrido', 0)}h, Cobertura: {genes_reales.get('cobertura_zona', 0)}, Extension: {genes_reales.get('extension_circuito', 0)} km)")
        print(f"- Componente 2 (Riesgo en Fitness por Loma):")
        for did in resultado_ag["ruta_ids"]:
            r = resultado_ag.get("riesgos_ruta", {}).get(did, 5.0)
            print(f"  * [{did}]: Riesgo Difuso = {r:.2f} / 10.0")

        print(f"\n{itinerario}")
        print("\nGUIA BASICA DE TRANSPORTE")
        for did, guia in guias_transporte.items():
            print(f"- {guia['nombre']}: {guia['medio_transporte']} (~{guia['tiempo_total_min']} min)")
        print("\n[OK] Pipeline finalizado con exito.\n")

    return {
        "perfil": perfil,
        "k": k,
        "beneficios_base": beneficios_base,
        "scores_difusos": scores_difusos,
        "resultado_ag": resultado_ag,
        "itinerario": itinerario,
        "guias_transporte": guias_transporte
    }


def main():
    parser = argparse.ArgumentParser(description="Pipeline CLI de Rutas en Lomas de Lima")
    parser.add_argument("--texto", type=str, default=None, help="Texto con preferencias del usuario")
    parser.add_argument("--demo", action="store_true", help="Ejecuta demostracion de prueba")
    args = parser.parse_args()

    texto = args.texto or "Quiero viajar 3 dias con 60 soles por senderos verdes de dificultad moderada."
    ejecutar_pipeline(texto, verbose=True)


if __name__ == "__main__":
    main()
