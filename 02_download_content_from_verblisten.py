import mechanicalsoup
import requests
import string
import shutil
import time
from bs4 import BeautifulSoup
from captcha import solve_captcha
from mongo_db import connect_mongo_db
from pathlib import Path

class VerblistenPageDownload:

    def __init__(self, verb, component):
        self.component = component
        self.word = self.get_verb(verb)
        self.db_collection = self.connect_db()
        if self.word:
            self.download_content_captcha_safe()
            self.save_file()
            self.mark_page_as_downloaded()
            
    def connect_db(self):
        db = connect_mongo_db()
        return db.sources.verblisten

    def get_verb(self, verb):
        if self.db_collection.count_documents({'word':verb}) == 1:
            return self.db_collection.find_one({'word':verb})
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
                        self.handle_captcha(self.query[self.component]['url'])
                        captcha_is_failing = False
                    except:
                        captcha_is_failing = True
                        print('Captcha solving failed. Trying again ...')
                        time.sleep(5)

        # the certificate of that website is not valid anymore
        # todo: $$$ change the download uri from definitions to this one: 
        #           https://www.verben.de/verben/essen.htm
        # if self.component == 'definitions':
        #     self.query[self.component]['url'] = self.query[self.component]['url'].replace('https', 'http')
    def download_content(self):
        # here remove the request_is_Failing ... put into other 
        print('Downloading ' + self.component + ' from ' + self.query[self.component]['url'])
        request_is_failing = True
        while(request_is_failing):
            try:
                self.response = requests.get(self.query[self.component]['url'])
                request_is_failing = False
            except:
                print('Page request failed. Trying again ...')
                time.sleep(5)
                request_is_failing = True
        soup = BeautifulSoup(self.response.content, 'html.parser')
        return False if soup.title.string == "Zugriffe" else True

    def save_file(self):
        with open(f'data_sources/verblisten/{self.component}/{self.query["word"]}.htm', 'w') as f:
            f.write(self.response.text)
        
    def mark_page_as_downloaded(self):
        self.db_collection.update_one({'_id': self.query['_id']}, {'$set':{self.component + '.download_status': True}})

    def handle_captcha(self, url):
        image_url = 'https://www.verbformen.de/zugriffe/captcha.png'
        if "woerter.net" in url:
            image_url = 'http://www.woerter.net/zugriffe/captcha.png'
        filename = 'captcha.png'
        r = requests.get(image_url, stream = True)
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(filename,'wb') as f:
                shutil.copyfileobj(r.raw, f)
            print('Captcha is getting solved...')
            answer = solve_captcha('captcha.png')
            browser = mechanicalsoup.StatefulBrowser()
            browser.open(url)
            # browser.select_form().print_summary()
            browser.select_form()
            try:
                browser["captcha"] = answer
            except:
                return
            browser.submit_selected()
            return
        else:
            print('Image couldn\'t be retrieved. Trying again ...')
            return

def main():
    db = connect_mongo_db()
    components = ['conjugations', 'examples', 'definitions']
    for component in components:
        Path('data_sources/verblisten/' + component).mkdir(parents=True, exist_ok=True)
        for v in db.sources.verblisten.find({component + '.download_status':False},{'word':1}):
            VerblistenPageDownload(v['word'], component)

if __name__ == "__main__":
    main()