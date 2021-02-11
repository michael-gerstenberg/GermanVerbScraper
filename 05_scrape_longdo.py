from mongo_db import connect_mongo_db
from tqdm import tqdm
import re
import copy
import pprint


# after the thai data is reviewed and connected, a thai oriented database should be created
# when something is reviewed it should be set to reviewed and added to the verbs_de database

db = connect_mongo_db()


# I guess this does extract all verbs from the longo list and save all verbs in a new file?
def check_verbs_in_longdo():
    db = connect_mongo_db()
    positive = 0
    negative = 0
    verbs = 0
    
    f = open('scrapes/longdo/longdo_de_th_edited.txt')
    line = f.readline()
    f_v = open('scrapes/longdo/longdo_de_th_edited_verbs.txt', 'a')
    # for verb in tqdm(verbs):
    while line:
        word = line.split('	')[0].strip()
        result = db.verbs.find({'keywords':word})
        leftovers = []
        if '(v)' in line:

            if result.count() < 1:
                print(word)


            verbs += 1
            f_v.write(line)
            #pprint(line)





        # word_type = re.findall('(\((v)\))', line)
        # print(wt)
        # word_types[word_type[1]] = True
        if result.count(True):
            ignore = ['(v)', '(Adj.)', '(Adj. Adv.)', '(Adv.)', '(Adv. Adj.)', '(adj)', '(adj adv)', '(adj adv slang)', '(adj colloq)', '(adj jargon)', '(adj n)', '(adj pp.)', '(adj slang)', '(adj, adv)', '(adj.)', '(adv)', '(adv adj)', '(adv phrase)', '(adv, Präp)', '(adv, adj)']
            for i in ignore:
                line = line.replace(i, '(x)')
            # if '(x)' not in line:
                # print(line)

            # ignore = ['(v)', '(Adj.)', '(Adj. Adv.)', '(Adv.)', '(Adv. Adj.)', '(adj)', '(adj adv)', '(adj adv slang)', '(adj colloq)', '(adj jargon)', '(adj n)', '(adj pp.)', '(adj slang)', '(adj, adv)', '(adj.)', '(adv)', '(adv adj)', '(adv phrase)', '(adv, Präp)', '(adv, adj)']
            # if any(x in line for i in ignore):
            #     continue
            # print(line)
                leftovers.append(line)
            positive += 1
            #print(positive)
        else:
            negative += 1
        line = f.readline()
    

    f.close()
    #print(verbs)
    # print(leftovers)
    # print(positive)
    # print(negative)

    # for word in db.verbs.find():if __name__ == "__main__":

def extract_verbs():
    
    empty_row = {
        'german_verb': '',
        'thai_translations': [],
        'examples': [],
        'status': 'not_reviewed'
    }
    empty_example = {
        'thai_sentence': '',
        'german_sentence': ''
    }
    
    f = open('scrapes/longdo/longdo_de_th_edited_verbs.txt')
    line = f.readline()
    i = 0
    while line:
        i += 1
        row = copy.deepcopy(empty_row)
        row['german_verb'] = line.split('	')[0]
        line = re.sub('(\|(.*?)\|)', '' , line)
        
        line_rest = line.split('(v) ')[1].strip()
        line_related = ''

        if line_rest.count('Related:') > 0:
            line_related = line_rest.split('Related:')[1].strip()
            line_rest = line_rest.split('Related:')[0].strip()
    
        if line_rest.count(' เช่น ') > 0:
            line_examples_and_rest = line_rest.split(' เช่น ')[1].replace(' =', '').strip().rstrip(',').strip()


            #print(line_examples_and_rest)

            if line_examples_and_rest.count('. ') > 0:

                row['examples'].append({
                    'thai_sentence': line_examples_and_rest.split('. ')[1],
                    'german_sentence': line_examples_and_rest.split('. ')[0]
                })


            line_rest = line_rest.split(' เช่น ')[0].strip()
        
        line_translations = line_rest.split(', ')
        
        row['thai_translations'] = [sub.replace(',', '') for sub in line_translations]
        
        
        pprint.pprint(row)

            # print({
            #     'translations': line_translations,
            #     'examples': line_examples_and_rest
            # })

        # else:
        #     print(line_rest.split(', '))

        #print(line)
        line = f.readline()





def list_wordtypes():
    word_types = []
    f = open('scrapes/longdo/longdo_de_th_edited.txt')
    line = f.readline()

    while line:
        word_type = re.findall('(\((.*?)\))', line)
        if  len(word_type) > 0:
            word_types.append(word_type[0][1])
        line = f.readline()
    
    word_types = sorted(list(set(word_types)))
    print(word_types)
    f.close()
    
if __name__ == "__main__":
    #check_verbs_in_longdo()
    extract_verbs()