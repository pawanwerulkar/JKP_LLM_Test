import pandas as pd
import os

# Function to generate the HTML report
def generate_html_report(excel_file, output_html_file):
    excel_data = pd.ExcelFile(excel_file)

    # Create the HTML report
    html_report = """
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Excel Report</title>
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

# Example usage
excel_file = r"report/test_report.xlsx"  #excel
output_html_file = "report/test_report.html"  # Output HTML file path

