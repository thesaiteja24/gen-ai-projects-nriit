from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
import os
import certifi
from UploadFile import upload_to_drive
from bson.objectid import ObjectId
import magic

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.environ.get("SESSION_KEY")

# Update MongoDB URI with correct SSL configuration
app.config["MONGO_URI"] = os.environ.get('MONGO_URI') + certifi.where()
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024
# Initialize PyMongo
mongo = PyMongo(app)


def login_required(f):
    def wrapper(*args, **kwargs):
        if 'student_id' not in session:  # Check if user is logged in
            flash("You need to log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Preserve the function name
    return wrapper


@app.route('/<path:path>')
def fallback(path):
    return render_template('page-not-found.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        user = mongo.db.students.find_one({"student_id": student_id})
        if user and user['password'] == password:
            session['user_id'] = str(user['_id'])
            session['student_id'] = student_id
            session['fullname'] = user.get('fullname', 'User')
            # Redirect to user dashboard
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/user')
@login_required
def user_dashboard():
    try:
        # Convert session['user_id'] to ObjectId
        user = mongo.db.students.find_one(
            {"_id": ObjectId(session['user_id'])})
        if not user:
            flash("User not found. Please log in again.", "danger")
            return redirect(url_for('login'))

        # Safely get 'projects' or default to an empty list
        projects = user.get('projects', [])
        return render_template('user.html', fullname=user['fullname'], projects=projects)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)

        # Get the project details from the form
        project_name = request.form.get('project_name', '').strip()
        project_description = request.form.get('project_description', '').strip()

        if not project_name or not project_description:
            flash("Project name and description are required.", "danger")
            return redirect(request.url)

        try:
            # Server-side file type validation using MIME type
            mime = magic.Magic(mime=True)
            file_mime_type = mime.from_buffer(file.stream.read(2048))
            file.stream.seek(0)  # Reset file pointer after reading

            if file_mime_type != "application/pdf":
                flash(
                    "Only PDF files are allowed. Please upload a valid file.", "danger")
                return redirect(request.url)

            # Upload the file and get the file URL and file ID
            file_url, file_id = upload_to_drive(file)

            # Generate a unique ID for the project
            project_id = ObjectId()

            # Update the user's project information in the database
            mongo.db.students.update_one(
                {"_id": ObjectId(session['user_id'])},
                {
                    "$push": {
                        "projects": {
                            "_id": project_id,  # Add project ID
                            "project_name": project_name,
                            "project_description": project_description,
                            "link": file_url,      # Direct link field
                            "file_id": file_id     # Direct file_id field
                        }
                    }
                }
            )

            flash("File uploaded and project added successfully!", "success")
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(request.url)
    return render_template("upload.html")


@app.route('/delete/<project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    try:
        # Convert project_id to ObjectId
        project_id = ObjectId(project_id)

        # Find the project to get the file_id
        user = mongo.db.students.find_one(
            {"_id": ObjectId(session['user_id'])})
        project = next((p for p in user.get('projects', [])
                       if p['_id'] == project_id), None)

        if not project:
            flash("Project not found or already deleted.", "danger")
            return redirect(url_for('user_dashboard'))

        # Delete the file from Google Drive
        file_id = project.get('file_id')
        if file_id:
            try:
                drive_service.files().delete(fileId=file_id).execute()
                flash("File deleted from Google Drive.", "success")
            except Exception as e:
                flash(
                    f"Failed to delete file from Google Drive: {str(e)}", "danger")

        # Remove the project from the user's projects
        result = mongo.db.students.update_one(
            {"_id": ObjectId(session['user_id'])},
            {"$pull": {"projects": {"_id": project_id}}}
        )

        if result.modified_count > 0:
            flash("Project deleted successfully.", "success")
        else:
            flash("Project not found or already deleted.", "danger")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
    return redirect(url_for('user_dashboard'))


@app.route('/id/<roll_number>', methods=['GET'])
def view_user_by_roll(roll_number):
    # Fetch the user details using the roll number
    user = mongo.db.students.find_one({"student_id": roll_number})
    projects = user.get('projects', []) if user else []

    # Render the `view_user.html` template directly
    return render_template(
        'view_user.html',
        fullname=user['fullname'] if user else "Unknown User",
        projects=projects
    )


@app.route('/flash_message')
def flash_message():
    msg = request.args.get('msg', '')
    category = request.args.get('category', 'info')
    flash(msg, category)
    return redirect(request.referrer or url_for('user_dashboard'))


@app.errorhandler(413)
def request_entity_too_large(error):
    flash("File size exceeds 3MB limit.", "danger")
    return redirect(request.referrer or url_for('upload_file')), 413


@app.route('/')
def home():
    # Redirect to the login route
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
