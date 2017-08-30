from flask_restful import Resource, reqparse, marshal

import config
from api import api_utils
from db import db_utils
from model import lda_utils


class Topics(Resource):

    def get(self, model_id):
        """
        Retrieve all topics associated to model_id or associated to a specified query

        :param model_id:
        :return:
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('threshold', default=0.0, required=False, type=float,
                            help='The minimum probability that a topic should have to be returned as related to the query string.')
        parser.add_argument('text', default=None, required=False, type=str,
                            help='The query to assign topics to.')

        args = parser.parse_args()

        if args['text'] is not None:
            data = {'model_id': model_id, 'threshold': args['threshold'], 'textual_query': args['text']}

            topics_assignment = lda_utils.assign_topics_for_query(model_id, args['text'], args['threshold'])
            if topics_assignment is None:
                response = "Error during topic extraction. Check logs."
                response_code = 500
            else:
                list_of_da = lda_utils.convert_topic_assignment_to_dictionary(topics_assignment)
                data['assigned_topics'] = list_of_da[0]['assigned_topics']
                response_code = 200
                response = "Topics extracted."

            marshalled = marshal(data, api_utils.textual_query_fields)
        else:
            # else restituisci la lista di topics
            data = {'topics': db_utils.get_all_topics(model_id), 'model_id': model_id}

            # data = api_utils.filter_only_exposed(data, config.exposed_fields['topics'])
            response = "Topics retrieved."
            response_code = 200
            marshalled = marshal(data, api_utils.topics_fields)

        if response_code == 200:
            return api_utils.prepare_success_response(response_code, response, marshalled)
        else:
            return api_utils.prepare_error_response(response_code, response, marshalled)

    def search(self, model_id):
        """
        Extracts topics from a specified query

        :param model_id:
        :return:
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('threshold', default=0.0, required=False, type=float,
                            help='The minimum probability that a topic should have to be returned as related to the query string.')
        parser.add_argument('text', default=None, required=True, type=str,
                            help='The query to assign topics to.')

        args = parser.parse_args()

        if args['text'].strip() is not None:
            data = {'model_id': model_id, 'threshold': args['threshold'], 'textual_query': args['text']}

            topics_assignment = lda_utils.assign_topics_for_query(model_id, args['text'], args['threshold'])
            if topics_assignment is None:
                response = "Error during topic extraction. Check logs."
                response_code = 500
            else:
                list_of_da = lda_utils.convert_topic_assignment_to_dictionary(topics_assignment)
                data['assigned_topics'] = list_of_da[0]['assigned_topics']
                response_code = 200
                response = "Topics extracted."

            marshalled = marshal(data, api_utils.textual_query_fields)
        else:
            response_code = 500
            marshalled = None
            response = "The text field is empty."

        if response_code == 200:
            return api_utils.prepare_success_response(response_code, response, marshalled)
        else:
            return api_utils.prepare_error_response(response_code, response, marshalled)

class Topic(Resource):
    def get(self, model_id, topic_id):
        """
        Get all info related to the topic topic_id in model model_id
        :param model_id:
        :param topic_id:
        :return:
        """
        data = db_utils.get_topic(model_id, int(topic_id))
        marshalled = marshal(data, api_utils.topic_fields)
        response = "Topic retrieved."

        return api_utils.prepare_success_response(200, response, marshalled)

    def patch(self, model_id, topic_id):
        """
        Edit the topic topic_id in model model_id changing some additional information (e.g. topic_label)
        :param model_id:
        :param topic_id:
        :return:
        """

        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('label', default=None, required=False, type=str,
                            help='The human readable label of the topic.')
        parser.add_argument('description', default=None, required=False, type=str,
                            help='The human readable description of the topic.')
        args = parser.parse_args()

        if args['label'] is not None or args['description'] is not None:
            topic = db_utils.update_topic(model_id, int(topic_id), args['label'], args['description'])
            if topic is None:
                return api_utils.prepare_error_response(500, 'Error during the update, check the provided topic id.')
            else:
                return api_utils.prepare_success_response(200, 'Topic updated.', data=marshal(topic, api_utils.topic_fields))
        else:
            return api_utils.prepare_error_response(500, 'Provide the label or the description to set.')

        # TODO controllare che ci sia almeno uno dei due argomenti e implementare il metodo

        return api_utils.prepare_error_response(500, "Not yet implemented.")
        # return api_utils.prepare_success_response(200, 'tutto ok', {'a': 1})
