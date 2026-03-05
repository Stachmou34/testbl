from moviepy.editor import *
import pandas as pd
import os
import numpy as np
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from colorthief import ColorThief
import math
from scipy import ndimage
import cv2
import time

# Configuration de MoviePy pour utiliser ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

# Créer le dossier screen s'il n'existe pas
if not os.path.exists('screen'):
    os.makedirs('screen')

# Cache pour les couleurs dominantes
club_colors = {}

def get_dominant_color(image_url):
    if image_url in club_colors:
        return club_colors[image_url]
    
    try:
        response = requests.get(image_url)
        img_data = BytesIO(response.content)
        color_thief = ColorThief(img_data)
        dominant_color = color_thief.get_color(quality=1)
        darkened_color = tuple(int(c * 0.7) for c in dominant_color)
        club_colors[image_url] = darkened_color
        return darkened_color
    except Exception as e:
        print(f"Erreur lors de l'extraction de la couleur: {e}")
        return BLUE_LIGHT

# Lecture des données CSV
# Changer ici le nom du fichier CSV
csv_file = 'one_piece_bounties.csv'
df = pd.read_csv(csv_file)
df = df.sort_values(by="value", ascending=True)

# Limiter aux 5 premiers personnages
df = df.head(4)

# Configuration de la vidéo
WIDTH = 1920
HEIGHT = 1080
SEPARATOR_WIDTH = 8
TOTAL_SEPARATORS_WIDTH = SEPARATOR_WIDTH * 2
CARD_WIDTH = (WIDTH - TOTAL_SEPARATORS_WIDTH) // 3
CARD_HEIGHT = HEIGHT
CARD_SPACING = CARD_WIDTH + SEPARATOR_WIDTH
FPS = 60
SCROLL_DURATION = 3.6
INTRO_DURATION = 1.0
PAUSE_DURATION = 0.5
INITIAL_DELAY = 0.2

# Couleurs
BLUE_LIGHT = (41, 128, 185)
BLUE_DARK = (31, 97, 141)
GOLD = (241, 196, 15)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (60, 60, 60)

# Police One Piece
ONE_PIECE_FONT = "fonts/one-piece.ttf"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_polygon_decoration(w, h, color=(0, 0, 0)):
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    points_left = [(0, h//2), (10, 0), (20, h//2), (10, h)]
    points_right = [(w-20, h//2), (w-10, 0), (w, h//2), (w-10, h)]
    draw.polygon(points_left, fill=color)
    draw.polygon(points_right, fill=color)
    return ImageClip(np.array(img))

def create_circular_mask(size):
    mask = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size[0]-1, size[1]-1], fill=(255, 255, 255, 255))
    border_width = 10
    draw.arc([0, 0, size[0]-1, size[1]-1], 0, 360, fill=BLUE_DARK, width=border_width)
    draw.arc([0, 0, size[0]-1, size[1]-1], -45, 45, fill=GOLD, width=border_width)
    draw.arc([0, 0, size[0]-1, size[1]-1], 135, 225, fill=GOLD, width=border_width)
    return mask

def create_gradient_band(width, height, color_top, color_bottom):
    gradient = np.zeros((height, width, 4), dtype=np.uint8)
    for y in range(height):
        factor = y / height
        color = tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color_top, color_bottom))
        gradient[y, :] = color + (255,)
    return ImageClip(gradient)

def process_club_image(image_url, width, height):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        data = np.array(img)
        data[..., 3] = data[..., 3] * 0.3
        return Image.fromarray(data)
    except Exception as e:
        print(f"Erreur lors du chargement de l'image du club: {e}")
        return None

def create_frame(width, height, color=(0, 0, 0, 180)):
    frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([0, 0, width-1, height-1], radius=10, fill=color)
    return frame

def resize_and_fit_image(img, target_width, target_height):
    """
    Redimensionne et ajuste l'image pour remplir complètement la zone cible
    en zoomant si nécessaire pour éviter les espaces vides
    """
    # Calculer le ratio de l'image source et de la cible
    source_ratio = img.width / img.height
    target_ratio = target_width / target_height

    if source_ratio > target_ratio:
        # Image plus large que la cible : on se base sur la hauteur
        new_height = target_height
        new_width = int(new_height * source_ratio)
        # Recadrer la largeur
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        img = img.crop((left, 0, left + target_width, new_height))
    else:
        # Image plus haute que la cible : on se base sur la largeur
        new_width = target_width
        new_height = int(new_width / source_ratio)
        # Recadrer la hauteur
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        top = (new_height - target_height) // 2
        img = img.crop((0, top, new_width, top + target_height))

    # S'assurer que l'image finale a exactement les dimensions cibles
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    return img

def find_white_area(image):
    """
    Détecte précisément les bords du cadre blanc dans l'avis de recherche
    en utilisant des contraintes de taille et de position
    """
    # Convertir l'image en niveaux de gris
    gray = image.convert('L')
    data = np.array(gray)
    
    # Créer un masque pour les pixels très clairs (presque blancs)
    white_mask = data > 245  # Réduire légèrement le seuil pour mieux détecter le cadre
    
    # Trouver les coordonnées des pixels blancs
    y_coords, x_coords = np.where(white_mask)
    
    if len(y_coords) > 0:
        # Définir les limites attendues pour le cadre blanc (en pourcentage de l'image)
        expected_width_min = int(image.size[0] * 0.40)  # Au moins 40% de la largeur
        expected_width_max = int(image.size[0] * 0.65)  # Au plus 65% de la largeur
        expected_height_min = int(image.size[1] * 0.30)  # Au moins 30% de la hauteur
        expected_height_max = int(image.size[1] * 0.55)  # Au plus 55% de la hauteur
        
        # Trouver les zones blanches connectées
        labeled_array, num_features = ndimage.label(white_mask)
        
        # Pour chaque zone blanche connectée
        best_area = None
        best_size = 0
        
        for feature in range(1, num_features + 1):
            feature_mask = labeled_array == feature
            feature_y, feature_x = np.where(feature_mask)
            
            # Calculer les dimensions de cette zone
            min_y, max_y = np.min(feature_y), np.max(feature_y)
            min_x, max_x = np.min(feature_x), np.max(feature_x)
            width = max_x - min_x
            height = max_y - min_y
            
            # Vérifier si cette zone correspond aux dimensions attendues
            if (expected_width_min <= width <= expected_width_max and 
                expected_height_min <= height <= expected_height_max):
                # Calculer la taille de la zone
                area_size = width * height
                
                # Garder la plus grande zone qui correspond aux critères
                if area_size > best_size:
                    best_size = area_size
                    # Ajuster les dimensions pour être sûr de remplir le cadre
                    width = int(width * 1.15)  # Augmenter de 15% la largeur
                    height = int(height * 1.15)  # Augmenter de 15% la hauteur
                    
                    # Recentrer la zone
                    min_x = max(0, min_x - int(width * 0.075))
                    min_y = max(0, min_y - int(height * 0.075))
                    
                    best_area = {
                        'x': min_x,
                        'y': min_y,
                        'width': width,
                        'height': height
                    }
        
        if best_area:
            print(f"Meilleure zone trouvée - X: {best_area['x']}, Y: {best_area['y']}, Largeur: {best_area['width']}, Hauteur: {best_area['height']}")
            return best_area
    
    # Si aucune zone appropriée n'est trouvée, utiliser des dimensions par défaut
    default_width = int(image.size[0] * 0.55)
    default_height = int(image.size[1] * 0.45)
    default_x = (image.size[0] - default_width) // 2
    default_y = int(image.size[1] * 0.15)
    
    print("Utilisation des dimensions par défaut")
    return {
        'x': default_x,
        'y': default_y,
        'width': default_width,
        'height': default_height
    }

def find_text_areas(image, white_area):
    """
    Trouve les zones de texte dans l'avis de recherche
    """
    height = image.size[1]
    
    # Zone pour le nom (juste en dessous de la photo)
    name_y = white_area['y'] + white_area['height'] + int(height * 0.02)
    name_height = int(height * 0.1)
    
    # Zone pour la prime (au-dessus de "MARINE")
    # On cherche la position du texte "MARINE" en bas
    data = np.array(image)
    # On regarde dans le dernier quart de l'image
    bottom_quarter = data[int(height * 0.75):, :, :]
    # Chercher les pixels non blancs (le texte)
    text_mask = (bottom_quarter[:, :, 0] < 240) | (bottom_quarter[:, :, 1] < 240) | (bottom_quarter[:, :, 2] < 240)
    text_coords = np.where(text_mask)
    if len(text_coords[0]) > 0:
        marine_y = int(height * 0.75) + np.min(text_coords[0])
        prime_y = marine_y - int(height * 0.15)  # La prime est placée au-dessus de "MARINE"
    else:
        prime_y = int(height * 0.8)  # Position par défaut
    
    return {
        'name': {
            'y': name_y,
            'height': name_height
        },
        'prime': {
            'y': prime_y,
            'height': int(height * 0.12)
        }
    }

def check_white_borders(img):
    """
    Vérifie si les 4 bords de l'image contiennent des pixels blancs
    """
    # Convertir en tableau numpy pour faciliter l'analyse
    img_array = np.array(img)
    
    # Seuils pour détecter le blanc (encore plus strict)
    white_threshold = 235
    
    # Vérifier les bords avec une marge plus large
    margin = 3  # Vérifier 3 pixels de chaque côté
    top_border = img_array[:margin, :, :]
    bottom_border = img_array[-margin:, :, :]
    left_border = img_array[:, :margin, :]
    right_border = img_array[:, -margin:, :]
    
    # Compter les pixels blancs sur chaque bord (au moins 3 pixels consécutifs)
    def has_white_line(border):
        return np.any(np.all(np.all(border > white_threshold, axis=2), axis=0))
    
    top_white = has_white_line(top_border)
    bottom_white = has_white_line(bottom_border)
    left_white = has_white_line(left_border)
    right_white = has_white_line(right_border)
    
    print(f"Pixels blancs détectés - Haut: {top_white}, Bas: {bottom_white}, Gauche: {left_white}, Droite: {right_white}")
    
    return top_white, bottom_white, left_white, right_white

def create_card(row):
    # Création de la carte de base avec fond blanc
    card = ColorClip(size=(CARD_WIDTH, CARD_HEIGHT), color=(255, 255, 255))
    
    # Chargement de l'image d'avis de recherche
    try:
        wanted_img = Image.open('img/avis de recherhche 2.jpg').convert('RGB')
        wanted_img = wanted_img.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
        
        # Dimensions du cadre blanc
        white_frame_width = int(CARD_WIDTH * 0.81)
        white_frame_height = int(CARD_HEIGHT * 0.65)
        
        # Chargement et redimensionnement de l'image du personnage
        try:
            image_path = str(row['image'])
            if image_path.startswith('http'):
                response = requests.get(image_path)
                img = Image.open(BytesIO(response.content)).convert('RGB')
            else:
                img = Image.open(image_path).convert('RGB')
            
            # Calculer les dimensions pour remplir complètement le cadre blanc
            img_ratio = img.width / img.height
            frame_ratio = white_frame_width / white_frame_height
            
            if img_ratio > frame_ratio:
                new_height = white_frame_height
                new_width = int(new_height * img_ratio * 1.12)
            else:
                new_width = white_frame_width
                new_height = int(new_width / img_ratio * 1.12)
            
            # Redimensionner l'image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Recadrer l'image
            left = (new_width - white_frame_width) // 2
            top = (new_height - white_frame_height) // 2
            img = img.crop((left, top, left + white_frame_width, top + white_frame_height))
            
            # Créer une copie de l'avis de recherche
            result = wanted_img.copy()
            
            # Position de la photo
            photo_x = (CARD_WIDTH - white_frame_width) // 2
            photo_y = int(CARD_HEIGHT * 0.105)
            
            # Coller l'image du personnage
            result.paste(img, (photo_x, photo_y))
            
            # Ajouter un cadre noir autour de l'image du personnage
            draw = ImageDraw.Draw(result)
            draw.rectangle([(photo_x, photo_y), (photo_x + white_frame_width, photo_y + white_frame_height)], 
                          outline=(0, 0, 0), width=2)
            
            # Ajouter le nom du personnage
            try:
                name_font = ImageFont.truetype("arial.ttf", 42)
            except:
                name_font = ImageFont.load_default()
            
            name = row['name'].upper()
            # Calculer la largeur du texte pour le centrer
            name_bbox = draw.textbbox((0, 0), name, font=name_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = (result.width - name_width) // 2
            name_y = photo_y + white_frame_height + 80
            
            # Dessiner le texte en gras en le dessinant plusieurs fois avec un léger décalage
            for offset in range(2):
                draw.text((name_x + offset, name_y), name, fill=(0, 0, 0), font=name_font)
            
            # Ajouter le montant de la prime
            try:
                font = ImageFont.truetype("arial.ttf", 38)
            except:
                font = ImageFont.load_default()
            
            bounty = f"{row['value']:,}"
            # Calculer la largeur de la prime pour le centrer
            bounty_bbox = draw.textbbox((0, 0), bounty, font=font)
            bounty_width = bounty_bbox[2] - bounty_bbox[0]
            bounty_x = (result.width - bounty_width) // 2
            bounty_y = name_y + 80
            
            # Dessiner la prime en gras en la dessinant plusieurs fois avec un léger décalage
            for offset in range(2):
                draw.text((bounty_x + offset, bounty_y), bounty, fill=(0, 0, 0), font=font)
            
            # Convertir l'image PIL en tableau numpy pour MoviePy
            result_np = np.array(result)
            card = ImageClip(result_np)
            
        except Exception as e:
            print(f"Erreur lors du traitement de l'image du personnage : {e}")
            return None
            
    except Exception as e:
        print(f"Erreur lors du chargement de l'avis de recherche : {e}")
        return None
    
    return card

def create_separator():
    return ColorClip(size=(SEPARATOR_WIDTH, CARD_HEIGHT), color=(0, 0, 0))

def get_card_position(index):
    if index == 0:
        return 0
    elif index == 1:
        return CARD_WIDTH + SEPARATOR_WIDTH
    else:
        return (CARD_WIDTH + SEPARATOR_WIDTH) * 2

def get_separator_position(index):
    return CARD_WIDTH + (index * CARD_SPACING)

def analyze_wanted_poster():
    """
    Analyse l'image de l'avis de recherche pour mesurer le cadre blanc
    """
    try:
        # Charger l'image
        img = Image.open('img/avis de recherhche 2.jpg').convert('RGB')
        width, height = img.size
        
        # Convertir en tableau numpy
        img_array = np.array(img)
        
        # Seuil pour détecter le blanc
        white_threshold = 230
        
        # Créer un masque pour les pixels blancs
        white_mask = np.all(img_array > white_threshold, axis=2)
        
        # Trouver les coordonnées des pixels blancs
        white_coords = np.where(white_mask)
        
        if len(white_coords[0]) > 0:
            # Trouver les limites du cadre blanc
            top = np.min(white_coords[0])
            bottom = np.max(white_coords[0])
            left = np.min(white_coords[1])
            right = np.max(white_coords[1])
            
            # Calculer les dimensions
            frame_width = right - left
            frame_height = bottom - top
            
            # Calculer les pourcentages
            width_percent = (frame_width / width) * 100
            height_percent = (frame_height / height) * 100
            
            print(f"\nAnalyse du cadre blanc dans l'avis de recherche:")
            print(f"Largeur du cadre: {frame_width}px ({width_percent:.1f}% de l'image)")
            print(f"Hauteur du cadre: {frame_height}px ({height_percent:.1f}% de l'image)")
            print(f"Position: Haut={top}px, Bas={bottom}px, Gauche={left}px, Droite={right}px")
            
            return width_percent, height_percent
            
    except Exception as e:
        print(f"Erreur lors de l'analyse de l'image: {e}")
        return None

# Analyser l'image avant de générer la vidéo
dimensions = analyze_wanted_poster()

if dimensions:
    width_percent, height_percent = dimensions
    # Utiliser ces dimensions pour le cadre
    white_frame_width = int(CARD_WIDTH * (width_percent / 100))
    white_frame_height = int(CARD_HEIGHT * (height_percent / 100))
else:
    # Dimensions par défaut si l'analyse échoue
    white_frame_width = int(CARD_WIDTH * 0.81)
    white_frame_height = int(CARD_HEIGHT * 0.65)

all_cards = [create_card(row) for _, row in df.iterrows()]
clips = []
for i in range(min(3, len(all_cards))):
    card = all_cards[i]
    final_x = get_card_position(i)
    def make_position(index, final_pos):
        def get_position(t):
            intro_start = index * INITIAL_DELAY
            relative_intro_t = t - intro_start
            if relative_intro_t < 0:
                return (final_pos, -HEIGHT)
            elif t < INTRO_DURATION:
                start_y = -HEIGHT
                end_y = 0
                progress = relative_intro_t / (INTRO_DURATION - (index * INITIAL_DELAY))
                progress = min(1, progress)
                eased_progress = 1 - (1 - progress) ** 2
                return (final_pos, start_y + (end_y - start_y) * eased_progress)
            elif t < (INTRO_DURATION + PAUSE_DURATION):
                return (final_pos, 0)
            else:
                scroll_time = t - (INTRO_DURATION + PAUSE_DURATION)
                speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                x = final_pos - (scroll_time * speed)
                return (x, 0)
        return get_position
    intro_clip = card.set_position(make_position(i, final_x))
    intro_clip = intro_clip.set_start(0)
    intro_clip = intro_clip.set_duration(INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5)
    clips.append(intro_clip)
    if i < 2:
        separator = create_separator()
        separator_x = get_separator_position(i)
        def make_separator_position(index, sep_pos):
            def get_position(t):
                if t < INTRO_DURATION + PAUSE_DURATION:
                    return (sep_pos, 0)
                else:
                    scroll_time = t - (INTRO_DURATION + PAUSE_DURATION)
                    speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                    x = sep_pos - (scroll_time * speed)
                    return (x, 0)
            return get_position
        separator_clip = separator.set_position(make_separator_position(i, separator_x))
        separator_clip = separator_clip.set_start(0)
        separator_clip = separator_clip.set_duration(INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5)
        clips.append(separator_clip)
for i in range(3, len(all_cards)):
    card = all_cards[i]
    start_time = INTRO_DURATION + PAUSE_DURATION + ((i - 3) * SCROLL_DURATION)
    duration = SCROLL_DURATION * 4
    def make_scroll_position_function():
        def get_position(t):
            start_x = WIDTH
            speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
            x = start_x - (t * speed)
            return (x, 0)
        return get_position
    moving_clip = card.set_position(make_scroll_position_function())
    moving_clip = moving_clip.set_start(start_time)
    moving_clip = moving_clip.set_duration(duration)
    clips.append(moving_clip)
    separator = create_separator()
    def make_separator_scroll_position():
        def get_position(t):
            start_x = WIDTH - SEPARATOR_WIDTH
            speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
            x = start_x - (t * speed)
            return (x, 0)
        return get_position
    separator_clip = separator.set_position(make_separator_scroll_position())
    separator_clip = separator_clip.set_start(start_time)
    separator_clip = separator_clip.set_duration(duration)
    clips.append(separator_clip)
total_duration = INTRO_DURATION + PAUSE_DURATION + ((len(all_cards) - 3) * SCROLL_DURATION) + SCROLL_DURATION * 3
final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
final_video = final_video.set_duration(total_duration)

# Après la génération de la vidéo, lancer la vidéo et faire une capture
def analyze_screenshot():
    # Attendre 2 secondes
    time.sleep(2)
    
    # Faire une capture d'écran
    import pyautogui
    screenshot = pyautogui.screenshot()
    screenshot_path = os.path.join('screen', 'capture.png')
    screenshot.save(screenshot_path)
    
    # Analyser la capture pour détecter les zones blanches
    img = cv2.imread(screenshot_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    white_pixels = cv2.countNonZero(cv2.inRange(gray, 250, 255))
    total_pixels = img.shape[0] * img.shape[1]
    white_ratio = white_pixels / total_pixels
    
    print(f"Ratio de pixels blancs : {white_ratio:.2%}")
    return white_ratio > 0.01  # Si plus de 1% de pixels blancs

# Après la génération de la vidéo
final_video.write_videofile(
    "presentation_one_piece.mp4",
    fps=30,
    codec='libx264',
    bitrate='4000k',
    preset='medium',
    threads=28,
    audio=False
)

# Lancer la vidéo
os.system('start presentation_one_piece.mp4')

# Analyser la capture
has_white = analyze_screenshot()
if has_white:
    print("Des zones blanches ont été détectées. Ajustement nécessaire des dimensions.")
else:
    print("Aucune zone blanche significative détectée.") 