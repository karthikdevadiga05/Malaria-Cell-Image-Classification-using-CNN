# 🩸 Malaria Detection & Analytics Web Application

A full-stack Flask application that uses a custom-trained CNN model to detect malaria from blood smear images and provides rich analytics, report generation, feedback management, diary logging, and an admin dashboard. The system runs on localhost and stores data in a local SQLite database (`users.db`).

---

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Training the Model](#training-the-model)
- [Running the Web Application](#running-the-web-application)
- [Main Functional Flows](#main-functional-flows)
- [Analytics API](#analytics-api)
- [Grad-CAM & Explainability](#grad-cam--explainability)
- [Security & Privacy Notes](#security--privacy-notes)
- [Known Limitations & Future Enhancements](#known-limitations--future-enhancements)

---

## ✨ Features

### 🧠 AI-based Malaria Detection
- Custom CNN trained on microscope cell images using Keras/TensorFlow
- Multi-class output internally (NotCell / Parasitized / Uninfected), with NotCell used for input validation
- Confidence-based rejection of low-quality predictions

### 👨‍⚕️ Doctor Portal
- Registration, login, and profile management
- Upload patient blood smear images and view detailed prediction results
- Patient-wise prediction history and searchable reports
- Diary module for recording clinical notes

### 📊 Analytics & Dashboards
- Per-user analytics API providing:
  - Overall counts (total / positive / negative)
  - Weekly and monthly trends
  - Demographic breakdowns (age groups and gender)
- Admin dashboard with users, predictions, contact messages, feedbacks, and counts
- Separate admin analytics dashboard (`analytics_dashboard.html`)

### 📄 Report Generation
- Downloadable PDF diagnostic reports for each prediction
- Includes hospital name, patient details, diagnosis, confidence, and analyzed blood cell image
- Personalized header with clinic logo/profile picture and disclaimer

### ✉️ Feedback & Contact
- Contact page for clinics to send feedback
- Feedback stored locally in `feedbacks.csv`
- Automatic email notifications to the project email
- Admin reply to contact messages via email from dashboard

### 📓 Diary Module
- Diary blueprint (`diary_bp`) for storing notes per user in `users.db`
- Simple UI page for adding and viewing diary entries

### 🧪 Model Training Utilities
- Dataset splitting, augmentation, and generators (`preprocess.py`)
- Training pipeline with callbacks, class-weighting, confusion matrix, and plots (`train_model.py`)
- Grad-CAM heatmap generation for model explainability (`utils.py`)

---

## 📁 Project Structure

```
PROJECTFINAL/
├── app.py                       # Main Flask app, routes, admin & user logic
├── preprocess.py                # Directory creation, dataset split, data generators, visualization
├── train_model.py               # CNN model definition, training, evaluation & plots
├── utils.py                     # Prediction, preprocessing, Grad-CAM, helpers, email utils
├── diary.py                     # Diary blueprint: routes for diary entries
├── requirements.txt             # Python dependencies
├── model_summary.txt            # Keras model summary text
├── malaria_model.keras          # (Sometimes placed here; main model in /model)
├── users.db                     # Main SQLite DB: users, predictions, diary, contact_messages, etc.
├── feedbacks.csv                # Stored clinic feedback messages
├── templatesbackup.zip          # Backup of templates
├── .gitignore                   # Git ignore rules
├── venv/                        # Virtual environment (ignored in Git)
│
├── dataset/
│   ├── cell_images/             # Raw dataset (NotCell, Parasitized, Uninfected)
│   └── processed/               # train / val / test directories (created by split_dataset)
│
├── docs/
│   └── project_documentation.md # Detailed documentation in markdown
│
├── logs/                        # Optional logs directory
│
├── model/
│   └── malaria_model.keras      # Trained CNN model saved by ModelCheckpoint
│
├── static/
│   ├── css/
│   │   ├── style.css            # Main styling for app pages
│   │   └── login-style.css      # Auth & landing styling
│   │
│   ├── js/
│   │   ├── script.js            # General front-end logic & dashboard scripts
│   │   └── feedback.js          # Contact/feedback-related JS
│   │
│   ├── images/                  # UI images, icons, logos
│   │
│   ├── lottie/                  # Lottie JSON animations
│   │   ├── ai-diagnosis.json
│   │   ├── brain.json
│   │   ├── hospital_animation.json
│   │   ├── report.json
│   │   ├── robot.json
│   │   ├── signup.json
│   │   ├── stats.json
│   │   └── upload.json
│   │
│   ├── profile_pics/            # Uploaded doctor profile pictures
│   ├── uploads/                 # Uploaded smear images + default logo
│   ├── reports/                 # Generated PDF reports
│   │
│   ├── accuracy_graph.png       # Training accuracy graph (if saved)
│   ├── training_curves.png      # Accuracy & loss vs epochs
│   └── sample_images.png        # Sample images visualization
│
└── templates/
    ├── landing.html             # Landing / intro page
    ├── index.html               # Main logged-in dashboard + prediction form/about section
    ├── login.html               # User login page
    ├── register.html            # User registration
    ├── profile.html             # Doctor profile page
    ├── result.html              # Prediction result view
    ├── reports.html             # User reports list & search/filter
    ├── diary.html               # Diary UI
    ├── contact.html             # Feedback/contact form
    ├── feedback_success.html    # Confirmation page after contact submission
    ├── forgot_password.html     # Forgot password form
    ├── password_sent.html       # Reset email sent message
    ├── reset_password.html      # Password reset form
    ├── admin_login.html         # Admin login page
    ├── admin_dashboard.html     # Admin dashboard (users, predictions, feedback, contacts)
    ├── admin_feedbacks.html     # Detailed feedback list
    ├── analytics_dashboard.html # Admin/user analytics view (charts)
    
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- pip
- (Optional) virtual environment tool (`venv` or `virtualenv`)

### Clone & Create Virtual Environment

```bash
cd PROJECTFINAL
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dataset Preparation

1. Download the malaria cell image dataset from kaggle (https://www.kaggle.com/datasets/iarunava/cell-images-for-detecting-malaria/data) and place folders under:

```
dataset/cell_images/
    ├── Parasitized/
    ├── Uninfected/
    └── NotCell/      # Optional third class used for validating "not a cell"
```

2. Run dataset preprocessing (splitting and visualization):

```bash
python preprocess.py
```

This will:
- Create basic directory structure (`static/uploads`, `model`, `dataset/processed`)
- Split `cell_images` into `dataset/processed/train`, `val`, `test`
- Create data generators and save sample visualization to `static/sample_images.png`

---

## 🧠 Training the Model

The training pipeline is defined in `train_model.py`.

### Model Architecture

- **Input:** 224 × 224 × 3
- Conv2D(32) → MaxPooling2D → BatchNormalization
- Conv2D(64) → MaxPooling2D → BatchNormalization
- Conv2D(128) → MaxPooling2D → BatchNormalization
- Conv2D(256) → MaxPooling2D → BatchNormalization
- Flatten
- Dense(128, ReLU) → Dropout(0.4)
- Dense(3, softmax) – classes: `NotCell`, `Parasitized`, `Uninfected`

**Compiled with:**
- Optimizer: `Adam(learning_rate=0.0001)`
- Loss: `categorical_crossentropy`
- Metrics: `accuracy`

### Training Script

```bash
python train_model.py
```

The script will:
- Use `create_data_generators()` to load augmented training and plain val/test sets
- Compute balanced `class_weight` to handle class imbalance
- Train for up to 30 epochs with:
  - `EarlyStopping` (patience 10)
  - `ModelCheckpoint` saving best model to `model/malaria_model.keras`
  - `ReduceLROnPlateau` on val_loss
- Evaluate on validation and test sets
- Save:
  - Training curves → `static/training_curves.png`
  - Confusion matrix → `static/confusion_matrix.png`
  - Model summary → `model_summary.txt`

---

## 🌐 Running the Web Application

### Ensure Model & Database Exist

- A trained model should be present at `model/malaria_model.keras` (from the training step)
- A SQLite DB `users.db` should exist with tables such as:
  - `users` (id, username, full_name, email, phone, hospital, specialization, password, reset_token, ...)
  - `predictions` (id, patient_name, patient_id, phone, age, sex, is_infected, confidence, image_path, predicted_on, username, ...)
  - `contact_messages` (id, name, email, subject, message, reply, created_at, replied_at, ...)
  - `diary` (id, username, title, content, created_at, ...)
  - `payments` (optional, for admin payments view)

If not yet created, these tables can be created using an initialization script or manually from SQLite.

### Configure Email Credentials

`app.py` and `utils.py` use Gmail SMTP:

```python
app.config['MAIL_USERNAME'] = 'malariadetect@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

smtp_username = 'malariadetect@gmail.com'
smtp_password = 'your_app_password'
```

Replace with your own email and app password before running in real use.

### Run the App

```bash
python app.py
```

By default, the app runs in debug mode on:

```
http://127.0.0.1:5000
```

---

## 🔄 Main Functional Flows

### User Registration & Login

#### Register (`/register`)
- Collects: username, full name, email, phone, hospital, specialization, password
- Checks if username exists; inserts into `users` table on success

#### Login (`/login`)
- Allows login using username or email plus password
- On success sets:
  - `session['username']`
  - `session['hospital']`
- Redirects to `/`

#### Logout (`/logout`)
- Clears session and redirects to `/landing`

#### Forgot / Reset Password
- `/forgot_password` generates `reset_token`, sends email with reset link
- `/reset_password/<token>` updates password if token is valid

### Prediction Flow

**Route:** `/predict` (POST)

1. Requires logged-in user
2. Receives:
   - Uploaded smear image (`file`)
   - Patient details: name, ID, age, sex, phone
3. Saves the image under `static/uploads/`
4. Resizes to 224 × 224 and re-saves
5. Calls `predict_image(model, img_path)`:
   - Model outputs probabilities for three classes
   - Highest probability chosen as label; confidence extracted
6. If label is `NotCell`:
   - Image deleted
   - Flash message asking to upload a valid microscope slide
7. If `confidence < 0.7`:
   - Image deleted
   - Flash message for low confidence
8. Otherwise:
   - `is_infected = (predicted_label == 'Parasitized')`
   - Inserts a row into `predictions` table in `users.db`
   - Renders `result.html` with diagnosis, confidence, patient details, and image path

### Reports & PDF Download

#### Reports (`/reports`)
- Lists predictions for logged-in `username`
- Supports search by `patient_id` and `patient_name`, and sort by date
- Decodes `confidence` and `is_infected` from DB even if stored as bytes

#### Download Report (`/download_report`)
- Accepts `report_id` (prediction id)
- Fetches prediction + hospital name
- Chooses doctor's profile picture as header logo if present; else default hospital logo
- Generates a styled PDF including:
  - Header with hospital name and logo
  - Patient details
  - Diagnosis and confidence
  - Embedded blood cell image
  - Footer with disclaimer and contact
- Saves under `static/reports/` and sends as file download

### Diary Module

- `diary_bp` blueprint from `diary.py` handles:
  - Creation and viewing of diary entries
  - Data stored in `diary` table in `users.db`
- The UI is rendered via `diary.html`

### Contact & Feedback

#### Contact Page (`/contact`)
- Requires login
- Pre-fills hospital name from `users` table
- On POST:
  - Reads `lab_head`, `message`, and user email
  - Appends row to `feedbacks.csv` → `[clinic, lab_head, email, message]`
  - Sends email to project email using `send_feedback_email`
  - Shows `feedback_success.html`

#### AJAX Contact API (`/contact_submit`)
- JSON endpoint to insert `contact_messages` into DB

### Admin Module

#### Admin Login (`/admin`)
- Hard-coded credentials:
  - `ADMIN_USERNAME = "admin"`
  - `ADMIN_PASSWORD = "05NOV@2004"`
- On success sets `session['admin'] = True` and redirects to `/admin/dashboard`

#### Admin Dashboard (`/admin/dashboard`)
Shows:
- All users
- All predictions
- All `contact_messages` ordered by `created_at`
- Total number of predictions
- Feedbacks loaded from `feedbacks.csv`

#### Admin Feedbacks (`/admin-feedbacks`)
- Displays feedbacks from `feedbacks.csv`

#### Admin Payments (`/admin/payments`)
- Lists `payments` entries with `status='pending'` and `status='paid'`, if table exists

#### Reply to Contact (`/admin/reply_contact`)
- Admin selects a contact message and submits a reply
- The reply is:
  - Stored back into `contact_messages` (`reply`, `replied_at` fields)
  - Sent to the user's email using `send_reply_email()` (SMTP via Gmail)

#### Delete User (`/delete-user/<int:user_id>`)
- Deletes the selected user record from `users` table
- Returns to the admin dashboard

#### Delete Feedback (`/delete-feedback`)
- Reads `email` and `message` from form
- Rewrites `feedbacks.csv` excluding the matching row
- Shows success flash message and redirects to admin dashboard

#### Admin Analytics (`/admin/analytics`)
- Renders `analytics_dashboard.html` for advanced charts
- Access controlled by `is_admin()` check (you can later extend this to a real admin role or flag)

---

## 📊 Analytics API

The analytics backend is implemented using helper functions and returned as JSON for charts on the dashboard.

### Endpoints

#### Dashboard Statistics API (`/api/dashboard/stats`)
- Requires logged-in user
- Optional query parameters: `start_date`, `end_date` (ISO date strings)
- Returns JSON with:
  - `overall`: total / positive / negative and percentages
  - `weekly`: data per week (`YYYY-Www`) with counts and percentages
  - `monthly`: data per month (`YYYY-MM`) with counts and percentages
  - `demographics`: age-group and gender-wise distribution

#### Debug DB Check (`/api/debug/db_check`)
- Restricted to admin (`is_admin` check)
- Returns:
  - Whether `predictions` table exists
  - Column info from `PRAGMA table_info`
  - A few sample rows with decoded `is_infected`
  - Record count and date range
- Useful for debugging DB schema issues

### Helper Functions

Defined in `app.py`:

- `get_overall_stats(cursor, username, start_date=None, end_date=None)`
- `get_weekly_data(cursor, username, start_date=None, end_date=None)`
- `get_monthly_data(cursor, username, start_date=None, end_date=None)`
- `get_demographic_data(cursor, username, start_date=None, end_date=None)`

These functions run SQL aggregation queries on the `predictions` table and compute counts and percentages for charting.

---

## 🔍 Grad-CAM & Explainability

`generate_gradcam(model, img_path, output_path="static/gradcam.jpg")` in `utils.py`:

- Loads an image, resizes and normalizes it
- Builds a Grad-CAM model using the last convolutional layer (`conv2d_3`)
- Computes gradients of the predicted class wrt feature maps
- Generates a colored heatmap superimposed on the original image
- Saves result at `static/gradcam.jpg`

This can be integrated into the result page to visually show which region the model focused on for its decision.

---

## 🔒 Security & Privacy Notes

- Application currently runs on **localhost** for demonstration and academic purposes
- Authentication is via username/password stored in `users.db`
- Passwords are currently stored as plain text in the code; for production, they **must** be hashed (e.g., using `werkzeug.security`)
- Image handling:
  - Uploaded microscope images are stored under `static/uploads/`
  - They are used for prediction, reports, and possibly Grad-CAM
- Admin credentials are hard-coded; for real deployment you should:
  - Move credentials and email passwords to environment variables
  - Enforce stronger authentication and role management
- PDF reports clearly mention that the diagnosis is AI-generated and should not be used as a sole clinical decision

---

## ⚠️ Known Limitations & Future Enhancements

### Current Limitations

- Passwords are not hashed; reset links are sent without expiry mechanism
- Admin check `is_admin(username)` is currently a placeholder and should be tightened
- No automatic cleanup job for old uploads/reports (you can reuse `cleanup_old_files` logic from `utils.py`)
- System is not yet containerized or deployed on a cloud platform
- No unit tests or CI pipeline configured

### Possible Future Improvements

- Hash passwords and use Flask-Login or JWT for authentication
- Add role field (`is_admin`) in `users` table instead of hard-coded admin credentials
- Implement periodic cleanup for `static/uploads` and `static/reports`
- Containerize with Docker and deploy on a cloud provider
- Add more extensive model evaluation, cross-validation, and versioning

---

## 👨‍💻 Author

**Karthik R Sherigara**  
BCA Final Year Project - 2025

This project was developed as a final year academic project for Bachelor of Computer Applications (BCA) degree program, completed in June 2025.

---

## 📝 License

This project is tailored for academic and demonstration purposes.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📧 Contact

For questions or feedback, contact: malariadetect@gmail.com

**Project Author:** Karthik R Sherigara

---

## 🙏 Acknowledgments

- NIH Malaria Dataset for training data
- Academic mentors and guides for support and guidance

---

**Made with ❤️ for improving malaria detection and healthcare diagnostics**
