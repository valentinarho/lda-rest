"""
LDA Wrapper for OntoMap integration.

Algorithm
---------
The LDA algorithm is LdaModel in gensim library.

"""
import logging
import os
import time

import wikipedia
from gensim import matutils
from gensim.models import LdaModel

import config
from model import lda_utils


class LdaModelHelper:

    status_scheduled = 'scheduled'
    status_computing = 'computing'
    status_completed = 'completed'
    status_error = 'interrupted_with_error'

    def __init__(self, training_number_of_topics_to_extract, language, training_use_lemmer=True, training_min_df=2,
                 training_max_df=0.8, chunksize=2000, passes=2):
        """

        :rtype: LdaModelHelper
        :param training_use_lemmer:
        :param training_min_df: int or float, min document frequency / document proportion (if float < 1)
        to consider a term in the model
        :param training_max_df: int or float, max document frequency / document proportion (if float < 1)
        to consider a term in the model
        """

        # TODO implementare diversi linguaggi
        self.language = language

        self.analysis_use_lemmer = None
        self.analysis_min_df = None
        self.analysis_max_df = None

        self.analysis_corpus = None
        self.analysis_features_names = None
        self.analysis_documents = None

        self.training_number_of_topics_to_extract = training_number_of_topics_to_extract
        self.training_use_lemmer = training_use_lemmer
        self.training_min_df = training_min_df
        self.training_max_df = training_max_df
        self.chunksize = chunksize
        self.passes = passes

        self.training_corpus = None
        self.training_features_names = None
        self.analysis_documents = None
        self.training_documents = None

        self.lda_model = None
        self.model_computation_time = None

        self.topic_labels = None
        self.topic_assignment = None

    def set_analysis_parameters(self, analysis_use_lemmer=True, analysis_min_df=2, analysis_max_df=0.8):

        self.analysis_use_lemmer = analysis_use_lemmer
        self.analysis_min_df = analysis_min_df
        self.analysis_max_df = analysis_max_df

        # reset related fields
        self.topic_assignment = None
        self.topic_labels = None
        self.analysis_corpus = None
        self.analysis_features_names = None
        self.analysis_documents = None

    def generate_model_filename(self):
        return "_".join([str(time.time()), str(self.training_number_of_topics_to_extract), str(self.training_min_df),
                         str(self.training_max_df), str(self.training_use_lemmer)]).replace('.', '')

    def set_lda_model(self, lda_model):
        self.lda_model = lda_model

    #####################
    # Model computation
    #####################

    def compute_lda_model(self, texts):
        """
        Compute the lda model
        :return:
        """
        if self.training_corpus is None:
            self.compute_corpus(texts, parameters='training')

        if len(self.training_corpus) == 0:
            raise Exception('The training corpus is empty. Tune model computation parameters.')

        start = time.time()

        if self.passes == 2:
            passes = 10 if (len(self.training_corpus) / self.chunksize) < 10 else 2
        else:
            passes = self.passes

        id2word = {k: v for k, v in enumerate(self.training_features_names)}

        self.lda_model = LdaModel(self.training_corpus, id2word=id2word,
                                    num_topics=self.training_number_of_topics_to_extract,
                                    eval_every=1, passes=passes, chunksize=self.chunksize)
        end = time.time()

        self.model_computation_time = end - start

    def save_model_to_file(self, file_path):
        """

        :type file_path: str
        :param file_path: the path of the models file
        :return:
        """
        if self.lda_model is None:
            logging.error('The model has not been computed yet.')
            return False
        else:
            self.lda_model.save(file_path)

    def load_model_from_file(self, input_filepath):
        """

        :param input_folder:
        :return:
        """
        self.lda_model = LdaModel.load(input_filepath)


    def compute_corpus(self, texts, parameters='training'):
        """
        Compute the corpus in gensim format considering the specified set of parameters 'training' or 'analysis'.
        :param parameters:
        :param texts:
        :return:
        """
        if parameters == 'training':
            tf_matrix, tf_matrix_features_names, tf_matrix_docs_ids = self.compute_tf_matrix(texts, parameters)

            if len(tf_matrix_features_names) == 0:
                return []

            self.training_corpus = matutils.Sparse2Corpus(tf_matrix, documents_columns=False)
            self.training_features_names = tf_matrix_features_names
            self.training_documents = tf_matrix_docs_ids
            return self.training_corpus
        elif parameters == 'analysis':
            if self.lda_model is None:
                logging.error('The model has not been computed yet.')
                return None
            else:
                # Note: words not included in the model are ignored
                tf_matrix, tf_matrix_features_names, tf_matrix_docs_ids = self.compute_tf_matrix(texts, parameters)

                if len(tf_matrix_features_names) == 0:
                    return []

                corpus = [None] * tf_matrix.shape[0]

                if len(tf_matrix_features_names) != 0:
                    word2id = {self.lda_model.id2word[id]: id for id in self.lda_model.id2word.keys()}

                    for i in range(tf_matrix.shape[0]):
                        doc = tf_matrix.getrow(i)
                        _, cols = doc.nonzero()

                        corpus[i] = [None] * len(cols)
                        count = 0
                        for col in cols:
                            if tf_matrix_features_names[col] in word2id.keys():
                                corpus[i][count] = (int(word2id[tf_matrix_features_names[col]]), int(tf_matrix[i, col]))
                                count += 1

                        corpus[i] = corpus[i][:count]

                self.analysis_corpus = corpus
                self.analysis_features_names = tf_matrix_features_names
                self.analysis_documents = tf_matrix_docs_ids

                return self.analysis_corpus
        else:
            logging.error("Value not allowed for argument parameters. Allowed values are 'training' or 'analysis'.")
            return None

    def compute_corpus_single_query(self, text):
        """
        Compute the corpus in gensim format for a single query (this implies using special parameters for preprocessing)
        :param parameters:
        :param texts:
        :return:
        """

        if self.lda_model is None:
            logging.error('The model has not been computed or loaded yet.')
            return None
        else:
            # Note: words not included in the model are ignored
            stopwords_list = lda_utils.get_stopwords(self.language)
            tf_matrix, tf_matrix_features_names = lda_utils.compute_tf([text], stopwords_list, self.language,
                                                                       True, 1, 1.0)

            if len(tf_matrix_features_names) == 0:
                return []

            corpus = [None] * tf_matrix.shape[0]

            if len(tf_matrix_features_names) != 0:
                word2id = {self.lda_model.id2word[id]: id for id in self.lda_model.id2word.keys()}

                for i in range(tf_matrix.shape[0]):
                    doc = tf_matrix.getrow(i)
                    _, cols = doc.nonzero()

                    corpus[i] = [None] * len(cols)
                    count = 0
                    for col in cols:
                        if tf_matrix_features_names[col] in word2id.keys():
                            corpus[i][count] = (int(word2id[tf_matrix_features_names[col]]), int(tf_matrix[i, col]))
                            count += 1

                    corpus[i] = corpus[i][:count]

            return corpus, tf_matrix_features_names


    def compute_tf_matrix(self, texts, parameters='training'):
        """
        Compute the tf matrix using the specified set of parameters ('training' or 'analysis').
        If texts is not specified the system tries to retrieve data directly from the associated db.
        :param parameters: 'training' or 'analysis'
        :param texts: list of strings representing texts to transform.
        :return:
        """

        tf_matrix_docs_id = None
        if parameters == 'training' or parameters == 'analysis':

            stopwords_list = lda_utils.get_stopwords(self.language)

            if parameters == 'training':
                use_lemmer = self.training_use_lemmer
                min_df = self.training_min_df
                max_df = self.training_max_df
            else:
                use_lemmer = self.analysis_use_lemmer
                min_df = self.analysis_min_df
                max_df = self.analysis_max_df

            tf_matrix, tf_matrix_features_names = lda_utils.compute_tf(texts, stopwords_list, self.language, use_lemmer,
                                                                       min_df,
                                                                       max_df)
        else:
            logging.error("Value not allowed for argument parameters. Allowed values are 'training' or 'analysis'.")
            return None

        return tf_matrix, tf_matrix_features_names, tf_matrix_docs_id


    def compute_topic_assignment(self, texts):
        """
        Computes the topics assignment for each document w.r.t the specified topic_model

        Example of output = [[(25, 0.1174058544855012), (49, 0.82926081218116554)],
                            [(6, 0.29928250617927882), (49, 0.59405082715405444)]]

        :param texts:
        :return:
        """
        corpus = self.compute_corpus(texts, parameters='analysis')

        if len(corpus) == 0:
            raise Exception('The corpus is empty. Tune analysis parameters and check stopwords.')

        computed_assignment = self.lda_model[corpus]
        if texts is not None:
            # is the corpus related to analysis parameters
            self.topic_assignment = computed_assignment

        return computed_assignment

    def compute_topic_assignment_for_query(self, text):
        corpus, _ = self.compute_corpus_single_query(text)

        if corpus is None or len(corpus) == 0:
            raise Exception('The corpus is empty. Tune analysis parameters and check stopwords.')

        computed_assignment = self.lda_model[corpus]

        return computed_assignment

    #######################
    # Print functions
    #######################

    def print_topic_assignment(self, topic_assignment):
        """
        Print a topic assignment in a human readable format
        :param topic_assignment:
        :return:
        """
        print('\tTopic importance\tTopic description')
        for i, doc in enumerate(topic_assignment):
            print('Document {0}'.format(i))
            for a in doc:
                print()
                string_topic = a[0] if self.lda_model is None else self.lda_model.print_topic(a[0])
                print('\t{1:2f}\t\t{0}'.format(string_topic, a[1]))

    def print_all_topics(self, num_topics=10, num_words=20, try_to_disambiguate=False,
                         min_word_probabity_for_disambiguation=0.010):
        """
        Print topics from a given LdaModel
        """
        print('Print {0} topics'.format(num_topics))
        print('------------')
        for t in self.lda_model.show_topics(num_topics=num_topics, num_words=num_words, formatted=False):
            if try_to_disambiguate:
                possible_labels = self.__class__.label_topic_by_probability(self.lda_model.show_topic(t[0]),
                                                             min_word_probability=min_word_probabity_for_disambiguation)[
                                  :2]
                print('{0}:\t{1}\n'.format(t[0], possible_labels))
                print('{0}\n'.format(t[1]))
            else:
                print('{0}:\t{1}\n'.format(t[0], t[1]))

    def get_topic_description(self, topic_id, num_words=20):
        """
        Print topics from a given LdaModel
        """
        if self.lda_model is None:
            logging.error('The model has not been computed yet.')
        else:
            return self.lda_model.show_topic(topic_id, num_words)

    #######################
    # Labeling functions
    #######################

    def compute_topic_labels(self, labeling_mode='mixed', min_word_probability=0.01,
                             max_number_of_words_per_query=6, n_words_to_label=3):
        """
        The labeling is performed querying wikipedia with a set of representative words for the topic.
        The words are chosen with the parameter
        labeling_mode:
        - 'based_on_probability': considers all words with a weight (probability) greater than 0.010
        - 'based_on_top_words': considers the 3 most probable words for the topic
        - 'mixed': try with 'based_on_probability', if there are no results try with 'based_on_top_words'
        """

        if self.lda_model is None:
            logging.error('No LDA model loaded.')

        n_labels_to_save = 3
        self.topic_labels = {}

        # label topics
        for t in self.lda_model.show_topics(num_topics=self.training_number_of_topics_to_extract, num_words=40,
                                            formatted=False):
            topic_id = t[0]

            possible_labels = []
            if labeling_mode == 'mixed' or labeling_mode == 'based_on_probability':
                possible_labels = self.__class__.label_topic_by_probability(self.lda_model.show_topic(topic_id),
                                                             min_word_probability=min_word_probability,
                                                             max_words=max_number_of_words_per_query
                                                             )[:n_labels_to_save]

            if len(possible_labels) == 0:
                # try to disambiguate by n_words
                possible_labels = self.__class__.label_topic_by_number_of_words(self.lda_model.show_topic(topic_id),
                                                                 n_words=n_words_to_label)[
                                  :n_labels_to_save]

            for i in range(len(possible_labels), n_labels_to_save):
                # fill empty labels
                possible_labels.append('')

            self.topic_labels[topic_id] = possible_labels
            time.sleep(0.5)

    def get_topic_labels(self):
        if self.topic_labels is None:
            self.compute_topic_labels()

        return self.topic_labels


    def get_all_topics(self):
        """
        Return a dictionary where keys are topic ids (integers) and values are words distributions.
        Words distribution should be a dictionary where keys are words and values are words weights within the topic
        :rtype: dict
        :return:
        """

        topics = {}

        for t in self.lda_model.show_topics(num_topics=self.training_number_of_topics_to_extract, num_words=40,
                                            formatted=False):
            topic_id = t[0]
            topic_distr = self.get_word_frequencies(self.lda_model.show_topic(topic_id))

            topics[topic_id] = topic_distr

        return topics

    def _get_words_distribution(self, topic_id):
        """
        Return a a dictionary where keys are words and values are words weights within the topic

        :param topic_id: the topic index
        :rtype: dict
        :return:
        """
        topic_description = self.lda_model.show_topic(topic_id, config.max_number_of_words_per_topic)
        return self.__class__.get_word_frequencies(topic_description)


    @classmethod
    def delete_model_files(cls, folder_path, files_prefix):
        """
        Delete all files related to a model that have the specified file prefix
        :param folder_path:
        :param files_prefix:
        :rtype:
        :return: 200 if all files have been removed, 404 if files does not exist
        """
        if os.path.exists(os.path.join(folder_path, files_prefix)):
            files_to_remove = [
                files_prefix,
                files_prefix + ".state",
                files_prefix + ".expElogbeta.npy",
                files_prefix + ".id2word",
            ]

            for f in files_to_remove:
                os.remove(os.path.join(folder_path, f));

            return 200
        else:
            logging.error('[ERROR] Model files does not exists.')
            return 404

    #######################
    # Topic labeling
    #######################

    @classmethod
    def label_topic_by_probability(cls, topic_description, min_word_probability=0.010, max_words=6):
        """
        Try to disambiguate a topic considering all words with a weight greater than min_word_probability
        :param max_words:
        :param topic_description: is a list of pairs  (word, word_probability)
        :param min_word_probability: is the minimum probability for words
        :return: list of strings, possible wikipedia pages
        """
        words = [w for w, p in topic_description if p >= min_word_probability]
        words = words[:max_words]

        if len(words) == 0:
            # if no words are over the threshold return empty
            res = []
        else:
            res = wikipedia.search(' '.join(words))

        return res

    @classmethod
    def label_topic_by_number_of_words(cls, topic_description, n_words=5):
        """
        Try to disambiguate a topic considering top k words in its description
        :param n_words:
        :param topic_description: is a list of pairs  (word, word_probability)
        :return: list of strings, possible wikipedia pages
        """
        words = [t[0] for i, t in enumerate(topic_description) if i < n_words]

        if len(words) == 0:
            # if no words are over the threshold, take the first
            words = [topic_description[0][0]]

        res = wikipedia.search(' '.join(words))
        return res

    @classmethod
    def get_word_frequencies(cls, topic_description):
        """
        Given a topic description, returns the corresponding dictionary with words as keys
        and frequencies (weight * 1000) as values.
        :param topic_description: list of pairs (word, word_weight)
        :return:
        """
        frequencies = {w: f for w, f in topic_description}
        return frequencies


