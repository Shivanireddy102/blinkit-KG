# knowledge_graph/neo4j/connection.py
from neo4j import GraphDatabase

# Neo4j connection details
URI = "bolt://localhost:7687"   # your instance is blinkit, but connection URI stays the same
USER = "neo4j"
PASSWORD = "shivanireddy"      # put your Neo4j password here
DATABASE = "neo4j"              # use the default database

# Create driver
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# Function to get a session for the default database
def get_session():
    return driver.session(database=DATABASE)
