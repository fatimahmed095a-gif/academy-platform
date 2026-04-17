"""
إدارة قاعدة البيانات - تخزين JSON مبسط
"""

import json
import os
import hashlib
from datetime import datetime

class DatabaseManager:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self._ensure_dir()
        self._load_all()
    
    def _ensure_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _get_path(self, name):
        return os.path.join(self.data_dir, f'{name}.json')
    
    def _load(self, name):
        path = self._get_path(name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save(self, name, data):
        with open(self._get_path(name), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_all(self):
        self.users = self._load('users')
        self.courses = self._load('courses')
        self.books = self._load('books')
        self.products = self._load('products')
        self.purchases = self._load('purchases')
        self.orders = self._load('orders')
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    # ===== عمليات المستخدمين =====
    def register_user(self, email, password, name):
        """تسجيل مستخدم جديد"""
        # التحقق من وجود البريد
        for u in self.users:
            if u.get('email') == email:
                return None
        
        user = {
            'id': str(int(datetime.now().timestamp() * 1000)),
            'email': email,
            'password': self._hash_password(password),
            'name': name,
            'role': 'student',
            'created_at': datetime.now().isoformat()
        }
        self.users.append(user)
        self._save('users', self.users)
        return {'id': user['id'], 'email': user['email'], 'name': user['name'], 'role': user['role']}
    
    def verify_user(self, email, password):
        """التحقق من بيانات المستخدم"""
        hashed = self._hash_password(password)
        for user in self.users:
            if user.get('email') == email and user.get('password') == hashed:
                return {'id': user['id'], 'email': user['email'], 'name': user['name'], 'role': user['role']}
        return None
    
    def get_user_by_id(self, user_id):
        """الحصول على مستخدم بالمعرف"""
        for user in self.users:
            if user.get('id') == user_id:
                return user
        return None
    
    # ===== عمليات المحتوى =====
    def get_all_courses(self):
        return self.courses
    
    def add_course(self, course):
        course['id'] = str(int(datetime.now().timestamp() * 1000))
        course['created_at'] = datetime.now().isoformat()
        self.courses.append(course)
        self._save('courses', self.courses)
        return True
    
    def get_all_books(self):
        return self.books
    
    def add_book(self, book):
        book['id'] = str(int(datetime.now().timestamp() * 1000))
        book['created_at'] = datetime.now().isoformat()
        self.books.append(book)
        self._save('books', self.books)
        return True
    
    def get_all_products(self):
        return self.products
    
    def add_product(self, product):
        product['id'] = str(int(datetime.now().timestamp() * 1000))
        product['created_at'] = datetime.now().isoformat()
        self.products.append(product)
        self._save('products', self.products)
        return True
    
    # ===== عمليات المشتريات =====
    def add_purchase(self, purchase):
        purchase['id'] = str(int(datetime.now().timestamp() * 1000))
        purchase['purchase_date'] = datetime.now().isoformat()
        self.purchases.append(purchase)
        self._save('purchases', self.purchases)
        return True
    
    def get_user_purchases(self, user_id):
        return [p for p in self.purchases if p.get('user_id') == user_id]
    
    # ===== عمليات الطلبات =====
    def add_order(self, order):
        order['id'] = str(int(datetime.now().timestamp() * 1000))
        order['created_at'] = datetime.now().isoformat()
        order['status'] = 'pending'
        self.orders.append(order)
        self._save('orders', self.orders)
        return True
    
    def get_all_orders(self):
        return self.orders
    
    # ===== الإحصائيات =====
    def get_stats(self):
        return {
            'users_count': len(self.users),
            'courses_count': len(self.courses),
            'books_count': len(self.books),
            'products_count': len(self.products),
            'purchases_count': len(self.purchases),
            'orders_count': len(self.orders)
        }