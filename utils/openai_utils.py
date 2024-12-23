import openai

def get_llm_response(question, response_text):
    """
    Get the LLM response (grading) based on the provided question and response text.
    """
    prompt = f"Grade the following response from 0-10 based on the question here and respond with a number between 0.0 and 10.0: {question}   response     {response_text}"

    try:
        # Send the prompt to OpenAI API and get the response
        response = openai.Completion.create(
            engine="text-davinci-003",  # Or the engine of your choice
            prompt=prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7
        )

        # Extract the LLM grade (response)
        llm_grade = response.choices[0].text.strip()
        return float(llm_grade) if llm_grade.replace('.', '', 1).isdigit() else None  # Return as float if valid

    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return None
