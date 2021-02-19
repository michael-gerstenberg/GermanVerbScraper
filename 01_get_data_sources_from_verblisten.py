import requests
import time
import string
from bs4 import BeautifulSoup
from mongo_db import connect_mongo_db
from captcha import solve_captcha_netzverb

db = connect_mongo_db()

def get_verb_data_sources():
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
    db.sources.verblisten_verbs.insert_many(data_sources)

def get_substantives_data_sources(base_url = 'https://www.verben.de/suche/substantive/'):
    print(base_url)
    data_sources = []
    verb_index_url = base_url
    response = requests.get(verb_index_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    while(soup.title.string == "Zugriffe"):
        print('solve captcha')
        try:
            solve_captcha_netzverb('https://www.verben.de/suche/substantive/', 'https://www.verben.de/zugriffe/captcha.png')
            response = requests.get(verb_index_url)
            soup = BeautifulSoup(response.content, 'html.parser')
        except:
            time.sleep(5)

    for div in soup.find_all('div', class_='wTrf'):
        link = div.get('onclick')
        if link is not None:
            data_sources.append({
                #'word': div.find_all('span')[2].find('q').replace('<q>', '').replace('</q>', ''),
                'url': div.get('onclick').replace('window.location=', 'https://www.verben.de').replace("'", ''),
                'download_status': False,
                'scrape_status': False,
                'license': 'CC-BY-SA 3.0',
                'letter': base_url.split('https://www.verben.de/suche/substantive/?w=')[1]
            })
        else:
            further_link = 'https://www.verben.de' + div.find('a', href=True)['href']
            data_sources += get_substantives_data_sources(further_link)
    return data_sources
    


def get_adj_adv_data_sources(base_url = 'https://www.verbformen.de/suche/deklination/adjektive/?w=a'):
    print(base_url)
    data_sources = []
    verb_index_url = base_url
    response = requests.get(verb_index_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    while(soup.title.string == "Zugriffe"):
        print('solve captcha')
        try:
            solve_captcha_netzverb('https://www.verbformen.de/suche/deklination/adjektive/', 'https://www.verbformen.de/zugriffe/captcha.png')
            response = requests.get(verb_index_url)
            soup = BeautifulSoup(response.content, 'html.parser')
        except:
            time.sleep(5)

    for a in soup.find_all('a', class_='vSuchWrt'):
        link = 'https://www.verbformen.de' + a.get('href')
        if '?w=' not in link:
            data_sources.append({
                'url': link,
                'download_status': False,
                'scrape_status': False,
                'license': 'CC-BY-SA 3.0',
                'letter': base_url.split('https://www.verbformen.de/suche/deklination/adjektive/?w=')[1]
            })
        else:
            further_link = link
            data_sources += get_adj_adv_data_sources(further_link)
    return data_sources

def check_doubles():
    for v in db.sources.verblisten_adj_adv.find({},{'_id':1, 'url':1}):
        if db.sources.verblisten_adj_adv.count_documents({'url': v['url']}) > 1:
            db.sources.verblisten_adj_adv.delete_one({'_id':v['_id']})

if __name__ == "__main__":

    # letters = "abcdefghijklmnopqrstuvwxyz"
    # for letter in letters:
    #     print(letter)
    #     if db.sources.verblisten_adj_adv.count_documents({'letter': letter}) < 1:
    #         db.sources.verblisten_adj_adv.insert_many(
    #             get_adj_adv_data_sources(f'https://www.verbformen.de/suche/deklination/adjektive/?w={letter}')
    #         )
    

    letters = "abcdefghijklmnopqrstuvwxz"
    for letter in letters:
        print(letter)
        if db.sources.verblisten_substantives.count_documents({'letter': letter}) < 1:
            db.sources.verblisten_substantives.insert_many(
                get_substantives_data_sources(f'https://www.verben.de/suche/substantive/?w={letter}')
            )
    #get_verb_data_sources()