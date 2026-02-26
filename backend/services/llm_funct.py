import json
from langchain_groq import ChatGroq
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.schema import Document

# ========================
# CONFIG
# ========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")



INPUT_FILE = "data.json"   # your JSON file

# ========================
# LOAD DATA
# ========================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

documents = [
    Document(page_content=json.dumps(record))
    for record in data
]

# ========================
# GROQ LLM (SUPPORTED MODEL)
# ========================
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="gemma2-9b-it",  # ✅ works
    temperature=0
)

# ========================
# GRAPH TRANSFORMER
# ========================
graph_transformer = LLMGraphTransformer(llm=llm)

graph_documents = graph_transformer.convert_to_graph_documents(documents)

# ========================
# NEO4J CONNECTION
# ========================
graph = Neo4jGraph(
    url=NEO4J_URL,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

# ========================
# AUTO CYPHER EXECUTION
# ========================
graph.add_graph_documents(
    graph_documents,
    baseEntityLabel=True,
    include_source=True
)

print("✅ Knowledge Graph created in Neo4j")
