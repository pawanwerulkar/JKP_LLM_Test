# config.py

import os
from dotenv import load_dotenv

load_dotenv()

# API configuration
# Open_BASE_URL = "http://13.233.245.126/"
OPEN_API_KEY = "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"
INDEX_DIMENSION = 768
# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "1606b7c2-95de-4c1c-a6d5-49e648b43441")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "basic-kn-index")
