from datetime import datetime
from pathlib import Path
import time

from bs4 import BeautifulSoup
import requests

from captcha import solve_captcha_netzverb
from mongo_db import connect_mongo_db
import netzverb_functions

class NetzverbPageDownload:

    def __init__(self, id, wordtype, component):
        self.component = component
        self.wordtype = wordtype
        self.collection = self.get_collection(get_collection_name(wordtype))
        self.document = self.collection.find_one({'_id':id})
        if self.document:
            self.url = self.document['components'][component]['url']
            self.page_content = self.download_page_content_captcha_safe()
            self.save_file()
            self.mark_page_as_downloaded()

    def get_collection(self):
        db = connect_mongo_db()
        return db.sources[self.collection_name]

    def download_page_content_captcha_safe(self):
        while True:
            page_content = self.download_page_content()
            # the title "Zugriffe" indicates the captcha page
            if page_content.title.string != "Zugriffe":
                return page_content.text
            else:
                solve_netzverb_captcha(self.url)

    def download_page_content(self):
        print('Downloading ' + self.url)
        while True:
            try:
                response = requests.get(self.url)
                return BeautifulSoup(response.content, 'html.parser')
            except:
                print('Page request failed. Trying again ...')
                time.sleep(5)

    def save_file(self, page_content):
        file_name = self.url.split('/')[-1]
        with open(f'data_sources/netzverb/{self.wordtype}/{self.component}/{file_name}', 'w') as f:
            f.write(self.page_content)

    def mark_page_as_downloaded(self):
        download_status_path = 'components.' + self.component + '.downloaded'
        download_date_path = 'components.' + self.component + '.last_download'
        self.db_collection.update_one({
            '_id': self.document['_id']
        }, {
            '$set':{
                download_status_path: True,
                download_date_path: datetime.now()
            }
        })

def get_wordtypes_and_components():
    return {
        'adjectives': ['declensions'],
        'substantives': ['declensions', 'definitions'],
        'verbs': ['conjugations', 'definitions', 'examples'],
    }

def get_collection_name(wordtype):
    return 'netzverb_' + wordtype

def main():
    db = connect_mongo_db()
    wordtypes = get_wordtypes_and_components()
    for wordtype, components in wordtypes.items():
        collection_name = get_collection_name(wordtype)
        for component in components:
            Path(f'data_sources/netzverb/{wordtype}/{component}/').mkdir(parents=True, exist_ok=True)
            component_path = 'components.' + component + '.downloaded'
            for word in db.sources[collection_name].find({component_path: False},{'_id': 1}):
                NetzverbPageDownload(word['_id'], wordtype, component)

if __name__ == "__main__":
    main()
