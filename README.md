# Sistema Inteligente de Asignación y Optimización de Paseos Caninos

## 1. Introducción y planteamiento del problema

La coordinacion diaria de paseos en albergues y refugios caninos representa un desafio logistico y de bienestar animal de alta complejidad. La planificacion tradicional suele realizarse de forma empirica y manual, lo que genera riesgos operativos significativos:

- Variabilidad conductual canina: La reactividad y el estres de un perro no son propiedades estaticas; fluctuan diariamente segun factores ambientales imprecisos (ruido en el refugio, dias acumulados de encierro, condiciones climaticas).
- Heterogeneidad del voluntariado: Los voluntarios presentan niveles de experiencia dispares, limites fisicos diferenciados y disponibilidades horarias parciales o variables.
- Restricciones criticas de seguridad: La coincidencia de dos caninos altamente reactivos en un mismo turno o zona puede desencadenar incidentes graves; asimismo, asignar un canino de manejo complejo a un voluntario novato representa un riesgo inaceptable.
- Equidad y fatiga operativa: La sobrecarga recurrente de voluntarios experimentados deriva en agotamiento y desercion, mientras que otros voluntarios quedan subutilizados.

El presente proyecto propone una solucion integral que articula Modelos de Lenguaje (LLM), Logica Difusa y Algoritmos Geneticos (AG) para automatizar, validar y optimizar este proceso de punta a punta.

## 2. Arquitectura del sistema y flujo end-to-end

El ciclo operativo diario se estructura en cuatro etapas secuenciales:

```
[Reporte no estructurado en texto libre]
"Hoy llovio fuerte, vino Juan (novato) y Maria (experta). Firulais lleva 4 dias encerrado."
                          |
                          v
         [Fase 1: Extraccion de Entidades (LLM)]
  Estructura variables ambientales, estado de los caninos y voluntarios disponibles.
                          |
                          v
      [Fase 2: Inferencia de Reactividad Dinamica (Fuzzy)]
  Calcula el Score de Reactividad Dinamica (Rd en [0, 10]) por cada canino.
                          |
                          v
      [Fase 3: Optimizacion Combinatoria (Algoritmo Genetico)]
  Determina la asignacion global optima de turnos y voluntarios respetando
  restricciones duras y balanceando la carga de trabajo.
                          |
                          v
       [Fase 4: Generacion de Directiva Operativa (LLM)]
  Produce la hoja de ruta clara en lenguaje natural con recomendaciones puntuales.
```

### Fase 1: Extracción de entidades (LLM)

Un modelo de lenguaje procesa el reporte matutino informal emitido por los encargados del albergue y lo transforma en un esquema estructurado (JSON tipificado) que alimenta las etapas analiticas posteriores.

### Fase 2: Inferencia de reactividad dinámica (Lógica Difusa)

El comportamiento canino ante la incertidumbre diaria se cuantifica mediante un sistema de inferencia difuso (Mamdani o Sugeno).

- Variables de entrada difusas:
  - Estres ambiental (Bajo, Medio, Alto): Cuantifica ruido, trafico o construcciones aledanas.
  - Historial de confinamiento (Pocos, Moderados, Muchos dias sin salir).
  - Clima adverso (Tranquilo, Lluvia, Tormenta).
- Reglas de inferencia representativas:
  - SI dias_sin_salir es *Muchos* Y estres_ambiental es *Alto*, ENTONCES reactividad es *Critica*.
  - SI clima es *Tormenta*, ENTONCES reactividad se desplaza hacia valores superiores.
- Salida defusificada: Un indice continuo $R_d \in [0, 10]$ denominado Score de Reactividad Dinamica.

### Fase 3: Optimización combinatoria (Algoritmo Genético)

Con los valores de $R_d$, el perfil de los voluntarios y los turnos disponibles, el motor de algoritmos geneticos resuelve la asignacion optima de recursos evitando conflictos espaciales y horarios.

### Fase 4: Generación de directiva operativa (LLM)

La asignacion resultante se sintetiza en una hoja de instrucciones clara y legible para el personal operativo, indicando turnos, parejas asignadas, advertencias especificas de reactividad y protocolos de seguridad.

## 3. Modelo y Funcionamiento del Algoritmo Genético

### 3.1. Espacio de Busqueda y Representacion del Cromosoma

El problema se formula como una asignacion discreta multiobjetivo con restricciones. Considerando un conjunto de $N$ perros, $M$ voluntarios y $T$ turnos horarios operativos:

- Codificacion del Genotipo: Se utiliza un vector de asignacion directa de longitud $N$, donde cada posicion (gen $i$) corresponde de manera fija al perro con indice $i$.
- Valor del Gen: Cada gen contiene una tupla codificada $(V_j, T_k)$, indicando que el perro $i$ sera paseado por el voluntario $V_j$ durante el turno $T_k$.

$$
\text{Cromosoma} = \left[ (V_a, T_b)_{\text{Perro 0}}, (V_c, T_d)_{\text{Perro 1}}, \dots, (V_e, T_f)_{\text{Perro } N-1} \right]
$$

Esta codificacion garantiza que todo canino tenga siempre una asignacion asignada, eliminando de entrada la necesidad de reparar caninos no asignados.

### 3.2. Mapeo Genotipo a Fenotipo

El arreglo lineal se proyecta en una estructura matricial indexada por turnos y voluntarios:

$$
\text{Fenotipo}: \text{Turno} \to \text{Voluntario} \to \text{Lista de Perros Asignados}
$$

Esta proyeccion permite evaluar de forma eficiente la concurrencia espacial (perros presentes en el mismo turno), la carga de trabajo asignada a cada voluntario por turno y a lo largo de toda la jornada.

### 3.3. Formulación de la Funcion de Aptitud (Fitness)

La funcion objetivo busca maximizar la compatibilidad voluntario-canino y la equidad en el esfuerzo, penalizando severamente cualquier violacion de restricciones operativas:

$$
\text{Fitness}(\text{cromosoma}) = w_{\text{comp}} \cdot \text{Compatibilidad} - \sum \text{Penalizaciones Duras} - w_{\text{bal}} \cdot \text{Desbalance Carga}
$$

Donde:

#### A. Termino de Compatibilidad (Alineacion de Nivel)

Premia la cercania entre el nivel de experiencia del voluntario $\text{Exp}(V_j) \in [0, 10]$ y el indice de reactividad dinamica del perro $R_d(D_i) \in [0, 10]$:

$$
\text{Compatibilidad} = \sum_{i=0}^{N-1} \left( 10 - |\text{Exp}(V_i) - R_d(D_i)| \right)
$$

Este termino asegura que los caninos con mayor complejidad sean conducidos por personal experimentado, reservando los caninos dociles a voluntarios principiantes.

#### B. Penalizaciones Duras (Inviabilidad Operativa)

Las restricciones duras representan condiciones operativas innegociables. Su incumplimiento deduce puntajes significativos para asegurar que los individuos infractores sean eliminados de la seleccion:

1. Capacidad por Turno: Un voluntario no puede pasear mas caninos de los permitidos por turno (usualmente 1, o su capacidad declarada):
 $$\text{Penalizacion} = -1000 \text{ pts por cada asignacion en exceso por turno}$$
2. Incompatibilidad Espacial de Reactividad: Si dos o mas perros con reactividad alta ($R_d \ge 7.0$) son programados en el mismo turno, se incrementa el riesgo de incidentes en areas de salida o retorno:
 $$\text{Penalizacion} = -500 \text{ pts por cada par conflictivo en el mismo turno}$$
3. Indisponibilidad Horaria: Si un voluntario es programado en un turno fuera de su horario declarado disponible:
 $$\text{Penalizacion} = -1000 \text{ pts por cada turno no disponible asignado}$$
4. Riesgo Critico Inaceptable: Si un voluntario con baja experiencia ($\text{Exp} < 6.0$) es asignado a un perro con reactividad critica ($R_d \ge 8.0$):
 $$\text{Penalizacion} = -2000 \text{ pts por cada asignacion de riesgo critico}$$

#### C. Penalizacion Blanda: Desbalance de Carga y Fatiga

Para prevenir la sobrecarga de los voluntarios mas calificados, se calcula la varianza muestral del numero total de paseos diarios asignados a cada voluntario activo:

$$
\text{Desbalance} = \frac{1}{|V|} \sum_{v \in V} (\text{Paseos}_v - \mu_{\text{paseos}})^2
$$

### 3.4. Operadores Geneticos y Dinamica Evolutiva

1. Inicializacion de la Poblacion: Se genera una poblacion de tamaño $P$ con genes muestreados uniformemente dentro de los rangos validos de voluntarios y turnos.
2. Seleccion de Progenitores: Se aplica seleccion por torneo de tamaño $k=3$. Este metodo mantiene una presion selectiva controlada y previene la convergencia prematura hacia optimos locales no factibles.
3. Cruce (Crossover): Se implementa cruce uniforme o cruce en dos puntos sobre los genes del vector. Dado que cada gen es una asignacion completa e independiente para un perro especifico, el cruce preserva la integridad estructural del individuo.
4. Mutacion: Se aplican operadores con probabilidad $p_m$:
  - Mutacion de Voluntario: Reasigna el perro a otro voluntario disponible.
  - Mutacion de Turno: Traslada el paseo a otro turno horario.
  - Mutacion por Intercambio (Swap): Intercambia los voluntarios o turnos entre dos caninos elegidos al azar.
5. Politica de Reemplazo y Elitismo: Los mejores $E$ individuos de cada generacion se transfieren intactos a la siguiente generacion, garantizando que el mejor fitness historico nunca decaiga.
6. Criterio de Parada: El proceso evolutivo concluye al alcanzar el numero maximo de generaciones o cuando se detecta estancamiento del fitness habiendo alcanzado cero penalizaciones duras.

