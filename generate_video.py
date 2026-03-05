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
df = pd.read_csv('date.csv')

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

def hex_to_rgb(hex_color):
    # Convertit une couleur hexadécimale en tuple RGB
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_polygon_decoration(w, h, color=(0, 0, 0)):
    # Création des décorations polygonales sur les côtés
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Polygone gauche
    points_left = [(0, h//2), (10, 0), (20, h//2), (10, h)]
    # Polygone droit
    points_right = [(w-20, h//2), (w-10, 0), (w, h//2), (w-10, h)]
    
    draw.polygon(points_left, fill=color)
    draw.polygon(points_right, fill=color)
    
    return ImageClip(np.array(img))

def create_circular_mask(size):
    # Création du cercle avec bordure et détails dorés
    mask = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(mask)
    
    # Cercle principal blanc
    draw.ellipse([0, 0, size[0]-1, size[1]-1], fill=(255, 255, 255, 255))
    
    # Bordure bleue
    border_width = 10
    draw.arc([0, 0, size[0]-1, size[1]-1], 0, 360, fill=BLUE_DARK, width=border_width)
    
    # Détails dorés
    draw.arc([0, 0, size[0]-1, size[1]-1], -45, 45, fill=GOLD, width=border_width)
    draw.arc([0, 0, size[0]-1, size[1]-1], 135, 225, fill=GOLD, width=border_width)
    
    return mask

def create_gradient_band(width, height, color_top, color_bottom):
    # Création d'une bande avec dégradé
    gradient = np.zeros((height, width, 4), dtype=np.uint8)
    for y in range(height):
        factor = y / height
        color = tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color_top, color_bottom))
        gradient[y, :] = color + (255,)
    return ImageClip(gradient)

def process_club_image(image_url, width, height):
    # Charge et redimensionne l'image du club depuis l'URL
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Ajoute un effet de transparence
        data = np.array(img)
        data[..., 3] = data[..., 3] * 0.3  # 30% d'opacité
        return Image.fromarray(data)
    except Exception as e:
        print(f"Erreur lors du chargement de l'image du club: {e}")
        return None

def create_frame(width, height, color=(0, 0, 0, 180)):
    # Crée un cadre semi-transparent avec coins arrondis
    frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([0, 0, width-1, height-1], radius=10, fill=color)
    return frame

def create_card(row):
    team_color = hex_to_rgb(row['team_color'])
    card = ColorClip(size=(CARD_WIDTH, CARD_HEIGHT), color=team_color)

    player_size = int(CARD_WIDTH * 0.92)
    player_y_pos = int(CARD_HEIGHT * 0.045)

    try:
        response = requests.get(row['image'])
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((player_size, player_size), Image.Resampling.LANCZOS)
        img_clip = ImageClip(np.array(img))
        img_clip = img_clip.set_position(('center', player_y_pos))
    except Exception as e:
        print(f"Erreur lors du chargement de l'image du joueur: {e}")
        img_clip = None

    frame_margin = int(CARD_HEIGHT * 0.018)

    # Cadre du nom
    name_frame_height = int(CARD_HEIGHT * 0.07)
    name_frame_y = player_y_pos + player_size + frame_margin
    name_frame = create_frame(CARD_WIDTH - 40, name_frame_height)
    name_frame_clip = ImageClip(np.array(name_frame))
    name_frame_clip = name_frame_clip.set_position(('center', name_frame_y))

    # Texte du nom
    name_text = TextClip(row['name'],
                        fontsize=int(HEIGHT * 0.042),
                        color='white',
                        font='Roboto-Bold')
    name_text = name_text.set_position(('center', name_frame_y + name_frame_height/2 - name_text.h/2))

    # Cadre fusionné montant + statut + logo club
    value_status_frame_height = int(CARD_HEIGHT * 0.18)
    value_status_frame_y = name_frame_y + name_frame_height + frame_margin
    value_status_frame = create_frame(CARD_WIDTH - 40, value_status_frame_height)
    value_status_frame_clip = ImageClip(np.array(value_status_frame))
    value_status_frame_clip = value_status_frame_clip.set_position(('center', value_status_frame_y))

    # Logo du club en fond dans ce cadre
    logo_clip = None
    try:
        response = requests.get(row['club_image'])
        club_logo = Image.open(BytesIO(response.content)).convert('RGBA')
        logo_width = int(CARD_WIDTH * 0.32)
        logo_height = int(value_status_frame_height * 0.8)
        club_logo = club_logo.resize((logo_width, int(logo_height)), Image.Resampling.LANCZOS)
        logo_data = np.array(club_logo)
        logo_data[..., 3] = (logo_data[..., 3] * 0.22).astype(np.uint8)
        club_logo = Image.fromarray(logo_data)
        logo_clip = ImageClip(np.array(club_logo))
        logo_x = (CARD_WIDTH - logo_width) // 2
        logo_y = value_status_frame_y + (value_status_frame_height - logo_height) // 2
        logo_clip = logo_clip.set_position((logo_x, logo_y))
    except Exception as e:
        print(f"Erreur lors du chargement du logo du club: {e}")
        logo_clip = None

    # Texte du montant
    value_text = f"{int(row['value']):,} ¥".replace(",", " ")
    value_text_clip = TextClip(value_text,
                            fontsize=int(HEIGHT * 0.055),
                            color='white',
                            font='Roboto-Bold')
    value_text_clip = value_text_clip.set_position(('center', value_status_frame_y + value_status_frame_height*0.32 - value_text_clip.h/2))

    # Statut
    status = str(row['status']).strip() if 'status' in row and pd.notna(row['status']) else ''
    if status.lower() == 'eliminated':
        status_color = 'red'
    elif status.lower() == 'qualified':
        status_color = 'green'
    else:
        status_color = 'white'
    show_status = status and status.lower() not in ['nan', '']
    if show_status:
        status_text_clip = TextClip(status,
                                fontsize=int(HEIGHT * 0.042),
                                color=status_color,
                                font='Roboto-Bold')
        status_text_clip = status_text_clip.set_position(('center', value_status_frame_y + value_status_frame_height*0.72 - status_text_clip.h/2))
    else:
        status_text_clip = None

    # Cadre de l'équipe
    team_frame_height = int(CARD_HEIGHT * 0.07)
    team_frame_y = value_status_frame_y + value_status_frame_height + frame_margin
    team_frame = create_frame(CARD_WIDTH - 40, team_frame_height)
    team_frame_clip = ImageClip(np.array(team_frame))
    team_frame_clip = team_frame_clip.set_position(('center', team_frame_y))

    team_text = TextClip(row['team'],
                        fontsize=int(HEIGHT * 0.037),
                        color='white',
                        font='Roboto-Bold')
    team_text = team_text.set_position(('center', team_frame_y + team_frame_height/2 - team_text.h/2))

    clips = [card]
    if img_clip is not None:
        clips.append(img_clip)
    clips.extend([
        name_frame_clip,
        name_text,
        value_status_frame_clip
    ])
    if logo_clip is not None:
        clips.append(logo_clip)
    clips.append(value_text_clip)
    if status_text_clip is not None:
        clips.append(status_text_clip)
    clips.extend([
        team_frame_clip,
        team_text
    ])

    return CompositeVideoClip(clips, size=(CARD_WIDTH, CARD_HEIGHT))

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
    "presentation_final.mp4",
    fps=60,  # 60fps pour une fluidité optimale
    codec='libx264',
    bitrate='4000k',  # Bon compromis pour du 1080p
    preset='medium',  # Bon équilibre entre vitesse et qualité
    threads=4,
    audio=False  # Désactivé car plus de musique
) 