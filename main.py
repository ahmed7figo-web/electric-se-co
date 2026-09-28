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
import jwt  # مكتبة التشفير (PyJWT)
app = FastAPI()
@app.get("/")
def read_root():
    return {"status": "success", "message": "Maayir Construction API is active and running!"}

@app.get("/tables")
def get_tables_info():
    return {
        "establishment": "مؤسسة مقاولات",
        "status": "Connected",
        "modules": [
            "Employees",
            "Warehouse Stock",
            "Contracts & Operations",
            "Financial Tracking"
        ]
    }

# --- إعدادات الأمان والتشفير ---
SECRET_KEY = "maayir_construction_secure_production_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # جلسة عمل لمدة 8 ساعات

# --- 1. إعداد قاعدة البيانات والاتصال ---
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

# --- 2. نماذج قاعدة البيانات (Database Models) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # مدير, مهندس_ميداني, مسؤول_مستودع, محاسب, مشرف_سلامة
    region = Column(String(50), nullable=False) # المنطقة (مثل الرياض، المدينة المنورة)
    city = Column(String(50), nullable=False)  # المدينة (مثل مهد الذهب)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ContractItem(Base):
    __tablename__ = "contract_items"
    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), index=True, nullable=False)
    description = Column(Text, nullable=False)
    unit_price = Column(Float, nullable=False)
    region = Column(String(50), nullable=True)

class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    work_type = Column(String(20), nullable=False)  # إنشاءات أو صيانة أو عدادات
    region = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    district = Column(String(100), nullable=False)
    consultant = Column(String(100), nullable=False)
    current_status = Column(String(50), default="جديدة")  # كشفيات, تصاريح, حفر, تنفيذ, منتهية, مرجعة
    return_reason = Column(Text, nullable=True)  # سبب الإرجاع للملاحظات
    approved_amount = Column(Float, default=0.0)  # المبلغ المعتمد من الاستشاري
    received_amount = Column(Float, default=0.0)  # المبلغ المستلم بالبنك
    created_at = Column(DateTime, default=datetime.utcnow)

class DepartmentLog(Base):
    __tablename__ = "department_logs"
    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    department_name = Column(String(50), nullable=False)
    employee_name = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    action_date = Column(DateTime, default=datetime.utcnow)

class WarehouseStock(Base):
    __tablename__ = "warehouse_stock"
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(50), nullable=False)
    warehouse_name = Column(String(50), nullable=False)
    item_code = Column(String(50), index=True, nullable=False)
    stock_type = Column(String(20), nullable=False)  # مواد جديدة
if  __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
