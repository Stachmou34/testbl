"""
Module de collecte de données anime depuis des APIs gratuites.
- Jikan API (MyAnimeList sans auth)
- AniList GraphQL API
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta

JIKAN_BASE = "https://api.jikan.moe/v4"
ANILIST_URL = "https://graphql.anilist.co"

# Rate limiting pour Jikan (3 req/sec max)
_last_jikan_call = 0


def _jikan_get(endpoint, params=None):
    """Requête Jikan avec rate limiting automatique."""
    global _last_jikan_call
    elapsed = time.time() - _last_jikan_call
    if elapsed < 0.4:
        time.sleep(0.4 - elapsed)

    url = f"{JIKAN_BASE}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        _last_jikan_call = time.time()
        if resp.status_code == 429:
            time.sleep(2)
            return _jikan_get(endpoint, params)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"[Jikan] Erreur: {e}")
        return None


def _anilist_query(query, variables=None):
    """Requête GraphQL AniList."""
    try:
        resp = requests.post(
            ANILIST_URL,
            json={"query": query, "variables": variables or {}},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data")
    except requests.RequestException as e:
        print(f"[AniList] Erreur: {e}")
        return None


def get_current_season():
    """Retourne la saison et l'année courante."""
    month = datetime.now().month
    year = datetime.now().year
    if month in (1, 2, 3):
        return "winter", year
    elif month in (4, 5, 6):
        return "spring", year
    elif month in (7, 8, 9):
        return "summer", year
    else:
        return "fall", year


def get_previous_season():
    """Retourne la saison précédente."""
    season, year = get_current_season()
    seasons = ["winter", "spring", "summer", "fall"]
    idx = seasons.index(season)
    if idx == 0:
        return "fall", year - 1
    return seasons[idx - 1], year


def fetch_trending_anime(limit=25):
    """Récupère les anime trending via AniList."""
    query = """
    query ($page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
            media(type: ANIME, sort: TRENDING_DESC, status: RELEASING) {
                id
                idMal
                title { romaji english native }
                coverImage { extraLarge large }
                bannerImage
                averageScore
                popularity
                trending
                episodes
                genres
                season
                seasonYear
                studios(isMain: true) { nodes { name } }
                nextAiringEpisode { episode timeUntilAiring }
            }
        }
    }
    """
    data = _anilist_query(query, {"page": 1, "perPage": limit})
    if not data:
        return []

    results = []
    for media in data.get("Page", {}).get("media", []):
        title = media["title"].get("english") or media["title"].get("romaji", "Unknown")
        studio = ""
        if media.get("studios", {}).get("nodes"):
            studio = media["studios"]["nodes"][0]["name"]

        next_ep = media.get("nextAiringEpisode")
        results.append({
            "title": title,
            "title_romaji": media["title"].get("romaji", title),
            "image": media["coverImage"].get("extraLarge") or media["coverImage"].get("large", ""),
            "banner": media.get("bannerImage", ""),
            "score": media.get("averageScore", 0) or 0,
            "popularity": media.get("popularity", 0),
            "trending": media.get("trending", 0),
            "genres": media.get("genres", []),
            "episodes": media.get("episodes"),
            "season": media.get("season", ""),
            "season_year": media.get("seasonYear", ""),
            "studio": studio,
            "next_episode": next_ep.get("episode") if next_ep else None,
            "next_airing_seconds": next_ep.get("timeUntilAiring") if next_ep else None,
            "source": "anilist",
            "id_mal": media.get("idMal"),
        })
    return results


def fetch_top_airing(limit=25):
    """Récupère le top des anime en cours de diffusion via Jikan."""
    data = _jikan_get("top/anime", {"filter": "airing", "limit": limit})
    if not data:
        return []

    results = []
    for anime in data.get("data", []):
        results.append({
            "title": anime.get("title_english") or anime.get("title", "Unknown"),
            "title_romaji": anime.get("title", ""),
            "image": anime.get("images", {}).get("jpg", {}).get("large_image_url", ""),
            "score": anime.get("score", 0) or 0,
            "popularity": anime.get("members", 0),
            "rank": anime.get("rank", 0),
            "genres": [g["name"] for g in anime.get("genres", [])],
            "episodes": anime.get("episodes"),
            "season": anime.get("season", ""),
            "season_year": anime.get("year"),
            "studio": anime.get("studios", [{}])[0].get("name", "") if anime.get("studios") else "",
            "source": "jikan",
            "mal_id": anime.get("mal_id"),
        })
    return results


def fetch_seasonal_anime(season=None, year=None, limit=50):
    """Récupère les anime d'une saison via AniList."""
    if not season or not year:
        season, year = get_current_season()

    query = """
    query ($season: MediaSeason, $seasonYear: Int, $page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
            media(type: ANIME, season: $season, seasonYear: $seasonYear, sort: POPULARITY_DESC, format: TV) {
                id
                idMal
                title { romaji english }
                coverImage { extraLarge large }
                averageScore
                popularity
                trending
                genres
                episodes
                studios(isMain: true) { nodes { name } }
                nextAiringEpisode { episode timeUntilAiring }
            }
        }
    }
    """
    variables = {
        "season": season.upper(),
        "seasonYear": year,
        "page": 1,
        "perPage": limit,
    }
    data = _anilist_query(query, variables)
    if not data:
        return []

    results = []
    for media in data.get("Page", {}).get("media", []):
        title = media["title"].get("english") or media["title"].get("romaji", "Unknown")
        studio = ""
        if media.get("studios", {}).get("nodes"):
            studio = media["studios"]["nodes"][0]["name"]

        results.append({
            "title": title,
            "title_romaji": media["title"].get("romaji", title),
            "image": media["coverImage"].get("extraLarge") or media["coverImage"].get("large", ""),
            "score": media.get("averageScore", 0) or 0,
            "popularity": media.get("popularity", 0),
            "trending": media.get("trending", 0),
            "genres": media.get("genres", []),
            "episodes": media.get("episodes"),
            "studio": studio,
            "season": season,
            "season_year": year,
            "source": "anilist",
            "id_mal": media.get("idMal"),
        })
    return results


def fetch_top_by_genre(genre, limit=15):
    """Récupère le top anime par genre via AniList."""
    query = """
    query ($genre: String, $page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
            media(type: ANIME, genre: $genre, sort: SCORE_DESC, status: FINISHED, format: TV, minimumTagRank: 50) {
                id
                idMal
                title { romaji english }
                coverImage { extraLarge large }
                averageScore
                popularity
                genres
                episodes
                season
                seasonYear
                studios(isMain: true) { nodes { name } }
            }
        }
    }
    """
    data = _anilist_query(query, {"genre": genre, "page": 1, "perPage": limit})
    if not data:
        return []

    results = []
    for media in data.get("Page", {}).get("media", []):
        title = media["title"].get("english") or media["title"].get("romaji", "Unknown")
        studio = ""
        if media.get("studios", {}).get("nodes"):
            studio = media["studios"]["nodes"][0]["name"]

        results.append({
            "title": title,
            "title_romaji": media["title"].get("romaji", title),
            "image": media["coverImage"].get("extraLarge") or media["coverImage"].get("large", ""),
            "score": media.get("averageScore", 0) or 0,
            "popularity": media.get("popularity", 0),
            "genres": media.get("genres", []),
            "episodes": media.get("episodes"),
            "studio": studio,
            "season": media.get("season", ""),
            "season_year": media.get("seasonYear", ""),
            "source": "anilist",
            "id_mal": media.get("idMal"),
        })
    return results


def fetch_recently_completed(limit=15):
    """Récupère les anime récemment terminés (pour reviews/bilans)."""
    query = """
    query ($page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
            media(type: ANIME, status: FINISHED, sort: END_DATE_DESC, format: TV) {
                id
                idMal
                title { romaji english }
                coverImage { extraLarge large }
                averageScore
                popularity
                genres
                episodes
                season
                seasonYear
                studios(isMain: true) { nodes { name } }
            }
        }
    }
    """
    data = _anilist_query(query, {"page": 1, "perPage": limit})
    if not data:
        return []

    results = []
    for media in data.get("Page", {}).get("media", []):
        title = media["title"].get("english") or media["title"].get("romaji", "Unknown")
        studio = ""
        if media.get("studios", {}).get("nodes"):
            studio = media["studios"]["nodes"][0]["name"]

        results.append({
            "title": title,
            "title_romaji": media["title"].get("romaji", title),
            "image": media["coverImage"].get("extraLarge") or media["coverImage"].get("large", ""),
            "score": media.get("averageScore", 0) or 0,
            "popularity": media.get("popularity", 0),
            "genres": media.get("genres", []),
            "episodes": media.get("episodes"),
            "studio": studio,
            "season": media.get("season", ""),
            "season_year": media.get("seasonYear", ""),
            "source": "anilist",
            "id_mal": media.get("idMal"),
        })
    return results


def fetch_season_comparison(limit=25):
    """Compare la saison actuelle avec la précédente."""
    current_season, current_year = get_current_season()
    prev_season, prev_year = get_previous_season()

    current_data = fetch_seasonal_anime(current_season, current_year, limit)
    prev_data = fetch_seasonal_anime(prev_season, prev_year, limit)

    return {
        "current": {
            "season": current_season,
            "year": current_year,
            "anime": current_data,
        },
        "previous": {
            "season": prev_season,
            "year": prev_year,
            "anime": prev_data,
        },
    }


def fetch_all_data():
    """Collecte toutes les données nécessaires pour la génération d'idées."""
    print("[Data] Collecte des données en cours...")

    print("  → Trending anime...")
    trending = fetch_trending_anime(25)

    print("  → Top airing...")
    top_airing = fetch_top_airing(25)

    print("  → Anime de la saison...")
    season, year = get_current_season()
    seasonal = fetch_seasonal_anime(season, year, 50)

    print("  → Anime récemment terminés...")
    completed = fetch_recently_completed(15)

    print("  → Comparaison saisonnière...")
    comparison = fetch_season_comparison(25)

    # Genres populaires pour les vidéos thématiques
    genres = ["Action", "Romance", "Fantasy", "Sci-Fi", "Horror", "Comedy", "Drama", "Sports"]
    genre_data = {}
    for genre in genres:
        print(f"  → Top {genre}...")
        genre_data[genre] = fetch_top_by_genre(genre, 15)
        time.sleep(0.3)

    data = {
        "trending": trending,
        "top_airing": top_airing,
        "seasonal": seasonal,
        "completed": completed,
        "comparison": comparison,
        "genres": genre_data,
        "fetch_date": datetime.now().isoformat(),
        "current_season": season,
        "current_year": year,
    }

    # Sauvegarder le cache
    cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"data_{datetime.now().strftime('%Y-%m-%d')}.json")
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[Data] Collecte terminée. {len(trending)} trending, {len(top_airing)} airing, {len(seasonal)} saisonniers.")
    return data


def load_cached_data():
    """Charge les données du cache du jour si disponibles."""
    cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
    cache_file = os.path.join(cache_dir, f"data_{datetime.now().strftime('%Y-%m-%d')}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
