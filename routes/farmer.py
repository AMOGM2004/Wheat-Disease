from flask import render_template, request, redirect, url_for, session, flash, send_file
from weather_risk import get_weather_data, calculate_risk
from . import farmer_bp
import sqlite3
import os
from werkzeug.utils import secure_filename
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from flask import jsonify, json


from flask import session
 # Debug line

# Load model once
model = tf.keras.models.load_model("wheat_model.h5")
class_names = ["Healthy", "BlackPoint", "LeafBlight", "WheatBlast", "FusariumFootRot"]

def predict_disease(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    prediction = model.predict(img_array)
    class_index = np.argmax(prediction)
    confidence = np.max(prediction)
    
    # Determine stage based on disease type and confidence
    if class_names[class_index] == "Healthy":
        stage = "Healthy"
    elif confidence > 0.7:
        stage = "Early"
    elif confidence > 0.4:
        stage = "Moderate"
    else:
        stage = "Severe"
    
    return class_names[class_index], float(confidence), stage

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def notify_nearby_farmers(disease, latitude, longitude, uploader_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, latitude, longitude FROM users WHERE role='farmer' AND id != ?", (uploader_id,))
    farmers = c.fetchall()
    for farmer in farmers:
        farmer_id, flat, flng = farmer
        if flat and flng and haversine(latitude, longitude, flat, flng) <= 3:
            message = f"⚠️ {disease} detected within 3km of your location!"
            c.execute("INSERT INTO notifications (farmer_id, message, disease, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
                     (farmer_id, message, disease, latitude, longitude))
    conn.commit()
    conn.close()

@farmer_bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('user_role') != 'farmer':
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC", 
              (session['user_id'],))
    predictions = c.fetchall()
    c.execute("SELECT * FROM notifications WHERE farmer_id = ? AND is_read = 0 ORDER BY timestamp DESC", (session['user_id'],))
    notifications = c.fetchall()
    conn.close()
    weather = get_weather_data()
    risk = calculate_risk(weather)
    
    return render_template('farmer/dashboard.html', predictions=predictions, weather=weather, risk=risk, notifications=notifications)

@farmer_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('logged_in') or session.get('user_role') != 'farmer':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        filename = secure_filename(f"{session['user_id']}_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join('static/uploads/', filename)
        db_image_ = f'uploads/{filename}' 
        file.save(filepath)
        
        disease, confidence, stage = predict_disease(filepath)
        
        # Save to database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO predictions (user_id, image_path, disease, confidence, stage) VALUES (?, ?, ?, ?, ?)",
                 (session['user_id'], db_image_, disease, confidence, stage))
        conn.commit()
        conn.close()
            # Save to disease_reports for map
        farmer_name = request.form.get('farmer_name', session.get('user_name', 'Unknown'))
        latitude = float(request.form.get('latitude', 20.5937))
        longitude = float(request.form.get('longitude', 78.9629))

        conn2 = sqlite3.connect('database.db')
        c2 = conn2.cursor()
        c2.execute("INSERT INTO disease_reports (farmer_name, disease_name, latitude, longitude, image_path) VALUES (?, ?, ?, ?, ?)",
                (farmer_name, disease, latitude, longitude, db_image_))
        conn2.commit()
        conn2.close()
        notify_nearby_farmers(disease, latitude, longitude, session['user_id'])
        
        return render_template('farmer/result.html', 
                             disease=disease, 
                             confidence=confidence, 
                             stage=stage,
                             filename=filename,
                             image_path=filepath)
    
    return render_template('farmer/upload.html')

@farmer_bp.route('/disease-info')
def disease_info():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM diseases ORDER BY name")
    diseases = c.fetchall()
    conn.close()
    return render_template('farmer/disease_info.html', diseases=diseases)

@farmer_bp.route('/disease-info/<stage>')
def disease_info_by_stage(stage):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM diseases WHERE stage_category = ? ORDER BY name", (stage,))
    diseases = c.fetchall()
    conn.close()
    return render_template('farmer/disease_info.html', diseases=diseases, selected_stage=stage)

@farmer_bp.route('/download_report')
def download_report():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],))
    predictions = c.fetchall()
    conn.close()
    
    filename = f"report_{session['user_id']}_{datetime.now().timestamp()}.pdf"
    filepath = os.path.join('static/reports/', filename)
    os.makedirs('static/reports/', exist_ok=True)
    
    from utils.pdf_generator import generate_prediction_report
    generate_prediction_report(predictions, session['user_name'], filepath)
    
    return send_file(filepath, as_attachment=True)

@farmer_bp.route('/mark-notifications-read', methods=['POST'])
def mark_notifications_read():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read = 1 WHERE farmer_id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    from flask import jsonify
    return jsonify({'status': 'ok'})


from flask import jsonify, json
@farmer_bp.route('/update-location', methods=['POST'])
def update_location():
    data = request.get_json()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET latitude=?, longitude=? WHERE id=?",
             (data['latitude'], data['longitude'], session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})