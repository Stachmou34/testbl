import requests
import os

def download_font():
    # URL de la police One Piece Manga
    font_url = "https://fontmeme.com/polices/police-one-piece-manga/"
    
    # Créer le dossier fonts s'il n'existe pas
    if not os.path.exists('fonts'):
        os.makedirs('fonts')
    
    # Télécharger la police
    response = requests.get(font_url)
    if response.status_code == 200:
        with open('fonts/one-piece.ttf', 'wb') as f:
            f.write(response.content)
        print("Police téléchargée avec succès !")
    else:
        print("Erreur lors du téléchargement de la police")

if __name__ == "__main__":
    download_font() 