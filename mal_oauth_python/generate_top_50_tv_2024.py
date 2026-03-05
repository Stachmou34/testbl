from moviepy.editor import *
import pandas as pd
import os
import numpy as np
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from colorthief import ColorThief

# Configuration de MoviePy pour utiliser ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

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
        # Assombrir légèrement la couleur pour un meilleur contraste
        darkened_color = tuple(int(c * 0.7) for c in dominant_color)
        club_colors[image_url] = darkened_color
        return darkened_color
    except Exception as e:
        print(f"Erreur lors de l'extraction de la couleur: {e}")
        return BLUE_LIGHT

# Lecture des données CSV
df = pd.read_csv('top_50_tv_2024.csv')

# Trier les animes par score moyen croissant (de la plus mauvaise à la meilleure note)
df.sort_values(by='mean', ascending=True, inplace=True)

# Ne garder que les 50 premiers
df = df.head(50)

# Configuration de la vidéo
WIDTH = 1920  # Résolution 1080p (16:9)
HEIGHT = 1080
SEPARATOR_WIDTH = 8  # Augmenté proportionnellement à la résolution
TOTAL_SEPARATORS_WIDTH = SEPARATOR_WIDTH * 2
CARD_WIDTH = (WIDTH - TOTAL_SEPARATORS_WIDTH) // 3
CARD_HEIGHT = HEIGHT
CARD_SPACING = CARD_WIDTH + SEPARATOR_WIDTH
FPS = 60  # Augmenté à 60 FPS pour une meilleure fluidité
SCROLL_DURATION = 3.6  # Augmenté de 2.4 à 3.6 pour un défilement plus lent
INTRO_DURATION = 1.0
PAUSE_DURATION = 0.5
INITIAL_DELAY = 0.2

# Couleurs
BLUE_LIGHT = (41, 128, 185)
BLUE_DARK = (31, 97, 141)
GOLD = (241, 196, 15)

def create_card(row):
    from PIL import ImageFont

    # Paramètres
    bg_color = (30, 30, 40)
    band_color = (0, 0, 0)
    text_color = (255, 255, 255)
    genre_color = (200, 200, 200)
    margin = 32
    band_h = int(CARD_HEIGHT * 0.32)
    img_h = CARD_HEIGHT - band_h

    # Créer la carte
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), bg_color)
    draw = ImageDraw.Draw(card)

    # Image de l'anime
    try:
        response = requests.get(row['image'], timeout=10)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((CARD_WIDTH, img_h), Image.LANCZOS)
        card.paste(img, (0, 0))
    except Exception as e:
        print(f"Erreur image: {e}")

    # Bandeau noir en bas
    band = Image.new("RGB", (CARD_WIDTH, band_h), band_color)
    card.paste(band, (0, img_h))

    # Polices (Luckiest Guy partout, date réduite)
    try:
        font_genre = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 30)
        font_title = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 48)
        font_type = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 30)
        font_date = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 40)
        font_score = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 60)
    except:
        font_genre = font_title = font_type = font_date = font_score = ImageFont.load_default()

    # Score (en haut à droite)
    score_txt = f"Score: {row['mean']:.2f}" if pd.notna(row['mean']) else "Score: N/A"
    bbox_score = draw.textbbox((0, 0), score_txt, font=font_score)
    w_score, h_score = bbox_score[2] - bbox_score[0], bbox_score[3] - bbox_score[1]
    draw.text((CARD_WIDTH - w_score - margin, margin), score_txt, font=font_score, fill=GOLD)

    # Date (centré en haut du bandeau, moins imposante)
    date_txt = f"Release on {row['start_date']}" if pd.notna(row['start_date']) else "Release date TBA"
    bbox = draw.textbbox((0, 0), date_txt, font=font_date)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y_date = img_h+10
    draw.text(((CARD_WIDTH-w)//2, y_date), date_txt, font=font_date, fill=text_color)

    # Trait blanc de séparation
    y_sep = y_date + h + 10
    draw.line([(margin, y_sep), (CARD_WIDTH-margin, y_sep)], fill=(255,255,255), width=3)

    # Genres (max 3, aligné à gauche)
    genres = str(row['genres']) if pd.notna(row['genres']) else ""
    genres_list = [g.strip() for g in genres.split(',')][:3]
    genres_str = ', '.join(genres_list)
    draw.text((margin, y_sep+10), genres_str, font=font_genre, fill=genre_color)

    # Type (centré en bas du bandeau)
    type_txt = str(row['media_type']).upper()
    bbox_type = draw.textbbox((0, 0), type_txt, font=font_type)
    w_type, h_type = bbox_type[2] - bbox_type[0], bbox_type[3] - bbox_type[1]
    y_type = CARD_HEIGHT - h_type - 18
    draw.text(((CARD_WIDTH-w_type)//2, y_type), type_txt, font=font_type, fill=text_color)

    # Titre (centré, retour à la ligne si besoin, centré verticalement entre genres et type)
    title = str(row['title'])
    max_width = CARD_WIDTH - 2*margin
    lines = []
    words = title.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        w = bbox[2] - bbox[0]
        if w > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines.append(line)
    # Calculer la hauteur totale du bloc titre
    h_lines = [draw.textbbox((0, 0), l, font=font_title)[3] - draw.textbbox((0, 0), l, font=font_title)[1] for l in lines]
    total_title_height = sum(h_lines) + (len(h_lines)-1)*2
    # Espace vertical disponible
    y_genres = y_sep+10
    y_title_zone_top = y_genres + font_genre.size + 10
    y_title_zone_bottom = y_type - 10
    available_height = y_title_zone_bottom - y_title_zone_top
    y_title = y_title_zone_top + (available_height - total_title_height)//2
    for idx, l in enumerate(lines):
        bbox = draw.textbbox((0, 0), l, font=font_title)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((CARD_WIDTH-w)//2, y_title), l, font=font_title, fill=text_color)
        y_title += h + 2

    return ImageClip(np.array(card))

def create_separator():
    return ColorClip(size=(SEPARATOR_WIDTH, CARD_HEIGHT), color=(0, 0, 0))

def get_card_position(index):
    # Calcule la position X d'une carte en fonction de son index
    if index == 0:
        return 0
    elif index == 1:
        return CARD_WIDTH + SEPARATOR_WIDTH
    else:
        return (CARD_WIDTH + SEPARATOR_WIDTH) * 2

def get_separator_position(index):
    # Calcule la position X d'un séparateur en fonction de son index
    return CARD_WIDTH + (index * CARD_SPACING)

# Création de toutes les cartes
all_cards = [create_card(row) for _, row in df.iterrows()]

# Création des clips avec animation
clips = []

# Phase 1: Animation d'introduction pour les 3 premières cartes et séparateurs
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
    
    # Ajout de la carte
    intro_clip = card.set_position(make_position(i, final_x))
    intro_clip = intro_clip.set_start(0)
    intro_clip = intro_clip.set_duration(INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5)
    clips.append(intro_clip)
    
    # Ajout du séparateur après la carte (sauf pour la dernière)
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

# Phase 2: Animation de défilement pour toutes les cartes après la 3ème
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
    
    # Ajout de la carte
    moving_clip = card.set_position(make_scroll_position_function())
    moving_clip = moving_clip.set_start(start_time)
    moving_clip = moving_clip.set_duration(duration)
    clips.append(moving_clip)
    
    # Ajout du séparateur avant la carte
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

# Calcul de la durée totale ajustée
total_duration = INTRO_DURATION + PAUSE_DURATION + ((len(all_cards) - 3) * SCROLL_DURATION) + SCROLL_DURATION * 3

# Création de la vidéo finale
final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
final_video = final_video.set_duration(total_duration)

# Export de la vidéo
final_video.write_videofile(
    "top_50_tv_2024_presentation.mp4",
    fps=60,  # 60fps pour une fluidité optimale
    codec='libx264',
    bitrate='4000k',  # Bon compromis pour du 1080p
    preset='medium',  # Bon équilibre entre vitesse et qualité
    threads=4,
    audio=False  # Désactivé car plus de musique
) 