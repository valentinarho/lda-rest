import logging
import os
import re

from time import time
from gensim.models import LdaModel
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer

import config
from db import db_utils
from model.lda_model import LdaModelHelper
from model.lemmatiser import LemNormalize, LemNormalizeIt
from scripts import scheduler
import json
from scipy import spatial


def load_lda_model(file_prefix):
    return LdaModel.load(os.path.join(config.data_path, file_prefix))


def read_documents_from_file(data_filename):
    """
    Get documents from a filename. The file should contain json dumped data
    :type data_filename: str
    :param data_filename:
    :rtype: lists
    :return: list of dictionaries, each dict contains the keys 'doc_id', 'doc_content'
    """

    filepath = os.path.join(config.data_path, data_filename)
    with open(filepath) as f:
        file_content = ''.join(line.replace('\n', '') for line in f.readlines())
        file_content = file_content.replace('},]', '}]')
        loaded_data = json.loads(file_content)

    return loaded_data

    # Start implementing tab separated values
    # filepath = os.path.join(config.data_path, data_filename)
    # with open(filepath) as f:
    #     line = f.readline()
    #     documents = []
    #     while line is not None:
    #         splitted = re.split(r'\t+', line)


def get_documents_from_endpoint(data_endpoint):
    """
    Get documents from a endpoint rest.
    :type data_endpoint: str
    :param data_endpoint:
    :rtype: list
    :return: list of dictionaries, each dict contains the keys 'doc_id', 'doc_content'
    """
    # TODO to be implemented
    return tmp_get_fake_data()


# TODO remove this function
def tmp_get_fake_data():
    """
    :rtype: list
    :return:
    """
    return [
        {'doc_id': 'doc_1',
         'doc_content': "Parco del Valentino (also known as Valentino Park) is a popular public park[1] in Turin, Italy. It is located along the west bank of the Po river. It covers an area of 500,000m², which makes it Turin's second largest park (Turin's largest park, the 840,000m² Pellerina Park, is Italy's most extended urban green area).[1]"},
        {'doc_id': 'doc_2',
         'doc_content': "The Palace of Venaria (Italian: Reggia di Venaria Reale) is a former royal residence located in Venaria Reale, near Turin, in Piedmont, northern Italy. It is one of the Residences of the Royal House of Savoy, included in the UNESCO Heritage List in 1997.  The Palace was designed and built from 1675 by Amedeo di Castellamonte, commissioned by duke Charles Emmanuel II, who needed a base for his hunting expeditions in the heathy hill country north of Turin. The name itself derives from Latin, Venatio Regia meaning 'Royal Hunt'.  Charles Emmanuel was inspired by the example of the Castle of Mirafiori, built by Duke Charles Emmanuel I for his wife Catherine Michelle of Spain. Keen to leave a memorial of himself and his wife, Marie Jeanne of Savoy-Nemours, he bought the two small villages of Altessano Superiore and Altessano Inferiore from the Milanese-origin Birago family, who had created here a large complex of plants. The place was rechristened Venaria for his future function as hunting base.  The design was commissioned from architects Amedeo di Castellamonte and Michelangelo Garove (it). The plan of the annexed borough was to symbolize the collar symbol of the Supreme Order of the Most Holy Annunciation, a dynastic order created by the House of Savoy. In 1675 the borough and the palace were nearly completed, including the so-called Reggia di Diana (Royal Residence of Diana, the heart of the complex. Works however continued until the next century, as in 1693 French invasion troops are known to have destroyed some buildings and Duke (future King) Victor Amadeus II had the residence modified according to French canons.  Further damage was inflicted during the Siege of Turin (1706), when the French troops under Louis d'Aubusson de La Feuillade were billeted there. After the Savoyard victory, Victor Amadeus named Filippo Juvarra as director of the works. It was here that during the reign of Charles Emmanuel III that his third wife died giving birth to son. The structure was rarely used after.  During the Napoleonic domination, the structures were turned into barracks and the gardens destroyed to create a training ground. The complex maintained this role also after the fall of Napoleon, and was used by the Italian Army until 1978, when it was sold to the Ministry of Culture. Restoration works were begun, but most of the complex was open for tourism from 13 October 2007."}
    ]


def compute_model(model_id, n_topics, language='en', use_lemmer=True, min_df=2, max_df=0.8, chunksize=2000,
                  num_passes=2, data_filename=None, data_endpoint=None, data=None, assign_topics=False,
                  waiting_time=300):
    """
    Compute a model corresponding to the provided arguments
    :param n_topics:
    :param language:
    :param use_lemmer:
    :param min_df:
    :param max_df:
    :param chunksize:
    :param data_filename:
    :param data_endpoint:
    :param data:
    :param assign_topics:
    :param waiting_time:
    :return:
    :param num_passes:
    :type model_id: str
    :param model_id: the id of the model to delete
    :rtype: (int, dict)
    :return: a pair, (status_code, computed_model_id). Status code in {200, 500}.
    """

    # get model informations
    model = db_utils.get_model(model_id)

    if model is not None:
        # model id already existing
        return 500, None
    else:
        # create the model in db

        model_values = {'model_id': model_id,
                        'modified': time(),
                        'status': LdaModelHelper.status_scheduled,
                        'training_parameters': {
                            'min_document_frequency': min_df,
                            'max_document_frequency': max_df,
                            'chunk_size': chunksize,
                            'min_passes': num_passes
                        }, 'number_of_topics': n_topics,
                        'language': language,
                        'use_lemmer': use_lemmer
                        }

        db_utils.upsert_model(model_id, model_values)
        # schedule the computation
        scheduler.schedule_model_computation(model_id, n_topics, language, use_lemmer, min_df, max_df, chunksize,
                                             num_passes, data_filename, data_endpoint, data,
                                             assign_topics, waiting_time)

        return 200, model_values


def delete_model(model_id):
    """
    Delete a model from db and filesystem and return the deleted model.
    :type model_id: str
    :param model_id: the id of the model to delete
    :rtype: (int, dict)
    :return: a pair, (status_code, deleted_model). Status code in {200, 404}.
    """

    # get model informations
    model = db_utils.get_model(model_id)

    if model is not None:
        pid = None
        if 'updating_process_id' in model:
            pid = model['updating_process_id']

        if model['status'] == LdaModelHelper.status_scheduled:
            scheduler.unschedule_model_computation(pid)
        elif model['status'] == LdaModelHelper.status_computing:
            scheduler.interrupt_model_computation(pid)

        # delete from file system
        if 'files_prefix' in model and model['files_prefix'] is not None:
            status_code = LdaModelHelper.delete_model_files(config.data_path, model['files_prefix'])

        # delete model from db
        db_utils.delete_model(model_id)

        return 200, model
    else:
        return 404, None


def get_stopwords(language):
    """
    Gets a stopwords list
    :param language: 'it' or 'en'
    :return: a string or a list of stopwords
    """
    stopwords_list = []
    if language == 'it':
        with open(config.italian_stopwords_filepath, 'r') as file:
            stopwords_list = file.readlines()

        stopwords_list = [s.strip() for s in stopwords_list]
        return stopwords_list

    return stopwords.words('english')




def compute_tf(data, stopwords_list, language, use_lemmer=True, min_df=2, max_df=0.8):
    """
    Compute the tf matrix for the provided data
    :param language: 'en' or 'it'
    :param data:
    :param stopwords_list:
    :param use_lemmer:
    :param min_df:
    :param max_df:
    :return:
    """
    lemmer_tokenizer = None

    if use_lemmer:
        if language == 'it':
            lemmer_tokenizer = LemNormalizeIt
        else:
            lemmer_tokenizer = LemNormalize

    min_df = min_df if len(data) > min_df else 1
    max_df = max_df if max_df * len(data) >= min_df else 1.0

    # tf
    tf_vectorizer = CountVectorizer(tokenizer=lemmer_tokenizer,
                                    max_df=max_df, min_df=min_df,
                                    max_features=None,
                                    stop_words=stopwords_list,
                                    token_pattern="[a-zA-Z]{3,}")

    try:
        tf = tf_vectorizer.fit_transform(data)
        tf_features_names = tf_vectorizer.get_feature_names()
    except:
        logging.warning('The computed tf matrix is empty. Check stopwords.')
        tf = []
        tf_features_names = []

    return tf, tf_features_names


def save_topic_assignment(new_documents, topics_assignment, model_id):
    """
    Update the model with the given topic assignment

    :return:
    """

    temp_documents_ids = db_utils.get_all_documents_ids()
    temp_ass = convert_topic_assignment_to_dictionary(topics_assignment)

    for t in temp_ass:
        t['model_id'] = model_id
        t['document_id'] = new_documents[t['document_index']]['doc_id']
        del t['document_index']

    # TODO we should check also document content, not only id
    documents_to_insert = [{'document_id': str(d['doc_id']), 'created': time(), 'text': d['doc_content']}
                           for d in new_documents if d['doc_id'] not in temp_documents_ids]

    # insert new data
    db_utils.insert_all_documents(documents_to_insert)
    db_utils.insert_all_assignments(temp_ass)


def convert_topic_assignment_to_dictionary(topics_assignment):

    return [{'assigned_topics': [{'topic_weight': v[1], 'topic_id': v[0]} for v in values],
                 'document_index': k} for k, values in enumerate(topics_assignment)]


def save_or_update_model(model, model_id, files_prefix, model_status, docs_count=-1, update_topics=True):
    """
    Update the model if a model with the specified id already exists in the db, create it otherwise

    :type model_status: str
    :param model_status:
    :type files_prefix: str
    :param files_prefix:
    :type model_id: str
    :param model_id: the id of the model
    :type model: LdaModelHelper
    :param model: the model to save
    :type docs_count: int
    :param docs_count: the number of documents involved in the training
    :return:
    """

    temp_topics = model.get_all_topics()
    if temp_topics is not None:
        topics = [{'topic_id': k, 'words_distribution': v, 'topic_label': '',
                   'topic_description': ''} for k, v in temp_topics.items()]
    else:
        topics = []

    model_values = {'model_id': model_id, 'files_prefix': files_prefix,
                    'modified': time(), 'training_documents_count': docs_count,
                    'status': model_status,
                    'training_parameters': {
                        'min_document_frequency': model.training_min_df,
                        'max_document_frequency': model.training_max_df,
                        'chunk_size': model.chunksize,
                        'min_passes': model.passes
                    }, 'number_of_topics': model.training_number_of_topics_to_extract,
                    'topics': topics,
                    'language': model.language,
                    'use_lemmer': model.training_use_lemmer
                    }

    # insert new data
    db_utils.upsert_model(model_id, model_values)


def update_model_status(model_id, model_status, model_values=None):
    """
    Updates the model status
    :param model_id:
    :param model_status: Model status should be one of LdaModelHelper.status_*
    :param model_values:
    :return:
    """
    if model_status == LdaModelHelper.status_completed:
        if model_values is None:
            model_values = {}
        model_values['process_id'] = None

    return db_utils.update_model_status(model_id, model_status, model_values)


def get_similar_documents(model_id, doc_id):
    model = db_utils.get_model(model_id)
    topics_assignment_from_db = db_utils.get_assigned_topics(model_id, doc_id)
    doc_topics_vector = transform_topics_assignment_from_db_to_vector(model['number_of_topics'],
                                                                      topics_assignment_from_db)

    return get_similar_documents_by_vector(model_id, doc_topics_vector)


def get_similar_documents_for_query(model_id, text):
    """
    Return documents similar to the query or an empty set if an error occurs or the query has no words after preprocessing
    :param model_id:
    :param text:
    :return:
    """
    model = db_utils.get_model(model_id)
    topics_assignment = assign_topics_for_query(model_id, text)

    if len(topics_assignment) != 0:
        topics_vector = transform_topics_assignment_from_lda_to_vector(model['number_of_topics'], topics_assignment[0])
        # print(topics_vector)
        return get_similar_documents_by_vector(model_id, topics_vector)
    else:
        return []


def transform_topics_assignment_from_db_to_vector(n_topics, topics_assignment):
    """
    Transform a single topic assignment in format [{'topic_id':id, 'topic_weight':value},...] in a vector of values
    """

    doc_topics_vector = [0.0] * n_topics
    for t in topics_assignment:
        doc_topics_vector[int(t['topic_id'])] = float(t['topic_weight'])

    return doc_topics_vector


def transform_topics_assignment_from_lda_to_vector(n_topics, topics_assignment):
    """
    Transform a single topic assignment in format [(id, value),(id, value),(id, value)] in a vector of values

    :param n_topics:
    :param topics_assignment:
    :return:
    """
    topic_vector = [0.0] * n_topics
    for t in topics_assignment:
        topic_vector[t[0]] = t[1]

    return topic_vector


def get_similar_documents_by_vector(model_id, source_topics_vector):
    # get all documents and trasform all to vectors
    docs = db_utils.get_all_documents(model_id)
    result_docs = [None] * len(docs)
    for i,d in enumerate(docs):
        topics_vector = transform_topics_assignment_from_db_to_vector(len(source_topics_vector),
                                                               db_utils.get_assigned_topics(model_id, d['document_id']))

        result_docs[i] = {
            'document_id': d['document_id'],
            'topics_vector': topics_vector,
            'similarity_score': 1 - spatial.distance.cosine(source_topics_vector, topics_vector),
            'model_id': model_id
        }

    return sorted(result_docs, key=lambda x: x['similarity_score'], reverse=True)


def assign_topics_for_query(model_id, text, threshold=0.0):
    """
    Retrieve topics assignment for the specified query in the model.
    Return None if the specified model is not found.
    Return an empty topic assignment if an error occurs during computation or if the query has no relevant word after preprocessing.
    :param model_id:
    :param text:
    :return:
    """
    model_info = db_utils.get_model(model_id)
    if model_info is None:
        return None

    # load model from file
    model = LdaModelHelper(model_info['number_of_topics'], model_info['language'])
    model.load_model_from_file(os.path.join(config.data_path, model_info['files_prefix']))

    topic_assignment = model.compute_topic_assignment_for_query(text)

    return topic_assignment


def assign_topics_for_new_doc(model_id, doc_id, doc_content, save_on_db=True):
    """
    Compute topics assignment for a new document and save on db
    :param model_id:
    :param doc_id:
    :param doc_content:
    :param save_on_db:
    :return:
    """

    model_info = db_utils.get_model(model_id)
    if model_info is None:
        return None

    # load model from file
    model = LdaModelHelper(model_info['number_of_topics'], model_info['language'])
    model.load_model_from_file(os.path.join(config.data_path, model_info['files_prefix']))

    topic_assignment = model.compute_topic_assignment([doc_content])
    if save_on_db:
        save_topic_assignment([{'doc_id': doc_id, 'doc_content': doc_content}], topic_assignment, model_id)

    return topic_assignment


def assign_topics_for_new_docs(model_id, docs, save_on_db=True):
    """
    Compute topics assignment for a list of new documents and save on db
    :param model_id:
    :param docs: list of jsons each one in format {'doc_id': 1, 'doc_content': 'c1'}
    :param save_on_db:
    :return:
    """
    model_info = db_utils.get_model(model_id)
    if model_info is None:
        return None

    # load model from file
    model = LdaModelHelper(model_info['number_of_topics'], model_info['language'])
    model.load_model_from_file(os.path.join(config.data_path, model_info['files_prefix']))

    doc_contents = []
    document_ids = []

    for d in docs:
        doc_contents.append(d['doc_content'])
        document_ids.append(d['doc_id'])

    topic_assignments = model.compute_topic_assignment(doc_contents)
    if save_on_db:
        save_topic_assignment(docs, topic_assignments, model_id)

    return topic_assignments, document_ids
