import os
import json
import streamlit as st

# Módulos del sistema inteligente
from modules.mapping import dias_a_k
from modules.fuzzy_module import calcular_scores_todos_destinos
from modules.genetic_algorithm import optimizar_ruta_lomas
from modules.llm_module import extraer_preferencias_usuario, generar_itinerario_narrativo
from modules.access_module import obtener_guia_acceso

# Verificación de librerías de mapas
try:
    import folium
    from streamlit_folium import st_folium
    MAPAS_DISPONIBLES = True
except ImportError:
    MAPAS_DISPONIBLES = False


# Configuración inicial de Streamlit
st.set_page_config(
    page_title="Rutas de Trekking - Lomas de Lima",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def cargar_destinos():
    ruta_json = os.path.join(os.path.dirname(__file__), "data", "destinos.json")
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def crear_mapa_lomas(destinos, ruta_ids=None, nodo_base=None):
    """Genera el mapa interactivo en Folium con los marcadores de lomas y el nodo base arrastrable."""
    centro_lima = [-12.0464, -77.0428]
    lat_mapa = nodo_base["lat"] if nodo_base else centro_lima[0]
    lon_mapa = nodo_base["lon"] if nodo_base else centro_lima[1]
    
    mapa = folium.Map(location=[lat_mapa, lon_mapa], zoom_start=10, tiles="OpenStreetMap")

    # Marcador de Alojamiento / Nodo Base (d0) Arrastrable (draggable=True)
    if nodo_base:
        folium.Marker(
            location=[nodo_base["lat"], nodo_base["lon"]],
            popup=folium.Popup("<div style='font-family: sans-serif;'><b>Tu Alojamiento (Nodo Base)</b><br/>¡Arrastra este pin o haz clic en el mapa para mover tu hospedaje!</div>", max_width=220),
            tooltip="Tu Alojamiento (Arrastra para mover)",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
            draggable=True
        ).add_to(mapa)

    orden_map = {}
    if ruta_ids:
        orden_map = {did: idx + 1 for idx, did in enumerate(ruta_ids)}

    for d in destinos:
        did = d['id']
        coords = [d['coordenadas']['lat'], d['coordenadas']['lon']]

        if did in orden_map:
            # Marcador de ruta con badge de orden
            orden = orden_map[did]
            icono = folium.Icon(color="green", icon="flag", prefix="fa")
            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 180px;">
                <h4 style="margin: 0; color: #1e7e34;">#{orden} {d['nombre']}</h4>
                <p style="margin: 4px 0;"><b>Distrito:</b> {d['distrito']}</p>
                <p style="margin: 4px 0;"><b>Dificultad:</b> {d['dificultad']}</p>
                <p style="margin: 4px 0;"><b>Costo Est.:</b> S/ {d['costo_estimado']}</p>
                <p style="margin: 4px 0; font-size: 12px;">{d.get('transporte_principal', '')}</p>
            </div>
            """
        else:
            # Marcador general inactivo
            icono = folium.Icon(color="gray", icon="mountain", prefix="fa")
            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 160px;">
                <h4 style="margin: 0;">{d['nombre']}</h4>
                <p style="margin: 4px 0;"><b>Distrito:</b> {d['distrito']}</p>
                <p style="margin: 4px 0;"><b>Dificultad:</b> {d['dificultad']}</p>
            </div>
            """

        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{d['id']}: {d['nombre']}",
            icon=icono
        ).add_to(mapa)

    return mapa


def main():
    destinos = cargar_destinos()
    destinos_dict = {d['id']: d for d in destinos}

    # Inicializar estado de sesión para persistencia entre renders
    # Inicializar estado de sesión para persistencia entre renders
    if 'resultado_optimizacion' not in st.session_state:
        st.session_state.resultado_optimizacion = None
    if 'perfil_usuario' not in st.session_state:
        st.session_state.perfil_usuario = None
    if 'nodo_base' not in st.session_state:
        st.session_state.nodo_base = {"lat": -12.0464, "lon": -77.0428}  # Centro de Lima por defecto

    # Título Principal
    st.title("Sistema Inteligente de Rutas de Trekking en las Lomas de Lima")

    # Barra lateral unificada (Diseño Híbrido UX)
    with st.sidebar:
        st.header("Perfil del Turista")

        st.subheader("1. Parámetros de ruta (AG)")
        dias_input = st.slider("Días disponibles para viajar:", min_value=1, max_value=15, value=3, help="Determina cuántas lomas (K) se seleccionarán.")
        presupuesto_input = st.slider("Presupuesto máximo total (S/):", min_value=15, max_value=300, value=60, step=5, help="Límite monetario para la penalización del AG.")
        condicion_input = st.selectbox("Condición física del viajero:", ["Fácil", "Moderado", "Difícil"], index=1)

        st.subheader("2. Preferencias difusas y clima (IA)")
        texto_usuario = st.text_area(
            "Preferencias adicionales (Opcional):",
            placeholder="Ejemplo: 'Prefiero lomas poco concurridas (baja saturación), muy seguras, con clima de neblina/garúa y senderos de acceso fácil.'",
            height=110,
            help="Orienta las 4 variables difusas: Saturación esperada, Nivel de Seguridad, Clima/Verdor y Accesibilidad."
        )

        st.markdown("---")
        st.caption("**Punto de Partida (Alojamiento):** Arrastra el marcador rojo en el mapa para establecer tu ubicación exacta.")

        btn_optimizar = st.button("Generar ruta óptima", type="primary", use_container_width=True)

        if btn_optimizar:
            with st.spinner("Procesando: LLM -> Mapeo -> Lógica Difusa -> Algoritmo Genético..."):
                # 1. Extracción de entidades de texto libre o fallback a formulario
                if texto_usuario.strip():
                    perfil_extraido = extraer_preferencias_usuario(texto_usuario)
                else:
                    perfil_extraido = {}

                perfil = {
                    "dias_disponibles": dias_input,
                    "presupuesto_max": float(presupuesto_input),
                    "condicion_fisica": condicion_input,
                    "clima_preferido": perfil_extraido.get("clima_preferido", "Garúa"),
                    "intereses": perfil_extraido.get("intereses", ["Naturaleza"]),
                    "nodo_base": st.session_state.nodo_base
                }

                nodo_base_actual = st.session_state.nodo_base

                # 2. Mapeo K
                k = dias_a_k(perfil["dias_disponibles"])

                # 3. Lógica Difusa (Evaluación de incertidumbre)
                scores_difusos = calcular_scores_todos_destinos(destinos)

                # 4. Algoritmo Genético (con costo de desplazamiento radial desde nodo_base)
                resultado_ag = optimizar_ruta_lomas(
                    destinos=destinos,
                    scores_difusos=scores_difusos,
                    k=k,
                    presupuesto=perfil["presupuesto_max"],
                    dias_disponibles=perfil["dias_disponibles"],
                    nodo_base=nodo_base_actual
                )

                # 5. Itinerario narrativo
                itinerario = generar_itinerario_narrativo(resultado_ag, perfil)

                # Guardar en sesión
                st.session_state.resultado_optimizacion = {
                    'ag': resultado_ag,
                    'scores_difusos': scores_difusos,
                    'itinerario': itinerario,
                    'k': k
                }
                st.session_state.perfil_usuario = perfil
                st.success("¡Ruta óptima calculada exitosamente!")

    # ÁREA PRINCIPAL: Layout Jerárquico Reorganizado
    st.subheader("Mapa de las Lomas de Lima")
    st.caption("**Alojamiento (Pin Rojo):** Arrastra el marcador rojo en el mapa para ubicar tu hospedaje/nodo base.")

    resultado = st.session_state.resultado_optimizacion
    ruta_ids = resultado['ag']['ruta_ids'] if resultado else None

    if MAPAS_DISPONIBLES:
        mapa = crear_mapa_lomas(destinos, ruta_ids, st.session_state.nodo_base)
        mapa_output = st_folium(mapa, width="100%", height=480, returned_objects=["last_active_drawing"])

        nueva_pos = None

        # Capturar únicamente el arrastre/soltado del marcador (last_active_drawing)
        if mapa_output and mapa_output.get("last_active_drawing"):
            drawing = mapa_output["last_active_drawing"]
            if isinstance(drawing, dict) and "geometry" in drawing:
                coords = drawing["geometry"].get("coordinates", [])
                if len(coords) >= 2:
                    # Folium / GeoJSON usa [lon, lat]
                    d_lon = round(coords[0], 4)
                    d_lat = round(coords[1], 4)

                    # Verificar si coincide con una loma catalogada
                    es_loma = any(
                        abs(round(d["coordenadas"]["lat"], 4) - d_lat) < 0.005 and
                        abs(round(d["coordenadas"]["lon"], 4) - d_lon) < 0.005
                        for d in destinos
                    )

                    if not es_loma:
                        nueva_pos = {"lat": d_lat, "lon": d_lon}

        # Si se detectó una nueva posición por arrastre válida, actualizar
        if nueva_pos and (nueva_pos["lat"] != st.session_state.nodo_base["lat"] or nueva_pos["lon"] != st.session_state.nodo_base["lon"]):
            st.session_state.nodo_base = nueva_pos
            st.toast(f"Alojamiento movido a ({nueva_pos['lat']}, {nueva_pos['lon']})")
            st.rerun()
    else:
        st.info("Para visualizar el mapa interactivo en Folium, instala `pip install folium streamlit-folium`.")

    st.markdown("---")

    # SECCIÓN DE RESULTADOS DETALLADOS
    if resultado:
        ag = resultado['ag']
        col_tit, col_reset = st.columns([4, 1])
        with col_tit:
            st.subheader("Resumen de la ruta óptima")
        with col_reset:
            if st.button("Nueva búsqueda", help="Limpia la ruta actual para realizar otra consulta manteniendo tu punto de partida."):
                st.session_state.resultado_optimizacion = None
                st.session_state.perfil_usuario = None
                st.rerun()

        # 1. Tarjetas de Métricas Principales (4 Columnas)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Destinos (K)", f"{resultado['k']}")
        m2.metric("Costo total", f"S/ {ag['costo_total']:.2f}")
        m3.metric("Distancia radial", f"{ag['distancia_total_km']:.1f} km")
        score_promedio = sum(resultado['scores_difusos'].get(did, 5.0) for did in ag['ruta_ids']) / max(1, len(ag['ruta_ids']))
        m4.metric("Score difuso prom.", f"{score_promedio:.2f} / 10")

        # 2. Secuencia de Visita con Badges Visuales
        st.write("**Secuencia recomendada de excursiones:**")
        cols_badges = st.columns(min(6, len(ag['ruta_ids'])))
        for idx, did in enumerate(ag['ruta_ids']):
            with cols_badges[idx % len(cols_badges)]:
                st.success(f"**Día {idx+1}**\n\n{destinos_dict[did]['nombre']}")

        nb = st.session_state.nodo_base
        st.caption(f"**Alojamiento (Nodo Base $d_0$):** Latitud {nb['lat']}, Longitud {nb['lon']}")

        st.markdown("<br/>", unsafe_allow_html=True)

        # 3. Pestañas de Detalles e Investigación Académica
        tabs = st.tabs(["Itinerario", "Guía de accesos", "Desplazamiento radial", "Scores difusos", "Métricas del AG"])

        with tabs[0]:
            st.markdown(resultado['itinerario'])

        with tabs[1]:
            st.write("### Instrucciones de Transporte Público")
            for did in ag['ruta_ids']:
                guia = obtener_guia_acceso(did)
                with st.expander(f"{guia['nombre']} (~{guia['tiempo_total_min']} min, S/{guia['costo_total_soles']})"):
                    st.write(f"**Punto de inicio:** {guia['punto_partida_recomendado']}")
                    st.write(f"**Transporte:** {guia['medio_transporte']}")
                    for paso in guia['pasos']:
                        st.write(f"• {paso}")

        with tabs[2]:
            st.write("### Desglose de Desplazamientos Radiales (Ida / Vuelta Diaria)")
            if ag.get("tramos"):
                tramos_df = [
                    {"Origen": t["de"], "Destino": t["hacia"], "Distancia (km)": f"{t['distancia_km']} km"}
                    for t in ag["tramos"]
                ]
                st.dataframe(tramos_df, use_container_width=True)
            else:
                st.write("Excursión de 1 solo destino desde el nodo base.")

        with tabs[3]:
            st.write("### Puntuación de Recomendación Difusa [0-10]")
            scores_df = [
                {"ID": did, "Loma": destinos_dict[did]["nombre"], "Score Difuso": round(resultado['scores_difusos'][did], 2)}
                for did in ag['ruta_ids']
            ]
            st.dataframe(scores_df, use_container_width=True)

        with tabs[4]:
            st.write("### Diagnóstico Heurístico y Convergencia Evolutiva")
            st.write(f"**Método de Resolución:** `{ag.get('metodo', 'algoritmo_genetico')}`")
            st.write(f"**Fitness Máximo Alcanzado:** `{ag.get('fitness', 0):.3f}`")
            if "grafica_ascii" in ag:
                st.code(ag["grafica_ascii"], language="text")

    else:
        st.info("Configura tus preferencias en la barra lateral y presiona **Generar ruta óptima** para calcular tu itinerario.")
        st.write("### Catálogo de las 15 Lomas de Lima:")
        destinos_tabla = [
            {"ID": d['id'], "Nombre": d['nombre'], "Distrito": d['distrito'], "Dificultad": d['dificultad'], "Costo": f"S/{d['costo_estimado']}"}
            for d in destinos
        ]
        st.dataframe(destinos_tabla, height=350, use_container_width=True)


if __name__ == "__main__":
    main()
