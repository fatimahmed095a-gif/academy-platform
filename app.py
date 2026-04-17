import os
import json
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# ===== تهيئة الاتصال بـ Supabase =====
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== Helper Functions =====
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# ===== API المصادقة (باستخدام Supabase Auth) =====
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    try:
        # محاولة تسجيل الدخول عبر Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return jsonify({
                'success': True, 
                'user': {
                    'id': response.user.id, 
                    'email': response.user.email, 
                    'name': response.user.user_metadata.get('name', email.split('@')[0])
                }
            })
    except Exception as e:
        # إذا فشل Auth، نبحث في جدول users القديم (للتوافق)
        users = supabase.table('users').select('*').eq('email', email).execute()
        if users.data and len(users.data) > 0:
            user = users.data[0]
            if user.get('password') == hash_password(password):
                return jsonify({
                    'success': True, 
                    'user': {
                        'id': user['id'], 
                        'email': user['email'], 
                        'name': user.get('name', email.split('@')[0])
                    }
                })
    
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', email.split('@')[0])
    
    try:
        # تسجيل مستخدم جديد عبر Supabase Auth
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"name": name}
            }
        })
        
        if response.user:
            # إضافة الملف الشخصي في جدول profiles
            supabase.table('profiles').insert({
                "id": response.user.id,
                "name": name,
                "email": email,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return jsonify({
                'success': True, 
                'user': {
                    'id': response.user.id, 
                    'email': response.user.email, 
                    'name': name
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({'success': False, 'error': 'فشل إنشاء الحساب'}), 400

# ===== API الدورات =====
@app.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        response = supabase.table('courses').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/courses', methods=['POST'])
def add_course():
    data = request.json
    try:
        new_course = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": data.get('price'),
            "lessons_count": data.get('lessons', 0),
            "hours": data.get('hours', 0),
            "rating": data.get('rating', 0),
            "image_url": data.get('image_data', ''),
            "video_url": data.get('video_data', ''),
            "instructor_name": data.get('instructor_name', 'المدرب'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('courses').insert(new_course).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API الكتب =====
@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        response = supabase.table('books').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.json
    try:
        new_book = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": data.get('price'),
            "quantity": data.get('hours', 1),
            "image_url": data.get('image_data', ''),
            "file_url": data.get('file_data', ''),
            "author": data.get('instructor_name', 'المؤلف'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('books').insert(new_book).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API المنتجات =====
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        response = supabase.table('products').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    try:
        new_product = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": data.get('price'),
            "quantity": data.get('hours', 1),
            "image_url": data.get('image_data', ''),
            "seller": data.get('instructor_name', 'البائع'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('products').insert(new_product).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API المشتريات =====
@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    data = request.json
    try:
        new_purchase = {
            "user_id": data.get('user_id'),
            "item_id": data.get('item_id'),
            "item_type": data.get('item_type'),
            "item_title": data.get('item_title'),
            "item_price": data.get('item_price'),
            "quantity": data.get('quantity', 1),
            "total_price": data.get('total_price', data.get('item_price', 0)),
            "purchase_date": datetime.now().isoformat()
        }
        response = supabase.table('purchases').insert(new_purchase).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/purchases/<user_id>', methods=['GET'])
def get_user_purchases(user_id):
    try:
        response = supabase.table('purchases').select('*').eq('user_id', user_id).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

# ===== API الطلبات =====
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        response = supabase.table('orders').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    try:
        new_order = {
            "user_id": data.get('userId'),
            "user_name": data.get('customerName'),
            "user_phone": data.get('customerPhone'),
            "user_email": data.get('userEmail', ''),
            "address": data.get('address'),
            "product_id": data.get('productId'),
            "product_title": data.get('productTitle'),
            "quantity": data.get('quantity', 1),
            "total_price": data.get('price', 0) * data.get('quantity', 1),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('orders').insert(new_order).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== الإحصائيات =====
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        courses = supabase.table('courses').select('*', count='exact').execute()
        products = supabase.table('products').select('*', count='exact').execute()
        books = supabase.table('books').select('*', count='exact').execute()
        orders = supabase.table('orders').select('*', count='exact').execute()
        
        # عدد المستخدمين من Auth (تقريبي)
        users_count = 0
        try:
            users = supabase.auth.admin.list_users()
            users_count = len(users.users) if hasattr(users, 'users') else 0
        except:
            users_count = 0
        
        return jsonify({
            'courses_count': courses.count if hasattr(courses, 'count') else len(courses.data),
            'products_count': (products.count if hasattr(products, 'count') else len(products.data)) + 
                             (books.count if hasattr(books, 'count') else len(books.data)),
            'users_count': users_count,
            'orders_count': orders.count if hasattr(orders, 'count') else len(orders.data)
        })
    except Exception as e:
        return jsonify({'courses_count': 0, 'products_count': 0, 'users_count': 0, 'orders_count': 0})

# ===== نقطة النهاية الرئيسية لخدمة الملفات =====
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)