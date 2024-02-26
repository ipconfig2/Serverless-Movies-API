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

        # Extract movie data and generate HTML response with embedded images and styles
        movies_html = """
            <html>
            <head>
                <style>
                    body {
                        background-color: #1f1f1f;  /* Dark background color */
                        color: #e0e0e0;  /* Text color */
                        font-family: 'Roboto', sans-serif; /* Use a custom font (Roboto in this case) */
                        padding: 20px;
                        line-height: 1.6; /* Improved line height for better readability */
                        margin: 0;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }

                    h1 {
                        color: #ffcc00;  /* Header text color */
                        text-align: center; /* Center-align the header */
                        margin-bottom: 30px;
                    }

                    ul {
                        list-style-type: none;
                        padding: 0;
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                    }

                    li {
                        background-color: #333333;  /* Darker background for list items */
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1); /* Add a subtle box shadow */
                        transition: transform 0.3s ease-in-out;
                    }

                    li:hover {
                        transform: scale(1.05); /* Scale up on hover for a subtle effect */
                    }

                    img {
                        width: 100%;
                        height: 200px;
                        object-fit: cover; /* Maintain aspect ratio while covering the container */
                        border-radius: 8px 8px 0 0;
                    }

                    .details {
                        padding: 20px;
                    }

                    strong {
                        color: #ffcc00;  /* Strong text color */
                    }
                </style>
            </head>
            <body>
                <h1>Movies</h1>
                <ul>
        """

        for item in items:
            movies_html += f"""
                    <li>
                        <img src='{item['coverUrl']}' alt='{item['title']} Cover'>
                        <div class='details'>
                            <strong>Title:</strong> {item['title']}<br>
                            <strong>Place:</strong> {item['place']}<br>
                            <strong>Release Year:</strong> {item['releaseYear']}<br>
                            <strong>Genre:</strong> {item['genre']}<br>
                        </div>
                    </li>
            """

        movies_html += """
                </ul>
            </body>
            </html>
        """

        # Return HTML response
        return func.HttpResponse(
            body=movies_html,
            mimetype="text/html",
            status_code=200
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return func.HttpResponse("Internal Server Error", status_code=500)
