from pathlib import Path

# Dossier racine à adapter
root_dir = Path("pokemon-card-pictures")

# Extensions d'image à traiter
valid_exts = {".jpg", ".jpeg", ".png"}

initialName = "swshp-SWSH"
replaceName = "swshp-"

for path in root_dir.rglob("*"):  # parcours récursif
    if path.is_file() and path.suffix.lower() in valid_exts:
        filename = path.name
        if initialName in filename:
            # Nouveau nom : on remplace initialName par replaceName
            new_name = filename.replace(initialName, replaceName)
            new_path = path.with_name(new_name)

            # Renommer le fichier
            print(f"Renommage : {path} -> {new_path}")
            path.rename(new_path)
