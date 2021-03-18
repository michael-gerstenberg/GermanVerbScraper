# make it letter oriented


# in the article: pip dnspython, requests
from datetime import datetime


# there could be something added to be able to scrape it again and again
import requests
import time
import copy
import string
from bs4 import BeautifulSoup
from mongo_db import connect_mongo_db
# from captcha import solve_captcha_netzverb
# from netzverb_functions import get_collection_name

from netzverb_functions import download_page_content_captcha_safe
from netzverb_functions import get_collection_name
from netzverb_functions import get_word_with_real_umlaut

from netzverb_functions import get_page

#wtf why are verbs in substantives?


db_connect = connect_mongo_db()
db = db_connect['sources']

def get_words_from_documents(documents):
    words = []
    for document in documents:
        words.append(document['word'])
    return words

def get_unsynced_words(available_words, words):
    new_words = []
    for word in words:
        if word['word'] not in available_words:
            new_words.append(word)
    return new_words

def remove_double_documents_by_word(documents):
    unique_documents = []
    words = []
    for document in documents:
        if document['word'] not in words:
            words.append(document['word'])
            unique_documents.append(document)
    return unique_documents

# only for verbs
def update_pages(wordtype):
    pages_from_db_count = db[get_collection_name(wordtype)].count_documents({})
    pages_from_db = db[get_collection_name(wordtype)].find({},{'word':1})
    pages_from_netzverb = get_all_pages(wordtype)
    if pages_from_db_count > 0:
        new_words = get_unsynced_words(get_words_from_documents(pages_from_db), pages_from_netzverb)
        if len(new_words) > 0:
            db[get_collection_name(wordtype)].insert_many(new_words)
        else:
            print(f'There are no new {wordtype}.')
    else:
        db[get_collection_name(wordtype)].insert_many(pages_from_netzverb)
        print(f'Collection netzverb_{wordtype} is empty, all new {wordtype} added.')




def get_all_pages(wordtype):
    # different for wordtype
    base_url = 'https://www.verblisten.de/listen/verben/anfangsbuchstabe/vollstaendig'
    alphabet = 'abcdefghijklmnopqrstuvwxyzäöü'
    alphabet = 'c'
    data_sources = []
    for letter in alphabet:
        if wordtype == 'verbs':
            base_url = 'https://www.verblisten.de/listen/verben/anfangsbuchstabe/vollstaendig'
            data_sources.extend(get_all_verb_pages_by_letter(base_url, letter))

        elif wordtype == 'adjectives':
            print(letter)
            # data_sources.extend(get_adjectives_index_by_letter(wordtype, letter))
        #             base_url = 'https://www.verblisten.de/listen/verben/anfangsbuchstabe/vollstaendig'
        # data_sources.extend(get_all_adjective_pages_by_letter(base_url, letter))
    return data_sources


def get_all_verb_pages_by_letter(base_url, letter):
    page_urls = []
    counter = 0
    links_found = True
    while links_found:
        counter+=1
        url = f'{base_url}-{counter}.html?i=^{letter}'
        print(url)
        new_pages = scrape_verb_index_page(url)
        page_urls += new_pages
        if len(new_pages) < 1:
            return page_urls
    return page_urls

def scrape_verb_index_page(url):
    page_urls = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    for div in soup.find_all('div', class_='listen-spalte'):
        links = div.find_all('a')
        for a in links:
            #print(a.get('href'))
            page_urls.append({
                'word': a.get('title').replace('Konjugation ', ''),
                'pages': [
                    {
                        'component': 'conjugations',
                        'downloaded': False,
                        'scraped': False,
                        'url': a.get('href')
                    },{
                        'component': 'definitions',
                        'downloaded': False,
                        'scraped': False,
                        'url': a.get('href').replace('verbformen.de/konjugation','woerter.net/verbs')
                    },{
                        'component': 'examples',
                        'downloaded': False,
                        'scraped': False,
                        'url': a.get('href').replace('.de/konjugation','.de/konjugation/beispiele')
                    },
                ],
                'license': 'CC-BY-SA 3.0',
            })
    return page_urls





# remove deklination/adjektive from subsctantives
# here there are two pages, but only one is visible here
# https://www.verbformen.de/deklination/substantive/Pizza.htm
# https://www.verben.de/substantive/Pizza.htm
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
                'downloaded': False,
                'scraped': False,
                'license': 'CC-BY-SA 3.0',
                'letter': base_url.split('https://www.verben.de/suche/substantive/?w=')[1]
            })
        else:
            further_link = 'https://www.verben.de' + div.find('a', href=True)['href']
            data_sources += get_substantives_data_sources(further_link)
    return data_sources




def update_adjectives(letter):
    wordtype = 'adjectives'
    pages_from_db_count = db[get_collection_name(wordtype)].count_documents({})
    pages_from_netzverb = remove_double_documents_by_word( get_adjectives_index_by_letter(wordtype, letter) )
    if pages_from_db_count > 0:
        pages_from_db = db[get_collection_name(wordtype)].find({},{'word':1})
        new_words = get_unsynced_words(get_words_from_documents(pages_from_db), pages_from_netzverb)
        if len(new_words) > 0:
            db[get_collection_name(wordtype)].insert_many(new_words)
        else:
            print(f'There are no new {wordtype}.')
    else:
        db[get_collection_name(wordtype)].insert_many(pages_from_netzverb)
        print(f'Collection netzverb_{wordtype} is empty, all new {wordtype} added.')




def get_adjectives_index_by_letter(wordtype = 'adjectives', letter = 'a'):

    indexes_from_db_count = db.netzverb_indexes.count_documents({
        'wordtype': wordtype,
        'letter': letter,
    })
    if indexes_from_db_count > 0:
        print(f'Words beginning with {letter} are already up to date.')
        return []
    
    
    
    data_sources = []
    # wordtype could be extracted
    base_url = 'https://www.verbformen.de/suche/deklination/adjektive/?w='
    url = base_url + letter
    # print(url)
    page_content = download_page_content_captcha_safe(url)

    db.netzverb_indexes.update_one(
        {
            "wordtype": wordtype,
            "url": url,
            "letter": url.split("https://www.verbformen.de/suche/deklination/adjektive/?w=")[1]
        },
        {
            "$set": {
                "last_scraped": datetime.now(),
            }
        },
        upsert = True
    )




# if not too old, the following can be skipped. thats the purpose of buffering the urls


    for a in page_content.find_all('a', class_='vSuchWrt'):
        link = 'https://www.verbformen.de' + a.get('href')
        
        if '?w=' not in link and '?i=' not in link:
            data_sources.append({
                'word': get_word_with_real_umlaut(link.replace('https://www.verbformen.de/deklination/adjektive/', '').replace('.htm', '')),
                'pages': [
                    {
                        'component': 'positive',
                        'downloaded': False,
                        'scraped': False,
                        'url': link
                    },{
                        'component': 'comparative',
                        'downloaded': False,
                        'scraped': False,
                        'url': link.replace('.htm','_komp.htm')
                    },{
                        'component': 'superlative',
                        'downloaded': False,
                        'scraped': False,
                        'url': link.replace('.htm','_sup.htm')
                    },
                ],
                'license': 'CC-BY-SA 3.0',
            })
        else:
            if 'verblisten.de' not in link:
                further_link = link.split(base_url)[1]
                data_sources += get_adjectives_index_by_letter(wordtype, further_link)
    return data_sources



def check_doubles_opt():
    db = connect_mongo_db()
    links_counter = {}
    for w in db.sources.verblisten_substantives.find({},{'url':1}):
        if w['url'] not in links_counter:
            links_counter[w['url']] = 0
        links_counter[w['url']] += 1

#    print(len(links_counter.keys()))

    for link, counter in links_counter.items():
        if counter > 1:
            quantity_to_del = counter - 1
            while quantity_to_del > 0:
                quantity_to_del -= 1
                db.sources.verblisten_substantives.delete_one({'url':link})


if __name__ == "__main__":
    # update_pages('verbs')
    # update_adjectives('e')

    url = 'https://www.verbformen.de/deklination/substantive/Fussel_fem.htm#Steckbrief'
    get_page(url)


    # data = get_adjectives_index_by_letter('c')
    # print(data)

    # letters = "abcdefghijklmnopqrstuvwxyz"
    # letters = "c"
    # for letter in letters:
    #     print(letter)
    #     if db.sources.netzverb_adjectives.count_documents({'letter': letter}) < 1:
    #         db.sources.netzverb_adj_adv.insert_many(
    #             get_adjectives_data_sources(f'https://www.verbformen.de/suche/deklination/adjektive/?w={letter}')
    #         )
    

    # letters = "abcdefghijklmnopqrstuvwxz"
    # for letter in letters:
    #     print(letter)
    #     if db.sources.verblisten_substantives.count_documents({'letter': letter}) < 1:
    #         
    
    #get_verb_data_sources()