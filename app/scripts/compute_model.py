import getopt
import logging
import os
import sys
import time
from multiprocessing import Process
from time import time, sleep

import config
from model import lda_utils
from model.lda_model import LdaModelHelper
import sys


class ComputeModelProcess(Process):
    def __init__(self, model_identifier, seconds_to_wait=60, *args):
        """

        :param timeout: number of seconds to sleep
        :param sleep_chunk:
        :param callback:
        :param args:
        """
        Process.__init__(self)

        self.seconds_to_wait = seconds_to_wait
        self.function_args = args
        logging.info(str(args))
        self.model_identifier = model_identifier

        # TODO questo comando non funziona perchè i sottoprocessi non possono chiamare questo metodo
        # signal.signal(signal.SIGUSR1, terminate)

    def run(self):
        sleep(self.seconds_to_wait)
        lda_utils.update_model_status(self.model_identifier, LdaModelHelper.status_computing, {'process_id': self.pid})
        try:
            compute_and_save_model(self.model_identifier, *self.function_args)
        except Exception as e:
            logging.exception("Error during the model computation.")
            _, _, tb = sys.exc_info()
            logging.error(tb.format_exc())
            lda_utils.update_model_status(self.model_identifier, LdaModelHelper.status_error, {'process_id': None})


    def get_pid(self):
        return self.pid


# Module functions

def setup_logging():
    logger = logging.getLogger()
    logging.basicConfig(filename=config.scripts_log_filepath, format='%(asctime)s %(message)s')
    logger.setLevel(logging.DEBUG)


def compute_and_save_model(model_id, n_topics, language, use_lemmer, min_df, max_df, chunksize, num_passes,
                           data_filename, data_endpoint, data, assign_topics):
    """

    :param model_id:
    :param n_topics:
    :param language:
    :param use_lemmer:
    :param min_df:
    :param max_df:
    :param chunksize:
    :param num_passes:
    :param data_filename: the filename (within data directory) from which extract data
    :param data_endpoint:
    :param data: dictionary of key:value where key is document id and value is document content
    :param assign_topics:
    """
    setup_logging()

    if data_filename is not None:
        # if documents_filename is set
        # read documents from file (json dump format)
        documents = lda_utils.read_documents_from_file(data_filename)
    elif data is not None:
        documents = [{'doc_id': k, 'doc_content': v} for k, v in data.items()]
    else:
        # else retrieve documents from endpoint
        # TODO to be implemented
        raise Exception('Retrieval from endpoint is not yet implemented.')
        # documents = lda_utils.get_documents_from_endpoint(data_endpoint)

    documents_texts = [d['doc_content'] for d in documents]

    # init the model
    lda_m = LdaModelHelper(n_topics, language, use_lemmer, min_df, max_df, chunksize, num_passes)
    # compute the model
    if len(documents_texts) == 0:
        logging.error("[ERROR] The list of documents for training is empty")
        sys.exit(2)
    # try:
    logging.info('Topic model computation started.')
    lda_m.compute_lda_model(documents_texts)
    logging.info('Topic model computation completed.')

    # save model files
    files_prefix = lda_m.generate_model_filename()
    lda_m.save_model_to_file(os.path.join(config.data_path, files_prefix))

    # save model in db
    lda_utils.save_or_update_model(lda_m, model_id, files_prefix, LdaModelHelper.status_completed,
                                   docs_count=len(documents_texts))

    if assign_topics:
        logging.info('Topics assignment started.')
        # assign documents to the model
        lda_m.set_analysis_parameters(lda_m.training_use_lemmer, lda_m.training_min_df, lda_m.training_max_df)
        topic_assignment = lda_m.compute_topic_assignment(documents_texts)
        # save on db
        lda_utils.save_topic_assignment(documents, topic_assignment, model_id)

        logging.info('Topics assignment completed.')

    # except Exception as e:
    #     print(str(e))
    #     logging.error(str(e))
    #     lda_utils.update_model_status(model_id, LdaModelHelper.status_error, {'last_error_message': str(e)})





if __name__ == '__main__':

    # MAIN not used

    argv = sys.argv[1:]

    setup_logging()

    # read parameters from command line
    n_topics = 50
    language = 'en'
    use_lemmer = True
    min_df = 1
    max_df = 0.8
    chunksize = 2000
    num_passes = 2
    data_filename = None
    data_endpoint = None
    model_id = int(time())
    assign_topics = False

    help_string = "compute_model.py -a -v <model identifier> -l <'it' or 'en'> -f <data filename> " + \
                  "-e <data endpoint> -t <number of topics> -p <'lemmer' or 'stemmer'> " + \
                  "-x <min document frequency> -y <max document frequency> -c <chunk size> " \
                  "-i <number of iterations over the dataset>"

    try:
        opts, args = getopt.getopt(argv, "hav:l:f:e:t:p:x:y:c:i:p:", [])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
            sys.exit()
        elif opt == '-a':
            assign_topics = True
        elif opt == '-v':
            model_id = arg
        elif opt == '-l':
            if arg not in ('it', 'en'):
                logging.error("[ERROR] Allowed values for {0}: {1}".format('-l', ('it', 'en')))
                sys.exit()
            language = arg
        elif opt == '-f':
            data_filename = arg
        elif opt == '-e':
            data_endpoint = arg
        elif opt == '-t':
            n_topics = int(arg)
        elif opt == '-p':
            options = ('lemmer', 'stemmer')
            if arg not in options:
                logging.error("[ERROR] Allowed values for {0}: {1}".format('-p', options))
                sys.exit()
            if arg == 'lemmer':
                use_lemmer = True
            else:
                use_lemmer = False
        elif opt == '-x':
            if '.' in arg:
                min_df = float(arg)
            else:
                min_df = int(arg)
        elif opt == '-y':
            if '.' in arg:
                max_df = float(arg)
            else:
                max_df = int(arg)
        elif opt == '-c':
            chunksize = int(arg)
        elif opt == '-i':
            num_passes = int(arg)

    compute_and_save_model(n_topics, language, use_lemmer, min_df, max_df, chunksize, num_passes, data_filename,
                           data_endpoint, None,
                           model_id, assign_topics)
