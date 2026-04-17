from flask import Flask, render_template, session, redirect, url_for
from routes.chatbot import chatbot_bp  # add this import
from predict import predict_disease

from dotenv import load_dotenv
load_dotenv()
import os
from routes import auth_bp, farmer_bp, admin_bp
import sqlite3

app = Flask(__name__)
from routes.map_routes import map_bp
app.register_blueprint(map_bp)
app.secret_key = 'your-secret-key-here-change-this-in'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SESSION_TYPE'] = 'filesystem'

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(farmer_bp, url_prefix='/farmer')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(chatbot_bp, url_prefix='/farmer')  # add after other blueprints

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  verified BOOLEAN DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN latitude REAL DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN longitude REAL DEFAULT 0")
    except:
        pass
    
    # Predictions table
    c.execute('''CREATE TABLE IF NOT EXISTS predictions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  image_path TEXT,
                  disease TEXT,
                  confidence REAL,
                  stage TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Diseases table
    c.execute('''CREATE TABLE IF NOT EXISTS diseases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  description TEXT,
                  symptoms TEXT,
                  causes TEXT,
                  treatment TEXT,
                  prevention TEXT,
                  stage_category TEXT,
                  images TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Insert default admin if not exists
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        import hashlib
        admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (name, email, password, role, verified) VALUES (?, ?, ?, ?, ?)",
                 ('Admin', 'admin@wheat.com', admin_pass, 'admin', 1))
    
    # Insert sample disease data
    c.execute("SELECT * FROM diseases")
    if not c.fetchone():
        sample_diseases = [
            ('Leaf Blight', 'Fungal disease affecting wheat leaves', 'Brown spots on leaves', 'Fungus', 'Use fungicides', 'Crop rotation', 'Early'),
            ('Black Point', 'Discoloration of wheat kernels', 'Black tips on grains', 'Fungal infection', 'Seed treatment', 'Use clean seeds', 'Moderate'),
            ('Wheat Blast', 'Severe fungal disease', 'White-gray lesions', 'Magnaporthe oryzae', 'Resistant varieties', 'Field sanitation', 'Severe'),
        ]
        c.executemany("INSERT INTO diseases (name, description, symptoms, causes, treatment, prevention, stage_category) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_diseases)

    c.execute('''
    CREATE TABLE IF NOT EXISTS disease_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_name TEXT,
        disease_name TEXT,
        latitude REAL,
        longitude REAL,
        image_path TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            message TEXT,
            disease TEXT,
            latitude REAL,
            longitude REAL,
            is_read INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

@app.route('/')
def home():
    if session.get('logged_in'):
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('farmer.dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/test')
def test():
    return "Flask app is working!"

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # Initialize database
    init_db()
    print("Starting Flask server...")
    app.run(debug=True, port=5000)



@app.route('/predict', methods=['POST'])
def predict():
    file = request.files['image']
    farmer_name = request.form.get('farmer_name', 'Unknown')
    latitude = float(request.form.get('latitude', 18.5204))
    longitude = float(request.form.get('longitude', 73.8567))

    # Save uploaded image
    img_path = os.path.join('static/uploads', file.filename)
    file.save(img_path)

    # Predict and save to database
    disease, confidence = predict_disease(img_path, farmer_name, latitude, longitude)

    return jsonify({
        'disease': disease,
        'confidence': round(float(confidence) * 100, 2)
    })

@farmer_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        farmer_name = request.form.get('farmer_name', 'Unknown')
        latitude = float(request.form.get('latitude', 18.5204))
        longitude = float(request.form.get('longitude', 73.8567))

        if file:
            img_path = os.path.join('static/uploads', file.filename)
            file.save(img_path)

            # Predict and save to DB
            disease, confidence = predict_disease(img_path, farmer_name, latitude, longitude)

            return redirect(url_for('farmer.result', 
                disease=disease, 
                confidence=round(float(confidence)*100, 2)))

    return render_template('farmer/upload.html')