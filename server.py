from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
import os
import certifi
from UploadFile import upload_to_drive
from bson.objectid import ObjectId

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Update MongoDB URI with correct SSL configuration
app.config["MONGO_URI"] = "MONGO_API"

# Initialize PyMongo
mongo = PyMongo(app)

# Authentication check decorator


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
@login_required  # Ensure only logged-in users can access
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
        project_description = request.form.get(
            'project_description', '').strip()

        if not project_name or not project_description:
            flash("Project name and description are required.", "danger")
            return redirect(request.url)

        try:
            # Upload the file and get the file URL
            file_url = upload_to_drive(file)

            # Update the user's project information in the database
            mongo.db.students.update_one(
                {"_id": ObjectId(session['user_id'])},
                {
                    "$push": {
                        "projects": {
                            "project_name": project_name,
                            "project_description": project_description,
                            "link": file_url
                        }
                    }
                }
            )

            flash("File uploaded and project added successfully!", "success")
            # Redirect to the user dashboard
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(request.url)
    return render_template("upload.html")


if __name__ == '__main__':
    app.run(debug=True, port=8080)
