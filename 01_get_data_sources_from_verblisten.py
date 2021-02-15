import requests
import string
from bs4 import BeautifulSoup
from mongo_db import connect_mongo_db

db = connect_mongo_db()

def get_data_sources():
    base_url = 'https://www.verblisten.de/listen/verben/anfangsbuchstabe/vollstaendig'
    alphabet = 'abcdefghijklmnopqrstuvwxzäöü'
    data_sources = []
    for letter in alphabet:
        counter = 0
        links_found = True
        while links_found:
            counter+=1
            verb_index_url = f'{base_url}-{counter}.html?i=^{letter}'
            response = requests.get(verb_index_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            for div in soup.find_all('div', class_='listen-spalte'):
                links = div.find_all('a')
                for a in links:
                    data_sources.append({
                        'word': a.get('title').replace('Konjugation ', ''),
                        'conjugations': {
                            'download_status': False,
                            'url': a.get('href')
                        },
                        'definitions': {
                            'download_status': False,
                            'url': a.get('href').replace('verbformen.de/konjugation','woerter.net/verbs')
                        },
                        'examples': {
                            'download_status': False,
                            'url': a.get('href').replace('.de/konjugation','.de/konjugation/beispiele')
                        },
                        'scrape_status': False
                    })
                if len(links) < 1:
                    links_found = False
    db.data_sources_verblisten.insert_many(data_sources)

if __name__ == "__main__":
    get_data_sources()