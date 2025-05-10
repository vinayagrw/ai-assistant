# AI Assistant Agent

An intelligent AI assistant that can answer questions about DuploCloud documentation and general knowledge queries using RAG (Retrieval-Augmented Generation) and internet search capabilities.

## Features

- RAG-based question answering using DuploCloud documentation
- Internet search capabilities for general knowledge queries
- RESTful API interface
- Web application interface
- Source citation and documentation
- Dockerized deployment

## AI Assistant Overview

 which is responsible for processing user queries related to DuploCloud documentation and general knowledge.

### Key Components:


1. **Flask Application Initialization**:
   - The Flask application is initialized with CORS (Cross-Origin Resource Sharing) enabled, allowing it to handle requests from different origins.
   - The API is set up using Flask-RESTx, which provides a structured way to define and document the API.
   - The `AIAssistant` class is initialized with configuration settings for the Ollama model and model priorities.
   - It loads documentation and initializes a vector database to store document embeddings for efficient querying.

2. **API Endpoints**:
   - **Query Endpoint (`/query`)**:
     - **Method**: `POST`
     - **Description**: This endpoint processes user queries. It expects a JSON body containing the query string.
     - The endpoint logs the incoming request, processes the query using the `AIAssistant`, and returns a structured response.
     - If an error occurs during processing, it logs the error and returns a generic error message.

   - **Health Check Endpoint (`/health`)**:
     - **Method**: `GET`
     - **Description**: This endpoint checks the health status of the API.
     - It returns a simple JSON response indicating whether the API is healthy or not. This is useful for monitoring and ensuring the service is operational.


3. **Documentation Management**:
   - The assistant can load documentation files and store their embeddings in **ChromaDB**, a vector database. This allows for quick retrieval of relevant information based on user queries
   - The documentation files were fetched from the DuploCloud GitHub repository using a shell script (`scripts/fetch_docs.sh`). This script automates the process of cloning the documentation repository and copying the relevant files to the local `docs` directory. The script ensures that the latest documentation is available for reference and integration with the AI Assistant.


4. **Query Processing**:
   - The `process_query` method handles incoming user queries. It determines if the query is related to DuploCloud and either generates a response using the documentation or performs an internet search.
   - If the query is related to DuploCloud, it retrieves relevant information from the vector database.

5. **Internet Search**:
   - The assistant can perform searches using both DuckDuckGo and SerpAPI. It attempts to find relevant information online if the query does not match any documentation.
   - The search results are processed and returned to the user, providing a comprehensive answer to their query.

6. **Chunking Techniques**:
   - Documents are split into chunks based on paragraph breaks using double newlines (\n\n).
   - Each chunk is treated as a separate document for embedding in the vector database, allowing for precise matching against user queries

7. **Evaluation Techniques**:

##### Direct Response Generation
   - Evaluates sentences based on word overlap with the user query to select the most relevant response.

##### Scoring Sentences
   Sentences are scored using multiple criteria:
   - **Exact Match**: Higher scores for sentences containing the query.
   - **Word Overlap**: Scores based on the number of overlapping words between the query and the sentence.
   - **Sentence Length**: Penalties for sentences that are too short or too long, with bonuses for ideal lengths.
   - **Proper Nouns**: Additional points for sentences containing proper nouns.
   - **Word Density**: Favoring sentences with a good ratio of unique words to total words.

8. **Scripts**:
This project includes several scripts for managing and interacting with the ChromaDB vector database. Below is a brief description of each script:

### `run_chroma_admin.py`

A script to run the ChromaDB Admin interface. It checks for the existence of the vector database, installs required packages, and starts the Streamlit application.

   ```bash
   python scripts/run_chroma_admin.py
   ```

### `streamlit_app.py`
This script implements a simple web application using Streamlit, allowing users to interact with the AI Assistant through a chat interface. Key functionalities include:

- **User Input**: A text input field where users can type their queries.
- **Session State Management**: Maintains conversation history between the user and the AI Assistant using Streamlit's session state.
- **API Integration**: Sends user queries to the Flask API endpoint (`/query`) and retrieves responses.
- **Conversation Display**: Shows the conversation history, displaying both user inputs and AI responses in a user-friendly format.

   ```bash
   python streamlit_app.py
   ```
Run above script after running your application. Follow below steps to run app in container.

## Project Structure

```
ai-assistant/
├── app/
│ ├── api/ # API endpoints for handling requests
│ ├── core/ # Core assistant logic, including AI processing and vector database management
│ ├── models/ # Data models for request and response schemas
│ ├── utils/ # Utility functions for logging and configuration management
│ └── config/ # Configuration files for application settings and parameters
├── docs/ # Documentation files for the AI Assistant
├── tests/ # Test files for unit and integration testing
├── Dockerfile # Docker configuration for containerization
├── requirements.txt # Python dependencies for the project
└── README.md # This file
```

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-assistant
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure SerpAPI**:
   - Sign up for a SerpAPI account at [SerpAPI](https://serpapi.com/).
   - After signing up, obtain your API key from the dashboard.
   - Add your SerpAPI key to the `.env` file:
     ```plaintext
     SERPAPI_API_KEY=your_api_key_here
     ```

## Installing Docker on Windows

1. **Download Docker Desktop**:
   - Go to the [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop) page.
   - Click on the "Download Docker Desktop" button.

2. **Install Docker Desktop**:
   - Run the downloaded installer.
   - Follow the installation instructions. You may need to enable WSL 2 (Windows Subsystem for Linux) if prompted.

3. **Start Docker Desktop**:
   - After installation, launch Docker Desktop from the Start menu.
   - Wait for Docker to start. You should see the Docker icon in the system tray.

4. **Verify Installation**:
   - Open a command prompt or PowerShell and run the following command to verify that Docker is installed correctly:
     ```bash
     docker --version
     ```
## Docker Deployment:

1. **Build the Docker image**:
   ```bash
   docker build -t ai-assistant .
   ```

2. **Run the container**:
   ```bash
   **Run the container with the SerpAPI key**:

   docker run -p 8000:8000 -e SERPAPI_API_KEY=your_api_key_here ai-assistant
   ```
   ```


## Run Application locally

**Start the API server**:
   ```bash
   python run.py
   ```

### Execute Test cases

**Run the tests**:
   ```bash
   pytest -s tests/test_assistant.py
   ```

### Test AI Assistant
 AI Agent can be tested using swagger try out option. Sample request body is already set by default for API /query 

                  OR 

Run Streamlit app for Chat interface by running  below script. Make sure you have AI Assistant running in docker image. 

  ```bash
   python streamlit_app.py
   ```
Then access Web UI in any browser - http://localhost:8501/ 

## API Documentation

Refer to the API documentation: http://localhost:8000/ for details on available endpoints and usage.




  



