from bs4 import BeautifulSoup
from mongo_db import connect_mongo_db
from pathlib import Path
from tqdm import tqdm

class WordScrape:

    def __init__(self, word):
        self.word = word
        self.connect_db()
        self.scrape_verb()

    def connect_db(self):
        self.db = connect_mongo_db()

    def scrape_verb(self):
        self.db.verbs_de.insert_one({
            'word': self.word,
            'level': self.scrape_level(),
            'conjugations': self.scrape_conjugations(),
            'examples': self.scrape_examples(),
            'definitions': self.scrape_definitions(),
            'grammar': self.scrape_grammar(),
            'translations': self.scrape_translations(),
            'source': {
                'name': 'verbformen.de',
                'license': 'CC-BY-SA 3.0'
            }
        })
        self.update_document()

    def update_document(self):
        self.db.data_sources_verblisten.update_one({'word': self.word}, {'$set':{'scrape_status': True}})

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
                                "source": 'verbformen.de',
                                "license": 'CC-BY-SA 3.0',
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
                                'name': 'verbformen.de',
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
    for v in tqdm(db.data_sources_verblisten.find({'scrape_status':False},{'word':1})):
        WordScrape(v['word'])

if __name__ == "__main__":
    scrape_missing_files()