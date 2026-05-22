# 🚴 CycloTrip - Plateforme d’itinéraires cyclables intelligents

## 📌 Contexte du projet

Projet réalisé dans le cadre de la formation Data Engineer de DataScientest.

L’objectif du projet était de construire une pipeline data complète autour des données de mobilité et de tourisme cyclable :

- collecte de données,
- organisation des données,
- stockage relationnel spatial,
- consommation des données,
- visualisation cartographique,
- déploiement cloud.

Le projet suit une architecture Data Engineering complète allant de l’ingestion des données jusqu’au déploiement d’une application interactive.

---

# 🎯 Objectifs

L’application permet :

- la recherche d’itinéraires cyclables,
- la visualisation des trajets sur carte interactive,
- l’exploitation de données géographiques spatiales,
- l’intégration de points d’intérêt touristiques,
- l’utilisation d’API de routage et météo.

---

# 🛠️ Stack technique

## Backend / Data Engineering

- Python
- PostgreSQL
- PostGIS
- SQL
- Supabase

## Data Visualization

- Streamlit
- Folium
- GeoPandas

## APIs

- OpenRouteService API
- OpenWeather API

## Déploiement

- GitHub
- Streamlit Community Cloud

---
# 🚴 CycloTrip - Plateforme d’itinéraires cyclables intelligents

🌍 **Application en ligne** :  
👉 https://cyclotrip-france.streamlit.app/

📂 **Repository GitHub** :  
👉 https://github.com/abdillahi-aden/projet-cyclotrip

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ton-app.streamlit.app)

---

# 🗂️ Architecture du projet

```text
CSV / APIs
     ↓
Python ETL
     ↓
PostgreSQL + PostGIS (Supabase)
     ↓
Requêtes SQL spatiales
     ↓
Application Streamlit
     ↓
Déploiement Cloud
