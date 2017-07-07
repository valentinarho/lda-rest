import string

import nltk
from nltk import WordNetLemmatizer

import config

italian_lemmas = None

def LemTokens(tokens):
    lemmer = WordNetLemmatizer()
    return [lemmer.lemmatize(token) for token in tokens]


def LemNormalize(text):
    # convert non ascii characters
    text = text.encode('ascii', 'replace').decode()
    # remove punctuation and digits
    remove_punct_and_digits = dict([(ord(punct), ' ') for punct in string.punctuation + string.digits])
    transformed = text.lower().translate(remove_punct_and_digits)
    # shortword = re.compile(r'\W*\b\w{1,2}\b')
    # transformed = shortword.sub('', transformed)

    # tokenize the transformed string
    tokenized = nltk.word_tokenize(transformed)

    # remove short words (less than 3 char)
    tokenized = [w for w in tokenized if len(w) > 3]
    tokenizer = LemTokens(tokenized)

    return tokenizer


def load_morph_it():
    global italian_lemmas
    if italian_lemmas is None:
        with open(config.italian_lemma_filepath, 'r') as file:
            lemmas = {v[0].strip(): v[1].strip() for v in [l.split('\t') for l in reversed(file.readlines())]}

        italian_lemmas = lemmas

    return italian_lemmas


def LemNormalizeIt(text):

    # convert non ascii characters
    text = text.encode('ascii', 'replace').decode()
    # remove punctuation and digits
    remove_punct_and_digits = dict([(ord(punct), ' ') for punct in string.punctuation + string.digits])
    transformed = text.lower().translate(remove_punct_and_digits)

    # tokenize the transformed string
    tokenized = nltk.word_tokenize(transformed)

    morph_it = load_morph_it()
    tokenized = [morph_it.get(w, w) for w in tokenized]

    return tokenized
