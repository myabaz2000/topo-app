import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# إعدادات الصفحة العامة
st.set_page_config(page_title="نظام تتبع مشاريع الطبوغرافيا", layout="wide")

# إجبار المتصفح على عرض القوائم والكتابة من اليمين إلى اليسار (RTL) بشكل احترافي
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=400;700&display=swap');
    html, body, [data-testid="stSidebar"], .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
    }
    div.stButton > button:first-child {
        background-color: #ff6e40;
        color: white;
        border-radius: 8px;
        width: 100%;
    }
    .stButton button[key^="del_"] {
        background-color: #d63031 !important;
        color: white !important;
    }
    .stButton button[key^="edit_"] {
        background-color: #2f3542 !important;
        color: white !important;
    }
    .stDownloadButton button {
        background-color: #2ecc71 !important;
        color: white !important;
        border-radius: 8px;
        width: 100%;
    }
    h1, h2, h3, h4 {
        color: #1e3d59;
    }
    input, select, textarea {
        direction: rtl !important;
        text-align: right !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- إعداد قاعدة البيانات (SQLite) -----------------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            phone TEXT,
            address TEXT NOT NULL,
            land_type TEXT,
            survey_date TEXT,
            price REAL,
            paid REAL,
            delivered INTEGER DEFAULT 0,
            delivery_date TEXT DEFAULT '-'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_all_projects():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df.to_dict(orient='records')

def add_project(client, phone, address, land_type, survey_date, price, paid):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (client, phone, address, land_type, survey_date, price, paid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (client, phone, address, land_type, str(survey_date), price, paid))
    conn.commit()
    conn.close()

def update_project_info(p_id, client, phone, address, land_type):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE projects 
        SET client = ?, phone = ?, address = ?, land_type = ? 
        WHERE id = ?
    ''', (client, phone, address, land_type, p_id))
    conn.commit()
    conn.close()

def update_delivery(p_id, date_str):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET delivered = 1, delivery_date = ? WHERE id = ?", (date_str, p_id))
    conn.commit()
    conn.close()

def update_payment(p_id, new_paid):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE projects SET paid = ? WHERE id = ?", (new_paid, p_id))
    conn.commit()
    conn.close()

def delete_project(p_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (p_id,))
    conn.commit()
    conn.close()

# ----------------- نظام المستخدم الموحد -----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'edit_project_id' not in st.session_state:
    st.session_state.edit_project_id = None

def login():
    st.title("برنامج مشاريع المسح الطبوغرافي")
    st.subheader("الرجاء تسجيل الدخول للوصول إلى قاعدة البيانات")
    
    with st.form("login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة السر", type="password")
        login_btn = st.form_submit_button("تسجيل الدخول")
        
        if login_btn:
            if username == "المسح الطبوغرافي" and password == "topo2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة!")

if not st.session_state.logged_in:
    login()
    st.stop()

# ----------------- واجهة التطبيق الرئيسية -----------------

if st.sidebar.button("تسجيل الخروج 🚪"):
    st.session_state.logged_in = False
    st.session_state.edit_project_id = None
    st.rerun()

st.title("بوابة إدارة المهام الطبوغرافية والتصاميم")
st.subheader("تنظيم العمل المشترك والمتابعة المالية بقاعدة بيانات آمنة")
st.write("---")

projects_list = get_all_projects()

if projects_list:
    df_excel = pd.DataFrame(projects_list)
    df_excel.columns = ['المعرف', 'اسم الزبون', 'رقم الهاتف', 'الموقع/العنوان', 'نوع الأرض', 'تاريخ القياس', 'الثمن الكلي', 'المبلغ المدفوع', 'حالة التسليم (1=نعم)', 'تاريخ التسليم']
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='المشاريع الطبوغرافية')
        workbook = writer.book
        worksheet = workbook.active
        worksheet.views.sheetView[0].showGridLines = True
        worksheet.sheet_properties.pageSetUpPr.fitToPage = True
        worksheet.sheet_view.rightToLeft = True

    st.sidebar.markdown("### 📊 التقارير المادية")
    st.sidebar.download_button(
        label="تحميل تقرير المشاريع كـ Excel 📂",
        data=buffer.getvalue(),
        file_name=f"تقرير_المشاريع_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

col1, col2 = st.columns([1, 2])

with col1:
    if st.session_state.edit_project_id is not None:
        target_project = next((p for p in projects_list if p['id'] == st.session_state.edit_project_id), None)
        if target_project:
            st.header("✏️ تعديل معلومات الملف")
            with st.form("edit_project_form"):
                edit_client = st.text_input("اسم الزبون *", value=target_project['client'])
                edit_phone = st.text_input("رقم الهاتف", value=target_project['phone'])
                edit_addr = st.text_input("عنوان المشروع / الموقع *", value=target_project['address'])
                
                land_types = ["تحفيظ (Titre)", "ملك غير محفظ (Melk)", "أرض سلالية", "ملحق / زينة", "أخرى"]
                default_idx = land_types.index(target_project['land_type']) if target_project['land_type'] in land_types else 0
                edit_land = st.selectbox("نوع البقعة الأرضية", land_types, index=default_idx)
                
                sub_save = st.form_submit_button("حفظ التعديلات الجديدة 💾")
                sub_cancel = st.form_submit_button("إلغاء التعديل ❌")
                
                if sub_save:
                    if edit_client and edit_addr:
                        update_project_info(target_project['id'], edit_client, edit_phone, edit_addr, edit_land)
                        st.session_state.edit_project_id = None
                        st.success("تم تحديث بيانات الزبون بنجاح!")
                        st.rerun()
                    else:
                        st.error("الرجاء ملء الخانات الأساسية")
                if sub_cancel:
                    st.session_state.edit_project_id = None
                    st.rerun()
    else:
        st.header("📝 إدخال طلب قياس جديد")
        with st.form("new_project_form", clear_on_submit=True):
            client_name = st.text_input("اسم صاحب القياس / الزبون *")
            phone_num = st.text_input("رقم الهاتف")
            project_addr = st.text_input("عنوان المشروع / الموقع *")
            land_type = st.selectbox("نوع البقعة الأرضية", ["تحفيظ (Titre)", "ملك غير محفظ (Melk)", "أرض سلالية", "ملحق / زينة", "أخرى"])
            survey_date = st.date_input("تاريخ أخذ القياسات (حمزة)", datetime.now())
            price = st.number_input("ثمن القياس المتفق عليه (درهم)", min_value=0.0, step=100.0)
            initial_pay = st.number_input("الدَفعة الأولى / التسبيق (درهم)", min_value=0.0, step=100.0)
            
            submit_btn = st.form_submit_button("حفظ في قاعدة البيانات 💾")
            
            if submit_btn:
                if client_name and project_addr:
                    add_project(client_name, phone_num, project_addr, land_type, survey_date, price, initial_pay)
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()
                else:
                    st.error("الرجاء ملء الخانات الأساسية (الاسم والعنوان)")

with col2:
    st.header("📊 برنامج تتبع ملفات المسح  الطوبوغرافي")
    filter_option = st.radio("تصفية التصاميم حسب حالة التسليم:", ["عرض الكل", "التصاميم المسلمة", "التصاميم غير المسلمة"], horizontal=True)
    
    if filter_option == "التصاميم المسلمة ":
        filtered_list = [p for p in projects_list if p['delivered'] == 1]
    elif filter_option == "التصاميم غير المسلمة ":
        filtered_list = [p for p in projects_list if p['delivered'] == 0]
    else:
        filtered_list = projects_list
        
    st.write("")
    if not filtered_list:
        st.info("لا توجد ملفات مسجلة في هذا القسم حالياً.")
    
    for p in filtered_list:
        reste = p['price'] - p['paid']
        status_color = "#2ecc71" if p['delivered'] == 1 else "#e74c3c"
        status_text = f"🟢 مُسلّم في ({p['delivery_date']})" if p['delivered'] == 1 else "🔴 غير مُسلم بعد"
        
        with st.container():
            st.markdown(f"""
            <div style="border: 1px solid #dcdde1; padding: 15px; border-radius: 10px; margin-bottom: 15px; background-color: #f8f9fa; border-right: 6px solid {status_color}; text-align: right;">
                <h4>👤 الزبون: {p['client']} | <span style="font-size: 14px; color: {status_color};">{status_text}</span></h4>
                <p style="margin: 5px 0;">📞 <b>الهاتف:</b> {p['phone'] if p['phone'] else 'غير مسجل'} | 🏷️ <b>نوع الأرض:</b> {p['land_type']}</p>
                <p style="margin: 5px 0;">📍 <b>الموقع:</b> {p['address']} | 📅 <b>تاريخ القياس:</b> {p['survey_date']}</p>
                <p style="margin: 5px 0; color: #1e3d59;">💰 <b>الثمن:</b> {p['price']} درهم | 💵 <b>المدفوع:</b> {p['paid']} درهم | ⚠️ <b>الباقي:</b> <span style="color:#e74c3c; font-weight:bold;">{reste} درهم</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            sub_col1, sub_col2, sub_col3, sub_col4 = st.columns([1.2, 1.2, 1, 1])
            
            with sub_col1:
                if p['delivered'] == 0:
                    if st.button(f"تسليم ✔️", key=f"del_{p['id']}"):
                        today_str = str(datetime.now().strftime("%Y-%m-%d"))
                        update_delivery(p['id'], today_str)
                        st.rerun()
                        
            with sub_col2:
                if reste > 0:
                    add_pay = st.number_input(f"إضافة تسديد", min_value=0.0, max_value=reste, step=100.0, key=f"pay_val_{p['id']}")
                    if st.button(f"تحديث 💵", key=f"pay_btn_{p['id']}"):
                        update_payment(p['id'], p['paid'] + add_pay)
                        st.rerun()
                        
            with sub_col3:
                if st.button(f"تعديل ✏️", key=f"edit_btn_{p['id']}"):
                    st.session_state.edit_project_id = p['id']
                    st.rerun()
                        
            with sub_col4:
                if st.button(f"حذف 🗑️", key=f"delete_btn_{p['id']}"):
                    delete_project(p['id'])
                    st.rerun()
                    
            st.write("---")
