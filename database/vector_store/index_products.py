"""
Index products into Pinecone
"""

import os
from dotenv import load_dotenv
from blinkit_rag import BlinkitRAG
from data_loader import DataLoader
from langchain_core.documents import Document

load_dotenv()

print("=" * 60)
print("📦 INDEXING PRODUCTS")
print("=" * 60)

pinecone_api_key = os.getenv("PINECONE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

rag = BlinkitRAG(
    pinecone_api_key=pinecone_api_key,
    groq_api_key=groq_api_key,
    index_name="blinkit-index"
)

# ✅ Detect embedding dimension
embedding_dim = rag.get_embedding_dimension()
print(f"🔍 Embedding dimension: {embedding_dim}")

# ✅ FORCE reset to avoid mismatch error
rag.create_index(dimension=embedding_dim, reset=True)

# Load data
loader = DataLoader()
products = loader.load_all_data()
print(f"✅ Loaded {len(products)} products")

documents = []

for item in products:
    name = str(item.get("name", "")).strip()
    if not name:
        continue

    try:
        price = float(item.get("price", 0))
    except:
        price = 0.0

    doc = Document(
        page_content=f"{name} {item.get('description','')}",
        metadata={
            "name": name,
            "price": price,
            "category": item.get("category", ""),
        },
    )

    documents.append(doc)

print(f"📄 Created {len(documents)} documents")

rag.index_documents(documents)
rag.setup_qa_system()

print("📊 Stats:", rag.get_stats())
print("✅ INDEXING COMPLETE")
