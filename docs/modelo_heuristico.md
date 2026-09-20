# Documentacion técnica del modulo heuristico: Algoritmo Genetico

## 1. Introduccion y Formulacion del Problema

El problema de diseno de rutas ecoturisticas en Lima Metropolitana consiste en seleccionar y ordenar un subconjunto de $K$ destinos a partir de un catalogo de $N = 15$ lomas costeras, satisfaciendo multiples objetivos contrapuestos y restricciones estrictas:

1. **Maximizar la satisfaccion turistica:** Priorizar las lomas que presenten mejores condiciones ambientales, de seguridad y accesibilidad, evaluadas de forma continua mediante los puntajes del modulo de logica difusa Mamdani ($S_{\text{difuso}} \in [0, 10]$).
2. **Minimizar los traslados geograficos:** Minimizar la distancia acumulada en kilometros entre paradas consecutivas, evitando desplazamientos dispersos a lo largo de la ciudad.
3. **Respetar el presupuesto del usuario:** La sumatoria de costos de transporte local y entradas a los circuitos no debe exceder el presupuesto total asignado por el turista.
4. **Respetar la disponibilidad de tiempo:** Las horas estimadas de caminata en los senderos deben ser compatibles con los dias disponibles declarados.

### 1.1 Clasificacion Computacional

Este problema pertenece a la clase de problemas de optimizacion combinatoria **NP-hard**. Especificamente, corresponde a una variante del **Orienteering Problem (OP)** o **Selective Traveling Salesperson Problem (STSP)** con restricciones presupuestales y temporales.

A diferencia del clasico Problema del Agente Viajero (TSP) donde se deben visitar obligatoriamente todos los nodos ($K = N$), en el Orienteering Problem se debe resolver de manera conjunta:

- Un problema de **seleccion de subconjunto (Knapsack / Mochila)**: Que $K$ lomas visitar de las $N=15$ disponibles para maximizar el puntaje acumulado dentro del presupuesto.
- Un problema de **ordenamiento de secuencia (TSP / Permutacion)**: En que orden especifico recorrer las $K$ lomas elegidas para minimizar la distancia geografica total de traslado.

### 1.2 Dimension del Espacio de Busqueda

El numero total de rutas ordenadas posibles de longitud $K$ a partir de $N = 15$ destinos viene dado por las variaciones sin repeticion:

$$
P(N, K) = \frac{N!}{(N - K)!}
$$


| Valor de K (Destinos) | Dias Equivalentes | Numero de Rutas Posibles $P(15, K)$ | Complejidad de Fuerza Bruta |
| :---------------------: | :-----------------: | :-----------------------------------: | :--------------------------- |
| $K = 1$               | 1 a 4 dias        | 15                                  | Inmediato                   |
| $K = 2$               | 5 a 8 dias        | 210                                 | Pequeño                     |
| $K = 3$               | 9 a 12 dias       | 2,730                               | Moderado                    |
| $K = 4$               | 13 a 16 dias      | 32,760                              | Elevado                     |
| $K = 5$               | 17 a 20 dias      | 360,360                             | Muy Elevado                 |
| $K = 6$               | 21 a 24 dias      | 3,603,600                           | Inviable en tiempo real     |
| $K = 8$               | Cota maxima       | 259,459,200                         | Espacio combinatorio masivo |


Debido a que el sistema debe responder en menos de un segundo en un entorno interactivo de terminal o web, la evaluacion exhaustiva por fuerza bruta resulta inviable para $K \ge 5$. El **Algoritmo Genetico (AG)** proporciona un mecanismo de busqueda estocastica guiada capaz de converger a soluciones de alta calidad (cuasi-optimas) en milisegundos.

## 2. Estructura Cromosomica y Espacio de Soluciones

### 2.1 Representacion del Gen y Locus

El genotipo de cada solucion se modela como un **cromosoma de permutacion de longitud fija** $K$:

- **Locus (**$i \in \{0, 1, \dots, K-1\}$**):** Representa el orden cronologico de visita (parada 1, parada 2, ..., parada $K$).
- **Alelo (**$g_i \in \{L_0, L_1, \dots, L_{14}\}$**):** Identificador unico del destino turistico asignado a dicha posicion.

```text
Locus:        0         1         2         ...     K-1
         +---------+---------+---------+-------+---------+
Alelos:  |   L4    |   L3    |   L0    |  ...  |   L7    |
         +---------+---------+---------+-------+---------+
Destino: Mangomarca  Manchay   Paraiso          Lucumo
```

### 2.2 Restriccion de Unicidad Absoluta

Ningun destino puede aparecer repetido dentro del mismo cromosoma:

$$
\forall i \neq j \implies g_i \neq g_j \quad \text{donde } g_i, g_j \in x
$$

Esta propiedad se preserva nativamente tanto en la inicializacion como en todos los operadores de cruce y mutacion, evitando la necesidad de fases de reparacion heuristica complejas.

## 3. Formulacion Matematica de la Funcion de Aptitud (Fitness)

La funcion de aptitud $F(x)$ sintetiza multiples objetivos mediante una **escalarizacion lineal con penalizaciones cuadraticas duras**:

$$
F(x) = \sum_{j=1}^{K} S_{\text{difuso}}(d_j) \;-\; \beta \cdot \left( \frac{\text{DistanciaTotal}(x)}{100} \right) \;-\; \lambda_1 \cdot \Omega_{\text{presupuesto}} \;-\; \lambda_2 \cdot \Omega_{\text{tiempo}} \;-\; \Omega_{\text{unicidad}}
$$

### 3.1 Termino 1: Beneficio Ecoturistico Difuso

$$
F_{\text{calidad}}(x) = \sum_{j=1}^{K} S_{\text{difuso}}(d_j)
$$

- $S_{\text{difuso}}(d_j) \in [0.0, 10.0]$ es el score de recomendacion calculado por el sistema de inferencia difusa Mamdani de 4 variables (saturacion, seguridad, clima-verdor y accesibilidad).
- Este termino recompensa la inclusion de destinos de alta calidad y pertinencia para el turista.

### 3.2 Termino 2: Costo por Desplazamiento Geografico

$$
f_{\text{distancia}}(x) = \beta \cdot \left( \frac{\text{DistanciaTotal}(x)}{100} \right)
$$

Donde $\beta = 1.0$ y el factor de escala $100$ normaliza la magnitud de los kilometros frente a la escala de los puntajes de calidad.

La distancia total entre paradas consecutivas se calcula mediante la **formula de Haversine**:

$$
\text{DistanciaTotal}(x) = \sum_{j=0}^{K-2} \text{dist}_{\text{haversine}}(x[j], x[j+1])
$$

Si la ruta contiene un unico destino ($K = 1$), $\text{DistanciaTotal}(x) = 0.0\text{ km}$.

#### Formula de Haversine:

Dados dos puntos $P_1(\phi_1, \lambda_1)$ y $P_2(\phi_2, \lambda_2)$ en coordenadas decimales (latitud y longitud):

$$
\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1
$$

$$
a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta \lambda}{2}\right)
$$

$$
c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)
$$

$$
d = R \cdot c \quad \text{con } R = 6371.0\text{ km (radio medio de la Tierra)}
$$

### 3.3 Termino 3: Penalizacion Cuadratica Presupuestal

$$
\Omega_{\text{presupuesto}} = \lambda_1 \cdot \left(\max\left(0,\; \sum_{j=1}^{K} \text{CostoEstimado}(d_j) - \text{Presupuesto}\right)\right)^2
$$

- Con $\lambda_1 = 1.0$.
- **Propiedad:** Si la ruta respeta el presupuesto ($\text{CostoTotal} \le \text{Presupuesto}$), la penalizacion es exactamente cero.
- Si el presupuesto se sobrepasa, la funcion cuadratica castiga de forma exponencial las desviaciones: excesos leves (ej. S/ 2) generan una penalizacion insignificante ($2^2 = 4$), mientras que excesos mayores (ej. S/ 20) degradan severamente el fitness ($20^2 = 400$), forzando al algoritmo a descartar rutas inviables durante la seleccion.

### 3.4 Termino 4: Penalizacion Cuadratica Temporal

$$
\Omega_{\text{tiempo}} = \lambda_2 \cdot \left(\max\left(0,\; \sum_{j=1}^{K} \text{HorasEstimadas}(d_j) - (\text{DiasDisponibles} \times 8.0)\right)\right)^2
$$

- Con $\lambda_2 = 1.0$, asumiendo una jornada util de 8.0 horas diarias de trekking por dia disponible.
- Penaliza aquellas combinaciones de lomas cuya duracion estimada de ascenso y recorrido exceda la ventana temporal del usuario.

### 3.5 Termino 5: Penalizacion Estricta de Unicidad

$$
\Omega_{\text{unicidad}} = 1000.0 \cdot (K - |\text{set}(x)|)
$$

- Actua como barrera de seguridad matematica con un castigo destructivo de 1000 puntos por cada destino duplicado en caso de anomalia en los operadores.

## 4. Operadores Geneticos Adaptados a Subconjuntos

Dado que $K < N$, el espacio combinatorio combina seleccion de elementos y ordenamiento. Para gobernar ambos aspectos se implementaron operadores especializados:

```text
+-------------------------------------------------------------------------+
|                  CICLO EVOLUTIVO DEL ALGORITMO GENETICO                 |
+-------------------------------------------------------------------------+
|  1. Inicializacion: P individuos aleatorios de longitud K sin repetidos |
|  2. Evaluacion: Computo de Fitness F(x) segun la ecuacion multiobjetivo |
|  3. Elitismo: Preservacion de los E=2 mejores individuos                |
|  4. Seleccion: Torneo estocastico con k_torneo = 3                      |
|  5. Cruce: Order Crossover (OX) para subconjuntos (prob = 0.85)         |
|  6. Mutacion Adaptativa (prob = 0.30):                                  |
|     - Mutacion Swap (40%): Intercambio de orden (optimiza distancia)    |
|     - Mutacion Reemplazo (40%): Cambio de loma (optimiza score/costo)   |
|     - Mutacion Inversion 2-Opt (20%): Eliminacion de cruces             |
|  7. Verificacion de Criterio de Parada (G_max generaciones alcanzadas)  |
+-------------------------------------------------------------------------+
```

### 4.1 Seleccion por Torneo ($k_{\text{torneo}} = 3$)

Para seleccionar cada progenitor:

1. Se eligen 3 individuos al azar de la poblacion con distribucion uniforme.
2. Se compara su aptitud $F(x)$.
3. El individuo con mayor fitness es seleccionado como progenitor.

- **Justificacion:** El torneo con $k=3$ ofrece una presion selectiva intermedia ideal: favorece a los mejores individuos sin descartar prematuramente la diversidad genetica, evitando caer en optimos locales tempranos.

### 4.2 Cruce: Order Crossover (OX) para Subconjuntos de Longitud $K$

El operador OX clasico asume que ambos padres contienen exactamente los mismos genes. Al tratarse de subconjuntos de tamano $K$ elegidos de un universo $N=15$, los padres pueden contener genes distintos.

**Procedimiento implementado:**

1. Se seleccionan dos indices de corte aleatorios $0 \le i_1 < i_2 < K$.
2. El descendiente hereda el subsegmento continuo del Padre 1 entre $i_1$ e $i_2$:
   $$
   \text{Hijo}[i_1 : i_2 + 1] = \text{Padre1}[i_1 : i_2 + 1]
   $$
3. Para completar las posiciones restantes, se recorren los genes del Padre 2 comenzando en la posicion $i_2 + 1$ de forma circular.
4. Solo se insertan aquellos genes que **no esten presentes** en el segmento heredado.
5. Si tras recorrer el Padre 2 aun quedan posiciones libres (porque ambos padres compartian muchos alelos), los huecos restantes se completan con destinos del catalogo global $N$ no presentes en el hijo, seleccionados al azar.

- **Resultado:** Garantia matematica de que el descendiente tiene exactamente longitud $K$ y cero duplicados.

### 4.3 Mutaciones Adaptativas

Cada vez que un individuo es seleccionado para mutar (con probabilidad $p_m = 0.30$), se aplica una de las siguientes tres estrategias:

#### A. Mutacion Swap (Intercambio — Probabilidad relativa 40%)

- **Mecanica:** Se seleccionan dos indices aleatorios $i \neq j$ y se intercambian sus alelos: $\text{Hijo}[i], \text{Hijo}[j] = \text{Hijo}[j], \text{Hijo}[i]$.
- **Objetivo:** Explorar permutaciones del mismo conjunto de lomas para acortar traslados.

#### B. Mutacion por Reemplazo (Sustitucion — Probabilidad relativa 40%)

- **Mecanica:** Se selecciona una posicion al azar $i$ del cromosoma y se reemplaza su destino por una loma del catalogo $N$ que **no pertenezca** a la ruta actual.
- **Objetivo:** Explorar nuevas combinaciones de destinos, permitiendo ingresar lomas con mejor score difuso o costos mas bajos que reduzcan la penalizacion de presupuesto.

#### C. Mutacion por Inversion (2-Opt Local — Probabilidad relativa 20%)

- **Mecanica:** Se seleccionan dos indices $i_1 < i_2$ y se invierte el subsegmento de paradas intermedias: $\text{Hijo}[i_1:i_2+1] = \text{reversed}(\text{Hijo}[i_1:i_2+1])$.
- **Objetivo:** Operador clasico de optimizacion de rutas que desenreda cruces geograficos.

### 4.4 Elitismo ($E = 2$)

Los 2 mejores individuos con mayor aptitud de cada generacion se copian intactos a la siguiente generacion sin pasar por cruce ni mutacion. Esto garantiza formalmente que:

$$
F(\text{Mejor}_{g+1}) \ge F(\text{Mejor}_{g}) \quad \forall g \ge 1
$$

El fitness de la mejor solucion encontrada nunca decae a lo largo de las generaciones.

## 5. Desglose y Explicacion del Codigo Fuente

A continuacion se explica la implementacion contenida en `modules/genetic_algorithm.py`:

### 5.1 Funcion `distancia_haversine(lat1, lon1, lat2, lon2)`

- Realiza la transformacion a radianes mediante `math.radians`.
- Implementa la ecuacion del semiverseno con proteccion ante errores de redondeo de punto flotante (`max(0.0, 1.0 - a)`).
- Si las coordenadas origen y destino son identicas, retorna `0.0` inmediatamente para optimizar llamadas redundantes.

### 5.2 Clase `LomasGeneticOptimizer`

Representa el motor evolutivo encapsulado.

#### Constructor `__init__(...)`

- Configura las colecciones del problema: lista de destinos, diccionario de acceso rapido por ID (`destinos_dict`) y conjunto de IDs totales.
- Normaliza los parametros de ejecucion: acota $K$ al rango $[1, 15]$, valida tipos flotantes para presupuesto y enteros para dias, y asegura que la poblacion minima sea viable.
- Permite inyeccion de semilla pseudoaleatoria (`semilla`) para pruebas unitarias deterministas.

#### Metodo `calcular_distancia_ruta(ruta)`

- Itera sobre los pares consecutivos $(x[i], x[i+1])$ y acumula la distancia Haversine de cada tramo extrayendo las coordenadas desde `self.destinos_dict`.
- Si `len(ruta) <= 1`, retorna `0.0 km`.

#### Metodo `fitness(ruta)`

- Implementa fielmente la ecuacion multiobjetivo descrita en la seccion 3.
- Calcula el beneficio difuso sumando los puntajes normalizados de cada loma en la ruta.
- Computa la penalizacion presupuestal elevando al cuadrado la diferencia positiva entre el costo real y el limite financiero.
- Aplica el descuento por kilometraje escalado a 100 km.

#### Metodo `_crossover_ox(padre1, padre2)`

- Genera dos descendientes complementarios preservando subsegmentos continuos.
- Realiza el seguimiento con un conjunto `set` para verificar pertenencia en tiempo $O(1)$.
- Si la interseccion entre ambos progenitores genera vacios, toma destinos restantes del catalogo general, garantizando cromosomas completos y sin duplicados.

#### Metodos de Mutacion `_mutacion_swap`, `_mutacion_reemplazo`, `_mutacion_inversion`

- Implementan las tecnicas de busqueda local descritas, verificando que los cromosomas resultantes respeten la longitud $K$ y la unicidad.

#### Metodo `_dibujar_grafica_ascii(historial, ancho=40, alto=8)`

- Muestrea el historial de fitness a lo largo de las generaciones y proyecta los valores en una matriz de caracteres ASCII.
- Utiliza `*` para puntos clave, `|` para lineas verticales y `-` para ejes, permitiendo visualizar la convergencia directamente en terminales Windows/Linux sin librerias graficas externas pesadas (como matplotlib).

#### Metodo `optimizar(verbose=False)`

- Orquesta el bucle evolutivo de $G$ generaciones.
- Registra en cada iteracion: mejor fitness, fitness promedio, costo del mejor individuo y kilometraje.
- Si `verbose=True`, imprime en consola trazas periodicas del avance generacional.
- Retorna un diccionario con la mejor ruta (`ruta_ids`), objetos completos de destinos ordenados (`destinos_ordenados`), metricas finales de costo, distancia, tiempo, desglose tramo a tramo, historial completo y la grafica en ASCII.

### 5.3 Funcion de Entrada `optimizar_ruta_lomas(...)`

- Funciona como fachada publica para invocar el optimizador desde `main.py` o scripts externos, asegurando compatibilidad con los argumentos preexistentes.

### 5.4 Funcion CLI `main()`

- Utiliza `argparse` para proporcionar una interfaz de linea de comandos flexible con banderas `--k`, `--presupuesto`, `--dias`, `--gen`, `--pop`, `--semilla`, `--silencioso`.
- Incluye soporte UTF-8 automatico en consola Windows mediante `sys.stdout.reconfigure`.

## 6. Guia de Ejecucion por Terminal (CLI)

El modulo puede ejecutarse directamente desde la raiz del repositorio mediante la terminal.

### 6.1 Ejecucion Estandar con Parametros por Defecto

```powershell
python modules/genetic_algorithm.py
```

*Parametros aplicados por defecto:* $K = 3$ *lomas, presupuesto S/ 60.00, 3 dias, 50 generaciones, 40 individuos.*

### 6.2 Consulta de Ayuda y Opciones Disponibles

```powershell
python modules/genetic_algorithm.py --help
```

### 6.3 Ejecucion con Restricciones Personalizadas

#### Caso A: Viaje Corto de Fin de Semana (Presupuesto Ajustado)

```powershell
python modules/genetic_algorithm.py --k 2 --presupuesto 35 --dias 2 --gen 40 --pop 30
```

#### Caso B: Itinerario Extenso de Vacaciones (4 Lomas)

```powershell
python modules/genetic_algorithm.py --k 4 --presupuesto 90 --dias 4 --gen 60 --pop 50
```

#### Caso C: Ejecucion con Semilla Determinista (Reproducibilidad)

```powershell
python modules/genetic_algorithm.py --k 3 --presupuesto 70 --dias 3 --semilla 42
```

### 6.4 Ejemplo Real de Salida en Terminal

```text

  MODULO HEURISTICO: OPTIMIZACION MEDIANTE ALGORITMO GENETICO

  Parametros de Entrada:
  - Destinos a seleccionar (K):  3
  - Presupuesto maximo:         S/ 70.00
  - Dias disponibles:           3
  - Generaciones:               50
  - Tamano de Poblacion:        40

  Iniciando proceso evolutivo...
  [Gen 001] Mejor Fit:  29.759 | Promedio:  22.963 | Costo: S/ 50.0 | Dist:  24.1 km
  [Gen 010] Mejor Fit:  30.125 | Promedio:  30.014 | Costo: S/ 35.0 | Dist:  23.5 km
  [Gen 020] Mejor Fit:  30.125 | Promedio:  30.040 | Costo: S/ 35.0 | Dist:  23.5 km
  [Gen 030] Mejor Fit:  30.125 | Promedio:  30.011 | Costo: S/ 35.0 | Dist:  23.5 km
  [Gen 040] Mejor Fit:  30.125 | Promedio:  30.003 | Costo: S/ 35.0 | Dist:  23.5 km
  [Gen 050] Mejor Fit:  30.125 | Promedio:  30.099 | Costo: S/ 35.0 | Dist:  23.5 km


  Curva de Convergencia del Fitness (Generaciones):
   30.12 ^------------------------------------------
   30.08 |     ************************************
   30.03 |     ||||||||||||||||||||||||||||||||||||
   29.99 |    *||||||||||||||||||||||||||||||||||||
   29.94 |    |||||||||||||||||||||||||||||||||||||
   29.90 |    |||||||||||||||||||||||||||||||||||||
   29.85 |    |||||||||||||||||||||||||||||||||||||
   29.80 |    |||||||||||||||||||||||||||||||||||||
   29.76 | ***|||||||||||||||||||||||||||||||||||||
         +---------------------------------------->
         Gen 1                            Gen 50


  RESULTADOS DE LA RUTA OPTIMIZADA:
  - Secuencia de IDs:        L4 -> L3 -> L0
  - Aptitud Final (Fitness): 30.125
  - Costo Total Estimado:    S/ 35.00 (Limite: S/ 70.00)
  - Distancia Inter-Loma:    23.55 km
  - Tiempo de Senderos:      12.00 horas
  - Estado del Presupuesto:  [CUMPLE]

  Detalle Parada por Parada:
    Parada 1: [L4] Lomas de Mangomarca (San Juan de Lurigancho)
              Dificultad: Moderado | Costo: S/ 10.00 | Tiempo: 4.0h
    Parada 2: [L3] Lomas de Manchay (Ate)
              Dificultad: Moderado | Costo: S/ 10.00 | Tiempo: 3.5h
    Parada 3: [L0] Lomas del Paraíso (+ Apu Siqay) (Villa María del Triunfo)
              Dificultad: Moderado | Costo: S/ 15.00 | Tiempo: 4.5h

  Tramos de Desplazamiento Geografico:
    - De Lomas de Mangomarca hasta Lomas de Manchay: 16.06 km
    - De Lomas de Manchay hasta Lomas del Paraíso (+ Apu Siqay): 7.49 km

```

## 7. Pruebas Unitarias y Control de Calidad

El modulo cuenta con una suite de 10 pruebas unitarias en `tests/test_genetic.py`:

```powershell
python -m unittest tests/test_genetic.py -v
```

### Detalle de las Pruebas Implementadas:

1. `test_distancia_haversine`: Valida precision de calculo, simetria $d(A, B) = d(B, A)$ y caso nulo $d(A, A) = 0$.
2. `test_unicidad_cromosoma_y_tamano_k`: Valida que la ruta generada tenga exactamente $K$ destinos y cero duplicados.
3. `test_crossover_ox_validez`: Valida que el cruce Order Crossover con subconjuntos produzca hijos validos de tamano $K$ sin elementos repetidos.
4. `test_mutaciones_generan_cromosomas_validos`: Comprueba que las mutaciones Swap, Reemplazo e Inversion mantengan la longitud y la unicidad del cromosoma.
5. `test_penalizacion_presupuesto_en_fitness`: Verifica que ante presupuestos insuficientes el fitness decaiga cuadraticamente.
6. `test_penalizacion_tiempo_en_fitness`: Verifica la penalizacion si las horas totales superan las horas disponibles.
7. `test_penalizacion_distancia_en_fitness`: Verifica que rutas mas cortas tengan mayor fitness a igualdad de scores difusos.
8. `test_elitismo_no_regresion_fitness`: Verifica que el mejor fitness historico sea monotonicamente no decreciente a traves de las generaciones.
9. `test_caso_borde_k1`: Valida el comportamiento correcto cuando $K = 1$ (cero distancia de traslado inter-loma).
10. `test_reproducibilidad_con_semilla`: Verifica el determinismo del algoritmo ante una misma semilla pseudoaleatoria.

