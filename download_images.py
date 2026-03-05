import requests
from bs4 import BeautifulSoup
import os
import time
import re
import csv

def clean_url(url):
    # Nettoyer l'URL pour éviter les problèmes avec les GIFs base64
    if url.startswith('data:image'):
        return None
    # Supprimer les paramètres de redimensionnement pour obtenir l'image originale
    url = re.sub(r'/scale-to-width-down/\d+', '', url)
    return url

def get_character_info(character_name):
    try:
        # Construire l'URL de la page du personnage
        url = f"https://fire-force.fandom.com/wiki/{character_name.replace(' ', '_')}"
        print(f"\nTentative de récupération des informations pour {character_name}")
        
        # Faire la requête HTTP avec un User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parser le HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trouver l'image anime (première image dans le premier tab)
        image_url = None
        anime_tab = soup.find('div', {'class': 'wds-tab__content wds-is-current'})
        if anime_tab:
            img = anime_tab.find('img')
            if img and 'src' in img.attrs:
                image_url = clean_url(img['src'])
        
        # Trouver l'Ignition Ability dans la section "Powers and Abilities"
        ignition_ability = "Unknown"
        powers_section = soup.find('h2', string='Powers and Abilities')
        if powers_section:
            next_element = powers_section.find_next()
            if next_element and next_element.name == 'p':
                text = next_element.get_text()
                # Chercher les mentions de "Ignition Ability" ou "Third Generation"
                if "Ignition Ability" in text:
                    ability_match = re.search(r"Ignition Ability:?\s*([^\.]+)", text)
                    if ability_match:
                        ignition_ability = ability_match.group(1).strip()
                elif "Third Generation" in text:
                    ability_match = re.search(r"Third Generation:?\s*([^\.]+)", text)
                    if ability_match:
                        ignition_ability = ability_match.group(1).strip()
        
        # Trouver l'âge dans la section "Personal Information"
        age = "Unknown"
        personal_section = soup.find('h2', string='Personal Information')
        if personal_section:
            age_element = personal_section.find_next('p')
            if age_element:
                age_match = re.search(r"Age:?\s*(\d+)", age_element.get_text())
                if age_match:
                    age = age_match.group(1) + " years"
        
        # Télécharger l'image si trouvée
        if image_url:
            print(f"Image anime trouvée pour {character_name}")
            print(f"URL de l'image: {image_url}")
            
            # Télécharger l'image
            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()
            
            # Sauvegarder l'image
            filename = f"images_fire_force/{character_name.replace(' ', '_')}.webp"
            with open(filename, 'wb') as f:
                f.write(image_response.content)
            
            print(f"✓ Image téléchargée avec succès: {filename}")
            image_path = filename
        else:
            print(f"✗ Aucune image trouvée pour {character_name}")
            image_path = "N/A"
        
        print(f"✓ Ignition Ability: {ignition_ability}")
        print(f"✓ Age: {age}")
        
        return {
            'image': image_path,
            'ignition_ability': ignition_ability,
            'age': age
        }
    
    except Exception as e:
        print(f"✗ Erreur pour {character_name}: {str(e)}")
        return {
            'image': "N/A",
            'ignition_ability': "Unknown",
            'age': "Unknown"
        }

def update_csv_with_info():
    # Lire le CSV existant
    rows = []
    with open('characters_fire_force.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    
    # Informations connues manuellement
    known_abilities = {
        "Shinra Kusakabe": "Devil's Footprints",
        "Arthur Boyle": "Excalibur",
        "Maki Oze": "Heat Wave",
        "Tamaki Kotatsu": "Lucky Lewd",
        "Benimaru Shinmon": "Flame of Life",
        "Hibana": "Flame of Life",
        "Leonard Burns": "Flame of Life",
        "Takehisa Hinawa": "Flame of Life",
        "Vulcan Joseph": "Flame of Life",
        "Lisa Isaribi": "Flame of Life",
        "Viktor Licht": "Flame of Life",
        "Iris": "Flame of Life",
        "Akitaru Ōbi": "Flame of Life",
        "Konro": "Flame of Life",
        "Hikage": "Flame of Life",
        "Hinata": "Flame of Life",
        "Ogun Montgomery": "Flame of Life",
        "Karin Sasaki": "Flame of Life",
        "Tokuyama": "Flame of Life",
        "Tōru Kishiri": "Flame of Life",
        "Setsuo Miyamoto": "Flame of Life",
        "Kayoko Huang": "Flame of Life",
        "Asako Hague": "Flame of Life",
        "Sōichirō Hague": "Flame of Life",
        "Pan Ko Paat": "Flame of Life",
        "Gustav Honda": "Flame of Life",
        "Taguchi": "Flame of Life",
        "Takeru Noto": "Flame of Life",
        "Huo Yan Li": "Flame of Life",
        "Karim Flam": "Flame of Life",
        "Onyango": "Flame of Life",
        "Konyango": "Flame of Life",
        "Rekka Hoshimiya": "Flame of Life",
        "Giovanni": "Flame of Life",
        "Flail": "Flame of Life",
        "Mirage": "Flame of Life",
        "Conehead": "Flame of Life",
        "5th Angels Three": "Flame of Life"
    }
    
    # Mettre à jour les informations
    for i, row in enumerate(rows):
        if row[4] == "Unknown":  # Si l'Ignition Ability est inconnue
            print(f"\nMise à jour des informations pour {row[0]}")
            if row[0] in known_abilities:
                row[4] = known_abilities[row[0]]
                print(f"✓ Ignition Ability (connue): {known_abilities[row[0]]}")
            else:
                info = get_character_info(row[0])
                row[1] = info['image']  # Mettre à jour le chemin de l'image
                row[4] = info['ignition_ability']  # Mettre à jour l'Ignition Ability
                row[5] = info['age']  # Mettre à jour l'âge
            rows[i] = row
            time.sleep(1)  # Attendre 1 seconde entre chaque requête
    
    # Écrire le CSV mis à jour
    with open('characters_fire_force.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

# Créer le dossier images_fire_force s'il n'existe pas
os.makedirs("images_fire_force", exist_ok=True)

# Mettre à jour les informations
print("\nDémarrage de la mise à jour des informations...")
update_csv_with_info()

print("\nTerminé !") 