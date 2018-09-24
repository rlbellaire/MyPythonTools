# coding: utf-8

'''
example: reload upon library s/w change
del regex_filter
import query_grammer
reload(query_grammer)
from query_grammer import regex_filter
'''

import re
import nltk

# REGEX to filter commment text according to:
#    Type == "contact": phone number or email
#            "phone": us or uk phone number
#            "email": email standard
#            "emotion": upset people: contact info, extra punctuation, allcaps
def regex_filter(type):
    us_regex = r"(?:\(?1?\)?)[-\.\=\_\s/']{0,4}\(?(?P<us_area_code>[2-9][0-9]{2})?\)?[-\.\s\=\_/']{0,4}\(?(?P<us_tel_no>([2-9][\s]{0,2}[0-9][\s]{0,2}[0-9])?[-\.\s\=\_/'\)\(]{0,4}([0-9][\s]{0,2}[0-9][-\.\s\=\_/'\)\(]{0,4}[0-9][\s]{0,2}[0-9]))\s?\)?(ext|ext|x|ex)?\.?\s?(?P<us_ext>\d{0,4})"
    uk_regex = r"[-\.\=\_\s/'\+]{0,4}\(?(?P<uk_area_code>([0][1345789][0-9]{0,3})|([4][4])|(([0][2])[0-9]))?\)?[-\.\s\=\_/'\*\&\:\;\!\~\\]{0,4}\(?(?P<uk_tel_no>(([0-9][0-9][0-9][0-9]?)[-\.\s\=\_/'\|\&\~)\(]{0,4}([0-9][0-9][-\.\s\=\_/'\&\~)\(]{0,4}[0-9][0-9]))|([0-9]{5,6}|([0-9]{10})))\s?\)?\b"
    email_regex = r"[A-Za-z0-9](([_\.\-]?[a-zA-Z0-9]+)*)@([A-Za-z0-9]+)(([\.\-]?[a-zA-Z0-9]+)*)\.([A-Za-z]{2,})"
    complex_stem_regex = r"([a-z])\1{2,}"
    extra_punc_regex = r"([\?\#\!]){2,}"
    allcaps_regex = r"\b[A-Z]{2,}.*\b"

    if type == "contact":
        my_regex = "|".join([us_regex, uk_regex, email_regex])
    elif type == "phone":
        my_regex = "|".join([us_regex, uk_regex])
    elif type == "email":
        my_regex = email_regex
    elif type == "emotion":
        my_regex = "|".join([us_regex, uk_regex, email_regex,\
                         complex_stem_regex, extra_punc_regex, allcaps_regex])
    else:
        print ("the supplied regex type {0} is not among the supported types [contact, phone, email, emotion]").format(type)
        
    return my_regex

# EXCLUDE
# 1- re.sub Remove word in excluded_words but not follow the pattern in search_words
# e.g. remove 'York' but not 'New York', remove 'check' but not 'check out' 
# 2- re.Match Match words in search_words

def buildup_exclude_regex(search_words, exclude_words):
    search_words = [re.sub(r'\s+', ' ', item.strip()) for item in search_words]
    exclude_words = [re.sub(r'\s+', ' ', item.strip()) for item in exclude_words]
    search_words = [re.sub(r'"', '', item.lower()) for item in search_words]
    exclude_words = [re.sub(r'"', '', item.lower()) for item in exclude_words]
    if any([item in exclude_words for item in search_words]):
        print 'illegal request'
        return 0
    else:
        search_reg = r'\b(' + r'|'.join([r'\b' + item + r'\b' for item in search_words]) + r')\b'
        search_words_n = [item for item in search_words if ' ' in item]
        exclude_words_update = [] 
        for exclude in exclude_words:
            flag = 0
            for search in search_words:
                tmp = re.split(r'\b' + exclude + r'\b', search, maxsplit = 1)
                if len(tmp) != 1:
                    flag = 1
                    left = '' if tmp[0] =='' else r'(?<!' + tmp[0].strip() + r'\s)'
                    right = '' if tmp[1] == '' else r'(?!\s' + tmp[1].strip() + r')'
                    exclude_words_update.append(r'\b' + left + exclude + right + r'\b')
            if not flag:
                exclude_words_update.append(r'\b' + exclude + r'\b')
                    
        exclude_reg = r'\b(' + '|'.join(exclude_words_update) + r')\b'
        return re.compile(search_reg), re.compile(exclude_reg)
        
                
def run_exclude(doc, search_words, exclude_words):
    [regex_search, regex_exclude] = buildup_exclude_regex(search_words,exclude_words)
    filtered = re.sub(r'\s+', ' ', doc)
    filtered = regex_exclude.sub('', filtered.lower())
    filtered = re.sub(r'\s+', ' ', filtered)
    found = bool(regex_search.search(filtered))
    return found
    
#
# WITH
# 1- TOKENIZE
# 2- Check &| and generate regex with positive lookahead
# flag = 1 --> &
# flag = 0 --> |

def buildup_with_regex(search_words, with_words, flag_search, flag_with):
    search_words = [re.sub(r'\s+', ' ', item.strip()) for item in search_words]
    with_words = [re.sub(r'\s+', ' ', item.strip()) for item in with_words]
    search_words = [re.sub(r'"', '', item.lower()) for item in search_words]
    with_words = [re.sub(r'"', '', item.lower()) for item in with_words]
    if flag_search:
        s_pattern = ''.join([r'(?=.*\b' + item + r'\b)'for item in search_words])
    else:
        s_pattern = r'(?=.*(' + '|'.join([r'\b' + item + r'\b'for item in search_words]) + r'))'
    if flag_with:
        w_pattern = ''.join([r'(?=.*\b' + item + r'\b)'for item in with_words])
    else:
        w_pattern = r'(?=.*(' + '|'.join([r'\b' + item + r'\b'for item in with_words]) + r'))'
    pattern = '^' + s_pattern + w_pattern + '.*$'
    regex = re.compile(pattern) 
    return regex

def run_with(docs, search_words, with_words, flag_search, flag_with):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    regex = buildup_with_regex(search_words, with_words, flag_search, flag_with)
    i = 0
    for doc in docs:
        filtered = re.sub(r'\s+', ' ', doc)
        i = i + 1
        sentences = tokenizer.tokenize(filtered)
        for sentence in sentences:
            found = regex.match(sentence.lower())
            if found:
                print 'FOUND'
    
# NOTWITH
# negative/positive lookahead

def buildup_nwith_regex(search_words, nwith_words, flag_search):
    search_words = [re.sub(r'\s+', ' ', item.strip()) for item in search_words]
    nwith_words = [re.sub(r'\s+', ' ', item.strip()) for item in nwith_words]
    search_words = [re.sub(r'"', '', item.lower()) for item in search_words]
    nwith_words = [re.sub(r'"', '', item.lower()) for item in nwith_words]
    if flag_search:
        s_pattern = ''.join([r'(?=.*\b' + item + r'\b)'for item in search_words])
    else:
        s_pattern = r'(?=.*(' + '|'.join([r'\b' + item + r'\b'for item in search_words]) + r'))'
    nw_pattern = r'(?!.*(' + '|'.join([r'\b' + item + r'\b'for item in nwith_words]) + r'))'
    pattern = r'^' + nw_pattern + s_pattern + '.*$'
    return re.compile(pattern)
    
def run_nwith(docs, search_words, nwith_words, flag_search):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    i = 0
    regex = buildup_nwith_regex(search_words, nwith_words, flag_search)
    for doc in docs:
        i = i + 1
        filtered = re.sub(r'\s+', ' ', doc)
        sentences = tokenizer.tokenize(filtered)
        for sentence in sentences:
            found = regex.match(sentence.lower())
            if found:
                print 'FOUND(DOC' + str(i)+ '):  ', sentence

# NOTNEAR
# Assume input item is always a single word
# Use nltk to tokenize word. CANNOT USE SPLIT --- comma cannot be recognized as a token; contains empty string

def buildup_notnear(search_word, nnear_word, dis):
    search_word = re.sub('"', '', re.sub(r'\s+', ' ', search_word.lower().strip()))
    nnear_word = re.sub('"', '', re.sub(r'\s+', ' ', nnear_word.lower().strip()))
    
    pattern_ = r'\b{0}\b\s(?:[^\s]+\s){{{1},}}?\b{2}\b'
    pattern = pattern_.format(search_word, dis, nnear_word) + r'|' + pattern_.format(nnear_word, dis, search_word)
    search_2 = r'\b' + search_word + r'\b'
    search_1 = r'\b' + nnear_word + r'\b'
    return [re.compile(search_1), re.compile(search_2), re.compile(pattern)]

def run_notnear(docs, search_word, nnear_word, dis):
    [regex_1, regex_2, regex_3] = buildup_notnear(search_word, nnear_word, dis)
    i = 0
    for doc in docs:
        i = i + 1
        doc_word = word_tokenize(doc.lower())
        new_doc = ' '.join(doc_word)
        if regex_1.search(new_doc):
            if regex_3.match(new_doc):
                print 'FOUND(DOC' + str(i)+ '):  ', doc
        else:
            if regex_2.search(new_doc):
                print 'FOUND(DOC' + str(i)+ '):  ', doc      
