import os
import cv2
import numpy as np
import uuid
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image


# utils.py
# Utility functions for malaria detection application

import os
import uuid
import cv2
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import load_model # type: ignore
import time
import shutil
import glob
from datetime import datetime

import numpy as np
import cv2
import tensorflow as tf

def generate_gradcam(model, img_path, output_path="static/gradcam.jpg"):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (224, 224))
    img_array = np.expand_dims(img, axis=0) / 255.0

    grad_model = tf.keras.models.Model(
        [model.inputs], 
        [model.get_layer("conv2d_3").output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array)
        loss = predictions[0]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = np.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-10)
    heatmap = cv2.resize(heatmap.numpy(), (224, 224))
    heatmap = np.uint8(255 * heatmap)

    heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    superimposed_img = cv2.addWeighted(img, 0.6, heatmap_color, 0.4, 0)

    cv2.imwrite(output_path, superimposed_img)
    return output_path



def is_valid_cell_image(image_path):
    import cv2

    img = cv2.imread(image_path)
    if img is None:
        return False

    # ✅ Relaxed dimension check
    h, w = img.shape[:2]
    if h < 40 or w < 40:
        return False

    # Convert to grayscale and blur
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)

    # Hough Circle detection (relax parameters)
    circles = cv2.HoughCircles(
        blur, cv2.HOUGH_GRADIENT, dp=1, minDist=10,
        param1=30, param2=20, minRadius=5, maxRadius=70
    )

    # 🧪 Debug Print (optional)
    # print(f"Circle detection: {circles}")

    return circles is not None and len(circles[0]) > 0



import os
import cv2
import numpy as np
from tensorflow.keras.preprocessing import image

def predict_image(model, image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0

    prediction = model.predict(img_array)[0]  # shape (3,)
    class_idx = np.argmax(prediction)
    confidence = float(np.max(prediction))
    # Make sure this order matches your train_gen.class_indices!
    class_labels = ['NotCell','Parasitized', 'Uninfected']
    predicted_label = class_labels[class_idx]

    print("Prediction Scores:", prediction)
    print("Classified as:", predicted_label)
    print("Confidence:", confidence)

    return predicted_label, confidence

def preprocess_image(image_path, target_size=(224,224)):
    img = cv2.imread(image_path)
    if img is None:
        raise Exception("Cannot read image.")
    img = cv2.resize(img, target_size)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0
    return np.expand_dims(img, axis=0)

def load_trained_model(model_path="model/malaria_model.keras"):
    import tensorflow as tf
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")
    return tf.keras.models.load_model(model_path)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def save_uploaded_file(file):
    import uuid
    upload_folder = "static/uploads"
    os.makedirs(upload_folder, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(upload_folder, filename)
    file.save(path)
    return path

def cleanup_old_files(folder="static/uploads", max_files=50):
    files = sorted([os.path.join(folder, f) for f in os.listdir(folder)], key=os.path.getmtime)
    for file in files[:-max_files]:
        try:
            os.remove(file)
        except:
            continue



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_feedback_email(name, clinic, message):
    sender = "your_email@example.com"
    receiver = "admin@example.com"
    password = "your_app_password"

    subject = "📝 New Feedback from Clinic"
    html_body = f"""
    <h2>Clinic Feedback Received</h2>
    <p><b>Name:</b> {name}</p>
    <p><b>Clinic:</b> {clinic}</p>
    <p><b>Message:</b> {message}</p>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
