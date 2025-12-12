from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import cv2
import os
import sqlite3
import numpy as np
from utils import  predict_image, load_trained_model
from flask_mail import Mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
from werkzeug.utils import secure_filename
from fpdf import FPDF
from diary import diary_bp
from utils import generate_gradcam



app = Flask(__name__)
# Mail configuration (Use your Gmail/SMTP settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'malariadetect@gmail.com'     
app.config['MAIL_PASSWORD'] = 'xhfobpmnpxkohrcl'        
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.register_blueprint(diary_bp)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "05NOV@2004"

mail = Mail(app)

app.secret_key = 'f4e317dec2d14e9fb948a54336c99725'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
model = load_trained_model()
   
@app.route('/landing')
def landing():
    return render_template('landing.html')


@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('landing'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
    user = c.fetchone()
    conn.close()

    return render_template('index.html', user=user)


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials", "danger")

    return render_template("admin_login.html")


import csv
import os
import os
import csv
from datetime import date
import sqlite3
from flask import session, redirect, url_for, render_template

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    users = cursor.execute("SELECT * FROM users").fetchall()
    predictions = cursor.execute("SELECT * FROM predictions").fetchall()
    contact_messages = cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC").fetchall()
    total_images = cursor.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    conn.close()

    # Load feedbacks from CSV
    feedbacks = []
    if os.path.exists("feedbacks.csv"):
        with open("feedbacks.csv", newline='') as file:
            reader = csv.reader(file)
            feedbacks = list(reader)

    return render_template(
        'admin_dashboard.html',
        users=users,
        predictions=predictions,
        feedbacks=feedbacks,
        contact_messages=contact_messages,
        total_images=total_images
    )


from datetime import datetime
from flask import request, redirect, url_for
import sqlite3
from flask import request, redirect, url_for, session
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

@app.route('/admin/reply_contact', methods=['POST'])
def admin_reply_contact():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    msg_id = request.form['msg_id']
    reply = request.form['reply']
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Get user's email and subject
    cursor.execute("SELECT email, subject FROM contact_messages WHERE id=?", (msg_id,))
    row = cursor.fetchone()
    user_email = row['email']
    subject = row['subject']
    # Update the reply in the database
    cursor.execute(
        "UPDATE contact_messages SET reply=?, replied_at=? WHERE id=?",
        (reply, datetime.now(), msg_id)
    )
    conn.commit()
    conn.close()

    # --- SEND EMAIL TO USER ---
    try:
        send_reply_email(user_email, subject, reply)
    except Exception as e:
        print("Failed to send email:", e)

    return redirect(url_for('admin_dashboard'))


def send_reply_email(to_email, subject, reply_message):
    # SMTP server settings 
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'malariadetect@gmail.com'       
    smtp_password = 'xhfobpmnpxkohrcl'  
    from_email = smtp_username
    to_email = to_email
    subject = f"Re: {subject} (Malaria Detection Support)"
    body = f"Hello,\n\n{reply_message}\n\nBest regards,\nMalaria Detection Team"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    # Send the email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail(from_email, [to_email], msg.as_string())
    server.quit()


def send_email(to_email, subject, message):
    sender_email = "malariadetect@gmail.com"
    app_password = "xhfobpmnpxkohrcl"  # 16-digit password from Gmail

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Email failed: {e}")

def send_feedback_email(clinic_name, lab_head, sender_email, message):
    content = f"""
📥 New Feedback Received

🏥 Clinic/Lab: {clinic_name}
👤 Contact Person: {lab_head}
📧 Submitted by: {sender_email}

📝 Message:
{message}
    """

    send_email("malariadetect@gmail.com", "New Clinic Feedback Submitted", content)

from PIL import Image
import imghdr
from utils import predict_image
import os
import cv2
from flask import flash, redirect, url_for, render_template, session
from utils import predict_image
import os
import cv2
from flask import flash, redirect, url_for, render_template, session
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime

@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    image_file = request.files['file']
    patient_name = request.form.get('patient_name', 'Anonymous')
    patient_id = request.form.get('patient_id', 'N/A')
    age = request.form.get('age', 'N/A')
    sex = request.form.get('sex', 'N/A')
    phone = request.form.get('phone', 'N/A')

    filename = secure_filename(image_file.filename)
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(img_path)

    try:
        img = cv2.imread(img_path)
        if img is None:
            raise Exception("Failed to read image file")

        img = cv2.resize(img, (224, 224))
        cv2.imwrite(img_path, img)

        predicted_label, confidence = predict_image(model, img_path)

        # Reject if image is not a blood cell
        if predicted_label == 'NotCell':
            os.remove(img_path)
            flash("The uploaded image is not a valid blood cell image. Please upload a clear microscope slide image.", "error")
            return redirect(url_for('index'))

        is_infected = (predicted_label == 'Parasitized')

        # Optional: confidence threshold to reject low-confidence predictions
        if confidence < 0.7:
            os.remove(img_path)
            flash("Low confidence in result. Please upload a better image.", "error")
            return redirect(url_for('index'))

    except Exception as e:
        flash("Prediction failed: " + str(e), "error")
        return redirect(url_for('index'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO predictions (patient_name, patient_id, phone, age, sex, is_infected, confidence, image_path, predicted_on, username)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (patient_name, patient_id, phone, age, sex, is_infected, confidence, img_path, datetime.now(), username))

    conn.commit()
    conn.close()

    return render_template('result.html', result={
        'is_infected': is_infected,
        'confidence': confidence,
        'image_path': img_path,
        'patient_name': patient_name,
        'patient_id': patient_id,
        'patient_phone': phone,
        'patient_sex': sex,
        'patient_age': age
    })


@app.route('/admin/payments')
def admin_payments():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    pending = cursor.execute("SELECT * FROM payments WHERE status='pending' ORDER BY created_at DESC").fetchall()
    paid = cursor.execute("SELECT * FROM payments WHERE status='paid' ORDER BY paid_at DESC").fetchall()
    conn.close()
    return render_template('admin_payments.html', pending=pending, paid=paid)

from datetime import datetime


@app.route('/delete-user/<int:user_id>', methods=["POST"])
def delete_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    #flash("User deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/delete-feedback', methods=["POST"])
def delete_feedback():
    email = request.form["email"]
    message = request.form["message"]
    
    rows = []
    with open("feedbacks.csv", newline='') as infile:
        rows = [row for row in csv.reader(infile) if not (row[2] == email and row[3] == message)]
    with open("feedbacks.csv", "w", newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)

    flash("Feedback deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/reports')
def reports():
    search_id = request.args.get('search_id', '').strip()
    search_name = request.args.get('search_name', '').strip()  
    sort_order = request.args.get('sort', 'desc')  

    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT * FROM predictions WHERE username = ?"
    params = [session['username']]

    if search_id:
        query += " AND patient_id LIKE ?"
        params.append(f"%{search_id}%")

    if search_name:
        query += " AND LOWER(patient_name) LIKE ?"
        params.append(f"%{search_name.lower()}%")

    query += f" ORDER BY predicted_on {'ASC' if sort_order == 'asc' else 'DESC'}"
    cursor.execute(query, tuple(params))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        # Decode confidence
        raw_conf = row['confidence']
        if isinstance(raw_conf, bytes):
            try:
                confidence = float(np.frombuffer(raw_conf, dtype=np.float32)[0])
            except:
                confidence = 0.0
        else:
            confidence = float(raw_conf)

        # ✅ Decode is_infected properly
        raw_infected = row['is_infected']
        if isinstance(raw_infected, bytes):
            raw_infected = raw_infected[0]  # b'\x01' → 1

        is_infected = bool(raw_infected)

        results.append({
            'id': row['id'],
            'patient_name': row['patient_name'],
            'patient_id': row['patient_id'],  
            'patient_age': row['age'],
            'is_infected': is_infected,
            'confidence': confidence,
            'predicted_on': row['predicted_on'],
            'image_path': row['image_path']
        })

    # Pass search_name and search_id back to template so fields stay filled
    return render_template(
        "reports.html",
        results=results,
        request=request  # so you can use request.args.get in template
    )


@app.route("/admin-feedbacks")
def admin_feedbacks():
    feedbacks = []
    if os.path.exists("feedbacks.csv"):
        with open("feedbacks.csv", newline='') as file:
            reader = csv.reader(file)
            feedbacks = list(reader)
    return render_template("admin_feedbacks.html", feedbacks=feedbacks)


@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
    user = c.fetchone()
    conn.close()

    return render_template('index.html', show_about=True, user=user)

@app.route('/contact', methods=["GET", "POST"])
def contact():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Fetch user from DB
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
    user = c.fetchone()
    conn.close()

    if not user:
        return redirect(url_for('login'))

    hospital_name = user['hospital']  #Fetch hospital name from database

    if request.method == "POST":
        clinic = hospital_name
        lab_head = request.form.get("lab_head")
        message = request.form.get("message")
        user_email = user['email']

        # Save feedback locally
        with open("feedbacks.csv", "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow([clinic, lab_head, user_email, message])

        # Send feedback email
        send_feedback_email(clinic, lab_head, user_email, message)

        return render_template("feedback_success.html")

    return render_template("contact.html", user=user, hospital_name=hospital_name)


import os
from flask import request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'username' not in session:
        flash('Please log in.', 'danger')
        return redirect(url_for('login'))
    file = request.files.get('profile_pic')
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{session['username']}.{ext}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('Profile picture updated!', 'success')
        session['profile_pic'] = filename
    else:
        flash('Invalid file type.', 'danger')
    return redirect(url_for('profile'))


from flask import request, jsonify, session, flash, redirect, render_template

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?", (username, username ,password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['hospital'] = user[5]

            return redirect('/')
        else:
            flash('Invalid username or password.', 'danger')
            return redirect('/login')

    return render_template('login.html')


import secrets
from flask import url_for

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND email = ?", (username, email))
        user = c.fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            c.execute("UPDATE users SET reset_token = ? WHERE username = ?", (token, username))
            conn.commit()
            conn.close()

            reset_link = url_for('reset_password', token=token, _external=True)

            message = f"""
            Hello {username},

            Click the link below to reset your password:
            {reset_link}

            If you did not request this, ignore this email.

            - Malaria Detection Support Team
            """

            send_email(email, "Reset Your Password", message)
            return render_template('password_sent.html')

        else:
            flash('Username and email do not match.', 'error')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')



@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('password')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE reset_token = ?", (token,))
        user = c.fetchone()

        if user:
            c.execute("UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?", (new_password, token))
            conn.commit()
            conn.close()
            flash('Password reset successfully. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired reset link.', 'error')
            return redirect(url_for('forgot_password'))

    return render_template('reset_password.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        hospital = request.form['hospital']
        specialization = request.form['specialization']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if user:
            flash('Username already exists. Try another one.', 'danger')
            return redirect('/register')

        c.execute('''INSERT INTO users (username, full_name, email, phone, hospital, specialization, password)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (username, full_name, email, phone, hospital, specialization, password))
        conn.commit()
        conn.close()

        flash('Registration successful! Please login.', 'success')
        return redirect('/login')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/landing')


from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
from flask import send_file
import os
from io import BytesIO

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/contact_submit', methods=['POST'])
def contact_submit():
    data = request.get_json()
    name = data.get('name', '')
    email = data.get('email', '')
    message = data.get('message', '')
    subject = data.get('subject', 'General')
    if not (name and email and message):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    db = get_db()
    db.execute(
        'INSERT INTO contact_messages (name, email, subject, message) VALUES (?, ?, ?, ?)',
        (name, email, subject, message)
    )
    db.commit()
    db.close()
    return jsonify({'status': 'success'})




from flask import request, session, send_file
import sqlite3
import os
from fpdf import FPDF
from flask import request, session, send_file
import sqlite3
import os
from fpdf import FPDF

@app.route('/download_report', methods=['POST'])
def download_report():
    report_id = request.form['report_id']

    # Fetch prediction record
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return "Report not found", 404

    # Fetch hospital name from users table using logged-in username
    username = session.get('username')
    cursor.execute("SELECT hospital FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    conn.close()
    hospital_name = user_row['hospital'] if user_row and user_row['hospital'] else "HealthCare Clinic"

    # Find the logo: try jpg, png, jpeg
    logo_extensions = ['jpg', 'png', 'jpeg']
    logo_path = None
    for ext in logo_extensions:
        candidate = os.path.join(app.root_path, 'static', 'uploads', f'{username}.{ext}')
        if os.path.exists(candidate):
            logo_path = candidate
            break
    if not logo_path:
        logo_path = os.path.join(app.root_path, 'static', 'uploads', 'hospital_logo.jpg')

    # Blood cell image path (filename stored in DB)
    image_path = os.path.join(app.root_path, 'static', 'uploads', row['image_path'])

    # Decode values
    confidence = float(row['confidence']) if not isinstance(row['confidence'], bytes) else float(np.frombuffer(row['confidence'], dtype=np.float32)[0])
    is_infected = row['is_infected']
    if isinstance(is_infected, bytes):
        is_infected = bool(is_infected[0])

    # --- PDF Generation ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False, margin=18)

    # Draw a colored rectangle for header background
    pdf.set_fill_color(44, 76, 71)  # Dark green
    pdf.rect(0, 0, 210, 38, 'F')

    # Logo (left)
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=12, y=8, w=22, h=22)

    # Hospital name (centered)
    pdf.set_xy(38, 12)
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(134, 10, hospital_name, align='C', ln=2)
    # Report title (centered)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(134, 8, "Malaria Detection Report", align='C', ln=2)
    pdf.set_text_color(0, 0, 0)  # Reset color

    # Thin line under header
    pdf.set_line_width(0.7)
    pdf.set_draw_color(15, 144, 201)
    pdf.line(12, 38, 198, 38)
    pdf.ln(18)

    # --- Patient Details Section ---
    pdf.set_xy(14, 46)
    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(230, 240, 250)
    pdf.cell(0, 10, "Patient Details", ln=True, fill=True, align='L')
    pdf.set_font("Arial", '', 11)
    details = [
        ("Patient Name", str(row['patient_name'])),
        ("Patient ID", str(row['patient_id'])),
        ("Phone", str(row['phone'])),
        ("Sex", str(row['sex'])),
        ("Age", str(row['age'])),
        ("Date", str(row['predicted_on'])),
    ]
    for field, value in details:
        pdf.set_x(18)
        pdf.cell(38, 9, field, border=0, align='L')
        pdf.cell(0, 9, value, border=0, align='L')
        pdf.ln(8)
    pdf.ln(2)

    # --- Diagnosis Section ---
    diagnosis = "Infected with Malaria Parasite" if is_infected else "No Malaria Infection Detected"
    diag_color = (244, 67, 54) if is_infected else (56, 142, 60)
    diag_bg = (255, 235, 238) if is_infected else (232, 245, 233)

    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(*diag_bg)
    pdf.set_text_color(*diag_color)
    pdf.set_x(14)
    pdf.cell(0, 12, f"Diagnosis: {diagnosis}", ln=True, fill=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    pdf.set_x(18)
    pdf.cell(38, 9, "Confidence", border=0, align='L')
    pdf.cell(0, 9, f"{round(confidence * 100, 2)}%", border=0, align='L')
    pdf.ln(14)

    # --- Blood Cell Image Section ---
    if os.path.exists(image_path):
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(230, 240, 250)
        pdf.set_x(14)
        pdf.cell(0, 10, "Analyzed Blood Cell Image", ln=True, fill=True, align='L')
        img_w = 70
        img_h = 50
        img_x = 18
        img_y = pdf.get_y() + 4
        pdf.set_xy(img_x, img_y)
        pdf.image(image_path, x=img_x, y=img_y, w=img_w, h=img_h)
        pdf.ln(img_h + 10)

    # --- Doctor, Signature, Footer ---
    pdf.set_font("Arial", '', 11)
    pdf.ln(2)
    pdf.set_x(18)
    pdf.cell(0, 8, "Diagnosed by: Dr. Anil Kumar, MD (Pathology)", ln=True)
    pdf.set_x(18)
    pdf.cell(0, 8, "Department of AI Diagnostics", ln=True)
    pdf.ln(8)
    y = pdf.get_y()
    pdf.set_draw_color(15, 144, 201)
    pdf.line(150, y, 200, y)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.set_xy(150, y + 2)
    pdf.cell(0, 10, "Authorized Signature", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(-35)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, "This is an AI-generated diagnostic report for assistance purposes only. Please consult a certified medical professional before making any treatment decisions.")
    pdf.cell(0, 10, "Contact: support@nittehealthcare.com | +91-12345-67890", ln=True)

    pdf_path = f"static/reports/report_{report_id}.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)


@app.route('/profile')
def profile():
    if 'username' in session:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
        user = c.fetchone()
        conn.close()
        return render_template('profile.html', user=user)
    return redirect(url_for('login'))

    
@app.route('/history')
def history():
    if 'user_id' not in session:
        flash("Please login to view your history.")
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY timestamp DESC", (session['user_id'],))
    results = cursor.fetchall()
    conn.close()

    return render_template("history.html", results=results)


import sqlite3
import numpy as np
from datetime import datetime
import json

def get_overall_stats(cursor, username, start_date=None, end_date=None):
    query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_infected = 1 THEN 1 ELSE 0 END) as positive,
SUM(CASE WHEN is_infected = 0 THEN 1 ELSE 0 END) as negative

        FROM predictions
        WHERE username = ?
    """
    params = [username]
    if start_date:
        query += " AND date(predicted_on) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(predicted_on) <= date(?)"
        params.append(end_date)

    cursor.execute(query, params)
    result = cursor.fetchone()

    total = result['total'] or 0
    positive = result['positive'] or 0
    negative = result['negative'] or 0

    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_percent": round((positive / total * 100) if total > 0 else 0, 2),
        "negative_percent": round((negative / total * 100) if total > 0 else 0, 2)
    }


def get_weekly_data(cursor, username, start_date=None, end_date=None):
    query = """
        SELECT 
            strftime('%Y-W%W', predicted_on) as week,
            COUNT(*) as total,
            SUM(CASE WHEN is_infected = 1 THEN 1 ELSE 0 END) as positive,
SUM(CASE WHEN is_infected = 0 THEN 1 ELSE 0 END) as negative

        FROM predictions
        WHERE username = ?
    """
    params = [username]
    if start_date:
        query += " AND date(predicted_on) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(predicted_on) <= date(?)"
        params.append(end_date)

    query += " GROUP BY week ORDER BY week"
    cursor.execute(query, params)
    results = cursor.fetchall()

    weekly_data = []
    for row in results:
        total = row['total'] or 0
        positive = row['positive'] or 0
        negative = row['negative'] or 0

        weekly_data.append({
            "week": row['week'],
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_percent": round((positive / total * 100) if total > 0 else 0, 2),
            "negative_percent": round((negative / total * 100) if total > 0 else 0, 2)
        })

    return weekly_data

def get_monthly_data(cursor, username, start_date=None, end_date=None):
    query = """
        SELECT 
            strftime('%Y-%m', predicted_on) as month,
            COUNT(*) as total,
            SUM(CASE WHEN is_infected = 1 THEN 1 ELSE 0 END) as positive,
SUM(CASE WHEN is_infected = 0 THEN 1 ELSE 0 END) as negative

        FROM predictions
        WHERE username = ?
    """
    params = [username]
    if start_date:
        query += " AND date(predicted_on) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(predicted_on) <= date(?)"
        params.append(end_date)

    query += " GROUP BY month ORDER BY month"
    cursor.execute(query, params)
    results = cursor.fetchall()

    monthly_data = []
    for row in results:
        total = row['total'] or 0
        positive = row['positive'] or 0
        negative = row['negative'] or 0

        monthly_data.append({
            "month": row['month'],
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_percent": round((positive / total * 100) if total > 0 else 0, 2),
            "negative_percent": round((negative / total * 100) if total > 0 else 0, 2)
        })

    return monthly_data

def get_demographic_data(cursor, username, start_date=None, end_date=None):
    # Age distribution
    age_query = """
        SELECT 
            CASE 
                WHEN age < 18 THEN '<18'
                WHEN age BETWEEN 18 AND 30 THEN '18-30'
                WHEN age BETWEEN 31 AND 45 THEN '31-45'
                WHEN age BETWEEN 46 AND 60 THEN '46-60'
                ELSE '>60'
            END as age_group,
            COUNT(*) as total,
            SUM(CASE WHEN is_infected = 1 THEN 1 ELSE 0 END) as positive
        FROM predictions
        WHERE username = ? AND age IS NOT NULL AND age != 'N/A'
    """
    age_params = [username]
    if start_date:
        age_query += " AND date(predicted_on) >= date(?)"
        age_params.append(start_date)
    if end_date:
        age_query += " AND date(predicted_on) <= date(?)"
        age_params.append(end_date)

    age_query += " GROUP BY age_group ORDER BY age_group"
    cursor.execute(age_query, age_params)
    age_results = cursor.fetchall()

    age_data = {}
    for row in age_results:
        total = row['total'] or 0
        positive = row['positive'] or 0
        age_data[row['age_group']] = {
            "total": total,
            "positive": positive,
            "positive_percent": round((positive / total * 100) if total > 0 else 0, 2)
        }

    # Gender distribution
    gender_query = """
        SELECT 
            sex as gender,
            COUNT(*) as total,
            SUM(CASE WHEN is_infected = 1 THEN 1 ELSE 0 END) as positive
        FROM predictions
        WHERE username = ? AND sex IS NOT NULL AND sex != 'N/A'
    """
    gender_params = [username]
    if start_date:
        gender_query += " AND date(predicted_on) >= date(?)"
        gender_params.append(start_date)
    if end_date:
        gender_query += " AND date(predicted_on) <= date(?)"
        gender_params.append(end_date)

    gender_query += " GROUP BY gender"
    cursor.execute(gender_query, gender_params)
    gender_results = cursor.fetchall()

    gender_data = {}
    for row in gender_results:
        total = row['total'] or 0
        positive = row['positive'] or 0
        gender_data[row['gender']] = {
            "total": total,
            "positive": positive,
            "positive_percent": round((positive / total * 100) if total > 0 else 0, 2)
        }

    return {
        "age": age_data,
        "gender": gender_data
    }
@app.route('/api/dashboard/stats')
def dashboard_stats():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session['username']
    start_date = request.args.get('start_date', default=None)
    end_date = request.args.get('end_date', default=None)

    try:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        overall_stats = get_overall_stats(cursor, username, start_date, end_date)
        weekly_data = get_weekly_data(cursor, username, start_date, end_date)
        monthly_data = get_monthly_data(cursor, username, start_date, end_date)
        demographic_data = get_demographic_data(cursor, username, start_date, end_date)

        conn.close()

        return jsonify({
            "overall": overall_stats,
            "weekly": weekly_data,
            "monthly": monthly_data,
            "demographics": demographic_data
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    
@app.route('/api/debug/db_check')
def debug_db_check():
    """Diagnostic endpoint to verify database connectivity and schema."""
    if 'username' not in session or not is_admin(session['username']):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if predictions table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            return jsonify({"error": "Predictions table does not exist"}), 500
        
        # Get column info
        cursor.execute("PRAGMA table_info(predictions)")
        columns = [dict(row) for row in cursor.fetchall()]
        
        # Get sample data
        cursor.execute("SELECT * FROM predictions LIMIT 5")
        sample_data = []
        for row in cursor.fetchall():
            sample_row = {}
            for key in row.keys():
                if key == 'is_infected':
                    # Convert binary to readable format
                    sample_row[key] = f"Binary: {row[key]}, Hex: {row[key].hex()}" if row[key] else "NULL"
                else:
                    sample_row[key] = row[key]
            sample_data.append(sample_row)
        
        # Get record count
        cursor.execute("SELECT COUNT(*) as count FROM predictions")
        record_count = cursor.fetchone()['count']
        
        # Get date range
        cursor.execute("""
            SELECT 
                MIN(predicted_on) as min_date,
                MAX(predicted_on) as max_date
            FROM predictions
        """)
        date_range = dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "table_exists": table_exists,
            "columns": columns,
            "sample_data": sample_data,
            "record_count": record_count,
            "date_range": date_range
        })
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

# Add these routes after your existing admin_dashboard route
@app.route('/admin/analytics', endpoint='admin_analytics')
def admin_analytics():
    if 'username' not in session or not is_admin(session['username']):
        flash("Unauthorized access", "error")
        return redirect(url_for('index'))
    
    return render_template('analytics_dashboard.html')

# Add function to check if user is admin
def is_admin(username):
    return username == username

if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    app.run(debug=True)