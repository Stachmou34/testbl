import requests
import csv
import json
from datetime import datetime

# Charger le token
with open('token.json', 'r') as f:
    token_data = json.load(f)
access_token = token_data['access_token']

# URL pour la recherche d'animes de 2023
url = 'https://api.myanimelist.net/v2/anime/ranking'
fields = 'id,title,main_picture,start_date,genres,num_list_users,media_type,alternative_titles,mean'
limit = 100  # On récupère plus d'animes pour avoir assez de TV après filtrage
animes = []
offset = 0
headers = {
    'Authorization': f'Bearer {access_token}'
}

print('Récupération des animes de 2023...')
while True:
    params = {
        'ranking_type': 'all',  # Tous les animes
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
        # Vérifier si l'anime est de type TV et de 2023
        start_date = anime.get('start_date', '')
        if (anime.get('media_type') == 'tv' and 
            start_date.startswith('2023')):
            alt_titles = anime.get('alternative_titles', {})
            title = alt_titles.get('en') or anime.get('title', '')
            animes.append({
                'image': anime.get('main_picture', {}).get('large') or anime.get('main_picture', {}).get('medium', ''),
                'title': title,
                'start_date': start_date,
                'genres': ', '.join([g['name'] for g in anime.get('genres', [])]),
                'num_list_users': anime.get('num_list_users', 0),
                'media_type': anime.get('media_type', ''),
                'mean': anime.get('mean', 0)  # Score moyen
            })
    
    # Si on a déjà plus de 50 animes TV de 2023, on peut arrêter
    if len(animes) >= 50:
        break
    
    # Pagination
    if 'paging' in data and 'next' in data['paging']:
        offset += limit
    else:
        break

# Trier les animes par score moyen décroissant
animes.sort(key=lambda x: x['mean'], reverse=True)

# Ne garder que les 50 premiers
animes = animes[:50]

# Écriture du CSV
csv_file = 'top_50_tv_2023.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['image', 'title', 'start_date', 'genres', 'num_list_users', 'media_type', 'mean'])
    writer.writeheader()
    for anime in animes:
        writer.writerow(anime)

if not animes:
    print('Aucun anime TV de 2023 trouvé. Vérifiez la réponse ci-dessus ou le token.')
else:
    print(f'{len(animes)} animes TV de 2023 exportés dans {csv_file}') 