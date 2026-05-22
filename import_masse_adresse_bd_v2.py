from dotenv import load_dotenv
import os

load_dotenv()
import psycopg2
import csv
import time

def insert_from_csv(file_path, log_path='progress.log'):
    start_global = time.time()  # Début du chronométrage global
    
    conn = None
    try:
        # Connexion à la base de données PostgreSQL
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        batch_size = 10000  # Taille des lots pour l'insertion des données
        last_line_processed = 0
        batch_count = 0  # Compteur pour les lots

        # Lire le dernier état de progression du fichier de log
        try:
            with open(log_path, 'r') as log_file:
                last_line_processed = int(log_file.read().strip())
        except FileNotFoundError:
            last_line_processed = 0

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            batch = []
            for i, row in enumerate(reader, 1):
                if i <= last_line_processed:
                    continue  # Ignorer les lignes déjà traitées
                # Validation des entrées pour les colonnes `numero` et `code_postal`
                numero = row['numero'] if row['numero'].isdigit() else '0'
                code_postal = row['code_postal'] if row['code_postal'].isdigit() else '0'
                # Ajout des données au lot
                batch.append((row['id'], numero, row['nom_voie'], code_postal, row['nom_commune'], row['lon'], row['lat'], row['lon'], row['lat']))
                if len(batch) >= batch_size:
                    start_time = time.time()  # Début du chronométrage pour ce batch
                    # Insertion du lot de données
                    cur.executemany("""
                        INSERT INTO adresses (id_unique, numero, nom_voie, code_postal, nom_commune, lon, lat, geom)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    """, batch)
                    batch = []
                    conn.commit()
                    elapsed_time = time.time() - start_time
                    batch_count += 1
                    print(f"Batch {batch_count} intégré en {elapsed_time:.2f} secondes.")
                    # Enregistrement de la progression
                    with open(log_path, 'w') as log_file:
                        log_file.write(str(i))

            # Traitement du dernier lot s'il reste des données non insérées
            if batch:
                start_time = time.time()  # Début du chronométrage pour ce dernier batch
                cur.executemany("""
                    INSERT INTO adresses (id_unique, numero, nom_voie, code_postal, nom_commune, lon, lat, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                """, batch)
                conn.commit()
                elapsed_time = time.time() - start_time
                batch_count += 1
                print(f"Batch {batch_count} intégré en {elapsed_time:.2f} secondes.")
                with open(log_path, 'w') as log_file:
                    log_file.write(str(i))

        # Calcul et affichage du temps total d'exécution
        elapsed_global = time.time() - start_global
        print(f"Insertion terminée avec succès. {batch_count} batches intégrés en {elapsed_global:.2f} secondes au total.")

    except Exception as e:
        print(f"Erreur de connexion ou lors de l'exécution : {e}")
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

# Utilisation du code avec un fichier de progression pour suivre la dernière ligne traitée
insert_from_csv('C:/Users/lenovo/Desktop/projet_AAE/Nouveau dossier/projet_cyclo_v1/data/adresse_dep_69_42.csv')
