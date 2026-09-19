# Alineación con el Enunciado del Proyecto y Cronograma de Trabajo

## 1. Alineación con el Enunciado Oficial del Proyecto


| Requisito del Enunciado Oficial          | Cómo se Cumple en el Proyecto                                                                        | Ubicación / Referencia                                                                                                                                                                                                                              |
| :---------------------------------------- | :---------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Objetivo General**                     | Desarrollar un software inteligente que complemente la formación teórica y práctica.                 | Sistema Inteligente de Rutas en las Lomas de Lima ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 1-2)                                                                                                |
| **Tipo de Problema**                     | Búsqueda, optimización, planificación o selección.                                                   | **Optimización y Selección Combinatoria:** Algoritmo Genético multiobjetivo con permutaciones y selección difusa Mamdani.                                                                                                                           |
| **Componente 1: IA Generativa**          | Conectada vía API para interpretar solicitudes en texto libre, generar inputs y explicar resultados. | OpenAI API (`gpt-4o-mini`) / Anthropic API para extracción de entidades a JSON y generación de itinerario amigable ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 3.2).                              |
| **Componente 2: Algoritmos Heurísticos** | Diseñado e implementado para resolver el problema combinatorio.                                      | Algoritmo Genético con población de 50 rutas, Order Crossover (OX), mutación swap/inserción y elitismo ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 6).                                            |
| **Componente 3: Incertidumbre**          | Razonamiento bajo incertidumbre (lógica difusa) para información imprecisa o incierta.               | Sistema Difuso Mamdani con **4 variables clave de incertidumbre** (Saturación, Seguridad, Clima/Verdor y Accesibilidad) con salida $[0, 10]$ ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 5).      |
| **Integración y Coordinación**           | Los 3 componentes integrados en una única aplicación interactiva.                                    | Pipeline end-to-end: Texto libre $\rightarrow$ LLM $\rightarrow$ Mapeo $\rightarrow$ Fuzzy $\rightarrow$ AG $\rightarrow$ LLM $\rightarrow$ GUI ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 3.5). |
| **Interfaz Gráfica (GUI)**               | El usuario ingresa información, solicita solución y obtiene respuesta visual.                        | Aplicación web en **Streamlit + Folium** con mapa interactivo centrado en Lima, panel lateral y badges numerados 1..K ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 7).                             |
| **Población Objetivo**                   | Empresas, ciudadanos, instituciones, gobierno, turistas.                                             | Turistas nacionales/extranjeros, comités locales ecoturísticos, SERPAR y GRML (ACR Sistema de Lomas de Lima).                                                                                                                                       |
| **Ventajas Competitivas**                | Comparación frente a software existente.                                                             | Diferenciación vs. *Andeshandbook* (Chile), *Lima Guía Oficial*, apps de transporte como *TuRuta/Rumbo* ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 2.3).                                         |
| **Entregables Exigidos**                 | Manual de instalación, manual de usuario, informe técnico y código fuente.                           | Estructurados en `/docs` y repositorio GitHub ([README.md](file:///C:/Users/Usuario/Desktop/Vilberto02-Git/si-project-unmsm/README.md) Sec. 11).                                                                                                    |


---

## 2. Calendario Oficial de la Cátedra vs. Estado Real del Proyecto

El enunciado docente estipula el siguiente esquema de avance porcentual y fechas de control:

```
[Semana 4: 10%] ──> [Semana 5: 30%] ──> [Semana 6: 60%] ──> [Semana 7: 100% Final y Sustentación]
```

## 3. Estructura y Distribución del Equipo (5 Integrantes)

Para garantizar velocidad y calidad, cada integrante asume un rol principal con responsabilidades concretas y entregables específicos:

### Definición de Roles y Responsabilidades


| Integrante       | Rol Principal                                        | Módulos y Archivos a Cargo                                                                                     | Responsabilidades Específicas                                                                                                                                                                                                                                                                                                                           |
| :---------------- | :---------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Integrante 1** | **Especialista en Razonamiento bajo Incertidumbre**  | `modules/fuzzy_module.py`<br>`data/destinos.json` (apoyo)                                                      | • Implementar el motor difuso Mamdani con `scikit-fuzzy`.<br>• Programar las 4 variables de entrada y sus funciones de membresía.<br>• Codificar las 20 reglas difusas y la defuzzificación por centroide.<br>• Validar que ningún destino genere salidas `NaN` o errores.                                                                              |
| **Integrante 2** | **Especialista en Optimización Heurística**          | `modules/genetic_algorithm.py`<br>`modules/mapping.py`                                                         | • Implementar el Algoritmo Genético en Python puro.<br>• Estructurar el cromosoma de permutación ($K$ destinos sin duplicados).<br>• Codificar la selección por torneo ($k=3$), cruce OX y mutaciones.<br>• Implementar la función de aptitud con penalizaciones cuadráticas.<br>• Programar la función de mapeo $K = \lceil \text{días} / 4 \rceil$.   |
| **Integrante 3** | **Especialista en IA Generativa y NLP**              | `modules/llm_module.py`<br>`modules/access_module.py`                                                          | • Integrar la API del LLM (OpenAI `gpt-4o-mini` / Anthropic).<br>• Crear el prompt para extracción de entidades a JSON estructurado.<br>• Implementar el generador de itinerarios narrativos comprensibles.<br>• Codificar el generador de instrucciones de transporte público.<br>• Crear un mock offline robusto para pruebas sin consumo de API.     |
| **Integrante 4** | **Desarrollador de Interfaz y Mapas (GUI/GIS)**      | `app.py`<br>`data/destinos.json`<br>`assets/`                                                                  | • Estructurar el dataset de 15 destinos en `data/destinos.json`.<br>• Construir la interfaz web con Streamlit (sidebar + panel principal).<br>• Integrar el mapa interactivo con `folium` y `streamlit-folium`.<br>• Implementar marcadores, popups con detalles y badges numerados.<br>• Configurar el flujo de pantallas y zoom automático a la ruta. |
| **Integrante 5** | **Integrador End-to-End, QA y Documentador Técnico** | `main.py`<br>`tests/`<br>`docs/manual_instalacion.md`<br>`docs/manual_usuario.md`<br>`docs/informe_tecnico.md` | • Enlazar el pipeline completo en `main.py` para ejecución por CLI.<br>• Diseñar y ejecutar pruebas automatizadas de coherencia y estrés.<br>• Redactar el Manual de Instalación y Manual de Usuario.<br>• Elaborar el Informe Técnico Final según los 4 puntos del enunciado.<br>• Coordinar diapositivas y preparación de la sustentación oral.       |


---

## 4. Cronograma de Trabajo y Plan de Recuperación Acelerado

### 4.1 Historial de Semanas 4 y 5 (Fase Conceptual)

- **Semana 4 (10% según enunciado):** Identificación de la problemática turística nacional y planteamiento preliminar de funciones de aptitud.
- **Semana 5 (30% según enunciado):** Evaluación crítica del alcance. **Hito de replanteamiento:** se descarta el proyecto nacional y se formula el proyecto de **Lomas de Lima**, logrando la formalización matemática completa en `README.md`.

---

### 4.2 Sprint 1 — Semana 6: Hito Parcial 2 (\~60% de Avance)

> **Objetivo del Hito:** Disponer de un **sistema computacional integrado y funcional**. Los 3 módulos principales deben ejecutarse de forma coordinada, resolviendo la optimización y mostrando resultados preliminares en consola y prototipo web.


| Día       | Actividad / Tarea                                                                                                                                                                                                                                                                       | Responsables                 | Entregable Concreto                                  |
| :---------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------- | :---------------------------------------------------- |
| **Día 1** | **Setup del Proyecto y Dataset:**<br>• Creación del repo base, `requirements.txt` y entorno virtual.<br>• Construcción de `data/destinos.json` con los 15 destinos, coordenadas, costos y 4 atributos.                                                                                  | Integrante 4<br>Integrante 5 | `data/destinos.json`<br>`requirements.txt`           |
| **Día 2** | **Construcción de Módulos Núcleo (Fuzzy y AG):**<br>• Programación de `fuzzy_module.py` (4 variables, membresías y 20 reglas).<br>• Programación de `genetic_algorithm.py` (cromosoma, población 50, operadores OX y mutación).                                                         | Integrante 1<br>Integrante 2 | `fuzzy_module.py`<br>`genetic_algorithm.py`          |
| **Día 3** | **Función Fitness y Módulo LLM:**<br>• Calibración de la función fitness con scores difusos y penalizaciones cuadráticas.<br>• Implementación de `llm_module.py` (parsing JSON + modo mock offline) y `mapping.py`.                                                                     | Integrante 2<br>Integrante 3 | `llm_module.py`<br>`mapping.py`                      |
| **Día 4** | **Integración CLI y Prototipo GUI:**<br>• Creación de `main.py` para probar el flujo: Texto $\rightarrow$ JSON $\rightarrow$ K $\rightarrow$ Fuzzy $\rightarrow$ AG $\rightarrow$ Itinerario.<br>• Construcción de la interfaz preliminar en Streamlit (`app.py`) con mapa base Folium. | Integrante 5<br>Integrante 4 | `main.py`<br>`app.py` (v1)                           |
| **Día 5** | **Pruebas de Integración y Calibración:**<br>• Pruebas de convergencia del AG (verificar 0 infracciones de presupuesto y tiempo).<br>• Verificación de consistencia del score difuso en las 15 lomas.<br>• Enlace de la GUI preliminar con el pipeline.                                 | Todos los integrantes        | Pipeline enlazado y funcional                        |
| **Día 6** | **Elaboración del Informe Parcial 2 (60%):**<br>• Redacción de `docs/informe_parcial.md` con evidencia de funcionamiento, capturas de CLI y métricas de convergencia.<br>• Revisión interna del equipo y congelamiento de versión Parcial.                                              | Integrante 5<br>Todos        | `docs/informe_parcial.md`<br>**Hito 60% Completado** |


---

### 4.3 Sprint 2 — Semana 7: Hito Final (\~100% de Entrega y Sustentación)

> **Objetivo del Hito:** Aplicación final pulida con GUI completa, módulo de accesos, documentación exhaustiva (informe técnico y manuales) y preparación de la sustentación oral.


| Día       | Actividad / Tarea                                                                                                                                                                                                                                                                                                    | Responsables                                 | Entregable Concreto                            |
| :---------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------- | :---------------------------------------------- |
| **Día 1** | **Módulo de Accesos y Transporte:**<br>• Programación de `modules/access_module.py` (generación de rutas en tren/bus/combi por destino).<br>• Refinamiento de prompts del LLM para narrativas de itinerario atractivas.                                                                                              | Integrante 3                                 | `access_module.py`<br>Prompts pulidos          |
| **Día 2** | **GUI Completa e Interactiva (9 Pantallas):**<br>• Implementación de badges numéricos 1..K sobre los marcadores en Folium.<br>• Modos de visualización: Vista General (15 lomas) vs. Modo Ruta Óptima (K lomas).<br>• Popups detallados de cada loma (costos, dificultad, atractivos).                               | Integrante 4                                 | `app.py` (versión final)                       |
| **Día 3** | **Manual de Usuario y Manual de Instalación:**<br>• Redacción de `docs/manual_instalacion.md` (requisitos, clone, venv, API keys y ejecución).<br>• Redacción de `docs/manual_usuario.md` (guía ilustrada paso a paso con capturas de pantalla).                                                                     | Integrante 5<br>Integrante 4                 | `manual_instalacion.md`<br>`manual_usuario.md` |
| **Día 4** | **Informe Técnico Final (Rúbrica Oficial):**<br>• Descripción exhaustiva de funcionalidades del software.<br>• Arquitectura inteligente detallada de los 3 componentes.<br>• Análisis de población objetivo (turistas, ciudadanos, instituciones, SERPAR).<br>• Comparativa de ventajas frente a software existente. | Integrante 5<br>Integrante 1<br>Integrante 2 | `docs/informe_tecnico.md`                      |
| **Día 5** | **Pruebas Finales y Empaquetado:**<br>• Pruebas de estrés y casos límite (presupuesto insuficiente, 1 solo día disponible, etc.).<br>• Verificación de compatibilidad multiplataforma (Windows, Linux, macOS).<br>• Limpieza y comentarios profesionales en el 100% del código fuente.                               | Todos los integrantes                        | Código limpio y testeado                       |
| **Día 6** | **Preparación de la Presentación y Demo:**<br>• Elaboración de diapositivas (PPT) con diagramas de arquitectura, fórmulas y demos.<br>• Ensayos de sustentación cronometrados (distribución de tiempos entre los 5 integrantes).                                                                                     | Todos los integrantes                        | Presentación PPT final                         |
| **Día 7** | **Entrega Final y Sustentación:**<br>• Subida de tags a GitHub, entrega de monografía/informe en la plataforma virtual.<br>• Sustentación y demostración en vivo del software ante el docente.                                                                                                                       | Todos los integrantes                        | **Hito 100% Finalizado**                       |


---

## 5. Matriz de Responsabilidades (RACI) para los 5 Integrantes

> **Convenciones:**  
> • **R (Responsible):** Quien ejecuta la tarea.  
> • **A (Accountable):** Quien aprueba y responde por el resultado final.  
> • **C (Consulted):** Quien aporta insumos o criterio técnico.  
> • **I (Informed):** Quien se mantiene al tanto del avance.


| Entregable / Componente                             | Int. 1 (Fuzzy) | Int. 2 (AG) | Int. 3 (LLM) | Int. 4 (GUI) | Int. 5 (QA/Doc) |
| :--------------------------------------------------- | :--------------: | :-----------: | :------------: | :------------: | :---------------: |
| **Catálogo de Destinos (`destinos.json`)**          | C              | C           | C            | **R / A**    | I               |
| **Módulo Difuso (`fuzzy_module.py`)**               | **R / A**      | C           | I            | I            | C               |
| **Algoritmo Genético (`genetic_algorithm.py`)**     | C              | **R / A**   | I            | I            | C               |
| **Módulo LLM &amp; NLP (`llm_module.py`)**          | I              | I           | **R / A**    | C            | C               |
| **Módulo de Mapeo (`mapping.py`)**                  | I              | **R / A**   | C            | I            | I               |
| **Módulo de Accesos (`access_module.py`)**          | I              | I           | **R / A**    | C            | I               |
| **Interfaz Streamlit + Folium (`app.py`)**          | C              | C           | C            | **R / A**    | C               |
| **Pipeline Integrador (`main.py`)**                 | C              | C           | C            | C            | **R / A**       |
| **Manual de Instalación (`manual_instalacion.md`)** | I              | I           | I            | C            | **R / A**       |
| **Manual de Usuario (`manual_usuario.md`)**         | I              | I           | I            | C            | **R / A**       |
| **Informe Técnico Final (`informe_tecnico.md`)**    | C              | C           | C            | C            | **R / A**       |
| **Diapositivas y Sustentación**                     | **R**          | **R**       | **R**        | **R**        | **A**           |


---

## 6. Estructura de Archivos del Proyecto

El repositorio mantendrá una disposición modular estricta:

```
si-project-unmsm/
├── app.py                     # Aplicación web interactiva principal (Streamlit + Folium)
├── main.py                    # Script de integración y pruebas CLI end-to-end
├── requirements.txt           # Dependencias fijadas (streamlit, folium, scikit-fuzzy, openai, etc.)
├── README.md                  # Especificación técnica completa y documentación central
├── data/
│   └── destinos.json          # Catálogo estructurado de las 15 lomas de Lima
├── modules/
│   ├── __init__.py
│   ├── fuzzy_module.py        # Sistema de inferencia Mamdani (4 variables + 20 reglas)
│   ├── genetic_algorithm.py   # Algoritmo Genético (cromosoma de permutación, OX, fitness)
│   ├── llm_module.py          # Extracción JSON de entidades y generación de itinerario
│   ├── access_module.py       # Instrucciones de transporte público y cómo llegar
│   └── mapping.py             # Mapeo matemático determinista días_disponibles -> K
├── tests/
│   ├── test_fuzzy.py          # Pruebas unitarias del motor difuso
│   ├── test_genetic.py        # Pruebas de restricciones y operadores genéticos
│   └── test_pipeline.py       # Prueba end-to-end con datos simulados
└── docs/
    ├── Enunciado_Entregables.md   # Este documento de gestión y cronograma
    ├── Enunciado_Proyecto_Parcial.pdf # Documento de requisitos del docente
    ├── manual_instalacion.md      # Guía técnica de instalación y despliegue
    ├── manual_usuario.md          # Manual ilustrado para el usuario final
    └── informe_tecnico.md         # Monografía e informe técnico de sustentación
```

---

## 7. Catálogo Oficial de Destinos (15 Lomas de Lima)

El catálogo incluye 15 lomas documentadas con coordenadas, nivel de esfuerzo y afluencia base:


| ID      | Destino                         | Distrito                | Dificultad    | Distancia Centro | Saturación Base | Acceso Clave                    |
| :------- | :------------------------------- | :----------------------- | :------------- | :---------------- | :--------------- | :------------------------------- |
| **L0**  | Lomas del Paraíso (+ Apu Siqay) | Villa María del Triunfo | Moderado      | \~1h             | 0.15            | Tren Eléctrico L1 + Combi       |
| **L1**  | Lomas de Carabayllo 2           | Carabayllo              | Fácil-Difícil | \~1.5h           | 0.20            | Bus alimentador + caminata      |
| **L2**  | Lomas de Primavera              | Carabayllo              | Fácil         | \~1h             | 0.10            | Bus Panamericana Norte          |
| **L3**  | Lomas de Manchay                | Ate                     | Moderado      | \~45 min         | 0.08            | Bus La Molina / Cieneguilla     |
| **L4**  | Lomas de Mangomarca             | San Juan de Lurigancho  | Moderado      | \~1h             | 0.15            | Tren L1 + bus auxiliar          |
| **L5**  | Lomas de Amancaes               | Rímac                   | Fácil         | \~40 min         | 0.45            | Corredor Azul Tacna             |
| **L6**  | Lomas de Lachay (Reserva)       | Huaura / Huaral         | Fácil-Mod     | \~2h             | 0.50            | Bus interprovincial Norte Chico |
| **L7**  | Lomas de Lúcumo                 | Pachacámac              | Fácil         | \~1h             | 0.45            | Panamericana Sur + colectivo    |
| **L8**  | Morro Solar                     | Chorrillos              | Fácil         | \~30 min         | 0.70            | Metropolitano + alimentador     |
| **L9**  | Huaca Pucllana                  | Miraflores              | Muy fácil     | \~15 min         | 0.85            | Corredor Azul / Metropolitano   |
| **L10** | Parque de la Reserva            | Cercado de Lima         | Muy fácil     | \~10 min         | 0.65            | Metropolitano Estación Estadio  |
| **L11** | Lomas de Ancón                  | Ancón                   | Fácil         | \~45 min         | 0.12            | Bus Panamericana Norte          |
| **L12** | Quebrada de Huaycoloro          | Lurigancho-Chosica      | Moderado      | \~1h             | 0.18            | Carretera Central + combi       |
| **L13** | Cerro de la Estrella            | Ate                     | Fácil         | \~40 min         | 0.40            | Carretera Central + colectivo   |
| **L14** | La Loma Amarilla                | Surco                   | Muy fácil     | \~20 min         | 0.55            | Metropolitano / Tren L1         |


---

## 8. Criterios de Aceptación para la Sustentación Final

Para garantizar la máxima calificación en la evaluación del docente, el proyecto deberá superar los siguientes hitos de control:

1. **Inferencia Difusa Mamdani:**
   - Debe responder con scores continuos $S_{\text{difuso}} \in [0, 10]$ en menos de 50 ms por destino.
   - 0 casos con fallas de defuzzificación (`NaN` o división por cero).
2. **Optimización con Algoritmo Genético:**
   - Cromosoma sin destinos repetidos en el 100% de los casos.
   - Convergencia comprobada: penalizaciones duras ($\Omega_{\text{presupuesto}}, \Omega_{\text{tiempo}}, \Omega_{\text{restricción}}$) deben llegar a $0$ en la mejor solución.
3. **Módulo LLM:**
   - Extracción confiable de parámetros JSON a partir de texto desestructurado.
   - Capacidad de conmutación automática a mock offline en caso de cortes de red o agotamiento de cuota de API.
4. **GUI Interactiva:**
   - Renderizado fluido del mapa Folium con zoom automático y marcadores con badges numéricos secuenciales 1..K.
   - Visualización clara del desglose del itinerario y guías de transporte público.
5. **Carpeta Documental:**
   - Manual de Instalación reproducible en entornos limpios (Windows, Linux, macOS).
   - Manual de Usuario con capturas explicativas.
   - Informe Técnico con la estructura académica requerida por la FISI - UNMSM.

