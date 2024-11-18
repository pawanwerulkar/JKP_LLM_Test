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
    report_path = os.getenv("REPORT_PATH", r"C:\Users\test_complete\PycharmProjects\KN_LLM\test_cases\report\test_report.xlsx")  # Adjust this default path as needed
    sender_email = os.getenv("SENDER_EMAIL", "pawanwerulkar1995@gmail.com")  # Add a default for testing
    # receiver_email = os.getenv("RECEIVER_EMAIL", "pawanwerulkar1995@gmail.com")  # Add a default for testing
    receiver_email = os.getenv("RECEIVER_EMAILS", "pawanwerulkar1995@gmail.com,deepak.jain@subtlelabs.com,sachin.singh@subtlelabs.com,udgam.goyal10@gmail.com,naveen@jkp.org.in").split(',')
    print(receiver_email)
    password = os.getenv("EMAIL_PASSWORD", "izwl jjuh rqyj tbun")  # Add a default for testing

    # Debugging statements to confirm environment variable values
    logger.debug(f"Report Path: {report_path}")
    logger.debug(f"Sender Email: {sender_email}")
    logger.debug(f"Receiver Email: {receiver_email}")
    logger.debug(f"Password Set: {'Yes' if password else 'No'}")

    # Ensure all necessary variables are set
    if not (report_path and sender_email and receiver_email and password):
        raise ValueError(
            "Please set the report path, sender email, receiver email, and email password. "
            f"Current values -> report_path: {report_path}, sender_email: {sender_email}, "
            f"receiver_email: {receiver_email}, password: {'Set' if password else 'Not Set'}"
        )

    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_email)
    msg['Subject'] = "Automated Test Report"

    # Email body
    body = "Please find attached the latest test report."
    msg.attach(MIMEText(body, 'plain'))

    # Attach the XLSX report
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
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            logger.info("Email sent successfully.")
    except smtplib.SMTPException as e:
        logger.error("Failed to send email.")
        raise e

if __name__ == "__main__":
    send_email_with_report()
