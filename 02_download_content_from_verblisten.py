# there could be something added to be able to scrape it again and again
# include a date when it was downloaded the last time and when it was scraped the last time ...


import mechanicalsoup
import requests
import string
import shutil
import time
from bs4 import BeautifulSoup
from captcha import solve_captcha_netzverb
from mongo_db import connect_mongo_db
from pathlib import Path
from datetime import datetime

class NetzverbPageDownload:

    def __init__(self, id, wordtype, component):
        self.component = component
        self.wordtype = wordtype
        self.collection_name = 'netzverb_' + wordtype
        self.db_collection = self.connect_db()
        self.document = self.get_document(id)
        self.url = self.document['components'][component]['url']
        if self.document:
            self.download_content_captcha_safe()
            self.save_file()
            self.mark_page_as_downloaded()
            
    def connect_db(self):
        db = connect_mongo_db()
        return db.sources[self.collection_name]

    def get_document(self, id):
        if self.db_collection.count_documents({'_id':id}) == 1:
            self.document = self.db_collection.find_one({'_id':id})
            #print(self.document)
            return self.db_collection.find_one({'_id':id})
        return False

    def download_content_captcha_safe(self):
        unsuccessful = True
        while (unsuccessful):
            if self.download_content():
                unsuccessful = False
            else:
                captcha_is_failing = True
                while(captcha_is_failing):
                    try:
                        if 'verbformen.de' in self.url:
                            image_url = 'https://www.verbformen.de/zugriffe/captcha.png'
                        elif 'woerter.net' in self.url:
                            image_url = 'http://www.woerter.net/zugriffe/captcha.png'
                        elif 'verben.de' in self.url:
                            image_url = 'https://www.verben.de/zugriffe/captcha.png'
                        solve_captcha_netzverb(self.url, image_url)
                        captcha_is_failing = False
                    except:
                        captcha_is_failing = True
                        print('Captcha solving failed. Trying again ...')
                        time.sleep(5)

        # the certificate of that website is not valid anymore
        # todo: $$$ change the download uri from definitions to this one: 
        #           https://www.verben.de/verben/essen.htm
        # if self.component == 'definitions':
        #     self.document[self.component]['url'] = self.document[self.component]['url'].replace('https', 'http')
        # should be brought to the 01 where the links are get ...

    def download_content(self):
        # here remove the request_is_Failing ... put into other 
        print('Downloading ' + self.component + ' from ' + self.url)
        request_is_failing = True
        while(request_is_failing):
            try:
                self.response = requests.get(self.url)
                request_is_failing = False
            except:
                print('Page request failed. Trying again ...')
                time.sleep(5)
                request_is_failing = True
        soup = BeautifulSoup(self.response.content, 'html.parser')
        return False if soup.title.string == "Zugriffe" else True

    def save_file(self):
        file_name = self.url.split('/')[-1]
        #print(f'data_sources/netzverb/{self.wordtype}/{self.component}/{file_name}')
        with open(f'data_sources/netzverb/{self.wordtype}/{self.component}/{file_name}', 'w') as f:
            f.write(self.response.text)

    def mark_page_as_downloaded(self):
        download_status_path = 'components.' + self.component + '.download_status'
        download_date_path = 'components.' + self.component + '.downloaded_date'
        self.db_collection.update_one({
            '_id': self.document['_id']
        }, {
            '$set':{
                download_status_path: True,
                download_date_path: datetime.now()
            }
        })

    # def handle_captcha(self, url):
    #     image_url = 'https://www.verbformen.de/zugriffe/captcha.png'
    #     if "woerter.net" in url:
    #         image_url = 'http://www.woerter.net/zugriffe/captcha.png'
    #     filename = 'captcha.png'
    #     r = requests.get(image_url, stream = True)
    #     if r.status_code == 200:
    #         r.raw.decode_content = True
    #         with open(filename,'wb') as f:
    #             shutil.copyfileobj(r.raw, f)
    #         print('Captcha is getting solved...')
    #         answer = solve_captcha('captcha.png')
    #         browser = mechanicalsoup.StatefulBrowser()
    #         browser.open(url)
    #         # browser.select_form().print_summary()
    #         browser.select_form()
    #         try:
    #             browser["captcha"] = answer
    #         except:
    #             return
    #         browser.submit_selected()
    #         return
    #     else:
    #         print('Image couldn\'t be retrieved. Trying again ...')
    #         return


#wtf why are verbs in substantives?

def main():
    db = connect_mongo_db()
    wordtypes = {
        'substantives': ['declensions', 'definitions']
    }
    for wordtype, components in wordtypes.items():
        collection_name = 'netzverb_' + wordtype
        for component in components:
            Path(f'data_sources/netzverb/{wordtype}/{component}/').mkdir(parents=True, exist_ok=True)
            component_path = 'components.' + component + '.download_status'
            for word in db.sources[collection_name].find({component_path: False},{'_id': 1}).limit(100000):
                NetzverbPageDownload(word['_id'], wordtype, component)

if __name__ == "__main__":
    main()
