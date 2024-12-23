# config.py

import os
from dotenv import load_dotenv

load_dotenv()

# API configuration
# Open_BASE_URL = "http://13.233.245.126/"

OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
# Pinecone configuration

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")