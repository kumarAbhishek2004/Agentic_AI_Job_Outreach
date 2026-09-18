import os
import base64
import mimetypes
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                print(f"ERROR: Missing {GMAIL_CREDENTIALS_PATH}.")
                print("You must download your OAuth 2.0 Client credentials from Google Cloud Console and save it as credentials.json")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES)
            # This opens a web browser to let the user authenticate
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(GMAIL_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def send_email(to_address, subject, body, resume_filename):
    """Creates a draft email via the Gmail API, attaching the specified resume."""
    service = authenticate_gmail()
    if not service:
        return False, "Failed to authenticate with Gmail."

    try:
        message = EmailMessage()
        
        # Set plain text fallback
        message.set_content(body)
        
        # Convert plain text to nice HTML so it formats beautifully in Gmail
        # We split by double-newline to wrap paragraphs, allowing precise control over the gap size
        normalized_body = body.replace('\r\n', '\n')
        paragraphs = normalized_body.split('\n\n')
        
        html_parts = []
        for p in paragraphs:
            # Any single newlines inside a paragraph just get a normal break
            p_html = p.replace('\n', '<br>')
            # margin: 0 0 10px 0 creates a tight 10px gap instead of a massive full blank line
            html_parts.append(f'<p style="margin: 0 0 10px 0; font-family: Arial, sans-serif; font-size: 14px; color: #222222;">{p_html}</p>')
            
        html_body = "<html><body>\n" + "\n".join(html_parts) + "\n</body></html>"
        message.add_alternative(html_body, subtype='html')
        
        message['To'] = to_address
        message['Subject'] = subject
        
        # Attach Resume if specified
        if resume_filename:
            resume_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resumes', resume_filename)
            if os.path.exists(resume_path):
                mime_type, _ = mimetypes.guess_type(resume_path)
                mime_type, mime_subtype = mime_type.split('/', 1) if mime_type else ('application', 'pdf')
                
                with open(resume_path, 'rb') as f:
                    message.add_attachment(
                        f.read(),
                        maintype=mime_type,
                        subtype=mime_subtype,
                        filename=resume_filename
                    )
            else:
                print(f"Warning: Resume {resume_filename} not found at {resume_path}")

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # CREATE DRAFT INSTEAD OF SENDING
        draft_body = {'message': {'raw': encoded_message}}
        draft = service.users().drafts().create(userId="me", body=draft_body).execute()
        return True, draft['id']
        
    except Exception as e:
        print(f"Error creating draft for {to_address}: {e}")
        return False, str(e)
