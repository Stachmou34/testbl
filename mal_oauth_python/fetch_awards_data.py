import requests
import pandas as pd
import time
from typing import Dict, List
import json

# Configuration de l'API MAL
MAL_CLIENT_ID = "6114d00ca681b7701d1e15fe11a4987e"  # Client ID MAL
BASE_URL = "https://api.myanimelist.net/v2"

# Mapping titres alternatifs et liens MAL pour les titres problématiques
ALTERNATIVE_TITLES = {
    "SPY×FAMILY Code: White": {
        "title": "Spy x Family Movie: Code: White",
        "mal_id": 53888
    },
    "BUCCHIGIRI?!": {
        "title": "Bucchigiri?!",
        "mal_id": 55358
    },
    "Jellyfish Can't Swim in the Night": {
        "title": "Yoru no Kurage wa Oyogenai",
        "mal_id": 54839
    },
    "Train to the End of the World": {
        "title": "Shuumatsu Train Doko e Iku?",
        "mal_id": 53356
    },
    "Delicious in Dungeon": {
        "title": "Dungeon Meshi",
        "mal_id": 52701
    },
    "The Dangers in My Heart Season 2": {
        "title": "Boku no Kokoro no Yabai Yatsu 2nd Season",
        "mal_id": 55690
    },
    "Sound! Euphonium 3": {
        "title": "Hibike! Euphonium 3",
        "mal_id": 39894
    },
    "A Sign of Affection": {
        "title": "Yubisaki to Renren",
        "mal_id": 55866
    },
    "Spy×Family Season 2": {
        "title": "Spy x Family Season 2",
        "mal_id": 53887
    },
    "The Colors Within": {
        "title": "Kimi no Iro",
        "mal_id": 53747
    },
}

def search_anime(title: str, mal_id: int = None):
    """Recherche un anime par titre ou par mal_id sur MyAnimeList."""
    headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
    if mal_id:
        url = f"https://api.myanimelist.net/v2/anime/{mal_id}?fields=title,main_picture,mean,media_type,genres"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return {
                "title": data.get("title", title),
                "image": data.get("main_picture", {}).get("large", "N/A"),
                "score": data.get("mean", "N/A"),
                "media_type": data.get("media_type", "N/A"),
                "genres": ', '.join([g['name'] for g in data.get("genres", [])])
            }
    # Fallback recherche par titre
    url = f"https://api.myanimelist.net/v2/anime?q={title}&limit=1&fields=title,main_picture,mean,media_type,genres"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if data.get("data"):
            anime = data["data"][0]["node"]
            return {
                "title": anime.get("title", title),
                "image": anime.get("main_picture", {}).get("large", "N/A"),
                "score": anime.get("mean", "N/A"),
                "media_type": anime.get("media_type", "N/A"),
                "genres": ', '.join([g['name'] for g in anime.get("genres", [])])
            }
    # Si tout échoue
    return {
        "title": title,
        "image": "N/A",
        "score": "N/A",
        "media_type": "N/A",
        "genres": "N/A"
    }

def process_awards_list() -> List[Dict]:
    """Traite la liste des gagnants et récupère leurs informations."""
    winners = []
    
    # Liste complète des catégories et leurs candidats
    awards_list = [
        {
            "category": "Anime of the Year",
            "candidates": [
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": True},
                {"title": "The Apothecary Diaries", "is_winner": False}
            ]
        },
        {
            "category": "Film of the Year",
            "candidates": [
                {"title": "HAIKYU!! The Dumpster Battle", "is_winner": False},
                {"title": "Look Back", "is_winner": True},
                {"title": "Mononoke the Movie: The Phantom in the Rain", "is_winner": False},
                {"title": "My Hero Academia: You're Next", "is_winner": False},
                {"title": "SPY×FAMILY Code: White", "is_winner": False},
                {"title": "The Colors Within", "is_winner": False}
            ]
        },
        {
            "category": "Best Original Anime",
            "candidates": [
                {"title": "BUCCHIGIRI?!", "is_winner": False},
                {"title": "GIRLS BAND CRY", "is_winner": False},
                {"title": "Jellyfish Can't Swim in the Night", "is_winner": False},
                {"title": "Metallic Rouge", "is_winner": False},
                {"title": "Ninja Kamui", "is_winner": True},
                {"title": "Train to the End of the World", "is_winner": False}
            ]
        },
        {
            "category": "Best Continuing Series",
            "candidates": [
                {"title": "Bleach: Thousand-Year Blood War Part 3 - The Conflict", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": True},
                {"title": "My Hero Academia Season 7", "is_winner": False},
                {"title": "One Piece", "is_winner": False},
                {"title": "Oshi no Ko Season 2", "is_winner": False},
                {"title": "Spy×Family Season 2", "is_winner": False}
            ]
        },
        {
            "category": "Best New Series",
            "candidates": [
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": True},
                {"title": "The Apothecary Diaries", "is_winner": False}
            ]
        },
        {
            "category": "Best Opening Sequence",
            "candidates": [
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "MASHLE: MAGIC AND MUSCLES", "is_winner": False},
                {"title": "Oshi no Ko Season 2", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": True},
                {"title": "ONE PIECE", "is_winner": False}
            ]
        },
        {
            "category": "Best Ending Sequence",
            "candidates": [
                {"title": "Ranma 1/2", "is_winner": False},
                {"title": "Oshi no Ko Season 2", "is_winner": False},
                {"title": "The Elusive Samurai", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": True},
                {"title": "DAN DA DAN", "is_winner": False}
            ]
        },
        {
            "category": "Best Action",
            "candidates": [
                {"title": "Bleach: Thousand-Year Blood War Part 3 - The Conflict", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": True},
                {"title": "WIND BREAKER", "is_winner": False}
            ]
        },
        {
            "category": "Best Comedy",
            "candidates": [
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "KonoSuba – God's blessing on this wonderful world!! 3", "is_winner": False},
                {"title": "MASHLE: MAGIC AND MUSCLES", "is_winner": True},
                {"title": "My Deer Friend Nokotan", "is_winner": False},
                {"title": "Ranma 1/2", "is_winner": False},
                {"title": "Spy×Family Season 2", "is_winner": False}
            ]
        },
        {
            "category": "Best Isekai Anime",
            "candidates": [
                {"title": "KonoSuba – God's blessing on this wonderful world!! 3", "is_winner": False},
                {"title": "Mushoku Tensei: Jobless Reincarnation", "is_winner": False},
                {"title": "Re:ZERO -Starting Life in Another World-", "is_winner": True},
                {"title": "Shangri-La Frontier", "is_winner": False},
                {"title": "Suicide Squad ISEKAI", "is_winner": False},
                {"title": "That Time I Got Reincarnated as a Slime", "is_winner": False}
            ]
        },
        {
            "category": "Best Drama",
            "candidates": [
                {"title": "A Sign of Affection", "is_winner": False},
                {"title": "DEAD DEAD DEMONS DEDEDEDE DESTRUCTION", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": True},
                {"title": "Oshi no Ko Season 2", "is_winner": False},
                {"title": "Pluto", "is_winner": False},
                {"title": "The Apothecary Diaries", "is_winner": False}
            ]
        },
        {
            "category": "Best Romance",
            "candidates": [
                {"title": "A Sign of Affection", "is_winner": False},
                {"title": "Blue Box", "is_winner": True},
                {"title": "Makeine: Too Many Losing Heroines!", "is_winner": False},
                {"title": "Ranma 1/2", "is_winner": False},
                {"title": "Scott Pilgrim Takes Off", "is_winner": False},
                {"title": "The Dangers in My Heart Season 2", "is_winner": False}
            ]
        },
        {
            "category": "Best Slice of Life",
            "candidates": [
                {"title": "Laid-Back Camp Season 3", "is_winner": False},
                {"title": "Makeine: Too Many Losing Heroines!", "is_winner": True},
                {"title": "Mr. Villain's Day Off", "is_winner": False},
                {"title": "My Deer Friend Nokotan", "is_winner": False},
                {"title": "Sound! Euphonium 3", "is_winner": False},
                {"title": "The Dangers in My Heart Season 2", "is_winner": False}
            ]
        },
        {
            "category": "Best Animation",
            "candidates": [
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": True},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": False}
            ]
        },
        {
            "category": "Best Background Art",
            "candidates": [
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": True},
                {"title": "Pluto", "is_winner": False},
                {"title": "The Apothecary Diaries", "is_winner": False}
            ]
        },
        {
            "category": "Best Character Design",
            "candidates": [
                {"title": "DAN DA DAN", "is_winner": True},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "The Apothecary Diaries", "is_winner": False}
            ]
        },
        {
            "category": "Best Director",
            "candidates": [
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": True},
                {"title": "One Piece", "is_winner": False},
                {"title": "The Apothecary Diaries", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False}
            ]
        },
        {
            "category": "Best Main Character",
            "candidates": [
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "The Apothecary Diaries", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": True}
            ]
        },
        {
            "category": "Best Supporting Character",
            "candidates": [
                {"title": "Frieren: Beyond Journey's End", "is_winner": True},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "The Apothecary Diaries", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False}
            ]
        },
        {
            "category": "Must Protect At All Costs Character",
            "candidates": [
                {"title": "Spy×Family Season 2", "is_winner": True},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Delicious in Dungeon", "is_winner": False},
                {"title": "The Elusive Samurai", "is_winner": False},
                {"title": "A Sign of Affection", "is_winner": False}
            ]
        },
        {
            "category": "Best Anime Song",
            "candidates": [
                {"title": "Kaiju No. 8", "is_winner": False},
                {"title": "MASHLE: MAGIC AND MUSCLES", "is_winner": False},
                {"title": "Oshi no Ko Season 2", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": True},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False}
            ]
        },
        {
            "category": "Best Score",
            "candidates": [
                {"title": "Bleach: Thousand-Year Blood War Part 3 - The Conflict", "is_winner": False},
                {"title": "DAN DA DAN", "is_winner": False},
                {"title": "Demon Slayer: Kimetsu no Yaiba Hashira Training Arc", "is_winner": False},
                {"title": "Frieren: Beyond Journey's End", "is_winner": False},
                {"title": "Look Back", "is_winner": False},
                {"title": "Solo Leveling", "is_winner": True}
            ]
        }
    ]
    
    for award in awards_list:
        category = award["category"]
        for candidate in award["candidates"]:
            title = candidate["title"]
            is_winner = candidate["is_winner"]
            alt = ALTERNATIVE_TITLES.get(title)
            if alt:
                anime_info = search_anime(alt["title"], mal_id=alt["mal_id"])
            else:
                anime_info = search_anime(title)
            anime_info.update({
                "category": category,
                "is_winner": is_winner
            })
            winners.append(anime_info)
            
            # Pause pour respecter les limites de l'API
            time.sleep(1)
    
    return winners

def main():
    # Récupération des données
    winners = process_awards_list()
    
    # Création du DataFrame
    df = pd.DataFrame(winners)
    
    # Sauvegarde en CSV
    df.to_csv('crunchyroll_awards_2025_updated.csv', index=False)
    print("Données sauvegardées dans crunchyroll_awards_2025_updated.csv")

if __name__ == "__main__":
    main() 