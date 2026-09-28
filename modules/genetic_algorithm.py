"""
Modulo de Optimizacion Heuristica: Algoritmo Genetico Hibrido.

Este modulo resuelve el problema combinatorio de seleccion y ordenamiento de rutas
(Orienteering Problem / Selective TSP) con dos componentes de logica difusa:
- Componente 1 (en cromosoma): 3 genes reales evolutivos que definen la exigencia.
- Componente 2 (en fitness): Evaluacion de riesgo difuso Mamdani por cada loma.

Estructura del cromosoma hibrido (18 genes):
- Genes 0-14: Permutacion de N=15 lomas con ventana activa K.
- Gen 15: Horas de recorrido [1.0, 6.0].
- Gen 16: Cobertura de zona [0.0, 1.0].
- Gen 17: Extension del circuito [1.0, 10.0] km.
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

from modules.fuzzy_module import (
    evaluar_exigencia,
    evaluar_riesgo_loma,
    calcular_riesgos_todos_destinos
)


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
    Motor de optimizacion heuristica basado en Algoritmo Genetico Hibrido
    con cromosoma de 18 genes (15 permutacion + 3 reales) y ventana activa K.
    """

    def __init__(
        self,
        destinos: List[Dict[str, Any]],
        beneficios_base: Optional[Dict[str, float]] = None,
        scores_difusos: Optional[Dict[str, float]] = None,
        k: int = 3,
        presupuesto: float = 60.0,
        dias_disponibles: int = 3,
        generaciones: int = 50,
        tam_poblacion: int = 40,
        prob_cruce: float = 0.85,
        prob_mutacion: float = 0.30,
        elitismo: int = 2,
        torneo_k: int = 3,
        beta_distancia: float = 1.0,
        lambda_presupuesto: float = 25.0,
        lambda_tiempo: float = 25.0,
        gamma_riesgo: float = 1.5,
        delta_exigencia: float = 2.0,
        semilla: Optional[int] = None,
        nodo_base: Optional[Dict[str, float]] = None
    ):
        self.semilla = semilla
        if semilla is not None:
            random.seed(semilla)

        self.destinos = destinos
        self.destinos_dict = {d["id"]: d for d in destinos}
        self.todos_ids = [d["id"] for d in destinos]
        self.n_total = len(self.todos_ids)

        # Beneficios base intrinsecos (soporta scores_difusos por compatibilidad)
        if beneficios_base is not None:
            self.beneficios_base = dict(beneficios_base)
        elif scores_difusos is not None:
            self.beneficios_base = dict(scores_difusos)
        else:
            self.beneficios_base = {d["id"]: 7.0 for d in destinos}

        # Coordenadas del nodo base del usuario (Centro de Lima por defecto)
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
        self.gamma_riesgo = float(gamma_riesgo)
        self.delta_exigencia = float(delta_exigencia)

        # Precalculo en cache de riesgos difusos por cada loma
        self.riesgos_lomas = calcular_riesgos_todos_destinos(self.destinos)

    def _generar_individuo(self) -> list:
        """
        Genera un cromosoma hibrido de 18 genes:
        - Genes 0-14: permutacion de los N=15 alelos del catalogo.
        - Gen 15: horas_recorrido en [1.0, 6.0].
        - Gen 16: cobertura_zona en [0.0, 1.0].
        - Gen 17: extension_circuito en [1.0, 10.0].
        """
        permutacion = random.sample(self.todos_ids, self.n_total)
        genes_reales = [
            random.uniform(1.0, 6.0),
            random.uniform(0.0, 1.0),
            random.uniform(1.0, 10.0)
        ]
        return permutacion + genes_reales

    def _extraer_genes_reales(self, individuo: list) -> Tuple[float, float, float]:
        """
        Extrae los 3 genes reales (posiciones 15, 16, 17) del cromosoma hibrido.
        Si el individuo solo tiene 15 genes, retorna valores moderados por defecto.
        """
        if len(individuo) >= self.n_total + 3:
            horas = float(individuo[self.n_total])
            cobertura = float(individuo[self.n_total + 1])
            extension = float(individuo[self.n_total + 2])
        else:
            horas, cobertura, extension = 3.5, 0.50, 5.0
        return horas, cobertura, extension

    def obtener_ruta_activa(self, individuo: list) -> List[str]:
        """
        Extrae la ventana activa de K destinos (fenotipo evaluado).
        """
        return individuo[:self.k]

    def calcular_distancia_ruta(self, ruta: List[str]) -> float:
        """
        Calcula la distancia acumulada de desplazamiento radial desde el nodo base (d0)
        hacia cada una de las K lomas del itinerario.
        """
        if not ruta:
            return 0.0

        lat0, lon0 = self.nodo_base["lat"], self.nodo_base["lon"]
        distancia_total = 0.0
        for did in ruta:
            coords = self.destinos_dict[did]["coordenadas"]
            distancia_total += distancia_haversine(lat0, lon0, coords["lat"], coords["lon"])
        return distancia_total

    def fitness(self, individuo: list) -> float:
        """
        Funcion de aptitud multiobjetivo con dos componentes de logica difusa:
        F(x) = + Suma beneficio_base(loma_i)
               + delta * nivel_exigencia
               - gamma * (Suma riesgo_difuso / 10) * factor_tolerancia
               - beta * (DistanciaRadial / 100)
               - lambda1 * (DeltaPres / Pres)^2
               - lambda2 * (DeltaTiempo / Tiempo)^2
               - Omega_unicidad
        """
        # Extraer ventana activa (fenotipo de permutacion)
        ruta = self.obtener_ruta_activa(individuo)

        # 1. Beneficio base acumulado (puntaje intrinseco de las lomas activas)
        beneficio_base = sum(self.beneficios_base.get(did, 5.0) for did in ruta)

        # Componente 1: Nivel de Exigencia (genes reales -> Mamdani)
        horas, cobertura, extension = self._extraer_genes_reales(individuo)
        nivel_exigencia = evaluar_exigencia(horas, cobertura, extension)
        bono_exigencia = self.delta_exigencia * nivel_exigencia

        # Componente 2: Penalizacion por Riesgo (datos de lomas -> Mamdani)
        riesgo_acumulado = sum(self.riesgos_lomas.get(did, 5.0) for did in ruta)
        # Factor de tolerancia: un perfil mas exigente tolera hasta un 30% mas de riesgo
        factor_tolerancia = 1.0 - (nivel_exigencia * 0.3)
        penalizacion_riesgo = self.gamma_riesgo * (riesgo_acumulado / 10.0) * factor_tolerancia

        # 2. Descuento por distancia geografica de desplazamiento radial
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

        valor_fitness = (
            beneficio_base
            + bono_exigencia
            - penalizacion_riesgo
            - costo_desplazamiento
            - omega_presupuesto
            - omega_tiempo
            - omega_unicidad
        )
        return valor_fitness

    def _seleccion_torneo(self, poblacion: List[list]) -> list:
        """
        Seleccion por torneo estocastico de tamano torneo_k.
        """
        aspirantes = random.sample(poblacion, self.torneo_k)
        mejor = max(aspirantes, key=self.fitness)
        return list(mejor)

    def _crossover_hibrido(self, padre1: list, padre2: list) -> Tuple[list, list]:
        """
        Crossover hibrido adaptado:
        - Genes 0-14 (permutacion): Order Crossover (OX) clasico.
        - Genes 15-17 (reales): Blend Crossover (BLX-alpha) con alpha=0.3.
        """
        n = self.n_total
        i1, i2 = sorted(random.sample(range(n), 2))

        def cruzar_ox(p1: list, p2: list) -> list:
            hijo = [None] * n
            hijo[i1:i2 + 1] = p1[i1:i2 + 1]
            genes_en_hijo = set(p1[i1:i2 + 1])

            candidatos_p2 = p2[i2 + 1:] + p2[:i2 + 1]
            posiciones_libres = [idx for idx in range(n) if hijo[idx] is None]

            pos_idx = 0
            for gen in candidatos_p2:
                if gen not in genes_en_hijo:
                    hijo[posiciones_libres[pos_idx]] = gen
                    genes_en_hijo.add(gen)
                    pos_idx += 1

            return hijo

        perm1 = padre1[:n]
        perm2 = padre2[:n]
        hijo1_perm = cruzar_ox(perm1, perm2)
        hijo2_perm = cruzar_ox(perm2, perm1)

        # BLX-alpha para genes reales
        alpha = 0.3
        reales1 = padre1[n:] if len(padre1) >= n + 3 else [3.5, 0.5, 5.0]
        reales2 = padre2[n:] if len(padre2) >= n + 3 else [3.5, 0.5, 5.0]
        limites = [(1.0, 6.0), (0.0, 1.0), (1.0, 10.0)]

        hijo1_reales = []
        hijo2_reales = []
        for j in range(3):
            v1, v2 = float(reales1[j]), float(reales2[j])
            d = abs(v1 - v2)
            c_min = min(v1, v2) - alpha * d
            c_max = max(v1, v2) + alpha * d
            lo, hi = limites[j]

            val1 = random.uniform(max(lo, c_min), min(hi, c_max))
            val2 = random.uniform(max(lo, c_min), min(hi, c_max))

            hijo1_reales.append(float(val1))
            hijo2_reales.append(float(val2))

        return hijo1_perm + hijo1_reales, hijo2_perm + hijo2_reales

    def _crossover_ox(self, padre1: list, padre2: list) -> Tuple[list, list]:
        """Alias compatible con tests anteriores."""
        return self._crossover_hibrido(padre1, padre2)

    def _mutar(self, individuo: list) -> list:
        """
        Aplica mutacion adaptativa en el cromosoma hibrido de 18 genes:
        - Swap Activo-Reserva (30%): Sustituye una loma activa por una de reserva.
        - Swap Activo-Activo (30%): Reordena la secuencia de paradas activas.
        - Inversion 2-Opt (15%): Invierte un subsegmento activo para desenredar cruces.
        - Mutacion Gaussiana (25%): Perturba genes reales con distribucion N(0, sigma).
        """
        if random.random() > self.prob_mutacion:
            return list(individuo)

        hijo = list(individuo)
        # Asegurar longitud completa
        if len(hijo) < self.n_total + 3:
            hijo = hijo[:self.n_total] + [3.5, 0.5, 5.0]

        r = random.random()

        # Estrategia 1: Swap Activo-Reserva (probabilidad 30%)
        if r < 0.30 and self.k < self.n_total:
            idx_activo = random.randrange(self.k)
            idx_reserva = random.randrange(self.k, self.n_total)
            hijo[idx_activo], hijo[idx_reserva] = hijo[idx_reserva], hijo[idx_activo]

        # Estrategia 2: Swap Activo-Activo (probabilidad 30%)
        elif r < 0.60 and self.k >= 2:
            i1, i2 = random.sample(range(self.k), 2)
            hijo[i1], hijo[i2] = hijo[i2], hijo[i1]

        # Estrategia 3: Inversion 2-Opt Activa (probabilidad 15%)
        elif r < 0.75 and self.k >= 3:
            i1, i2 = sorted(random.sample(range(self.k), 2))
            hijo[i1:i2 + 1] = reversed(hijo[i1:i2 + 1])

        # Estrategia 4: Mutacion Gaussiana en Genes Reales (probabilidad 25%)
        else:
            sigmas = [0.5, 0.1, 0.9]  # ~10% del rango de cada variable
            limites = [(1.0, 6.0), (0.0, 1.0), (1.0, 10.0)]
            for j in range(3):
                idx = self.n_total + j
                ruido = random.gauss(0, sigmas[j])
                nuevo_val = float(hijo[idx]) + ruido
                lo, hi = limites[j]
                hijo[idx] = max(lo, min(hi, nuevo_val))

        return hijo

    def _atajo_determinista_k1(self) -> Dict[str, Any]:
        """
        Bifurcacion de control determinista para horizonte unitario (K = 1).
        Selecciona la loma con mejor balance beneficio-riesgo dentro del presupuesto.
        """
        candidatos_presupuesto = [
            d for d in self.destinos
            if d.get("costo_estimado", 15.0) <= self.presupuesto
        ]
        universo = candidatos_presupuesto if candidatos_presupuesto else self.destinos

        # Evaluar puntaje neto: beneficio_base - 0.15 * riesgo
        def score_neto(d: Dict[str, Any]) -> float:
            did = d["id"]
            b = self.beneficios_base.get(did, 5.0)
            r = self.riesgos_lomas.get(did, 5.0)
            return b - (0.15 * r)

        mejor_destino = max(universo, key=score_neto)
        mejor_id = mejor_destino["id"]

        # Cromosoma de 18 genes: mejor gen en pos 0, resto en reserva, genes reales moderados
        genes_reales_default = [3.5, 0.50, 5.0]
        cromosoma = [mejor_id] + [did for did in self.todos_ids if did != mejor_id] + genes_reales_default
        fit_final = self.fitness(cromosoma)
        nivel_exig = evaluar_exigencia(*genes_reales_default)

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
            "cromosoma_completo": cromosoma,
            "genes_reales": {
                "horas_recorrido": genes_reales_default[0],
                "cobertura_zona": genes_reales_default[1],
                "extension_circuito": genes_reales_default[2],
            },
            "nivel_exigencia": round(nivel_exig, 4),
            "riesgos_ruta": {mejor_id: self.riesgos_lomas.get(mejor_id, 5.0)},
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
        Genera una representacion grafica de la curva de convergencia del fitness en arte ASCII.
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
        Ejecuta el ciclo evolutivo del Algoritmo Genetico Hibrido o el atajo determinista si K=1.
        """
        if self.semilla is not None:
            random.seed(self.semilla)

        if self.k == 1:
            if verbose:
                print("  [Bifurcacion K=1] Atajo determinista activado (seleccion directa O(N)).")
            return self._atajo_determinista_k1()

        poblacion = [self._generar_individuo() for _ in range(self.tam_poblacion)]
        mejor_historico = None
        mejor_fitness_historico = -float("inf")
        historial = []

        for gen in range(1, self.generaciones + 1):
            poblacion.sort(key=self.fitness, reverse=True)
            mejor_gen = poblacion[0]
            fit_mejor_gen = self.fitness(mejor_gen)
            fit_promedio = sum(self.fitness(ind) for ind in poblacion) / len(poblacion)

            if fit_mejor_gen > mejor_fitness_historico:
                mejor_fitness_historico = fit_mejor_gen
                mejor_historico = list(mejor_gen)

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

            if verbose and (gen == 1 or gen % 10 == 0 or gen == self.generaciones):
                print(f"  [Gen {gen:03d}] Mejor Fit: {mejor_fitness_historico:7.3f} | "
                      f"Promedio: {fit_promedio:7.3f} | Costo: S/{costo_gen:5.1f} | Dist: {dist_gen:5.1f} km")

            # Elitismo
            nueva_poblacion = [list(poblacion[i]) for i in range(self.elitismo)]

            # Reproduccion
            while len(nueva_poblacion) < self.tam_poblacion:
                p1 = self._seleccion_torneo(poblacion)
                p2 = self._seleccion_torneo(poblacion)

                if random.random() < self.prob_cruce:
                    h1, h2 = self._crossover_hibrido(p1, p2)
                else:
                    h1, h2 = list(p1), list(p2)

                h1 = self._mutar(h1)
                nueva_poblacion.append(h1)

                if len(nueva_poblacion) < self.tam_poblacion:
                    h2 = self._mutar(h2)
                    nueva_poblacion.append(h2)

            poblacion = nueva_poblacion

        # Fenotipo y metricas finales
        ruta_final = self.obtener_ruta_activa(mejor_historico)
        costo_final = sum(self.destinos_dict[did].get("costo_estimado", 15.0) for did in ruta_final)
        horas_final = sum(self.destinos_dict[did].get("tiempo_estimado_horas", 4.0) for did in ruta_final)
        distancia_final = self.calcular_distancia_ruta(ruta_final)
        grafica_ascii = self._dibujar_grafica_ascii(historial)

        # Genes reales evolucionados
        horas_real, cob_real, ext_real = self._extraer_genes_reales(mejor_historico)
        nivel_exig = evaluar_exigencia(horas_real, cob_real, ext_real)
        riesgos_ruta = {did: self.riesgos_lomas.get(did, 5.0) for did in ruta_final}

        # Desglose de desplazamientos radiales
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
            "genes_reales": {
                "horas_recorrido": round(horas_real, 2),
                "cobertura_zona": round(cob_real, 3),
                "extension_circuito": round(ext_real, 2)
            },
            "nivel_exigencia": round(nivel_exig, 4),
            "riesgos_ruta": riesgos_ruta,
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
    beneficios_base: Optional[Dict[str, float]] = None,
    scores_difusos: Optional[Dict[str, float]] = None,
    k: int = 3,
    presupuesto: float = 60.0,
    dias_disponibles: int = 3,
    generaciones: int = 50,
    tam_poblacion: int = 40,
    semilla: Optional[int] = None,
    verbose: bool = False,
    nodo_base: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Punto de entrada estandar para ejecutar la optimizacion por Algoritmo Genetico Hibrido.
    Mantiene compatibilidad con main.py, app.py y la suite de tests.
    """
    opt = LomasGeneticOptimizer(
        destinos=destinos,
        beneficios_base=beneficios_base,
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
        description="Modulo Heuristico: Algoritmo Genetico Hibrido con Logica Difusa Dual"
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

    # Beneficios base intrinsecos (sin logica difusa)
    beneficios_base = {
        d["id"]: round(7.0 + (1.0 if d.get("patrimonio", False) else 0.0), 2)
        for d in destinos
    }

    print("  MODULO HEURISTICO: ALGORITMO GENETICO HIBRIDO (DUAL DIFUSO)\n")
    print("  Parametros de Entrada:")
    print(f"  - Destinos a seleccionar (K):  {args.k}")
    print(f"  - Presupuesto maximo:         S/ {args.presupuesto:.2f}")
    print(f"  - Dias disponibles:           {args.dias}")
    print(f"  - Generaciones:               {args.gen}")
    print(f"  - Tamano de Poblacion:        {args.pop}")
    print("\n  Iniciando proceso evolutivo...")

    opt = LomasGeneticOptimizer(
        destinos=destinos,
        beneficios_base=beneficios_base,
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
    print("\n  RESULTADOS DE LA RUTA OPTIMIZADA:")
    print(f"  - Metodo de Resolucion:       {resultado.get('metodo', 'algoritmo_genetico')}")
    print(f"  - Secuencia de IDs:           {' -> '.join(resultado['ruta_ids'])}")
    print(f"  - Aptitud Final (Fitness):    {resultado['fitness']:.3f}")
    print(f"  - Costo Total Estimado:       S/ {resultado['costo_total']:.2f} (Limite: S/ {args.presupuesto:.2f})")
    print(f"  - Distancia Radial Total:     {resultado['distancia_total_km']:.2f} km")
    print(f"  - Tiempo de Senderos:         {resultado['tiempo_estimado_horas']:.2f} horas")

    print("\n  COMPONENTES DE LOGICA DIFUSA:")
    genes = resultado.get("genes_reales", {})
    print(f"  - Componente 1 (Genes Reales): Horas={genes.get('horas_recorrido', 0)}h | Cobertura={genes.get('cobertura_zona', 0)} | Extension={genes.get('extension_circuito', 0)}km")
    print(f"    -> Nivel de Exigencia Difusa: {resultado.get('nivel_exigencia', 0.0):.4f}")
    print("  - Componente 2 (Nivel de Riesgo por Loma):")
    for did, r in resultado.get("riesgos_ruta", {}).items():
        print(f"    * [{did}]: Riesgo Difuso = {r:.2f} / 10.0")

    cumple_presupuesto = resultado["costo_total"] <= args.presupuesto
    estado_presupuesto = "[CUMPLE]" if cumple_presupuesto else "[EXCEDE (Penalizado)]"
    print(f"\n  - Estado del Presupuesto:     {estado_presupuesto}")

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
