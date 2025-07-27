import os
import logging
from pathlib import Path
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Création du dossier logs s'il n'existe pas
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Nom du fichier de log avec date+heure à la seconde
now = datetime.now()
log_filename = log_dir / now.strftime("%Y-%m-%d_%H-%M-%S.log")

logging.basicConfig(
    filename=log_filename,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    level=logging.INFO,
    encoding='utf-8'
)

logger = logging.getLogger()

env_path = Path(".env")

if not env_path.is_file():
    error_msg = "Fichier .env introuvable ! Veuillez créer un fichier .env à la racine du projet."
    logger.error(error_msg)
    print(error_msg)
    exit(1)
else:
    load_dotenv(dotenv_path=env_path)
    logger.info(".env chargé avec succès.")

host = os.getenv('MYSQL_HOST', 'localhost')
user = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
database = os.getenv('MYSQL_DATABASE')

conn = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    ssl_disabled=True
)
cursor = conn.cursor(buffered=True)

root_dir = Path("pokemon-card-pictures")

def extract_info(filename):
    id = Path(filename).stem
    parts = id.split("-")
    extension = parts[0]
    try:
        local_id = int(parts[1])
    except:
        local_id = id
    return id, local_id, extension

try:
    conn.start_transaction()

    # Récupère les Id des cartes déjà existantes
    cursor.execute("SELECT Id FROM PokemonCards")
    existing_card_ids = set(row[0] for row in cursor.fetchall())

    # Récupère les extensions avec leurs SetId
    cursor.execute("SELECT Id, SetId FROM Sets")
    set_mapping = {row[1]: row[0] for row in cursor.fetchall()}
    logger.info(f"{len(set_mapping)} extensions chargées depuis la table 'Sets'.")
    logger.info(set_mapping)

    # Récupère les Pokemons existants pour lookup (Name -> Id)
    cursor.execute("SELECT Id, Name FROM Pokemons")
    pokemon_name_to_id = {row[1]: row[0] for row in cursor.fetchall()}

    cards_to_insert = []
    associations_to_insert = []
    pokemon_count = 0

    for subdir in sorted(root_dir.iterdir()):
        if not subdir.is_dir():
            continue

        name = subdir.name

        if name not in pokemon_name_to_id:
            logger.error(f"❌ Pokémon non trouvé : {name}")
            continue

        pokemon_id = pokemon_name_to_id[name]
        pokemon_count += 1

        for file in subdir.glob("*"):
            if file.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                continue
            
            card_id, local_id, extension = extract_info(file.name)
            logger.info(f"🔍 Traitement de : {name} : {card_id}")

            set_id = set_mapping.get(extension)
            if not set_id:
                logger.error(f"❌ SetId introuvable pour extension : {extension}")
                continue

            image_path = f"/pokemon-card-pictures/{subdir.name}/{file.name}"

            if card_id not in existing_card_ids:
                # Carte non existante, insertion dans PokemonCards
                cards_to_insert.append((card_id, local_id, extension, name, image_path, set_id))
                existing_card_ids.add(card_id)
            else:
                logger.warning(f"⚠️ Carte déjà existante : {card_id} - insertion de l'association uniquement.")

            # Prépare insertion dans PokemonCardPokemon (association)
            associations_to_insert.append((pokemon_id, card_id))

            logger.info(f"➕ Carte traitée : {card_id}")


    if cards_to_insert:
        logger.info(f"Inserts à faire dans PokemonCards : {len(cards_to_insert)}")
        cursor.executemany("""
            INSERT INTO PokemonCards (Id, LocalId, Extension, Name, Image, SetId)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, cards_to_insert)
        logger.info(f"Rows insérées dans PokemonCards (rowcount) : {cursor.rowcount}")
        logger.info(f"✅ {cursor.rowcount} cartes insérées avec succès dans PokemonCards.")

    if associations_to_insert:
        logger.info(f"Inserts à faire dans PokemonCardPokemon : {len(associations_to_insert)}")
        cursor.executemany("""
            INSERT IGNORE INTO PokemonCardPokemons (PokemonId, PokemonCardId)
            VALUES (%s, %s)
        """, associations_to_insert)

        logger.info(f"Rows insérées dans PokemonCardPokemon (rowcount) : {cursor.rowcount}")
        logger.info(f"✅ {cursor.rowcount} associations insérées avec succès dans PokemonCardPokemon.")

    conn.commit()

    logger.info(f"\n🎉 Traitement terminé : {pokemon_count} Pokémon(s) ont été traités.")

except mysql.connector.Error as err:
    logger.error(f"❌ Erreur détectée, rollback effectué : {err}")
    conn.rollback()

finally:
    cursor.close()
    conn.close()
