from flask import Flask, render_template, request, flash, redirect, url_for
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Google Drive API Setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
# Replace with your credentials file
SERVICE_ACCOUNT_FILE = '/Users/saiteja/gh repos/host-gen-ai-projects/service-account.json'

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part", "danger")
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash("No selected file", "danger")
        return redirect(request.url)

    try:
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

        flash(f"File uploaded successfully! <a href='{file_url}' target='_blank'>View File</a>", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect('/')


if __name__ == "__main__":
    # Create 'uploads' directory if it doesn't exist
    if not os.path.exists('uploads'):
        os.mkdir('uploads')
    app.run(debug=True)
