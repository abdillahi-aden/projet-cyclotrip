import os

import psycopg2
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


class DatabaseConnectionError(Exception):
    pass


@st.cache_resource(show_spinner=False)
def connect_db():
    try:
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            sslmode=os.getenv("DB_SSLMODE", "require"),
            connect_timeout=10,
        )
    except psycopg2.OperationalError as exc:
        raise DatabaseConnectionError(
            "La base de données CycloTrip est momentanément inaccessible. "
            "Vérifiez la connexion réseau, les paramètres Supabase ou réessayez dans quelques instants."
        ) from exc
