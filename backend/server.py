"""
خادم Flask بسيط للمنصة التعليمية
يوفر API لتخزين واسترجاع البيانات
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database import DatabaseManager
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

db = DatabaseManager()

# ========== خدمة الملفات الثابتة ==========
@app.route('/')
def serve_index():
    """تقديم صفحة الواجهة الرئيسية"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """تقديم الملفات الثابتة"""
    return send_from_directory('../frontend', path)

# ========== API المصادقة ==========
@app.route('/api/register', methods=['POST'])
def register():
    """تسجيل مستخدم جديد"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    result = db.register_user(email, password, name)
    if result:
        return jsonify({'success': True, 'user': result})
    return jsonify({'success': False, 'error': 'البريد موجود مسبقاً'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """تسجيل دخول المستخدم"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = db.verify_user(email, password)
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'}), 401

# ========== API المحتوى ==========
@app.route('/api/courses', methods=['GET'])
def get_courses():
    """الحصول على جميع الدورات"""
    return jsonify(db.get_all_courses())

@app.route('/api/courses', methods=['POST'])
def add_course():
    """إضافة دورة جديدة"""
    course = request.json
    result = db.add_course(course)
    return jsonify({'success': result})

@app.route('/api/books', methods=['GET'])
def get_books():
    """الحصول على جميع الكتب"""
    return jsonify(db.get_all_books())

@app.route('/api/books', methods=['POST'])
def add_book():
    """إضافة كتاب جديد"""
    book = request.json
    result = db.add_book(book)
    return jsonify({'success': result})

@app.route('/api/products', methods=['GET'])
def get_products():
    """الحصول على جميع المنتجات"""
    return jsonify(db.get_all_products())

@app.route('/api/products', methods=['POST'])
def add_product():
    """إضافة منتج جديد"""
    product = request.json
    result = db.add_product(product)
    return jsonify({'success': result})

# ========== API المشتريات ==========
@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    """تسجيل عملية شراء"""
    purchase = request.json
    result = db.add_purchase(purchase)
    return jsonify({'success': result})

@app.route('/api/purchases/<user_id>', methods=['GET'])
def get_user_purchases(user_id):
    """الحصول على مشتريات المستخدم"""
    return jsonify(db.get_user_purchases(user_id))

# ========== API الطلبات ==========
@app.route('/api/orders', methods=['POST'])
def add_order():
    """إنشاء طلب جديد"""
    order = request.json
    result = db.add_order(order)
    return jsonify({'success': result})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """الحصول على جميع الطلبات"""
    return jsonify(db.get_all_orders())

# ========== الإحصائيات ==========
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """الحصول على إحصائيات المنصة"""
    return jsonify(db.get_stats())

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════╗
    ║     أكاديميتي - منصة التعلم الذكية       ║
    ╠══════════════════════════════════════════╣
    ║  الخادم يعمل على: http://localhost:5000  ║
    ║  لوحة التحكم: http://localhost:5000      ║
    ╚══════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5000)