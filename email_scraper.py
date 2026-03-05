import os
import base64
import hashlib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from models import JobLead

class EmailScraper:
    """
    Directly pulls and decodes job leads from Gmail via OAuth2.
    """
    def __init__(self, credentials_path='credentials.json'):
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        self.creds = self._auth(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _auth(self, path):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(path, self.scopes)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    async def scrape_inbox(self, query: str) -> list[JobLead]:
        results = self.service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        leads = []
        for msg in messages[:5]:
            m = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = m.get('payload', {})
            body_data = payload.get('body', {}).get('data', '')
            
            if body_data:
                clean_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
                job_id = hashlib.sha256(f"gmail_{msg['id']}".encode()).hexdigest()[:32]
                
                leads.append(JobLead(
                    job_id=job_id,
                    title="Email Discovery",
                    company="Direct Contact",
                    url=f"https://mail.google.com/mail/u/0/#inbox/{msg['id']}",
                    description=clean_text,
                    source_method="GmailAPI"
                ))
        return leads