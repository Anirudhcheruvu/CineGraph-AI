import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
# Keep Node, Relationship if needed elsewhere, but not for querying funcs
from py2neo import Graph

# Configure logging (optional, Streamlit handles its own)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class ClientHandler():
    def __init__(self):
        load_dotenv()  # Ensure env vars are loaded when creating client
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logging.error("GOOGLE_API_KEY not found in environment variables.")
            raise ValueError("GOOGLE_API_KEY not found.")

        # Configure the API key globally for the genai module
        genai.configure(api_key=api_key)

        # Store the configured module itself or initialize a default model
        # Storing the module allows using different models later if needed
        # Or, initialize the specific model you use most often.
        # Let's initialize the model directly since generate_content is called on it.
        # We'll use "gemini-pro" as a default, adjust if needed.
        self.model = genai.GenerativeModel('gemini-2.0-flash')

        logging.info("Gemini Client Configured and Model Initialized.")

    # Modify get_client to return the model instance
    def get_model(self):
        # Rename this method for clarity
        return self.model
# --- Graph Connection Function (New) ---


def get_neo4j_graph():
    """Initializes and returns the Neo4j graph connection."""
    load_dotenv()  # Ensure env vars are loaded
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "GraphRAG")
    # Use env var for db name
    db_name = os.getenv("NEO4J_DATABASE", "graphrag")

    if not password:
        logging.error("NEO4J_PASSWORD not found in environment variables.")
        raise ValueError("NEO4J_PASSWORD not found.")

    try:
        graph = Graph(uri, auth=(user, password), name=db_name)
        # Optional: Test connection
        graph.run("RETURN 1")
        logging.info(
            f"Neo4j Graph connection established to database '{db_name}'.")
        return graph
    except Exception as e:
        logging.error(
            f"Failed to connect to Neo4j at {uri} as user {user}: {e}", exc_info=True)
        raise ConnectionError(f"Failed to connect to Neo4j: {e}")


# --- Querying Functions (Modified to accept client/graph) ---

def database_stats_Generator(graph):  # Pass graph object
    """Generates and prints database stats."""
    try:
        node_query = """
        MATCH (n)
        UNWIND labels(n) as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        """
        node_stats = graph.run(node_query).data()
        logging.info("Node stats by label:")
        logging.info(node_stats)

        relationship_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
        """
        relationship_stats = graph.run(relationship_query).data()
        logging.info("Relationship stats by type:")
        logging.info(relationship_stats)
        return node_stats, relationship_stats
    except Exception as e:
        logging.error(f"Error getting database stats: {e}", exc_info=True)
        return None, None


# Accept client and graph
def context_generator(query: str, model: genai.GenerativeModel, graph: Graph):
    """Generates Cypher, runs it, and returns context."""
    system_instruction = """Using the below Neo4j database description, Create a CYPHER query to get the necessary context for another LLM to generate an appropriate output.
The query should retrieve relevant information based on the user's question, including movie titles and poster URLs when movies are involved.
Return ONLY the Cypher query. No explanation, preamble, or markdown formatting (like ```cypher```) is needed.

Database Schema:

Nodes:
1)  Movie: Represents individual movies.
    *   Properties: `title` (string, primary identifier), `overview` (string), `poster` (string URL), `gross` (string or number), `rating` (float)
2)  Person: Represents individuals (directors and stars).
    *   Properties: `name` (string, lowercase, primary identifier)
3)  Genre: Represents movie genres.
    *   Properties: `name` (string, lowercase, primary identifier)

Relationships:
1)  `DIRECTED`: `(Person)-[:DIRECTED]->(Movie)`
2)  `STARS_IN`: `(Person)-[:STARS_IN]->(Movie)`
3)  `OF_GENRE`: `(Movie)-[:OF_GENRE]->(Genre)`
4)  `ASSOCIATED_WITH`: `(Person)-[:ASSOCIATED_WITH]->(Genre)`

Important for query generation:
*   Match `Person` or `Genre` nodes using the lowercase `name` property.
*   The `title` property for `Movie` nodes retains original casing.
*   Ensure relationship directions are correct.
*   When returning movie information, include the `poster` property if available. Example: `RETURN m.title, m.poster, m.rating` or `RETURN movie {.*}`.
"""
    logging.info(f"Generating Cypher for query: {query}")
    try:
        # Use the passed model object directly
        response = model.generate_content(  # Call generate_content on the model
            contents=[system_instruction, "Here is the User query: " + query],
            generation_config={
                'temperature': 0.0,
                'top_p': 0.0,
            }
        )
        # Access text safely
        cypher_query = response.text.strip() if response.candidates and response.text else ""
        cypher_query = cypher_query.replace(
            '```cypher', '').replace('```', '').strip()

        if not cypher_query:
            logging.warning("LLM did not return a Cypher query.")
            return []  # Return empty context if no query generated

        logging.info(f"Generated Cypher Query: {cypher_query}")

        # Use the passed graph object
        context = graph.run(cypher_query).data()
        logging.info(f"Context retrieved: {context}")
        return context

    except Exception as e:
        logging.error(f"Error in context_generator: {e}", exc_info=True)
        # Depending on the error, you might want to return specific info
        # For now, return empty context on error
        return []


# Changed type hint
def respone_from_context(query: str, context: list, model: genai.GenerativeModel):
    """Generates a response using the query and context."""
    system_instruction = f"""You are a helpful movie chatbot. Use the provided CONTEXT to answer the user's USER QUERY accurately and concisely.
If the context contains movie information (like titles, ratings, posters), mention them naturally in your response.
If the context is empty or doesn't seem relevant to the query, state that you couldn't find specific information in the database but try to answer generally if possible.

CONTEXT:
{context}

USER QUERY: {query}

Answer:"""
    logging.info("Generating response from context...")
    try:
        # Use the passed model object directly
        response = model.generate_content(  # Call generate_content on the model
            # The prompt now includes context and query
            contents=[system_instruction],
            generation_config={
                'temperature': 0.0,
                'top_p': 0.3,
            }
        )
        response_text = response.text.strip(
        ) if response.candidates and response.text else "Sorry, I couldn't generate a response."
        logging.info(f"Generated Response: {response_text}")
        return response_text

    except Exception as e:
        logging.error(f"Error in respone_from_context: {e}", exc_info=True)
        return "Sorry, I encountered an error while generating the response."

# Remove the old global initializations and the __main__ block
# client = ClientHandler().get_client() # Remove
# graph = Graph(...) # Remove
# if __name__ == "__main__": # Remove or comment out
