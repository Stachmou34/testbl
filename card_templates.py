"""
Templates de cartes pour chaque type de video.
Chaque fonction create_card_* retourne un ImageClip/CompositeVideoClip.
"""
import numpy as np
import pandas as pd
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip, ColorClip, TextClip
from colorthief import ColorThief

# -- Couleurs partagees --
BLUE_LIGHT = (41, 128, 185)
BLUE_DARK = (31, 97, 141)
GOLD = (241, 196, 15)
FIRE_RED = (255, 69, 0)

# -- Cache couleurs --
_color_cache = {}


def _get_dominant_color_url(image_url):
    if image_url in _color_cache:
        return _color_cache[image_url]
    try:
        response = requests.get(image_url, timeout=10)
        img_data = BytesIO(response.content)
        color_thief = ColorThief(img_data)
        dominant_color = color_thief.get_color(quality=1)
        darkened = tuple(int(c * 0.7) for c in dominant_color)
        _color_cache[image_url] = darkened
        return darkened
    except Exception as e:
        print(f"Erreur couleur dominante: {e}")
        return BLUE_LIGHT


def _get_dominant_color_file(image_path):
    if image_path in _color_cache:
        return _color_cache[image_path]
    try:
        color_thief = ColorThief(image_path)
        dominant_color = color_thief.get_color(quality=1)
        darkened = tuple(int(c * 0.7) for c in dominant_color)
        _color_cache[image_path] = darkened
        return darkened
    except Exception as e:
        print(f"Erreur couleur dominante: {e}")
        return BLUE_LIGHT


def _create_frame(width, height, color=(0, 0, 0, 180)):
    frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=10, fill=color)
    return frame


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


# =============================================================================
# BLUE LOCK
# =============================================================================

def create_card_blue_lock(row, card_width, card_height):
    HEIGHT = card_height
    team_color = hex_to_rgb(row['team_color'])
    card = ColorClip(size=(card_width, card_height), color=team_color)

    player_size = int(card_width * 0.92)
    player_y_pos = int(card_height * 0.045)

    try:
        response = requests.get(row['image'], timeout=10)
        img = Image.open(BytesIO(response.content)).convert('RGBA')
        img = img.resize((player_size, player_size), Image.Resampling.LANCZOS)
        img_clip = ImageClip(np.array(img))
        img_clip = img_clip.set_position(('center', player_y_pos))
    except Exception as e:
        print(f"Erreur image joueur: {e}")
        img_clip = None

    frame_margin = int(card_height * 0.018)

    # Name frame
    name_frame_height = int(card_height * 0.07)
    name_frame_y = player_y_pos + player_size + frame_margin
    name_frame = _create_frame(card_width - 40, name_frame_height)
    name_frame_clip = ImageClip(np.array(name_frame)).set_position(('center', name_frame_y))

    name_text = TextClip(row['name'], fontsize=int(HEIGHT * 0.042), color='white', font='Roboto-Bold')
    name_text = name_text.set_position(('center', name_frame_y + name_frame_height / 2 - name_text.h / 2))

    # Value + status frame
    value_status_frame_height = int(card_height * 0.18)
    value_status_frame_y = name_frame_y + name_frame_height + frame_margin
    value_status_frame = _create_frame(card_width - 40, value_status_frame_height)
    value_status_frame_clip = ImageClip(np.array(value_status_frame)).set_position(('center', value_status_frame_y))

    # Club logo
    logo_clip = None
    try:
        response = requests.get(row['club_image'], timeout=10)
        club_logo = Image.open(BytesIO(response.content)).convert('RGBA')
        logo_width = int(card_width * 0.32)
        logo_height = int(value_status_frame_height * 0.8)
        club_logo = club_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        logo_data = np.array(club_logo)
        logo_data[..., 3] = (logo_data[..., 3] * 0.22).astype(np.uint8)
        logo_clip = ImageClip(np.array(Image.fromarray(logo_data)))
        logo_x = (card_width - logo_width) // 2
        logo_y = value_status_frame_y + (value_status_frame_height - logo_height) // 2
        logo_clip = logo_clip.set_position((logo_x, logo_y))
    except Exception:
        pass

    # Value text
    value_text = f"{int(row['value']):,} \u00a5".replace(",", " ")
    value_text_clip = TextClip(value_text, fontsize=int(HEIGHT * 0.055), color='white', font='Roboto-Bold')
    value_text_clip = value_text_clip.set_position(('center', value_status_frame_y + value_status_frame_height * 0.32 - value_text_clip.h / 2))

    # Status
    status = str(row.get('status', '')).strip() if pd.notna(row.get('status')) else ''
    status_text_clip = None
    if status and status.lower() not in ['nan', '']:
        status_color = 'red' if status.lower() == 'eliminated' else ('green' if status.lower() == 'qualified' else 'white')
        status_text_clip = TextClip(status, fontsize=int(HEIGHT * 0.042), color=status_color, font='Roboto-Bold')
        status_text_clip = status_text_clip.set_position(('center', value_status_frame_y + value_status_frame_height * 0.72 - status_text_clip.h / 2))

    # Team frame
    team_frame_height = int(card_height * 0.07)
    team_frame_y = value_status_frame_y + value_status_frame_height + frame_margin
    team_frame = _create_frame(card_width - 40, team_frame_height)
    team_frame_clip = ImageClip(np.array(team_frame)).set_position(('center', team_frame_y))

    team_text = TextClip(row['team'], fontsize=int(HEIGHT * 0.037), color='white', font='Roboto-Bold')
    team_text = team_text.set_position(('center', team_frame_y + team_frame_height / 2 - team_text.h / 2))

    clips = [card]
    if img_clip:
        clips.append(img_clip)
    clips.extend([name_frame_clip, name_text, value_status_frame_clip])
    if logo_clip:
        clips.append(logo_clip)
    clips.append(value_text_clip)
    if status_text_clip:
        clips.append(status_text_clip)
    clips.extend([team_frame_clip, team_text])

    return CompositeVideoClip(clips, size=(card_width, card_height))


# =============================================================================
# FIRE FORCE
# =============================================================================

def _create_fire_effect(width, height):
    fire = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(fire)
    for i in range(5):
        points = [
            (width * 0.2 + i * width * 0.15, height * 0.8),
            (width * 0.3 + i * width * 0.15, height * 0.6),
            (width * 0.4 + i * width * 0.15, height * 0.8)
        ]
        draw.polygon(points, fill=(255, 69, 0, 100))
    return ImageClip(np.array(fire))


def create_card_fire_force(row, card_width, card_height):
    HEIGHT = card_height
    character_color = _get_dominant_color_file(row['Image']) if row['Image'] != 'N/A' else BLUE_LIGHT
    card = ColorClip(size=(card_width, card_height), color=character_color)

    character_size = int(card_width * 0.92)
    character_y_pos = int(card_height * 0.045)

    try:
        img = Image.open(row['Image']).convert('RGBA')
        img = img.resize((character_size, character_size), Image.Resampling.LANCZOS)
        img_clip = ImageClip(np.array(img)).set_position(('center', character_y_pos))
    except Exception as e:
        print(f"Erreur image personnage: {e}")
        img_clip = None

    frame_margin = int(card_height * 0.018)

    # Name
    name_frame_height = int(card_height * 0.07)
    name_frame_y = character_y_pos + character_size + frame_margin
    name_frame_clip = ImageClip(np.array(_create_frame(card_width - 40, name_frame_height))).set_position(('center', name_frame_y))
    name_text = TextClip(row['Name'], fontsize=int(HEIGHT * 0.042), color='white', font='Roboto-Bold')
    name_text = name_text.set_position(('center', name_frame_y + name_frame_height / 2 - name_text.h / 2))

    # Info frame
    info_frame_height = int(card_height * 0.24)
    info_frame_y = name_frame_y + name_frame_height + frame_margin
    info_frame_clip = ImageClip(np.array(_create_frame(card_width - 40, info_frame_height))).set_position(('center', info_frame_y))

    fire_effect = _create_fire_effect(card_width - 40, info_frame_height)
    fire_effect = fire_effect.set_opacity(0.3).set_position((int((card_width - (card_width - 40)) / 2), info_frame_y))

    company_text = TextClip(row['Company'], fontsize=int(HEIGHT * 0.037), color='white', font='Roboto-Bold')
    company_text = company_text.set_position(('center', info_frame_y + info_frame_height * 0.20 - company_text.h / 2))

    position_text = TextClip(row['Position'], fontsize=int(HEIGHT * 0.037), color='white', font='Roboto-Bold')
    position_text = position_text.set_position(('center', info_frame_y + info_frame_height * 0.50 - position_text.h / 2))

    if str(row['Age']).strip().lower() == 'unknown':
        age_number = TextClip('Unknown', fontsize=int(HEIGHT * 0.045), color='white', font='Roboto-Bold')
        age_number = age_number.set_position(('center', info_frame_y + info_frame_height * 0.80 - age_number.h / 2))
        age_label = None
    else:
        age_number = TextClip(str(row['Age']), fontsize=int(HEIGHT * 0.065), color='white', font='Roboto-Bold')
        age_label = TextClip('Years\nold', fontsize=int(HEIGHT * 0.037), color='white', font='Roboto-Bold', method='caption', align='West')
        age_x = int(card_width / 2 - 90)
        label_x = int(card_width / 2 + 50)
        age_y = int(info_frame_y + info_frame_height * 0.80 - age_number.h / 2)
        label_y = int(info_frame_y + info_frame_height * 0.80 - age_label.h / 2)
        age_number = age_number.set_position((age_x, age_y))
        age_label = age_label.set_position((label_x, label_y))

    clips = [card]
    if img_clip:
        clips.append(img_clip)
    clips.extend([name_frame_clip, name_text, info_frame_clip, fire_effect, company_text, position_text, age_number])
    if age_label:
        clips.append(age_label)

    return CompositeVideoClip(clips, size=(card_width, card_height))


# =============================================================================
# ONE PIECE (wanted poster)
# =============================================================================

def _analyze_white_frame(image_path):
    from scipy import ndimage
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    img_array = np.array(img)
    white_mask = np.all(img_array > 245, axis=2)
    labeled_array, num_features = ndimage.label(white_mask)

    frame_info = []
    for feature in range(1, num_features + 1):
        feature_mask = labeled_array == feature
        y_coords, x_coords = np.where(feature_mask)
        if len(y_coords) > 0:
            top = np.min(y_coords)
            bottom = np.max(y_coords)
            left = np.min(x_coords)
            right = np.max(x_coords)
            fw = right - left
            fh = bottom - top
            if (fw > width * 0.3 and fw < width * 0.8 and
                    fh > height * 0.3 and fh < height * 0.6 and
                    top > height * 0.1 and bottom < height * 0.9):
                margin = 2
                frame_info.append({
                    'top': top - margin, 'bottom': bottom + margin,
                    'left': left - margin, 'right': right + margin,
                    'width': fw + 2 * margin, 'height': fh + 2 * margin,
                    'area': fw * fh
                })

    frame_info.sort(key=lambda x: x['area'], reverse=True)
    return frame_info[0] if frame_info else None


def create_card_wanted_poster(row, card_width, card_height, wanted_poster_path='img/avis de recherhche 2.jpg'):
    card = ColorClip(size=(card_width, card_height), color=(255, 255, 255))

    try:
        wanted_img = Image.open(wanted_poster_path).convert('RGB')
        frame = _analyze_white_frame(wanted_poster_path)
        wanted_img_resized = wanted_img.resize((card_width, card_height), Image.Resampling.LANCZOS)

        if not frame:
            print("Impossible de detecter le cadre blanc.")
            return None

        width_ratio = card_width / wanted_img.width
        height_ratio = card_height / wanted_img.height
        white_frame_width = int(frame['width'] * width_ratio)
        white_frame_height = int(frame['height'] * height_ratio)
        frame_left = int(frame['left'] * width_ratio)
        frame_top = int(frame['top'] * height_ratio)

        image_path = str(row['image'])
        if image_path.startswith('http'):
            response = requests.get(image_path, timeout=10)
            img = Image.open(BytesIO(response.content)).convert('RGB')
        else:
            img = Image.open(image_path).convert('RGB')

        img_ratio = img.width / img.height
        frame_ratio = white_frame_width / white_frame_height
        if img_ratio > frame_ratio:
            new_height = white_frame_height
            new_width = int(new_height * img_ratio * 1.1)
        else:
            new_width = white_frame_width
            new_height = int(new_width / img_ratio * 1.1)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - white_frame_width) // 2
        top = (new_height - white_frame_height) // 2
        img = img.crop((left, top, left + white_frame_width, top + white_frame_height))

        result = wanted_img_resized.copy()
        result.paste(img, (frame_left, frame_top))

        draw = ImageDraw.Draw(result)
        draw.rectangle([(frame_left, frame_top), (frame_left + white_frame_width, frame_top + white_frame_height)],
                       outline=(0, 0, 0), width=2)

        try:
            name_font = ImageFont.truetype("arial.ttf", 42)
        except Exception:
            name_font = ImageFont.load_default()

        text_color = (70, 35, 10)
        name = row['name'].upper()
        name_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (result.width - name_width) // 2
        name_y = frame_top + white_frame_height + 80
        draw.text((name_x, name_y), name, fill=text_color, font=name_font)

        try:
            font = ImageFont.truetype("arial.ttf", 38)
        except Exception:
            font = ImageFont.load_default()

        bounty = f"{row['value']:,}"
        bounty_bbox = draw.textbbox((0, 0), bounty, font=font)
        bounty_width = bounty_bbox[2] - bounty_bbox[0]
        bounty_x = (result.width - bounty_width) // 2
        bounty_y = name_y + 80
        draw.text((bounty_x, bounty_y), bounty, fill=text_color, font=font)

        return ImageClip(np.array(result))

    except Exception as e:
        print(f"Erreur carte wanted poster: {e}")
        return None


# =============================================================================
# ANIME SEASON (Spring 2025, Summer 2025, etc.)
# =============================================================================

def create_card_anime_season(row, card_width, card_height):
    bg_color = (30, 30, 40)
    text_color = (255, 255, 255)
    genre_color = (200, 200, 200)
    margin = 32
    band_h = int(card_height * 0.32)
    img_h = card_height - band_h

    card = Image.new("RGB", (card_width, card_height), bg_color)
    draw = ImageDraw.Draw(card)

    # Anime image
    try:
        response = requests.get(row['image'], timeout=10)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((card_width, img_h), Image.LANCZOS)
        card.paste(img, (0, 0))
    except Exception as e:
        print(f"Erreur image anime: {e}")

    # Black band
    band = Image.new("RGB", (card_width, band_h), (0, 0, 0))
    card.paste(band, (0, img_h))

    # Fonts
    try:
        font_genre = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 30)
        font_title = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 48)
        font_type = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 30)
        font_date = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 40)
        font_score = ImageFont.truetype("fonts/LuckiestGuy-Regular.ttf", 60)
    except Exception:
        font_genre = font_title = font_type = font_date = font_score = ImageFont.load_default()

    # Score
    score_txt = f"Score: {row['num_list_users']:.2f}" if pd.notna(row.get('num_list_users')) and row.get('num_list_users', 0) > 0 else "Score: N/A"
    bbox_score = draw.textbbox((0, 0), score_txt, font=font_score)
    w_score = bbox_score[2] - bbox_score[0]
    draw.text((card_width - w_score - margin, margin), score_txt, font=font_score, fill=GOLD)

    # Date
    date_txt = f"Release on {row['start_date']}" if pd.notna(row.get('start_date')) else "Release date TBA"
    bbox = draw.textbbox((0, 0), date_txt, font=font_date)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y_date = img_h + 10
    draw.text(((card_width - w) // 2, y_date), date_txt, font=font_date, fill=text_color)

    # Separator line
    y_sep = y_date + h + 10
    draw.line([(margin, y_sep), (card_width - margin, y_sep)], fill=(255, 255, 255), width=3)

    # Genres
    genres = str(row.get('genres', '')) if pd.notna(row.get('genres')) else ""
    genres_list = [g.strip() for g in genres.split(',')][:3]
    draw.text((margin, y_sep + 10), ', '.join(genres_list), font=font_genre, fill=genre_color)

    # Type
    type_txt = str(row.get('media_type', '')).upper()
    bbox_type = draw.textbbox((0, 0), type_txt, font=font_type)
    w_type, h_type = bbox_type[2] - bbox_type[0], bbox_type[3] - bbox_type[1]
    y_type = card_height - h_type - 18
    draw.text(((card_width - w_type) // 2, y_type), type_txt, font=font_type, fill=text_color)

    # Title (word-wrap)
    title = str(row.get('title', ''))
    max_width = card_width - 2 * margin
    lines = []
    line = ""
    for word in title.split():
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if bbox[2] - bbox[0] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines.append(line)

    h_lines = [draw.textbbox((0, 0), l, font=font_title)[3] - draw.textbbox((0, 0), l, font=font_title)[1] for l in lines]
    total_title_height = sum(h_lines) + (len(h_lines) - 1) * 2
    y_genres = y_sep + 10
    y_title_zone_top = y_genres + font_genre.size + 10
    y_title_zone_bottom = y_type - 10
    available_height = y_title_zone_bottom - y_title_zone_top
    y_title = y_title_zone_top + (available_height - total_title_height) // 2
    for idx, l in enumerate(lines):
        bbox = draw.textbbox((0, 0), l, font=font_title)
        w = bbox[2] - bbox[0]
        draw.text(((card_width - w) // 2, y_title), l, font=font_title, fill=text_color)
        y_title += h_lines[idx] + 2

    return ImageClip(np.array(card))
