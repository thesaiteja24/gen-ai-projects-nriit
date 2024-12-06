from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
import os
import certifi
from UploadFile import upload_to_drive, delete_from_drive
from bson.objectid import ObjectId
import magic
import bcrypt

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.environ.get("SESSION_KEY", "default_secret_key")

# MongoDB Configuration
app.config["MONGO_URI"] = os.environ.get("MONGO_URI") + certifi.where()
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024  # Limit upload size to 3MB

# Initialize MongoDB connection
mongo = PyMongo(app)


# ----------------------------- Utility Functions ---------------------------- #

def login_required(f):
    """
    Decorator to restrict access to authenticated users.
    Redirects to login if the user is not logged in.
    """
    def wrapper(*args, **kwargs):
        if 'student_id' not in session:
            flash("You need to log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Preserve original function name
    return wrapper


def get_user_projects():
    """
    Fetch the currently logged-in user's projects.
    Returns the user document and projects list.
    """
    user = mongo.db.students.find_one({"_id": ObjectId(session['user_id'])})
    if not user:
        flash("User not found. Please log in again.", "danger")
        return None, []
    return user, user.get("projects", [])


# ----------------------------- Error Handlers ----------------------------- #

@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handles file size limit errors (413).
    """
    flash("File size exceeds 3MB limit.", "danger")
    return redirect(request.referrer or url_for('upload_file')), 413


@app.errorhandler(404)
def page_not_found(error):
    """
    Handles 404 errors and displays a custom page.
    """
    return render_template('page-not-found.html'), 404


# ------------------------------- Routes ----------------------------------- #

@app.route('/')
def home():
    """
    Redirects to the login page.
    """
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login functionality.
    If session exists, redirect the user to the dashboard automatically.
    """
    # Check if the user is already logged in
    if 'student_id' in session:
        flash("You are already logged in.", "info")
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')

        # Verify user credentials
        user = mongo.db.students.find_one({"student_id": student_id})
        if user and bcrypt.checkpw(password.encode('utf-8'), user.get("password").encode('utf-8')):
            session['user_id'] = str(user['_id'])
            session['student_id'] = student_id
            session['fullname'] = user.get('fullname', 'User')
            flash("Login successful!", "success")
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Logs the user out and clears the session.
    """
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/user')
@login_required
def user_dashboard():
    """
    Displays the user dashboard with their projects.
    """
    try:
        user, projects = get_user_projects()
        if not user:
            return redirect(url_for('login'))

        return render_template('user.html', fullname=user['fullname'], projects=projects)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """
    Handles file uploads and associates them with user projects.
    """
    if request.method == 'POST':
        file = request.files.get('file')
        project_name = request.form.get('project_name', '').strip()
        project_description = request.form.get(
            'project_description', '').strip()

        if not file or file.filename == '':
            flash("No file selected.", "danger")
            return redirect(request.url)

        if not project_name or not project_description:
            flash("Project name and description are required.", "danger")
            return redirect(request.url)

        try:
            # Validate file type (must be PDF)
            mime = magic.Magic(mime=True)
            file_mime_type = mime.from_buffer(file.read(2048))
            file.seek(0)  # Reset file pointer

            if file_mime_type != "application/pdf":
                flash("Only PDF files are allowed.", "danger")
                return redirect(request.url)

            # Upload file and save project details
            file_url, file_id = upload_to_drive(file)
            project_id = ObjectId()
            mongo.db.students.update_one(
                {"_id": ObjectId(session['user_id'])},
                {"$push": {
                    "projects": {
                        "_id": project_id,
                        "project_name": project_name,
                        "project_description": project_description,
                        "link": file_url,
                        "file_id": file_id
                    }
                }}
            )
            flash("File uploaded successfully!", "success")
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('upload.html')


@app.route('/delete/<project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    """
    Deletes a user project and its associated file.
    """
    try:
        user, projects = get_user_projects()
        if not user:
            return redirect(url_for('login'))

        project = next(
            (p for p in projects if str(p["_id"]) == project_id), None)
        if not project:
            flash("Project not found.", "danger")
            return redirect(url_for('user_dashboard'))

        # Delete file from Google Drive
        file_id = project.get('file_id')
        if file_id:
            delete_from_drive(file_id)

        # Remove project from database
        mongo.db.students.update_one(
            {"_id": ObjectId(session['user_id'])},
            {"$pull": {"projects": {"_id": ObjectId(project_id)}}}
        )
        flash("Project deleted successfully.", "success")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
    return redirect(url_for('user_dashboard'))


@app.route('/id/<roll_number>', methods=['GET'])
def view_user_by_roll(roll_number):
    """
    Displays user details by their roll number.
    """
    user = mongo.db.students.find_one({"student_id": roll_number})
    projects = user.get('projects', []) if user else []
    return render_template(
        'view_user.html',
        fullname=user['fullname'] if user else "Unknown User",
        projects=projects
    )


@app.route('/flash_message')
def flash_message():
    """
    Handles flash messages and redirects.
    """
    msg = request.args.get('msg', '')
    category = request.args.get('category', 'info')
    flash(msg, category)
    return redirect(request.referrer or url_for('user_dashboard'))


# ------------------------------- Main Entry -------------------------------- #

if __name__ == '__main__':
    app.run()
