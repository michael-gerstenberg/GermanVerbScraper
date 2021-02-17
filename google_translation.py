from google.cloud import translate
from mongo_db import connect_to_mongo_db

# def call_google_api(source_language_code, words):
#     # project_id = "thaiwords" # 1st google account
#     project_id = "genial-runway-305023" # 2nd google account
#     client = translate.TranslationServiceClient()
#     location = "global"
#     parent = f"projects/{project_id}/locations/{location}"
#     response = client.translate_text(
#         parent= parent,
#         contents= words,
#         mime_type= "text/plain",  # mime types= text/plain, text/html
#         source_language_code= source_language_code,
#         target_language_code= "th",
#     )
#     new_list = []
#     # Save the translation for each input text provided
#     for translation in response.translations:
#         new_list.append(translation.translated_text)
#     return new_list

class GoogleTranslation:

    def __init__(self, source_language_code, source_word, target_language_code):
        self.source_language_code = source_language_code
        self.source_word = source_word
        self.target_language_code = target_language_code
        self.connect_to_mongo_db()
        self.get_translation_from_google()

    def connect_to_mongo_db(self):
        self.db = connect_to_mongo_db()

    def get_translation_from_google(self):
        translation_result = self.get_translation_from_google_collection()
        if translation_result != False:
            self.translation_result
            return self.translation_result
        else:
            self.translation_result = self.get_translation_from_google_api()
            self.add_translation_to_google_collection()
            return self.translation_result

    def get_translation_from_google_api(self):
        project_id = "genial-runway-305023"
        client = translate.TranslationServiceClient()
        location = "global"
        parent = f"projects/{project_id}/locations/{location}"
        response = client.translate_text(
            parent= parent,
            contents= [self.source_word],
            mime_type= "text/plain",
            source_language_code= self.source_language_code,
            target_language_code= self.target_language_code,
        )
        for translation in response.translations:
            return translation.translated_text

    def get_translation_from_google_collection(self):
        collection_name = 'google_translations_' + self.source_language_code
        if self.db.sources[collection_name].count_documents({
            'word': self.source_word,
            'translations': {
                'language': self.target_language_code
            }
        }) > 0:
            return self.db.sources[collection_name].find_one({
                'word': self.source_word,
                'translations': {
                    'language': self.target_language_code
                }
            })
        return False

    def add_translation_to_google_collection(self):
        collection_name = 'google_translations_' + self.source_language_code
        if self.db.sources[collection_name].count_documents({'word':self.source_word}) > 0:
            collection_name = 'google_translations_' + self.source_language_code
            self.db.sources[collection_name].update_one(
                {
                    'word': self.source_word
                },
                {
                    "$addToSet": {
                        "translations": {
                            'language': self.target_language_code,
                            'word': self.translation_result
                        }
                    }
                }
            )
        else:
            self.db.sources[collection_name].insert_one({
                'word': self.source_word,
                'translations': [{
                    'language': self.target_language_code,
                    'word': self.translation_result
                }]
            })
