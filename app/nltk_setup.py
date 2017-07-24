import nltk
from nltk.corpus import wordnet
from nltk.tokenize import punkt
from nltk.corpus import stopwords

try:
    wordnet.words
except Exception:
    print('Downloading wordnet.')
    nltk.download('wordnet', download_dir='/usr/share/nltk_data')

# always downloading punkt
print('Downloading punkt.')
nltk.download('punkt', download_dir='/usr/share/nltk_data')

try:
    stopwords.words
except Exception:
    print('Downloading stopwords.')
    nltk.download('stopwords', download_dir='/usr/share/nltk_data')
