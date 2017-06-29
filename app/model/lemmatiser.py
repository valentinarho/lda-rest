import string

import nltk
from nltk import WordNetLemmatizer


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
