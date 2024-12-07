# GenAI Project Hosting Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg) ![Flask](https://img.shields.io/badge/flask-2.3-lightgrey.svg)

A **Flask-based web application** that allows students to host their GenAI project documents by logging in with their credentials. This platform was developed collaboratively by **Sai Teja** and **Mushtaq** for our college.

---

## 🚀 Features

- **User Authentication**:
  - Login functionality to ensure secure access.
- **File Uploads**:
  - Students can upload GenAI project-related documents directly to the platform.
- **Google Drive Integration**:
  - Files are securely uploaded and stored using the Google Drive API.
- **User-Friendly Interface**:
  - Simple and intuitive design for students to manage their documents easily.

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, Jinja2 Templates, Bootstrap, Favicon
- **Storage**: Google Drive API
- **Libraries**:
  - `Flask`
  - `Flask-WTF`
  - `Google API Client`
  - `Werkzeug` (for file handling)

---

## 📂 Project Structure

```plaintext
host-gen-ai-projects/
├── UploadFile.py            # Handles file uploads to Google Drive
├── data_loader.py           # Data management and processing
├── server.py                # Main Flask application
├── templates/               # HTML templates for the web app
│   ├── login.html
│   ├── upload.html
│   ├── user.html
│   └── view_user.html
├── .env.example             # Example environment variables
└── service-account.json     # Google Drive API service account credentials
```

---

## 🔧 Installation

Follow these steps to set up the project locally:

### 1. Clone the Repository

```bash
git clone https://github.com/thesaiteja24/gen-ai-projects-nriit.git
cd genai-project-hosting
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Rename `.env.example` to `.env`.
2. Update the values of the following environment variables in `.env`:
   - `MONGO_URI`
   - `SESSION_KEY`
   - `PASSWORD`
   - `MONGO_URI_2`
3. Ensure the correct values are used for your setup.

### 5. Set Up Google Drive API

1. Obtain a service account JSON file for your Google Drive API project.
2. Place it in the project root directory and name it `service-account.json`.

### 6. Run the Application

```bash
python server.py
```

Access the app at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## 📝 Usage

### Steps to Log In:

1. **Enter Credentials**: Enter your username and password to log in.
2. **Upload File**: Navigate to the upload section and upload your GenAI project document.

### Viewing Uploaded Files:

- After logging in, view your uploaded documents in the **View Projects** section.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 📬 Contact

If you have any questions or feedback, feel free to reach out:

- **Name**: Sai Teja
- **GitHub**: [thesaiteja24](https://github.com/thesaiteja24)

and

- **Name**: Mushtaq Ahamad
- **GitHub**: [Mushtaq1295](https://github.com/Mushtaq1295)

---

### 🙌 Acknowledgments

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Drive API Documentation](https://developers.google.com/drive/api/)
- **Mushtaq** for collaborative development and brainstorming.
