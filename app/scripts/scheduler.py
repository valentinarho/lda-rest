import os
import signal
from threading import Timer
from scripts import compute_model
from time import time
from scripts.compute_model import ComputeModelProcess


def schedule_model_computation(model_identifier, n_topics, language, use_lemmer, min_df, max_df, chunksize, num_passes, data_filename, data_endpoint,
                  data, assign_topics, waiting_time):
    # create the new process and start
    t = ComputeModelProcess(model_identifier, waiting_time, n_topics, language, use_lemmer, min_df, max_df, chunksize, num_passes, data_filename, data_endpoint,
                  data, assign_topics)
    t.start()


def unschedule_model_computation(process_id):
    if process_id is not None:
        try:
            # send SIGUSR1 to the process_id
            os.kill(process_id, signal.SIGINT)
        except ProcessLookupError:
            pass


def interrupt_model_computation(process_id):
    if process_id is not None:
        try:
            # send SIGUSR1 to the process_id
            os.kill(process_id, signal.SIGINT)
        except ProcessLookupError:
            pass
