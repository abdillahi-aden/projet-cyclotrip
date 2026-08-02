import pandas as pd
import streamlit as st

from database.connection import DatabaseConnectionError, connect_db


ADDRESS_COLUMNS = """
    id,
    numero,
    nom_voie,
    code_postal,
    nom_commune,
    lon,
    lat
"""


def format_address(row):
    numero = str(row.get("numero") or "").strip()
    voie = str(row.get("nom_voie") or "").strip()
    code_postal = str(row.get("code_postal") or "").strip()
    commune = str(row.get("nom_commune") or "").strip()
    prefix = f"{numero} " if numero and numero != "0" else ""
    return f"{prefix}{voie}, {code_postal} {commune}".strip()


@st.cache_data(ttl=3600, show_spinner=False)
def search_addresses(term, limit=25):
    term = (term or "").strip()
    if len(term) < 3:
        return []

    tokens = [token for token in term.split() if token]
    where = " AND ".join(
        [
            "(numero::text ILIKE %s OR nom_voie ILIKE %s OR nom_commune ILIKE %s OR code_postal::text ILIKE %s)"
            for _ in tokens
        ]
    )
    params = []
    for token in tokens:
        pattern = f"%{token}%"
        params.extend([pattern, pattern, pattern, pattern])
    params.append(limit)

    query = f"""
        SELECT {ADDRESS_COLUMNS}
        FROM public.adresses
        WHERE {where}
        ORDER BY nom_commune, nom_voie, numero
        LIMIT %s;
    """
    try:
        df = pd.read_sql(query, connect_db(), params=params)
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError(
            "La recherche d'adresses est momentanément indisponible."
        ) from exc
    records = df.to_dict("records")
    for record in records:
        record["label"] = format_address(record)
    return records


@st.cache_data(ttl=3600, show_spinner=False)
def list_departments():
    query = """
        SELECT DISTINCT LEFT(code_postal::text, 2) AS dep
        FROM public.adresses
        WHERE code_postal IS NOT NULL
        ORDER BY dep;
    """
    try:
        return pd.read_sql(query, connect_db())["dep"].dropna().tolist()
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError("Les départements ne peuvent pas être chargés.") from exc


@st.cache_data(ttl=3600, show_spinner=False)
def list_communes(dep):
    query = """
        SELECT DISTINCT nom_commune
        FROM public.adresses
        WHERE code_postal::text LIKE %s
        ORDER BY nom_commune;
    """
    try:
        return pd.read_sql(query, connect_db(), params=[f"{dep}%"])["nom_commune"].dropna().tolist()
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError("Les communes ne peuvent pas être chargées.") from exc


@st.cache_data(ttl=3600, show_spinner=False)
def list_voies(commune):
    query = """
        SELECT DISTINCT nom_voie
        FROM public.adresses
        WHERE nom_commune = %s
        ORDER BY nom_voie;
    """
    try:
        return pd.read_sql(query, connect_db(), params=[commune])["nom_voie"].dropna().tolist()
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError("Les voies ne peuvent pas être chargées.") from exc


@st.cache_data(ttl=3600, show_spinner=False)
def list_numeros(voie, commune):
    query = """
        SELECT DISTINCT numero
        FROM public.adresses
        WHERE nom_voie = %s AND nom_commune = %s
        ORDER BY numero;
    """
    try:
        return pd.read_sql(query, connect_db(), params=[voie, commune])["numero"].dropna().astype(str).tolist()
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError("Les numéros ne peuvent pas être chargés.") from exc


@st.cache_data(ttl=1800, show_spinner=False)
def find_address(dep, commune, voie, numero):
    query = f"""
        SELECT {ADDRESS_COLUMNS}
        FROM public.adresses
        WHERE code_postal::text LIKE %s
          AND nom_commune = %s
          AND nom_voie = %s
          AND numero::text = %s
        LIMIT 1;
    """
    try:
        df = pd.read_sql(query, connect_db(), params=[f"{dep}%", commune, voie, str(numero)])
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError("L'adresse sélectionnée ne peut pas être localisée.") from exc
    if df.empty:
        return None
    record = df.iloc[0].to_dict()
    record["label"] = format_address(record)
    return record


def load_pois_near_route(route_wkt, bounds, limit=100):
    minx, miny, maxx, maxy = bounds
    query = """
        SELECT
            poi,
            description,
            adresse,
            code_postal,
            site_internet,
            longitude,
            latitude
        FROM public.pois
        WHERE geom::geometry && ST_MakeEnvelope(%s, %s, %s, %s, 4326)
          AND ST_DWithin(
              geom,
              ST_SetSRID(ST_GeomFromText(%s), 4326)::geography,
              1000
          )
        LIMIT %s;
    """
    try:
        return pd.read_sql(
            query,
            connect_db(),
            params=[minx, miny, maxx, maxy, route_wkt, limit],
        )
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        raise DatabaseConnectionError("Les points d'intérêt ne peuvent pas être chargés.") from exc
