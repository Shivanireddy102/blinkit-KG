import os

from backend.services.config import (
    PINECONE_API_KEY,
    PINECONE_ENV,
    PINECONE_INDEX_NAME,
    EMBEDDING_DIMENSION,
    GROQ_API_KEY,
)

from database.vector_store.pinecone_setup import PineconeManager
from database.vector_store.langchain_retriever import SemanticRetriever
from backend.pipeline.data_loader import DataLoader


os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

print("✅ Environment variables set")
print(f"   Pinecone Environment: {PINECONE_ENV}")
print(f"   Index Name: {PINECONE_INDEX_NAME}")


def main():
    print("\n BLINKIT SEARCH PIPELINE")

    # STEP 1: Load Data
    try:
        loader = DataLoader()
        products = loader.load_all_data()

        if not products:
            print(" No products loaded!")
            return

        print(f"✅ Loaded {len(products)} products")

    except Exception as e:
        print(f" Error loading data: {e}")
        return

    # STEP 2: Initialize Pinecone
    try:
        pinecone_manager = PineconeManager()
        index = pinecone_manager.create_index(
            index_name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            reset=False,
        )
        print(f"✅ Pinecone index '{PINECONE_INDEX_NAME}' ready")

    except Exception as e:
        print(f" Pinecone init error: {e}")
        return

    # STEP 3: Initialize Retriever
    try:
        retriever = SemanticRetriever(index=index)
        print("✅ Retriever initialized")

    except Exception as e:
        print(f" Retriever init error: {e}")
        return

    # STEP 4: Convert & Store
    try:
        docs = retriever.convert_products_to_documents(products)

        if docs:
            retriever.store_documents(docs)
            print(f"✅ Stored {len(docs)} documents in Pinecone")
        else:
            print("⚠️ No documents created")

    except Exception as e:
        print(f"Error storing documents: {e}")
        return

    # STEP 5: Semantic Search (Interactive)
try:
    while True:
        query = input("\n🔎 Enter product search (or type 'exit'): ")

        if query.lower() == "exit":
            break

        results = retriever.similarity_search(query, top_k=5)
        matches = results.get("matches", [])

        print(f"\n🔍 Top Results for '{query}':\n")

        if not matches:
            print("❌ No results found.\n")
        else:
            for i, match in enumerate(matches, 1):
                md = match.get("metadata", {})
                score = match.get("score", 0)

                print(f"{i}. {md.get('text', '')}")
                print(f"   🔹 Similarity Score: {round(score, 4)}\n")

except Exception as e:
    print(f" Search error: {e}")