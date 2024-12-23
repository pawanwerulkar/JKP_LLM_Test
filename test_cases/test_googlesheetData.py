import os
import time
from copyreg import pickle
from idlelib.iomenu import encoding
import pickle
import pytest
from sqlalchemy.sql.functions import current_date

import config
import pandas as pd
from pinecone import Pinecone
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
# from utils.fileRename_utils import rename_file_with_date
from utils.email_utils2 import send_email_with_report
from utils.generate_html_report import generate_html_report, excel_file, output_html_file
from utils.pinecone_utils import query_pinecone2
from utils.utils import generate_embedding, check_overlap, check_time_matching
from utils.report_utils import get_or_create_report, calculate_and_save_summary
from utils.Summery_utils3 import append_summary_to_new_workbook
from utils.report_utils import calculate_and_save_average_accuracy, calculate_accuracy
from utils.Summery_utils3 import get_llm_response


# Google Sheets API Setup
SERVICE_ACCOUNT_FILE = "Configgoogle.json"  # Path to your JSON file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = "1XM-cxoCw1bwofMiUw0NhtAa7GF44bI3vvgKIqZ_CrBw"  # Google Sheet ID from the URL
RANGE_NAME = "Sheet1"  # Adjust based on your sheet's range

# Authenticate with Google Sheets
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

def clean_value(value):
    """Clean up the value to ensure it's valid for Excel."""
    if pd.isna(value) or value is None:
        return "N/A"  # Replace empty or None with "N/A"
    if isinstance(value, (dict, list)):
        return str(value)  # Convert unsupported types to a string
    return value

def fetch_google_sheet_data():
    """Fetch data from Google Sheets."""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
        rows = result.get('values', [])
        if not rows:
            raise ValueError("No data found in the Google Sheet.")

        # Convert to a DataFrame for easy handling
        headers = rows[0]  # First row as headers
        data = rows[1:]  # Remaining rows as data
        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        raise RuntimeError(f"Error fetching Google Sheets data: {e}")


# Fetch test data from Google Sheet
try:
    test_data_df = fetch_google_sheet_data()
    # Drop rows with completely empty values
    test_data_df.dropna(how='all', inplace=True)
except Exception as e:
    raise ValueError(f"Error loading Google Sheets data: {e}")

# Validate that required columns are present
required_columns = {"question", "expected_snippet", "expected_start_time", "expected_end_time"}
if not required_columns.issubset(test_data_df.columns):
    raise ValueError(f"Google Sheet must contain these columns: {required_columns}")

# Convert the DataFrame to a list of dictionaries for parameterization
test_data = test_data_df.to_dict(orient="records")

# Path for the report
report_path = r"report/test_report.xlsx"
os.makedirs(os.path.dirname(report_path), exist_ok=True)  # Ensure directory exists
wb = get_or_create_report()
ws = wb["Test Results"]
ws_metrics = wb["Metrics"]

# Initialize Pinecone client
pc = Pinecone(api_key=config.PINECONE_API_KEY)

# Retrieve the list of index names dynamically
index_names = pc.list_indexes().names()
if not index_names:
    raise ValueError("No indexes found in Pinecone. Please ensure indexes are available.")
print("Indexes:", index_names)

@pytest.mark.parametrize("data", test_data)
@pytest.mark.parametrize("index_name", index_names)
def test_pinecone_search_response(data, index_name):
    print(f"Running test for question: {data['question']} on index: {index_name}")

    # Extracting test case details from the data
    question = data.get("question", "N/A")
    video_title = data.get("video_title","N/A")
    expected_snippet = data.get("expected_snippet", "N/A")
    expected_start_time = data.get("expected_start_time", "N/A")
    expected_end_time = data.get("expected_end_time", "N/A")
    question_type = data.get("question_type")
    llm_response = get_llm_response(question,expected_snippet)

    print(question,video_title,expected_snippet)


    # Create a report row template
    report_row = {
        "Category": question_type,
        "Question": question,
        "Index": index_name,
        "Response Video Title": "",
        "Response Text": "",
        "Response Video": "",
        "Response Snippet Start": "",
        "Response Snippet End": "",
        "Ground Truth Video Title": video_title,
        "Ground Truth Text": expected_snippet,
        "Ground Truth Video": "N/A",
        "Ground Truth Snippet Start": expected_start_time,
        "Ground Truth Snippet End": expected_end_time,
        "Similarity Score": "",
        "LLM Response": llm_response,
        "Result": "",
        "Detail Response": ""

    }

    # Initialize flags
    snippets_overlap = True
    time_match = True
    should_fail = False  # Flag to track failure conditions

    # Query Pinecone (pass the current index_name)
    try:
        response = query_pinecone2(question, index_name)
        print(response)

        # Handle the 'query_pinecone2' responses
        if isinstance(response, list):
            top_results = response
        else:
            top_results = response.get("matches", [])

        report_row["Detail Response"] = str(top_results)

        if not top_results:
            print(f"No matches found for index: {index_name}.")
            report_row["Result"] = "Fail: No matches found"
            should_fail = True  # Set the flag to fail the test
            ws.append([clean_value(val) for val in report_row.values()])
            wb.save(report_path)  # Save report even if no matches found
            return

        # Process the top results
        # for result in top_results:
        #     actual_snippet = result.page_content
        #     actual_start_time = result.document.metadata.get("start", "")
        #     actual_end_time = result.metadata.get("end", "")
        #     video_name = result.document.metadata.get("name", "")
        #     print(f"Processing result for video: {video_name} on index: {index_name}")

        for idx, result in enumerate(top_results, 1):
            # Access document and score from each result
            doc = result[0]  # result[0] is the document
            score = result[1]  # result[1] is the similarity score

            # Extract metadata from the document
            actual_snippet = doc.page_content  # The snippet/text content
            actual_start_time = doc.metadata.get("start", "")  # Get start time, default to empty if not found
            actual_end_time = doc.metadata.get("end", "")  # Get end time, default to empty if not found
            video_name = doc.metadata.get("name", "")  # Get the name of the video
            media_source = doc.metadata.get("media_source", "")

            # Fill actual response data
            report_row["Response Video Title"] = video_name
            report_row["Response Text"] = actual_snippet
            report_row["Response Video"] = doc.metadata.get("media_source", "")
            report_row["Response Snippet Start"] = actual_start_time
            report_row["Response Snippet End"] = actual_end_time
            report_row["Similarity Score"] = score
            print(score)

        #     # Check snippet overlap result
        #     if not check_overlap(expected_snippet, actual_snippet):
        #         snippets_overlap = False
        #         print(f"Snippet overlap failed for video: {video_name} on index: {index_name}")
        #         should_fail = True
        #
        #     # Check start and end time match result
        #     if not check_time_matching(expected_start_time, actual_start_time, expected_end_time, actual_end_time):
        #         time_match = False
        #         print(f"Time mismatch for video: {video_name} on index: {index_name}")
        #         should_fail = True
        #
        # # Test case result based on overlap and time match
        # if snippets_overlap and time_match:
        #     report_row["Result"] = "Pass"
        #     accuracy = calculate_accuracy(expected_snippet, actual_snippet)
        # else:
        #     report_row["Result"] = "Fail"
        #     accuracy = 0
        #
        # print(f"Accuracy: {accuracy}%")
        #
        # # Add accuracy to the metrics sheet
        # ws_metrics.append([index_name, "similarity-search", accuracy])

        #check similarity score
        if  int(llm_response)>=  7:
            report_row["Result"] = "Pass"

        else:
            report_row["Result"] = "Fail"
            should_fail = True



        # Append the report row to the Test Results worksheet and save
        ws.append([clean_value(val) for val in report_row.values()])
        wb.save(report_path)

    except Exception as e:
        print(f"Error querying Pinecone for index {index_name}: {e}")
        report_row["Result"] = f"Error: {e}"
        ws.append([clean_value(val) for val in report_row.values()])
        wb.save(report_path)
        should_fail = True  # If exception occurs, force failure

    # Assert at the end of the test to fail if conditions were met
    assert not should_fail, "Test failed due to response grade <= 7."

def  test_2():
    calculate_and_save_average_accuracy()
    calculate_and_save_summary()
    # generate_html_report(excel_file=excel_file, output_html_file=output_html_file)



# Pytest fixture to run after all tests
# @pytest.fixture(scope="session", autouse=True)
def test_after_all_tests():
    # """This fixture runs after all tests are executed to calculate and save average accuracy."""
    # yield  # Wait for all tests to finish
    try:

        input_file_path = r"C:\Users\test_complete\PycharmProjects\KN_LLM\report\test_report.xlsx"
        output_file_path = r"C:\Users\test_complete\PycharmProjects\KN_LLM\report\final_report.xlsx"

        #function that will create final report
        append_summary_to_new_workbook(input_file_path, output_file_path)
        calculate_and_save_average_accuracy()
        calculate_and_save_summary()
        # generate_html_report(excel_file=excel_file, output_html_file=output_html_file)
    except Exception as e:
        print(f"Error in post-test processing: {e}")







