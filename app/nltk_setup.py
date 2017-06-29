import nltk
from nltk.corpus import wordnet
from nltk.tokenize import punkt
from nltk.corpus import stopwords

try:
    wordnet.words
except LookupError:
    nltk.download('wordnet')

try:
    punkt.REASON_DEFAULT_DECISION
except LookupError:
    nltk.download('punkt')

try:
    stopwords.words
except LookupError:
    nltk.download('stopwords')
