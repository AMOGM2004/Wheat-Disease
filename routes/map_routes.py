from flask import Blueprint, render_template, request, jsonify
import sqlite3

map_bp = Blueprint('map', __name__)

@map_bp.route('/map')
def disease_map():
    return render_template('map.html')

@map_bp.route('/api/disease-reports')
def get_reports():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT farmer_name, disease_name, latitude, longitude, timestamp FROM disease_reports')
    rows = cursor.fetchall()
    conn.close()

    reports = []
    for row in rows:
        reports.append({
            'farmer_name': row[0],
            'disease': row[1],
            'lat': row[2],
            'lng': row[3],
            'time': row[4]
        })
    return jsonify(reports)