from mongo_db import connect_mongo_db
from tqdm import tqdm
import json
import re

db = connect_mongo_db()

def main():
    verbs = db.scraped_verbs.find()
    for verb in tqdm(verbs):
        db.scraped_verbs.update_one({'_id': verb['_id']}, {'$set':{'keywords': sorted(get_keywords(verb))}})

def get_keywords(verb):
    cut_first_word = {
        'subjunctive_active': ['perfect', 'plusquamperfect', 'future', 'future_perfect'],
        'indicative_active': ['perfect', 'plusquamperfect', 'future', 'future_perfect'],
        'conditional_active': ['perfect', 'plusquamperfect', 'future', 'future_perfect', 'imperfect'],
        'imperative_active': [],
        'infinitive_participle_active': [],
    }
    keywords = [verb['word']]
    for x in verb['conjugations']:
        for y in verb['conjugations'][x]:
            for z in verb['conjugations'][x][y]:
                if y in cut_first_word[x]:
                    result1 = (' ').join(z.split(' ')[2:]) 
                    keywords.append(result1)
                    result2 = (' ').join(z.split(' ')[1:]) 
                    keywords.append(result2)
                else:
                    keywords.append(replace_no_keywords(z))
    keywords = final_touch(keywords)
    return remove_useless_items(keywords)

def final_touch(keywords):
    keywords_final_touched = []
    for keyword in keywords:
        buffer = re.sub(r"([\(\[]).*?([\)\]])", "", keyword)
        keywords_final_touched.append(buffer.strip().replace('  ', ' '))
    return list(set(keywords_final_touched))

def replace_no_keywords(expression):
    no_keywords = ['er ', 'sie ', 'du ', 'ihr ', 'wir ', 'ich ', 'es ']
    for no_keyword in no_keywords:
        if expression[0:len(no_keyword)] == no_keyword:
            return expression[len(no_keyword):]
    return expression

def remove_useless_items(input_list):
    to_remove = ['Sie', '(du)', 'zu']
    for word in to_remove:
        if word in input_list:
            input_list.remove(word)
    return input_list

if __name__ == "__main__":
    main()
