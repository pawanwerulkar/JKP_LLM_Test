# config.py

import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

# API configuration
# Open_BASE_URL = "http://13.233.245.126/"
OPEN_API_KEY = dotenv_values("OPEN_API_KEY")
INDEX_DIMENSION = 768
# Pinecone configuration
PINECONE_API_KEY = dotenv_values("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "basic-kn-index")
