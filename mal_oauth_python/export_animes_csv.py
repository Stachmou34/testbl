import requests
import csv
import json
from datetime import datetime

# Charger le token
with open('token.json', 'r') as f:
    token_data = json.load(f)
access_token = token_data['access_token']

url = 'https://api.myanimelist.net/v2/anime/season/2025/summer'
fields = 'id,title,main_picture,start_date,genres,num_list_users,media_type,alternative_titles'
limit = 50
animes = []
offset = 0
headers = {
    'Authorization': f'Bearer {access_token}'
}

print('Récupération des animes été 2025...')
while True:
    params = {
        'limit': limit,
        'offset': offset,
        'fields': fields
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print('Erreur lors de la requête:', response.status_code, response.text)
        break
    data = response.json()
    if not data.get('data'):
        print('Réponse API sans données :', data)
        break
    for entry in data.get('data', []):
        anime = entry.get('node', {})
        alt_titles = anime.get('alternative_titles', {})
        title = alt_titles.get('en') or anime.get('title', '')
        animes.append({
            'image': anime.get('main_picture', {}).get('large') or anime.get('main_picture', {}).get('medium', ''),
            'title': title,
            'start_date': anime.get('start_date', ''),
            'genres': ', '.join([g['name'] for g in anime.get('genres', [])]),
            'num_list_users': anime.get('num_list_users', 0),
            'media_type': anime.get('media_type', '')
        })
    # Pagination
    if 'paging' in data and 'next' in data['paging']:
        offset += limit
    else:
        break

# Trier les animes par date de sortie croissante (du plus ancien au plus récent)
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return datetime.max  # Les dates invalides ou vides vont à la fin

animes.sort(key=lambda x: parse_date(x['start_date']))

# Écriture du CSV
csv_file = 'animes_summer_2025.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['image', 'title', 'start_date', 'genres', 'num_list_users', 'media_type'])
    writer.writeheader()
    for anime in animes:
        writer.writerow(anime)

if not animes:
    print('Aucun anime trouvé. Vérifiez la réponse ci-dessus ou le token.')
else:
    print(f'{len(animes)} animes exportés dans {csv_file}') 