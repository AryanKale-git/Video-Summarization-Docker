from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, g, after_this_request
import cv2
import numpy as np
import os
import sqlite3
import secrets
from werkzeug.utils import secure_filename
# Use Werkzeug's secure password hashing functions
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# --- Configuration ---
# Load secret key from environment variable. Fail if not set.
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("No SECRET_KEY set for Flask application")

# Email configuration - CHANGE THESE TO YOUR ACTUAL EMAIL SETTINGS
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
if not (EMAIL_ADDRESS and EMAIL_PASSWORD):
    app.logger.warning("Email credentials (EMAIL_ADDRESS, EMAIL_PASSWORD) are not set. Password reset will not work.")

# Set the server name for external URL generation (e.g., 'localhost:5000')
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')

# Create necessary directories
os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)
os.makedirs("templates", exist_ok=True)

DATABASE = os.path.join(app.instance_path, 'users.db')

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        # Ensure the instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row  # This allows accessing columns by name
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()


# Database initialization
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_token TEXT,
            reset_token_expires TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


# Helper functions
def generate_reset_token():
    return secrets.token_urlsafe(32)


def get_user_by_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    return user


def get_user_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    return user


def create_user(username, email, password):
    db = get_db()
    cursor = db.cursor()
    try:
        # Use a strong, salted password hash
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def update_reset_token(email, token):
    db = get_db()
    cursor = db.cursor()
    expires = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
    cursor.execute('''
        UPDATE users SET reset_token = ?, reset_token_expires = ?
        WHERE email = ?
    ''', (token, expires, email))
    db.commit()


def verify_reset_token(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT email FROM users 
        WHERE reset_token = ? AND reset_token_expires > ?
    ''', (token, datetime.now()))
    result = cursor.fetchone()
    return result['email'] if result else None


def reset_password(email, new_password):
    db = get_db()
    cursor = db.cursor()
    password_hash = generate_password_hash(new_password)
    cursor.execute('''
        UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
        WHERE email = ?
    ''', (password_hash, email))
    db.commit()


def send_reset_email(email, username, token):
    """Send password reset email to user"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = "Password Reset - Video Summarizer"

        # Create reset link
        reset_link = url_for('reset_password_token', token=token, _external=True)

        # Email body
        body = f"""
Hello {username},

You have requested to reset your password for Video Summarizer.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
Video Summarizer Team
        """

        msg.attach(MIMEText(body, 'plain'))

        # Connect to server and send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Video summarization function - keeping your original algorithm
def summarize_video(input_path, output_path, frame_skip=5):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) // 2  # Reduce output video FPS

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:  # Skip frames for faster processing
            continue

        mask = back_sub.apply(frame)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        _, thresh = cv2.threshold(mask, 25, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        significant_movement = False

        for contour in contours:
            if cv2.contourArea(contour) > 1500:  # Filter based on contour size
                significant_movement = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Movement", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 2)

        if significant_movement:  # Only write frames with motion
            out.write(frame)

    cap.release()
    out.release()


# Routes
@app.route("/")
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("video_summarizer.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template("register.html")

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template("register.html")

        if create_user(username, email, password):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists!', 'error')

    return render_template("register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']

        # Verify user exists by both username and email
        user_by_username = get_user_by_username(username)
        user_by_email = get_user_by_email(email)

        # Check if username and email belong to the same user account
        if (user_by_username and user_by_email and
                user_by_username['id'] == user_by_email['id']):  # Same user ID

            token = generate_reset_token()
            update_reset_token(email, token)

            # Send reset email
            if send_reset_email(email, username, token):
                flash('Password reset email sent! Check your inbox and follow the instructions.', 'success')
            else:
                flash('Error sending email. Please try again later.', 'error')

            return redirect(url_for('login'))

        else:
            flash('Username and email do not match or account not found!', 'error')

    return render_template("forgot_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password_token(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired reset token!', 'error')
        return redirect(url_for('login'))

    if request.method == "POST":
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template("reset_password.html")

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template("reset_password.html")

        reset_password(email, password)
        flash('Password reset successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template("reset_password.html")


@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route("/upload", methods=["POST"])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if "video" not in request.files:
        return redirect(url_for("index"))

    video = request.files["video"]

    if not video.filename.endswith(('.mp4', '.avi', '.mov')):
        return "Unsupported file type", 400

    upload_folder = os.path.join(app.instance_path, 'uploads')
    input_path = os.path.join(upload_folder, secure_filename(video.filename))
    output_path = os.path.join(upload_folder, "summary_" + secure_filename(video.filename))

    try:
        video.save(input_path)
        summarize_video(input_path, output_path)
    except Exception as e:
        # Clean up on error as well
        if os.path.exists(input_path):
            os.remove(input_path)
        return str(e), 500

    @after_this_request
    def cleanup(response):
        """Clean up the files after the request is complete."""
        try:
            os.remove(input_path)
            os.remove(output_path)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle: %s", error)
        return response

    return send_file(output_path, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))