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
    url = f"https://api.tcgdex.net/v2/fr/cards?name={urllib.parse.quote(name_query)}*"
    print(f"Fetching: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Erreur API pour {pokemon_name}: {response.status_code}")
        return []
    return response.json()

def download_image(image_url, output_path):
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Téléchargé : {output_path}")
        else:
            print(f"Image non trouvée : {image_url}")
    except Exception as e:
        print(f"Erreur téléchargement : {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', help="Nom du Pokémon à chercher")
    parser.add_argument('--path', required=True, help="Dossier de destination")
    parser.add_argument('--download', action='store_true', help="Télécharger les images")
    args = parser.parse_args()

    if not args.name:
        print("Veuillez spécifier un nom de Pokémon avec -n")
        return

    cards = fetch_cards(args.name)
    if not cards:
        print("Aucune carte trouvée.")
        return

    print(f"{len(cards)} cartes trouvées pour {args.name}")
    subfolder = os.path.join(args.path, args.name)
    os.makedirs(subfolder, exist_ok=True)

    for card in cards:
        card_name = card.get("name", "")
        card_id = card.get("id", "")
        image = card.get("image")

        if should_ignore_card(card_name, args.name):
            continue

        if not image or "/tcgp/" in image:
            continue

        image_url = image + "/low.jpg"
        image_path = os.path.join(subfolder, f"{card_id}.jpg")

        if args.download:
            download_image(image_url, image_path)
        else:
            print(f"[TEST] {card_id} - {image_url}")

if __name__ == "__main__":
    main()
