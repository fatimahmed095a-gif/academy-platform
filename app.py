import os
import json
import hashlib
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# --- محاكاة بسيطة لقاعدة البيانات باستخدام الملفات (لضمان العمل على Render) ---
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- API لتسجيل الدخول والمستخدمين (مبسط) ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    users = load_data('users.json')
    for user in users:
        if user.get('email') == email and user.get('password') == password:
            return jsonify({'success': True, 'user': {'id': user['id'], 'email': user['email'], 'name': user['name']}})
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    users = load_data('users.json')
    if any(u.get('email') == email for u in users):
        return jsonify({'success': False, 'error': 'البريد موجود'}), 400
    new_user = {'id': str(datetime.now().timestamp()), 'email': email, 'password': password, 'name': name}
    users.append(new_user)
    save_data('users.json', users)
    return jsonify({'success': True, 'user': {'id': new_user['id'], 'email': new_user['email'], 'name': new_user['name']}})

# --- API للدورات والمنتجات (لإرضاء الكود في index.html) ---
@app.route('/api/courses', methods=['GET'])
def get_courses():
    return jsonify(load_data('courses.json'))

@app.route('/api/courses', methods=['POST'])
def add_course():
    if request.is_json:
        courses = load_data('courses.json')
        new_course = request.get_json()
        new_course['id'] = str(datetime.now().timestamp())
        courses.append(new_course)
        save_data('courses.json', courses)
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# --- نقطة النهاية الرئيسية لخدمة الملفات ---
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
