import streamlit as st
import os
import logging
from dotenv import load_dotenv

# Import functions and classes from your Querying script
from Querying import ClientHandler, get_neo4j_graph, context_generator, respone_from_context

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Environment Variables ---
load_dotenv()
st.set_page_config(page_title="Movie Chatbot", layout="wide")

# --- Helper function to extract posters ---
# (Needs careful adjustment based on how your Cypher queries return data)


def extract_posters_from_context(context_data: list):
    """Extracts poster URLs from the context data list."""
    poster_urls = []
    if not isinstance(context_data, list):
        return poster_urls

    for record in context_data:
        poster_url = None
        if isinstance(record, dict):
            # Check common patterns (adjust keys based on your generated Cypher)
            # Direct property:
            poster_url = record.get('poster')
            # Property of a returned node 'm' or 'movie':
            if not poster_url:
                movie_node = record.get('m') or record.get('movie')
                if isinstance(movie_node, dict):  # If node properties are returned as dict
                    poster_url = movie_node.get('poster')
            # Property prefixed like 'm.poster':
            if not poster_url:
                poster_url = record.get(
                    'm.poster') or record.get('movie.poster')

        if poster_url and isinstance(poster_url, str) and poster_url not in poster_urls:
            # Basic check for valid URL structure (optional)
            if poster_url.startswith("http://") or poster_url.startswith("https://"):
                poster_urls.append(poster_url)
                logging.info(f"Extracted poster: {poster_url}")

    if not poster_urls:
        logging.info("No poster URLs extracted from context.")
    return poster_urls

# --- Resource Initialization using Streamlit Caching ---


@st.cache_resource
def initialize_resources():
    """Initializes and returns the Gemini model and Neo4j graph connection."""  # Docstring updated
    logging.info("Attempting to initialize resources...")
    try:
        # client = ClientHandler().get_client() # Old way
        model = ClientHandler().get_model()  # Get the model instance
        graph = get_neo4j_graph()
        logging.info("Resources initialized successfully.")
        # return client, graph # Old way
        return model, graph  # Return model instead of client
    # ... rest of the function ...
    except Exception as e:
        logging.error(f"Failed to initialize resources: {e}", exc_info=True)
        st.error(
            f"Fatal Error: Could not initialize backend services. Please check logs. Error: {e}")
        return None, None  # Indicate failure


# --- Initialize Client and Graph ---
# gemini_client, neo4j_graph = initialize_resources() # Old variable name
gemini_model, neo4j_graph = initialize_resources()  # Use new variable name

# --- Streamlit App UI ---
st.title("🎬 Movie Chatbot (Manual Flow)")
st.caption("Ask me about movies, actors, directors, or genres!")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    logging.info("Initialized messages in session state.")

# Display prior chat messages
for message in st.session_state.messages:
    role = message["role"]
    with st.chat_message(role):
        st.markdown(message["content"])
        if role == "assistant" and "posters" in message and message["posters"]:
            st.image(message["posters"], width=100)  # Display posters

# Get user input
prompt = st.chat_input("Your message")  # Assign the result first
if prompt:                             # Then check if it has a value <--- START OF THE BLOCK
    # Check if resources are available
    if not gemini_model or not neo4j_graph:  # <-- Make sure this uses gemini_model too!
        st.error(
            "Chatbot is not available due to initialization error. Please check logs.")
    else:
        # ... (code to add user message to history and display it) ...

        # 2. Display assistant response placeholder
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            posters_placeholder = st.empty()

            # --- THIS IS THE try BLOCK WHERE YOU MAKE THE CHANGE ---
            try:
                # 3. Generate Context
                logging.info("Calling context_generator...")
                # --- REPLACE THIS LINE ---
                # context_data = context_generator(prompt, gemini_client, neo4j_graph) # OLD LINE
                # --- WITH THIS LINE ---
                context_data = context_generator(
                    prompt, gemini_model, neo4j_graph)  # NEW LINE

                # 4. Generate Response from Context
                logging.info("Calling respone_from_context...")
                # --- REPLACE THIS LINE ---
                # bot_response_text = respone_from_context(prompt, context_data, gemini_client) # OLD LINE
                # --- WITH THIS LINE ---
                bot_response_text = respone_from_context(
                    prompt, context_data, gemini_model)  # NEW LINE

                # 5. Extract poster URLs from the raw context
                poster_urls = extract_posters_from_context(context_data)

                # 6. Update placeholders with actual response and posters
                message_placeholder.markdown(bot_response_text)
                if poster_urls:
                    posters_placeholder.image(poster_urls, width=150)

                # 7. Add assistant response (with posters) to chat history
                # ... (rest of the try block) ...

            except Exception as e:
                # --- CORRECTLY INDENTED LINES ---
                logging.error(
                    f"Error during chat processing: {e}", exc_info=True)
                error_message = f"Sorry, an error occurred processing your request: {e}"
                message_placeholder.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message,
                    "posters": []
                })
