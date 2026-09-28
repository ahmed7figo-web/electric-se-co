from datetime import datetime, timedelta
import io
import csv

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import jwt

SECRET_KEY = "maayir_construction_secure_production_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

SQLALCHEMY_DATABASE_URL = "sqlite:///./maayir_enterprise_system.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- نماذج قاعدة البيانات ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    region = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)

class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    work_type = Column(String(20), nullable=False)
    region = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    district = Column(String(100), nullable=False)
    consultant = Column(String(100), nullable=False)
    current_status = Column(String(50), default="جديدة")
    approved_amount = Column(Float, default=0.0)
    received_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class WarehouseStock(Base):
    __tablename__ = "warehouse_stock"
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(50), nullable=False)
    warehouse_name = Column(String(50), nullable=False)
    item_code = Column(String(50), index=True, nullable=False)
    stock_type = Column(String(20), nullable=False)
    quantity = Column(Float, default=0.0)

class FinancialExpense(Base):
    __tablename__ = "financial_expenses"
    id = Column(Integer, primary_key=True, index=True)
    expense_category = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    paid_to = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Maayir Construction - نظام العقد الموحد",
    version="4.0.0",
    description="النظام الموحد المتكامل لإدارة المقاولات والمشاريع الميدانية"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- الواجهة التفاعلية الكاملة لنظام العقد الموحد ---
@app.get("/", response_class=HTMLResponse)
def unified_contract_app():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>نظام العقد الموحد - مؤسسة معايير التشييد للمقاولات</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Cairo', sans-serif; }</style>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col">
        <!-- شريط العنوان -->
        <header class="bg-slate-800 border-b border-slate-700 p-4 shadow-lg flex justify-between items-center">
            <div class="flex items-center space-x-3 space-x-reverse">
                <span class="text-2xl">⚡</span>
                <h1 class="text-xl font-bold text-amber-400">مؤسسة معايير التشييد للمقاولات - نظام العقد الموحد</h1>
            </div>
            <div id="user-info" class="text-sm bg-slate-700 px-3 py-1 rounded-full text-slate-300">غير مسجل الدخول</div>
        </header>

        <!-- المحتوى الرئيسي -->
        <main class="flex-1 p-6 max-w-7xl mx-auto w-full grid grid-cols-1 md:grid-cols-4 gap-6">
            
            <!-- القائمة الجانبية للأقسام -->
            <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 space-y-3 h-fit">
                <h3 class="font-bold text-slate-300 border-b border-slate-700 pb-2 mb-3">أقسام النظام</h3>
                <button onclick="switchTab('dashboard')" class="w-full text-right px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-bold transition">الرئيسية والمؤشرات</button>
                <button onclick="switchTab('orders')" class="w-full text-right px-4 py-2 rounded-lg hover:bg-slate-700 transition">أوامر العمل والمقايسات</button>
                <button onclick="switchTab('warehouse')" class="w-full text-right px-4 py-2 rounded-lg hover:bg-slate-700 transition">المستودعات والسكراب</button>
                <button onclick="switchTab('finance')" class="w-full text-right px-4 py-2 rounded-lg hover:bg-slate-700 transition">الإدارة المالية والمصروفات</button>
                <div class="pt-4 border-t border-slate-700">
                    <a href="/docs" target="_blank" class="block text-center text-xs bg-slate-700 hover:bg-slate-600 p-2 rounded text-amber-300">فتح التوثيق البرمجي (Swagger)</a>
                </div>
            </div>

            <!-- لوحة العرض التفاعلية -->
            <div class="md:col-span-3 bg-slate-800 p-6 rounded-xl border border-slate-700">
                
                <!-- قسم الرئيسية -->
                <div id="tab-dashboard" class="space-y-6">
                    <h2 class="text-2xl font-bold text-amber-400">مرحباً بك في نظام إدارة العقود والمشاريع</h2>
                    <p class="text-slate-300 leading-relaxed">
                        هذا النظام مصمم خصيصاً لإدارة عمليات المقاولات الميدانية، تتبع مراحل أوامر العمل (كشفيات، تصاريح، حفر، تنفيذ، إعادة وضع، ومستخلصات)، مراقبة المخزون، والتدفقات المالية مع عزل صلاحيات المناطق الجغرافية بدقة.
                    </p>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                        <div class="bg-slate-700 p-4 rounded-lg border border-slate-600">
                            <h4 class="text-sm text-slate-400">أوامر العمل النشطة</h4>
                            <p class="text-2xl font-bold text-amber-400 mt-2">--</p>
                        </div>
                        <div class="bg-slate-700 p-4 rounded-lg border border-slate-600">
                            <h4 class="text-sm text-slate-400">إجمالي الاعتمادات</h4>
                            <p class="text-2xl font-bold text-emerald-400 mt-2">-- ر.س</p>
                        </div>
                        <div class="bg-slate-700 p-4 rounded-lg border border-slate-600">
                            <h4 class="text-sm text-slate-400">المصروفات الحالية</h4>
                            <p class="text-2xl font-bold text-rose-400 mt-2">-- ر.س</p>
                        </div>
                    </div>
                </div>

                <!-- قسم أوامر العمل -->
                <div id="tab-orders" class="hidden space-y-4">
                    <h2 class="text-xl font-bold text-amber-400">إدارة أوامر العمل والمقايسات</h2>
                    <p class="text-sm text-slate-400">متابعة مراحل التنفيذ من الكشفيات حتى المستخلص النهائي واستلام المندوب.</p>
                    <div class="bg-slate-700 p-4 rounded-lg border border-slate-600 text-center text-slate-300">
                        جاري تحميل قائمة أوامر العمل المرتبطة بنطاقك الجغرافي...
                    </div>
                </div>

                <!-- قسم المستودعات -->
                <div id="tab-warehouse" class="hidden space-y-4">
                    <h2 class="text-xl font-bold text-amber-400">إدارة المستودعات ومواد السكراب</h2>
                    <p class="text-sm text-slate-400">مراقبة أرصدة المواد الجديدة والراجعة (Scrap) وإذن الصرف والإرجاع.</p>
                    <div class="bg-slate-700 p-4 rounded-lg border border-slate-600 text-center text-slate-300">
                        أرصدة المستودعات والمواد مطابقة للنظام السحابي.
                    </div>
                </div>

                <!-- قسم المالية -->
                <div id="tab-finance" class="hidden space-y-4">
                    <h2 class="text-xl font-bold text-amber-400">الرقابة المالية والتدفقات النقدية</h2>
                    <p class="text-sm text-slate-400">تسجيل مصروفات الإيجارات، الأجور، والمواد، وحساب صافي الأرباح.</p>
                    <div class="bg-slate-700 p-4 rounded-lg border border-slate-600 text-center text-slate-300">
                        التقارير المالية والملخصات جاهزة للاستخراج والتصدير.
                    </div>
                </div>

            </div>
        </main>

        <script>
            function switchTab(tabId) {
                document.getElementById('tab-dashboard').classList.add('hidden');
                document.getElementById('tab-orders').classList.add('hidden');
                document.getElementById('tab-warehouse').classList.add('hidden');
                document.getElementById('tab-finance').classList.add('hidden');
                
                document.getElementById('tab-' + tabId).classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """

# --- مسارات الـ API الأساسية ---
@app.get("/api/health")
def health_check():
    return {"status": "online", "system": "Maayir Construction Unified System"}
