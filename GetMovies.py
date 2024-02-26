import logging
import os
import requests
from azure.cosmos import CosmosClient
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Your Hugging Face API key goes here
huggingface_api_key = os.environ.get('HUGGINGFACE_API_KEY')

# Azure Cosmos DB connection details from environment variables
cosmosdb_endpoint = os.environ.get("CosmosDBEndpoint")
cosmosdb_key = os.environ.get("CosmosDBKey")
database_id = 'Movies'
container_id = 'Movies'

# Initialize Cosmos DB client using the master key
client = CosmosClient(cosmosdb_endpoint, cosmosdb_key)
database = client.get_database_client(database_id)
container = database.get_container_client(container_id)

# Hugging Face API URL
huggingface_api_url = "https://api-inference.huggingface.co/models/google/gemma-7b"

def get_movie_details(title):
    query = f'SELECT * FROM c WHERE c.title = "{title}"'
    items = container.query_items(query, enable_cross_partition_query=True)
    return next(iter(items), None)

def generate_summary_using_api(text, max_tokens=5):
    payload = {"inputs": text, "max_tokens": max_tokens}
    headers = {"Authorization": f"Bearer {huggingface_api_key}", "Content-Type": "application/json"}
    response = requests.post(huggingface_api_url, headers=headers, json=payload)

    if response.status_code != 200:
        return f"Error generating summary. Hugging Face API response: {response.status_code}"

    generated_summary = response.json()[0].get("generated_text", "Summary not available")
    return generated_summary

@app.route(route="GetMovies")
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Query Cosmos DB to get all movies
        query = 'SELECT * FROM c'
        items = container.query_items(query, enable_cross_partition_query=True)

        # Embed the styling within the HTML response for movies
        movies_html = f"""
            <html>
            <head>
                <style>
                    /* Your CSS styling here */
                    body {{
                        background-color: #1f1f1f;
                        color: #e0e0e0;
                        font-family: 'Roboto', sans-serif;
                        padding: 20px;
                        line-height: 1.6;
                        margin: 0;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}
                    h1 {{
                        color: #ffcc00;
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    ul {{
                        list-style-type: none;
                        padding: 0;
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                    }}
                    li {{
                        background-color: #333333;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
                        transition: transform 0.3s ease-in-out;
                    }}
                    li:hover {{
                        transform: scale(1.05);
                    }}
                    img {{
                        width: 100%;
                        height: 200px;
                        object-fit: cover;
                        border-radius: 8px 8px 0 0;
                    }}
                    .details {{
                        padding: 20px;
                    }}
                    strong {{
                        color: #ffcc00;
                    }}
                    .summary-button {{
                        background-color: #ffcc00;
                        color: #1f1f1f;
                        padding: 10px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        margin-top: 10px;
                    }}
                    .summary {{
                        background-color: #444444;
                        color: #ffffff;
                        padding: 10px;
                        margin-top: 10px;
                        border-radius: 5px;
                    }}
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
                        <strong>Place:</strong> {item.get('place', 'N/A')}<br>
                        <strong>Release Year:</strong> {item.get('releaseYear', 'N/A')}<br>
                        <strong>Genre:</strong> {item.get('genre', 'N/A')}<br>
                        <button class='summary-button' onclick="generateSummary('{item['title']}')">Generate Summary</button>
                        <div class='summary' id='summary-{item['title'].replace(' ', '-')}'> </div>
                    </div>
                </li>
            """

        movies_html += """
                </ul>
                <script>
                    function generateSummary(title) {
                        const summaryElement = document.getElementById('summary-' + title.replace(/ /g, '-'));
                        summaryElement.innerHTML = 'Generating summary...';

                        fetch('/api/GenerateSummary?title=' + encodeURIComponent(title))
                            .then(response => response.text())
                            .then(summary => {
                                summaryElement.innerHTML = '<strong>Summary:</strong> ' + summary;
                            })
                            .catch(error => {
                                summaryElement.innerHTML = 'Error generating summary.';
                                console.error(error);
                            });
                    }
                </script>
            </body>
            </html>
        """

        # Return HTML response for movies
        return func.HttpResponse(
            body=movies_html,
            mimetype="text/html",
            status_code=200
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return func.HttpResponse("Internal Server Error", status_code=500)


@app.route(route="GenerateSummary")
def generate_summary_handler(req: func.HttpRequest) -> func.HttpResponse:
    try:
        title = req.params.get('title')
        if not title:
            return func.HttpResponse("Title parameter missing", status_code=400)

        # Get movie details
        movie = get_movie_details(title)

        if not movie:
            return func.HttpResponse("Movie not found", status_code=404)

        # Generate summary using the Hugging Face API with max_tokens set to 5
        summary_text = f"Summary of the movie '{title}': {movie.get('title', 'N/A')} is a {movie.get('genre', 'N/A')} movie released in {movie.get('releaseYear', 'N/A')}."
        generated_summary = generate_summary_using_api(summary_text, max_tokens=5)

        return func.HttpResponse(
            body=generated_summary,
            mimetype="text/plain",
            status_code=200
        )
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return func.HttpResponse("Internal Server Error", status_code=500)
