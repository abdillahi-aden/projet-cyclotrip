# CycloTrip — Planification d’itinéraires cyclables

Application SIG en Python et Streamlit associant recherche d’adresses, calcul d’itinéraires cyclables, points d’intérêt et cartographie interactive.

[Application en ligne](https://cyclotrip-france.streamlit.app/) · [Dépôt GitHub](https://github.com/abdillahi-aden/projet-cyclotrip)

## Contexte et objectif

CycloTrip a été réalisé dans le cadre de la formation Data Engineer de DataScientest. Le projet relie ingestion de données, stockage spatial PostgreSQL/PostGIS et interface de préparation de parcours cyclables. Le dépôt documente une réalisation de formation présentée dans le portfolio d’Abdillahi Aden.

## Fonctionnalités présentes dans le code

- Recherche d’adresses à partir de trois caractères, ou sélection par département, commune, voie et numéro.
- Validation du départ et de l’arrivée avant calcul, avec refus des coordonnées identiques.
- Calcul d’un itinéraire cyclable via OpenRouteService : distance, durée estimée et dénivelés.
- Carte Folium du parcours et des points d’intérêt, recherchés avec `ST_DWithin` dans PostGIS à moins de 1 000 mètres, avec un préfiltre d’emprise et une limite de 100 résultats.
- Estimation d’étapes selon la distance quotidienne et classement indicatif de difficulté.
- Météo actuelle au départ et à l’arrivée lorsque la clé OpenWeatherMap est configurée.
- Téléchargement du tracé en GPX et GeoJSON.

## Technologies et organisation

**Python 3.11**, Streamlit, PostgreSQL/PostGIS, psycopg2, Pandas, Folium, streamlit-folium, Shapely et Requests. Les dépendances sont fixées dans [requirements.txt](requirements.txt).

```text
app.py                         Interface Streamlit
components/map.py              Carte Folium et points d’intérêt
database/connection.py         Connexion PostgreSQL depuis l’environnement
database/queries.py            Requêtes d’adresses et de proximité PostGIS
services/routing.py            OpenRouteService, géométries et exports
services/weather.py            OpenWeatherMap
tests/test_routing.py          Trois tests unitaires
creer_table.sql                SQL de préparation et opérations de maintenance
import_masse_adresse_bd_v2.py   Import CSV d’adresses
import_pois_bd.py              Import CSV de points d’intérêt
.github/workflows/ci.yml       Intégration continue sous Python 3.11
```

`test_streamlit_final_v2.py` appelle `main()` depuis `app.py` et conserve la compatibilité avec un point d’entrée Streamlit existant.

## Prérequis

- Python 3.11 et pip ; accès réseau pour installer les dépendances.
- Une base PostgreSQL avec l’extension PostGIS, accessible depuis la machine qui lance l’application, et un compte autorisé à lire les tables nécessaires.
- Des tables **déjà préparées et alimentées** : le dépôt ne fournit ni les CSV sources ni une base de démonstration prête à l’emploi.
- Une clé OpenRouteService pour calculer des itinéraires ; une clé OpenWeatherMap facultative pour la météo. Les quotas et conditions des fournisseurs s’appliquent.

### Données attendues

Les requêtes de l’application utilisent :

- `public.adresses` : `id`, `numero`, `nom_voie`, `code_postal`, `nom_commune`, `lon`, `lat` ;
- `public.pois` : `poi`, `description`, `adresse`, `code_postal`, `site_internet`, `longitude`, `latitude`, `geom` de type `geography(Point, 4326)`.

Le fichier SQL décrit ces tables, des index attributaires et un index spatial GiST. Il contient aussi un `DELETE` sur les adresses et un `DROP TABLE` suivi d’une recréation de `pois` ; l’index GiST y est créé avant cette recréation. **Ce fichier ne constitue donc pas une migration à exécuter intégralement sur une base existante.** Examiner et adapter les opérations sur une base locale dédiée.

Les deux scripts d’import écrivent dans la base et s’exécutent dès leur chargement. Ils utilisent des chemins locaux absolus à adapter et les variables `DB_*`, sans prendre en charge `DATABASE_URL`. Ils ne sont pas nécessaires pour lancer l’interface sur une base déjà alimentée.

Les CSV attendus comportent les en-têtes suivants :

- Adresses : `id`, `numero`, `nom_voie`, `code_postal`, `nom_commune`, `lon`, `lat`.
- Points d’intérêt : `ID`, `POI`, `Description`, `adresse`, `code_postal`, `site_internet`, `longitude`, `latitude`.

Le nombre d’adresses affiché dans l’interface est une valeur inscrite dans le code ; il ne mesure pas le contenu de votre base au lancement.

## Installation locale

Depuis un terminal, avec Python 3.11 sélectionné :

```bash
git clone https://github.com/abdillahi-aden/projet-cyclotrip.git
cd projet-cyclotrip
python -m venv .venv
```

Activer l’environnement :

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Puis installer les dépendances :

```bash
python -m pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` à la racine. `python-dotenv` le charge dans `database/connection.py`. Le code lit les paramètres via `os.getenv` ; une configuration dans un fichier `secrets.toml` seul n’est pas lue directement par cette connexion.

| Variable | Rôle |
| --- | --- |
| `DATABASE_URL` | Chaîne de connexion PostgreSQL ; prioritaire si renseignée. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Paramètres de connexion utilisés lorsque `DATABASE_URL` est absente. Également utilisés par les scripts d’import. |
| `DB_SSLMODE` | Mode SSL de l’application ; défaut : `require`. À adapter uniquement selon la configuration de la base choisie. |
| `ORS_API_KEY` | Clé OpenRouteService, nécessaire au calcul du parcours. |
| `WEATHER_API_KEY` | Clé OpenWeatherMap facultative ; sans elle, la météo est indisponible. |

Renseigner les valeurs réelles uniquement dans l’environnement local ou le mécanisme de configuration de l’hébergeur qui les expose à `os.getenv`. `.env` est déjà ignoré par Git. Ne publier aucune clé ni chaîne de connexion contenant des identifiants.

### Lancement

À la racine du dépôt, dans l’environnement activé :

```bash
python -m streamlit run app.py
```

Ouvrir l’URL locale affichée par Streamlit, généralement `http://localhost:8501`. La page d’accueil peut s’afficher sans base configurée ; la recherche d’adresses et le calcul complet nécessitent les prérequis ci-dessus.

## Tests et intégration continue

Pour exécuter uniquement les trois tests unitaires de logique d’itinéraire, sans appel à la base ni aux API :

```bash
python -m pytest tests/test_routing.py
```

Ils couvrent la détection de coordonnées identiques ou différentes et les trois classes de difficulté. Ils ne valident pas les requêtes PostGIS, les exports, les API ou l’interface complète.

Le workflow [CI](.github/workflows/ci.yml) s’exécute sur les push et pull requests sous Python 3.11, installe `requirements.txt` et lance `python -m pytest`. Cette collecte globale inclut aussi le wrapper `test_streamlit_final_v2.py` ; ce wrapper n’est pas un test automatisé de l’interface.

Un [résultat CI réussi pour le commit `2453ec2`](https://github.com/abdillahi-aden/projet-cyclotrip/actions/runs/30772219020) a été consulté pendant la revue documentaire. Il ne prouve pas le fonctionnement des services distants.

## Services externes et limites

- Le parcours dépend d’OpenRouteService, de sa disponibilité et de ses quotas. La recherche dépend du contenu et de la disponibilité de PostgreSQL/PostGIS ; Supabase est l’hébergeur mentionné dans la documentation et les messages existants.
- Les fonds cartographiques Folium utilisent CartoDB et nécessitent un accès réseau.
- La distance utilisée pour estimer les étapes est une approximation à partir des coordonnées en degrés (`longueur × 111`). Les segments sont des lignes entre points interpolés ; ils ne constituent pas des itinéraires quotidiens détaillés ni une réservation d’hébergement.
- La météo utilise les conditions actuelles aux extrémités du trajet, pas une prévision à la date future de chaque étape ; les étapes intermédiaires n’ont pas de météo dédiée.
- Le niveau de difficulté est une règle simple fondée sur distance et dénivelé, sans validation sportive.
- Le jeu complet de données, les accès de déploiement et un scénario d’installation de base entièrement automatisé ne sont pas fournis. Le parcours complet n’a pas été exécuté pendant la revue documentaire afin de ne pas solliciter les API métier ni une base distante.
