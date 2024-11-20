# import pytest
# from utils.pinecone_utils import query_pinecone
# from utils.utils import generate_embedding, check_overlap, check_time_matching
# from utils.report_utils import get_or_create_report
# from utils.report_utils import calculate_and_save_average_accuracy,calculate_accuracy,calculate_and_save_summary
# from openpyxl import load_workbook
# import os
# # Load test data
# import json
# data_file_path = os.path.join(os.path.dirname(__file__), '../data/test_data.json')
# with open(data_file_path, 'r', encoding='utf-8') as f:
#     test_data = json.load(f)
#
# report_path = "report/test_report.xlsx"
# wb = get_or_create_report()
# ws = wb["Test Results"]
# ws_metrics = wb["Metrics"]
# #
# # def calculate_accuracy(expected_snippet, actual_snippet):
# #     expected_words = expected_snippet.split()
# #     actual_words = actual_snippet.split()
# #     match_count = sum(1 for word in expected_words if word in actual_words)
# #     return (match_count / len(expected_words)) * 100 if expected_words else 0
#
# @pytest.mark.parametrize("data", test_data)
# def test_pinecone_search_response(data):
#     print("Running test for question:", data["question"])  # Debug statement
#
#     question = data["question"]
#     expected_snippet = data["expected_snippet"]
#     expected_start_time = data["expected_start_time"]
#     # expected_start_time = data.get("expected_start_time", "")
#     expected_end_time = data["expected_end_time"]
#     # expected_end_time = data.get("expected_end_time", "")
#     last_row = ws.max_row + 1
#     report_row = {
#         "Question": question,
#         "Response Video Title": "",
#         "Response Text": "",
#         "Response Video": "",
#         "Response Snippet Start": "",
#         "Response Snippet End": "",
#         "Ground Truth Video Title": "",
#         "Ground Truth Text": "",
#         "Ground Truth Video": "",
#         "Ground Truth Snippet Start": "",
#         "Ground Truth Snippet End": "",
#         "Result": ""
#     }
#
#     # Initialize flags
#     snippets_overlap = True
#     time_match = True
#     should_fail = False  # Flag to track failure conditions
#
#     # Generate embedding for the question
#     # embedding = generate_embedding(question)
#     # Generate embedding for the question
#     embedding = generate_embedding(question)
#     # Query Pinecone
#     try:
#         response = query_pinecone(embedding, top_k=5)
#         top_results = response.get("matches", [])
#         print(response)
#         if isinstance(response, list):
#             print("Response is list")
#             top_results = response
#         else:
#             top_results = response.get("matches", [])
#
#         if not top_results:
#             print("No matches found.")
#             report_row["Result"] = "Fail: No matches found"
#             should_fail = True  # Set the flag to fail the test
#             ws.append(list(report_row.values()))
#             wb.save(report_path)  # Save report even if no matches found
#             return
#
#         # for result in top_results:
#         #     actual_snippet = result.get("metadata", {}).get("page_content", "")
#         #     actual_start_time = result.get("metadata", {}).get("start", "")
#         #     actual_end_time = result.get("metadata", {}).get("end", "")
#         #     video_name = result.get("metadata", {}).get("media_source", "")
#         for result in top_results:
#             # Access metadata directly, as `result` is a Document object
#             actual_snippet = result.page_content  # result.metadata.get("page_content", "")  # Access content
#             actual_start_time = result.metadata.get("start", "")  # Access start time
#             actual_end_time = result.metadata.get("end", "")  # Access end time
#             video_name = result.metadata.get("name", "")  # Access video name
#             print(f"Processing result for video: {video_name}")  # Debug statement
#
#             # Fill report_row with the actual response data
#             report_row["Response Video Title"] = video_name
#             report_row["Response Text"] = actual_snippet
#             report_row["Response Video"] = result.metadata.get("media_source", "")
#             report_row["Response Snippet Start"] = actual_start_time
#             report_row["Response Snippet End"] = actual_end_time
#
#             # Check snippet overlap
#             if not check_overlap(expected_snippet, actual_snippet):
#                 snippets_overlap = False
#                 print(f"Snippet overlap failed for video: {video_name}")
#                 should_fail = True  # Set the flag to fail the test
#
#             # Check start and end time match
#             if not check_time_matching(expected_start_time, actual_start_time, expected_end_time, actual_end_time):
#                 time_match = False
#                 print(f"Time mismatch for video: {video_name}")
#                 should_fail = True  # Set the flag to fail the test
#
#         # Fill in ground truth data from the test data
#         report_row["Ground Truth Video Title"] = "N/A"  # data.get("ground_truth_video_title", "")
#         report_row["Ground Truth Text"] = expected_snippet  # data.get("ground_truth_text", "")
#         report_row["Ground Truth Video"] =  "N/A" # data.get("ground_truth_video", "")
#         report_row["Ground Truth Snippet Start"] = expected_start_time
#         report_row["Ground Truth Snippet End"] = expected_end_time
#
#         # Determine result based on overlap and time checks
#         if snippets_overlap and time_match:
#             report_row["Result"] = "Pass"
#             accuracy = calculate_accuracy(expected_snippet, actual_snippet)
#         else:
#             report_row["Result"] = "Fail"
#             accuracy = 0  # Set accuracy to 0 for failures
#
#         # Print the accuracy score for debugging
#         print(f"Accuracy: {accuracy}%")
#
#         # Append to Metrics with specified index and model name
#         last_row = ws.max_row + 1
#         ws_metrics.append(["basic-kn-index2", "similarity-search", accuracy])
#
#         # Append the report row to the worksheet and save
#         ws.append(list(report_row.values()))
#         wb.save(report_path)
#
#     except Exception as e:
#         print(f"Error querying Pinecone: {e}")
#         report_row["Result"] = f"Fail: {str(e)}"
#         ws.append(list(report_row.values()))
#         wb.save(report_path)  # Ensuring the workbook is saved in case of error any error
#
#         should_fail = True  # If exception occurs, force failure
#
#     # Assert at the end of the test to fail if conditions were met
#     assert not should_fail, "Test failed due to snippet overlap or time mismatch."
#
# @pytest.fixture(scope="session", autouse=True)
# def after_all_tests():
#     get_or_create_report()
#
#     """This fixture runs after all tests are executed and then calls the function to calculate and save average accuracy."""
#     # This function will be called after all test cases have finished running
#     yield  # pytest will run tests before this part
#
#     # Call the function to calculate and save average accuracy after all tests are done
#     # get_or_create_report()  # This will ensure the report and directory are created if not present.
#     calculate_and_save_summary()  # This will calculate and append the summary to the report.
#     calculate_and_save_average_accuracy()