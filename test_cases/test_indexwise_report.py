


import os
import time
import pytest
import config
import pandas as pd
from pinecone import Pinecone
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from utils.fileRename_utils import rename_file_with_date
from utils.email_utils2 import send_email_with_report
from utils.generate_html_report import generate_html_report, excel_file, output_html_file
from utils.pinecone_utils import query_pinecone2
from utils.utils import generate_embedding, check_overlap, check_time_matching
from utils.report_utils import get_or_create_report, calculate_and_save_summary
from utils.report_utils import calculate_and_save_average_accuracy, calculate_accuracy

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

# Initialize the workbook and add the necessary sheets
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
# Prepare data structures for the summary and individual reports
overall_summary = {}
category_summary = {}
question_summary = {}
deep_dive_summary = {}
@pytest.mark.parametrize("data", test_data)
@pytest.mark.parametrize("index_name", index_names)
def test_pinecone_search_response(data, index_name):
    print(f"Running test for question: {data['question']} on index: {index_name}")

    # Extracting test case details from the data
    question = data.get("question", "N/A")
    video_title = data.get("video_title", "N/A")
    expected_snippet = data.get("expected_snippet", "N/A")
    expected_start_time = data.get("expected_start_time", "N/A")
    expected_end_time = data.get("expected_end_time", "N/A")

    print(question, video_title, expected_snippet)

    # Create a report row template
    report_row = {
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
        "Result": ""
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

        if not top_results:
            print(f"No matches found for index: {index_name}.")
            report_row["Result"] = "Fail: No matches found"
            should_fail = True  # Set the flag to fail the test
            ws.append([clean_value(val) for val in report_row.values()])
            wb.save(report_path)  # Save report even if no matches found
            return

        # Process the top results
        for result in top_results:
            actual_snippet = result.page_content
            actual_start_time = result.metadata.get("start", "")
            actual_end_time = result.metadata.get("end", "")
            video_name = result.metadata.get("name", "")
            print(f"Processing result for video: {video_name} on index: {index_name}")

            # Fill actual response data
            report_row["Response Video Title"] = video_name
            report_row["Response Text"] = actual_snippet
            report_row["Response Video"] = result.metadata.get("media_source", "")
            report_row["Response Snippet Start"] = actual_start_time
            report_row["Response Snippet End"] = actual_end_time

            # Check snippet overlap result
            if not check_overlap(expected_snippet, actual_snippet):
                snippets_overlap = False
                print(f"Snippet overlap failed for video: {video_name} on index: {index_name}")
                should_fail = True

            # Check start and end time match result
            if not check_time_matching(expected_start_time, actual_start_time, expected_end_time, actual_end_time):
                time_match = False
                print(f"Time mismatch for video: {video_name} on index: {index_name}")
                should_fail = True

        # Test case result based on overlap and time match
        if snippets_overlap and time_match:
            report_row["Result"] = "Pass"
            accuracy = calculate_accuracy(expected_snippet, actual_snippet)
        else:
            report_row["Result"] = "Fail"
            accuracy = 0

        print(f"Accuracy: {accuracy}%")

        # Add accuracy to the metrics sheet
        ws_metrics.append([index_name, "similarity-search", accuracy])

        # Append the report row to the Test Results worksheet and save
        ws.append([clean_value(val) for val in report_row.values()])
        wb.save(report_path)

        # Collect data for the summary tables
        if index_name not in overall_summary:
            overall_summary[index_name] = {"total_tests": 0, "pass_count": 0, "pass_rate": 0}
        overall_summary[index_name]["total_tests"] += 1
        if report_row["Result"] == "Pass":
            overall_summary[index_name]["pass_count"] += 1

        # Category summary (e.g., "Snippet Overlap", "Time Matching")
        category = "Overall"
        if category not in category_summary:
            category_summary[category] = {"pass_rate": 0, "total_tests": 0, "pass_count": 0}
        category_summary[category]["total_tests"] += 1
        if report_row["Result"] == "Pass":
            category_summary[category]["pass_count"] += 1

        # Question-specific summary
        if question not in question_summary:
            question_summary[question] = {
                "result": report_row["Result"],
                "video_matching": snippets_overlap,
                "snippet_overlap": snippets_overlap,
                "llm_response_score": accuracy
            }

        # Deep-dive details
        deep_dive_entry = {
            "Question Category": category,
            "Question": question,
            "Result": report_row["Result"],
            "Video Matching": "Pass" if snippets_overlap else "Fail",
            "Snippet Time Overlap": "Pass" if time_match else "Fail",
            "Ground Truth Similarity Score": accuracy,
            "Ground Truth Video Title": video_title,
            "Ground Truth Snippet Start": expected_start_time,
            "Ground Truth Snippet End": expected_end_time,
            "Ground Truth Text": expected_snippet,
            "Top Similarity Score for 5 Responses": "",  # Placeholder for later processing
            "Top 5 Response Video Title": ""  # Placeholder for later processing
        }
        if index_name not in deep_dive_summary:
            deep_dive_summary[index_name] = []
        deep_dive_summary[index_name].append(deep_dive_entry)

    except Exception as e:
        print(f"Error querying Pinecone for index {index_name}: {e}")
        report_row["Result"] = f"Error: {e}"
        ws.append([clean_value(val) for val in report_row.values()])
        wb.save(report_path)
        should_fail = True  # If exception occurs, force failure

    # Assert at the end of the test to fail if conditions were met
    assert not should_fail, "Test failed due to snippet overlap or time mismatch."

# Pytest fixture to run after all tests
@pytest.fixture(scope="session", autouse=True)
def after_all_tests():
    """This fixture runs after all tests are executed to calculate and save average accuracy."""
    yield  # Wait for all tests to finish

    # Create a new sheet for each index with its summary data
    for index_name in index_names:
        if index_name in overall_summary:
            total_tests = overall_summary[index_name]["total_tests"]
            pass_count = overall_summary[index_name]["pass_count"]
            pass_rate = (pass_count / total_tests) * 100 if total_tests > 0 else 0

            # Create a new sheet for each index
            if index_name not in wb.sheetnames:
                wb.create_sheet(title=index_name)

            ws_index = wb[index_name]
            ws_index.append(["Index Name", index_name])
            ws_index.append(["Overall Average Pass Rate", f"{pass_rate:.2f}%"])
            ws_index.append(["Total Tests", total_tests])
            ws_index.append(["Pass Count", pass_count])

            # Populate the "Category Summary" table
            ws_category = wb.create_sheet(title=f"{index_name} Category Summary")
            ws_category.append(["Category", "Pass Rate", "Total Tests", "Pass Count"])
            for category, values in category_summary.items():
                pass_rate = (values["pass_count"] / values["total_tests"]) * 100 if values["total_tests"] > 0 else 0
                ws_category.append([category, f"{pass_rate:.2f}%", values["total_tests"], values["pass_count"]])

            # Populate the "Question Summary" table
            ws_question = wb.create_sheet(title=f"{index_name} Question Summary")
            ws_question.append(["Question", "Result", "Video Matching", "Snippet Overlap", "LLM Response Score"])
            for question, values in question_summary.items():
                ws_question.append([question, values["result"], "Pass" if values["video_matching"] else "Fail",
                                    "Pass" if values["snippet_overlap"] else "Fail", values["llm_response_score"]])

            # Populate the "Deep Dive" table
            ws_deep_dive = wb.create_sheet(title=f"{index_name} Deep Dive")
            ws_deep_dive.append(["Question Category", "Question", "Result", "Video Matching", "Snippet Time Overlap",
                                 "Ground Truth Similarity Score", "Ground Truth Video Title", "Ground Truth Snippet Start",
                                 "Ground Truth Snippet End", "Ground Truth Text", "Top Similarity Score for 5 Responses",
                                 "Top 5 Response Video Title"])
            for entry in deep_dive_summary.get(index_name, []):
                ws_deep_dive.append([entry[col] for col in ws_deep_dive.columns])

    # Save the report at the end of all tests
    wb.save(report_path)
    # generate_html_report(excel_file=report_path, output_html_file="report/test_report.html")

# Pytest fixture to run after all tests
@pytest.fixture(scope="session", autouse=True)
def after_all_tests():
    """This fixture runs after all tests are executed to calculate and save average accuracy."""
    yield  # Wait for all tests to finish
    try:
        calculate_and_save_average_accuracy()
        calculate_and_save_summary()
        generate_html_report(excel_file=excel_file, output_html_file=output_html_file)
    except Exception as e:
        print(f"Error in post-test processing: {e}")