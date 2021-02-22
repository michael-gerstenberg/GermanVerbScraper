from bs4 import BeautifulSoup
from mongo_db import connect_mongo_db
from pathlib import Path
from tqdm import tqdm
import pprint
from datetime import datetime

db = connect_mongo_db()

# rename a collection
# db.sources.netzverb_adj_adv_new.rename('netzverb_adj_adv')

# change status of all


# delete something

# for w in db.sources.verblisten_substantives.find({"url":{"$regex": u"/artikel-pronomen/"}},{'_id':1, 'url':1}):
#     print(w['url'])
#     # if db.sources.netzverb_adj_adv.count_documents({'url': w['url']}) > 1:
#     #     print(w['url'])
#     db.sources.verblisten_substantives.delete_one({'_id':w['_id']})


# del files
# for w in db.sources.verblisten_substantives.find({"url":{"$regex": u"/adjektive/"}},{'_id':1, 'url':1}):
#     print(w['url'].replace('https://www.verben.de/substantive/', ''))
#     print(w['url'])




# documents = []
# for w in db.sources.netzverb_substantives.find({}):
#     document = {
#         'components':{
#             'definitions': {
#                 'url': w['components'][0]['url'],
#                 'download_status': True,
#                 'scrape_status': False,
#                 'downloaded_date': datetime.now(),
#                 'scraped_date': '',
#             },
#             'declensions': {
#                 'url': w['components'][0]['url'].replace('verben.de/', 'verbformen.de/deklination/'),
#                 'download_status': False,
#                 'scrape_status': False,
#                 'downloaded_date': '',
#                 'scraped_date': '',
#             }
#         },
#         'source': 'CC-BY-SA 3.0',
#         'letter': w['letter'],
#     }
#     documents.append(document)
# db.sources.netzverb_substantives_new.insert_many(documents)


######################################################
###### Update all documents with condition

# for w in db.sources.netzverb_adj_adv_old.find({'scrape_status':False}):
#     print(w['url'])
#     db.sources.netzverb_adj_adv_old.update_one({
#         '_id': w['_id']
#     }, {
#         '$set':{
#             'download_status': False
#         }
#     })



documents = []
for w in db.sources.verblisten.find({}).limit(10000000):
    
    modified = w['scraped_content']
    modified['declension_sorting'] = w['scraped_content']['declension_order']
    del modified['declension_order']

    document = {
        'word': w['word'],
        'components':{
            'conjugations': {
                'url': w['conjugations']['url'],
                'download_status': True,
                'downloaded_date': datetime.now(),
                'scrape_status': True,
                'scraped_date': datetime.now(),
            },
            'definitions': {
                'url': w['definitions']['url'],
                'download_status': True,
                'downloaded_date': datetime.now(),
                'scrape_status': True,
                'scraped_date': datetime.now(),
            },
            'examples':  {
                'url': w['examples']['url'],
                'download_status': True,
                'downloaded_date': datetime.now(),
                'scrape_status': True,
                'scraped_date': datetime.now(),
            },
        },
        'license': 'CC-BY-SA 3.0',
        'scraped_content': {
            'translations': w['translations'],
        },
    }
    documents.append(document)
db.sources.netzverb_adj_adv_new.insert_many(documents)