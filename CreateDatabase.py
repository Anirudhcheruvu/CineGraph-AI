import pandas as pd
import logging
from py2neo import Graph, Node, Relationship

# Configure logging to display info-level messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to and clear the database
graph = Graph("bolt://localhost:7687", auth=("neo4j", "GraphRAG"), name="graphrag")
graph.run("MATCH (n) DETACH DELETE n")
logging.info("Cleared the database.")

# Load CSV data
df = pd.read_csv("imdb_top_1000.csv")
logging.info("CSV file loaded successfully.")

for index, row in df.iterrows():
    # Create or merge Movie node using title as unique identifier
    movie = Node("Movie",
                 title=row["Series_Title"],
                 overview=row["Overview"],
                 poster=row["Poster_Link"],
                 gross=row["Gross"],
                 rating=row["IMDB_Rating"])
    graph.merge(movie, "Movie", "title")
    logging.info(f"Processed Movie node: {row['Series_Title']}")

    # Create or merge Director node and relationship to Movie
    director_name = row["Director"].strip().lower()
    director = Node("Person", name=director_name)
    graph.merge(director, "Person", "name")
    logging.info(f"Processed Director node: {director_name}")

    rel_directed = Relationship(director, "DIRECTED", movie)
    graph.create(rel_directed)
    logging.info(f"Created DIRECTED relationship: {director_name} -> {row['Series_Title']}")

    # Create or merge Star nodes and relationships to Movie
    stars = []
    for star_col in ["Star1", "Star2", "Star3", "Star4"]:
        star_name = row[star_col]
        if pd.notna(star_name):
            star_name = star_name.strip().lower()
            star = Node("Person", name=star_name)
            graph.merge(star, "Person", "name")
            stars.append(star)
            logging.info(f"Processed Star node: {star_name}")
            rel_star_movie = Relationship(star, "STARS_IN", movie)
            graph.create(rel_star_movie)
            logging.info(f"Created STARS_IN relationship: {star_name} -> {row['Series_Title']}")

    # Process and create Genre nodes and their relationships
    genres = [g.strip().lower() for g in row["Genre"].split(",")]
    for genre_name in genres:
        # Merge Genre node based on the name property
        genre = Node("Genre", name=genre_name)
        graph.merge(genre, "Genre", "name")
        logging.info(f"Processed Genre node: {genre_name}")
        
        # Create relationship between movie and genre
        rel_movie_genre = Relationship(movie, "OF_GENRE", genre)
        graph.create(rel_movie_genre)
        logging.info(f"Created OF_GENRE relationship: {row['Series_Title']} -> {genre_name}")
        
        # Create relationship between director and genre
        rel_director_genre = Relationship(director, "ASSOCIATED_WITH", genre)
        graph.create(rel_director_genre)
        logging.info(f"Created ASSOCIATED_WITH relationship: {director_name} -> {genre_name}")
        # Create relationships between each star and genre
        for star in stars:
            rel_star_genre = Relationship(star, "ASSOCIATED_WITH", genre)
            graph.create(rel_star_genre)
            logging.info(f"Created ASSOCIATED_WITH relationship: {star['name']} -> {genre_name}")
