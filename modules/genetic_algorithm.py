"""
Modulo de Optimizacion Heuristica: Algoritmo Genetico.

Este modulo resuelve el problema combinatorio de seleccion y ordenamiento de rutas
(Orienteering Problem / Selective TSP) mediante un Algoritmo Genetico multiobjetivo:
- Maximiza la calidad ecoturistica de los destinos (Scores Difusos Mamdani).
- Minimiza la distancia geografica total de traslado (Formula de Haversine).
- Penaliza cuadraticamente el exceso de presupuesto y tiempo disponible.
"""

import os
import sys
import json
import math
import random
import argparse
from typing import List, Dict, Any, Tuple, Optional

# Compatibilidad de codificacion UTF-8 para consola en Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia ortodromica en kilometros entre dos coordenadas
    geograficas utilizando la formula de Haversine.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    r = 6371.0  # Radio medio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return r * c


class LomasGeneticOptimizer:
    """
    Motor de optimizacion heuristica basado en Algoritmo Genetico para rutas en lomas.
    """

    def __init__(
        self,
        destinos: List[Dict[str, Any]],
        scores_difusos: Dict[str, float],
        k: int,
        presupuesto: float,
        dias_disponibles: int,
        generaciones: int = 50,
        tam_poblacion: int = 40,
        prob_cruce: float = 0.85,
        prob_mutacion: float = 0.30,
        elitismo: int = 2,
        torneo_k: int = 3,
        beta_distancia: float = 1.0,
        lambda_presupuesto: float = 1.0,
        lambda_tiempo: float = 1.0,
        semilla: Optional[int] = None
    ):
        if semilla is not None:
            random.seed(semilla)

        self.destinos = destinos
        self.destinos_dict = {d["id"]: d for d in destinos}
        self.todos_ids = [d["id"] for d in destinos]
        self.scores_difusos = scores_difusos

        # Restringir K al rango valido [1, len(destinos)]
        self.k = max(1, min(int(k), len(destinos)))
        self.presupuesto = float(presupuesto)
        self.dias = max(1, int(dias_disponibles))

        self.generaciones = max(1, int(generaciones))
        self.tam_poblacion = max(4, int(tam_poblacion))
        self.prob_cruce = float(prob_cruce)
        self.prob_mutacion = float(prob_mutacion)
        self.elitismo = min(elitismo, self.tam_poblacion // 2)
        self.torneo_k = max(2, min(torneo_k, self.tam_poblacion))

        self.beta_distancia = float(beta_distancia)
        self.lambda_presupuesto = float(lambda_presupuesto)
        self.lambda_tiempo = float(lambda_tiempo)

    def _generar_individuo(self) -> List[str]:
        """
        Genera un cromosoma inicial: subconjunto de K destinos aleatorios sin repeticion.
        """
        return random.sample(self.todos_ids, self.k)

    def calcular_distancia_ruta(self, ruta: List[str]) -> float:
        """
        Calcula la distancia total acumulada en kilometros entre paradas consecutivas.
        Si la ruta tiene 1 destino, la distancia de traslado inter-loma es 0.0 km.
        """
        if len(ruta) <= 1:
            return 0.0

        distancia_total = 0.0
        for i in range(len(ruta) - 1):
            c1 = self.destinos_dict[ruta[i]]["coordenadas"]
            c2 = self.destinos_dict[ruta[i + 1]]["coordenadas"]
            distancia_total += distancia_haversine(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
        return distancia_total

    def fitness(self, ruta: List[str]) -> float:
        """
        Funcion de aptitud multiobjetivo con penalizaciones cuadraticas.
        F(x) = Beneficio_Difuso - beta*(Distancia/100) - lambda1*Omega_pres - lambda2*Omega_tiempo - Omega_unicidad
        """
        # 1. Beneficio acumulado por scores difusos
        beneficio_difuso = sum(self.scores_difusos.get(did, 5.0) for did in ruta)

        # 2. Descuento por distancia geografica de traslado
        distancia_km = self.calcular_distancia_ruta(ruta)
        costo_desplazamiento = self.beta_distancia * (distancia_km / 100.0)

        # 3. Penalizacion cuadratica por exceso de presupuesto
        costo_total = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in ruta)
        exceso_presupuesto = max(0.0, costo_total - self.presupuesto)
        omega_presupuesto = self.lambda_presupuesto * (exceso_presupuesto ** 2)

        # 4. Penalizacion cuadratica por tiempo disponible (8 horas utiles por dia)
        horas_totales = sum(self.destinos_dict[did].get("tiempo_estimado_horas", 4.0) for did in ruta)
        horas_disponibles = self.dias * 8.0
        exceso_tiempo = max(0.0, horas_totales - horas_disponibles)
        omega_tiempo = self.lambda_tiempo * (exceso_tiempo ** 2)

        # 5. Penalizacion estricta por destinos duplicados (garantia de unicidad)
        destinos_unicos = len(set(ruta))
        omega_unicidad = 1000.0 * (len(ruta) - destinos_unicos)

        valor_fitness = beneficio_difuso - costo_desplazamiento - omega_presupuesto - omega_tiempo - omega_unicidad
        return valor_fitness

    def _seleccion_torneo(self, poblacion: List[List[str]]) -> List[str]:
        """
        Seleccion por torneo estocastico de tamano k_torneo.
        """
        aspirantes = random.sample(poblacion, self.torneo_k)
        mejor = max(aspirantes, key=self.fitness)
        return list(mejor)

    def _crossover_ox(self, padre1: List[str], padre2: List[str]) -> Tuple[List[str], List[str]]:
        """
        Order Crossover (OX) adaptado a subconjuntos de longitud K.
        Preserva un segmento continuo del primer padre y completa los genes
        restantes respetando el orden relativo del segundo padre sin generar duplicados.
        """
        if self.k <= 2:
            return list(padre1), list(padre2)

        # Seleccionar dos puntos de corte aleatorios
        i1, i2 = sorted(random.sample(range(self.k), 2))

        def cruzar_un_lado(p1: List[str], p2: List[str]) -> List[str]:
            hijo = [None] * self.k
            # Heredar segmento continuo de p1
            hijo[i1:i2 + 1] = p1[i1:i2 + 1]
            genes_en_hijo = set(p1[i1:i2 + 1])

            # Orden de busqueda en p2 comenzando inmediatamente despues de i2
            candidatos_p2 = p2[i2 + 1:] + p2[:i2 + 1]
            posiciones_libres = [idx for idx in range(self.k) if hijo[idx] is None]

            pos_idx = 0
            for gen in candidatos_p2:
                if gen not in genes_en_hijo and pos_idx < len(posiciones_libres):
                    hijo[posiciones_libres[pos_idx]] = gen
                    genes_en_hijo.add(gen)
                    pos_idx += 1

            # Si faltan genes por completar (debido a alta interseccion de padres)
            if pos_idx < len(posiciones_libres):
                disponibles = [g for g in self.todos_ids if g not in genes_en_hijo]
                random.shuffle(disponibles)
                for gen in disponibles:
                    if pos_idx < len(posiciones_libres):
                        hijo[posiciones_libres[pos_idx]] = gen
                        genes_en_hijo.add(gen)
                        pos_idx += 1
                    else:
                        break

            return hijo

        hijo1 = cruzar_un_lado(padre1, padre2)
        hijo2 = cruzar_un_lado(padre2, padre1)
        return hijo1, hijo2

    def _mutacion_swap(self, individuo: List[str]) -> List[str]:
        """
        Mutacion por intercambio: Permuta las posiciones de dos destinos en la ruta.
        Optimiza el orden de visita para reducir la distancia de recorrido.
        """
        if len(individuo) < 2:
            return list(individuo)
        hijo = list(individuo)
        i1, i2 = random.sample(range(len(hijo)), 2)
        hijo[i1], hijo[i2] = hijo[i2], hijo[i1]
        return hijo

    def _mutacion_reemplazo(self, individuo: List[str]) -> List[str]:
        """
        Mutacion por sustitucion: Reemplaza una loma de la ruta por otra del catalogo no visitada.
        Permite explorar nuevas combinaciones de destinos para optimizar el score difuso y costo.
        """
        genes_actuales = set(individuo)
        disponibles = [did for did in self.todos_ids if did not in genes_actuales]
        if not disponibles:
            return list(individuo)

        hijo = list(individuo)
        pos = random.randrange(len(hijo))
        nuevo_destino = random.choice(disponibles)
        hijo[pos] = nuevo_destino
        return hijo

    def _mutacion_inversion(self, individuo: List[str]) -> List[str]:
        """
        Mutacion por inversion (2-Opt local): Invierte un subsegmento de la ruta.
        Corrige cruces en el trazado geografico de la ruta.
        """
        if len(individuo) < 3:
            return self._mutacion_swap(individuo)
        hijo = list(individuo)
        i1, i2 = sorted(random.sample(range(len(hijo)), 2))
        hijo[i1:i2 + 1] = reversed(hijo[i1:i2 + 1])
        return hijo

    def _mutar(self, individuo: List[str]) -> List[str]:
        """
        Aplica uno de los operadores de mutacion de acuerdo a sus probabilidades relativas.
        """
        if random.random() > self.prob_mutacion:
            return list(individuo)

        r = random.random()
        if r < 0.40:
            return self._mutacion_swap(individuo)
        elif r < 0.80:
            return self._mutacion_reemplazo(individuo)
        else:
            return self._mutacion_inversion(individuo)

    def _dibujar_grafica_ascii(self, historial: List[Dict[str, Any]], ancho: int = 40, alto: int = 8) -> str:
        """
        Genera una representacion grafica de la curva de convergencia del fitness
        en arte ASCII para visualizacion en terminal.
        """
        if not historial:
            return ""

        valores = [h["mejor_fitness"] for h in historial]
        min_v = min(valores)
        max_v = max(valores)
        rango = max_v - min_v if max_v != min_v else 1.0

        # Muestrear a lo largo del ancho disponible
        n_puntos = len(valores)
        muestras = []
        for col in range(ancho):
            idx = int((col / (ancho - 1)) * (n_puntos - 1)) if ancho > 1 else 0
            muestras.append(valores[idx])

        lineas = []
        lineas.append("  Curva de Convergencia del Fitness (Generaciones):")
        lineas.append(f"  {max_v:6.2f} ^" + "-" * (ancho + 2))

        for row in range(alto - 1, -1, -1):
            umbral_inferior = min_v + (row / alto) * rango
            umbral_superior = min_v + ((row + 1) / alto) * rango
            fila_caracteres = []

            for val in muestras:
                if umbral_inferior <= val <= umbral_superior:
                    fila_caracteres.append("*")
                elif val > umbral_superior:
                    fila_caracteres.append("|")
                else:
                    fila_caracteres.append(" ")

            valor_eje = f"  {umbral_inferior:6.2f} | " + "".join(fila_caracteres)
            lineas.append(valor_eje)

        lineas.append("         +" + "-" * ancho + ">")
        lineas.append(f"         Gen 1{' ' * (ancho - 12)}Gen {len(valores)}")
        return "\n".join(lineas)

    def optimizar(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Ejecuta el ciclo evolutivo completo del Algoritmo Genetico.
        """
        poblacion = [self._generar_individuo() for _ in range(self.tam_poblacion)]
        mejor_historico = None
        mejor_fitness_historico = -float("inf")
        historial = []

        for gen in range(1, self.generaciones + 1):
            # Evaluar y ordenar poblacion por fitness descendente
            poblacion.sort(key=self.fitness, reverse=True)
            mejor_gen = poblacion[0]
            fit_mejor_gen = self.fitness(mejor_gen)
            fit_promedio = sum(self.fitness(ind) for ind in poblacion) / len(poblacion)

            # Actualizar mejor individuo global
            if fit_mejor_gen > mejor_fitness_historico:
                mejor_fitness_historico = fit_mejor_gen
                mejor_historico = list(mejor_gen)

            # Registrar metricas de la generacion
            costo_gen = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in mejor_historico)
            dist_gen = self.calcular_distancia_ruta(mejor_historico)

            historial.append({
                "generacion": gen,
                "mejor_fitness": round(mejor_fitness_historico, 3),
                "promedio_fitness": round(fit_promedio, 3),
                "costo_mejor": round(costo_gen, 2),
                "distancia_mejor": round(dist_gen, 2)
            })

            # Imprimir traza de convergencia si verbose esta activo
            if verbose and (gen == 1 or gen % 10 == 0 or gen == self.generaciones):
                print(f"  [Gen {gen:03d}] Mejor Fit: {mejor_fitness_historico:7.3f} | "
                      f"Promedio: {fit_promedio:7.3f} | Costo: S/{costo_gen:5.1f} | Dist: {dist_gen:5.1f} km")

            # Nueva poblacion con elitismo
            nueva_poblacion = [list(poblacion[i]) for i in range(self.elitismo)]

            # Reproduccion
            while len(nueva_poblacion) < self.tam_poblacion:
                p1 = self._seleccion_torneo(poblacion)
                p2 = self._seleccion_torneo(poblacion)

                if random.random() < self.prob_cruce:
                    h1, h2 = self._crossover_ox(p1, p2)
                else:
                    h1, h2 = list(p1), list(p2)

                h1 = self._mutar(h1)
                nueva_poblacion.append(h1)

                if len(nueva_poblacion) < self.tam_poblacion:
                    h2 = self._mutar(h2)
                    nueva_poblacion.append(h2)

            poblacion = nueva_poblacion

        # Calculo de metricas finales de la mejor solucion
        costo_final = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in mejor_historico)
        horas_final = sum(self.destinos_dict[did].get("tiempo_estimado_horas", 4.0) for did in mejor_historico)
        distancia_final = self.calcular_distancia_ruta(mejor_historico)
        grafica_ascii = self._dibujar_grafica_ascii(historial)

        # Desglose tramo a tramo
        tramos = []
        if len(mejor_historico) > 1:
            for i in range(len(mejor_historico) - 1):
                d_origen = self.destinos_dict[mejor_historico[i]]
                d_destino = self.destinos_dict[mejor_historico[i + 1]]
                c1 = d_origen["coordenadas"]
                c2 = d_destino["coordenadas"]
                d_km = distancia_haversine(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
                tramos.append({
                    "de": d_origen["nombre"],
                    "hacia": d_destino["nombre"],
                    "distancia_km": round(d_km, 2)
                })

        return {
            "ruta_ids": mejor_historico,
            "destinos_ordenados": [self.destinos_dict[did] for did in mejor_historico],
            "fitness": round(mejor_fitness_historico, 3),
            "costo_total": round(costo_final, 2),
            "distancia_total_km": round(distancia_final, 2),
            "tiempo_estimado_horas": round(horas_final, 2),
            "tramos": tramos,
            "historial": historial,
            "grafica_ascii": grafica_ascii
        }


def optimizar_ruta_lomas(
    destinos: List[Dict[str, Any]],
    scores_difusos: Dict[str, float],
    k: int,
    presupuesto: float,
    dias_disponibles: int,
    generaciones: int = 50,
    tam_poblacion: int = 40,
    semilla: Optional[int] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Punto de entrada estandar para ejecutar la optimizacion por Algoritmo Genetico.
    """
    opt = LomasGeneticOptimizer(
        destinos=destinos,
        scores_difusos=scores_difusos,
        k=k,
        presupuesto=presupuesto,
        dias_disponibles=dias_disponibles,
        generaciones=generaciones,
        tam_poblacion=tam_poblacion,
        semilla=semilla
    )
    return opt.optimizar(verbose=verbose)


def main():
    """
    Punto de entrada autonomo para ejecucion por terminal con analisis completo.
    """
    parser = argparse.ArgumentParser(
        description="Modulo Heuristico: Algoritmo Genetico para Rutas en Lomas de Lima"
    )
    parser.add_argument("--k", type=int, default=3, help="Numero de destinos a seleccionar (K)")
    parser.add_argument("--presupuesto", type=float, default=60.0, help="Presupuesto maximo en Soles")
    parser.add_argument("--dias", type=int, default=3, help="Dias disponibles para la ruta")
    parser.add_argument("--gen", type=int, default=50, help="Numero de generaciones evolutivas")
    parser.add_argument("--pop", type=int, default=40, help="Tamano de la poblacion")
    parser.add_argument("--semilla", type=int, default=None, help="Semilla pseudoaleatoria opcional")
    parser.add_argument("--silencioso", action="store_true", help="Oculta el detalle por generacion")
    args = parser.parse_args()

    # Cargar catalogo oficial
    ruta_json = os.path.join(os.path.dirname(__file__), "..", "data", "destinos.json")
    if not os.path.exists(ruta_json):
        print(f"Error: No se encontro el archivo de datos en {ruta_json}")
        sys.exit(1)

    with open(ruta_json, "r", encoding="utf-8") as f:
        destinos = json.load(f)

    # Scores difusos de ejemplo para ejecucion autonoma (si no se conecta fuzzy)
    scores_ejemplo = {
        d["id"]: round(8.5 - (d.get("saturacion_base", 0.5) * 3.0) + (d.get("seguridad_base", 5.0) * 0.3), 2)
        for d in destinos
    }

    print("  MODULO HEURISTICO: OPTIMIZACION MEDIANTE ALGORITMO GENETICO")
    print(f"  Parametros de Entrada:")
    print(f"  - Destinos a seleccionar (K):  {args.k}")
    print(f"  - Presupuesto maximo:         S/ {args.presupuesto:.2f}")
    print(f"  - Dias disponibles:           {args.dias}")
    print(f"  - Generaciones:               {args.gen}")
    print(f"  - Tamano de Poblacion:        {args.pop}")
    print("\n\n")
    print("  Iniciando proceso evolutivo...")

    opt = LomasGeneticOptimizer(
        destinos=destinos,
        scores_difusos=scores_ejemplo,
        k=args.k,
        presupuesto=args.presupuesto,
        dias_disponibles=args.dias,
        generaciones=args.gen,
        tam_poblacion=args.pop,
        semilla=args.semilla
    )

    resultado = opt.optimizar(verbose=not args.silencioso)

    print("\n\n")
    print(resultado["grafica_ascii"])
    print("\n\n")
    print("  RESULTADOS DE LA RUTA OPTIMIZADA:")
    print(f"  - Secuencia de IDs:        {' -> '.join(resultado['ruta_ids'])}")
    print(f"  - Aptitud Final (Fitness): {resultado['fitness']:.3f}")
    print(f"  - Costo Total Estimado:    S/ {resultado['costo_total']:.2f} (Limite: S/ {args.presupuesto:.2f})")
    print(f"  - Distancia Inter-Loma:    {resultado['distancia_total_km']:.2f} km")
    print(f"  - Tiempo de Senderos:      {resultado['tiempo_estimado_horas']:.2f} horas")

    cumple_presupuesto = resultado["costo_total"] <= args.presupuesto
    estado_presupuesto = "[CUMPLE]" if cumple_presupuesto else "[EXCEDE (Penalizado)]"
    print(f"  - Estado del Presupuesto:  {estado_presupuesto}")

    print("\n  Detalle Parada por Parada:")
    for idx, d in enumerate(resultado["destinos_ordenados"], start=1):
        print(f"    Parada {idx}: [{d['id']}] {d['nombre']} ({d['distrito']})")
        print(f"              Dificultad: {d['dificultad']} | Costo: S/ {d['costo_estimado']:.2f} | Tiempo: {d['tiempo_estimado_horas']}h")

    if resultado["tramos"]:
        print("\n  Tramos de Desplazamiento Geografico:")
        for t in resultado["tramos"]:
            print(f"    - De {t['de']} hasta {t['hacia']}: {t['distancia_km']:.2f} km")

    print("\n")


if __name__ == "__main__":
    main()
