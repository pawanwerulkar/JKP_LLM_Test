import os
from operator import index
import pinecone
import openai
from openai import OpenAI
# from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec, Index
# from pygame.examples.audiocapture import names
# from dotenv import load_dotenv
import config
# from config import PINECONE_INDEX_NAME
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
index = pc.Index(config.PINECONE_INDEX_NAME)

indexes = pc.list_indexes()
print(f"Indexes: {indexes}")


def query_pinecone(embedding, top_k=5):
    """Query the Pinecone index with the given embedding."""
    # Query the index
    results = index.query(
        query_vector=embedding,  # Use query_vector for the embedding
        # top_k=top_k,
        top_k=5,
        include_metadata=True,
        vector=[0] * config.INDEX_DIMENSION

    )
    return results


client = OpenAI()


def convert_to_hindi(text):
    """translate english search query string to hindi string"""

    prompt = "Translate the text in brackets to Hindi in Hindi script and respond only with the translation"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": "{" + f"{text}" + "}"},
        ],
    )
    return response.choices[0].message.content

def query_pinecone2(user_query,index_name):

    documents_db = PineconeVectorStore.from_existing_index(config.PINECONE_INDEX_NAME,get_embeddings())

    llm_output = convert_to_hindi(user_query)
    # docs = documents_db.similarity_search(llm_output)
    docs =documents_db.similarity_search_with_score(llm_output,k=5)


    return docs
    # document_db = index.query(vector=user_query,top_k=5,include_metadata=True)
    # llm_output = convert_to_hindi(user_query)
    # docs = document_db.similarity_search(llm_output)
    # return docs


def query_pinecone3(question, index_name):
    # Query Pinecone using the provided index_name
    # index_name = pc.list_indexes().names()
    index = pinecone.Index(index_name)
    print(f"Indesxes : {index}")
    response = index.query([question], top_k=5)  # Adjust the query as needed
    return response

#test purpose only dynamic index test 2
# from pinecone import PineconeClient

# import os
#
# # Initialize Pinecone client
# # pc = PineconeClient(api_key=config.PINECONE_API_KEY)
#
# def query_pinecone(embedding, index_name, top_k=5):
#     """Query the Pinecone index with the given embedding."""
#     index = pc.Index(index_name)  # Dynamically choose the index
#     results = index.query(
#         query_vector=embedding,
#         top_k=top_k,
#         include_metadata=True,
#         vector=[0] * config.INDEX_DIMENSION  # Example, adjust as needed
#     )
#     return results

# openai.api_key = config.OPENAI_API_KEY
# import openai  # Assuming you're using OpenAI API


# Function to query LLM and get the score
# def get_llm_response(question, response_text):
#     try:
#         # Construct your prompt
#         prompt = f"Grade the following response from 0-10 based on the question here and respond with a number between 0.0 and 10.0: {question} {response_text}"
#
#         # Call the new OpenAI API method
#         response = openai.chat.Completion.create(
#             model="gpt-3.5-turbo",  # Or use "gpt-4" if you have access
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": prompt}
#             ]
#         )
#
#         # Extract the LLM response
#         llm_response = response['choices'][0]['message']['content']
#         return llm_response
#     except Exception as e:
#         print(f"Error getting LLM response: {e}")
#         return None



