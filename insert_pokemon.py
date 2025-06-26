import os
from pathlib import Path
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='qBZc9KLhynJWLKGu8clK',
    database='pokedex-pokemon-db'
)
cursor = conn.cursor(buffered=True)

root_dir = Path("pokemon-card-pictures")

def extract_info(filename):
    id = filename.replace(".jpg", "")
    parts = id.split("-")
    extension = parts[0]
    try:
        local_id = int(parts[1])
    except:
        local_id = id
    return id, local_id, extension

try:
    # Démarrer la transaction explicitement
    conn.start_transaction()

    cursor.execute("SELECT Id FROM PokemonCards")
    existing_ids = set(row[0] for row in cursor.fetchall())

    inserts = []
    pokemon_count = 0

    for subdir in sorted(root_dir.iterdir()):
        if not subdir.is_dir():
            continue

        name = subdir.name
        print(f"🔍 Traitement de : {name}")

        cursor.execute("SELECT Id FROM Pokemons WHERE Name = %s", (name,))
        result = cursor.fetchone()

        if not result:
            print(f"❌ Pokémon non trouvé : {name}")
            continue

        pokemon_id = result[0]
        pokemon_count += 1

        for file in subdir.glob("*.jpg"):
            id, local_id, extension = extract_info(file.name)

            if id in existing_ids:
                print(f"⚠️ Carte déjà existante ignorée : {id}")
                continue

            image_path = f"/pokemon-card-pictures/{subdir.name}/{file.name}"
            inserts.append((id, local_id, extension, name, image_path, pokemon_id))
            existing_ids.add(id)

    if inserts:
        cursor.executemany("""
            INSERT INTO PokemonCards (Id, LocalId, Extension, Name, Image, PokemonId)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, inserts)
        print(f"✅ {cursor.rowcount} cartes insérées avec succès.")

    # Commit si tout va bien
    conn.commit()

    print(f"\n🎉 Traitement terminé : {pokemon_count} Pokémon(s) ont été traités.")

except mysql.connector.Error as err:
    print("❌ Erreur détectée, rollback effectué :", err)
    conn.rollback()

finally:
    cursor.close()
    conn.close()
