import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import requests
from io import BytesIO
import cv2

def analyze_white_frame(image_path):
    """
    Analyse le cadre blanc central dans l'image de l'avis de recherche
    """
    # Charger l'image
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    
    # Convertir en tableau numpy
    img_array = np.array(img)
    
    # Créer un masque pour les pixels très blancs (presque purs)
    white_threshold = 245  # Réduire le seuil pour être plus strict
    white_mask = np.all(img_array > white_threshold, axis=2)
    
    # Trouver les zones blanches connectées
    from scipy import ndimage
    labeled_array, num_features = ndimage.label(white_mask)
    
    # Pour chaque zone blanche, calculer sa taille et position
    frame_info = []
    for feature in range(1, num_features + 1):
        feature_mask = labeled_array == feature
        y_coords, x_coords = np.where(feature_mask)
        
        if len(y_coords) > 0 and len(x_coords) > 0:
            # Calculer les dimensions
            top = np.min(y_coords)
            bottom = np.max(y_coords)
            left = np.min(x_coords)
            right = np.max(x_coords)
            
            frame_width = right - left
            frame_height = bottom - top
            area = frame_width * frame_height
            
            # Ne garder que les zones qui correspondent aux critères du cadre central
            if (frame_width > width * 0.3 and frame_width < width * 0.8 and  # Entre 30% et 80% de la largeur
                frame_height > height * 0.3 and frame_height < height * 0.6 and  # Entre 30% et 60% de la hauteur
                top > height * 0.1 and bottom < height * 0.9):  # Pas trop près des bords
                # Ajouter une marge de sécurité
                margin = 2  # pixels
                frame_info.append({
                    'top': top - margin,
                    'bottom': bottom + margin,
                    'left': left - margin,
                    'right': right + margin,
                    'width': frame_width + (2 * margin),
                    'height': frame_height + (2 * margin),
                    'area': area,
                    'width_percent': (frame_width / width) * 100,
                    'height_percent': (frame_height / height) * 100
                })
    
    # Trier par taille de zone
    frame_info.sort(key=lambda x: x['area'], reverse=True)
    
    # Afficher l'image avec les zones détectées
    plt.figure(figsize=(12, 8))
    plt.subplot(121)
    plt.imshow(img)
    plt.title('Image originale')
    
    plt.subplot(122)
    plt.imshow(white_mask, cmap='gray')
    plt.title('Masque blanc')
    
    # Dessiner des rectangles autour des zones blanches
    for frame in frame_info:
        rect = plt.Rectangle((frame['left'], frame['top']),
                           frame['width'], frame['height'],
                           fill=False, color='red', linewidth=2)
        plt.gca().add_patch(rect)
        
        # Ajouter un rectangle correspondant sur l'image originale
        rect_orig = plt.Rectangle((frame['left'], frame['top']),
                                frame['width'], frame['height'],
                                fill=False, color='red', linewidth=2)
        plt.subplot(121)
        plt.gca().add_patch(rect_orig)
    
    plt.tight_layout()
    plt.savefig('white_frame_analysis.png')
    
    # Afficher les informations
    print("\nAnalyse du cadre blanc central dans l'avis de recherche:")
    if frame_info:
        frame = frame_info[0]  # Prendre la plus grande zone qui correspond aux critères
        print(f"\nDimensions du cadre blanc central:")
        print(f"Largeur: {frame['width']}px ({frame['width_percent']:.1f}% de l'image)")
        print(f"Hauteur: {frame['height']}px ({frame['height_percent']:.1f}% de l'image)")
        print(f"Position: Haut={frame['top']}px, Bas={frame['bottom']}px, Gauche={frame['left']}px, Droite={frame['right']}px")
        print(f"Surface: {frame['area']} pixels carrés")
        return frame
    else:
        print("Aucun cadre blanc central détecté avec les critères spécifiés.")
        return None

def detect_b_symbol(image_path):
    """
    Détecte la position approximative du symbole "B" barré
    """
    # Charger l'image
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    
    # Zone de recherche (près du mot "WANTED")
    search_area = {
        'top': 0,
        'bottom': int(height * 0.15),  # Chercher dans les 15% supérieurs
        'left': int(width * 0.75),    # Chercher dans les 25% droits
        'right': width
    }
    
    # Convertir en tableau numpy
    img_array = np.array(img)
    
    # Créer un masque pour les pixels sombres (le "B" est sombre)
    dark_threshold = 150  # Augmenter le seuil pour les pixels sombres
    dark_mask = np.any(img_array < dark_threshold, axis=2)  # Utiliser any au lieu de all
    
    # Limiter la recherche à la zone définie
    dark_mask[:search_area['top'], :] = False
    dark_mask[search_area['bottom']:, :] = False
    dark_mask[:, :search_area['left']] = False
    dark_mask[:, search_area['right']:] = False
    
    # Trouver les zones sombres connectées
    from scipy import ndimage
    labeled_array, num_features = ndimage.label(dark_mask)
    
    # Pour chaque zone sombre, calculer sa taille et position
    b_positions = []
    for feature in range(1, num_features + 1):
        feature_mask = labeled_array == feature
        y_coords, x_coords = np.where(feature_mask)
        
        if len(y_coords) > 0 and len(x_coords) > 0:
            # Calculer les dimensions
            top = np.min(y_coords)
            bottom = np.max(y_coords)
            left = np.min(x_coords)
            right = np.max(x_coords)
            
            width = right - left
            height = bottom - top
            
            # Chercher une zone qui pourrait être le "B" barré
            if (width < 20 and height < 20 and  # Petite zone
                width > 5 and height > 5):     # Mais pas trop petite
                b_positions.append({
                    'top': top,
                    'bottom': bottom,
                    'left': left,
                    'right': right,
                    'width': width,
                    'height': height
                })
    
    # Retourner la position la plus probable (la plus à droite et en haut)
    if b_positions:
        return min(b_positions, key=lambda x: (x['top'], -x['left']))
    return None

def find_berry_symbol(wanted_poster_path, berry_template_path):
    """
    Trouve la position du symbole Berry dans l'avis de recherche
    """
    # Charger l'image et le template
    wanted = cv2.imread(wanted_poster_path)
    template = cv2.imread("berry.png")  # Chemin vers l'image à la racine
    
    if wanted is None:
        print(f"Erreur : Impossible de charger l'image {wanted_poster_path}")
        return None
    
    if template is None:
        print(f"Erreur : Impossible de charger le template berry.png")
        return None
    
    # Redimensionner le template pour différentes tailles
    scales = [0.5, 0.75, 1.0, 1.25, 1.5]
    best_match = None
    best_val = -1
    
    for scale in scales:
        width = int(template.shape[1] * scale)
        height = int(template.shape[0] * scale)
        resized = cv2.resize(template, (width, height))
        
        # Convertir en niveaux de gris
        wanted_gray = cv2.cvtColor(wanted, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Appliquer le template matching
        result = cv2.matchTemplate(wanted_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > best_val:
            best_val = max_val
            best_match = {
                'position': max_loc,
                'scale': scale,
                'width': width,
                'height': height
            }
    
    if best_match and best_val > 0.4:  # Seuil de confiance
        top_left = best_match['position']
        bottom_right = (top_left[0] + best_match['width'], 
                       top_left[1] + best_match['height'])
        
        # Dessiner un rectangle autour du symbole trouvé
        cv2.rectangle(wanted, top_left, bottom_right, (0, 255, 0), 2)
        
        # Sauvegarder l'image avec le rectangle
        cv2.imwrite('berry_detection.png', wanted)
        
        print(f"\nSymbole Berry détecté :")
        print(f"- Position : ({top_left[0]}, {top_left[1]})")
        print(f"- Taille : {best_match['width']}x{best_match['height']} pixels")
        print(f"- Échelle : {best_match['scale']:.2f}")
        print(f"- Confiance : {best_val:.2%}")
        
        return {
            'left': top_left[0],
            'top': top_left[1],
            'width': best_match['width'],
            'height': best_match['height'],
            'right': top_left[0] + best_match['width'],
            'bottom': top_left[1] + best_match['height'],
            'confidence': best_val
        }
    else:
        print("Symbole Berry non trouvé dans l'image (confiance trop faible).")
        return None

def test_character_image(wanted_poster_path, character_image_path, bounty="76,000,000"):
    """
    Teste l'intégration d'une image de personnage dans le cadre blanc
    """
    # Analyser le cadre blanc
    frame = analyze_white_frame(wanted_poster_path)
    if not frame:
        print("Impossible de détecter le cadre blanc.")
        return
    
    # Détecter la position du symbole Berry
    berry_info = find_berry_symbol(wanted_poster_path, "berry.png")
    if not berry_info:
        print("Impossible de détecter le symbole Berry.")
        return
    
    # Charger l'avis de recherche
    wanted = Image.open(wanted_poster_path).convert('RGB')
    
    # Charger l'image du personnage
    try:
        if character_image_path.startswith('http'):
            response = requests.get(character_image_path)
            char_img = Image.open(BytesIO(response.content)).convert('RGB')
        else:
            char_img = Image.open(character_image_path).convert('RGB')
        
        # Facteur d'échelle pour augmenter légèrement la taille
        scale_factor = 1.1  # Augmenter de 10%
        
        # Calculer les dimensions pour remplir le cadre blanc
        char_ratio = char_img.width / char_img.height
        frame_ratio = frame['width'] / frame['height']
        
        if char_ratio > frame_ratio:
            # Image plus large que le cadre
            new_height = int(frame['height'] * scale_factor)
            new_width = int(new_height * char_ratio)
        else:
            # Image plus haute que le cadre
            new_width = int(frame['width'] * scale_factor)
            new_height = int(new_width / char_ratio)
        
        # Redimensionner l'image du personnage
        char_img = char_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Centrer et recadrer l'image
        left = (new_width - frame['width']) // 2
        top = (new_height - frame['height']) // 2
        char_img = char_img.crop((left, top, left + frame['width'], top + frame['height']))
        
        # Créer une copie de l'avis de recherche
        result = wanted.copy()
        
        # Coller l'image du personnage
        result.paste(char_img, (frame['left'], frame['top']))
        
        # Ajouter un cadre noir autour de l'image du personnage
        draw = ImageDraw.Draw(result)
        draw.rectangle([(frame['left'], frame['top']), (frame['right'], frame['bottom'])], 
                      outline=(0, 0, 0), width=2)
        
        # Ajouter le nom du personnage
        try:
            name_font = ImageFont.truetype("arial.ttf", 42)  # Police augmentée à 42
        except:
            name_font = ImageFont.load_default()
        
        name = "KUMA"
        # Calculer la largeur du texte pour le centrer
        name_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (result.width - name_width) // 2
        name_y = frame['bottom'] + 80  # Augmenté à 80 pixels d'espacement
        
        # Dessiner le texte en gras en le dessinant plusieurs fois avec un léger décalage
        for offset in range(2):
            draw.text((name_x + offset, name_y), name, fill=(0, 0, 0), font=name_font)

        # Ajouter le montant de la prime
        draw = ImageDraw.Draw(result)
        # Utiliser une police similaire à celle des avis de recherche
        try:
            font = ImageFont.truetype("arial.ttf", 38)  # Police augmentée à 38
        except:
            font = ImageFont.load_default()
        
        # Calculer la largeur de la prime pour le centrer
        bounty_bbox = draw.textbbox((0, 0), bounty, font=font)
        bounty_width = bounty_bbox[2] - bounty_bbox[0]
        bounty_x = (result.width - bounty_width) // 2  # Même position horizontale que le nom
        bounty_y = name_y + 80  # Augmenté l'espacement à 80 pixels sous le nom
        
        # Dessiner la prime en gras en la dessinant plusieurs fois avec un léger décalage
        for offset in range(2):
            draw.text((bounty_x + offset, bounty_y), bounty, fill=(0, 0, 0), font=font)

        # Afficher les résultats
        plt.figure(figsize=(15, 5))
        
        plt.subplot(131)
        plt.imshow(wanted)
        plt.title('Avis de recherche original')
        
        plt.subplot(132)
        plt.imshow(char_img)
        plt.title('Image du personnage ajustée')
        
        plt.subplot(133)
        plt.imshow(result)
        plt.title('Résultat final')
        
        plt.tight_layout()
        plt.savefig('character_integration_test.png')
        
        # Sauvegarder l'image finale
        result.save('wanted_poster_with_character.png')
        
        print("\nTest d'intégration terminé :")
        print(f"- Image redimensionnée à {new_width}x{new_height}")
        print(f"- Recadrée à {frame['width']}x{frame['height']}")
        print(f"- Montant de la prime ajouté : {bounty}")
        print("- Résultats sauvegardés dans 'character_integration_test.png' et 'wanted_poster_with_character.png'")
        
    except Exception as e:
        print(f"Erreur lors du traitement de l'image du personnage : {e}")

if __name__ == "__main__":
    wanted_poster_path = "img/avis de recherhche 2.jpg"
    character_image_path = "img/Don_Quichotte_Doflamingo_Portrait.webp"
    bounty = "76,000,000"  # Prime de Kuma
    test_character_image(wanted_poster_path, character_image_path, bounty) 