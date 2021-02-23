# save order also with the verb documents

from bs4 import BeautifulSoup
from mongo_db import connect_mongo_db
from pathlib import Path
from tqdm import tqdm
import pprint
from datetime import datetime

class NetzverbWordScraper:

    def __init__(self, wordtype, id):
        self.wordtype = wordtype
        self.collection_name = 'netzverb_' + wordtype
        self.db = self.connect_db()
        self.document = self.get_document(id)
        if wordtype == "adj_adv":
            self.scrape_adj_adv()
        elif wordtype == "verbs":
            self.scrape_verb()

    # functions for all wordtypes

    def connect_db(self):
        return connect_mongo_db()

    def get_document(self, id):
        return self.db.sources[self.collection_name].find_one({'_id': id})

    def get_file_content(self, file_name):
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            return soup
        return False

    ## works only for urls directly on root
    def check_if_page_is_valid(self, file_content):
        if file_content.title.string == "503 Service Unavailable":
            self.db.sources[self.collection_name].update_one({
                '_id': self.document['_id']
            }, {
                '$set':{
                    'download_status': False
                }
            })
            return False
        return True

    # Section ADJ ADV

    def scrape_adj_adv(self):
        file_name = 'data_sources/netzverb/adj_adv/declensions/' + self.document['url'].split('/')[-1]
        file_content = self.get_file_content(file_name)
        if file_content and self.check_if_page_is_valid(file_content):
            print(file_name)
            self.db.sources[self.collection_name].update_one({
                '_id': self.document['_id']
            }, {
                '$set':{
                    'word': self.scrape_adj_adv_word(file_content),
                    'scrape_status': True,
                    'scraped_date': datetime.now(),
                    'scraped_content': {
                        'comparisons': self.scrape_adj_adv_comparisons(file_content),
                        'strong_declensions': self.scrape_adj_adv_declensions(file_content, 1),
                        'weak_declensions': self.scrape_adj_adv_declensions(file_content, 2),
                        'mixed_declensions': self.scrape_adj_adv_declensions(file_content, 3),
                        'declension_order': ['nom', 'gen', 'dat', 'acc'],
                    }
                }
            })

    def scrape_adj_adv_word(self, file_content):
        return file_content.title.string.replace('Deklination und Steigerung ', '').replace(' | Alle Formen, Plural, Downloads, Sprachausgabe', '')

    def scrape_adj_adv_comparisons(self, file_content):
        comparisons = file_content.find_all('div', class_='vTxtTbl')
        comparison_rows = comparisons[0].find_all('td')
        return {
            'positive': comparison_rows[0].contents[0],
            'comparative': comparison_rows[1].contents[0],
            'superlative': comparison_rows[2].contents[0],
        }
    
    def scrape_adj_adv_declensions(self, file_content, counter):
        strong_declensions = file_content.find_all('ul')[counter].find_all('li')
        strong_declensions_scraped = {}
        types = ['masculine', 'neutral', 'feminine', 'plural']
        for counter,li in enumerate(strong_declensions):
            strong_declensions_scraped[types[counter]] = str(li).split('\n')[2].split(', ')
        return strong_declensions_scraped

    # Section VERBS

    def scrape_verb(self):
        self.db..update_one({
            '_id': self.document['_id']
        }, {
            '$set':{
                'scrape_status': True,
                'translations': self.scrape_translations(),
                'license': 'CC-BY-SA 3.0'
            }
        })

    # Section Verbs $$$ no clean code!

    def scrape_verb(self):
        # self.db.dict.verbs_de.insert_one({
        #     'word': self.word,
        #     'level': self.scrape_level(),
        #     'conjugations': self.scrape_conjugations(),
        #     'examples': self.scrape_examples(),
        #     'definitions': self.scrape_definitions(),
        #     'grammar': self.scrape_grammar()
        # })
        self.db.sources.verblisten.update_one({
            '_id': self.document['_id']
        }, {
            '$set':{
                'scrape_status': True,
                'translations': self.scrape_translations(),
                'license': 'CC-BY-SA 3.0'
            }
        })

    def scrape_translations(self):
        file_name = 'data_sources/verblisten/conjugations/' + self.word + '.htm'
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            translations = []
            for div in soup.find_all('div'):
                if div.has_attr('lang'):
                    language = div.get("lang")
                    for span in div.find_all('span'):
                        if len(span.contents) > 0 and len(span.contents[0]) > 0:
                            translations.append({
                                "language": div.get("lang"),
                                # "source": 'verbformen.de',
                                # "license": 'CC-BY-SA 3.0',
                                "translation": span.contents[0]
                            })
        return translations

    def scrape_level(self):
        file_name = 'data_sources/verblisten/definitions/' + self.word + '.htm'
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            for section in soup.find_all('section'):
                if 'wNr' in section.get('class'):
                    for b in section.find_all('b'):
                        return b.contents[0]
        return ''

    def scrape_grammar(self):
        file_name = 'data_sources/verblisten/definitions/' + self.word + '.htm'
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            definition = {
                'grammar': {
                    'general':[],
                    'sometimes':[],
                },
                'prepositions_and_context': [],
                'usage': self.scrape_definitions_usage(soup),
                'source': {
                    'name': 'verbformen.de',
                    'license': 'CC-BY-SA 3.0'
                }
            }
            section_count = 0
            for section in soup.find_all('section'):
                section_count += 1
                if section_count == 1:
                    sometimes = False
                    for div in section.find_all('div'):
                        if isinstance(div.get('class'), list) and 'rInf' in div.get('class'):
                            for span in div.find_all('span'):
                                if span.get('title') == 'sometimes also:':
                                    sometimes = True
                                    continue
                                if sometimes == False:
                                    definition['grammar']['general'].append(span.get('title'))
                                else:
                                    definition['grammar']['sometimes'].append(span.get('title'))
                # escape prepositions and context
                if section_count == 1:
                    for div in section.find_all('div'):
                        if div.get('class') is not None and 'wVal' in div.get('class'):
                            for span in div.find_all('span'):
                                if span.get('title'):
                                    definition['prepositions_and_context'].append(span.get('title'))
            return definition
        return ''

    def scrape_definitions(self):
        file_name = 'data_sources/verblisten/definitions/' + self.word + '.htm'
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            definitions = []
            for div in soup.find_all('div'):
                if div.get('class') is not None and 'rAbschnitt' in div.get('class'):
                    for section in div.find_all('section'):
                        definition = {"visible": True}
                        if 'wNr' in section.get('class'):
                            for div in section.find_all('div'):
                                if div.get('class') is not None and ('wBst4' in div.get('class') or 'wBst2' in div.get('class') or 'wBst1' in div.get('class')):
                                    sub_defs = []
                                    for li in div.find_all('li'):
                                        sub_defs.append(li.contents[0].strip())
                                    for a in div.find_all('a'):
                                        sub_defs.append(a.contents[0].strip())
                                    definition[div.h3.contents[0].lower().replace(' ', '_').replace('_(opposite)', '').replace('-', '_')] = sub_defs
                            definition['source'] = {
                                'name': 'verben.de',
                                'license': 'CC-BY-SA 3.0'
                            }
                            definitions.append(definition)
            return definitions
        return ''

    def scrape_definitions_usage(self, soup: BeautifulSoup) -> dict:
        definitions = {}
        for div in soup.find_all('div'):
            if div.get('class') is not None and 'rAbschnitt' in div.get('class'):
                for section in div.find_all('section'):
                    definition = {}
                    if 'wFlx' in section.get('class'):
                        for div in section.find_all('div'):
                            if div.get('class') is not None and 'wBstn' in div.get('class'):
                                for div_inner in div.find_all('div'):
                                    if div_inner.get('class') is not None and 'wBst1' in div_inner.get('class'):
                                        for ul in div_inner.find_all('ul'):
                                            usage = []
                                            for a in ul.find_all('a'):
                                                usage.append(a.get('href').replace('http://www.satzapp.de/?s=', ''))
                                            keyword = div_inner.h3.contents[0].lower().replace(' ', '_').replace('-', '_')
                                            definition[keyword] = usage
                                            if not definitions.get(keyword):
                                                definitions[keyword] = usage
                                            else:
                                                definitions[keyword] += usage
        return definitions

    def scrape_conjugations(self):
        file_name = f'data_sources/verblisten/conjugations/{self.word}.htm'
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            lines = []
            for ul in soup.find_all('ul'):
                if ul.get('class') == ['rLst']:
                    continue
                for li in ul.find_all('li'):
                    lines.append(str(li).split(':\n')[1].split('\n<')[0])
            conjugations = {
                'indicative_active': {
                    'present': lines[0].split(', '),
                    'imperfect': lines[1].split(', '),
                    'perfect': lines[2].split(', '),
                    'plusquamperfect': lines[3].split(', '),
                    'future': lines[4].split(', '),
                    'future_perfect': lines[5].split(', '),
                },
                'subjunctive_active': {
                    'present': lines[6].split(', '),
                    'imperfect': lines[7].split(', '),
                    'perfect': lines[8].split(', '),
                    'plusquamperfect': lines[9].split(', '),
                    'future': lines[10].split(', '),
                    'future_perfect': lines[11].split(', '),
                },
                'conditional_active': {
                    'imperfect': lines[12].split(', '),
                    'plusquamperfect': lines[13].split(', '),
                },
                'imperative_active': {
                    'present': lines[14].split(', '),
                },
                'infinitive_participle_active': {
                    'infinitive_1': lines[15].split(', '),
                    'infinitive_2': lines[16].split(', '),
                    'participle_1': lines[17].split(', '),
                    'participle_2': lines[18].split(', '),
                },
                'source': {
                    'name': 'verbformen.de',
                    'license': 'CC-BY-SA 3.0'
                }
            }
            return conjugations
        return ''

    def scrape_examples(self):
        file_name = f'data_sources/verblisten/examples/{self.word}.htm'
        if Path(file_name).is_file():
            f = open(file_name, "r")
            soup = BeautifulSoup(f.read(), 'html.parser')
            f.close()
            i = 0
            examples = []
            for div in soup.find_all('div'):
                if div.get('class') == ['rAbschnitt']:
                    for tr in div.find_all('tr'):
                        examples.append('')
                        for a in tr.find_all('a'):
                            if a.get('target') == '_blank':
                                examples[i] = a.get('href').replace('http://www.satzapp.de/?s=', '')
                        i += 1
            examples_ordered = {
                'indicative_active': {
                    'present': examples[0:6],
                    'imperfect': examples[6:12],
                    'perfect': examples[12:18],
                    'plusquamperfect': examples[18:24],
                    'future': examples[24:30],
                    'future_perfect': examples[30:36],
                },
                'subjunctive_active': {
                    'present': examples[36:42],
                    'imperfect': examples[42:48],
                    'perfect': examples[48:54],
                    'plusquamperfect': examples[54:60],
                    'future': examples[60:66],
                    'future_perfect': examples[66:72],
                },
                'conditional_active': {
                    'imperfect': examples[72:78],
                    'plusquamperfect': examples[78:84],
                },
                'imperative_active': {
                    'present': examples[84:],
                },
                'source': {
                    'name': 'verbformen.de',
                    'license': 'CC-BY-SA 3.0',
                }
            }
            return examples_ordered
        return ''


def scrape_missing_files():
    db = connect_mongo_db()
    # db.dict.verbs_de.update_many({},{'$set':{'translations':[]}})
    # for v in tqdm(db.sources.verblisten.find({'scrape_status':False},{'_id':1, word':1})):    
    #     NetzverbWordScraper(v['_id'])

# only valid vor adj right now
def scrape_new_files(wordtype):
    db = connect_mongo_db()
    collection_name = 'netzverb_' + wordtype
    for word in db.sources[collection_name].find({'scrape_status':False,'download_status':True},{'_id':1}).sort("url",-1):
        NetzverbWordScraper(wordtype, word['_id'])

if __name__ == "__main__":
    #scrape_missing_files()
    scrape_new_files('adj_adv')