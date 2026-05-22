CREATE DATABASE nom_de_votre_base_de_donnees;
\c nom_de_votre_base_de_donnees; -- Se connecter à la base de données
CREATE EXTENSION postgis; -- Activer PostGIS



-- Table pour les adresses
CREATE TABLE adresses (
    id SERIAL PRIMARY KEY,
    id_unique TEXT,
    nom_voie TEXT,
    numero TEXT,
    code_postal INTEGER,
    nom_commune TEXT,
    lon DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    geom GEOGRAPHY(Point, 4326)
);

-- Table pour les points d'intérêt (POIs)
CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
    POI TEXT,
    Description TEXT,
    adresse TEXT,
    code_postal INTEGER,
    site_internet TEXT,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    geom GEOGRAPHY(Point, 4326)
);



-- Index pour accélérer les recherches par nom de voie et commune
CREATE INDEX idx_adresses_nom_voie ON public.adresses USING btree (nom_voie);
CREATE INDEX idx_adresses_nom_commune ON public.adresses USING btree (nom_commune);
CREATE INDEX idx_adresses_numero ON public.adresses USING btree (numero);
-- Index pour les recherches et filtres par code postal
CREATE INDEX idx_adresses_code_postal ON public.adresses USING btree (code_postal);

-- Index spatial sur les géométries pour les requêtes de proximité
CREATE INDEX idx_pois_geom ON public.pois USING gist (geom);


DELETE FROM public.adresses
WHERE code_postal = 0;


DROP TABLE IF EXISTS public.pois;

CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
	id_unique TEXT,
    POI TEXT,
    Description TEXT,
    adresse TEXT,
    code_postal INTEGER,
    site_internet TEXT,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    geom GEOGRAPHY(Point, 4326)
);
