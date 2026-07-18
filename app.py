import streamlit as st
import pandas as pd
import sqlite3
import datetime

# ==========================================
# 1. إعدادات الصفحة واللغة العربية
# ==========================================
st.set_page_config(
    page_title="نظام إدارة الملفات الطبوغرافية",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# دعم اتجاه النص من اليمين إلى اليسار (RTL) للغة العربية
st.markdown("""
    <style>
    .big-title { text-align: right; color: #ff6e40; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stApp { direction: RTL; text-align: right; }
    div[data-testid="stBlock"] { direction: RTL; text-align: right; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div.stNumberInput { direction: RTL; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إعداد قاعدة البيانات وتحديث الجداول
# ==========================================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # إنشاء جدول المشاريع الأساسي
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT,
            land_type TEXT,
            location TEXT,
            price REAL DEFAULT 0.0,
            paid REAL DEFAULT 0.0,
            date_measured TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_payment(project_id, new_paid_amount):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET paid = ? WHERE id = ?", (new_paid_amount, project_id))
    conn.commit()
    conn.close()

def delete_project(project_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def add_project(client_name, phone, land_type, location, price, paid, date_measured):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO projects (client_name, phone, land_type, location, price, paid, date_measured)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (client_name, phone, land_type, location, price, paid, date_measured))
    conn.commit()
    conn.close()

def update_project_details(project_id, name, phone, l_type, loc, price, paid, dt):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE projects 
        SET client_name=?, phone=?, land_type=?, location=?, price=?, paid=?, date_measured=?
        WHERE id=?
    """, (name, phone, l_type, loc, price, paid, dt, project_id))
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند تشغيل البرنامج
init_db()

# ==========================================
# 3. إدارة الجلسة (Session State) للغلق والتعديل
# ==========================================
if "edit_project_id" not in st.session_state:
    st.session_state.edit_project_id = None

# ==========================================
# 4. واجهة المستخدم الرسومية (UI)
# ==========================================
st.markdown("<h1 class='big-title'>🗺️ نظام إدارة الملفات الطبوغرافية</h1>", unsafe_allow_html=True)
st.markdown("---")

# الحصيلة الإجمالية السريعة في الأعلى
conn = sqlite3.connect("database.db")
df_stats = pd.read_sql_query("SELECT price, paid FROM projects", conn)
conn.close()

if not df_stats.empty:
    total_revenue = df_stats['price'].sum()
    total_paid = df_stats['paid'].sum()
    total_remaining = total_revenue - total_paid
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("إجمالي المداخيل المتوقعة", f"{total_revenue:,.2f} درهم")
    stat_col2.metric("إجمالي المبالغ المدفوعة 💵", f"{total_paid:,.2f} درهم", delta=f"+{total_paid:,.2f}", delta_color="inverse")
    stat_col3.metric("إجمالي المبالغ المتبقية ⚠️", f"{total_remaining:,.2f} درهم", delta=f"-{total_remaining:,.2f}" if total_remaining > 0 else "0.00")
    st.markdown("---")

# قسما الواجهة: إضافة وتعديل / عرض وبحث
tab1, tab2 = st.tabs(["➕ إضافة / تعديل ملف", "🔍 استعراض وبحث الملفات"])

# --- التبويب الأول: إضافة وتعديل ملف ---
with tab1:
    if st.session_state.edit_project_id is not None:
        st.subheader("✏️ تعديل بيانات الملف الحالي")
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM projects WHERE id = ?", (st.session_state.edit_project_id,))
        p_data = cur.fetchone()
        conn.close()
        
        if p_data:
            with st.form("edit_form"):
                e_name = st.text_input("اسم الزبون", value=p_data[1])
                e_phone = st.text_input("رقم الهاتف", value=p_data[2])
                e_type = st.selectbox("نوع الأرض", ["ملك حر محفظ (Titre)", "ملك غير محفظ (Melk)", "أراضي جموع", "أخرى"], index=["ملك حر محفظ (Titre)", "ملك غير محفظ (Melk)", "أراضي جموع", "أخرى"].index(p_data[3]) if p_data[3] in ["ملك حر محفظ (Titre)", "ملك غير محفظ (Melk)", "أراضي جموع", "أخرى"] else 0)
                e_loc = st.text_input("مكان العقار / الموقع", value=p_data[4])
                
                col_e1, col_e2 = st.columns(2)
                e_price = col_e1.number_input("السعر الإجمالي (درهم)", min_value=0.0, value=p_data[5])
                e_paid = col_e2.number_input("المبلغ المدفوع حالياً (درهم)", min_value=0.0, value=p_data[6])
                
                e_date = st.date_input("تاريخ القياس", value=datetime.datetime.strptime(p_data[7], "%Y-%m-%d").date() if p_data[7] else datetime.date.today())
                
                btn_sub_col1, btn_sub_col2 = st.columns(2)
                if btn_sub_col1.form_submit_button("💾 حفظ التعديلات الجديدة"):
                    update_project_details(st.session_state.edit_project_id, e_name, e_phone, e_type, e_loc, e_price, e_paid, str(e_date))
                    st.session_state.edit_project_id = None
                    st.success("تم تحديث بيانات الملف بنجاح!")
                    st.rerun()
                if btn_sub_col2.form_submit_button("❌ إلغاء التعديل"):
                    st.session_state.edit_project_id = None
                    st.rerun()
    else:
        st.subheader("➕ تسجيل ملف طبوغرافي جديد")
        with st.form("add_form"):
            c_name = st.text_input("اسم الزبون الكامل")
            c_phone = st.text_input("رقم الهاتف")
            c_type = st.selectbox("نوع الأرض العقارية", ["ملك حر محفظ (Titre)", "ملك غير محفظ (Melk)", "أراضي جموع", "أخرى"])
            c_loc = st.text_input("مكان العقار (مثال: حي إكلكال تافراوت)")
            
            col_c1, col_c2 = st.columns(2)
            c_price = col_c1.number_input("السعر الإجمالي المتفق عليه (درهم)", min_value=0.0, step=100.0, value=0.0)
            c_paid = col_c2.number_input("المبلغ المدفوع مسبقاً تسبيغ (درهم)", min_value=0.0, step=100.0, value=0.0)
            
            c_date = st.date_input("تاريخ النزول للميدان / القياس", value=datetime.date.today())
            
            if st.form_submit_button("✅ تسجيل الملف في قاعدة البيانات"):
                if c_name.strip() == "":
                    st.error("المرجو إدخال اسم الزبون!")
                else:
                    add_project(c_name, c_phone, c_type, c_loc, c_price, c_paid, str(c_date))
                    st.success(f"تم تسجيل ملف الزبون '{c_name}' بنجاح تام!")
                    st.rerun()

# --- التبويب الثاني: استعراض وبحث الملفات ---
with tab2:
    st.subheader("🔍 البحث الفوري واستعراض الملفات المسجلة")
    search_query = st.text_input("اكتب اسم الزبون أو مكان العقار للبحث السريع:")
    
    # جلب البيانات
    conn = sqlite3.connect("database.db")
    if search_query.strip() != "":
        query = "SELECT * FROM projects WHERE client_name LIKE ? OR location LIKE ? ORDER BY id DESC"
        df = pd.read_sql_query(query, conn, params=(f"%{search_query}%", f"%{search_query}%"))
    else:
        df = pd.read_sql_query("SELECT * FROM projects ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("لا توجد ملفات مسجلة تطابق بحثك حالياً.")
    else:
        # تحويل البيانات إلى قاموس لعرض مخصص وبطاقات منظمة بدل الجداول الضيقة
        projects_list = df.to_dict(orient="records")
        
        for p in projects_list:
            reste = p['price'] - p['paid']
            
            # تصميم بطاقة مخصصة لكل ملف طبوغرافي
            st.markdown(f"""
            <div style="background-color: #f9f9f9; padding: 15px; border-right: 5px solid #ff6e40; border-radius: 4px; margin-bottom: 10px;">
                <h4>👤 الزبون: {p['client_name']}</h4>
                <p>📞 <b>الهاتف:</b> {p['phone']} | 🏷️ <b>نوع الأرض:</b> {p['land_type']}</p>
                <p>📍 <b>الموقع:</b> {p['location']} | 📅 <b>تاريخ القياس:</b> {p['date_measured']}</p>
                <p>💰 <b>الإجمالي:</b> {p['price']:.2f} درهم | 💵 <b>المدفوع:</b> {p['paid']:.2f} درهم | ⚠️ <span style="color:red;"><b>الباقي:</b> {reste:.2f} درهم</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # توزيع عناصر التحكم والتحرير والأزرار
            sub_col1, sub_col2 = st.columns([2, 3])
            
            with sub_col1:
                st.write("") # فراغ مالي للتوازن العمودي مع الأزرار بجانبه
                
            with sub_col2:
                if reste > 0:
                    # خانة إضافة تسديد تأخذ العرض المتاح بالكامل
                    add_pay = st.number_input(f"إضافة تسديد", min_value=0.0, max_value=reste, step=100.0, key=f"pay_input_{p['id']}", use_container_width=True)
                    
                    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True) # فراغ صغير جداً للتناسق الفني
                    
                    # إنشاء 3 أعمدة صغيرة ومتقايسة داخل نفس القسم لتصفيف الأزرار جنباً إلى جنب في سطر مستقيم
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    with btn_col1:
                        if st.button(f"تحديث 💵", key=f"pay_btn_{p['id']}", use_container_width=True):
                            update_payment(p['id'], p['paid'] + add_pay)
                            st.rerun()
                            
                    with btn_col2:
                        if st.button(f"تعديل ✏️", key=f"edit_btn_{p['id']}", use_container_width=True):
                            st.session_state.edit_project_id = p['id']
                            st.rerun()
                            
                    with btn_col3:
                        if st.button(f"حذف 🗑️", key=f"delete_btn_{p['id']}", use_container_width=True):
                            delete_project(p['id'])
                            st.rerun()
                else:
                    # في حالة سُدد المبلغ بالكامل، تظهر أزرار التعديل والحذف فقط جنباً إلى جنب بشكل متقايس ومريح
                    btn_full_col1, btn_full_col2 = st.columns(2)
                    with btn_full_col1:
                        if st.button(f"تعديل ✏️", key=f"edit_btn_{p['id']}", use_container_width=True):
                            st.session_state.edit_project_id = p['id']
                            st.rerun()
                    with btn_full_col2:
                        if st.button(f"حذف 🗑️", key=f"delete_btn_{p['id']}", use_container_width=True):
                            delete_project(p['id'])
                            st.rerun()
                            
            st.write("---")
