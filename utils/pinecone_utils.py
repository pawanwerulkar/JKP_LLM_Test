import os
from operator import index

from openai import OpenAI
# from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec, Index
import config
from config import PINECONE_INDEX_NAME
from langchain_pinecone import PineconeVectorStore
# Initialize Pinecone with the provided API key
pc = Pinecone(api_key=config.PINECONE_API_KEY)

def get_embeddings():
    from langchain_huggingface.embeddings.huggingface import HuggingFaceEmbeddings
    model_name = "l3cube-pune/hindi-sentence-similarity-sbert"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": False}
    hfEmbeddings = HuggingFaceEmbeddings(
        model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
    )
    return hfEmbeddings


# Access the index using the Index class
# Specify the host for the index
index = pc.Index(PINECONE_INDEX_NAME)




def query_pinecone(embedding, top_k=5):
    """Query the Pinecone index with the given embedding."""
    # Query the index
    results = index.query(
        query_vector=embedding,  # Use query_vector for the embedding
        # top_k=top_k,
        top_k=100,
        include_metadata=True,
        vector=[0] * config.INDEX_DIMENSION



    )
    return results


client = OpenAI()
def convert_to_hindi(text):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Respond only with the hindi writing of the given text.",
                },
                {"role": "user", "content": f"{text}"},
            ],
        )
        return response.choices[0].message.content

def query_pinecone2(user_query):

    documents_db = PineconeVectorStore.from_existing_index(PINECONE_INDEX_NAME,get_embeddings())

    llm_output = convert_to_hindi(user_query)
    docs = documents_db.similarity_search(llm_output)


    return docs


# from pinecone.grpc import PineconeGRPC as Pinecone
def get_index_name():
    # pc = Pinecone(api_key="YOUR_API_KEY")
    index_name = pc.list_indexes()
    print(index_name)

get_index_name()