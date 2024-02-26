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

        # Create a set to store movie titles and avoid duplicates
        existing_movies = set()

        # Embed the styling within the HTML response for movies
        movies_html = f"""
            <html>
            <head>
                <title>Movie Ranker</title>
                <style>
                    /* Dark theme with a rainbow color animation for the title */
                    body {{
                        background-color: #1f1f1f;
                        color: #e0e0e0;
                        font-family: 'Arial', sans-serif;
                        padding: 20px;
                        line-height: 1.6;
                        margin: 0;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}
                    h1 {{
                        text-align: center;
                        margin-bottom: 30px;
                        font-size: 2em;
                        animation: rainbow 3s infinite;  /* Rainbow color animation */
                    }}
                    @keyframes rainbow {{
                        0% {{ color: #ff0000; }}   /* Red */
                        16.67% {{ color: #ff9900; }}  /* Orange */
                        33.33% {{ color: #ffff00; }}  /* Yellow */
                        50% {{ color: #33cc33; }}   /* Green */
                        66.67% {{ color: #3399ff; }}  /* Blue */
                        83.33% {{ color: #9933ff; }}  /* Purple */
                        100% {{ color: #ff0000; }}  /* Back to Red */
                    }}
                    ul {{
                        list-style-type: none;
                        padding: 0;
                        display: flex;  /* Display movies in a row */
                        flex-wrap: wrap;  /* Allow wrapping to the next line */
                        justify-content: space-around;  /* Evenly distribute items along the row */
                    }}
                    li {{
                        background-color: #333333;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 4px 8px rgba(224, 224, 224, 0.1);
                        transition: transform 0.3s ease-in-out;
                        margin: 10px;  /* Add margin between movies */
                        width: 300px;  /* Set a fixed width for each movie */
                    }}
                    li:hover {{
                        transform: scale(1.05);
                    }}
                    img {{
                        width: 100%;
                        height: auto; /* Allow the image to adjust its height while maintaining aspect ratio */
                        object-fit: cover;
                        border-radius: 8px 8px 0 0;
                    }}
                    .details {{
                        padding: 20px;
                    }}
                    strong {{
                        color: #2196F3;
                        font-weight: bold;
                    }}
                    .summary-button {{
                        background-color: #2196F3;
                        color: #ffffff;
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
                <h1>Movie Ranker</h1>
                <ul>
        """

        for item in items:
            title = item['title']
            # Check if the title is already processed to avoid duplicates
            if title not in existing_movies:
                movies_html += f"""
                    <li>
                        <img src='{item['coverUrl']}' alt='{title} Cover'>
                        <div class='details'>
                            <strong>Title:</strong> {title}<br>
                            <strong>Place:</strong> {item.get('place', 'N/A')}<br>
                            <strong>Release Year:</strong> {item.get('releaseYear', 'N/A')}<br>
                            <strong>Genre:</strong> {item.get('genre', 'N/A')}<br>
                            <button class='summary-button' onclick="generateSummary('{title}')">Generate Summary</button>
                            <div class='summary' id='summary-{title.replace(' ', '-')}'> </div>
                        </div>
                    </li>
                """
                existing_movies.add(title)

        movies_html += """
                </ul>
                <script>
                    const generatedSummaries = {};

                    function generateSummary(title) {
                        const summaryElement = document.getElementById('summary-' + title.replace(/ /g, '-'));

                        if (generatedSummaries[title]) {
                            // Use the already generated summary
                            summaryElement.innerHTML = '<strong>Summary:</strong> ' + generatedSummaries[title];
                        } else {
                            // Fetch the summary if not already generated
                            summaryElement.innerHTML = 'Generating summary...';
                            fetch('/api/GenerateSummary?title=' + encodeURIComponent(title))
                                .then(response => response.text())
                                .then(summary => {
                                    summaryElement.innerHTML = '<strong>Summary:</strong> ' + summary;
                                    generatedSummaries[title] = summary;  // Store the generated summary
                                })
                                .catch(error => {
                                    summaryElement.innerHTML = 'Error generating summary.';
                                    console.error(error);
                                });
                        }
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
