# CineGraph AI: LLM-Powered GraphRAG Movie Knowledge Chatbot

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Optional License Badge -->

CineGraph AI is an interactive chatbot application that allows users to query a Neo4j graph database containing movie information using natural language. It leverages the Graph Retrieval-Augmented Generation (GraphRAG) pattern, utilizing Google's Gemini API to understand user queries, generate appropriate Cypher queries for Neo4j, retrieve context, and synthesize informative answers, complete with relevant movie posters.

<!-- Add a GIF or Screenshot here! -->
![CineGraph AI Demo](link_to_your_demo_image_or_gif.gif)
*(Replace the above line with a link to your actual demo image or GIF)*

## Features

*   **Natural Language Querying:** Ask questions about movies, actors, directors, and genres in plain English.
*   **GraphRAG Pipeline:**
    *   Uses Gemini API to generate Cypher queries based on user input and database schema.
    *   Retrieves relevant context (including movie details and poster URLs) from a Neo4j graph database.
    *   Uses Gemini API again to generate a final, context-aware response.
*   **Interactive Chat Interface:** Built with Streamlit, providing a familiar chat experience with conversation history.
*   **Dynamic Poster Display:** Automatically displays movie posters alongside relevant answers when available in the database.
*   **Efficient Resource Management:** Uses Streamlit's caching to initialize backend connections (Gemini, Neo4j) only once per session.

## Technology Stack

*   **Language:** Python 3.9+
*   **Web Framework:** Streamlit
*   **Database:** Neo4j Graph Database
*   **LLM:** Google Generative AI (Gemini API)
*   **Neo4j Driver:** py2neo
*   **Configuration:** python-dotenv
*   **Core Logic:** Custom Python scripts (`Querying.py`, `streamlit_app.py`)

## Architecture / How it Works

1.  **User Input:** The user types a message into the Streamlit chat interface.
2.  **Streamlit Backend:** `streamlit_app.py` receives the message.
3.  **Cypher Generation:** The user's prompt is sent to the Gemini API (via `Querying.py`) along with the Neo4j schema description to generate a Cypher query.
4.  **Neo4j Query:** The generated Cypher query is executed against the Neo4j database using `py2neo` to retrieve relevant context (movie nodes, person nodes, relationships, properties like poster URLs).
5.  **Response Synthesis:** The original user prompt and the retrieved Neo4j context are sent back to the Gemini API (via `Querying.py`) to generate a final, natural language answer.
6.  **Poster Extraction:** The application parses the context data retrieved from Neo4j to extract relevant movie poster URLs.
7.  **Streamlit Frontend:** The final text answer and extracted poster URLs are sent back to the Streamlit app, which displays them in the chat interface.

## Setup and Installation

Follow these steps to set up and run the project locally:

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory-name>
    ```

2.  **Install Python:** Ensure you have Python 3.9 or newer installed on your system.

3.  **Set Up Neo4j:**
    *   Install and run a Neo4j instance (e.g., via Neo4j Desktop or Docker).
    *   Note down your Neo4j connection URI (e.g., `bolt://localhost:7687`), username, and password.
    *   Create a database (e.g., `graphrag` or use the default `neo4j`).
    *   **(Optional - If Database is Empty):** Populate the database using the provided CSV data:
        ```bash
        # Make sure your venv is active first (see step 5)
        python CreateDatabase.py
        ```
        *(Requires `pandas` - add `pandas` to `requirements.txt` if needed for this step)*

4.  **Create `.env` File:**
    *   Create a file named `.env` in the root project directory.
    *   Add your API key and Neo4j credentials to this file (see Configuration section below).
    *   **Important:** Add `.env` to your `.gitignore` file to avoid committing secrets.

5.  **Create and Activate Virtual Environment:**
    ```bash
    # Create venv using your Python 3.9+ installation
    python -m venv venv
    # Activate venv
    # Windows:
    .\venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

6.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure your Neo4j database is running.
2.  Make sure your virtual environment is activated.
3.  Run the Streamlit application from the project root directory:
    ```bash
    streamlit run streamlit_app.py
    ```
4.  Streamlit will provide a local URL (usually `http://localhost:8501`). Open this URL in your web browser.
5.  Start chatting with CineGraph AI!

## Configuration (`.env` File)

Create a `.env` file in the project root with the following variables:

```dotenv
# .env

# Google API Key for Gemini
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"

# Neo4j Connection Details
NEO4J_URI="bolt://localhost:7687" # Or your Neo4j instance URI
NEO4J_USERNAME="neo4j" # Your Neo4j username
NEO4J_PASSWORD="YOUR_NEO4J_PASSWORD_HERE"
NEO4J_DATABASE="graphrag" # The specific Neo4j database name to use
