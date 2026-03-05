#!/usr/bin/env python3
"""
Pipeline quotidien de génération automatique de vidéos anime.

Usage:
    python -m daily_pipeline.main              # Pipeline complet
    python -m daily_pipeline.main --fetch-only # Collecte de données uniquement
    python -m daily_pipeline.main --idea-only  # Affiche l'idée du jour sans générer
    python -m daily_pipeline.main --no-video   # Tout sauf la vidéo (miniature + métadonnées)
    python -m daily_pipeline.main --type genre_top  # Force un type de vidéo
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from daily_pipeline.data_fetcher import fetch_all_data, load_cached_data
from daily_pipeline.idea_generator import generate_idea, format_idea_summary
from daily_pipeline.video_generator import generate_video
from daily_pipeline.thumbnail_generator import generate_thumbnail
from daily_pipeline.metadata_generator import generate_metadata, save_metadata


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), ".cache", "history.json")


def load_history():
    """Charge l'historique des types de vidéos générées."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"types": [], "dates": []}


def save_history(history):
    """Sauvegarde l'historique."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def run_pipeline(args):
    """Exécute le pipeline complet."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    day_output_dir = os.path.join(OUTPUT_DIR, date_str)

    print(f"\n{'='*60}")
    print(f"  PIPELINE ANIME QUOTIDIEN - {date_str}")
    print(f"{'='*60}\n")

    # Étape 1 : Collecte des données
    print("[1/5] Collecte des données...")
    data = load_cached_data()
    if data and not args.force_fetch:
        print("  → Données du cache trouvées, utilisation du cache.")
    else:
        data = fetch_all_data()

    if not data:
        print("[ERREUR] Impossible de collecter les données. Abandon.")
        return

    if args.fetch_only:
        print("\n[OK] Collecte terminée (--fetch-only).")
        return

    # Étape 2 : Sélection de l'idée
    print("\n[2/5] Sélection de l'idée du jour...")
    history = load_history()

    if args.force_type:
        # Forcer un type de vidéo
        from daily_pipeline.idea_generator import VIDEO_TYPES
        if args.force_type not in VIDEO_TYPES:
            print(f"  [ERREUR] Type inconnu: {args.force_type}")
            print(f"  Types disponibles: {', '.join(VIDEO_TYPES.keys())}")
            return
        # Modifier temporairement le générateur
        idea = generate_idea(data, history.get("types", []))
        idea["type"] = args.force_type
        idea["config"] = VIDEO_TYPES[args.force_type]
        # Re-générer avec le bon type
        idea = generate_idea(data, [args.force_type] * 10)  # Force le choix
        # Hack: on force le type voulu
        from daily_pipeline import idea_generator
        original_weighted = idea_generator._weighted_choice
        idea_generator._weighted_choice = lambda h=None: args.force_type
        idea = generate_idea(data, history.get("types", []))
        idea_generator._weighted_choice = original_weighted
    else:
        idea = generate_idea(data, history.get("types", []))

    print(format_idea_summary(idea))

    if args.idea_only:
        print("\n[OK] Idée affichée (--idea-only).")
        return

    # Étape 3 : Génération des métadonnées
    print("\n[3/5] Génération des métadonnées...")
    metadata = generate_metadata(idea)
    meta_path = save_metadata(metadata, day_output_dir)
    print(f"  Titre: {metadata['title']}")
    print(f"  Hashtags: {metadata['hashtags_str'][:80]}...")

    # Étape 4 : Génération de la miniature
    print("\n[4/5] Génération de la miniature...")
    thumb_path = generate_thumbnail(idea, day_output_dir)

    if args.no_video:
        print("\n[OK] Pipeline terminé sans vidéo (--no-video).")
        _print_summary(day_output_dir, metadata, thumb_path, None, meta_path)
        return

    # Étape 5 : Génération de la vidéo
    print("\n[5/5] Génération de la vidéo...")
    video_path = generate_video(idea, day_output_dir)

    # Sauvegarder l'historique
    history["types"].append(idea["type"])
    history["dates"].append(date_str)
    # Garder seulement les 30 derniers
    history["types"] = history["types"][-30:]
    history["dates"] = history["dates"][-30:]
    save_history(history)

    _print_summary(day_output_dir, metadata, thumb_path, video_path, meta_path)


def _print_summary(output_dir, metadata, thumb_path, video_path, meta_path):
    """Affiche le résumé final."""
    print(f"\n{'='*60}")
    print(f"  PIPELINE TERMINÉ")
    print(f"{'='*60}")
    print(f"  Dossier de sortie : {output_dir}")
    print(f"  Titre : {metadata['title']}")
    if video_path:
        print(f"  Vidéo : {video_path}")
    if thumb_path:
        print(f"  Miniature : {thumb_path}")
    if meta_path:
        print(f"  Métadonnées : {meta_path}")
    print(f"  Hashtags : {len(metadata['hashtags'])} tags")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Pipeline quotidien de vidéos anime")
    parser.add_argument("--fetch-only", action="store_true", help="Collecte de données uniquement")
    parser.add_argument("--idea-only", action="store_true", help="Affiche l'idée sans générer")
    parser.add_argument("--no-video", action="store_true", help="Tout sauf la vidéo")
    parser.add_argument("--force-fetch", action="store_true", help="Force la re-collecte des données")
    parser.add_argument("--type", dest="force_type", help="Force un type de vidéo")

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
