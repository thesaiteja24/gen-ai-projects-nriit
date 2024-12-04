from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
import os
import certifi

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Update MongoDB URI with correct SSL configuration
app.config["MONGO_URI"] = "MONGO_URL"

# Initialize PyMongo
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


@app.route('/<path:path>')
def fallback(path):
    return render_template('page-not-found.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        user = mongo.db.users.find_one({"student_id": student_id})
        if user and user['password'] == password:
            session['user_id'] = str(user['_id'])
            session['student_id'] = student_id
            return "user logged in"
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return f"Welcome, {session['username']}! You are logged in."
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
