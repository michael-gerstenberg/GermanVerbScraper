from mongo_db import connect_mongo_db
import config
import operator
from datetime import datetime
from google_translation import GoogleTranslation


# FOR WINDOWS $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\google_creds.json"
# FOR UNIX export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google_creds.json"
# FOR UNIX export GOOGLE_APPLICATION_CREDENTIALS="/Users/michaelgerstenberg/Projects/OwnPosts/GermanVerbScraper/google_creds.json"




db = connect_mongo_db()

def get_all_translations():
    translations = {}
    for translation_list in db.verbs_de.find({},{'translations':1}):
        for translation in translation_list['translations']:
            if translation['language'] not in translations:
                translations[translation['language']] = []
            translations[translation['language']].append({
                'word': translation['translation'],
                'translations': []
            })
    return translations

def get_german_verbs():
    words = []
    for verb in db.verbs_de.find({},{'word':1}):
        words.append({
            'word': verb['word'],
            'language': 'de',
            'translations': []
        })
    return words

def add_translations_to_db(language_code, translations):
    collection_name = 'google_translations_' + language_code
    db[collection_name].drop()
    db[collection_name].insert_many(translations)

def get_google_translation_collections():
    collections = []
    for collection in db.list_collection_names():
        if "google_translations_" in collection:
            collections.append(collection)
    return collections

def get_translations_from_google(source_language_code):
    collection_name = 'google_translations_' + source_language_code
    source_words = []
    for word in db[collection_name].find({'translations':[]}).limit(100):
        source_words.append(word['word'])
    # if not source_words:
    if len(source_words) < 1:
        return
    translated_words = call_google_api(source_language_code, source_words)
    if len(source_words) != len(translated_words):
        print('#ERROR# Lists not same length')
        return
    for i in zip(source_words, translated_words):
        add_translation_to_document(source_language_code, i[0], 'th', i[1])

def add_translation_to_document(source_language_code, source_word, target_language_code, result_word):
    collection_name = 'google_translations_' + source_language_code
    db[collection_name].update_one(
        {
            'word':source_word
        },
        {
            "$addToSet": {
                "translations": {
                    'language': target_language_code,
                    'word': result_word
                }
            }
        }
    )

def create_google_translation_collections():
    translations = get_all_translations()
    translations['de'] = get_german_verbs()
    for language_code in translations.keys():
        print('language_code: ' + language_code)
        list_without_duplicates = [i for n, i in enumerate(translations[language_code]) if i not in translations[language_code][n + 1:]]
        add_translations_to_db(language_code, list_without_duplicates)

# estimation michi: 3 Mio
# estimation robin: 23 Mio
# 40.156 characters
def calculate_sum_signs():
    sum = 0
    collections = get_google_translation_collections()
    for collection in collections:
        print(collection)
        for x in db[collection].find({},{'word':1}):
            sum += len(x['word'])
    print(sum)

if __name__ == "__main__":

    source_language_code = 'de'
    source_word = 'essen'
    target_language_code = 'th'
    print(GoogleTranslation(source_language_code, source_word, target_language_code).translation_result)



    # for i in range(5):
    #     collections = get_google_translation_collections()
    #     for collection in collections:
    #         language_code = collection.split('google_translations_')[1]
    #         print(language_code)
    #         get_translations_from_google(language_code)

    # 01: create_google_translation_collections()
    # XX: calculate_sum_signs()
