# request / response utilities

# 200 - OK
# 404 - Not Found
# 500 - Internal Server Error
# 201 - Created
# 304 - Not Modified
# 400 - Bad Request
# 401 - Unauthorized
# 403 - Forbidden

from flask import jsonify
from flask_restful import fields

##
# Rest marshalling configurations
##

words_distribution_fields = {
    'w': fields.String,
    'w_weight': fields.Float
}

topic_assignment_fields = {
    'topic_id': fields.Integer,
    'topic_weight': fields.Float
}

topic_fields = {
    'topic_id': fields.Integer,
    'topic_label': fields.String(default=""),
    'topic_description': fields.String(default=""),
    'words_distribution': fields.List(fields.Nested(words_distribution_fields))
}

topics_fields = {
    'topics': fields.List(fields.Nested(topic_fields)),
    'model_id': fields.String
}

textual_query_fields = {
    'assigned_topics': fields.List(fields.Nested(topic_assignment_fields)),
    'model_id': fields.String,
    'textual_query': fields.String,
    'threshold': fields.Float
}

model_fields = {
    'model_id': fields.String,
    'model_description': fields.String,
    'created': fields.String,
    'modified': fields.String,
    'number_of_topics': fields.Integer,
    'status': fields.String,
    'training_documents_count': fields.Integer,
    'training_parameters': {
        'min_document_frequency': fields.Float(attribute='training_parameters.min_document_frequency'),
        'max_document_frequency': fields.Float(attribute='training_parameters.max_document_frequency'),
        'chunk_size': fields.Integer(attribute='training_parameters.chunk_size'),
        'min_passes': fields.Integer(attribute='training_parameters.min_passes')
    },
    'topics': fields.Url('topics', absolute=True),
    'documents': fields.Url('documents', absolute=True),
}

models_fields = {
    'models': fields.List(fields.Nested(model_fields))
}

document_fields = {
    'document_id': fields.String,
    'text': fields.String,
    'assigned_topics': fields.List(fields.Nested(topic_assignment_fields)),
    'model_id': fields.String,
    'threshold': fields.Float,
    'similar_documents': fields.Url('doc_neighbors', absolute=True)
}

document_fields_restricted = {
    'document_id': fields.String,
    'model_id': fields.String,
    'document_details': fields.Url('document', absolute=True),
    'similar_documents': fields.Url('doc_neighbors', absolute=True)
}

documents_fields = {
    'documents': fields.List(fields.Nested(document_fields_restricted))
}

neighbor_fields = {
    'document_id': fields.String,
    'model_id': fields.String,
    'document_details': fields.Url('document', absolute=True),
    'similar_documents': fields.Url('doc_neighbors', absolute=True),
    'similarity_score': fields.Float
}

neighbors_fields = {
    'neighbors': fields.List(fields.Nested(neighbor_fields)),
    'similarity_method': fields.String,
    'number_of_similar_documents': fields.Integer,
    'query_text': fields.String,
    'source_document_id': fields.String,
    'model_id': fields.String
}

errors = {
    'ModelAlreadyExists': {
        'message': "A model with the specified model_id already exists.",
        'status': 409,
    },
    'ResourceDoesNotExist': {
        'message': "A resource with the specified id does not exists.",
        'status': 404,
        'extra': "Any extra information you want.",
    },
}

def prepare_error_response(error_status, error_message, more_info=None):
    """

    :param error_status: integer, status code of the error
    :param error_message: string, message describing the error
    :param more_info: dictionary of key-values, additional info
    :return:
    """
    response = {
        'status': error_status,
        'message': error_message,
        'more_info': more_info if more_info is not None else {}
    }

    return response #jsonify(response)


def prepare_success_response(response_status, response_message, data=None, more_info=None):
    """

    :param response_status: integer, status of the response
    :param response_message: string, message
    :param data: dictionary of key-values, data to give back to the sender
    :param more_info: dictionary of key-values, additional info
    :return:
    """
    response = {
        'status': response_status,
        'message': response_message,
        'more_info': more_info if more_info is not None else {}
    }

    if data is not None:
        response.update({'data': data})

    return response #jsonify(response)


def filter_only_exposed(data, exposed_keys, additional_information_function=None):
    """
    Filter data to show only

    :param data: dict or list of dict
    :param exposed_keys: list of strings
    :param additional_information_function:
    :return:
    """

    if data is None:
        return None

    new_data = [None] * len(data)
    if type(data) == list:
        for i, d in enumerate(data):
            new_data[i] = filter_only_exposed(d, exposed_keys)
        return new_data

    new_item = {}
    for k, v in data.items():
        if k in exposed_keys:
            new_item[k] = v

    if additional_information_function is not None:
        additional_information_function(new_item)

    return new_item
    # return {k: v for k, v in data.items() if k in exposed_keys}


def get_uri(endpoint_name, api_method='GET', uri_parameters=None, get_parameters=None):
    """

    :param endpoint_name: a string equals to the classname of the Resource that handles the uri
    :param api_method: the method to access
    :param uri_parameters: the parameters to replace within the uri, if empty the function returns the generic uri
    :param get_parameters: the get parameters to append at the end of the uri
    :return:
    """
    if get_parameters is None:
        get_parameters = {}

    if uri_parameters is None:
        uri_parameters = {}

    models_api_endpoint = '/models'
    topics_api_endpoint = '/topics'
    documents_api_endpoint = '/documents'
    neighbors_api_endpoint = '/neighbors'

    base_uri_by_endpoint_name = {
        'models': models_api_endpoint,
        'model': models_api_endpoint + '/<model_id>',
        'topics': models_api_endpoint + '/<model_id>' + topics_api_endpoint,
        'topic': models_api_endpoint + '/<model_id>' + topics_api_endpoint + '/<topic_id>',
        'documents': models_api_endpoint + '/<model_id>' + documents_api_endpoint,
        'document': models_api_endpoint + '/<model_id>' + documents_api_endpoint + '/<document_id>',
        'doc_neighbors': models_api_endpoint + '/<model_id>' + documents_api_endpoint + '/<document_id>' +
                         neighbors_api_endpoint,
        'text_neighbors': models_api_endpoint + '/<model_id>' + neighbors_api_endpoint

    }

    return base_uri_by_endpoint_name[endpoint_name]
