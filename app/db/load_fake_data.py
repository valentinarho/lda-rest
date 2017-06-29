import os
import sys

sys.path.append(os.path.abspath('.'))

from time import time

import config
from db import db_utils

def load_models_data():
    client = db_utils.get_mongo_client()
    db = client[config.db_name]
    models_collection = db[config.models_collection_name]

    model = {
        'files_prefix': 'lda-2000-2004-153-50',
        'model_id': '1.0',
        'model_description': 'Model computed on scientific citations',
        'status': 'computed',
        'created': time(),
        'modified': time(),
        'training_documents_count': 100,
        'training_parameters': {
            'min_document_frequency': 1,
            'max_document_frequency': 0.8,
            'chunk_size': 2000,
            'min_passes': 2
        },
        'number_of_topics': 50,
        'language': 'en',
        'use_lemmer': True,
        'topics': [
            {
                'topic_id': 1,
                'topic_label': 'data mining',
                'topic_description': 'prova di description del topic data mining',
                'words_distribution': {
                    'w5': 0.3,
                    'w1': 0.2,
                    'w2': 0.03,
                }
            },
            {
                'topic_id': 2,
                'topic_label': 'artificial intelligence',
                'topic_description': 'prova di description del topic art int',
                'words_distribution': {
                    'w5': 0.35,
                    'w4': 0.22,
                    'w1': 0.03,
                }
            }
        ]
    }

    models_collection.insert(model)

    del model['_id']
    model['model_id'] = 'tmp'
    model['files_prefix'] = 'prova_modello'
    model['topics'].append({
                'topic_id': 3,
                'topic_label': 'cognitive science',
                'topic_description': 'prova di dsf del topic art int',
                'words_distribution': {
                    'w5': 0.2,
                    'w3': 0.22,
                    'w1': 0.22,
                }
            })

    models_collection.insert(model)


def load_documents_data():
    client = db_utils.get_mongo_client()
    db = client[config.db_name]
    documents_collection = db[config.documents_collection_name]

    documents = [
        {
            'document_id': "1",
            'text': 'questa prova documento topic ciao',
            'created': time()
        },
        {
            'document_id': "21",
            'text': 'questa altro documento topic ciao',
            'created': time()
        }
    ]

    documents_collection.insert_many(documents)


def load_topics_data():
    client = db_utils.get_mongo_client()
    db = client[config.db_name]
    topics_collection = db[config.topics_collection_name]

    topics = [
        {
            'model_id': '1.0',
            'document_id': '1',
            'assigned_topics': [
                {'topic_id': 1, 'topic_weight': 0.324},
                {'topic_id': 2, 'topic_weight': 0.22},
            ]
        },
        {
            'model_id': '1.0',
            'document_id': '21',
            'assigned_topics': [
                {'topic_id': 1, 'topic_weight': 0.5232},
                {'topic_id': 2, 'topic_weight': 0.123},
            ]
        },
        {
            'model_id': 'tmp',
            'document_id': '1',
            'assigned_topics': [
                {'topic_id': 1, 'topic_weight': 0.7},
                {'topic_id': 2, 'topic_weight': 0.2},
                {'topic_id': 3, 'topic_weight': 0.1},

            ]
        },
        {
            'model_id': 'tmp',
            'document_id': '21',
            'assigned_topics': [
                {'topic_id': 1, 'topic_weight': 0.6},
                {'topic_id': 2, 'topic_weight': 0.11},
                {'topic_id': 3, 'topic_weight': 0.22},

            ]
        }
    ]

    topics_collection.insert_many(topics)


def clear_db():
    client = db_utils.get_mongo_client()
    db = client[config.db_name]
    topics_collection = db[config.topics_collection_name]
    topics_collection.delete_many({})
    documents_collection = db[config.documents_collection_name]
    documents_collection.delete_many({})
    models_collection = db[config.models_collection_name]
    models_collection.delete_many({})


if __name__ == "__main__":
    clear_db()
    load_models_data()
    load_documents_data()
    load_topics_data()
