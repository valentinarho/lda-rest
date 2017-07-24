## OntoMap Integration

The system is composed by two Docker containers: 

* Python container, contains the API library code. This container is mapped on `localhost` on port `5000`.
* Mongodb container, contains the database server. The container is available with the `db` hostname on port `27017`. 

### Run the containers and the application

Download code, then: 
	
	docker-compose build
	docker-compose up
	docker-compose exec web python db/load_fake_data.py

### Python container composition

The main container is composed by

* a Flask application that exposes some REST routes (see below)
* a library with algorithms to compute and query the LDA model 
* some support tools to load initial data into the associated database
 
### Available APIs

Following a table describing the available APIs: 

| Endpoint | Http request | Description | Parameters | 
| --- | --- | --- | --- |
| models/ | GET | Lists all models | - |
| models/ | PUT | Creates a new model w.r.t. the provided parameters | * `model_id`: str, the id of the model to be created; * `number_of_topics`: int, the number of topics to extract; * `language`: 'en', the language of the documents; * `use_lemmer`: bool, true to perform lemmatisation, false to perform stemming; * `min_df`: int, the minimum number of documents that should contain a term to consider it; * `max_df`: float, the maximum percentage of documents that should contain a term to consider it as valid; * `chunksize`: int, the size of a chunk in LDA; * `num_passes`: int, the minimum number of passes through the dataset during learning with LDA;  * `waiting_seconds`: int, the number of seconds to wait before starting the learning; * `data_filename`: str, the filename in the 'data' folder that contains data, the file should contain a json dump of documents each one with `doc_id` and `doc_content` keys; * `data`: json dictionary, a dictionary of documents, containing document_id as key and document_content as value; * `assign_topics`: bool, true to assign topics to the newly created model and to save on db, false to ignore assignments for the learning documents; |  
| models/`<model-id>` | GET | Shows detailed information about model with id `<model-id>` | | 
| models/`<model-id>`/documents/ | GET | Lists all documents assigned to the model with id `<model-id>` | - |
| models/`<model-id>`/documents/ | DELETE | Delete the model with the specified id, stops the computation if scheduled or performed | - |
| models/`<model-id>`/documents/`<doc-id>` | GET | Shows detailed information about document with id `<doc-id>` in model `<model-id>`| * `threshold`: float, the minimum probability that a topic should have to be returned as associated to the document.| 
| models/`<model-id>`/neighbors/ | GET | Computes and shows documents similar to the specified text.| * `text`: str, the text to categorize; * `limit`: int, the maximum number of similar documents to extract. |
| models/`<model-id>`/documents/`<doc-id>`/neighbors/ | GET | Computes and shows documents similar to the document identified with `<doc-id>`.| * `limit`: int, the maximum number of similar documents to extract. |
| models/`<model-id>`/topics/ | GET | Lists all topics related to the model with id `<model-id>`, or, if `text` parameter is specified computes and returns all topics assigned to the text. | * `text`, str, the text to compute topics for; * `threshold`, float, the min weight of a topic to be retrieved. |
| models/`<model-id>`/topics/`<topic-id>` | GET | Shows detailed information about topic with id `<topic-id>` in model `<model-id>`| * `threshold`: float, the minimum probability that a topic should have to be returned as associated to the document.| 


### Load sample data

To invoke the modules that loads fake data into the database run, from the machine that is running Docker, the following command: 

    docker-compose exec web python db/load_fake_data.py


### Database 

To connect directly to the mongodb instance:

* connect to the machine that hosts docker with ssh (optional: only if it is not the current machine)
* the db is available on host 'db' port 27017

#### Models

When asking for model's detailed information, the required model can be in one of the following statuses: 

* `scheduled`, the model computation will start after the specified waiting period
* `computing`, the model computation has been started and is currently running
* `completed`, the model computation is finished and the model is stable
* `killed`, the model computation has been interrupted by an error 

#### Languages
The language can be specified during in model creation message. Each model can handle only one language, chosen from: 

* `en` for english documents
* `it` for italian documents, stopwords are available in `/app/resources` folder and lemmatisation is performed with `MorphIt`

#### Documents

During model computation it is possible to load documents in two ways: 

* load from file: provide the `data_filename` field in the request. The file should be a json file and should be contained in the data folder. The json should be a list of dictionaries, each dictionary represent a document and contains the keys `doc_id` and `doc_content`. For example: 

		[
			{'doc_id': 'doc_1', 'doc_content': 'doc content 1'}, 
			{'doc_id': 'doc_2', 'doc_content': 'doc content 2'}, 
			{'doc_id': 'doc_3', 'doc_content': 'doc content 3'}
		]

* load directly: provide the documents in the `data` field. This field should contain a dictionary of key:values where keys are document ids and values are document contents. 

		{
			'doc_1': 'doc content 1', 
			'doc_2': 'doc content 2', 
			'doc_3': 'doc content 3'
		}

#### Useful commands 

To build all containers 

	docker-compose build

To run all containers 

	docker-compose up

To exec a command within a running container, e.g. load fake data into the mongo database

    docker-compose exec web COMANDO ARGS
