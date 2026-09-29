from datetime import datetime
import os
import io

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn

SQLALCHEMY_DATABASE_URL = "sqlite:///./unified_contract_master.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 1. جدول المهام الميدانية والمستخلصات ---
class UltimateFieldTask(Base):
    __tablename__ = "ultimate_field_tasks"
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(50), nullable=False)     # طوارئ / صيانة / إنشاءات
    work_order = Column(String(50), nullable=False)     # رقم أمر العمل
    team_name = Column(String(100), nullable=False)     # اسم الفني أو المشرف
    location_desc = Column(String(150), nullable=False) # الحي والشارع
    gps_coords = Column(String(100), nullable=True)   # الإحداثيات
    
    equipment_name = Column(String(100), nullable=False) # اسم المعدة
    equipment_capacity = Column(String(50), nullable=True) # السعة
    equipment_serial = Column(String(100), nullable=True)  # رقم اللوحة Nameplate
    cable_type = Column(String(100), nullable=True)      # نوع الكابل
    trench_meters = Column(Float, default=0.0)           # أمتار الحفر / التمديد
    unit_rate = Column(Float, default=150.0)             # سعر الوحدة / المتر (ريال)
    total_amount = Column(Float, default=0.0)            # إجمالي المبلغ المستحق
    power_source = Column(String(100), nullable=True)    # مصدر التغذية
    
    image_path = Column(String(255), nullable=True)      # مسار صورة المعدة المرفوعة
    safety_checked = Column(Boolean, default=False)
    site_closed = Column(Boolean, default=False)
    approval_status = Column(String(50), default="قيد الانتظار")
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- 2. جدول المستودعات والعهد العينية ---
class WarehouseItem(Base):
    __tablename__ = "warehouse_items"
    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), unique=True, nullable=False) # كود الصنف SKU
    item_name = Column(String(100), nullable=False)            # اسم المادة / الأداة
    category = Column(String(50), nullable=False)              # كابلات / قواطع / أدوات سلامة
    quantity = Column(Integer, default=0)                      # الكمية المتوفرة
    unit = Column(String(20), default="قطعة")                  # وحدة القياس (متر، حبة، طرد)
    location = Column(String(50), default="المستودع الرئيسي")   # الرف / الموقع

# --- 3. جدول العهد المالية لتسيير الأعمال والمصروفات النثرية ---
class FieldPettyCash(Base):
    __tablename__ = "field_petty_cash"
    id = Column(Integer, primary_key=True, index=True)
    supervisor_name = Column(String(100), nullable=False)      # اسم المشرف حامل العهدة
    advance_amount = Column(Float, default=0.0)                # قيمة العهدة المسلمة (ريال)
    spent_amount = Column(Float, default=0.0)                  # المبلغ المنصرف على المصروفات
    expense_desc = Column(Text, nullable=True)                 # بيان المصروف (و�
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
