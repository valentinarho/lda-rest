import os

from flask_restful import Resource, marshal, reqparse

from api import api_utils
from db import db_utils
from model import lda_utils
from flask import jsonify
from scripts import scheduler
import config
import json
import logging

class Models(Resource):
    # parser = reqparse.RequestParser(bundle_errors=True)
    # parser.add_argument('rating', default=2, required=False, type=int, help='blablabla')
    # args = parser.parse_args()

    def get(self):
        """
        Retrieve all available models from db.
        :return:
        """

        models = {'models': db_utils.get_all_models()}
        # models = api_utils.filter_only_exposed(models, config.exposed_fields['models'])
        return api_utils.prepare_success_response(200, 'Models retrieved.', marshal(models, api_utils.models_fields)), 200

    def put(self):
        """
        Schedule the computing of a new model.
        :return:
        """

        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('model_id', required=True, type=str, help='The identifier of the model to create')

        parser.add_argument('number_of_topics', required=True, type=int,
                            help='The number of topics to extract from the documents.')

        parser.add_argument('language', default=config.defaults['language']['value'], required=False,
                            type=str,
                            help=config.defaults['language']['description'])

        parser.add_argument('use_lemmer', default=config.defaults['use_lemmer']['value'], required=False,
                            type=bool,
                            help=config.defaults['use_lemmer']['description'])

        parser.add_argument('min_df', default=config.defaults['min_df']['value'], required=False,
                            type=int,
                            help=config.defaults['min_df']['description'])

        parser.add_argument('max_df', default=config.defaults['max_df']['value'], required=False,
                            type=float,
                            help=config.defaults['max_df']['description'])

        parser.add_argument('chunksize', default=config.defaults['chunksize']['value'], required=False,
                            type=int,
                            help=config.defaults['chunksize']['description'])

        parser.add_argument('waiting_seconds', default=config.defaults['waiting_seconds']['value'], required=False,
                            type=int,
                            help=config.defaults['waiting_seconds']['description'])

        parser.add_argument('num_passes', default=config.defaults['num_passes']['value'], required=False,
                            type=int,
                            help=config.defaults['num_passes']['description'])

        parser.add_argument('data_filename', required=False,
                            type=str, default=None,
                            help='The filename of the input data. The file should be contained in the /data folder.')

        parser.add_argument('data', required=False,
                            type=api_utils.json_dictionary, default=None,
                            help='A dictionary containing documents ids as keys and documents content as values.')

        parser.add_argument('data_endpoint', default=None, required=False,
                            type=str,
                            help='The rest endpoint from which retrieve documents.')

        parser.add_argument('assign_topics', default=config.defaults['assign_topics']['value'], required=False,
                            type=bool,
                            help=config.defaults['assign_topics']['description'])

        args = parser.parse_args()

        # TODO implement retrieval from data endpoint
        if args['data_filename'] is None and args['data'] is None:

            if args['data_endpoint'] is not None:
                message = 'Retrieval of documents from endpoint is not yet implemented. Provide a correct data_filename or a data dictionary.'
            else:
                message = 'Missing input documents information, provide a correct data_filename or a data dictionary.'

            return api_utils.prepare_error_response(500, message, more_info=args)


        # elif args['data'] is not None:
        #
        #     try:
        #         data = json.loads(args['data'])
        #     except:
        #         return api_utils.prepare_error_response(500, 'Format not valid for data field. Should be a json encoded string.', more_info=args)

        status_code, model_values = lda_utils.compute_model(args['model_id'], args['number_of_topics'], language=args['language'], use_lemmer=args['use_lemmer'], min_df=args['min_df'], max_df=args['max_df'], chunksize=args['chunksize'],
                  num_passes=args['num_passes'], data_filename=args['data_filename'], data_endpoint=args['data_endpoint'], data=args['data'], assign_topics=args['assign_topics'], waiting_time=args['waiting_seconds'])

        if status_code == 200:
            return api_utils.prepare_success_response(200, 'Models computation scheduled.',
                                                      data={'parameters': args, 'model': marshal(model_values, api_utils.model_fields)},
                                                      more_info={'message': 'The model computation will start in {} seconds. '
                                                                            'To cancel make a DELETE request to the delete route.'
                                                      .format(args['waiting_seconds'])}), 200
        else:
            return api_utils.prepare_error_response(status_code, 'Model id already exists.', more_info=args)


class Model(Resource):

    def get(self, model_id):
        """
        Get all info related to model model_id

        :param model_id:
        :return:
        """
        model = db_utils.get_model(model_id)
        if model is None:
            return jsonify(api_utils.prepare_error_response(404,
                                                    'Model id not found.',
                                                    more_info={'model_id': model_id}))

        return api_utils.prepare_success_response(200, 'Model retrieved.',
                                                  marshal(model, api_utils.model_fields)), 200

    def delete(self, model_id):
        """
        Delete model model_id

        :param model_id:
        :return:
        """

        # delete model and files on disk
        status_code, deleted_model = lda_utils.delete_model(model_id)

        if status_code == 404:
            return api_utils.prepare_error_response(404, 'Model not found.',
                                                      more_info={'model_id': model_id}), 404

        else:
            return api_utils.prepare_success_response(200, 'Model deleted.',
                                                      more_info=marshal(deleted_model,
                                                                        api_utils.model_fields)), 200

    def patch(self, model_id):
        """
        Modifies the description of a model

        :param model_id: the model id
        :return:
        """
        # TODO to be implemented
        return api_utils.prepare_error_response(500, 'Method to be implemented.',
                                                      more_info={'model_id': model_id}), 500

