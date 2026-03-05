from moviepy.editor import *
import pandas as pd
import os
import numpy as np
from moviepy.config import change_settings
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from colorthief import ColorThief
import random

# Configuration de MoviePy pour utiliser ImageMagick
try:
    change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})
except:
    print("ImageMagick non trouvé, utilisation de la configuration par défaut")

# Vérification du dossier fonts
if not os.path.exists("fonts"):
    os.makedirs("fonts")
    print("Dossier fonts créé")

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
PURPLE = (142, 68, 173)

def create_award_card(row):
    from PIL import ImageFont

    # Paramètres
    is_winner = row['is_winner']
    if is_winner:
        # Fond dégradé doré pour le gagnant
        bg_color_top = (255, 215, 0)
        bg_color_bottom = (255, 239, 170)
        card_bg = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), bg_color_top)
        for y in range(CARD_HEIGHT):
            ratio = y / CARD_HEIGHT
            r = int(bg_color_top[0] * (1 - ratio) + bg_color_bottom[0] * ratio)
            g = int(bg_color_top[1] * (1 - ratio) + bg_color_bottom[1] * ratio)
            b = int(bg_color_top[2] * (1 - ratio) + bg_color_bottom[2] * ratio)
            for x in range(CARD_WIDTH):
                card_bg.putpixel((x, y), (r, g, b))
        card = card_bg
    else:
        bg_color = (30, 30, 40)
        card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), bg_color)
    draw = ImageDraw.Draw(card)

    # Halo doré pour le gagnant
    if is_winner:
        halo = Image.new("RGBA", (CARD_WIDTH+40, CARD_HEIGHT+40), (0,0,0,0))
        halo_draw = ImageDraw.Draw(halo)
        halo_draw.ellipse([10, 10, CARD_WIDTH+30, CARD_HEIGHT+30], fill=(255, 215, 0, 60))
        card_with_halo = Image.new("RGBA", (CARD_WIDTH+40, CARD_HEIGHT+40), (0,0,0,0))
        card_with_halo.paste(halo, (0,0), halo)
        card_with_halo.paste(card, (20,20))
        card = card_with_halo.crop((20,20,CARD_WIDTH+20,CARD_HEIGHT+20)).convert("RGB")
        draw = ImageDraw.Draw(card)

    band_color = (0, 0, 0)
    text_color = (255, 255, 255)
    award_color = GOLD
    score_color = (255, 215, 0)
    margin = 32
    band_h = int(CARD_HEIGHT * 0.32)
    img_h = CARD_HEIGHT - band_h

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

    # Polices
    try:
        font_path = "fonts/LuckiestGuy-Regular.ttf"
        if not os.path.exists(font_path):
            print("Police Luckiest Guy non trouvée, utilisation de la police par défaut")
            font_award = font_title = font_category = font_score = font_genres = ImageFont.load_default()
        else:
            font_award = ImageFont.truetype(font_path, 48 if is_winner else 36)
            font_title = ImageFont.truetype(font_path, 48)
            font_category = ImageFont.truetype(font_path, 40)
            font_score = ImageFont.truetype(font_path, 32)
            font_genres = ImageFont.truetype(font_path, 28)
    except Exception as e:
        print(f"Erreur lors du chargement des polices : {e}")
        font_award = font_title = font_category = font_score = font_genres = ImageFont.load_default()

    # Catégorie (centré en haut du bandeau)
    category_txt = str(row['category']).upper()
    bbox = draw.textbbox((0, 0), category_txt, font=font_category)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y_category = img_h + 10
    draw.text(((CARD_WIDTH-w)//2, y_category), category_txt, font=font_category, fill=text_color)

    # Trait doré de séparation
    y_sep = y_category + h + 10
    draw.line([(margin, y_sep), (CARD_WIDTH-margin, y_sep)], fill=GOLD, width=3)

    # Score MAL (si disponible)
    if pd.notna(row['score']) and row['score'] != 'N/A':
        score_txt = f"MAL Score: {row['score']}"
        bbox_score = draw.textbbox((0, 0), score_txt, font=font_score)
        w_score, h_score = bbox_score[2] - bbox_score[0], bbox_score[3] - bbox_score[1]
        y_score = y_sep + 10
        draw.text(((CARD_WIDTH-w_score)//2, y_score), score_txt, font=font_score, fill=score_color)
        y_next = y_score + h_score + 10
    else:
        y_next = y_sep + 10

    # Badge "WINNER 2025" (plus grand et plus visible)
    if is_winner:
        award_txt = "WINNER 2025"
        bbox_award = draw.textbbox((0, 0), award_txt, font=font_award)
        w_award, h_award = bbox_award[2] - bbox_award[0], bbox_award[3] - bbox_award[1]
        y_award = y_next
        # Rectangle doré derrière le texte
        draw.rectangle([
            ((CARD_WIDTH-w_award)//2 - 16, y_award - 8),
            ((CARD_WIDTH+w_award)//2 + 16, y_award + h_award + 8)
        ], fill=(255, 215, 0, 180))
        draw.text(((CARD_WIDTH-w_award)//2, y_award), award_txt, font=font_award, fill=(80, 40, 0))
        y_next = y_award + h_award + 18

    # Genres (max 2 lignes)
    if pd.notna(row['genres']):
        genres = str(row['genres'])
        genres_list = [g.strip() for g in genres.split(',')][:3]  # Limite à 3 genres
        genres_str = ', '.join(genres_list)
        bbox_genres = draw.textbbox((0, 0), genres_str, font=font_genres)
        w_genres, h_genres = bbox_genres[2] - bbox_genres[0], bbox_genres[3] - bbox_genres[1]
        y_genres = y_next
        draw.text(((CARD_WIDTH-w_genres)//2, y_genres), genres_str, font=font_genres, fill=text_color)
        y_title = y_genres + h_genres + 10
    else:
        y_title = y_next

    # Titre (centré, retour à la ligne si besoin)
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

    # Position du titre
    for idx, l in enumerate(lines):
        bbox = draw.textbbox((0, 0), l, font=font_title)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((CARD_WIDTH-w)//2, y_title), l, font=font_title, fill=text_color)
        y_title += h + 2

    return ImageClip(np.array(card))

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

def create_category_background(category_name):
    # Création d'un fond avec le titre de la catégorie
    bg = Image.new("RGB", (WIDTH, HEIGHT), (30, 30, 40))
    draw = ImageDraw.Draw(bg)
    
    try:
        font = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 72)
    except:
        font = ImageFont.load_default()
    
    # Centrer le texte
    bbox = draw.textbbox((0, 0), category_name, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (WIDTH - w) // 2
    y = (HEIGHT - h) // 2
    
    # Ajouter un effet de brillance
    draw.text((x+2, y+2), category_name, font=font, fill=(255, 215, 0, 180))
    draw.text((x, y), category_name, font=font, fill=(255, 255, 255))
    
    return ImageClip(np.array(bg))

# Création des clips avec animation
clips = []

# Lecture des données CSV
try:
    df = pd.read_csv('crunchyroll_awards_2025_updated.csv')
    print(f"Données chargées : {len(df)} entrées")
except Exception as e:
    print(f"Erreur lors de la lecture du CSV : {e}")
    exit(1)

# Grouper les animes par catégorie
categories = df['category'].unique()
print(f"Catégories trouvées : {len(categories)}")

# Placer 'Anime of the Year' en dernier pour le watchtime
categories = [cat for cat in categories if cat != 'Anime of the Year'] + [cat for cat in categories if cat == 'Anime of the Year']

# Pour chaque catégorie
category_start_time = 0.0
for category_idx, category in enumerate(categories):
    print(f"Traitement de la catégorie : {category}")
    
    # Filtrer les animes de cette catégorie
    category_df = df[df['category'] == category]
    
    # Séparer les gagnants des nominés
    winners_df = category_df[category_df['is_winner'] == True]
    nominees_df = category_df[category_df['is_winner'] == False]
    
    # Créer les cartes pour tous les participants (nominés + gagnant)
    all_cards = []
    # Ajouter d'abord les nominés
    for _, row in nominees_df.iterrows():
        all_cards.append((create_award_card(row), False))
    
    # Ajouter le gagnant à une position aléatoire
    if not winners_df.empty:
        winner_row = winners_df.iloc[0].copy()
        winner_row['is_winner'] = False  # Désactiver temporairement le badge gagnant
        winner_card = (create_award_card(winner_row), True)
        
        # Choisir une position aléatoire pour le gagnant
        random_position = random.randint(0, len(all_cards))
        all_cards.insert(random_position, winner_card)
    
    # Ajouter le fond de la catégorie
    category_bg = create_category_background(category)
    category_bg = category_bg.set_start(category_start_time)
    category_bg = category_bg.set_duration(INTRO_DURATION + 1.0)  # 2 secondes au total
    clips.append(category_bg)
    
    # Décaler le début des participants après le fond de catégorie
    participants_start_time = category_start_time + INTRO_DURATION + 1.0  # 2 secondes après le début de la catégorie
    
    # Animation d'introduction pour les 3 premiers participants
    for i in range(min(3, len(all_cards))):
        card, is_winner = all_cards[i]
        final_x = get_card_position(i)
        
        def make_position(index, final_pos):
            def get_position(t):
                intro_start = index * INITIAL_DELAY
                relative_intro_t = t - intro_start
                
                if relative_intro_t < 0:
                    return (final_pos, -HEIGHT)
                elif t < (INTRO_DURATION + 1.0):
                    start_y = -HEIGHT
                    end_y = 0
                    progress = relative_intro_t / ((INTRO_DURATION + 1.0) - (index * INITIAL_DELAY))
                    progress = min(1, progress)
                    eased_progress = 1 - (1 - progress) ** 2
                    return (final_pos, start_y + (end_y - start_y) * eased_progress)
                elif t < (INTRO_DURATION + 1.0 + PAUSE_DURATION):
                    return (final_pos, 0)
                else:
                    scroll_time = t - (INTRO_DURATION + 1.0 + PAUSE_DURATION)
                    speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                    x = final_pos - (scroll_time * speed)
                    return (x, 0)
            return get_position
        
        # Ajout de la carte
        intro_clip = card.set_position(make_position(i, final_x))
        intro_clip = intro_clip.set_start(participants_start_time)
        intro_clip = intro_clip.set_duration(INTRO_DURATION + 1.0 + PAUSE_DURATION + SCROLL_DURATION * 3.5)
        clips.append(intro_clip)
        
        # Ajout du séparateur après la carte (sauf pour la dernière)
        if i < 2:
            separator = create_separator()
            separator_x = get_separator_position(i)
            
            def make_separator_position(index, sep_pos):
                def get_position(t):
                    if t < INTRO_DURATION + 1.0 + PAUSE_DURATION:
                        return (sep_pos, 0)
                    else:
                        scroll_time = t - (INTRO_DURATION + 1.0 + PAUSE_DURATION)
                        speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                        x = sep_pos - (scroll_time * speed)
                        return (x, 0)
                return get_position
            
            separator_clip = separator.set_position(make_separator_position(i, separator_x))
            separator_clip = separator_clip.set_start(participants_start_time)
            separator_clip = separator_clip.set_duration(INTRO_DURATION + 1.0 + PAUSE_DURATION + SCROLL_DURATION * 3.5)
            clips.append(separator_clip)
    
    # Animation de défilement pour les participants restants
    last_participant_end = participants_start_time
    for i in range(3, len(all_cards)):
        card, is_winner = all_cards[i]
        start_time = participants_start_time + INTRO_DURATION + 1.0 + PAUSE_DURATION + ((i - 3) * SCROLL_DURATION)
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
        
        # Garder la fin du dernier participant
        last_participant_end = start_time + duration
    
    # Animation finale pour mettre en évidence le gagnant
    if not winners_df.empty:
        winner_row = winners_df.iloc[0].copy()
        winner_row['is_winner'] = True
        winner_card = create_award_card(winner_row)
        # Le gagnant doit apparaître juste après la fin du dernier participant
        winner_start_time = last_participant_end
        def make_winner_position():
            def get_position(t):
                return (WIDTH//2 - CARD_WIDTH//2, HEIGHT//2 - CARD_HEIGHT//2)
            return get_position
        winner_duration = 2.0  # 2 secondes pour le gagnant
        winner_clip = winner_card.set_position(make_winner_position())
        winner_clip = winner_clip.set_start(winner_start_time)
        winner_clip = winner_clip.set_duration(winner_duration)
        clips.append(winner_clip)
    
    # Calculer le temps de début de la prochaine catégorie
    if not winners_df.empty:
        category_start_time = winner_start_time + winner_duration
    else:
        category_start_time = last_participant_end

# Calcul de la durée totale avec la nouvelle logique
final_end = category_start_time
print(f"Durée totale de la vidéo: {final_end}")

# Création de la vidéo finale
final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
final_video = final_video.set_duration(final_end)

# Export de la vidéo
final_video.write_videofile(
    "crunchyroll_awards_2025.mp4",
    fps=60,
    codec='libx264',
    bitrate='2000k',
    preset='ultrafast',
    threads=4,
    audio=False,
    logger=None
) 