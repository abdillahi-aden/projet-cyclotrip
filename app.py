import logging

import streamlit as st

from components.map import render_route_map
from database.connection import DatabaseConnectionError
from database.queries import (
    find_address,
    list_communes,
    list_departments,
    list_numeros,
    list_voies,
    load_pois_near_route,
    search_addresses,
)
from services.routing import (
    RouteError,
    difficulty,
    get_route,
    route_geojson,
    route_gpx,
    same_location,
    split_route,
)
from services.weather import format_weather, get_weather


st.set_page_config(page_title="CycloTrip", page_icon="🚲", layout="wide")
logger = logging.getLogger(__name__)


def inject_style():
    st.markdown(
        """
        <style>
        .main .block-container { padding-top: 2rem; }
        .hero {
            padding: 2.5rem 0 1.5rem 0;
            border-bottom: 1px solid #e5e7eb;
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            font-size: 3rem;
            line-height: 1.05;
            margin: 0 0 .75rem 0;
            color: #102a43;
        }
        .hero p {
            font-size: 1.2rem;
            max-width: 840px;
            color: #425466;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .75rem;
            margin: 1.5rem 0 2rem 0;
        }
        .metric-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1rem;
            background: #ffffff;
        }
        .metric-card strong {
            display: block;
            font-size: 1.15rem;
            color: #0f766e;
        }
        .metric-card span { color: #475569; font-size: .9rem; }
        @media (max-width: 900px) {
            .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .hero h1 { font-size: 2.2rem; }
        }
        @media (max-width: 560px) {
            .metric-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar():
    st.sidebar.image("logo_app.png", width=96)
    st.sidebar.title("CycloTrip")
    return st.sidebar.radio(
        "Navigation",
        ["Accueil", "Recherche d'itinéraire", "À propos du projet"],
    )


def home_page():
    st.markdown(
        """
        <section class="hero">
            <h1>CycloTrip — Planificateur intelligent d'itinéraires cyclables</h1>
            <p>
                Concevez un parcours adapté à votre rythme, visualisez les étapes,
                découvrez les points d'intérêt et anticipez les conditions météo.
            </p>
        </section>
        <div class="metric-grid">
            <div class="metric-card"><strong>620 065</strong><span>adresses intégrées</span></div>
            <div class="metric-card"><strong>PostgreSQL/PostGIS</strong><span>base spatiale indexée</span></div>
            <div class="metric-card"><strong>OpenRouteService</strong><span>calcul d'itinéraires cyclables</span></div>
            <div class="metric-card"><strong>Données enrichies</strong><span>géographie, tourisme et météo</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Une application SIG orientée terrain")
        st.write(
            "CycloTrip combine une base d'adresses massive, des requêtes spatiales "
            "PostGIS, des API d'itinéraires et des données contextuelles pour préparer "
            "des parcours cyclables exploitables."
        )
        st.write("Application réalisée en langage Python par Abdillahi Aden et Karim Douar.")
    with right:
        st.image("logo_app.png", width=260)


def address_picker(label, key_prefix):
    st.subheader(label)
    query = st.text_input(
        "Adresse",
        key=f"{key_prefix}_query",
        placeholder="Sélectionnez une adresse",
    )
    if len(query.strip()) < 3:
        st.caption("Saisissez au moins 3 caractères pour lancer l'autocomplétion.")
        return None
    try:
        results = search_addresses(query)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return None
    if not results:
        st.info("Aucune adresse trouvée pour cette recherche.")
        return None
    labels = ["Sélectionnez une adresse"] + [address["label"] for address in results]
    selected = st.selectbox("Résultats", labels, key=f"{key_prefix}_result", index=0)
    if selected == "Sélectionnez une adresse":
        return None
    return next(address for address in results if address["label"] == selected)


def advanced_address_picker(label, key_prefix):
    st.subheader(label)
    try:
        departments = ["Sélectionnez une adresse"] + list_departments()
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return None
    dep = st.selectbox("Département", departments, key=f"{key_prefix}_dep", index=0)
    if dep == "Sélectionnez une adresse":
        return None

    try:
        communes = ["Sélectionnez une adresse"] + list_communes(dep)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return None
    commune = st.selectbox("Commune", communes, key=f"{key_prefix}_commune", index=0)
    if commune == "Sélectionnez une adresse":
        return None

    try:
        voies = ["Sélectionnez une adresse"] + list_voies(commune)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return None
    voie = st.selectbox("Voie", voies, key=f"{key_prefix}_voie", index=0)
    if voie == "Sélectionnez une adresse":
        return None

    try:
        numeros = ["Sélectionnez une adresse"] + list_numeros(voie, commune)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return None
    numero = st.selectbox("Numéro", numeros, key=f"{key_prefix}_numero", index=0)
    if numero == "Sélectionnez une adresse":
        return None

    try:
        return find_address(dep, commune, voie, numero)
    except DatabaseConnectionError as exc:
        st.error(str(exc))
        return None


def load_example(start_text, end_text):
    st.session_state.depart_query = start_text
    st.session_state.arrivee_query = end_text


def search_page():
    st.title("Recherche d'itinéraire cyclable")
    st.write("Choisissez un départ et une arrivée, puis ajustez la distance quotidienne souhaitée.")

    examples = [
        ("Lyon Part-Dieu", "Lyon"),
        ("Saint-Étienne", "Lyon"),
        ("Villeurbanne", "Lyon"),
    ]
    example_cols = st.columns(3)
    for col, (start_text, end_text) in zip(example_cols, examples):
        with col:
            st.button(
                f"{start_text} → {end_text}",
                on_click=load_example,
                args=(start_text, end_text),
                use_container_width=True,
            )

    mode = st.radio(
        "Mode de recherche",
        ["Autocomplétion", "Recherche avancée"],
        horizontal=True,
    )

    col_start, col_swap, col_end = st.columns([1, 0.18, 1])
    with col_start:
        start = advanced_address_picker("Départ", "depart_adv") if mode == "Recherche avancée" else address_picker("Départ", "depart")
    with col_swap:
        st.write("")
        st.write("")
        if st.button("↔", help="Inverser le départ et l'arrivée", use_container_width=True):
            st.session_state.depart_query, st.session_state.arrivee_query = (
                st.session_state.get("arrivee_query", ""),
                st.session_state.get("depart_query", ""),
            )
            st.rerun()
    with col_end:
        end = advanced_address_picker("Arrivée", "arrivee_adv") if mode == "Recherche avancée" else address_picker("Arrivée", "arrivee")

    daily_distance_km = st.slider("Distance quotidienne visée", 10, 120, 40, step=5)
    calculate = st.button("Calculer l'itinéraire", type="primary", use_container_width=True)

    if not calculate:
        return

    if not start or not end:
        st.warning("Sélectionnez une adresse de départ et une adresse d'arrivée.")
        return
    if same_location(start, end) or start.get("id") == end.get("id"):
        st.warning("Le départ et l'arrivée doivent être différents.")
        return

    with st.spinner("Calcul de l'itinéraire et des données associées..."):
        try:
            route = get_route(start, end)
            segments = split_route(route["line"], daily_distance_km)
            pois = load_pois_near_route(route["line"].wkt, route["line"].buffer(0.01).bounds)
        except DatabaseConnectionError as exc:
            st.error(str(exc))
            return
        except RouteError as exc:
            st.error(str(exc))
            return
        except Exception:
            logger.exception("Unexpected route calculation error")
            st.error("Une erreur est survenue pendant le calcul. Vérifiez les adresses puis réessayez.")
            return

    st.success("Itinéraire calculé.")
    metric_cols = st.columns(5)
    metric_cols[0].metric("Distance totale", f"{route['distance_km']:.1f} km")
    metric_cols[1].metric("Durée estimée", f"{route['duration_min'] / 60:.1f} h")
    metric_cols[2].metric("Dénivelé +", f"{route['ascent_m']:.0f} m")
    metric_cols[3].metric("Dénivelé -", f"{route['descent_m']:.0f} m")
    metric_cols[4].metric("Difficulté", difficulty(route["distance_km"], route["ascent_m"]))

    render_route_map(route, start, end, pois)

    st.subheader("Étapes quotidiennes")
    weather_start = get_weather(start["lat"], start["lon"])
    weather_end = get_weather(end["lat"], end["lon"])
    rows = []
    for segment in segments:
        weather = weather_start if segment["day"] == 1 else weather_end if segment["day"] == len(segments) else None
        rows.append(
            {
                "Jour": segment["day"],
                "Distance estimée": f"{segment['distance_km']:.1f} km",
                "Météo": format_weather(weather),
            }
        )
    st.dataframe(rows, hide_index=True, use_container_width=True)

    st.subheader("Points d'intérêt autour du parcours")
    if pois.empty:
        st.info("Aucun point d'intérêt n'a été trouvé à moins d'un kilomètre du parcours.")
    else:
        st.dataframe(
            pois[["poi", "description", "adresse", "code_postal", "site_internet"]],
            hide_index=True,
            use_container_width=True,
        )

    dl_cols = st.columns(2)
    dl_cols[0].download_button(
        "Télécharger le GPX",
        data=route_gpx(route),
        file_name="cyclotrip_itineraire.gpx",
        mime="application/gpx+xml",
        use_container_width=True,
    )
    dl_cols[1].download_button(
        "Télécharger le GeoJSON",
        data=route_geojson(route["geojson"]),
        file_name="cyclotrip_itineraire.geojson",
        mime="application/geo+json",
        use_container_width=True,
    )


def about_page():
    st.title("À propos du projet")
    st.write(
        "CycloTrip répond à un besoin simple : préparer un itinéraire cyclable réaliste "
        "en combinant données d'adresses, calcul réseau, enrichissement touristique et météo."
    )

    st.subheader("Architecture technique")
    st.code(
        """
Streamlit
  ├── Autocomplétion et interface de recherche
  ├── Carte Folium interactive
  └── Téléchargements GPX / GeoJSON

Services Python
  ├── OpenRouteService : itinéraires cyclables
  ├── OpenWeatherMap : météo par étape
  └── Shapely : géométrie et découpage

PostgreSQL / PostGIS
  ├── 620 065 adresses intégrées
  ├── index attributaires sur voie, commune, numéro, code postal
  └── index spatial GiST pour les points d'intérêt
        """.strip()
    )

    st.subheader("Traitements réalisés")
    st.write(
        "Les données d'adresses sont importées par lots, normalisées puis indexées dans "
        "PostgreSQL/PostGIS. Les points d'intérêt sont géolocalisés et interrogés par "
        "proximité autour du tracé via `ST_DWithin`."
    )
    st.write(
        "Abdillahi Aden a porté l'intégration SIG, la base PostGIS, les traitements "
        "géospatiaux, l'interface Streamlit et les connexions API. Karim Douar a contribué "
        "à la conception fonctionnelle, aux données et aux validations projet."
    )

    st.subheader("Liens")
    st.markdown("- [Application Streamlit](https://cyclotrip-france.streamlit.app/)")
    st.markdown("- [GitHub](https://github.com/abdillahi-aden/projet-cyclotrip)")
    st.markdown("- [LinkedIn Abdillahi Aden](https://www.linkedin.com/)")


def main():
    inject_style()
    page = sidebar()
    if page == "Accueil":
        home_page()
    elif page == "Recherche d'itinéraire":
        search_page()
    else:
        about_page()


if __name__ == "__main__":
    main()
