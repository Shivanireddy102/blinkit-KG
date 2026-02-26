import os
import json
from dotenv import load_dotenv
from groq import Groq

# Absolute path to your .env file
ENV_PATH = r"C:\Users\gcboo\OneDrive\Desktop\Neo4jImport\llm_graph_transformer\.env"
load_dotenv(dotenv_path=ENV_PATH)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("❌ GROQ_API_KEY not found in .env")


def extract_entities_relationships(text):
    prompt = f"""
    Extract entities and relationships from the text below.
    Return ONLY valid JSON in this format:

    {{
      "entities": [
        {{"id": "EntityName", "label": "EntityType"}}
      ],
      "relationships": [
        {{"from": "EntityName", "type": "RELATION", "to": "EntityName"}}
      ]
    }}

    Text:
    "{text}"
    """

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
