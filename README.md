# Movie Ranker

Movie Ranker is a web application that provides information about movies stored in Azure Cosmos DB. Users can explore the list of movies, view details, and generate summaries for each movie using Hugging Face API.
Link: https://serverless-movies-api.azurewebsites.net/api/GetMovies

![movie ranker](https://github.com/ipconfig2/Serverless-Movies-API/assets/78152356/58e51ab3-5194-451a-948e-0b16000ad6dd)

## Features

- **Movie Listing:** Display a list of movies with essential details.
- **Movie Details:** View detailed information about each movie.
- **Summary Generation:** Generate movie summaries using Hugging Face API.
- **Dark Theme:** Stylish dark theme for a better user experience.

## Setup

1. **Azure Cosmos DB:**
    - Set up an Azure Cosmos DB instance and create a database with the name 'Movies' and a container with the name 'Movies'.
    - Populate the container with movie data, including fields like title, place, releaseYear, genre, and coverUrl.

2. **Environment Variables:**
    - Set the required environment variables in your Azure Function App:
        - `CosmosDBEndpoint`: URL of your Cosmos DB instance.
        - `CosmosDBKey`: Primary key for Cosmos DB access.
        - `HUGGINGFACE_API_KEY`: API key for accessing Hugging Face API.

3. **Deployment:**
    - Deploy the Azure Function App containing the provided code.

4. **Accessing the Application:**
    - After deployment, you can access the Movie Ranker application using the specified routes.

## Usage

- **GetMovies:**
    - Navigate to the `/GetMovies` route to view the list of movies.
    - Click on the "Generate Summary" button for any movie to see a dynamically generated summary.

## API Routes

- **GetMovies:**
    - **Route:** `/GetMovies`
    - **Method:** GET
    - **Description:** Retrieve a list of movies.

- **GenerateSummary:**
    - **Route:** `/GenerateSummary`
    - **Method:** GET
    - **Parameters:** `title` (movie title)
    - **Description:** Generate a summary for a specific movie.

## Dependencies

- **Azure Functions SDK:** for creating serverless functions.
- **Azure Cosmos SDK:** for connecting to Azure Cosmos DB.
- **Requests:** for making HTTP requests to Hugging Face API.

## Contributions

Feel free to contribute to the project by opening issues or submitting pull requests. Follow the [contribution guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the [MIT License](LICENSE).
