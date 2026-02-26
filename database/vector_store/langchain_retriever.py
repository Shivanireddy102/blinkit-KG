from sentence_transformers import SentenceTransformer
from backend.services.config import (
    PINECONE_API_KEY,
    PINECONE_ENV,
    PINECONE_INDEX_NAME,
    EMBEDDING_DIMENSION,
)
from langchain_core.documents import Document


class SemanticRetriever:
    def __init__(self, index, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.index = index
        self.index_name = PINECONE_INDEX_NAME
        print("✅ Embeddings loaded")
        print(f"✅ Retriever initialized with index: {self.index_name}")

    def convert_products_to_documents(self, products):
        documents = []

        for idx, item in enumerate(products):
            if not isinstance(item, dict):
                continue

            product_name = str(item.get("product_name", "")).strip()
            category = str(item.get("category", "")).strip()
            brand = str(item.get("brand", "")).strip()
            price = str(item.get("price", "")).strip()
            mrp = str(item.get("mrp", "")).strip()
            discount = str(item.get("discount", "")).strip()
            rating = str(item.get("rating", "")).strip()
            quantity = str(item.get("quantity", "")).strip()

            if not product_name:
                continue

            content = (
                f"Product: {product_name}. "
                f"Brand: {brand}. "
                f"Category: {category}. "
                f"Price: ₹{price}. "
                f"MRP: ₹{mrp}. "
                f"Discount: {discount}%. "
                f"Rating: {rating}. "
                f"Stock: {quantity}"
            )

            doc = Document(
                page_content=content,
                metadata={
                    "id": str(item.get("product_id", idx)),
                    "text": content,
                    "brand": brand,
                    "category": category,
                    "price": price,
                },
            )

            documents.append(doc)

        print(f"✅ Created {len(documents)} documents")
        return documents

    def embed_text(self, text: str):
        embedding = self.model.encode(text)
        return embedding.tolist()

    def store_documents(self, documents):
        vectors = []

        for doc in documents:
            embedding = self.embed_text(doc.page_content)
            vectors.append(
                (
                    doc.metadata["id"],
                    embedding,
                    {"text": doc.page_content},
                )
            )

        self.index.upsert(vectors=vectors)
        print(f"✅ Upserted {len(vectors)} vectors")

    def similarity_search(self, query, top_k=5):
        query_embedding = self.embed_text(query)
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )
        return results