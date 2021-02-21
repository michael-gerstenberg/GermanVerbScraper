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

    def __init__(self, word, wordtype, component = None):
        self.component = component
        self.wordtype = wordtype
        self.db = self.connect_db()
        if self.wordtype == "verb":
            self.word = self.get_verb(word)
        elif self.wordtype == "adj_adv":
            self.word = self.get_adj_adv(word)
        elif self.wordtype == "substantive":
            self.word = self.get_substantive(word)
        if self.word:
            self.download_content_captcha_safe()
            self.save_file()
            self.mark_page_as_downloaded()
            
    def connect_db(self):
        db = connect_mongo_db()
        return db.sources

    def get_verb(self, word):
        if self.db.verblisten.count_documents({'word':word}) == 1:
            self.query = self.db.verblisten.find_one({'word':word})
            return self.db.verblisten.find_one({'word':word})
        return False

    def get_adj_adv(self, id):
        if self.db.verblisten_adj_adv.count_documents({'_id':id}) == 1:
            self.query = self.db.verblisten_adj_adv.find_one({'_id':id})
            return self.db.verblisten_adj_adv.find_one({'_id':id})
        return False
    
    def get_substantive(self, id):
        if self.db.verblisten_substantives.count_documents({'_id':id}) == 1:
            self.query = self.db.verblisten_substantives.find_one({'_id':id})
            return self.db.verblisten_substantives.find_one({'_id':id})
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
                        # make more beautiful with the different cases (verbs ...)
                        image_url = 'https://www.verbformen.de/zugriffe/captcha.png'
                        if self.wordtype == "verb":
                            url = self.query[self.component]['url']
                            if "woerter.net" in self.query[self.component]['url']:
                                image_url = 'http://www.woerter.net/zugriffe/captcha.png'
                        elif self.wordtype == "substantive":
                            image_url = 'https://www.verben.de/zugriffe/captcha.png'
                            url = self.query['url']
                        else:
                            url = self.query['url']
                        solve_captcha_netzverb(url, image_url)
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
        if self.wordtype == "verbs":    
            print('Downloading ' + self.component + ' from ' + self.query[self.component]['url'])
        else:
            print('Downloading from ' + self.query['url'])

        request_is_failing = True
        while(request_is_failing):
            try:
                if self.wordtype == "verbs":
                    self.response = requests.get(self.query[self.component]['url'])
                else:
                    self.response = requests.get(self.query['url'])
                request_is_failing = False
            except:
                print('Page request failed. Trying again ...')
                time.sleep(5)
                request_is_failing = True
        soup = BeautifulSoup(self.response.content, 'html.parser')
        return False if soup.title.string == "Zugriffe" else True

    def save_file(self):
        if self.wordtype == "verbs":
            with open(f'data_sources/netzverb/verbs/{self.component}/{self.query["word"]}.htm', 'w') as f:
                f.write(self.response.text)
        elif self.wordtype == "substantive":
            word = self.query['url'].replace('https://www.verben.de/substantive/', '')
            with open(f'data_sources/netzverb/substantives/{word}', 'w') as f:
                f.write(self.response.text)

    def mark_page_as_downloaded(self):
        if self.wordtype == "verb":
            self.db.verblisten.update_one({
                '_id': self.query['_id']
            }, {
                '$set':{
                    self.component + '.download_status': True,
                    'downloaded_date': datetime.now()
                }
            })
        elif self.wordtype == "adj_adv":
            self.db.verblisten_adj_adv.update_one({
                '_id': self.query['_id']
            }, {
                '$set':{
                    'download_status': True,
                    'downloaded_date': datetime.now()
                }
            })
        elif self.wordtype == "substantive":
            self.db.verblisten_substantives.update_one({
                '_id': self.query['_id']
            }, {
                '$set':{
                    'download_status': True,
                    'downloaded_date': datetime.now()
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

def check_strange():

    # better check if something like a link makes sense ...
    db = connect_mongo_db()

    for w in db.sources.verblisten_substantives.find({"url":{"$regex": u"/artikel-pronomen/"}},{'_id':1, 'url':1}):
        print(w['url'])
        # if db.sources.verblisten_adj_adv.count_documents({'url': w['url']}) > 1:
        #     print(w['url'])
        db.sources.verblisten_substantives.delete_one({'_id':w['_id']})



#wtf why are verbs in substantives?

def main():
    
    check_strange()

    db = connect_mongo_db()

    # subst
    Path('data_sources/netzverb/substantives/').mkdir(parents=True, exist_ok=True)
    for w in db.sources.verblisten_substantives.find({'download_status':False},{'_id':1}).limit(100000).sort("url",1):
        NetzverbPageDownload(w['_id'], 'substantive')

    # adj adv
    Path('data_sources/netzverb/adj_adv/').mkdir(parents=True, exist_ok=True)
    for w in db.sources.verblisten_adj_adv.find({'download_status':False},{'_id':1}).limit(100000):
        NetzverbPageDownload(w['_id'], 'adj_adv')

    # verbs
    components = ['conjugations', 'examples', 'definitions']
    for component in components:
        Path('data_sources/netzverb/verbs/' + component).mkdir(parents=True, exist_ok=True)
        for w in db.sources.verblisten.find({component + '.download_status':False},{'word':1}):
            NetzverbPageDownload(w['word'], 'verb', component)

if __name__ == "__main__":
    main()