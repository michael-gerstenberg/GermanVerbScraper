




import time

import requests
from bs4 import BeautifulSoup

from captcha import solve_netzverb_captcha

prefix = 'netzverb'

def get_wordtypes_and_components():
    return {
        'adjectives': ['declensions'],
        'substantives': ['declensions', 'definitions'],
        'verbs': ['conjugations', 'definitions', 'examples'],
    }

def get_collection_name(wordtype):
    return prefix + '_' + wordtype


# how about https://www.verbformen.de/suche/deklination/substantive/?w=bo
def get_page(url, refresh = False):
    # replace all from #
    url = url.split('://')[1]
    url = url.split('#')[0]

    # base url


    folders = url.split('/')[:-1]
    print(folders)
    filename = url.split('/')[-1]
    filename = filename.split('.')[0] + '.htm'

    # if ... add index.html
        
    
    print(filename)


    print(url)

def download_page_content_captcha_safe(url):
    while True:
        page_content = download_page_content(url)
        # the title "Zugriffe" indicates the captcha page
        if page_content.title.string != "Zugriffe":
            return page_content
        else:
            solve_netzverb_captcha(url)

def download_page_content(url):
    print('Downloading ' + url)
    while True:
        try:
            response = requests.get(url)
            return BeautifulSoup(response.content, 'html.parser')
        except:
            print('Page request failed. Trying again ...')
            time.sleep(5)

def get_word_with_real_umlaut(word):
    return word.replace('a3', 'ä').replace('s5', 'ß').replace('o3', 'ö').replace('u3', 'ü')
            
# def get_netzverb_filepath(wordtype, component, filename):
#     return 'sources/netzverb/' + wordtype + '/' + component + '/' + filename + '.htm'

def get_netzverb_structure():
    return {
        'wordtypes': [{
            'name': 'adjectives',
            'indexes': [{
                'url': 'https://www.verbformen.de/deklination/adjektive/?w={letter}',
                'captcha_url': '',
                'placeholder': ['letter'],
                'type': 'nested',
            }],
            'components': [{
                'name': 'declensions_positiv',
                'availability': 'always',
                'url': 'https://www.verbformen.de/deklination/adjektive/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'declensions_comparative',
                'availability': 'partial',
                'url': 'https://www.verbformen.de/deklination/adjektive/{word}_komp.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'declensions_superlative',
                'availability': 'partial',
                'url': 'https://www.verbformen.de/deklination/adjektive/{word}_sup.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            }],
        },{
            'name': 'articles',
            'indexes': [{
                'url': 'https://www.verbformen.de/deklination/artikel/?w=',
                'captcha_url': '',
                'placeholder': [],
                'type': 'nested',
            }],
            'components': [{
                'name': 'overview',
                'availability': 'always',
                'url': 'https://www.verbformen.de/deklination/artikel/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            }],
        },{
            'name': 'pronouns',
            'indexes': [{
                'url': 'https://www.verbformen.de/deklination/pronomen/?w=',
                'captcha_url': '',
                'placeholder': [],
                'type': 'nested',
            }],
            'components': [{
                'name': 'overview',
                'availability': 'always',
                'url': 'https://www.verbformen.de/deklination/pronomen/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            }]
        },{
            'name': 'substantives',
            'indexes': [{
                'url': 'https://www.verbformen.de/deklination/substantive/?w={letter}',
                'captcha_url': '',
                'placeholder': ['letter'],
                'type': 'nested',
            }],
            'components': [{
                'name': 'declensions',
                'availability': 'always',
                'url': 'https://www.verbformen.de/deklination/substantive/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'declensions_masculine',
                'availability': 'partial',
                'url': 'https://www.verbformen.de/deklination/substantive/{word}_mask.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'declensions_feminine',
                'availability': 'partial',
                'url': 'https://www.verbformen.de/deklination/substantive/{word}_fem.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'declensions_neuter',
                'availability': 'always',
                'url': 'https://www.verbformen.de/deklination/substantive/{word}_neut.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            # the following page doesn't contain additional data
            # },{
            #     'name': 'overview',
            #     'availability': 'always',
            #     'url': 'https://www.verben.de/substantive/{word}.htm',
            #     'placeholder': ['word'],
            #     'captcha_url': '',
            },{
                'name': 'definitions',
                'availability': 'always',
                'url': 'https://www.verben.de/substantive/bedeutungen/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'translations',
                'availability': 'always',
                'url': 'https://www.verben.de/substantive/uebersetzungen/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            }],
        },{
            'name': 'verbs',
            'indexes': [{
                'url': 'https://www.verbformen.com/conjugation/?w={letter}',
                'captcha_url': '',
                'placeholder': ['letter'],
                'type': 'nested',
            },{
                'url': 'https://www.verblisten.de/listen/verben/anfangsbuchstabe/vollstaendig-{counter}.html?i=^{letter}',
                'captcha_url': '',
                'placeholder': ['letter', 'counter'],
                'type': 'list',
            }],
            'components': [{
                'name': 'definitions',
                'availability': 'always',
                'url': 'https://www.verben.de/verben/bedeutungen/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'usage',
                'availability': 'always',
                'url': 'https://www.verben.de/verben/verwendungen/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            },{
                'name': 'conjugations',
                'availability': 'always',
                'url': 'https://www.verbformen.de/konjugation/{word}.htm',
                'placeholder': ['word'],
                'captcha_url': '',
            # the following page doesn't contain additional data
            # },{
            #     'name': 'overview',
            #     'availability': 'always',
            #     'url': 'https://www.verben.de/verben/{word}.htm',
            #     'placeholder': ['word'],
            #     'captcha_url': '',
            }],
        }],
        'exceptions': {
            '404': 'Uups ... Seite wurde nicht gefunden  (HTTP 404) ',
            'captcha': 'Zugriffe',
        },
        'alphabet': 'abcdefghijklmnopqrstuvwxyzäöü',
        'replacements': {
            'a3': 'ä',
            'u3': 'ü',
            'o3': 'ö',
            's5': 'ß',
        }
    }