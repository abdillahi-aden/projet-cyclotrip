from dotenv import load_dotenv
import os

load_dotenv()
import streamlit as st
import requests
import folium
from folium.plugins import MarkerCluster
from folium.map import LayerControl
import geopandas as gpd
from shapely.geometry import Point, LineString
import folium.plugins
import numpy as np
import pandas as pd
import psycopg2
from streamlit_folium import folium_static

# Configuration de la barre latérale et du layout principal, doit être la première commande Streamlit utilisée.
st.set_page_config(layout="wide")
# Établissement d'une connexion persistante à la base de données
@st.cache_resource
def connect_db():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        sslmode="require"
    )



# fonction pour trouver les coordonnées basées sur l'adresse complète
conn = connect_db()

# Fonction pour trouver les coordonnées basées sur l'adresse complète, optimisation avec un index sur les colonnes utilisées
def find_coordinates(nom_voie, numero, code_postal, nom_commune, conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT lon, lat FROM adresses
            WHERE nom_voie ILIKE %s AND numero = %s AND CAST(code_postal AS TEXT) LIKE %s AND nom_commune ILIKE %s
            LIMIT 1;
        """, (f'%{nom_voie}%', str(numero), code_postal, f'%{nom_commune}%'))
        result = cur.fetchone()
    return result if result else (None, None)

# Fonction pour charger et filtrer les POI directement dans la requête SQL pour améliorer les performances
def load_and_filter_pois(route, conn):
    buffer = route.buffer(0.01)  # Création d'une zone tampon autour de l'itinéraire
    # Conversion des coordonnées en format texte pour utilisation dans la requête SQL
    bounds = buffer.bounds
    bbox_filter = f"geom && ST_MakeEnvelope({bounds[0]}, {bounds[1]}, {bounds[2]}, {bounds[3]}, 4326)"
    sql = f"""
    SELECT * FROM pois WHERE {bbox_filter} AND ST_DWithin(geom, ST_SetSRID(ST_GeomFromText('{route.wkt}'), 4326), 1000);
    """
    nearby_pois = gpd.read_postgis(sql, conn, geom_col='geom')

    return nearby_pois
    


################################


# Fonction pour récupérer l'itinéraire depuis OpenRouteService
def get_route(start, end, api_key):
    url = f"https://api.openrouteservice.org/v2/directions/cycling-regular?api_key={api_key}&start={start}&end={end}"
    response = requests.get(url)
    data = response.json()
    geometry = data['features'][0]['geometry']['coordinates']
    route = LineString(geometry)
    return route



# Fonction pour récupérer les données météorologiques à partir de OpenWeatherMap
def get_weather(api_key, latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    return data

# Fonction pour diviser l'itinéraire en segments journaliers en utilisant des itinéraires cyclistes réels
def divide_route_into_daily_segments(route, daily_distance_km):
    total_length_km = route.length * 111  # Conversion approximative de degrés à kilomètres
    num_days = int(np.ceil(total_length_km / daily_distance_km))
    points = [route.interpolate(fraction, normalized=True) for fraction in np.linspace(0, 1, num_days+1)]

    segments = []
    for i in range(len(points) - 1):
        start_point = points[i]
        end_point = points[i + 1]
        segment_route = get_route(f"{start_point.x},{start_point.y}", f"{end_point.x},{end_point.y}",api_key_ors)
        segments.append(segment_route)
    return segments

# Paramètres API et coordonnées
api_key_ors = os.getenv("ORS_API_KEY")
api_key_weather = os.getenv("WEATHER_API_KEY")


# Configuration de la barre latérale

st.sidebar.image("logo_app.png", width=100)  # Ajustez le chemin vers votre logo
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisissez une page",
    ["Accueil", "Application CycloTrip"]
)
# Gestion de l'affichage selon la page sélectionnée
if page == "Accueil":
    intro = st.container()
    with intro:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.image("logo_app.png", width=500)
            
        st.markdown("<h1 style='text-align: center;'>Application de création d'itinéraires cycliste </h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Réalisée en language Python</h3>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>Abdillahi ADEN</h4>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center;'>Karim DOUAR</h4>", unsafe_allow_html=True)
        
        
        footlogo1, footlogo2, footlogo3 = st.columns((1.4, 1, 1))
        with footlogo2:
            st.image("DataScientest_logo.png", width=200)
        
elif page == "Application CycloTrip":
   
    conn = connect_db()
    # Chargement initial des données
    @st.cache_data
    def load_data():
        conn = connect_db()
        df = pd.read_sql("SELECT DISTINCT code_postal FROM public.adresses;", conn)
        #conn.close()
        return df

    data = load_data()
    data['code_postal'] = data['code_postal'].astype(str)

    @st.cache_data
    def load_communes(dep, prefix=""):
        conn = connect_db()
        # Convertissez code_postal en texte avant d'utiliser LIKE
        query = """
        SELECT DISTINCT nom_commune 
        FROM public.adresses 
        WHERE CAST(code_postal AS TEXT) LIKE %s;
        """
        df = pd.read_sql(query, conn, params=[f"{dep}%"])
        #conn.close()
        return df


    @st.cache_data
    def load_voies(commune, prefix=""):
        conn = connect_db()
        query = f"SELECT DISTINCT nom_voie FROM public.adresses WHERE nom_commune = %s;"
        df = pd.read_sql(query, conn, params=[commune])
        #conn.close()
        return df

    @st.cache_data
    def load_numeros(voie, commune):
        conn = connect_db()
        query = """
        SELECT DISTINCT numero 
        FROM public.adresses 
        WHERE nom_voie = %s AND nom_commune = %s
        ORDER BY numero;
        """
        df = pd.read_sql(query, conn, params=[voie, commune])
        #conn.close()
        return df



    # Interface utilisateur avec Streamlit
    st.title('Planifiez Votre Parcours Cycliste')
    # Sélection du département de départ
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Départ")
        selected_dep_depart = st.selectbox('Département de départ', data['code_postal'].apply(lambda x: x[:2]).unique())
        selected_commune_depart = st.selectbox('Commune de départ', load_communes(selected_dep_depart))
        selected_voie_depart = st.selectbox('Voie de départ', load_voies(selected_commune_depart))
        selected_numero_depart = st.selectbox('Numéro de départ', load_numeros(selected_voie_depart, selected_commune_depart))
        
        # Répétez le processus pour l'adresse d'arrivée
    with col2:
        st.subheader("Arrivée")
        selected_dep_arrivee = st.selectbox('Département d\'arrivée', data['code_postal'].apply(lambda x: x[:2]).unique())
        selected_commune_arrivee = st.selectbox('Commune d\'arrivée', load_communes(selected_dep_arrivee))
        selected_voie_arrivee = st.selectbox('Voie d\'arrivée', load_voies(selected_commune_arrivee))
        selected_numero_arrivee = st.selectbox('Numéro d\'arrivée', load_numeros(selected_voie_arrivee, selected_commune_arrivee))
    # Widget pour permettre à l'utilisateur de définir la distance quotidienne souhaitée
    daily_distance_km = st.number_input("Distance quotidienne en km", min_value=5, value=30, step=5)


    # Bouton pour exécuter le traitement
    if st.button('Calculer l’itinéraire'):
        # Obtenez les coordonnées pour les adresses de départ et d'arrivée
        start_lon, start_lat = find_coordinates(selected_voie_depart, selected_numero_depart, f"{selected_dep_depart}%", selected_commune_depart, conn)
        end_lon, end_lat = find_coordinates(selected_voie_arrivee, selected_numero_arrivee, f"{selected_dep_arrivee}%", selected_commune_arrivee, conn)

        if start_lon and end_lon:
            start_coords = f"{start_lon},{start_lat}"
            end_coords = f"{end_lon},{end_lat}"
            route = get_route(start_coords, end_coords, api_key_ors)
            daily_segments = divide_route_into_daily_segments(route, daily_distance_km)
            # Récupération des données météorologiques pour le point de départ et d'arrivée
            weather_data_start = get_weather(api_key_weather, start_lat, start_lon)
            weather_data_end = get_weather(api_key_weather, end_lat, end_lon)

            # Conversion de la vitesse du vent de m/s à km/h
            wind_speed_start_kmh = weather_data_start['wind']['speed'] * 3.6
            wind_speed_end_kmh = weather_data_end['wind']['speed'] * 3.6
           
            # Affichage de chaque segment sur une carte avec des espaces entre les cartes
            for i in range(0, len(daily_segments), 2):
                cols = st.columns([1, 0.8, 1])  # Crée deux colonnes avec un espace au milieu
                for j in range(2):
                    if i + j < len(daily_segments):
                        with cols[j*2]:
                            segment = daily_segments[i + j]
                            st.header(f"Jour {i + j + 1}")
                            mymap = folium.Map(location=[segment.centroid.y, segment.centroid.x], zoom_start=12)

                            # Charger les POIs à proximité pour ce segment et les ajouter en cluster
                            nearby_pois = load_and_filter_pois(segment, conn)
                            poi_cluster = MarkerCluster()
                            for _, poi in nearby_pois.iterrows():
                                popup_content = f"<b>POI :</b> {poi['poi']}<br><b>Description :</b> {poi['description']}<br><b>Adresse :</b> {poi['adresse']}<br><b>Code postal :</b> {poi['code_postal']}<br><b>Site Internet :</b> <a href='{poi['site_internet']}'>{poi['site_internet']}</a>"
                                folium.Marker(location=[poi['latitude'], poi['longitude']], popup=folium.Popup(popup_content, max_width=300)).add_to(poi_cluster)
                            poi_cluster.add_to(mymap)

                            # Ajouter le trajet sur la carte
                            folium.plugins.AntPath(locations=[(coord[1], coord[0]) for coord in segment.coords], color='blue', delay=1000, dash_array=[50, 100]).add_to(mymap)

                            # Gérer les informations météorologiques pour le premier et dernier segment
                            if i + j == 0:
                                popup_content = f"<b>Adresse de départ :</b> {selected_numero_depart} {selected_voie_depart}, {selected_dep_depart} {selected_commune_depart}<br><b>Météo :</b><br>Température : {weather_data_start['main']['temp']} °C<br>Conditions : {weather_data_start['weather'][0]['description']}<br>Vitesse du vent : {wind_speed_start_kmh:.2f} km/h<br>Direction du vent : {weather_data_start['wind']['deg']}°"
                                folium.Marker(location=[start_lat, start_lon], popup=folium.Popup(popup_content, max_width=300), icon=folium.Icon(color='green')).add_to(mymap)
                            elif i + j == len(daily_segments) - 1:
                                popup_content = f"<b>Adresse d'arrivée :</b> {selected_numero_arrivee} {selected_voie_arrivee}, {selected_dep_arrivee} {selected_commune_arrivee}<br><b>Météo :</b><br>Température : {weather_data_end['main']['temp']} °C<br>Conditions : {weather_data_end['weather'][0]['description']}<br>Vitesse du vent : {wind_speed_end_kmh:.2f} km/h<br>Direction du vent : {weather_data_end['wind']['deg']}°"
                                folium.Marker(location=[end_lat, end_lon], popup=folium.Popup(popup_content, max_width=300), icon=folium.Icon(color='red')).add_to(mymap)
                            
                            LayerControl().add_to(mymap)
                            folium_static(mymap)
        else:
            st.error("L'une des adresses n'a pas pu être localisée.")

    pass

