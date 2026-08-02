# CycloTrip - Planificateur intelligent d'itinéraires cyclables

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cyclotrip-france.streamlit.app/)

Application en ligne : https://cyclotrip-france.streamlit.app/

Dépôt GitHub : https://github.com/abdillahi-aden/projet-cyclotrip

## Contexte

CycloTrip est un projet réalisé dans le cadre de la formation Data Engineer de DataScientest. L'objectif est de construire une solution complète autour des données de mobilité et de tourisme cyclable : ingestion, stockage spatial, requêtes PostGIS, calcul d'itinéraires, enrichissement touristique, météo et visualisation cartographique.

## Objectif fonctionnel

L'application permet de rechercher une adresse de départ et une adresse d'arrivée, de calculer un itinéraire cyclable, de visualiser le tracé sur une carte interactive, d'identifier les points d'intérêt autour du parcours, d'estimer les étapes quotidiennes et de télécharger le résultat en GPX ou GeoJSON.

## Fonctionnalités

- Autocomplétion d'adresses depuis une base de 620 065 adresses.
- Recherche avancée par département, commune, voie et numéro.
- Validation utilisateur avant le calcul : aucune adresse par défaut et blocage des départs/arrivées identiques.
- Messages utilisateur clairs en cas d'erreur base de données, OpenRouteService ou météo.
- Calcul d'itinéraires cyclables avec OpenRouteService.
- Carte Folium interactive avec tracé, départ, arrivée et points d'intérêt.
- Distance totale, durée estimée, dénivelé positif/négatif et niveau de difficulté.
- Découpage en étapes quotidiennes selon la distance choisie.
- Données météo par étape quand la clé OpenWeatherMap est disponible.
- Téléchargement GPX et GeoJSON.

## Stack technique

- Python
- Streamlit
- PostgreSQL / PostGIS
- Supabase
- Folium
- Shapely
- Pandas
- OpenRouteService API
- OpenWeatherMap API
- GitHub Actions
- Streamlit Community Cloud

## Architecture du dépôt

```text
app.py                    Point d'entrée Streamlit
components/               Composants d'interface et carte
database/                 Connexion et requêtes PostgreSQL/PostGIS
services/                 Itinéraire, météo et logique métier
tests/                    Tests unitaires
.streamlit/               Configuration Streamlit
.github/workflows/        Intégration continue
```

L'ancien fichier `test_streamlit_final_v2.py` reste présent comme wrapper de compatibilité pour un déploiement Streamlit existant.

## Données et SIG

Les adresses sont importées dans PostgreSQL/PostGIS, normalisées puis indexées sur les champs de recherche principaux : voie, commune, numéro et code postal. Les points d'intérêt sont stockés avec une géométrie `Point` et interrogés autour du tracé avec un index spatial GiST et `ST_DWithin`.

## Configuration

Créer un fichier `.env` local ou configurer les secrets Streamlit avec les variables suivantes :

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_SSLMODE=require
ORS_API_KEY=
WEATHER_API_KEY=
```

Ne versionnez jamais `.env` dans Git.

## Lancement local

```bash
streamlit run app.py
```

## Tests

```bash
python -m pytest
```
