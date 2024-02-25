import json
import logging
import os
from azure.cosmos import CosmosClient
from azure.functions import func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="GetMovies")
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Azure Cosmos DB connection details from environment variables
        cosmosdb_endpoint = os.environ.get("CosmosDBEndpoint")
        cosmosdb_key = os.environ.get("CosmosDBKey")
        database_id = 'Movies'
        container_id = 'Movies'

        # Initialize Cosmos DB client
        client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
        database = client.get_database_client(database_id)
        container = database.get_container_client(container_id)

        # Query Cosmos DB to get all movies
        query = 'SELECT * FROM c'
        items = container.query_items(query, enable_cross_partition_query=True)

        # Extract movie data and generate response
        movies = [
            {
                "title": item['title'],
                "place": item['place'],
                "releaseYear": item['releaseYear'],
                "genre": item['genre'],
                "coverUrl": item['coverUrl'],
            }
            for item in items
        ]

        # Return JSON response
        return func.HttpResponse(
            body=json.dumps(movies),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return func.HttpResponse("Internal Server Error", status_code=500)
