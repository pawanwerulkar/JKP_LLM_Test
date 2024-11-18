import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging

# Set up logging to capture debugging information
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def send_email_with_report():
    # Configure paths and credentials (either hardcode for testing or use environment variables)
    report_path = os.getenv("REPORT_PATH", r"C:\Users\test_complete\PycharmProjects\KN_LLM\report\test_report.html")  # Adjust this default path as needed
    sender_email = os.getenv("SENDER_EMAIL", "pawanwerulkar1995@gmail.com")  # Add a default for testing
    # receiver_email = os.getenv("RECEIVER_EMAILS", "udgam.goyal10@gmail.com,naveen@jkp.org.in,pawanwerulkar1995@gmail.com,sachin.singh@subtlelabs.com,deepak.jain@subtlelabs.com").split(',')
    receiver_email = os.getenv("RECEIVER_EMAILS", "pawanwerulkar1995@gmail.com,sachin.singh@subtlelabs.com").split(',')

    password = os.getenv("EMAIL_PASSWORD", "izwl jjuh rqyj tbun")  # Add a default for testing
    #deepak.jain@subtlelabs.com,,udgam.goyal10@gmail.com,naveen@jkp.org.in
    # Debugging: Ensure all necessary variables are set
    logger.debug(f"Report Path: {report_path}")
    logger.debug(f"Sender Email: {sender_email}")
    logger.debug(f"Receiver Emails: {receiver_email}")
    logger.debug(f"Password Set: {'Yes' if password else 'No'}")

    # Ensure all necessary variables are set
    if not (report_path and sender_email and receiver_email and password):
        raise ValueError(
            "Please set the report path, sender email, receiver email, and email password."
        )

    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_email)
    msg['Subject'] = "Automated Test Report"

    # Email body
    body = "Please find attached the latest test report."
    msg.attach(MIMEText(body, 'plain'))

    # Attach the HTML report
    try:
        with open(report_path, "r", encoding="utf-8") as html_file:  # Specify UTF-8 encoding
            html_content = html_file.read()  # Read the file content

        # Attach the HTML content directly to the email body (inline)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        logger.debug("HTML report attached successfully.")

    except FileNotFoundError as e:
        logger.error(f"HTML report file not found: {report_path}")
        raise e
    except UnicodeDecodeError as e:
        logger.error(f"Error decoding HTML file with UTF-8 encoding: {e}")
        raise e

#attach excel
    try:
        with open(report_path, "rb") as attachment:
            part = MIMEApplication(attachment.read(), Name="test_report.xlsx")
            part['Content-Disposition'] = f'attachment; filename="test_report.xlsx"'
            msg.attach(part)
        logger.debug("Report file attached successfully.")
    except FileNotFoundError as e:
        logger.error(f"Report file not found: {report_path}")
        raise e

    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:  # For Gmail SMTP; change as per your provider
            server.starttls()  # Encrypt the connection
            server.login(sender_email, password)
            server.send_message(msg)
            logger.info("Email sent successfully.")
    except smtplib.SMTPException as e:
        logger.error("Failed to send email.")
        raise e

# if __name__ == "__main__":
#     send_email_with_report()
