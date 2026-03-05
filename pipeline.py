#!/usr/bin/env python3
"""
Pipeline automatise de generation video anime/manga.

Usage:
    python pipeline.py --type blue_lock
    python pipeline.py --type fire_force
    python pipeline.py --type one_piece
    python pipeline.py --type anime_spring_2025
    python pipeline.py --all
    python pipeline.py --list
    python pipeline.py --type anime_season --csv mon_fichier.csv --output ma_video.mp4
"""
import argparse
import os
import sys
import time
import yaml
import pandas as pd

from video_engine import build_scrolling_video
from card_templates import (
    create_card_blue_lock,
    create_card_fire_force,
    create_card_wanted_poster,
    create_card_anime_season,
)


def load_config(config_path='pipeline_config.yaml'):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


# =============================================================================
# Steps
# =============================================================================

def step_fetch_mal_data(pipeline_cfg, config):
    """Recupere les donnees depuis l'API MyAnimeList."""
    mal_cfg = pipeline_cfg.get('mal_config', {})
    season = mal_cfg.get('season', 'spring')
    year = mal_cfg.get('year', 2025)
    csv_file = pipeline_cfg['csv']

    # Check if CSV already exists and is recent (< 1 day)
    if os.path.exists(csv_file):
        age_hours = (time.time() - os.path.getmtime(csv_file)) / 3600
        if age_hours < 24:
            print(f"  [fetch] {csv_file} est recent ({age_hours:.1f}h), skip.")
            return

    token_path = 'mal_oauth_python/token.json'
    if not os.path.exists(token_path):
        print(f"  [fetch] ATTENTION: {token_path} introuvable. Impossible de fetcher les donnees MAL.")
        print(f"  [fetch] Utilisation du CSV existant si disponible: {csv_file}")
        if not os.path.exists(csv_file):
            print(f"  [fetch] ERREUR: {csv_file} introuvable. Configurez d'abord votre token MAL.")
            sys.exit(1)
        return

    import json
    import requests

    with open(token_path, 'r') as f:
        token_data = json.load(f)
    access_token = token_data['access_token']

    url = f'https://api.myanimelist.net/v2/anime/season/{year}/{season}'
    fields = 'id,title,main_picture,start_date,genres,mean,media_type,alternative_titles'
    headers = {'Authorization': f'Bearer {access_token}'}

    animes = []
    offset = 0
    print(f"  [fetch] Recuperation animes {season} {year}...")

    while True:
        params = {'offset': offset, 'fields': fields}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"  [fetch] Erreur API: {response.status_code}")
            break
        data = response.json()
        if not data.get('data'):
            break
        for entry in data['data']:
            anime = entry.get('node', {})
            alt_titles = anime.get('alternative_titles', {})
            title = alt_titles.get('en') or anime.get('title', '')
            animes.append({
                'image': anime.get('main_picture', {}).get('large') or anime.get('main_picture', {}).get('medium', ''),
                'title': title,
                'start_date': anime.get('start_date', ''),
                'genres': ', '.join([g['name'] for g in anime.get('genres', [])]),
                'num_list_users': anime.get('mean', 0),
                'media_type': anime.get('media_type', '')
            })
        if 'paging' in data and 'next' in data['paging']:
            offset += len(data['data'])
        else:
            break

    if animes:
        df = pd.DataFrame(animes)
        df.to_csv(csv_file, index=False)
        print(f"  [fetch] {len(animes)} animes sauvegardes dans {csv_file}")
    else:
        print(f"  [fetch] Aucun anime recupere, utilisation du CSV existant.")


def step_download_images(pipeline_cfg, config):
    """Telecharge les images manquantes pour Fire Force."""
    csv_file = pipeline_cfg['csv']
    if not os.path.exists(csv_file):
        print(f"  [images] CSV {csv_file} introuvable, skip.")
        return

    df = pd.read_csv(csv_file)
    images_dir = 'images_fire_force'
    os.makedirs(images_dir, exist_ok=True)

    missing = 0
    for _, row in df.iterrows():
        image_path = str(row.get('Image', 'N/A'))
        if image_path != 'N/A' and not os.path.exists(image_path):
            missing += 1

    if missing == 0:
        print(f"  [images] Toutes les images sont presentes.")
        return

    print(f"  [images] {missing} images manquantes. Lancement du scraping...")
    # Import and run the existing download script
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("download_images", "download_images.py")
        mod = importlib.util.load_module_from_spec(spec)
        # The script runs on import (update_csv_with_info)
        print(f"  [images] Scraping termine.")
    except Exception as e:
        print(f"  [images] Erreur scraping: {e}")
        print(f"  [images] Continuation avec les images disponibles.")


def step_generate_video(pipeline_cfg, config):
    """Genere la video a partir du CSV et du template de carte."""
    csv_file = pipeline_cfg['csv']
    template = pipeline_cfg['card_template']
    output_file = pipeline_cfg.get('output_file', 'output.mp4')

    if not os.path.exists(csv_file):
        print(f"  [video] ERREUR: {csv_file} introuvable.")
        sys.exit(1)

    df = pd.read_csv(csv_file)

    # Sort if configured
    sort_by = pipeline_cfg.get('sort_by')
    if sort_by and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=pipeline_cfg.get('sort_ascending', True))

    # Limit rows if configured
    limit = pipeline_cfg.get('limit')
    if limit:
        df = df.head(limit)

    # Build video config from defaults + overrides
    defaults = config.get('defaults', {})
    video_config = {**defaults}
    for key in ['width', 'height', 'separator_width', 'fps', 'scroll_duration',
                'intro_duration', 'pause_duration', 'initial_delay', 'bitrate', 'preset', 'threads']:
        if key in pipeline_cfg:
            video_config[key] = pipeline_cfg[key]
    video_config['output_file'] = output_file

    # Calculate card dimensions
    card_width = (video_config['width'] - video_config['separator_width'] * 2) // 3
    card_height = video_config['height']

    # Map template name to card function
    CARD_FUNCTIONS = {
        'blue_lock': lambda row: create_card_blue_lock(row, card_width, card_height),
        'fire_force': lambda row: create_card_fire_force(row, card_width, card_height),
        'wanted_poster': lambda row: create_card_wanted_poster(
            row, card_width, card_height,
            pipeline_cfg.get('wanted_poster_path', 'img/avis de recherhche 2.jpg')
        ),
        'anime_season': lambda row: create_card_anime_season(row, card_width, card_height),
    }

    card_fn = CARD_FUNCTIONS.get(template)
    if not card_fn:
        print(f"  [video] ERREUR: Template inconnu '{template}'")
        sys.exit(1)

    print(f"  [video] Creation de {len(df)} cartes ({template})...")
    all_cards = []
    for idx, (_, row) in enumerate(df.iterrows()):
        card = card_fn(row)
        if card is not None:
            all_cards.append(card)
            print(f"    Carte {idx + 1}/{len(df)}: OK")
        else:
            print(f"    Carte {idx + 1}/{len(df)}: SKIP (erreur)")

    if len(all_cards) < 3:
        print(f"  [video] ERREUR: Il faut au moins 3 cartes, seulement {len(all_cards)} disponibles.")
        sys.exit(1)

    build_scrolling_video(all_cards, video_config)


# =============================================================================
# Pipeline runner
# =============================================================================

STEP_FUNCTIONS = {
    'fetch_mal_data': step_fetch_mal_data,
    'download_images': step_download_images,
    'generate_video': step_generate_video,
}


def run_pipeline(pipeline_name, pipeline_cfg, config):
    steps = pipeline_cfg.get('steps', ['generate_video'])
    description = pipeline_cfg.get('description', pipeline_name)

    print(f"\n{'=' * 60}")
    print(f"  PIPELINE: {description}")
    print(f"  Steps: {' -> '.join(steps)}")
    print(f"{'=' * 60}\n")

    start_time = time.time()

    for i, step_name in enumerate(steps):
        step_fn = STEP_FUNCTIONS.get(step_name)
        if not step_fn:
            print(f"  ERREUR: Step inconnue '{step_name}'")
            sys.exit(1)

        print(f"[{i + 1}/{len(steps)}] {step_name}...")
        step_start = time.time()
        step_fn(pipeline_cfg, config)
        elapsed = time.time() - step_start
        print(f"[{i + 1}/{len(steps)}] {step_name} termine en {elapsed:.1f}s\n")

    total = time.time() - start_time
    print(f"Pipeline '{pipeline_name}' termine en {total:.1f}s")
    print(f"Output: {pipeline_cfg.get('output_file', 'output.mp4')}")


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline automatise de generation video anime/manga',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python pipeline.py --list                           Lister les pipelines
  python pipeline.py --type blue_lock                 Generer video Blue Lock
  python pipeline.py --type fire_force                Generer video Fire Force
  python pipeline.py --type one_piece                 Generer video One Piece
  python pipeline.py --type anime_spring_2025         Generer video anime saison
  python pipeline.py --all                            Tout generer
  python pipeline.py --type blue_lock --output v.mp4  Override le fichier de sortie
  python pipeline.py --type blue_lock --csv data.csv  Override le fichier CSV
  python pipeline.py --type blue_lock --fps 30        Override le FPS
        """
    )

    parser.add_argument('--type', '-t', help='Type de pipeline a executer')
    parser.add_argument('--all', '-a', action='store_true', help='Executer tous les pipelines')
    parser.add_argument('--list', '-l', action='store_true', help='Lister les pipelines disponibles')
    parser.add_argument('--config', '-c', default='pipeline_config.yaml', help='Fichier de configuration')

    # Overrides
    parser.add_argument('--csv', help='Override le fichier CSV source')
    parser.add_argument('--output', '-o', help='Override le fichier video de sortie')
    parser.add_argument('--fps', type=int, help='Override le FPS')
    parser.add_argument('--width', type=int, help='Override la largeur')
    parser.add_argument('--height', type=int, help='Override la hauteur')
    parser.add_argument('--limit', type=int, help='Limiter le nombre de cartes')
    parser.add_argument('--threads', type=int, help='Nombre de threads pour l\'encodage')

    args = parser.parse_args()

    config = load_config(args.config)
    pipelines = config.get('pipelines', {})

    # List mode
    if args.list:
        print("\nPipelines disponibles:\n")
        for name, cfg in pipelines.items():
            desc = cfg.get('description', '')
            csv = cfg.get('csv', '')
            output = cfg.get('output_file', '')
            steps = ' -> '.join(cfg.get('steps', []))
            print(f"  {name:25s} {desc}")
            print(f"  {'':25s} CSV: {csv} | Output: {output}")
            print(f"  {'':25s} Steps: {steps}\n")
        return

    if not args.type and not args.all:
        parser.print_help()
        return

    # Build list of pipelines to run
    if args.all:
        to_run = list(pipelines.keys())
    else:
        if args.type not in pipelines:
            print(f"Erreur: pipeline '{args.type}' inconnu.")
            print(f"Pipelines disponibles: {', '.join(pipelines.keys())}")
            sys.exit(1)
        to_run = [args.type]

    # Apply overrides
    for name in to_run:
        cfg = pipelines[name]
        if args.csv:
            cfg['csv'] = args.csv
        if args.output:
            cfg['output_file'] = args.output
        if args.fps:
            cfg['fps'] = args.fps
        if args.width:
            cfg['width'] = args.width
        if args.height:
            cfg['height'] = args.height
        if args.limit:
            cfg['limit'] = args.limit
        if args.threads:
            cfg['threads'] = args.threads

    # Run
    total_start = time.time()
    for name in to_run:
        run_pipeline(name, pipelines[name], config)

    if len(to_run) > 1:
        total = time.time() - total_start
        print(f"\n{'=' * 60}")
        print(f"  TOUS LES PIPELINES TERMINES en {total:.1f}s")
        print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
