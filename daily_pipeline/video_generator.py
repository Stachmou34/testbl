"""
Générateur vidéo universel.
Reproduit le style des vidéos existantes (cartes scrollantes en 3 colonnes)
et s'adapte au type de contenu (classement, comparaison, etc.).
"""

import os
import numpy as np
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from colorthief import ColorThief

try:
    from moviepy import CompositeVideoClip, ColorClip, ImageClip, TextClip
except ImportError:
    try:
        from moviepy.editor import CompositeVideoClip, ColorClip, ImageClip, TextClip
    except ImportError:
        print("[WARN] moviepy non trouvé, la génération vidéo ne fonctionnera pas.")

# Configuration vidéo
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

# Couleurs par défaut
DEFAULT_BG = (30, 30, 40)
GOLD = (241, 196, 15)
WHITE = (255, 255, 255)

# Cache couleurs
_color_cache = {}


def _find_font():
    """Trouve une police disponible sur le système."""
    font_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "LuckiestGuy-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return fp
    return None


def _get_moviepy_font():
    """Retourne un nom de police utilisable par TextClip."""
    for font_name in ["DejaVu-Sans-Bold", "Liberation-Sans-Bold", "LuckiestGuy-Regular"]:
        try:
            test = TextClip("test", fontsize=20, color="white", font=font_name)
            test.close()
            return font_name
        except Exception:
            continue
    return "DejaVu-Sans-Bold"


def _download_image(url, timeout=10):
    """Télécharge une image depuis une URL."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        print(f"  [WARN] Impossible de télécharger l'image: {e}")
        return None


def _get_dominant_color(image_url):
    """Extrait la couleur dominante d'une image URL."""
    if image_url in _color_cache:
        return _color_cache[image_url]
    try:
        resp = requests.get(image_url, timeout=10)
        color_thief = ColorThief(BytesIO(resp.content))
        color = color_thief.get_color(quality=1)
        darkened = tuple(int(c * 0.6) for c in color)
        _color_cache[image_url] = darkened
        return darkened
    except Exception:
        return DEFAULT_BG


def _create_frame(width, height, color=(0, 0, 0, 180)):
    """Crée un cadre semi-transparent avec coins arrondis."""
    frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=10, fill=color)
    return frame


def _format_value(value, fmt="score"):
    """Formate une valeur selon le type."""
    if fmt == "score":
        if isinstance(value, (int, float)):
            if value > 10:
                return f"{value / 10:.1f} / 10"
            return f"{value:.1f} / 10" if isinstance(value, float) else f"{value} / 10"
        return str(value)
    elif fmt == "popularity":
        if isinstance(value, (int, float)):
            if value >= 1_000_000:
                return f"{value / 1_000_000:.1f}M membres"
            elif value >= 1_000:
                return f"{value / 1_000:.0f}K membres"
            return f"{int(value)} membres"
        return str(value)
    elif fmt == "trending":
        return f"#{value}" if value else "N/A"
    return str(value)


def _create_ranking_card(anime, rank, total, idea):
    """Crée une carte de classement pour un anime."""
    font = _get_moviepy_font()
    image_url = anime.get("image", "")

    # Couleur de fond basée sur l'image
    bg_color = _get_dominant_color(image_url) if image_url else DEFAULT_BG
    card = ColorClip(size=(CARD_WIDTH, CARD_HEIGHT), color=bg_color)

    clips = [card]

    # Image de l'anime
    img_size = int(CARD_WIDTH * 0.85)
    img_y = int(CARD_HEIGHT * 0.02)

    img = _download_image(image_url) if image_url else None
    if img:
        # Redimensionner en gardant le ratio
        ratio = img.width / img.height
        if ratio > 1:
            new_w = img_size
            new_h = int(img_size / ratio)
        else:
            new_h = img_size
            new_w = int(img_size * ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        img_clip = ImageClip(np.array(img))
        img_clip = img_clip.set_position(("center", img_y))
        clips.append(img_clip)

        content_y = img_y + new_h + int(CARD_HEIGHT * 0.015)
    else:
        content_y = img_y + img_size + int(CARD_HEIGHT * 0.015)

    # Badge de rang
    rank_display = total - rank  # Inverser car trié ascending
    rank_badge_size = 70
    rank_badge = Image.new("RGBA", (rank_badge_size, rank_badge_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rank_badge)
    badge_color = GOLD if rank_display <= 3 else (80, 80, 80, 220)
    draw.ellipse([0, 0, rank_badge_size - 1, rank_badge_size - 1], fill=badge_color)
    # Numéro du rang
    pil_font = None
    font_path = _find_font()
    if font_path:
        try:
            pil_font = ImageFont.truetype(font_path, 32)
        except Exception:
            pil_font = ImageFont.load_default()
    else:
        pil_font = ImageFont.load_default()
    rank_text = str(rank_display)
    bbox = draw.textbbox((0, 0), rank_text, font=pil_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((rank_badge_size - tw) // 2, (rank_badge_size - th) // 2 - 2), rank_text, fill="white", font=pil_font)

    rank_clip = ImageClip(np.array(rank_badge))
    rank_clip = rank_clip.set_position((15, 15))
    clips.append(rank_clip)

    # Cadre du titre
    title_frame_h = int(CARD_HEIGHT * 0.08)
    title_frame = _create_frame(CARD_WIDTH - 40, title_frame_h)
    title_frame_clip = ImageClip(np.array(title_frame))
    title_frame_clip = title_frame_clip.set_position(("center", content_y))
    clips.append(title_frame_clip)

    # Texte du titre (tronquer si trop long)
    title = anime.get("title", "Unknown")
    if len(title) > 25:
        title = title[:23] + "..."
    title_clip = TextClip(
        title, fontsize=int(HEIGHT * 0.038), color="white", font=font
    )
    title_clip = title_clip.set_position(
        ("center", content_y + title_frame_h / 2 - title_clip.h / 2)
    )
    clips.append(title_clip)

    # Cadre des infos (score + studio + genres)
    info_y = content_y + title_frame_h + int(CARD_HEIGHT * 0.015)
    info_frame_h = int(CARD_HEIGHT * 0.18)
    info_frame = _create_frame(CARD_WIDTH - 40, info_frame_h)
    info_frame_clip = ImageClip(np.array(info_frame))
    info_frame_clip = info_frame_clip.set_position(("center", info_y))
    clips.append(info_frame_clip)

    # Valeur principale (score/trending/etc.)
    value_key = idea.get("value_key", "score")
    value_fmt = idea.get("value_format", "score")
    raw_value = anime.get(value_key, 0)
    value_text = _format_value(raw_value, value_fmt)

    value_clip = TextClip(
        value_text, fontsize=int(HEIGHT * 0.048), color="white", font=font
    )
    value_clip = value_clip.set_position(
        ("center", info_y + info_frame_h * 0.25 - value_clip.h / 2)
    )
    clips.append(value_clip)

    # Studio
    studio = anime.get("studio", "")
    if studio:
        studio_clip = TextClip(
            studio, fontsize=int(HEIGHT * 0.03), color="#cccccc", font=font
        )
        studio_clip = studio_clip.set_position(
            ("center", info_y + info_frame_h * 0.55 - studio_clip.h / 2)
        )
        clips.append(studio_clip)

    # Genres (max 2)
    genres = anime.get("genres", [])[:2]
    if genres:
        genre_text = " | ".join(genres)
        genre_clip = TextClip(
            genre_text, fontsize=int(HEIGHT * 0.025), color="#aaaaaa", font=font
        )
        genre_clip = genre_clip.set_position(
            ("center", info_y + info_frame_h * 0.80 - genre_clip.h / 2)
        )
        clips.append(genre_clip)

    return CompositeVideoClip(clips, size=(CARD_WIDTH, CARD_HEIGHT))


def _create_comparison_card(current_anime, prev_anime, rank, font_name):
    """Crée une carte de comparaison (saison vs saison)."""
    font = font_name
    bg_color = DEFAULT_BG
    image_url = current_anime.get("image", "") if current_anime else (prev_anime.get("image", "") if prev_anime else "")
    if image_url:
        bg_color = _get_dominant_color(image_url)

    card = ColorClip(size=(CARD_WIDTH, CARD_HEIGHT), color=bg_color)
    clips = [card]

    half_h = CARD_HEIGHT // 2 - 5

    # Moitié haute : anime saison actuelle
    if current_anime:
        clips.extend(_half_card(current_anime, 0, half_h, rank, font, "current"))

    # Séparateur central
    sep = Image.new("RGBA", (CARD_WIDTH - 20, 4), (255, 255, 255, 150))
    sep_clip = ImageClip(np.array(sep))
    sep_clip = sep_clip.set_position(("center", half_h))
    clips.append(sep_clip)

    # Moitié basse : anime saison précédente
    if prev_anime:
        clips.extend(_half_card(prev_anime, half_h + 8, half_h, rank, font, "previous"))

    return CompositeVideoClip(clips, size=(CARD_WIDTH, CARD_HEIGHT))


def _half_card(anime, y_offset, height, rank, font, label):
    """Crée une demi-carte pour les comparaisons."""
    clips = []
    image_url = anime.get("image", "")
    img = _download_image(image_url) if image_url else None

    img_size = int(CARD_WIDTH * 0.4)
    if img:
        ratio = img.width / img.height
        new_h = int(height * 0.75)
        new_w = int(new_h * ratio)
        if new_w > img_size:
            new_w = img_size
            new_h = int(new_w / ratio)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img_clip = ImageClip(np.array(img))
        img_clip = img_clip.set_position((15, y_offset + (height - new_h) // 2))
        clips.append(img_clip)

    # Titre
    title = anime.get("title", "Unknown")
    if len(title) > 20:
        title = title[:18] + "..."
    title_clip = TextClip(
        title, fontsize=int(HEIGHT * 0.032), color="white", font=font
    )
    text_x = img_size + 30
    title_clip = title_clip.set_position((text_x, y_offset + int(height * 0.2)))
    clips.append(title_clip)

    # Score
    score = anime.get("score", 0)
    score_text = f"{score / 10:.1f}" if score > 10 else f"{score:.1f}" if isinstance(score, float) else str(score)
    score_clip = TextClip(
        f"Score: {score_text}", fontsize=int(HEIGHT * 0.03), color=GOLD, font=font
    )
    score_clip = score_clip.set_position((text_x, y_offset + int(height * 0.5)))
    clips.append(score_clip)

    # Label saison
    season_label = "▲ ACTUEL" if label == "current" else "▼ PRÉCÉDENT"
    label_color = "#00cc66" if label == "current" else "#cc6600"
    label_clip = TextClip(
        season_label, fontsize=int(HEIGHT * 0.022), color=label_color, font=font
    )
    label_clip = label_clip.set_position((text_x, y_offset + int(height * 0.75)))
    clips.append(label_clip)

    return clips


def _create_separator():
    """Crée un séparateur vertical noir."""
    return ColorClip(size=(SEPARATOR_WIDTH, CARD_HEIGHT), color=(0, 0, 0))


def _get_card_position(index):
    """Position X d'une carte."""
    if index == 0:
        return 0
    elif index == 1:
        return CARD_WIDTH + SEPARATOR_WIDTH
    else:
        return (CARD_WIDTH + SEPARATOR_WIDTH) * 2


def _get_separator_position(index):
    """Position X d'un séparateur."""
    return CARD_WIDTH + (index * CARD_SPACING)


def generate_video(idea, output_dir):
    """Génère la vidéo MP4 à partir de l'idée."""
    os.makedirs(output_dir, exist_ok=True)

    is_comparison = idea.get("is_comparison", False)
    font = _get_moviepy_font()

    print("[Video] Création des cartes...")

    all_cards = []
    if is_comparison:
        current_anime = idea.get("current_anime", [])
        previous_anime = idea.get("previous_anime", [])
        max_len = max(len(current_anime), len(previous_anime))
        for i in range(max_len):
            cur = current_anime[i] if i < len(current_anime) else None
            prev = previous_anime[i] if i < len(previous_anime) else None
            print(f"  Carte {i + 1}/{max_len}...")
            card = _create_comparison_card(cur, prev, i, font)
            all_cards.append(card)
    else:
        anime_list = idea.get("anime", [])
        total = len(anime_list)
        for i, anime in enumerate(anime_list):
            print(f"  Carte {i + 1}/{total}: {anime.get('title', 'Unknown')}")
            card = _create_ranking_card(anime, i, total, idea)
            all_cards.append(card)

    if not all_cards:
        print("[Video] Aucune carte à générer !")
        return None

    print(f"[Video] {len(all_cards)} cartes créées. Assemblage de l'animation...")

    # Animation identique au style existant
    clips = []

    # Phase 1 : Introduction avec les 3 premières cartes
    for i in range(min(3, len(all_cards))):
        card = all_cards[i]
        final_x = _get_card_position(i)

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
        intro_clip = intro_clip.set_duration(
            INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5
        )
        clips.append(intro_clip)

        if i < 2:
            separator = _create_separator()
            separator_x = _get_separator_position(i)

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

            sep_clip = separator.set_position(make_separator_position(i, separator_x))
            sep_clip = sep_clip.set_start(0)
            sep_clip = sep_clip.set_duration(
                INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5
            )
            clips.append(sep_clip)

    # Phase 2 : Défilement des cartes restantes
    for i in range(3, len(all_cards)):
        card = all_cards[i]
        start_time = INTRO_DURATION + PAUSE_DURATION + ((i - 3) * SCROLL_DURATION)
        duration = SCROLL_DURATION * 4

        def make_scroll_position():
            def get_position(t):
                start_x = WIDTH
                speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                x = start_x - (t * speed)
                return (x, 0)
            return get_position

        moving_clip = card.set_position(make_scroll_position())
        moving_clip = moving_clip.set_start(start_time)
        moving_clip = moving_clip.set_duration(duration)
        clips.append(moving_clip)

        separator = _create_separator()

        def make_separator_scroll():
            def get_position(t):
                start_x = WIDTH - SEPARATOR_WIDTH
                speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                x = start_x - (t * speed)
                return (x, 0)
            return get_position

        sep_clip = separator.set_position(make_separator_scroll())
        sep_clip = sep_clip.set_start(start_time)
        sep_clip = sep_clip.set_duration(duration)
        clips.append(sep_clip)

    # Durée totale
    total_duration = (
        INTRO_DURATION
        + PAUSE_DURATION
        + ((len(all_cards) - 3) * SCROLL_DURATION)
        + SCROLL_DURATION * 3
    )

    final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
    final_video = final_video.set_duration(total_duration)

    # Export
    date_str = idea.get("date", "output")
    video_path = os.path.join(output_dir, f"anime_video_{date_str}.mp4")

    print(f"[Video] Export vers {video_path}...")
    final_video.write_videofile(
        video_path,
        fps=FPS,
        codec="libx264",
        bitrate="4000k",
        preset="medium",
        threads=4,
        audio=False,
    )

    print(f"[Video] Vidéo générée : {video_path}")
    return video_path
