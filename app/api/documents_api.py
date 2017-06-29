from flask_restful import Resource, reqparse, marshal

import config
from api import api_utils
from db import db_utils


class Documents(Resource):

    def get(self, model_id):
        """
        Get all documents that have a topic assignment in model model_id

        :param model_id:
        :return:
        """
        data = {'documents': db_utils.get_all_documents(model_id)}

        # data = api_utils.filter_only_exposed(data, config.exposed_fields['documents'])
        response = 'Documents retrieved.'

        return api_utils.prepare_success_response(200, response, marshal(data, api_utils.documents_fields)['documents'])


class Document(Resource):

    def get(self, model_id, document_id):
        """
        Get all info about documents and topics assigned to document document_id in model model_id

        :param model_id:
        :param document_id: string, the document id
        :return:
        """

        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('threshold', default=config.defaults['minimum_threshold']['value'], required=False,
                            type=float,
                            help='The minimum probability that a topic should '
                                 'have to be returned as related to the document.')

        args = parser.parse_args()
        threshold = args['threshold']

        data = db_utils.get_document(model_id, str(document_id), topics_threshold=threshold)

        if data is None:
            return api_utils.prepare_error_response(400, 'Document not found', more_info={'model_id': model_id, 'document_id': document_id})

        data['threshold'] = threshold
        data['model_id'] = model_id

        return api_utils.prepare_success_response(200, 'Document retrieved.', marshal(data, api_utils.document_fields))
