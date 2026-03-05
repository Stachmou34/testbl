from moviepy.editor import *
import pandas as pd
import os
import numpy as np
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import time
from scipy import ndimage

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
    white_threshold = 245
    white_mask = np.all(img_array > white_threshold, axis=2)
    
    # Trouver les zones blanches connectées
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
            if (frame_width > width * 0.3 and frame_width < width * 0.8 and
                frame_height > height * 0.3 and frame_height < height * 0.6 and
                top > height * 0.1 and bottom < height * 0.9):
                margin = 2
                frame_info.append({
                    'top': top - margin,
                    'bottom': bottom + margin,
                    'left': left - margin,
                    'right': right + margin,
                    'width': frame_width + (2 * margin),
                    'height': frame_height + (2 * margin),
                    'area': area
                })
    
    # Trier par taille de zone
    frame_info.sort(key=lambda x: x['area'], reverse=True)
    
    if frame_info:
        return frame_info[0]
    return None

# Configuration de MoviePy pour utiliser ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

# Créer le dossier screen s'il n'existe pas
if not os.path.exists('screen'):
    os.makedirs('screen')

# Lecture des données CSV
csv_file = 'one_piece_bounties.csv'
df = pd.read_csv(csv_file)
df = df.sort_values(by="value", ascending=True)

# Configuration de la vidéo
WIDTH = 1700
HEIGHT = 800
SEPARATOR_WIDTH = 6
TOTAL_SEPARATORS_WIDTH = SEPARATOR_WIDTH * 2
CARD_WIDTH = (WIDTH - TOTAL_SEPARATORS_WIDTH) // 3
CARD_HEIGHT = HEIGHT
CARD_SPACING = CARD_WIDTH + SEPARATOR_WIDTH
FPS = 60
SCROLL_DURATION = 4.0
INTRO_DURATION = 1.2
PAUSE_DURATION = 0.6
INITIAL_DELAY = 0.3

def create_card(row):
    # Création de la carte de base avec fond blanc
    card = ColorClip(size=(CARD_WIDTH, CARD_HEIGHT), color=(255, 255, 255))
    
    # Chargement de l'image d'avis de recherche
    try:
        wanted_img = Image.open('img/avis de recherhche 2.jpg').convert('RGB')
        wanted_img = wanted_img.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
        
        # Analyser le cadre blanc pour obtenir les dimensions exactes
        frame = analyze_white_frame('img/avis de recherhche 2.jpg')
        if not frame:
            print("Impossible de détecter le cadre blanc.")
            return None
        
        # Calculer les dimensions proportionnelles pour la nouvelle taille
        width_ratio = CARD_WIDTH / wanted_img.width
        height_ratio = CARD_HEIGHT / wanted_img.height
        
        white_frame_width = int(frame['width'] * width_ratio)
        white_frame_height = int(frame['height'] * height_ratio)
        frame_left = int(frame['left'] * width_ratio)
        frame_top = int(frame['top'] * height_ratio)
        
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
                new_width = int(new_height * img_ratio * 1.1)  # Facteur d'échelle de 1.1
            else:
                new_width = white_frame_width
                new_height = int(new_width / img_ratio * 1.1)  # Facteur d'échelle de 1.1
            
            # Redimensionner l'image
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Recadrer l'image
            left = (new_width - white_frame_width) // 2
            top = (new_height - white_frame_height) // 2
            img = img.crop((left, top, left + white_frame_width, top + white_frame_height))
            
            # Créer une copie de l'avis de recherche
            result = wanted_img.copy()
            
            # Coller l'image du personnage
            result.paste(img, (frame_left, frame_top))
            
            # Ajouter un cadre noir autour de l'image du personnage
            draw = ImageDraw.Draw(result)
            draw.rectangle([(frame_left, frame_top), (frame_left + white_frame_width, frame_top + white_frame_height)], 
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
            name_y = frame_top + white_frame_height + 80
            
            # Couleur sépia pour le texte (marron foncé)
            text_color = (70, 35, 10)
            
            # Dessiner le texte sans effet de contour
            draw.text((name_x, name_y), name, fill=text_color, font=name_font)
            
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
            
            # Dessiner la prime avec la même couleur sépia
            draw.text((bounty_x, bounty_y), bounty, fill=text_color, font=font)
            
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

# Créer toutes les cartes
all_cards = [create_card(row) for _, row in df.iterrows()]

# Créer les clips pour l'animation
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

# Calculer la durée totale
total_duration = INTRO_DURATION + PAUSE_DURATION + ((len(all_cards) - 3) * SCROLL_DURATION) + SCROLL_DURATION * 3

# Créer la vidéo finale
final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
final_video = final_video.set_duration(total_duration)

# Générer la vidéo
final_video.write_videofile(
    "wanted_poster_video.mp4",
    fps=60,
    codec='libx264',
    bitrate='8000k',
    preset='medium',
    threads=28,
    audio=False
)

# Lancer la vidéo
#os.system('start wanted_poster_video.mp4') 