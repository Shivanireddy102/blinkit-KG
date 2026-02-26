import os
from dotenv import load_dotenv

load_dotenv()

print("ENV VALUE:", os.getenv("GROQ_API_KEY"))