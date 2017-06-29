from flask_restful import Resource, reqparse, marshal

from api import api_utils
from model import lda_utils


class Neighbors(Resource):

    def get(self, model_id, document_id=None):
        """
        Get documents similar to a known document (if document_id is specified) or to a textual string w.r.t. the specified model
        :param model_id: the model_id
        :param document_id: string, the id of the document to retrieve neighbors of
        :return:
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        data = {}

        if document_id is None:
            # Get all neighbors of the document described by text
            parser.add_argument('text', default=None, required=True, type=str,
                                help='The text to assign topics to.')

            parser.add_argument('limit', default=None, required=False, type=int,
                                help='The max number of documents to return.')

            # parser.add_argument('save', default=None, required=False, type=bool,
            #                     help='Save the current document in the db.')
            #
            # parser.add_argument('new_document_id', default=None, required=False, type=str,
            #                     help='If the save parameter is true, the new_document_id should be provided.')

            args = parser.parse_args()

            # list of dictionaries with keys 'document_id', 'similarity_score'
            ranked_similar_documents = lda_utils.get_similar_documents_for_query(model_id, args['text'])
            if args['limit'] is not None:
                ranked_similar_documents = ranked_similar_documents[:args['limit']]

            data['query_text'] = args['text']

        else:
            # get all neighbors of the document identified with document id in the specified model
            parser.add_argument('limit', default=None, required=False, type=int,
                                help='The max number of documents to return.')

            args = parser.parse_args()

            # list of dictionaries with keys 'document_id', 'similarity_score'
            ranked_similar_documents = lda_utils.get_similar_documents(model_id, document_id)

            if args['limit'] is not None:
                ranked_similar_documents = ranked_similar_documents[:args['limit']]

            data['source_document_id'] = document_id

        response = 'Similar documents retrieved.'

        data['neighbors'] = ranked_similar_documents
        data['number_of_similar_documents'] = len(ranked_similar_documents)
        data['model_id'] = model_id

        return api_utils.prepare_success_response(200, response, marshal(data, api_utils.neighbors_fields))
