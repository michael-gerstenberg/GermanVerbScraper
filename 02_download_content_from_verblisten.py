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

    def __init__(self, verb, directory):
        self.directory = directory
        self.word = self.get_verb(verb)
        self.create_folder()
        self.db_collection = connect_db()
        if self.word:
            self.download_content_captcha_safe()
            self.save_file()
            self.update_document()
            
    def connect_db(self):
        db = connect_mongo_db()
        return db.sources.verblisten

    def create_folder(self):
        Path('data_sources/verblisten/' + self.directory).mkdir(parents=True, exist_ok=True)

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
                        self.handle_captcha(self.query[self.directory]['url'])
                        captcha_is_failing = False
                    except:
                        captcha_is_failing = True
                        print('Captcha solving failed. Trying again ...')
                        time.sleep(5)

    def download_content(self):
        # the certificate of that website is not valid anymore
        if self.directory == 'definitions':
            self.query[self.directory]['url'] = self.query[self.directory]['url'].replace('https', 'http')
        print('Downloading ' + self.directory + ' from ' + self.query[self.directory]['url'])
        request_is_failing = True
        while(request_is_failing):
            try:
                self.response = requests.get(self.query[self.directory]['url'])
                request_is_failing = False
            except:
                print('Page request failed. Trying again ...')
                time.sleep(5)
                request_is_failing = True
        soup = BeautifulSoup(self.response.content, 'html.parser')
        return False if soup.title.string == "Zugriffe" else True

    def save_file(self):
        with open(f'data_sources/verblisten/{self.directory}/{self.query["word"]}.htm', 'w') as f:
            f.write(self.response.text)
        
    def update_document(self):
        self.db_collection.update_one({'_id': self.query['_id']}, {'$set':{self.directory + '.download_status': True}})

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

if __name__ == "__main__":
    db = connect_mongo_db()
    directories = ['conjugations', 'examples', 'definitions']
    for directory in directories:
        for v in db.sources.verblisten.find({directory + '.download_status':False},{'word':1}):
            VerblistenPageDownload(v['word'], directory)
