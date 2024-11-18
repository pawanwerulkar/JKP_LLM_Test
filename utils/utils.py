# utils/utils.py

import openai
import config

# OpenAI API configuration
openai.api_key = config.OPEN_API_KEY

def generate_embedding(text):
    """
    Generates an embedding for the given text using OpenAI's API.
    """
    try:
        response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        return response["data"][0]["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def check_overlap(expected_snippet, actual_snippet):
    """
    Check if the expected snippet is present in the actual snippet.
    """
    if not isinstance(expected_snippet, str) or not isinstance(actual_snippet, str):
        print("Both expected_snippet and actual_snippet must be strings.")
        return False
    return expected_snippet.lower() in actual_snippet.lower()


def check_time_matching(expected_start_time, actual_start_time, expected_end_time, actual_end_time):
    """
    Check if the expected start time and end time match the actual times.

    :param expected_start_time: The expected start time as a string.
    :param actual_start_time: The actual start time as a string.
    :param expected_end_time: The expected end time as a string.
    :param actual_end_time: The actual end time as a string.
    :return: True if both start and end times match, otherwise False.
    """
    if not isinstance(expected_start_time, str) or not isinstance(actual_start_time, str):
        print("Both expected_start_time and actual_start_time must be strings.")
        return False

    if not isinstance(expected_end_time, str) or not isinstance(actual_end_time, str):
        print("Both expected_end_time and actual_end_time must be strings.")
        return False

    start_time_match = expected_start_time.lower() == actual_start_time.lower()
    end_time_match = expected_end_time.lower() == actual_end_time.lower()

    return start_time_match and end_time_match
