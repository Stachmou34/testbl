from moviepy.editor import *
import pandas as pd
import os
import numpy as np
from moviepy.config import change_settings
from PIL import Image, ImageDraw
import requests
from io import BytesIO
from colorthief import ColorThief

# Configuration de MoviePy pour utiliser ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

# Cache pour les couleurs dominantes
character_colors = {}

def get_dominant_color(image_path):
    if image_path in character_colors:
        return character_colors[image_path]
    
    try:
        img = Image.open(image_path)
        color_thief = ColorThief(image_path)
        dominant_color = color_thief.get_color(quality=1)
        # Assombrir légèrement la couleur pour un meilleur contraste
        darkened_color = tuple(int(c * 0.7) for c in dominant_color)
        character_colors[image_path] = darkened_color
        return darkened_color
    except Exception as e:
        print(f"Erreur lors de l'extraction de la couleur: {e}")
        return (41, 128, 185)  # Bleu par défaut

# Lecture des données CSV et sélection des 4 premiers personnages
df = pd.read_csv('characters_fire_force.csv')
# df = df.head(4)  # Cette ligne est supprimée pour traiter tous les personnages

# Configuration de la vidéo
WIDTH = 1920
HEIGHT = 1080
SEPARATOR_WIDTH = 8
TOTAL_SEPARATORS_WIDTH = SEPARATOR_WIDTH * 2
CARD_WIDTH = (WIDTH - TOTAL_SEPARATORS_WIDTH) // 3
CARD_HEIGHT = HEIGHT
CARD_SPACING = CARD_WIDTH + SEPARATOR_WIDTH
FPS = 30  # Réduit à 30 FPS
SCROLL_DURATION = 3.6
INTRO_DURATION = 1.0
PAUSE_DURATION = 0.5
INITIAL_DELAY = 0.2

# Couleurs
BLUE_LIGHT = (41, 128, 185)
BLUE_DARK = (31, 97, 141)
GOLD = (241, 196, 15)
FIRE_RED = (255, 69, 0)

def create_frame(width, height, color=(0, 0, 0, 180)):
    frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([0, 0, width-1, height-1], radius=10, fill=color)
    return frame

def create_fire_effect(width, height):
    # Création d'un effet de feu stylisé
    fire = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(fire)
    
    # Dessiner des flammes stylisées
    for i in range(5):
        points = [
            (width * 0.2 + i * width * 0.15, height * 0.8),
            (width * 0.3 + i * width * 0.15, height * 0.6),
            (width * 0.4 + i * width * 0.15, height * 0.8)
        ]
        draw.polygon(points, fill=(255, 69, 0, 100))
    
    return ImageClip(np.array(fire))

def create_card(row):
    # Couleur de fond basée sur l'image du personnage
    character_color = get_dominant_color(row['Image']) if row['Image'] != 'N/A' else BLUE_LIGHT
    card = ColorClip(size=(CARD_WIDTH, CARD_HEIGHT), color=character_color)

    # Image du personnage
    character_size = int(CARD_WIDTH * 0.92)
    character_y_pos = int(CARD_HEIGHT * 0.045)

    try:
        img = Image.open(row['Image']).convert('RGBA')
        img = img.resize((character_size, character_size), Image.Resampling.LANCZOS)
        img_clip = ImageClip(np.array(img))
        img_clip = img_clip.set_position(('center', character_y_pos))
    except Exception as e:
        print(f"Erreur lors du chargement de l'image du personnage: {e}")
        img_clip = None

    frame_margin = int(CARD_HEIGHT * 0.018)

    # Cadre du nom
    name_frame_height = int(CARD_HEIGHT * 0.07)
    name_frame_y = character_y_pos + character_size + frame_margin
    name_frame = create_frame(CARD_WIDTH - 40, name_frame_height)
    name_frame_clip = ImageClip(np.array(name_frame))
    name_frame_clip = name_frame_clip.set_position(('center', name_frame_y))

    # Texte du nom
    name_text = TextClip(row['Name'],
                        fontsize=int(HEIGHT * 0.042),
                        color='white',
                        font='Roboto-Bold')
    name_text = name_text.set_position(('center', name_frame_y + name_frame_height/2 - name_text.h/2))

    # Cadre des informations
    info_frame_height = int(CARD_HEIGHT * 0.24)  # Augmenté pour 3 lignes
    info_frame_y = name_frame_y + name_frame_height + frame_margin
    info_frame = create_frame(CARD_WIDTH - 40, info_frame_height)
    info_frame_clip = ImageClip(np.array(info_frame))
    info_frame_clip = info_frame_clip.set_position(('center', info_frame_y))

    # Effet de feu centré dans le cadre d'informations
    fire_effect = create_fire_effect(CARD_WIDTH - 40, info_frame_height)
    fire_effect = fire_effect.set_opacity(0.3)
    fire_effect = fire_effect.set_position((int((CARD_WIDTH - (CARD_WIDTH - 40)) / 2), info_frame_y))

    # Texte de la brigade
    company_text = TextClip(row['Company'],
                          fontsize=int(HEIGHT * 0.037),
                          color='white',
                          font='Roboto-Bold')
    company_text = company_text.set_position(('center', info_frame_y + info_frame_height*0.20 - company_text.h/2))

    # Texte de la position
    position_text = TextClip(row['Position'],
                          fontsize=int(HEIGHT * 0.037),
                          color='white',
                          font='Roboto-Bold')
    position_text = position_text.set_position(('center', info_frame_y + info_frame_height*0.50 - position_text.h/2))

    # Affichage de l'âge dans le style demandé
    if str(row['Age']).strip().lower() == 'unknown':
        age_number = TextClip('Unknown', fontsize=int(HEIGHT * 0.045), color='white', font='Roboto-Bold')
        age_number = age_number.set_position(('center', info_frame_y + info_frame_height*0.80 - age_number.h/2))
        age_label = None
    else:
        age_number = TextClip(str(row['Age']), fontsize=int(HEIGHT * 0.065), color='white', font='Roboto-Bold')
        age_label = TextClip('Years\nold', fontsize=int(HEIGHT * 0.037), color='white', font='Roboto-Bold', method='caption', align='West')
        # Augmenter l'espacement horizontal
        age_x = int(CARD_WIDTH/2 - 90)
        label_x = int(CARD_WIDTH/2 + 50)
        age_y = int(info_frame_y + info_frame_height*0.80 - age_number.h/2)
        label_y = int(info_frame_y + info_frame_height*0.80 - age_label.h/2)
        age_number = age_number.set_position((age_x, age_y))
        age_label = age_label.set_position((label_x, label_y))

    clips = [card]
    if img_clip is not None:
        clips.append(img_clip)
    clips.extend([
        name_frame_clip,
        name_text,
        info_frame_clip,
        fire_effect,
        company_text,
        position_text,
        age_number
    ])
    if age_label is not None:
        clips.append(age_label)

    return CompositeVideoClip(clips, size=(CARD_WIDTH, CARD_HEIGHT))

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

# Création de toutes les cartes
all_cards = [create_card(row) for _, row in df.iterrows()]

# Création des clips avec animation
clips = []

# Phase 1: Animation d'introduction pour les 3 premières cartes
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

# Calcul de la durée totale ajustée
total_duration = INTRO_DURATION + PAUSE_DURATION + ((len(all_cards) - 3) * SCROLL_DURATION) + SCROLL_DURATION * 3

# Création de la vidéo finale
final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
final_video = final_video.set_duration(total_duration)

# Export de la vidéo
final_video.write_videofile(
    "fire_force_presentation.mp4",
    fps=30,  # Réduit à 30 FPS
    codec='libx264',
    bitrate='4000k',
    preset='medium',
    threads=4,
    audio=False
) 