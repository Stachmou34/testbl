"""
Générateur de métadonnées pour les vidéos (titre, description, hashtags).
Optimisé pour YouTube et TikTok.
"""

from datetime import datetime


HASHTAGS_BASE = [
    "#anime", "#animefan", "#otaku", "#manga",
    "#animecommunity", "#animerecommendation",
]

GENRE_HASHTAGS = {
    "Action": ["#actionanime", "#shounen", "#fight"],
    "Romance": ["#romanceanime", "#animelove", "#shoujo"],
    "Fantasy": ["#fantasyanime", "#isekai", "#magic"],
    "Sci-Fi": ["#scifianime", "#mecha", "#cyberpunk"],
    "Horror": ["#horroranime", "#darkanime", "#thriller"],
    "Comedy": ["#comedyanime", "#funny", "#animefunny"],
    "Drama": ["#dramaanime", "#emotional", "#feels"],
    "Sports": ["#sportsanime", "#animesports"],
}

TYPE_HASHTAGS = {
    "top_trending": ["#trending", "#trendinganime", "#popular", "#viral"],
    "seasonal_ranking": ["#animeseason", "#newanime", "#seasonal"],
    "genre_top": ["#bestanime", "#topanime", "#animeranking"],
    "season_comparison": ["#animecomparison", "#versus", "#animevs"],
    "recently_completed": ["#animereview", "#completed", "#animebilan"],
    "top_scores": ["#bestrated", "#toprated", "#animescore"],
}


def generate_metadata(idea):
    """Génère titre, description et hashtags optimisés."""
    video_type = idea.get("type", "")
    title_template = idea.get("title_template", "Anime Video")
    anime_list = idea.get("anime", [])
    date = idea.get("date", datetime.now().strftime("%Y-%m-%d"))
    is_comparison = idea.get("is_comparison", False)

    # Titre YouTube
    title = _generate_title(idea)

    # Description
    description = _generate_description(idea)

    # Hashtags
    hashtags = _generate_hashtags(idea)

    metadata = {
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "hashtags_str": " ".join(hashtags),
        "date": date,
        "video_type": video_type,
        "anime_count": len(anime_list),
    }

    return metadata


def _generate_title(idea):
    """Génère un titre accrocheur pour YouTube."""
    video_type = idea.get("type", "")
    title_template = idea.get("title_template", "")
    anime_list = idea.get("anime", [])

    if video_type == "top_trending":
        count = len(anime_list)
        top_anime = anime_list[-1]["title"] if anime_list else ""
        return f"Top {count} Anime Trending du Moment | {top_anime} est #1 !"

    elif video_type == "seasonal_ranking":
        season_info = title_template
        top_anime = anime_list[-1]["title"] if anime_list else ""
        return f"{season_info} - Classement Complet | Qui est #1 ?"

    elif video_type == "genre_top":
        genre = idea.get("genre", "")
        count = len(anime_list)
        return f"Top {count} Meilleurs Anime {genre} de Tous les Temps"

    elif video_type == "season_comparison":
        return f"Anime {idea.get('current_season', '')} vs {idea.get('previous_season', '')} | Quelle Saison Gagne ?"

    elif video_type == "recently_completed":
        return "Ces Anime Viennent de Se Terminer | Bilan & Notes"

    elif video_type == "top_scores":
        top_anime = anime_list[-1]["title"] if anime_list else ""
        return f"Les Anime les Mieux Notés en Cours de Diffusion | {top_anime}"

    return title_template


def _generate_description(idea):
    """Génère une description détaillée."""
    video_type = idea.get("type", "")
    anime_list = idea.get("anime", [])
    is_comparison = idea.get("is_comparison", False)

    lines = []

    if video_type == "top_trending":
        lines.append("Découvrez les anime les plus populaires et tendances du moment !")
        lines.append("Ce classement est basé sur les données de popularité et trending d'AniList et MyAnimeList.")
    elif video_type == "seasonal_ranking":
        lines.append(f"Classement complet des anime de la saison {idea.get('title_template', '')} !")
        lines.append("Basé sur les scores et la popularité sur MyAnimeList et AniList.")
    elif video_type == "genre_top":
        genre = idea.get("genre", "")
        lines.append(f"Les meilleurs anime du genre {genre} selon les notes des communautés anime !")
    elif video_type == "season_comparison":
        lines.append(f"On compare les anime de {idea.get('current_season', '')} et {idea.get('previous_season', '')} !")
        lines.append("Quelle saison a les meilleurs anime ? Les scores parlent d'eux-mêmes.")
    elif video_type == "recently_completed":
        lines.append("Bilan des anime qui viennent de se terminer. Quels sont les meilleurs ?")
    elif video_type == "top_scores":
        lines.append("Les anime actuellement en diffusion avec les meilleures notes !")

    lines.append("")

    # Liste des anime
    if is_comparison:
        current = idea.get("current_anime", [])
        previous = idea.get("previous_anime", [])
        lines.append(f"═══ {idea.get('current_season', 'Actuel')} ═══")
        for i, a in enumerate(reversed(current), 1):
            score = a.get("score", 0)
            score_str = f"{score/10:.1f}" if score > 10 else str(score)
            lines.append(f"  {i}. {a['title']} ({score_str})")
        lines.append(f"\n═══ {idea.get('previous_season', 'Précédent')} ═══")
        for i, a in enumerate(reversed(previous), 1):
            score = a.get("score", 0)
            score_str = f"{score/10:.1f}" if score > 10 else str(score)
            lines.append(f"  {i}. {a['title']} ({score_str})")
    else:
        lines.append("Anime dans cette vidéo :")
        for i, a in enumerate(reversed(anime_list), 1):
            score = a.get("score", 0)
            score_str = f"{score/10:.1f}" if score > 10 else str(score)
            studio = a.get("studio", "")
            studio_str = f" | {studio}" if studio else ""
            lines.append(f"  {i}. {a['title']} (Score: {score_str}{studio_str})")

    lines.append("")
    lines.append("Sources : AniList, MyAnimeList")
    lines.append("Données mises à jour quotidiennement.")

    return "\n".join(lines)


def _generate_hashtags(idea):
    """Génère une liste de hashtags pertinents."""
    hashtags = list(HASHTAGS_BASE)

    # Hashtags par type de vidéo
    video_type = idea.get("type", "")
    if video_type in TYPE_HASHTAGS:
        hashtags.extend(TYPE_HASHTAGS[video_type])

    # Hashtags par genre
    genre = idea.get("genre", "")
    if genre in GENRE_HASHTAGS:
        hashtags.extend(GENRE_HASHTAGS[genre])

    # Hashtags des anime populaires (noms)
    anime_list = idea.get("anime", [])
    for anime in anime_list[-3:]:  # Top 3
        title = anime.get("title", "").replace(" ", "").replace(":", "")
        if title and len(title) < 25:
            hashtags.append(f"#{title}")

    # Limiter à 30 hashtags max
    return hashtags[:30]


def save_metadata(metadata, output_dir):
    """Sauvegarde les métadonnées dans un fichier texte."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    date_str = metadata.get("date", "output")
    filepath = os.path.join(output_dir, f"metadata_{date_str}.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TITRE:\n{metadata['title']}\n\n")
        f.write(f"DESCRIPTION:\n{metadata['description']}\n\n")
        f.write(f"HASHTAGS:\n{metadata['hashtags_str']}\n\n")
        f.write(f"DATE: {metadata['date']}\n")
        f.write(f"TYPE: {metadata['video_type']}\n")
        f.write(f"NOMBRE D'ANIME: {metadata['anime_count']}\n")

    print(f"[Metadata] Métadonnées sauvegardées : {filepath}")
    return filepath
