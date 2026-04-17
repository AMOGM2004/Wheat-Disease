from flask import render_template, request, redirect, url_for, session, flash
from . import admin_bp
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import sqlite3

@admin_bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM users WHERE role='farmer'")
    farmers_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM predictions")
    predictions_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM diseases")
    diseases_count = c.fetchone()[0]
    
    # Get most common disease
    c.execute("""SELECT disease, COUNT(*) as count FROM predictions 
                 WHERE disease != 'Healthy' GROUP BY disease ORDER BY count DESC LIMIT 1""")
    most_common = c.fetchone()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         farmers_count=farmers_count,
                         predictions_count=predictions_count,
                         diseases_count=diseases_count,
                         most_common=most_common)

@admin_bp.route('/diseases')
def manage_diseases():
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM diseases ORDER BY created_at DESC")
    diseases = c.fetchall()
    conn.close()
    
    return render_template('admin/diseases.html', diseases=diseases)

@admin_bp.route('/disease/add', methods=['GET', 'POST'])
def add_disease():
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        symptoms = request.form['symptoms']
        causes = request.form['causes']
        treatment = request.form['treatment']
        prevention = request.form['prevention']
        stage_category = request.form['stage_category']
        
        # Handle image uploads
        image_paths = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files[:3]:  # Max 3 images
                if file and file.filename:
                    filename = secure_filename(f"disease_{int(datetime.now().timestamp())}_{file.filename}")
                    filepath = os.path.join('static/disease_images/', filename)
                    file.save(filepath)
                    image_paths.append(f"disease_images/{filename}")
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO diseases 
                        (name, description, symptoms, causes, treatment, prevention, stage_category, images) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (name, description, symptoms, causes, treatment, prevention, stage_category, ','.join(image_paths)))
            conn.commit()
            flash('Disease added successfully')
        except sqlite3.IntegrityError:
            flash('Disease already exists')
        finally:
            conn.close()
        
        return redirect(url_for('admin.manage_diseases'))
    
    return render_template('admin/add_disease.html')

@admin_bp.route('/disease/edit/<int:id>', methods=['GET', 'POST'])
def edit_disease(id):
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        image_paths = []

        # Get existing images
        c.execute("SELECT images FROM diseases WHERE id=?", (id,))
        existing = c.fetchone()
        existing_imgs = existing[0].split(',') if existing and existing[0] else ['', '', '']

        # Ensure 3 slots
        while len(existing_imgs) < 3:
            existing_imgs.append('')

        # Handle 3 image inputs
        for i in range(1, 4):
            file = request.files.get(f'image_{i}')
            if file and file.filename:
                filename = secure_filename(f"disease_{int(datetime.now().timestamp())}_{file.filename}")
                filepath = os.path.join('static/disease_images/', filename)
                file.save(filepath)
                image_paths.append(f"disease_images/{filename}")
            else:
                image_paths.append(existing_imgs[i-1].strip())

        images_str = ','.join([p for p in image_paths if p])

        # UPDATE QUERY
        c.execute("""UPDATE diseases SET 
                    name=?, description=?, symptoms=?, causes=?, 
                    treatment=?, prevention=?, stage_category=?, images=?
                    WHERE id=?""",
                 (request.form['name'], request.form['description'],
                  request.form['symptoms'], request.form['causes'],
                  request.form['treatment'], request.form['prevention'],
                  request.form['stage_category'], images_str, id))

        conn.commit()
        flash('Disease updated successfully')
        conn.close()
        return redirect(url_for('admin.manage_diseases'))
    
    # GET request
    c.execute("SELECT * FROM diseases WHERE id=?", (id,))
    disease = c.fetchone()
    conn.close()
    
    return render_template('admin/edit_disease.html', disease=disease)
 
        
@admin_bp.route('/disease/delete/<int:id>')
def delete_disease(id):
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM diseases WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash('Disease deleted successfully')
    return redirect(url_for('admin.manage_diseases'))

@admin_bp.route('/users')
def manage_users():
    if not session.get('logged_in') or session.get('user_role') != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, email, role, verified, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)