from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os

# Google Drive API Setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = '/Users/saiteja/gh repos/host-gen-ai-projects/service-account.json'

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)


def upload_to_drive(file):
    """
    Upload a file to Google Drive and return the shareable link.

    :param file: File object from Flask's `request.files`.
    :return: Shareable link of the uploaded file.
    """
    try:
        # Create 'uploads' directory if it doesn't exist
        if not os.path.exists('uploads'):
            os.mkdir('uploads')

        # Save the file locally (temporarily)
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

        # Upload the file to Google Drive
        file_metadata = {'name': file.filename}
        media = MediaFileUpload(file_path, resumable=True)
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        # Get the file ID and generate a shareable link
        file_id = uploaded_file.get('id')
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        file_url = f"https://drive.google.com/file/d/{file_id}/view"

        # Clean up the local file
        os.remove(file_path)

        return file_url
    except Exception as e:
        raise RuntimeError(f"An error occurred during upload: {str(e)}")
