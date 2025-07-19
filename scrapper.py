# USE : python .\scrapper.py -n "Félicanis" --path "./output" --download

import os
import argparse
import requests
import urllib.parse

def normalize_pokemon_name(name):
    name = name.replace("Méga-", "M-")
    name = name.replace("GMax", "VMAX")
    return name

def should_ignore_card(card_name, pokemon_name):
    regions = ["Hisui", "Galar", "Alola"]
    for region in regions:
        if region.lower() in card_name.lower() and region.lower() not in pokemon_name.lower():
            return True
    if "M-" in card_name and "Méga" not in pokemon_name:
        return True
    if "VMAX" in card_name and "GMax" not in pokemon_name:
        return True
    return False

def fetch_cards(pokemon_name):
    name_query = normalize_pokemon_name(pokemon_name)
    url = f"https://api.tcgdex.net/v2/fr/cards?name=like:{urllib.parse.quote(name_query)}*"
    print(f"🔎 Requête API : {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Erreur API pour {pokemon_name}: {response.status_code}")
        return []
    return response.json()

def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ Image téléchargée : {output_path}")
        else:
            print(f"⚠️ Image non trouvée : {image_url}")
    except Exception as e:
        print(f"❌ Erreur téléchargement : {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--names', nargs='+', help="Liste de noms de Pokémon (ex: Pikachu Salamèche)")
    parser.add_argument('--file', help="Fichier texte contenant un nom de Pokémon par ligne")
    parser.add_argument('--path', required=True, help="Dossier de destination")
    parser.add_argument('--download', action='store_true', help="Télécharger les images")
    args = parser.parse_args()

    # Récupération des noms
    pokemon_names = []

    if args.names:
        pokemon_names.extend(args.names)

    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ Le fichier {args.file} n'existe pas.")
            return
        with open(args.file, 'r', encoding='utf-8') as f:
            file_names = [line.strip() for line in f if line.strip()]
            pokemon_names.extend(file_names)

    if not pokemon_names:
        print("❗ Veuillez spécifier au moins un nom de Pokémon via --names ou --file")
        return

    for name in pokemon_names:
        print(f"\n📦 Traitement de {name}...")
        cards = fetch_cards(name)
        if not cards:
            print(f"❌ Aucune carte trouvée pour {name}.")
            continue

        print(f"🔍 {len(cards)} carte(s) trouvée(s) pour {name}")
        subfolder = os.path.join(args.path, name)
        os.makedirs(subfolder, exist_ok=True)

        dl_count = 0
        for card in cards:
            card_name = card.get("name", "")
            card_id = card.get("id", "")
            image = card.get("image")

            if should_ignore_card(card_name, name):
                continue

            if not image or "/tcgp/" in image:
                continue

            image_url = image + "/low.jpg"
            image_path = os.path.join(subfolder, f"{card_id}.jpg")

            if args.download:
                download_image(image_url, image_path)
                dl_count = dl_count + 1
            else:
                print(f"[TEST] {card_id} - {image_url}")

        print(f"🔍✅ {dl_count} carte(s) téléchargée(s) pour {name}")

if __name__ == "__main__":
    main()
