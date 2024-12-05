from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import os

# Google Drive API Setup
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = './service-account.json'

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def convert_bytes(bytes_val):
    """
    Convert bytes to KB, MB, and GB
    """
    if not bytes_val:
        return 0, 0, 0
    
    kb = bytes_val / 1024
    mb = kb / 1024
    gb = mb / 1024
    
    return kb, mb, gb

def check_drive_storage():
    """
    Check current Google Drive storage usage in multiple units
    """
    about = drive_service.about().get(fields="storageQuota").execute()
    quota = about.get('storageQuota', {})
    
    # Get total storage
    total_bytes = float(quota.get('limit', 0))
    total_kb, total_mb, total_gb = convert_bytes(total_bytes)
    
    # Get used storage
    used_bytes = float(quota.get('usage', 0))
    used_kb, used_mb, used_gb = convert_bytes(used_bytes)
    
    # Calculate remaining storage
    remaining_bytes = total_bytes - used_bytes
    remaining_kb, remaining_mb, remaining_gb = convert_bytes(remaining_bytes)
    
    # Calculate usage percentage
    usage_percentage = (used_bytes/total_bytes*100) if total_bytes > 0 else 0
    
    print("\nDrive Storage Status:")
    print("\nTotal Storage:")
    print(f"  {total_kb:.2f} KB")
    print(f"  {total_mb:.2f} MB")
    print(f"  {total_gb:.2f} GB")
    
    print("\nUsed Storage:")
    print(f"  {used_kb:.2f} KB")
    print(f"  {used_mb:.2f} MB")
    print(f"  {used_gb:.2f} GB")
    
    print("\nRemaining Storage:")
    print(f"  {remaining_kb:.2f} KB")
    print(f"  {remaining_mb:.2f} MB")
    print(f"  {remaining_gb:.2f} GB")
    
    print(f"\nUsage Percentage: {usage_percentage:.2f}%")

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

# Check storage when the script runs
if __name__ == "__main__":
    check_drive_storage()