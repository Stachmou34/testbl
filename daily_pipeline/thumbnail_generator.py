"""
Générateur de miniatures PNG pour les vidéos anime.
Crée des thumbnails accrocheurs au format YouTube/TikTok.
"""

import os
import requests
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from colorthief import ColorThief


THUMB_WIDTH = 1280
THUMB_HEIGHT = 720


def _find_font(size=48):
    """Trouve et charge une police."""
    font_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts", "LuckiestGuy-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _download_image(url):
    """Télécharge une image."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None


def _get_dominant_color(url):
    """Extrait la couleur dominante."""
    try:
        resp = requests.get(url, timeout=10)
        ct = ColorThief(BytesIO(resp.content))
        return ct.get_color(quality=1)
    except Exception:
        return (30, 30, 60)


def _draw_text_with_shadow(draw, pos, text, font, fill="white", shadow_color="black"):
    """Dessine du texte avec ombre portée."""
    x, y = pos
    # Ombre
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            draw.text((x + dx, y + dy), text, font=font, fill=shadow_color)
    # Texte principal
    draw.text((x, y), text, font=font, fill=fill)


def generate_thumbnail(idea, output_dir):
    """Génère une miniature PNG accrocheuse."""
    os.makedirs(output_dir, exist_ok=True)

    is_comparison = idea.get("is_comparison", False)
    anime_list = idea.get("anime", [])
    title = idea.get("title_template", "Anime Video")

    # Créer l'image de fond
    thumb = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (20, 20, 30, 255))
    draw = ImageDraw.Draw(thumb)

    if is_comparison:
        # Miniature de comparaison : 2 images côte à côte
        current_anime = idea.get("current_anime", [])
        prev_anime = idea.get("previous_anime", [])

        # Image gauche (saison actuelle, top 1)
        if current_anime and current_anime[0].get("image"):
            left_img = _download_image(current_anime[0]["image"])
            if left_img:
                left_img = left_img.resize((THUMB_WIDTH // 2, THUMB_HEIGHT), Image.Resampling.LANCZOS)
                thumb.paste(left_img, (0, 0))

        # Image droite (saison précédente, top 1)
        if prev_anime and prev_anime[0].get("image"):
            right_img = _download_image(prev_anime[0]["image"])
            if right_img:
                right_img = right_img.resize((THUMB_WIDTH // 2, THUMB_HEIGHT), Image.Resampling.LANCZOS)
                thumb.paste(right_img, (THUMB_WIDTH // 2, 0))

        # Ligne de séparation
        draw = ImageDraw.Draw(thumb)
        draw.line(
            [(THUMB_WIDTH // 2, 0), (THUMB_WIDTH // 2, THUMB_HEIGHT)],
            fill=(255, 255, 255),
            width=6,
        )

        # Labels
        font_label = _find_font(36)
        current_label = idea.get("current_season", "Actuel")
        prev_label = idea.get("previous_season", "Précédent")
        _draw_text_with_shadow(draw, (30, THUMB_HEIGHT - 80), current_label, font_label, fill="#00ff66")
        _draw_text_with_shadow(draw, (THUMB_WIDTH // 2 + 30, THUMB_HEIGHT - 80), prev_label, font_label, fill="#ff6600")

    else:
        # Miniature classique : top 3 anime en arrière-plan
        top_anime = anime_list[-3:] if len(anime_list) >= 3 else anime_list  # Les 3 meilleurs (fin de liste car trié ascending)
        img_width = THUMB_WIDTH // max(len(top_anime), 1)

        for i, anime in enumerate(reversed(top_anime)):
            img_url = anime.get("image", "")
            if img_url:
                img = _download_image(img_url)
                if img:
                    # Redimensionner pour couvrir la zone
                    ratio = img.width / img.height
                    new_h = THUMB_HEIGHT
                    new_w = int(new_h * ratio)
                    if new_w < img_width:
                        new_w = img_width
                        new_h = int(new_w / ratio)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    # Centrer et cropper
                    left = (new_w - img_width) // 2
                    top = (new_h - THUMB_HEIGHT) // 2
                    img = img.crop((left, top, left + img_width, top + THUMB_HEIGHT))
                    thumb.paste(img, (i * img_width, 0))

        # Overlay sombre pour lisibilité
        overlay = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0, 0, 0, 140))
        thumb = Image.alpha_composite(thumb, overlay)
        draw = ImageDraw.Draw(thumb)

    # Titre principal
    font_title = _find_font(64)
    # Centrer le titre
    bbox = draw.textbbox((0, 0), title, font=font_title)
    text_w = bbox[2] - bbox[0]
    text_x = (THUMB_WIDTH - text_w) // 2
    text_y = THUMB_HEIGHT // 2 - 50
    _draw_text_with_shadow(draw, (text_x, text_y), title, font_title, fill="white")

    # Sous-titre avec le nombre d'anime
    if not is_comparison:
        count = len(anime_list)
        subtitle = f"{count} Anime Classés"
        font_sub = _find_font(36)
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        sub_w = bbox[2] - bbox[0]
        sub_x = (THUMB_WIDTH - sub_w) // 2
        _draw_text_with_shadow(
            draw, (sub_x, text_y + 80), subtitle, font_sub, fill=(241, 196, 15)
        )

    # Badge "TOP"
    badge_font = _find_font(28)
    badge_text = idea["config"]["name"].upper()
    draw.rounded_rectangle(
        [20, 20, 20 + len(badge_text) * 18, 65],
        radius=8,
        fill=(241, 196, 15),
    )
    draw.text((30, 25), badge_text, font=badge_font, fill="black")

    # Sauvegarder
    date_str = idea.get("date", "output")
    thumb_path = os.path.join(output_dir, f"thumbnail_{date_str}.png")
    thumb = thumb.convert("RGB")
    thumb.save(thumb_path, "PNG", quality=95)

    print(f"[Thumbnail] Miniature générée : {thumb_path}")
    return thumb_path
