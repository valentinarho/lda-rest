import os

db_host = os.environ['DB_PORT_27017_TCP_ADDR']

db_port = 27017

db_name = 'om_lda'

documents_collection_name = 'documents'
models_collection_name = 'models'
topics_collection_name = 'topics'

current_model_id = 'unique_model'

data_path = '/data'


resource_path = os.path.join(os.path.split(__file__)[0], "resources")

italian_stopwords_filepath = resource_path + '/stopwords_it.txt'
italian_lemma_filepath = resource_path + '/morph-it_048_UTF8.txt'

app_log_filepath = '/logs/om_integration_app_log.log'
scripts_log_filepath = '/logs/lda_scripts_log.log'

defaults = {
    'minimum_threshold': {'value': 0.0, 'description': 'float, the minimum weight that a topic should have with respect '
                                                       'to a query or a document to be considered as inherent.'},
    'language': {'value': 'en', 'description': 'string, the language of the documents, allowed values are "en" and "it".'},
    'use_lemmer': {'value': True, 'description': 'boolean, True to apply lemmatisation, False to apply only stemming.'},
    'min_df': {'value': 2, 'description': 'float or int, the minimum document frequency to consider a word as interesting.'},
    'max_df': {'value': 0.8, 'description': 'float, the maximum document frequency to consider a word as interesting.'},
    'chunksize': {'value': 2000, 'description': 'int, the size of each chunk of documents processed by LDA.'},
    'num_passes': {'value': 2, 'description': 'int, the minimum number of passes through each document during learning.'},
    'assign_topics': {'value': True, 'description': 'boolean, True to save learning documents with their corresponding assignment, False to ignore them.'},
    'waiting_seconds': {'value': 300, 'description': 'int, the waiting time in seconds before starting module computation.'},

}

# LDA
max_number_of_words_per_topic = 30

exposed_fields = {
    'models': ['version', 'version_description', 'created',
               'modified', 'number_of_topics',
               'training_documents_count', 'training_parameters'],
    'documents': ['document_id', 'text', 'assigned_topics'],
    'topics': ['topic_id', 'topic_label', 'topic_description',
               'words_distribution']
}
