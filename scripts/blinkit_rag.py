"""
Blinkit RAG System - Fully Corrected Stable Version
"""

import time
from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from pinecone import Pinecone, ServerlessSpec


class BlinkitRAG:

    def __init__(
        self,
        pinecone_api_key: str,
        groq_api_key: str,
        index_name: str = "blinkit-index",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "llama-3.3-70b-versatile",
        pinecone_cloud: str = "aws",
        pinecone_region: str = "us-east-1"
    ):

        print("🚀 Initializing Blinkit RAG System...")

        self.index_name = index_name
        self.pinecone_cloud = pinecone_cloud
        self.pinecone_region = pinecone_region

        # Pinecone
        self.pc = Pinecone(api_key=pinecone_api_key)

        # Embeddings (384 dimension)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # LLM
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model=llm_model,
            temperature=0.3,
        )

        self.vectorstore = None
        self.retrieval_k = 3

        print("✅ RAG System initialized!")

    # Detect embedding dimension safely
    def get_embedding_dimension(self) -> int:
        test_embedding = self.embeddings.embed_query("test")
        return len(test_embedding)

    # Create Pinecone index
    def create_index(self, dimension: int, reset: bool = True):
        print(f"📊 Setting up index: {self.index_name}")

        if self.pc.has_index(self.index_name):
            if reset:
                print("   🔄 Deleting old index...")
                self.pc.delete_index(self.index_name)
                time.sleep(5)
            else:
                print("   ✅ Index already exists")
                return

        print(f"   🆕 Creating new index (dimension={dimension})...")
        self.pc.create_index(
            name=self.index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=self.pinecone_cloud,
                region=self.pinecone_region,
            ),
        )

        # Wait until ready
        while not self.pc.describe_index(self.index_name).status["ready"]:
            time.sleep(2)

        print("   ✅ Index ready!")

    # Load existing index
    def load_existing_index(self):
        print("📂 Loading existing index...")

        self.vectorstore = PineconeVectorStore.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
        )

        print("✅ Index loaded successfully!")

    # Index documents
    def index_documents(self, documents: List[Document]):
        print(f"💾 Indexing {len(documents)} documents...")

        self.vectorstore = PineconeVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
            index_name=self.index_name,
        )

        print("✅ Documents indexed!")

    def setup_qa_system(self, retrieval_k: int = 5):
        self.retrieval_k = retrieval_k
        print(f"✅ QA ready (top {retrieval_k} retrieval)")

    # ✅ FULLY FIXED QUERY METHOD
    def query(self, question: str, return_sources: bool = False) -> Dict:

        if not self.vectorstore:
            raise ValueError("Vectorstore not loaded. Call load_existing_index() first.")

        docs = self.vectorstore.similarity_search(
            question, k=self.retrieval_k
        )

        context = "\n\n".join([
            f"Product: {doc.metadata.get('name')}\n"
            f"Price: ₹{doc.metadata.get('price')}\n"
            f"Category: {doc.metadata.get('category')}"
            for doc in docs
        ])

        prompt = f"""
You are a helpful Blinkit grocery assistant.

Products:
{context}

User Question: {question}

Give short, clear answer mentioning product names and prices.
"""

        response = self.llm.invoke(prompt)

        result = {
            "answer": response.content,
            "sources_count": len(docs),
        }

        if return_sources:
            result["sources"] = [doc.metadata for doc in docs]

        return result

    def get_stats(self):
        index = self.pc.Index(self.index_name)
        stats = index.describe_index_stats()
        return {
            "index_name": self.index_name,
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", 384),
        }
