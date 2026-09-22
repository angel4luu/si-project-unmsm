"""
Modulo de Optimizacion Heuristica: Algoritmo Genetico.

Este modulo resuelve el problema combinatorio de seleccion y ordenamiento de rutas
(Orienteering Problem / Selective TSP) mediante un Algoritmo Genetico multiobjetivo:
- Representacion cromosomica: Permutacion completa de N=15 alelos con ventana activa K.
- Operadores geneticos: Order Crossover (OX) estandar, mutaciones compuestas y elitismo.
- Funcion de aptitud: Escalado adimensional relativo para presupuesto y tiempo.
- Atajo determinista: Bifurcacion directa en O(N) para horizonte unitario (K = 1).
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
    Motor de optimizacion heuristica basado en Algoritmo Genetico con cromosoma
    de longitud completa (N=15) y ventana activa K.
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
        lambda_presupuesto: float = 25.0,
        lambda_tiempo: float = 25.0,
        semilla: Optional[int] = None,
        nodo_base: Optional[Dict[str, float]] = None
    ):
        if semilla is not None:
            random.seed(semilla)

        self.destinos = destinos
        self.destinos_dict = {d["id"]: d for d in destinos}
        self.todos_ids = [d["id"] for d in destinos]
        self.n_total = len(self.todos_ids)
        self.scores_difusos = scores_difusos

        # Coordenadas del nodo base del usuario (por defecto: Centro de Lima -12.0464, -77.0428)
        self.nodo_base = nodo_base or {"lat": -12.0464, "lon": -77.0428}

        # Restringir K al rango valido [1, n_total]
        self.k = max(1, min(int(k), self.n_total))
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
        Genera un cromosoma de permutacion completa de los N=15 alelos del catalogo.
        Los primeros K genes constituyen la ventana activa (fenotipo).
        Los genes restantes [K:15] actuan como reserva genetica inactiva.
        """
        return random.sample(self.todos_ids, self.n_total)

    def obtener_ruta_activa(self, individuo: List[str]) -> List[str]:
        """
        Extrae la ventana activa de K destinos (fenotipo evaluado).
        """
        return individuo[:self.k]

    def calcular_distancia_ruta(self, ruta: List[str]) -> float:
        """
        Calcula la distancia acumulada de desplazamiento radial desde el nodo base (d0)
        hacia cada una de las K lomas del itinerario.
        Modelado logistico real: El turista realiza excursiones diurnas e independientes
        retornando cada dia a su alojamiento base.
        """
        if not ruta:
            return 0.0

        lat0, lon0 = self.nodo_base["lat"], self.nodo_base["lon"]
        distancia_total = 0.0
        for did in ruta:
            coords = self.destinos_dict[did]["coordenadas"]
            distancia_total += distancia_haversine(lat0, lon0, coords["lat"], coords["lon"])
        return distancia_total

    def fitness(self, individuo_o_ruta: List[str]) -> float:
        """
        Funcion de aptitud multiobjetivo con penalizaciones relativas adimensionales.
        F(x) = Beneficio_Difuso - beta*(DistanciaRadial/100) - lambda1*(DeltaPres/Pres)^2 - lambda2*(DeltaTiempo/Tiempo)^2 - Omega_unicidad
        """
        # Extraer ventana activa (fenotipo)
        ruta = self.obtener_ruta_activa(individuo_o_ruta)

        # 1. Beneficio acumulado por scores difusos
        beneficio_difuso = sum(self.scores_difusos.get(did, 5.0) for did in ruta)

        # 2. Descuento por distancia geografica de desplazamiento radial desde el nodo base
        distancia_km = self.calcular_distancia_ruta(ruta)
        costo_desplazamiento = self.beta_distancia * (distancia_km / 100.0)

        # 3. Penalizacion relativa adimensional por exceso de presupuesto
        costo_total = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in ruta)
        exceso_presupuesto = max(0.0, costo_total - self.presupuesto)
        denominador_presupuesto = max(1.0, self.presupuesto)
        omega_presupuesto = self.lambda_presupuesto * ((exceso_presupuesto / denominador_presupuesto) ** 2)

        # 4. Penalizacion relativa adimensional por tiempo disponible (8h utiles por dia)
        horas_totales = sum(self.destinos_dict[did].get("tiempo_estimado_horas", 4.0) for did in ruta)
        horas_disponibles = max(1.0, self.dias * 8.0)
        exceso_tiempo = max(0.0, horas_totales - horas_disponibles)
        omega_tiempo = self.lambda_tiempo * ((exceso_tiempo / horas_disponibles) ** 2)

        # 5. Penalizacion de seguridad por duplicados en la ventana activa
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
        Order Crossover (OX) clasico de permutacion completa sobre los N=15 alelos.
        Garantiza que ambos descendientes sean permutaciones estrictas sin duplicados.
        """
        n = self.n_total
        i1, i2 = sorted(random.sample(range(n), 2))

        def cruzar_un_lado(p1: List[str], p2: List[str]) -> List[str]:
            hijo = [None] * n
            # Heredar segmento continuo de p1
            hijo[i1:i2 + 1] = p1[i1:i2 + 1]
            genes_en_hijo = set(p1[i1:i2 + 1])

            # Recorrer p2 en orden circular a partir de i2 + 1
            candidatos_p2 = p2[i2 + 1:] + p2[:i2 + 1]
            posiciones_libres = [idx for idx in range(n) if hijo[idx] is None]

            pos_idx = 0
            for gen in candidatos_p2:
                if gen not in genes_en_hijo:
                    hijo[posiciones_libres[pos_idx]] = gen
                    genes_en_hijo.add(gen)
                    pos_idx += 1

            return hijo

        hijo1 = cruzar_un_lado(padre1, padre2)
        hijo2 = cruzar_un_lado(padre2, padre1)
        return hijo1, hijo2

    def _mutar(self, individuo: List[str]) -> List[str]:
        """
        Aplica mutacion adaptativa en el cromosoma de 15 alelos:
        - Swap Activo-Reserva: Sustituye una loma de la ventana activa por una de reserva.
        - Swap Activo-Activo: Reordena la secuencia de paradas activas para optimizar distancia.
        - Inversion 2-Opt: Invierte un subsegmento activo para desenredar cruces de ruta.
        """
        if random.random() > self.prob_mutacion:
            return list(individuo)

        hijo = list(individuo)
        r = random.random()

        # Estrategia 1: Swap Activo-Reserva (Sustitucion de destino, prob 40%)
        if r < 0.40 and self.k < self.n_total:
            idx_activo = random.randrange(self.k)
            idx_reserva = random.randrange(self.k, self.n_total)
            hijo[idx_activo], hijo[idx_reserva] = hijo[idx_reserva], hijo[idx_activo]

        # Estrategia 2: Swap Activo-Activo (Reordenamiento de ruta, prob 40%)
        elif r < 0.80 and self.k >= 2:
            i1, i2 = random.sample(range(self.k), 2)
            hijo[i1], hijo[i2] = hijo[i2], hijo[i1]

        # Estrategia 3: Inversion 2-Opt Activa (Optimizacion de tramo, prob 20%)
        elif self.k >= 3:
            i1, i2 = sorted(random.sample(range(self.k), 2))
            hijo[i1:i2 + 1] = reversed(hijo[i1:i2 + 1])

        # Caso por defecto si K=1 o condiciones no aplicaron
        else:
            i1, i2 = random.sample(range(self.n_total), 2)
            hijo[i1], hijo[i2] = hijo[i2], hijo[i1]

        return hijo

    def _atajo_determinista_k1(self) -> Dict[str, Any]:
        """
        Bifurcacion de control para horizonte unitario (K = 1).
        Selecciona de forma determinista la loma con mayor score difuso respetando presupuesto.
        """
        candidatos_presupuesto = [
            d for d in self.destinos
            if d.get("costo_estimado", 15.0) <= self.presupuesto
        ]

        universo = candidatos_presupuesto if candidatos_presupuesto else self.destinos
        mejor_destino = max(universo, key=lambda d: self.scores_difusos.get(d["id"], 0.0))
        mejor_id = mejor_destino["id"]

        # Construir cromosoma completo con el mejor gen en la posicion 0
        cromosoma = [mejor_id] + [did for did in self.todos_ids if did != mejor_id]
        fit_final = self.fitness(cromosoma)

        historial = [{
            "generacion": 1,
            "mejor_fitness": round(fit_final, 3),
            "promedio_fitness": round(fit_final, 3),
            "costo_mejor": round(mejor_destino.get("costo_estimado", 15.0), 2),
            "distancia_mejor": 0.0
        }]

        grafica = (
            "  Curva de Convergencia del Fitness (Generaciones):\n"
            f"  {fit_final:6.2f} ^------------------------------------------\n"
            f"  {fit_final:6.2f} | ******************************************\n"
            "         +---------------------------------------->\n"
            "         [Atajo Determinista K=1: Seleccion Directa]"
        )

        return {
            "ruta_ids": [mejor_id],
            "destinos_ordenados": [mejor_destino],
            "fitness": round(fit_final, 3),
            "costo_total": round(mejor_destino.get("costo_estimado", 15.0), 2),
            "distancia_total_km": 0.0,
            "tiempo_estimado_horas": round(mejor_destino.get("tiempo_estimado_horas", 4.0), 2),
            "tramos": [],
            "historial": historial,
            "grafica_ascii": grafica,
            "metodo": "atajo_determinista"
        }

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
        Ejecuta el ciclo evolutivo del Algoritmo Genetico o el atajo determinista si K=1.
        """
        # Bifurcacion de control para K = 1
        if self.k == 1:
            if verbose:
                print("  [Bifurcacion K=1] Atajo determinista activado (seleccion directa O(N)).")
            return self._atajo_determinista_k1()

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

            # Registrar metricas de la generacion sobre la ventana activa
            ruta_mejor = self.obtener_ruta_activa(mejor_historico)
            costo_gen = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in ruta_mejor)
            dist_gen = self.calcular_distancia_ruta(ruta_mejor)

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

        # Extraer fenotipo optimo
        ruta_final = self.obtener_ruta_activa(mejor_historico)
        costo_final = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in ruta_final)
        horas_final = sum(self.destinos_dict[did].get("tiempo_estimado_horas", 4.0) for did in ruta_final)
        distancia_final = self.calcular_distancia_ruta(ruta_final)
        grafica_ascii = self._dibujar_grafica_ascii(historial)

        # Desglose de traslados radiales desde el nodo base (d0)
        tramos = []
        lat0, lon0 = self.nodo_base["lat"], self.nodo_base["lon"]
        for did in ruta_final:
            d_destino = self.destinos_dict[did]
            c2 = d_destino["coordenadas"]
            d_km = distancia_haversine(lat0, lon0, c2["lat"], c2["lon"])
            tramos.append({
                "de": "Alojamiento (Nodo Base)",
                "hacia": d_destino["nombre"],
                "distancia_km": round(d_km, 2)
            })

        return {
            "ruta_ids": ruta_final,
            "destinos_ordenados": [self.destinos_dict[did] for did in ruta_final],
            "cromosoma_completo": mejor_historico,
            "fitness": round(mejor_fitness_historico, 3),
            "costo_total": round(costo_final, 2),
            "distancia_total_km": round(distancia_final, 2),
            "tiempo_estimado_horas": round(horas_final, 2),
            "tramos": tramos,
            "historial": historial,
            "grafica_ascii": grafica_ascii,
            "metodo": "algoritmo_genetico"
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
    verbose: bool = False,
    nodo_base: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Punto de entrada estandar para ejecutar la optimizacion por Algoritmo Genetico.
    Mantiene compatibilidad total con main.py y tests.
    """
    opt = LomasGeneticOptimizer(
        destinos=destinos,
        scores_difusos=scores_difusos,
        k=k,
        presupuesto=presupuesto,
        dias_disponibles=dias_disponibles,
        generaciones=generaciones,
        tam_poblacion=tam_poblacion,
        semilla=semilla,
        nodo_base=nodo_base
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

    print("  MODULO HEURISTICO: OPTIMIZACION MEDIANTE ALGORITMO GENETICO\n")
    print(f"  Parametros de Entrada:")
    print(f"  - Destinos a seleccionar (K):  {args.k}")
    print(f"  - Presupuesto maximo:         S/ {args.presupuesto:.2f}")
    print(f"  - Dias disponibles:           {args.dias}")
    print(f"  - Generaciones:               {args.gen}")
    print(f"  - Tamano de Poblacion:        {args.pop}")
    print("\n")
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

    print("\n")
    print(resultado["grafica_ascii"])
    print("\n")
    print("  RESULTADOS DE LA RUTA OPTIMIZADA:")
    print(f"  - Metodo de Resolucion:    {resultado.get('metodo', 'algoritmo_genetico')}")
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
