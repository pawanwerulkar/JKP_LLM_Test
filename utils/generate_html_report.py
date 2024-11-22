import pandas as pd
# import os
from utils.report_utils import current_date, report_path

# This function will generate HTML file for excel-report
def generate_html_report(excel_file, output_html_file):
    excel_data = pd.ExcelFile(excel_file)

    # Create the HTML report
    html_report = """
    <html>
    <head>
        <meta charset="UTF-8">
        <title>KN Test Report</title>
    </head>
    <body>
        <h1>Excel Report</h1>
    """

    # Loop through the sheets and convert each sheet into a table
    for sheet_name in reversed(excel_data.sheet_names):
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        html_report += f"<h2>Sheet: {sheet_name}</h2>"
        html_report += df.to_html(index=False, border=1)

    html_report += """
    </body>
    </html>
    """

    # Write the HTML report to a file with UTF-8 encoding
    with open(output_html_file, "w", encoding="utf-8") as file:
        file.write(html_report)

    print(f"HTML report saved to {output_html_file}")


excel_file = fr"report/test_report_{current_date}.xlsx"
output_html_file = f"report/test_report_{current_date}.html"

