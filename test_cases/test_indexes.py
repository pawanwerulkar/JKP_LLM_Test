
'''This script is to fetching responses from pinecone indexes according to that we are generate excel report and stored it into root report dir
   function test_pinecone_search response gets test data from perticular file. We have parameterize the kn indexes as well as test data.'''

import config
import pytest
import pinecone
from pinecone import Pinecone

from utils.email_utils2 import send_email_with_report
from utils.generate_html_report import generate_html_report, excel_file, output_html_file
from utils.pinecone_utils import query_pinecone2
from utils.utils import generate_embedding, check_overlap, check_time_matching
from utils.report_utils import get_or_create_report, calculate_and_save_summary, current_date
from utils.report_utils import calculate_and_save_average_accuracy, calculate_accuracy
from openpyxl import load_workbook
import os
import json

# Load test data
data_file_path = os.path.join(os.path.dirname(__file__), '../data/test_data.json')
with open(data_file_path, 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# Path for the report
report_path = fr"report/test_report_{current_date}.xlsx"
wb = get_or_create_report()
ws = wb["Test Results"]
ws_metrics = wb["Metrics"]

# Initialize Pinecone client
pc = Pinecone(api_key=config.PINECONE_API_KEY)



# # Retrieve the list of index names
index_name = pc.list_indexes().names()
print("Indexes:", index_name)


@pytest.mark.parametrize("data", test_data)
@pytest.mark.parametrize("index_name", index_name)
def test_pinecone_search_response(data, index_name):
    print(f"Running test for question: {data['question']} on index: {index_name}")

    question = data["question"]
    expected_snippet = data["expected_snippet"]
    expected_start_time = data["expected_start_time"]
    expected_end_time = data["expected_end_time"]

    #here we have add index_name report row to report
    report_row = {
        "Question": question,
        "Index": index_name,
        "Response Video Title": "",
        "Response Text": "",
        "Response Video": "",
        "Response Snippet Start": "",
        "Response Snippet End": "",
        "Ground Truth Video Title": "",
        "Ground Truth Text": "",
        "Ground Truth Video": "",
        "Ground Truth Snippet Start": "",
        "Ground Truth Snippet End": "",
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
            ws.append(list(report_row.values()))
            wb.save(report_path)  # Save report even if no matches found
            return

        # Process the top results and accessing the content
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

            # Check snippet overlaping result
            if not check_overlap(expected_snippet, actual_snippet):
                snippets_overlap = False
                print(f"Snippet overlap failed for video: {video_name} on index: {index_name}")
                should_fail = True

            # Check start and end time match result
            if not check_time_matching(expected_start_time, actual_start_time, expected_end_time, actual_end_time):
                time_match = False
                print(f"Time mismatch for video: {video_name} on index: {index_name}")
                should_fail = True

        # Fill in ground truth data/ expected data from the test data
        report_row["Ground Truth Video Title"] = "N/A"
        report_row["Ground Truth Text"] = expected_snippet
        report_row["Ground Truth Video"] = "N/A"
        report_row["Ground Truth Snippet Start"] = expected_start_time
        report_row["Ground Truth Snippet End"] = expected_end_time

        # test cases resport based on overlap and time
        if snippets_overlap and time_match:
            report_row["Result"] = "Pass"
            accuracy = calculate_accuracy(expected_snippet, actual_snippet)
        else:
            report_row["Result"] = "Fail"
            accuracy = 0


        print(f"Accuracy: {accuracy}%")

        # fill accuracy to the metrics sheet
        ws_metrics.append([index_name, "similarity-search", accuracy])

        # Append the report row to the Test Results worksheet and save
        ws.append(list(report_row.values()))
        wb.save(report_path)

    except Exception as e:
        print(f"Error querying Pinecone on index {index_name}: {e}")
        report_row["Result"] = f"Fail: {str(e)}"
        ws.append(list(report_row.values()))
        wb.save(report_path)  # Ensuring the workbook is saved in case of error any error

        should_fail = True  # If exception occurs, force failure

    # Assert at the end of the test to fail if conditions were met
    assert not should_fail, "Test failed due to snippet overlap or time mismatch."


#pytest fixture that will run before and after session

@pytest.fixture(scope="session", autouse=True)
def after_all_tests():
    get_or_create_report()
    """This fixture runs after all tests are executed and then calls the function to calculate and save average accuracy."""
    yield

    calculate_and_save_average_accuracy()
    calculate_and_save_summary()
    generate_html_report(excel_file=excel_file,output_html_file=output_html_file)
    # save_report_date()
    #send_email_with_report()




