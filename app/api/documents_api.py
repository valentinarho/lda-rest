from flask_restful import Resource, reqparse, marshal

import config
from api import api_utils
from db import db_utils
from model import lda_utils


class Documents(Resource):

    def get(self, model_id, topic_id=None):
        """
        Get all documents that have a topic assignment in model model_id

        :param model_id:
        :return:
        """
        topic_weight = 0.0

        if topic_id is not None:
            topic_id = int(topic_id)

            parser = reqparse.RequestParser(bundle_errors=True)
            parser.add_argument('threshold', default=0.0, required=False,
                                type=float, help='The minimum probability that the specified topic should '
                                     'have to consider that document as related.')

            args = parser.parse_args()
            topic_weight = args['threshold']

        data = {'documents': db_utils.get_all_documents(model_id, topic_id, topic_weight)}

        # data = api_utils.filter_only_exposed(data, config.exposed_fields['documents'])
        response = 'Documents retrieved.'

        return api_utils.prepare_success_response(200, response, marshal(data, api_utils.documents_fields)['documents'])

    def put(self, model_id):
        """
        Extracts topics from a specified document and save the document in the db

        :param model_id:
        :return:
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument('doc_content', required=False, type=str, default=None,
                            help='The document content.')
        parser.add_argument('doc_id', required=False, type=str, default=None,
                            help='The document id.')
        parser.add_argument('documents', required=False, type=api_utils.json_dictionary, default=None,
                            help='The documents to assign topics to.')
        parser.add_argument('save_on_db', required=False, type=bool, default=True,
                            help='True to save new assignments to db, False otherwise.')

        args = parser.parse_args()
        save_on_db = args['save_on_db']

        if args['doc_content'] is not None:

            data = {'model_id': model_id, 'document_id': args['doc_id'], 'document_content': args['doc_content']}

            topics_assignment = lda_utils.assign_topics_for_new_doc(model_id, args['doc_id'], args['doc_content'], save_on_db)

            if topics_assignment is None:
                response = "Error during topic extraction. Check logs."
                response_code = 500
            elif len(topics_assignment) == 0:
                data['assigned_topics'] = []
                response_code = 200
                response = "Topics extracted and document saved (attention: topics list is empty!)."
            else:
                list_of_da = lda_utils.convert_topic_assignment_to_dictionary(topics_assignment)
                data['assigned_topics'] = sorted(list_of_da[0]['assigned_topics'], reverse=True,
                                                 key=lambda d: d['topic_weight'])
                response_code = 200
                response = "Topics extracted and document saved."

            marshalled = marshal(data, api_utils.document_fields_restricted)
        elif args['documents'] is not None:
            data = {'model_id': model_id}
            documents = [{'doc_id': key, 'doc_content': args['documents'][key]} for key in args['documents']]
            topics_assignment, document_ids = lda_utils.assign_topics_for_new_docs(model_id, documents, save_on_db)

            if topics_assignment is None:
                response = "Error during topic extraction. Check logs."
                response_code = 500
            else:

                list_of_da = lda_utils.convert_topic_assignment_to_dictionary(topics_assignment)

                data['documents'] = [
                    {
                        'model_id': model_id,
                        'document_id': document_ids[ta['document_index']],
                        'doc_content': args['documents'][document_ids[ta['document_index']]],
                        'assigned_topics': ta['assigned_topics']
                    }
                    for ta in list_of_da
                ]


                response_code = 200
                response = "Topics extracted and documents saved."

            marshalled = marshal(data, api_utils.documents_fields)

        else:
            response_code = 500
            marshalled = None
            response = "Document content is missing."

        if response_code == 200:
            return api_utils.prepare_success_response(response_code, response, marshalled)
        else:
            return api_utils.prepare_error_response(response_code, response, marshalled)


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

