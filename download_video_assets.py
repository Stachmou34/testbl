import csv
import os
import requests
import time
from urllib.parse import unquote

def clean_url(url):
    if not url:
        return None
    # Supprimer les paramètres de redimensionnement
    url = url.split('/scale-to-width-down/')[0]
    return url

def download_image(url, save_path):
    try:
        if not url:
            return False
        
        # Nettoyer l'URL
        url = clean_url(url)
        if not url:
            return False
        
        # Créer le dossier parent s'il n'existe pas
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Télécharger l'image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Sauvegarder l'image
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Image téléchargée: {save_path}")
        return True
    
    except Exception as e:
        print(f"✗ Erreur lors du téléchargement de {url}: {str(e)}")
        return False

def process_character(row):
    # Créer un nom de fichier sécurisé pour le personnage
    character_name = row[0].replace(' ', '_')
    brigade = row[2].replace(' ', '_')
    
    # Créer le chemin du dossier
    base_path = f"video_assets/personnages/{brigade}/{character_name}"
    
    # Télécharger l'image du personnage
    if row[4]:  # Lien Image
        download_image(row[4], f"{base_path}/portrait.png")
    
    # Créer un fichier info.txt avec les informations du personnage
    info_path = f"{base_path}/info.txt"
    os.makedirs(os.path.dirname(info_path), exist_ok=True)
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(f"Nom: {row[0]}\n")
        f.write(f"Rôle: {row[1]}\n")
        f.write(f"Brigade: {row[2]}\n")
        f.write(f"Grade: {row[3]}\n")

def main():
    # Créer le dossier principal
    os.makedirs("video_assets/personnages", exist_ok=True)
    
    # Lire le CSV
    with open('personnages_fire_force.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        
        # Traiter chaque personnage
        for row in reader:
            print(f"\nTraitement de {row[0]} ({row[2]})...")
            process_character(row)
            time.sleep(1)  # Attendre 1 seconde entre chaque personnage

if __name__ == "__main__":
    main() 