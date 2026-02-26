"""
Interactive product search
"""

import os
from dotenv import load_dotenv
from blinkit_rag import BlinkitRAG

load_dotenv()

print("=" * 70)
print("🔍 BLINKIT PRODUCT SEARCH")
print("=" * 70)

rag = BlinkitRAG(
    pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    groq_api_key=os.getenv("GROQ_API_KEY"),
    index_name="blinkit-index"
)

rag.load_existing_index()
rag.setup_qa_system(retrieval_k=5)

print("✅ System ready! Type your questions (or 'quit' to exit)\n")

while True:
    user_query = input("🛒 Your question: ").strip()

    if user_query.lower() in ["quit", "exit", "q"]:
        print("\n👋 Goodbye!")
        break

    if not user_query:
        continue

    try:
        result = rag.query(user_query, return_sources=True)

        print("\n🤖 Answer:")
        print(f"   {result['answer']}")

        print(f"\n📚 Based on {result['sources_count']} products:")

        if "sources" in result:
            for i, source in enumerate(result["sources"][:3], 1):
                print(
                    f"   {i}. {source.get('name')} "
                    f"- ₹{source.get('price')} "
                    f"({source.get('category')})"
                )

        print("\n" + "-" * 70 + "\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
 