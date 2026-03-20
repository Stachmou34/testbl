"""
Moteur de sélection automatique d'idées vidéo.
Analyse les données collectées et choisit la meilleure idée du jour.
"""

import random
import hashlib
from datetime import datetime


# Types de vidéos disponibles avec leur poids de sélection
VIDEO_TYPES = {
    "top_trending": {
        "name": "Top Anime Trending",
        "weight": 25,
        "description": "Les anime les plus populaires en ce moment",
    },
    "seasonal_ranking": {
        "name": "Classement de la Saison",
        "weight": 20,
        "description": "Les meilleurs anime de la saison en cours",
    },
    "genre_top": {
        "name": "Top par Genre",
        "weight": 20,
        "description": "Les meilleurs anime d'un genre spécifique",
    },
    "season_comparison": {
        "name": "Saison vs Saison",
        "weight": 15,
        "description": "Comparaison entre la saison actuelle et la précédente",
    },
    "recently_completed": {
        "name": "Anime Récemment Terminés",
        "weight": 10,
        "description": "Bilan des anime qui viennent de se terminer",
    },
    "top_scores": {
        "name": "Top Scores du Moment",
        "weight": 10,
        "description": "Les anime les mieux notés actuellement en diffusion",
    },
}


def _daily_seed():
    """Seed déterministe basé sur la date du jour."""
    return int(hashlib.md5(datetime.now().strftime("%Y-%m-%d").encode()).hexdigest(), 16)


def _weighted_choice(video_type_history=None):
    """Choisit un type de vidéo pondéré en évitant les répétitions récentes."""
    weights = {}
    for vtype, config in VIDEO_TYPES.items():
        weights[vtype] = config["weight"]

    # Réduire le poids des types récemment utilisés
    if video_type_history:
        for i, past_type in enumerate(reversed(video_type_history[-5:])):
            if past_type in weights:
                # Plus c'est récent, plus on réduit
                weights[past_type] = max(1, weights[past_type] // (5 - i))

    types = list(weights.keys())
    w = [weights[t] for t in types]
    total = sum(w)
    probs = [x / total for x in w]

    rng = random.Random(_daily_seed())
    return rng.choices(types, weights=probs, k=1)[0]


def generate_idea(data, video_type_history=None):
    """Génère la meilleure idée vidéo du jour basée sur les données."""
    video_type = _weighted_choice(video_type_history)
    rng = random.Random(_daily_seed())

    idea = {
        "type": video_type,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "config": VIDEO_TYPES[video_type],
    }

    if video_type == "top_trending":
        anime_list = data.get("trending", [])
        if not anime_list:
            anime_list = data.get("top_airing", [])
        # Top 10 ou 15 trending
        count = rng.choice([10, 15, 20])
        idea["anime"] = sorted(anime_list, key=lambda x: x.get("trending", 0), reverse=True)[:count]
        idea["title_template"] = f"Top {count} Anime Trending"
        idea["sort_key"] = "trending"
        idea["sort_label"] = "Trending Score"
        idea["value_key"] = "trending"
        idea["value_format"] = "score"

    elif video_type == "seasonal_ranking":
        season = data.get("current_season", "winter").capitalize()
        year = data.get("current_year", 2026)
        anime_list = data.get("seasonal", [])
        # Filtrer ceux avec un score
        scored = [a for a in anime_list if a.get("score", 0) > 0]
        if len(scored) < 5:
            scored = anime_list
        count = min(len(scored), rng.choice([15, 20, 25]))
        idea["anime"] = sorted(scored, key=lambda x: x.get("score", 0))[:count]  # ascending pour le scroll
        idea["title_template"] = f"Classement Anime {season} {year}"
        idea["sort_key"] = "score"
        idea["sort_label"] = "Score"
        idea["value_key"] = "score"
        idea["value_format"] = "score"

    elif video_type == "genre_top":
        genres_data = data.get("genres", {})
        available_genres = [g for g, animes in genres_data.items() if len(animes) >= 5]
        if not available_genres:
            available_genres = list(genres_data.keys())
        genre = rng.choice(available_genres) if available_genres else "Action"
        anime_list = genres_data.get(genre, [])
        count = min(len(anime_list), 15)
        idea["anime"] = sorted(anime_list, key=lambda x: x.get("score", 0))[:count]
        idea["title_template"] = f"Top {count} Meilleurs Anime {genre}"
        idea["genre"] = genre
        idea["sort_key"] = "score"
        idea["sort_label"] = "Score"
        idea["value_key"] = "score"
        idea["value_format"] = "score"

    elif video_type == "season_comparison":
        comparison = data.get("comparison", {})
        current = comparison.get("current", {})
        previous = comparison.get("previous", {})
        current_anime = current.get("anime", [])
        prev_anime = previous.get("anime", [])

        # Trouver les anime communs ou faire un versus
        idea["current_season"] = f"{current.get('season', '').capitalize()} {current.get('year', '')}"
        idea["previous_season"] = f"{previous.get('season', '').capitalize()} {previous.get('year', '')}"
        idea["current_anime"] = sorted(current_anime, key=lambda x: x.get("score", 0), reverse=True)[:10]
        idea["previous_anime"] = sorted(prev_anime, key=lambda x: x.get("score", 0), reverse=True)[:10]
        idea["title_template"] = f"{idea['current_season']} vs {idea['previous_season']}"
        idea["is_comparison"] = True

    elif video_type == "recently_completed":
        anime_list = data.get("completed", [])
        count = min(len(anime_list), 10)
        idea["anime"] = sorted(anime_list, key=lambda x: x.get("score", 0))[:count]
        idea["title_template"] = "Anime Récemment Terminés - Bilan"
        idea["sort_key"] = "score"
        idea["sort_label"] = "Score"
        idea["value_key"] = "score"
        idea["value_format"] = "score"

    elif video_type == "top_scores":
        anime_list = data.get("top_airing", [])
        if not anime_list:
            anime_list = data.get("trending", [])
        scored = [a for a in anime_list if a.get("score", 0) > 0]
        count = min(len(scored), 15)
        idea["anime"] = sorted(scored, key=lambda x: x.get("score", 0))[:count]
        idea["title_template"] = "Top Anime les Mieux Notés en Cours"
        idea["sort_key"] = "score"
        idea["sort_label"] = "Score MAL"
        idea["value_key"] = "score"
        idea["value_format"] = "score"

    return idea


def format_idea_summary(idea):
    """Formate un résumé lisible de l'idée."""
    lines = [
        f"{'='*60}",
        f"  IDÉE VIDÉO DU JOUR - {idea['date']}",
        f"{'='*60}",
        f"  Type: {idea['config']['name']}",
        f"  Description: {idea['config']['description']}",
        f"  Titre: {idea.get('title_template', 'N/A')}",
    ]

    if idea.get("is_comparison"):
        lines.append(f"  {idea['current_season']} ({len(idea.get('current_anime', []))} anime)")
        lines.append(f"  vs {idea['previous_season']} ({len(idea.get('previous_anime', []))} anime)")
    else:
        anime_list = idea.get("anime", [])
        lines.append(f"  Nombre d'anime: {len(anime_list)}")
        if anime_list:
            lines.append(f"\n  Anime inclus:")
            for i, a in enumerate(anime_list, 1):
                score = a.get("score", 0)
                score_str = f"{score/10:.1f}" if score > 10 else str(score)
                lines.append(f"    {i:2d}. {a['title']} (Score: {score_str})")

    lines.append(f"{'='*60}")
    return "\n".join(lines)
