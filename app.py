import os
import json
import uuid
import base64
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# ===== تهيئة الاتصال بـ Supabase =====
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Warning: Supabase credentials not found!")
    
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase connected successfully")
except Exception as e:
    print(f"❌ Supabase connection error: {e}")
    supabase = None

# ===== Helper Functions =====
def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def safe_uuid(value):
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return str(value)

def upload_to_storage(file_data, file_name, bucket_name):
    """رفع ملف إلى Supabase Storage"""
    if not supabase:
        return None
    
    try:
        # تحويل Base64 إلى bytes
        if ',' in file_data:
            file_bytes = base64.b64decode(file_data.split(',')[1])
        else:
            file_bytes = base64.b64decode(file_data)
        
        # رفع الملف
        supabase.storage.from_(bucket_name).upload(file_name, file_bytes)
        
        # الحصول على الرابط العام
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        print(f"Upload error: {e}")
        return None

# ===== API المصادقة =====
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    try:
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
        print(f"Login error: {e}")
    
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', email.split('@')[0])
    
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"name": name}}
        })
        
        if response.user:
            try:
                supabase.table('profiles').insert({
                    "id": response.user.id,
                    "name": name,
                    "email": email,
                    "created_at": datetime.now().isoformat()
                }).execute()
            except:
                pass
            
            return jsonify({
                'success': True, 
                'user': {
                    'id': response.user.id, 
                    'email': response.user.email, 
                    'name': name
                }
            })
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({'success': False, 'error': 'فشل إنشاء الحساب'}), 400

# ===== API الكتب (مع رفع إلى Storage) =====
@app.route('/api/books', methods=['GET'])
def get_books():
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('books').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/books', methods=['POST'])
def add_book():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    
    try:
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'العنوان مطلوب'}), 400
        
        image_url = None
        if data.get('image_data'):
            file_name = f"{uuid.uuid4()}.jpg"
            image_url = upload_to_storage(data.get('image_data'), file_name, 'book-covers')
        
        file_url = None
        if data.get('file_data'):
            file_name = f"{uuid.uuid4()}.pdf"
            file_url = upload_to_storage(data.get('file_data'), file_name, 'pdf-books')
        
        new_book = {
            "title": data.get('title'),
            "description": data.get('description', ''),
            "price": int(data.get('price', 0)),
            "quantity": int(data.get('quantity', 1)),
            "image_url": image_url or '',
            "file_url": file_url or '',
            "author": data.get('author', 'المؤلف'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('books').insert(new_book).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API المنتجات =====
@app.route('/api/products', methods=['GET'])
def get_products():
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('products').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/products', methods=['POST'])
def add_product():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    
    try:
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'العنوان مطلوب'}), 400
        
        image_url = None
        if data.get('image_data'):
            file_name = f"{uuid.uuid4()}.jpg"
            image_url = upload_to_storage(data.get('image_data'), file_name, 'product-images')
        
        new_product = {
            "title": data.get('title'),
            "description": data.get('description', ''),
            "price": int(data.get('price', 0)),
            "quantity": int(data.get('quantity', 1)),
            "image_url": image_url or '',
            "seller": data.get('seller', 'البائع'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('products').insert(new_product).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API الدورات =====
@app.route('/api/courses', methods=['GET'])
def get_courses():
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('courses').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/courses', methods=['POST'])
def add_course():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    
    try:
        image_url = None
        if data.get('image_data'):
            file_name = f"{uuid.uuid4()}.jpg"
            image_url = upload_to_storage(data.get('image_data'), file_name, 'course-images')
        
        new_course = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": int(data.get('price', 0)),
            "lessons_count": int(data.get('lessons', 0)),
            "hours": int(data.get('hours', 0)),
            "rating": float(data.get('rating', 0)),
            "image_url": image_url or '',
            "video_url": data.get('video_data', ''),
            "instructor_name": data.get('instructor_name', 'المدرب'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('courses').insert(new_course).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API المشتريات =====
@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    
    try:
        user_id = safe_uuid(data.get('user_id'))
        item_id = safe_uuid(data.get('item_id'))
        
        new_purchase = {
            "user_id": user_id,
            "item_id": item_id,
            "item_type": data.get('item_type'),
            "item_title": data.get('item_title'),
            "item_price": int(data.get('item_price', 0)),
            "quantity": int(data.get('quantity', 1)),
            "total_price": int(data.get('total_price', data.get('item_price', 0))),
            "purchase_date": datetime.now().isoformat()
        }
        response = supabase.table('purchases').insert(new_purchase).execute()
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/purchases/<user_id>', methods=['GET'])
def get_user_purchases(user_id):
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('purchases').select('*').eq('user_id', str(user_id)).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

# ===== API الطلبات =====
@app.route('/api/orders', methods=['GET'])
def get_orders():
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('orders').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/orders', methods=['POST'])
def create_order():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
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
            "quantity": int(data.get('quantity', 1)),
            "total_price": int(data.get('price', 0)) * int(data.get('quantity', 1)),
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
    if not supabase:
        return jsonify({'courses_count': 0, 'products_count': 0, 'users_count': 0, 'orders_count': 0})
    
    try:
        courses = supabase.table('courses').select('*', count='exact').execute()
        products = supabase.table('products').select('*', count='exact').execute()
        books = supabase.table('books').select('*', count='exact').execute()
        orders = supabase.table('orders').select('*', count='exact').execute()
        
        return jsonify({
            'courses_count': courses.count if hasattr(courses, 'count') else len(courses.data),
            'products_count': (products.count if hasattr(products, 'count') else len(products.data)) + 
                             (books.count if hasattr(books, 'count') else len(books.data)),
            'users_count': 0,
            'orders_count': orders.count if hasattr(orders, 'count') else len(orders.data)
        })
    except Exception as e:
        return jsonify({'courses_count': 0, 'products_count': 0, 'users_count': 0, 'orders_count': 0})

# ===== نقطة النهاية الرئيسية =====
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)