import logging

import time
from pymongo import MongoClient
from pymongo.collection import Collection

import config

mongo_client = None


def get_mongo_client():
    global mongo_client
    if mongo_client is None:
        mongo_client = MongoClient(config.db_host, config.db_port)

    return mongo_client


def get_collection(collection_name, custom_mongo_client=None):
    """
    Return the collection

    :type collection_name: str
    :param collection_name:
    :type custom_mongo_client: MongoClient
    :param custom_mongo_client:
    :rtype: Collection
    :return:
    """
    if custom_mongo_client is None:
        custom_mongo_client = get_mongo_client()

    db = custom_mongo_client[config.db_name]
    return db[collection_name]


def get_all_models(collection=None):
    if collection is None:
        collection = get_collection(config.models_collection_name)

    result = collection.find()
    if result is None:
        return []

    return list(result)


def get_model(model_id):
    collection = get_collection(config.models_collection_name)

    result = collection.find_one({'model_id': model_id})
    if result is None:
        return None
    else:
        return {k: v for k, v in result.items()}


def delete_model(model_id):
    models_collection = get_collection(config.models_collection_name)
    models_collection.delete_one({'model_id': model_id})

    topics_collection = get_collection(config.topics_collection_name)
    topics_collection.delete_many({'model_id': model_id})


def upsert_model(model_id, model_values):
    models_collection = get_collection(config.models_collection_name)
    db_model = models_collection.find_one({'model_id': model_id})

    if db_model is None:
        # insert new
        update = False
        model_values['model_description'] = ''
        model_values['created'] = time.time()
    else:
        update = True
        model_values['model_id'] = model_id
        if 'created' in model_values: del model_values['created']

    model_values['modified'] = time.time()

    if update:
        models_collection.update_one({'model_id': model_id}, {'$set': model_values})
    else:
        models_collection.insert_one(model_values)


def get_all_topics(model_id):
    collection = get_collection(config.models_collection_name)

    result = collection.find_one({'model_id': model_id})

    if result is None:
        return None

    topics = []
    for i, t in enumerate(result['topics']):
        t['words_distribution'] = [{'w': k, 'w_weight': v} for k,v in t['words_distribution'].items()]
        topics.append(t)

    return topics


def get_topic(model_id, topic_id):
    """

    :param model_id: string
    :param topic_id: int
    :param collection:
    :return:
    """
    collection = get_collection(config.models_collection_name)

    result = collection.find_one({'model_id': model_id})
    if result['topics'] is not None and len(result['topics']) != 0:
        topic = list(filter(lambda t: t['topic_id'] == topic_id, result['topics']))[0]
        topic['words_distribution'] = sorted([{'w': k, 'w_weight': v} for k, v in topic['words_distribution'].items()], key=lambda t:t['w_weight'], reverse=True)
        return topic

    return None;


def get_all_documents(model_id=None):
    """
    Get all documents that have an assignment w.r.t the specified model
    :param model_id:
    :param collection:
    :return:
    """

    if model_id is not None:
        collection = get_collection(config.topics_collection_name)

        results = collection.find({'model_id': model_id})
        results = [
            {
                'document_id': r['document_id'],
                'model_id': model_id
            } for r in results]
    else:
        collection = get_collection(config.documents_collection_name)
        results = collection.find()
        results = [{'doc_id': r['document_id'], 'text': r['text']} for r in results]

    return results


def get_all_documents_ids():
    collection = get_collection(config.documents_collection_name)
    results = collection.find()
    results = [r['document_id'] for r in results]
    return results


def get_document(model_id, document_id, topics_threshold):
    """
    Get document information and topic assignments for the document w.r.t. the selected model

    :param model_id: string
    :param document_id: string
    :param topics_threshold: float, range [0,1] the weight threshold for the topics
    :return:
    """
    topics_collection = get_collection(config.topics_collection_name)
    docs_collection = get_collection(config.documents_collection_name)

    topics = topics_collection.find_one({'model_id': model_id, 'document_id': str(document_id)})
    doc = docs_collection.find_one({'document_id': str(document_id)})

    if doc is None:
        return None

    result = {k: v for k, v in doc.items()}
    if topics is not None:
        result['assigned_topics'] = [{'topic_id': a['topic_id'], 'topic_weight': a['topic_weight']}
                                     for a in topics['assigned_topics']
                                     if a['topic_weight'] >= topics_threshold]
        result['model_id'] = model_id

    return result


def get_texts(document_ids):
    # TODO TO BE IMPLEMENTED
    pass


def update_model(model_id, model_description):
    models_collection = get_collection(config.models_collection_name)
    models_collection.update_one({'model_id': model_id}, {'$set': {'model_description': model_description}})


def update_model_status(model_id, model_status, model_values):
    models_collection = get_collection(config.models_collection_name)
    models_collection.update_one({'model_id': model_id}, {'$set': {'status': model_status,
                                                                   'updating_process_id': model_values['process_id']}})


def insert_all_documents(docs):
    if docs is not None and len(docs) != 0:
        docs_collection = get_collection(config.documents_collection_name)
        docs_collection.insert_many(docs)


def insert_all_assignments(topics_ass):
    if topics_ass is not None and len(topics_ass) != 0:
        topics_collection = get_collection(config.topics_collection_name)
        topics_collection.insert_many(topics_ass)


def get_assigned_topics(model_id, document_id, topics_threshold=0.0):
    """
    Get topics assigned to a document in a model

    :param model_id:
    :param doc_id:
    :return:
    """
    topics_collection = get_collection(config.topics_collection_name)

    topics = topics_collection.find_one({'model_id': model_id, 'document_id': str(document_id)})

    if topics is not None:
        result = [{'topic_id': a['topic_id'], 'topic_weight': a['topic_weight']}
                                     for a in topics['assigned_topics']
                                     if a['topic_weight'] >= topics_threshold]

    return result