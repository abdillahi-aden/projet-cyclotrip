import folium
from folium.plugins import AntPath, MarkerCluster
from streamlit_folium import folium_static


def render_route_map(route, start, end, pois):
    line = route["line"]
    route_map = folium.Map(
        location=[line.centroid.y, line.centroid.x],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    AntPath(
        locations=[(lat, lon) for lon, lat in line.coords],
        color="#0f766e",
        weight=5,
        delay=900,
    ).add_to(route_map)

    folium.Marker(
        [float(start["lat"]), float(start["lon"])],
        popup=f"Départ : {start['label']}",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(route_map)
    folium.Marker(
        [float(end["lat"]), float(end["lon"])],
        popup=f"Arrivée : {end['label']}",
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(route_map)

    if pois is not None and not pois.empty:
        cluster = MarkerCluster(name="Points d'intérêt").add_to(route_map)
        for _, poi in pois.iterrows():
            website = poi.get("site_internet") or ""
            popup = (
                f"<b>{poi.get('poi') or 'Point d’intérêt'}</b><br>"
                f"{poi.get('description') or ''}<br>"
                f"{poi.get('adresse') or ''}"
            )
            if website:
                popup += f"<br><a href='{website}' target='_blank'>{website}</a>"
            folium.Marker(
                [poi["latitude"], poi["longitude"]],
                popup=folium.Popup(popup, max_width=320),
            ).add_to(cluster)

    folium.LayerControl().add_to(route_map)
    folium_static(route_map, width=None, height=560)
