from flask import render_template, request, redirect, url_for, session, flash
from . import auth_bp
import sqlite3
import hashlib
import os
import re

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hash_password(request.form['password'])
        role = request.form.get('role', 'farmer')
        latitude = float(request.form.get('latitude', 0))
        longitude = float(request.form.get('longitude', 0))

        
        # Basic validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Invalid email address')
            return redirect(url_for('auth.register'))
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, role, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)",
                     (name, email, password, role, latitude, longitude))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash('Email already exists')
        finally:
            conn.close()
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[4]
            session['logged_in'] = True
            
            if user[4] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('farmer.dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    if new_password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('auth.login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()

    if not user:
        flash('No account found with that email', 'error')
        conn.close()
        return redirect(url_for('auth.login'))

    c.execute("UPDATE users SET password = ? WHERE email = ?",
              (hash_password(new_password), email))
    conn.commit()
    conn.close()

    flash('Password reset successful! Please login.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))