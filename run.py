#!/usr/bin/env python
"""
تشغيل منصة أكاديميتي
"""

import os
import sys

# إضافة مجلد backend إلى مسار البحث
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.server import app

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║     🎓 أكاديميتي - منصة التعلم الذكية 🎓            ║
    ║                                                      ║
    ║     ✨ تم تشغيل الخادم بنجاح ✨                      ║
    ║                                                      ║
    ║     📱 افتح المتصفح على: http://localhost:5000      ║
    ║                                                      ║
    ║     👤 حساب المدرب: admin@academy.com               ║
    ║     🔑 كلمة المرور: 123456                          ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)