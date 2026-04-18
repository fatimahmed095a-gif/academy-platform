import os
import json
import uuid
import base64
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import boto3
from botocore.client import Config

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

# ===== إعدادات Cloudflare R2 =====
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", "c056df2bce9d0974127b6bab5e4bf725")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY", "40d27dd171158496732d980fd06c35f33bdbf0a7f234781ec0ad58f3d5e555c9")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "https://68abc98bcef9ff6c6471cdd592d4094e.r2.cloudflarestorage.com")
R2_BUCKET = os.environ.get("R2_BUCKET", "academy-storage")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL", "https://pub-81cde84cb32b4392b5ffe20735d33097.r2.dev")

def upload_to_r2(file_data, file_name, folder):
    """رفع ملف إلى Cloudflare R2"""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        
        if ',' in file_data:
            file_bytes = base64.b64decode(file_data.split(',')[1])
        else:
            file_bytes = base64.b64decode(file_data)
        
        key = f"{folder}/{uuid.uuid4()}_{file_name}"
        
        # تحديد نوع المحتوى
        if file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif file_name.endswith('.png'):
            content_type = 'image/png'
        elif file_name.endswith('.pdf'):
            content_type = 'application/pdf'
        elif file_name.endswith('.mp4'):
            content_type = 'video/mp4'
        elif file_name.endswith('.webm'):
            content_type = 'video/webm'
        else:
            content_type = 'application/octet-stream'
        
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType=content_type
        )
        
        public_url = f"{R2_PUBLIC_URL}/{key}"
        print(f"✅ File uploaded to R2: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ R2 Upload error: {e}")
        return None

def upload_video_to_r2(file_data, file_name):
    """رفع فيديو إلى Cloudflare R2"""
    return upload_to_r2(file_data, file_name, 'course-videos')

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

# ===== API الكتب (مع رفع إلى R2) =====
@app.route('/api/books', methods=['GET'])
def get_books():
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('books').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        print(f"Error getting books: {e}")
        return jsonify([])

@app.route('/api/books', methods=['POST'])
def add_book():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    print(f"📚 Received book data")
    
    try:
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'العنوان مطلوب'}), 400
        
        # رفع الصورة إلى R2
        image_url = None
        if data.get('image_data'):
            print("📸 Uploading image to R2...")
            image_url = upload_to_r2(data.get('image_data'), 'image.jpg', 'book-covers')
            print(f"📸 Image URL: {image_url}")
        
        # رفع ملف PDF إلى R2
        file_url = None
        if data.get('file_data'):
            print("📄 Uploading PDF to R2...")
            file_url = upload_to_r2(data.get('file_data'), 'document.pdf', 'pdf-books')
            print(f"📄 PDF URL: {file_url}")
        
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
        print(f"✅ Book saved: {response.data}")
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"❌ Error saving book: {e}")
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
        print(f"Error getting products: {e}")
        return jsonify([])

@app.route('/api/products', methods=['POST'])
def add_product():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    print(f"🎁 Received product data")
    
    try:
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'العنوان مطلوب'}), 400
        
        # رفع الصورة إلى R2
        image_url = None
        if data.get('image_data'):
            print("🖼️ Uploading product image to R2...")
            image_url = upload_to_r2(data.get('image_data'), 'product.jpg', 'product-images')
            print(f"🖼️ Image URL: {image_url}")
        
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
        print(f"✅ Product saved: {response.data}")
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"❌ Error saving product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API الدورات (مع رفع الفيديو إلى R2) =====
@app.route('/api/courses', methods=['GET'])
def get_courses():
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('courses').select('*').execute()
        return jsonify(response.data)
    except Exception as e:
        print(f"Error getting courses: {e}")
        return jsonify([])

@app.route('/api/courses', methods=['POST'])
def add_course():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    print(f"🎓 Received course data")
    
    try:
        if not data.get('title'):
            return jsonify({'success': False, 'error': 'العنوان مطلوب'}), 400
        
        # رفع الصورة إلى R2
        image_url = None
        if data.get('image_data'):
            print("🖼️ Uploading course image to R2...")
            image_url = upload_to_r2(data.get('image_data'), 'course.jpg', 'course-images')
            print(f"🖼️ Image URL: {image_url}")
        
        # رفع الفيديو إلى R2
        video_url = None
        if data.get('video_data'):
            print("🎬 Uploading course video to R2...")
            video_url = upload_video_to_r2(data.get('video_data'), 'course.mp4')
            print(f"🎬 Video URL: {video_url}")
        
        new_course = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": int(data.get('price', 0)),
            "lessons_count": int(data.get('lessons', 0)),
            "hours": int(data.get('hours', 0)),
            "rating": float(data.get('rating', 0)),
            "image_url": image_url or '',
            "video_url": video_url or '',
            "instructor_name": data.get('instructor_name', 'المدرب'),
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table('courses').insert(new_course).execute()
        print(f"✅ Course saved: {response.data}")
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"❌ Error saving course: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

# ===== API المشتريات =====
@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    if not supabase:
        return jsonify({'success': False, 'error': 'Supabase not connected'}), 500
    
    data = request.json
    print(f"💰 Purchase data received")
    
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
        print(f"✅ Purchase saved")
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"❌ Add purchase error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/purchases/<user_id>', methods=['GET'])
def get_user_purchases(user_id):
    if not supabase:
        return jsonify([])
    try:
        response = supabase.table('purchases').select('*').eq('user_id', str(user_id)).execute()
        return jsonify(response.data)
    except Exception as e:
        print(f"Get purchases error: {e}")
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
        print(f"Get orders error: {e}")
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
        print(f"✅ Order created")
        return jsonify({'success': True, 'data': response.data})
    except Exception as e:
        print(f"Create order error: {e}")
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
        print(f"Stats error: {e}")
        return jsonify({'courses_count': 0, 'products_count': 0, 'users_count': 0, 'orders_count': 0})

# ===== نقطة النهاية الرئيسية =====
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve(path):
    return send_from_directory('frontend', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)