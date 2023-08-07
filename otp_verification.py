import random
import string
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

class OtpHandler:
    def __init__(self):
        self.gmail_username = os.environ.get('GMAIL_USERNAME')
        self.gmail_password = os.environ.get('GMAIL_PASSWORD')

    def generate_otp(self, length=6):
        characters = string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def send_email(self, subject, body, to_email):
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_username, self.gmail_password)

            message = f'Subject: {subject}\n\n{body}'
            server.sendmail(self.gmail_username, to_email, message)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

