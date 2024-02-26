import json
import logging
import os
from azure.cosmos import CosmosClient
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="GetMovies")
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Azure Cosmos DB connection details from environment variables
        cosmosdb_endpoint = os.environ.get("CosmosDBEndpoint")
        cosmosdb_key = os.environ.get("CosmosDBKey")
        database_id = 'Movies'
        container_id = 'Movies'

        # Initialize Cosmos DB client using the master key
        client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
        database = client.get_database_client(database_id)
        container = database.get_container_client(container_id)

        # Query Cosmos DB to get all movies
        query = 'SELECT * FROM c'
        items = container.query_items(query, enable_cross_partition_query=True)

        # Extract movie data and generate HTML response
        movies_html = "<html><body><h1>Movies</h1><ul>"

        for item in items:
            movies_html += f"<li>Title: {item['title']}, Place: {item['place']}, Release Year: {item['releaseYear']}, Genre: {item['genre']}, Cover Url: {item['coverUrl']}</li>"

        movies_html += "</ul></body></html>"

        # Return HTML response
        return func.HttpResponse(
            body=movies_html,
            mimetype="text/html",
            status_code=200
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return func.HttpResponse("Internal Server Error", status_code=500)
