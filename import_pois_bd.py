import psycopg2
import csv
import time  # Importez le module time

def insert_from_csv(file_path):
    start_time = time.time()  # Démarre le chronomètre avant l'exécution

    conn = None
    try:
        conn = psycopg2.connect("dbname=tourisme_cyclo user=postgres password=Dawo2016@")
        cur = conn.cursor()

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                try:
                    cur.execute("""
                        INSERT INTO pois (id_unique, poi, description, adresse, code_postal, site_internet, longitude, latitude, geom)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    """, (row['ID'], row['POI'], row['Description'], row['adresse'], row['code_postal'], row['site_internet'], row['longitude'], row['latitude'], row['longitude'], row['latitude']))

                except psycopg2.Error as e:
                    print(f"Erreur lors de l'insertion de la ligne : {row}. Erreur : {e}")
                    conn.rollback()  # Annule la transaction en cours en cas d'erreur
                else:
                    conn.commit()  # Valide la transaction si tout s'est bien passé

        print("Insertion terminée avec succès.")

    except Exception as e:
        print(f"Erreur de connexion ou lors de l'exécution : {e}")
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    end_time = time.time()  # Arrête le chronomètre après l'exécution
    print(f"Durée d'exécution de l'insertion : {end_time - start_time:.2f} secondes.")

# Remplacez le chemin réel de votre fichier CSV
insert_from_csv('C:/Users/lenovo/Desktop/projet_AAE/Nouveau dossier/projet_cyclo_v1/POI_france.csv')
