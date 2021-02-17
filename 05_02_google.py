import json
import os
from google.cloud import translate
from mongo_db import connect_mongo_db, connect_to_mongo_db
import config
import operator
from datetime import datetime
import bson.json_util as bson_jo

# FOR WINDOWS $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\google_creds.json"
# FOR UNIX export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google_creds.json"
# FOR UNIX export GOOGLE_APPLICATION_CREDENTIALS="/Users/michaelgerstenberg/Projects/OwnPosts/GermanVerbScraper/google_creds.json"

# todo:      the calculation is not correct, if there are already thai results. then the sum needs to be subsctracted by the sum of thai translations

class GoogleThaiTranslations:
    def __init__(self, word):
        self.connect_db()
        self.word = self.get_verb(word)
        self.available_translations = []
        self.missing_translations = []
        self.get_available_translations()
        
        
        
        # self.translations = self.cluster_translations_by_languages()
        # self.thai_translations = self.get_thai_translations()
        # self.thai_translations_summary = self.summarize_translations()
        # self.best_translations = self.calculate_translation_score()
        # self.add_to_document()
        # self.update_source_document()

    def connect_db(self):
        self.db = connect_mongo_db()

    def get_verb(self, word):
        return self.db.verbs_de.find_one({'word':word})





    def add_translation_to_data_source(self, source_lang, source_word, target_lang, result_word):
        query = self.db.data_source_google_api.count_documents({
            'word': source_word,
            'language': source_lang,
            'translated_from': {
                'word':result_word,
                'language':target_lang
            }
        })
        if query < 1:
            self.db.data_source_google_api.insert_one(
                {
                    'word':source_word,
                    'language':source_lang,
                    'translated_from': {
                        'word':result_word,
                        'language':target_lang
                    },
                    'date':datetime.now()
                }
            )

    def get_translations_from_google_api(self, source_language_code, words):
        project_id = "thaiwords" # for second google account => genial-runway-305023
        client = translate.TranslationServiceClient()
        location = "global"
        parent = f"projects/{project_id}/locations/{location}"
        response = client.translate_text(
                parent= parent,
                contents= words,
                mime_type= "text/plain",  # mime types= text/plain, text/html
                source_language_code= source_language_code,
                target_language_code= "th",
        )
        new_list = []
        # Save the translation for each input text provided
        for translation in response.translations:
            new_list.append(translation.translated_text)
        return new_list

    def get_translation_from_data_scource():
        return False

    def cluster_translations_by_languages(self):
        clustered_translations = {
            'de': [self.word['word']]
        }
        for translation in self.word['translations']:
            if translation['language'] not in clustered_translations.keys():
                clustered_translations[translation['language']] = []
            clustered_translations[translation['language']].append(translation['translation'])
        return clustered_translations

    def get_thai_translations(self):
        thai_translations = []
        for language in self.translations.keys():
            if language != 'th':
                thai_translations += self.translate_with_google_api(language, self.translations[language])
        return thai_translations

    def summarize_translations(self):
        translation_summary = {word:self.thai_translations.count(word) for word in self.thai_translations}
        return dict(sorted(translation_summary.items(), key=lambda item: item[1], reverse=True))

    def calculate_translation_score(self):
        # calculate sum without thai translations
        sum_translations = len(self.word['translations'])+1
        sum_translations_used = 0
        best_translations = []
        quote = 0

        for word, count in self.thai_translations_summary.items():
            sum_translations_used += count
            best_translations.append({
                'language': 'th',
                'source': 'googleAPI',
                'license': 'paid',
                'translation': word
            })
            quote += count/sum_translations
            #if quote > 0.618:
            if quote > 1:
                break

        for counter, w  in enumerate(best_translations):
            best_translations[counter]['score'] = round(self.thai_translations_summary[w['translation']] / sum_translations_used, 2)

        return best_translations

        # if self.direct_translation not in best_translations:
        #     print(f"Obacht, denn {self.direct_translation} is not in the result list")

    def add_to_document(self):
        for t in self.best_translations:
            self.db.verbs_de.update_one(
                {
                    'word':self.word['word']
                },
                {
                    "$addToSet": {
                        "translations": t
                    }
                }
            )

    def translate_with_google_api(self, source_language_code, words, project_id="thaiwords"):
        """Translating Text."""
        client = translate.TranslationServiceClient()
        location = "global"
        parent = f"projects/{project_id}/locations/{location}"
        # Detail on supported types can be found here:
        # https://cloud.google.com/translate/docs/supported-formats
        response = client.translate_text(
                parent= parent,
                contents= words,
                mime_type= "text/plain",  # mime types= text/plain, text/html
                source_language_code= source_language_code,
                target_language_code= "th",
        )
        new_list = []
        # Save the translation for each input text provided
        for translation in response.translations:
            new_list.append(translation.translated_text)
        return new_list


    def update_source_document(self):
        self.db.data_sources_google.update_one({'word': self.word['word']}, {'$set':{'status': True}})








def get_missing_translations_from_google():
    db = connect_mongo_db()
    for v in db.data_sources_google.find({'status':False}).limit(15):
        print(v['word'])
# e.g. the word "abbrechen" gives bad results. Why?
#       best: ยก or 
# ask Noon about the quality!!!
# translate.google.de gives แท้ง -> means "abtreiben, abortion"
# there are also sometimes a bit too much russian translations...
        GoogleThaiTranslations(v['word'])

def create_google_collection():
    db = connect_mongo_db()

    if db.data_sources_google.count_documents() < 1:

        verbs = db.verbs_de.find({},{'word':1})
        verbs_name_only = []
        for verb in verbs:
            verbs_name_only.append({
                'word': verb['word'],
                'status': False,
            })

        db.data_sources_google.insert_many(verbs_name_only)

def import_collections():
    client = connect_to_mongo_db()
    db = client['sources']
    for filename in os.listdir('mongo_db_dumps/sources'):
        with open('mongo_db_dumps/sources/' + filename) as f:
            collection_name = f.name.split('.')[1]
            file_data = bson_jo.loads(f.read())
            db[collection_name].insert_many(file_data)

if __name__ == "__main__":
    # get_missing_translations_from_google()
    import_collections()





# file: sources.google_translation_ar.json