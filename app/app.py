import logging
# Path init
import os
import sys

from flask import Flask
from flask_restful import Api

import config
from api import api_utils
from api.documents_api import Documents, Document
from api.models_api import Models, Model
from api.neighbors_api import Neighbors
from api.topics_api import Topics, Topic

sys.path.append(os.path.abspath('.'))

# Flask init
app = Flask(__name__)
api = Api(app, errors=api_utils.errors)


# Mongo init
# client = db_utils.get_mongo_client()
# db = client[config.db_name]

# @app.route('/topics', methods=['GET'])
# def get_topics():
#     return utils.prepare_error_response(500, 'Internal Server Error', {'prova': 1})
#
#
# @app.route('/topics/<int:topic_id>', methods=['GET'])
# def get_topic(topic_id):
#     return jsonify({'topic_id': topic_id})


def setup_logging():
    logging.basicConfig(filename=config.app_log_filepath, level=logging.DEBUG)


if __name__ == "__main__":
    # setup logging
    # setup_logging()

    # setup api
    models_api_endpoint = '/models'
    topics_api_endpoint = '/topics'
    documents_api_endpoint = '/documents'
    neighbors_api_endpoint = '/neighbors'

    api.add_resource(Models, api_utils.get_uri('models'), methods=['GET', 'PUT'],
                     strict_slashes=False)
    api.add_resource(Model, api_utils.get_uri('model'), methods=['GET', 'PATCH', 'DELETE'],
                     strict_slashes=False)
    api.add_resource(Topics, api_utils.get_uri('topics'), methods=['GET', 'SEARCH'], strict_slashes=False)
    api.add_resource(Topic, api_utils.get_uri('topic'),
                     methods=['GET', 'PATCH'], strict_slashes=False)

    api.add_resource(Documents, api_utils.get_uri('documents'), methods=['GET', 'PUT'],
                     strict_slashes=False)
    api.add_resource(Document, api_utils.get_uri('document'),
                     methods=['GET', 'PATCH', 'DELETE'], strict_slashes=False)

    api.add_resource(Neighbors, api_utils.get_uri('doc_neighbors'), methods=['GET', 'POST'],
                     endpoint="doc_neighbors",
                     strict_slashes=False)
    api.add_resource(Neighbors, api_utils.get_uri('text_neighbors'),
                     methods=['GET', 'PATCH', 'DELETE'], endpoint="text_neighbors",
                     strict_slashes=False)
    api.add_resource(Documents, api_utils.get_uri('docs_topic'),
                     methods=['GET'], endpoint="docs_topic",
                     strict_slashes=False)

    app.run(host='0.0.0.0', debug=True)
