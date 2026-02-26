# ===========================================
# PINECONE VECTOR STORE SETUP
# ===========================================

from pinecone import Pinecone, ServerlessSpec
from backend.services.config import PINECONE_API_KEY, PINECONE_INDEX_NAME


class PineconeManager:

    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index_name = PINECONE_INDEX_NAME
        print("✅ Pinecone initialized")

    def create_index(self, index_name=None, dimension=384, reset=False):

        index_name = index_name or self.index_name

        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if index_name in existing_indexes:
            if reset:
                print(f"🔄 Deleting index: {index_name}")
                self.pc.delete_index(index_name)
            else:
                print(f"✅ Index '{index_name}' already exists")
                return self.pc.Index(index_name)

        print(f"📦 Creating index: {index_name}")

        self.pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print(f"✅ Index '{index_name}' created")

        return self.pc.Index(index_name)
