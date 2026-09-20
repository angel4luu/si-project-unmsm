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


def crear_mapa_lomas(destinos, ruta_ids=None):
    """Genera el mapa interactivo en Folium con los marcadores de lomas."""
    centro_lima = [-12.0464, -77.0428]
    mapa = folium.Map(location=centro_lima, zoom_start=10, tiles="OpenStreetMap")

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
    if 'resultado_optimizacion' not in st.session_state:
        st.session_state.resultado_optimizacion = None
    if 'perfil_usuario' not in st.session_state:
        st.session_state.perfil_usuario = None

    # Título Principal
    st.title("Sistema Inteligente de Rutas de Trekking en las Lomas de Lima")

    # Barra lateral
    with st.sidebar:
        st.header("Configuración del Turista")

        modo_entrada = st.radio("Modo de Entrada:", ["Texto Libre (IA Generativa)", "Formulario Guiado"])

        if modo_entrada == "Texto Libre (IA Generativa)":
            texto_usuario = st.text_area(
                "Describe tu viaje deseado:",
                value="Quiero hacer trekking 3 días en lomas verdes con dificultad moderada y no gastar más de 60 soles.",
                height=100
            )
            dias_input = None
            presupuesto_input = None
        else:
            texto_usuario = ""
            dias_input = st.slider("Días disponibles para viajar:", min_value=1, max_value=15, value=3)
            presupuesto_input = st.slider("Presupuesto máximo (Soles):", min_value=15, max_value=200, value=60, step=5)
            condicion_input = st.selectbox("Condición física:", ["Fácil", "Moderado", "Difícil"], index=1)
            intereses_input = st.multiselect("Intereses:", ["Naturaleza", "Arqueología", "Vistas Panorámicas", "Aventura"], default=["Naturaleza"])

        btn_optimizar = st.button("Generar Ruta Óptima", type="primary", use_container_width=True)

        if btn_optimizar:
            with st.spinner("Procesando: LLM -> Mapeo -> Lógica Difusa -> Algoritmo Genético..."):
                # 1. Extracción de entidades
                if modo_entrada == "Texto Libre (IA Generativa)":
                    perfil = extraer_preferencias_usuario(texto_usuario)
                else:
                    perfil = {
                        "dias_disponibles": dias_input,
                        "presupuesto_max": float(presupuesto_input),
                        "condicion_fisica": condicion_input,
                        "intereses": intereses_input,
                        "clima_preferido": "Garúa"
                    }

                # 2. Mapeo K
                k = dias_a_k(perfil.get("dias_disponibles", 3))

                # 3. Lógica Difusa
                scores_difusos = calcular_scores_todos_destinos(destinos)

                # 4. Algoritmo Genético
                resultado_ag = optimizar_ruta_lomas(
                    destinos=destinos,
                    scores_difusos=scores_difusos,
                    k=k,
                    presupuesto=perfil.get("presupuesto_max", 60.0),
                    dias_disponibles=perfil.get("dias_disponibles", 3)
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

    # ÁREA PRINCIPAL: Mapa y Resultados
    col_mapa, col_detalle = st.columns([3, 2])

    resultado = st.session_state.resultado_optimizacion

    with col_mapa:
        st.subheader("Mapa Interactivo de las Lomas")
        ruta_ids = resultado['ag']['ruta_ids'] if resultado else None

        if MAPAS_DISPONIBLES:
            mapa = crear_mapa_lomas(destinos, ruta_ids)
            st_folium(mapa, width="100%", height=560, returned_objects=[])
        else:
            st.info("Para visualizar el mapa interactivo en Folium, instala `pip install folium streamlit-folium`.")
            st.write("Lista de Destinos Catalogados:")
            for d in destinos:
                st.write(f"• **{d['id']}**: {d['nombre']} ({d['distrito']}) - Lat: {d['coordenadas']['lat']}, Lon: {d['coordenadas']['lon']}")

    with col_detalle:
        if resultado:
            ag = resultado['ag']
            st.subheader("Resumen de la Ruta Óptima")

            m1, m2, m3 = st.columns(3)
            m1.metric("Destinos", f"{resultado['k']}")
            m2.metric("Costo Total", f"S/ {ag['costo_total']:.2f}")
            m3.metric("Distancia", f"{ag['distancia_total_km']:.1f} km")

            st.write("**Secuencia de Visita:**")
            badges = [f"**{i+1}.** {destinos_dict[did]['nombre']}" for i, did in enumerate(ag['ruta_ids'])]
            st.markdown(" -> ".join(badges))

            tabs = st.tabs(["Itinerario", "Cómo Llegar", "Scores Difusos"])

            with tabs[0]:
                st.markdown(resultado['itinerario'])

            with tabs[1]:
                st.write("### Instrucciones de Transporte Público")
                for did in ag['ruta_ids']:
                    guia = obtener_guia_acceso(did)
                    with st.expander(f" {guia['nombre']} (~{guia['tiempo_total_min']} min, S/{guia['costo_total_soles']})"):
                        st.write(f"**Punto de inicio:** {guia['punto_partida_recomendado']}")
                        st.write(f"**Transporte:** {guia['medio_transporte']}")
                        for paso in guia['pasos']:
                            st.write(f"• {paso}")

            with tabs[2]:
                st.write("### Puntuación de Recomendación Difusa [0-10]")
                scores_df = [
                    {"ID": did, "Loma": destinos_dict[did]["nombre"], "Score Difuso": resultado['scores_difusos'][did]}
                    for did in ag['ruta_ids']
                ]
                st.dataframe(scores_df, use_container_width=True)
        else:
            st.info("Configura tus preferencias en la barra lateral y presiona **Generar Ruta Óptima** para visualizar la recomendación.")
            st.write("###  Catálogo de las 15 Lomas de Lima:")
            destinos_tabla = [
                {"ID": d['id'], "Nombre": d['nombre'], "Distrito": d['distrito'], "Dificultad": d['dificultad'], "Costo": f"S/{d['costo_estimado']}"}
                for d in destinos
            ]
            st.dataframe(destinos_tabla, height=450, use_container_width=True)


if __name__ == "__main__":
    main()
