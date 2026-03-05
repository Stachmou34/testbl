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
        darkened_color = tuple(int(c * 0.7) for c in dominant_color)
        club_colors[image_url] = darkened_color
        return darkened_color
    except Exception as e:
        print(f"Erreur lors de l'extraction de la couleur: {e}")
        return BLUE_LIGHT

# Lecture des données CSV
df_2023 = pd.read_csv('top_50_tv_2023.csv')
df_2024 = pd.read_csv('top_50_tv_2024.csv')

# Configuration de la vidéo
WIDTH = 1920
HEIGHT = 1080
SEPARATOR_WIDTH = 8
TOTAL_SEPARATORS_WIDTH = SEPARATOR_WIDTH * 2
CARD_WIDTH = (WIDTH - TOTAL_SEPARATORS_WIDTH) // 3
CARD_HEIGHT = int((HEIGHT - SEPARATOR_WIDTH * 2) // 2.3)
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
RED = (231, 76, 60)
GREEN = (46, 204, 113)

def create_comparison_card(row_2023, row_2024, index):
    from PIL import ImageFont

    # Paramètres
    bg_color = (30, 30, 40)
    band_color = (0, 0, 0)
    text_color = (255, 255, 255)
    margin = 18
    band_h = int(CARD_HEIGHT * 0.22)
    img_h = CARD_HEIGHT - band_h - 10

    # Créer la carte
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT * 2 + SEPARATOR_WIDTH), bg_color)
    draw = ImageDraw.Draw(card)

    # Images des animes
    try:
        # Image 2023 (en haut)
        response_2023 = requests.get(row_2023['image'], timeout=10)
        img_2023 = Image.open(BytesIO(response_2023.content)).convert('RGB')
        img_2023 = img_2023.resize((CARD_WIDTH, img_h), Image.LANCZOS)
        card.paste(img_2023, (0, 0))

        # Image 2024 (en bas)
        response_2024 = requests.get(row_2024['image'], timeout=10)
        img_2024 = Image.open(BytesIO(response_2024.content)).convert('RGB')
        img_2024 = img_2024.resize((CARD_WIDTH, img_h), Image.LANCZOS)
        card.paste(img_2024, (0, CARD_HEIGHT + SEPARATOR_WIDTH))
    except Exception as e:
        print(f"Erreur image: {e}")

    # Bandeaux noirs
    band_2023 = Image.new("RGB", (CARD_WIDTH, band_h), band_color)
    band_2024 = Image.new("RGB", (CARD_WIDTH, band_h), band_color)
    card.paste(band_2023, (0, img_h))
    card.paste(band_2024, (0, CARD_HEIGHT + SEPARATOR_WIDTH + img_h))

    # Polices
    try:
        font_title = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 38)
        font_score = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 44)
        font_year = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 48)
    except:
        font_title = font_score = font_year = ImageFont.load_default()

    # Années
    draw.text((margin, margin), "2023", font=font_year, fill=BLUE_LIGHT)
    draw.text((margin, CARD_HEIGHT + SEPARATOR_WIDTH + margin), "2024", font=font_year, fill=GOLD)

    # Scores avec comparaison
    score_2023 = row_2023['mean']
    score_2024 = row_2024['mean']
    score_diff = score_2024 - score_2023
    
    # Score 2023
    score_txt_2023 = f"Score: {score_2023:.2f}"
    bbox_score = draw.textbbox((0, 0), score_txt_2023, font=font_score)
    w_score, h_score = bbox_score[2] - bbox_score[0], bbox_score[3] - bbox_score[1]
    draw.text((CARD_WIDTH - w_score - margin, margin), score_txt_2023, font=font_score, fill=BLUE_LIGHT)

    # Score 2024
    score_txt_2024 = f"Score: {score_2024:.2f}"
    bbox_score = draw.textbbox((0, 0), score_txt_2024, font=font_score)
    w_score, h_score = bbox_score[2] - bbox_score[0], bbox_score[3] - bbox_score[1]
    draw.text((CARD_WIDTH - w_score - margin, CARD_HEIGHT + SEPARATOR_WIDTH + margin), score_txt_2024, font=font_score, fill=GOLD)

    # Différence de score (au centre)
    diff_color = GREEN if score_diff > 0 else RED
    diff_txt = f"{'+' if score_diff > 0 else ''}{score_diff:.2f}"
    bbox_diff = draw.textbbox((0, 0), diff_txt, font=font_score)
    w_diff, h_diff = bbox_diff[2] - bbox_diff[0], bbox_diff[3] - bbox_diff[1]
    draw.text(((CARD_WIDTH - w_diff)//2, CARD_HEIGHT + SEPARATOR_WIDTH//2 - h_diff//2), diff_txt, font=font_score, fill=diff_color)

    # Titres
    title_2023 = str(row_2023['title'])
    title_2024 = str(row_2024['title'])
    
    # Titre 2023
    max_width = CARD_WIDTH - 2*margin
    lines_2023 = []
    words = title_2023.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        w = bbox[2] - bbox[0]
        if w > max_width and line:
            lines_2023.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines_2023.append(line)

    # Titre 2024
    lines_2024 = []
    words = title_2024.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        w = bbox[2] - bbox[0]
        if w > max_width and line:
            lines_2024.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines_2024.append(line)

    # Position des titres
    y_title_2023 = img_h + 4
    for l in lines_2023:
        bbox = draw.textbbox((0, 0), l, font=font_title)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((CARD_WIDTH-w)//2, y_title_2023), l, font=font_title, fill=text_color)
        y_title_2023 += h + 2

    y_title_2024 = CARD_HEIGHT + SEPARATOR_WIDTH + img_h + 4
    for l in lines_2024:
        bbox = draw.textbbox((0, 0), l, font=font_title)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((CARD_WIDTH-w)//2, y_title_2024), l, font=font_title, fill=text_color)
        y_title_2024 += h + 2

    return ImageClip(np.array(card))

def create_separator():
    return ColorClip(size=(SEPARATOR_WIDTH, HEIGHT), color=(0, 0, 0))

def get_card_position(index):
    if index == 0:
        return 0
    elif index == 1:
        return CARD_WIDTH + SEPARATOR_WIDTH
    else:
        return (CARD_WIDTH + SEPARATOR_WIDTH) * 2

def get_separator_position(index):
    return CARD_WIDTH + (index * CARD_SPACING)

# Création de toutes les cartes de comparaison
all_cards = [create_comparison_card(df_2023.iloc[i], df_2024.iloc[i], i) for i in range(len(df_2023))]

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
    "comparison_2023_2024_presentation.mp4",
    fps=60,
    codec='libx264',
    bitrate='4000k',
    preset='medium',
    threads=4,
    audio=False
) 