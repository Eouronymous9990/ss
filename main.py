import streamlit as st
import pandas as pd
import os
from datetime import date
from PIL import Image
import numpy as np
import cv2
import qrcode
from io import BytesIO
import time
import plotly.express as px

# تأكد من إضافة هذه الاستيرادات في الأعلى

class StudentAttendanceSystem:
    def __init__(self):
        st.set_page_config(page_title="نظام حضور الطلاب", layout="wide", page_icon="🎓")
        self.excel_path = "students_data.xlsx"
        self.current_group = None
        # تعريف أسماء الأشهر الجديدة
        self.months = [
            'يوليو_2025', 'أغسطس_2025', 'سبتمبر_2025', 'أكتوبر_2025', 
            'نوفمبر_2025', 'ديسمبر_2025', 'يناير_2026', 'فبراير_2026', 
            'مارس_2026', 'أبريل_2026', 'مايو_2026', 'يونيو_2026'
        ]
        
        # تحميل البيانات أولاً قبل إعداد الواجهة
        self.load_data()
        self.setup_ui()
    
    def load_data(self):
        if os.path.exists(self.excel_path):
            try:
                # قراءة جميع الأوراق من ملف الإكسل
                self.groups_df = pd.read_excel(self.excel_path, sheet_name=None)
                
                # إذا كان الملف فارغاً أو به مشاكل
                if not self.groups_df:
                    self.initialize_default_group()
                else:
                    # تصحيح الأعمدة إذا كان هناك خطأ إملائي
                    for group_name, df in self.groups_df.items():
                        if 'رقم_الهاتf' in df.columns and 'رقم_الهاتف' not in df.columns:
                            df.rename(columns={'رقم_الهاتf': 'رقم_الهاتف'}, inplace=True)
                    
                    # توحيد أسماء الأعمدة لكل مجموعة
                    for group_name, df in self.groups_df.items():
                        # إنشاء الأعمدة الأساسية
                        base_columns = [
                            'الكود',
                            'الاسم', 
                            'رقم_الهاتف',
                            'ولي_الامر',
                            'الحصص_الحاضرة',
                            'تواريخ_الحضور',
                            'تاريخ_التسجيل',
                            'ملاحظات',
                            'الاختبارات'
                        ]
                        
                        # إضافة أعمدة الأشهر
                        columns = base_columns[:5] + self.months + base_columns[5:]
                        
                        # إذا كان عدد الأعمدة مختلفاً، نقوم بإعادة تنظيم البيانات
                        if len(df.columns) != len(columns):
                            # حفظ البيانات الموجودة
                            existing_data = df.copy()
                            
                            # إنشاء DataFrame جديد بالأعمدة المحدثة
                            new_df = pd.DataFrame(columns=columns)
                            
                            # نسخ البيانات المتوافقة
                            for col in existing_data.columns:
                                if col in columns:
                                    new_df[col] = existing_data[col]
                            
                            # تعيين القيم الافتراضية للأعمدة الجديدة
                            for month in self.months:
                                if month not in new_df.columns:
                                    new_df[month] = False
                                    
                            if 'تواريخ_الحضور' not in new_df.columns:
                                new_df['تواريخ_الحضور'] = ''
                                
                            self.groups_df[group_name] = new_df
                        else:
                            # التأكد من أن الأعمدة مرتبة بشكل صحيح
                            self.groups_df[group_name] = df[columns]
                        
                        # تحويل أنواع البيانات
                        df = self.groups_df[group_name]
                        df['الكود'] = df['الكود'].astype(str)
                        df['رقم_الهاتف'] = df['رقم_الهاتف'].astype(str)
                        df['ولي_الامر'] = df['ولي_الامر'].astype(str)
                        
                        if 'تاريخ_التسجيل' in df.columns:
                            # تحويل التواريخ بشكل صحيح
                            df['تاريخ_التسجيل'] = pd.to_datetime(df['تاريخ_التسجيل'], errors='coerce').dt.date
                            
                        if 'الاختبارات' not in df.columns:
                            df['الاختبارات'] = ''
                            
                        if 'تواريخ_الحضور' not in df.columns:
                            df['تواريخ_الحضور'] = ''
                            
                        # التأكد من أن أعمدة الأشهر من النوع المنطقي
                        for month in self.months:
                            if month in df.columns:
                                # تحويل القيم النصية إلى منطقية إذا لزم الأمر
                                if df[month].dtype == 'object':
                                    df[month] = df[month].apply(lambda x: str(x).lower() in ['true', 'yes', '1', 'نعم', 'صحيح', '✅'])
                                df[month] = df[month].fillna(False).astype(bool)
                    
                    # تحديد المجموعة الحالية (استخدم الأولى إذا لم تكن محددة)
                    if self.current_group is None or self.current_group not in self.groups_df:
                        self.current_group = list(self.groups_df.keys())[0]
                        
            except Exception as e:
                st.error(f"حدث خطأ عند تحميل البيانات: {str(e)}")
                self.initialize_default_group()
        else:
            self.initialize_default_group()

    # ... باقي الكود بدون تغيير ...


    def initialize_default_group(self):
        # إنشاء الأعمدة الأساسية
        base_columns = [
            'الكود',
            'الاسم', 
            'رقم_الهاتف',
            'ولي_الامر',
            'الحصص_الحاضرة',
            'تواريخ_الحضور',
            'تاريخ_التسجيل',
            'ملاحظات',
            'الاختبارات'
        ]
        
        # إضافة أعمدة الأشهر
        columns = base_columns[:5] + self.months + base_columns[5:]
        
        self.groups_df = {
            "المجموعة_الافتراضية": pd.DataFrame(columns=columns)
        }
        self.current_group = "المجموعة_الافتراضية"
        self.save_data()
    
    def save_data(self):
        with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
            for group_name, df in self.groups_df.items():
                df_to_save = df.copy()
                if 'تاريخ_التسجيل' in df_to_save.columns:
                    df_to_save['تاريخ_التسجيل'] = df_to_save['تاريخ_التسجيل'].astype(str)
                df_to_save.to_excel(writer, sheet_name=group_name, index=False)
    
    def setup_ui(self):
        st.markdown("""
        <style>
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #FFFFFF !important;
            }
            .stTextInput>div>div>input, 
            .stTextArea>div>div>textarea, 
            .stSelectbox>div>div>select,
            .stNumberInput>div>div>input {
                color: #FFFFFF;
                background-color: #1E1E1E;
            }
            .stats-card {
                background: linear-gradient(135deg, #1E1E1E, #2A2A2A);
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                text-align: center;
                border-left: 4px solid #4CAF50;
            }
            .stDownloadButton>button {
                background-color: #4CAF50 !important;
                color: white !important;
                border: none;
                font-weight: bold;
            }
            .welcome-message {
                font-size: 42px !important;
                font-weight: bold !important;
                color: #4CAF50 !important;
                text-align: center;
                margin: 20px 0;
                text-shadow: 2px 2px 4px #000;
            }
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            .stTabs [role="tablist"] {
                background: #1E1E1E;
            }
            .dataframe {
                background-color: #1E1E1E !important;
                color: white !important;
            }
            .student-info {
                background-color: #1E1E1E;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .group-tabs {
                margin-bottom: 20px;
            }
            .month-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                margin-bottom: 20px;
            }
            .month-checkbox {
                background-color: #2A2A2A;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
            }
            .attendance-dates {
                max-height: 200px;
                overflow-y: auto;
                background-color: #2A2A2A;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("🎓 نظام حضور الطلاب")
        
        # إدارة المجموعات في الشريط الجانبي
        with st.sidebar:
            st.header("إدارة المجموعات")
            
            # عرض المجموعات الحالية
            current_groups = list(self.groups_df.keys())
            self.current_group = st.selectbox(
                "اختر المجموعة الحالية", 
                current_groups, 
                index=current_groups.index(self.current_group) if self.current_group in current_groups else 0
            )
            
            # إضافة مجموعة جديدة
            new_group_name = st.text_input("اسم المجموعة الجديدة")
            if st.button("➕ إضافة مجموعة") and new_group_name:
                if new_group_name not in self.groups_df:
                    # إنشاء الأعمدة الأساسية
                    base_columns = [
                        'الكود',
                        'الاسم', 
                        'رقم_الهاتف',
                        'ولي_الامر',
                        'الحصص_الحاضرة',
                        'تواريخ_الحضور',
                        'تاريخ_التسجيل',
                        'ملاحظات',
                        'الاختبارات'
                    ]
                    
                    # إضافة أعمدة الأشهر
                    columns = base_columns[:5] + self.months + base_columns[5:]
                    
                    self.groups_df[new_group_name] = pd.DataFrame(columns=columns)
                    self.save_data()
                    st.success(f"تم إنشاء المجموعة '{new_group_name}' بنجاح!")
                    st.rerun()
                else:
                    st.error("هذه المجموعة موجودة بالفعل!")
            
            # حذف مجموعة
            if len(self.groups_df) > 1:
                group_to_delete = st.selectbox("اختر مجموعة للحذف", current_groups)
                if st.button("🗑️ حذف المجموعة") and group_to_delete:
                    del self.groups_df[group_to_delete]
                    self.current_group = list(self.groups_df.keys())[0]
                    self.save_data()
                    st.success(f"تم حذف المجموعة '{group_to_delete}' بنجاح!")
                    st.rerun()
        
        # تبويبات الواجهة الرئيسية
        tabs = st.tabs(["📷 مسح حضور الطالب", "➕ تسجيل طالب جديد", "🔄 إدارة الطلاب", "📊 الإحصائيات"])
        
        with tabs[0]:
            self.scan_qr_tab()
        with tabs[1]:
            self.create_student_tab()
        with tabs[2]:
            self.manage_students_tab()
        with tabs[3]:
            self.view_analytics_tab()
            
    def scan_qr_tab(self):
        if self.current_group not in self.groups_df:
            st.warning("الرجاء اختيار مجموعة صالحة")
            return
            
        st.header(f"📷 تسجيل حضور الطالب - مجموعة {self.current_group}")
        welcome_placeholder = st.empty()
        
        # استخدام session state لتجنب المعالجة المكررة للصورة
        if 'last_processed_image' not in st.session_state:
            st.session_state.last_processed_image = None
        
        img_file = st.camera_input("امسح كود الطالب", key="qr_scanner")
        
        # إذا كانت هناك صورة جديدة ولم يتم معالجتها من قبل
        if img_file is not None and img_file != st.session_state.last_processed_image:
            st.session_state.last_processed_image = img_file
            
            try:
                img = Image.open(img_file)
                frame = np.array(img)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detector = cv2.QRCodeDetector()
                data, vertices, _ = detector.detectAndDecode(gray)
                
                if data:
                    self.process_student_attendance(data.strip(), welcome_placeholder)
                else:
                    st.warning("لم يتم التعرف على كود الطالب، حاول مرة أخرى")
            except Exception as e:
                st.error(f"خطأ في المسح: {str(e)}")
        
        # زر لمسح الصورة يدوياً إذا احتجنا
        if st.button("🗑️ مسح الصورة والبدء من جديد"):
            st.session_state.last_processed_image = None
            st.rerun()
    
    def process_student_attendance(self, student_id, welcome_placeholder):
        df = self.groups_df[self.current_group]
        
        if student_id in df['الكود'].values:
            student_row = df[df['الكود'] == student_id].iloc[0]
            
            # نتأكد إن الصورة هذه ما اتعملتش قبل كدة
            if f'last_attendance_{student_id}' not in st.session_state:
                st.session_state[f'last_attendance_{student_id}'] = None
            
            if st.session_state[f'last_attendance_{student_id}'] != st.session_state.last_processed_image:
                # تحديث عدد الحصص
                df.loc[df['الكود'] == student_id, 'الحصص_الحاضرة'] += 1
                
                # تسجيل تاريخ الحضور
                current_date = date.today().strftime("%Y-%m-%d")
                current_presence = student_row['تواريخ_الحضور'] if pd.notna(student_row['تواريخ_الحضور']) else ""
                
                if current_presence:
                    new_presence = f"{current_presence}; {current_date}"
                else:
                    new_presence = current_date
                    
                df.loc[df['الكود'] == student_id, 'تواريخ_الحضور'] = new_presence
                
                self.groups_df[self.current_group] = df
                self.save_data()
                
                st.session_state[f'last_attendance_{student_id}'] = st.session_state.last_processed_image
            
            # عرض معلومات الطالب
            welcome_html = f"""
            <div class='welcome-message'>
                <div style='font-size: 48px;'>مرحباً</div>
                <div style='font-size: 56px;'>{student_row['الاسم']}</div>
                <div style='font-size: 24px; margin-top: 20px;'>
                    الحصص الحاضرة: <span style='color: #FFD700;'>{int(student_row['الحصص_الحاضرة']) + 1}</span>
                </div>
            </div>
            """
            welcome_placeholder.markdown(welcome_html, unsafe_allow_html=True)
            
            # عرض تفاصيل الطالب
            st.markdown('<div class="student-info">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### المعلومات الشخصية")
                st.markdown(f"""
                - **الكود**: {student_row['الكود']}
                - **الاسم**: {student_row['الاسم']}
                - **رقم الهاتف**: {student_row['رقم_الهاتف']}
                - **ولي الأمر**: {student_row['ولي_الامر']}
                - **تاريخ التسجيل**: {student_row['تاريخ_التسجيل']}
                """)
                
            with col2:
                st.markdown("### الحضور والدفع")
                months_paid = [month for month in self.months if student_row[month]]
                months_display = [month.replace('_', ' ') for month in months_paid]
                
                st.markdown(f"""
                - **الحصص الحاضرة**: {int(student_row['الحصص_الحاضرة']) + 1}
                - **الأشهر المدفوعة**: {', '.join(months_display) if months_paid else 'لا يوجد'}
                """)
            
            # عرض تواريخ الحضور
            if pd.notna(student_row['تواريخ_الحضور']) and student_row['تواريخ_الحضور'] != '':
                st.markdown("### تواريخ الحضور")
                dates = student_row['تواريخ_الحضور'].split(';')
                st.markdown('<div class="attendance-dates">', unsafe_allow_html=True)
                for i, date_str in enumerate(dates, 1):
                    if date_str.strip():
                        st.markdown(f"- الحصة {i}: {date_str.strip()}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # عرض نتائج الاختبارات
            if pd.notna(student_row['الاختبارات']) and student_row['الاختبارات'] != '':
                st.markdown("### نتائج الاختبارات")
                tests = student_row['الاختبارات'].split(';')
                for test in tests:
                    if test.strip():
                        st.markdown(f"- {test.strip()}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            welcome_placeholder.error("❌ كود الطالب غير مسجل في النظام")
    
    def create_student_tab(self):
        st.header(f"➕ تسجيل طالب جديد - مجموعة {self.current_group}")
        
        with st.form("student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                student_name = st.text_input("اسم الطالب بالكامل", placeholder="أدخل الاسم ثلاثي")
                student_id = st.text_input("كود الطالب", placeholder="رقم فريد لكل طالب")
                phone = st.text_input("رقم هاتف الطالب", placeholder="01012345678")
            
            with col2:
                parent_phone = st.text_input("رقم ولي الأمر", placeholder="01012345678")
                registration_date = st.date_input("تاريخ التسجيل", value=date.today())
                notes = st.text_area("ملاحظات إضافية")
            
            # تحديد الشهر الحالي بناءً على تاريخ التسجيل
            current_month = None
            if registration_date:
                # تحويل التاريخ إلى تنسيق الشهر المتوافق مع أسماء الأشهر
                month_num = registration_date.month
                year = registration_date.year
                
                # إنشاء قائمة بالأشهر مع سنواتها الصحيحة
                months_mapping = {
                    7: 'يوليو_2025', 8: 'أغسطس_2025', 9: 'سبتمبر_2025', 
                    10: 'أكتوبر_2025', 11: 'نوفمبر_2025', 12: 'ديسمبر_2025',
                    1: 'يناير_2026', 2: 'فبراير_2026', 3: 'مارس_2026', 
                    4: 'أبريل_2026', 5: 'مايو_2026', 6: 'يونيو_2026'
                }
                
                current_month = months_mapping.get(month_num)
            
            # إظهار حالة الدفع (الكل غير مدفوع باستثناء شهر التسجيل)
            st.subheader("حالة الدفع للأشهر")
            if current_month:
                st.info(f"سيتم تحديد شهر {current_month.replace('_', ' ')} تلقائياً كمدفوع بناءً على تاريخ التسجيل")
            
            if st.form_submit_button("تسجيل الطالب"):
                if student_name and student_id:
                    if student_id in self.groups_df[self.current_group]['الكود'].values:
                        st.error("هذا الكود مسجل بالفعل لطالب آخر")
                    else:
                        # إنشاء حالة الدفع (الكل غير مدفوع باستثناء شهر التسجيل)
                        month_status = {}
                        for month in self.months:
                            month_status[month] = (month == current_month)
                        
                        qr_image = self.create_student(
                            student_id,
                            student_name,
                            phone,
                            parent_phone,
                            registration_date,
                            notes,
                            month_status
                        )
                        
                        st.success("تم تسجيل الطالب بنجاح! ✅")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(qr_image, caption=f"كود الطالب {student_name}", width=300)
                        
                        with col2:
                            months_paid = [m.replace('_', ' ') for m, paid in month_status.items() if paid]
                            st.markdown(f"""
                            ### بيانات الطالب المسجل:
                            - **الاسم**: {student_name}
                            - **كود الطالب**: {student_id}
                            - **رقم الهاتف**: {phone}
                            - **ولي الأمر**: {parent_phone}
                            - **تاريخ التسجيل**: {registration_date}
                            - **الشهر المدفوع**: {', '.join(months_paid) if months_paid else 'لا يوجد'}
                            """)
                else:
                    st.error("الرجاء إدخال اسم الطالب وكود الطالب")
    
    def create_student(self, student_id, student_name, phone, parent_phone, registration_date, notes, month_status):
        # إنشاء QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(student_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        img_bytes = BytesIO()
        qr_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # إعداد حالة الدفع للأشهر
        payment_status = {}
        for month in self.months:
            payment_status[month] = month_status.get(month, False)
        
        # إضافة الطالب للبيانات
        new_row_data = {
            'الكود': student_id,
            'الاسم': student_name,
            'رقم_الهاتف': phone,
            'ولي_الامر': parent_phone,
            'الحصص_الحاضرة': 0,
            'تواريخ_الحضور': '',
            'تاريخ_التسجيل': registration_date,
            'ملاحظات': notes,
            'الاختبارات': ''
        }
        
        # إضافة حالة الدفع لكل شهر
        for month in self.months:
            new_row_data[month] = payment_status[month]
        
        new_row = pd.DataFrame([new_row_data])
        
        # التأكد من أن البيانات الجديدة تحتوي على جميع الأعمدة المطلوبة
        for col in self.groups_df[self.current_group].columns:
            if col not in new_row.columns:
                new_row[col] = False if col in self.months else ''
        
        self.groups_df[self.current_group] = pd.concat(
            [self.groups_df[self.current_group], new_row], 
            ignore_index=True
        )
        self.save_data()
        
        return img_bytes
    
    def search_students(self, query, search_by="name"):
        df = self.groups_df[self.current_group]
        
        if search_by == "name":
            # البحث بأسماء الطلاب مع الاقتراحات
            all_names = df['الاسم'].dropna().unique()
            matches = [name for name in all_names if query.lower() in name.lower()]
            return matches
        else:
            # البحث بأكواد الطلاب مع الاقتراحات
            all_codes = df['الكود'].dropna().unique().astype(str)
            matches = [code for code in all_codes if query.lower() in code.lower()]
            return matches
    
    def generate_qr_code(self, student_id):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(student_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        img_bytes = BytesIO()
        qr_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        return img_bytes
    
    def manage_students_tab(self):
        st.header(f"🔄 إدارة الطلاب - مجموعة {self.current_group}")
        
        df = self.groups_df[self.current_group]
        
        if not df.empty:
            # قسم البحث عن الطالب
            st.subheader("بحث عن الطالب")
            
            # خيارات البحث: بالكود أو بالاسم مع البحث الذكي
            search_option = st.radio("ابحث باستخدام:", ["الكود", "الاسم"], horizontal=True, key="manage_search")
            
            student_data = pd.DataFrame()
            
            if search_option == "الكود":
                search_query = st.text_input("اكتب كود الطالب", key="code_search_manage")
                if search_query:
                    suggestions = self.search_students(search_query, "code")
                    if suggestions:
                        selected_code = st.selectbox("الاقتراحات", suggestions, key="code_suggestions_manage")
                        student_data = df[df['الكود'] == selected_code] if selected_code else pd.DataFrame()
            else:
                search_query = st.text_input("اكتب اسم الطالب", key="name_search_manage")
                if search_query:
                    suggestions = self.search_students(search_query, "name")
                    if suggestions:
                        selected_name = st.selectbox("الاقتراحات", suggestions, key="name_suggestions_manage")
                        student_data = df[df['الاسم'] == selected_name] if selected_name else pd.DataFrame()
            
            if not student_data.empty:
                student_row = student_data.iloc[0]
                
                # عرض بيانات الطالب
                st.markdown('<div class="student-info">', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### المعلومات الشخصية")
                    st.markdown(f"""
                    - **الكود**: {student_row['الكود']}
                    - **الاسم**: {student_row['الاسم']}
                    - **رقم الهاتف**: {student_row['رقم_الهاتف']}
                    """)
                
                with col2:
                    st.markdown("### الحضور والدفع")
                    st.markdown(f"""
                    - **ولي الأمر**: {student_row['ولي_الامر']}
                    - **تاريخ التسجيل**: {student_row['تاريخ_التسجيل']}
                    - **الحصص الحاضرة**: {student_row['الحصص_الحاضرة']}
                    """)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # قسم إدارة الحضور والدفع والاختبارات
                tab1, tab2, tab3, tab4 = st.tabs(["الحضور", "الدفع", "الاختبارات", "استرجاع QR Code"])
                
                with tab1:
                    st.subheader("إدارة الحضور")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("➕ تسجيل حضور إضافي"):
                            df.loc[df['الكود'] == student_row['الكود'], 'الحصص_الحاضرة'] += 1
                            
                            # تسجيل تاريخ الحضور
                            current_date = date.today().strftime("%Y-%m-%d")
                            current_presence = student_row['تواريخ_الحضور'] if pd.notna(student_row['تواريخ_الحضور']) else ""
                            
                            if current_presence:
                                new_presence = f"{current_presence}; {current_date}"
                            else:
                                new_presence = current_date
                                
                            df.loc[df['الكود'] == student_row['الكود'], 'تواريخ_الحضور'] = new_presence
                            
                            self.groups_df[self.current_group] = df
                            self.save_data()
                            st.success("تم تسجيل الحضور بنجاح!")
                            time.sleep(1)
                            st.rerun()
                    
                    with col2:
                        if st.button("➖ خصم حصة حضور"):
                            if student_row['الحصص_الحاضرة'] > 0:
                                df.loc[df['الكود'] == student_row['الكود'], 'الحصص_الحاضرة'] -= 1
                                
                                # إزالة آخر تاريخ حضور
                                if pd.notna(student_row['تواريخ_الحضور']) and student_row['تواريخ_الحضور'] != '':
                                    dates = student_row['تواريخ_الحضور'].split(';')
                                    if len(dates) > 1:
                                        new_dates = ';'.join(dates[:-1])
                                    else:
                                        new_dates = ''
                                    df.loc[df['الكود'] == student_row['الكود'], 'تواريخ_الحضور'] = new_dates
                                
                                self.groups_df[self.current_group] = df
                                self.save_data()
                                st.success("تم خصم الحصة بنجاح!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("لا يمكن خصم حصة حيث أن عدد الحصص الحاضرة صفر")
                
                with tab2:
                    st.subheader("حالة الدفع للأشهر")
                    
                    # استخدام نموذج لتحديث حالة الدفع
                    with st.form(f"payment_form_{student_row['الكود']}"):
                        st.write("حدد الأشهر المدفوعة:")
                        
                        # إنشاء شبكة من الخانات لجميع الأشهر
                        cols = st.columns(4)
                        updated_payment_status = {}
                        
                        for i, month in enumerate(self.months):
                            with cols[i % 4]:
                                current_status = bool(student_row[month])
                                updated_payment_status[month] = st.checkbox(
                                    month.replace('_', ' '), 
                                    value=current_status,
                                    key=f"pay_{month}_{student_row['الكود']}"
                                )
                        
                        if st.form_submit_button("حفظ حالة الدفع"):
                            for month in self.months:
                                df.loc[df['الكود'] == student_row['الكود'], month] = updated_payment_status[month]
                            
                            self.groups_df[self.current_group] = df
                            self.save_data()
                            st.success("تم تحديث حالة الدفع بنجاح!")
                            time.sleep(1)
                            st.rerun()
                
                with tab3:
                    st.subheader("إدارة الاختبارات")
                    
                    # عرض الاختبارات الحالية
                    if pd.notna(student_row['الاختبارات']) and student_row['الاختبارات'] != '':
                        st.markdown("#### نتائج الاختبارات الحالية")
                        tests = student_row['الاختبارات'].split(';')
                        for test in tests:
                            if test.strip():
                                st.markdown(f"- {test.strip()}")
                    
                    # إضافة اختبار جديد
                    st.markdown("#### إضافة اختبار جديد")
                    test_name = st.text_input("اسم الاختبار", key="test_name")
                    test_score = st.text_input("الدرجة", key="test_score")
                    
                    if st.button("إضافة نتيجة الاختبار"):
                        if test_name and test_score:
                            new_test = f"{test_name}: {test_score}"
                            current_tests = student_row['الاختبارات']
                            
                            if pd.isna(current_tests) or current_tests == '':
                                updated_tests = new_test
                            else:
                                updated_tests = f"{current_tests}; {new_test}"
                            
                            df.loc[df['الكود'] == student_row['الكود'], 'الاختبارات'] = updated_tests
                            self.groups_df[self.current_group] = df
                            self.save_data()
                            st.success("تم إضافة نتيجة الاختبار بنجاح!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("الرجاء إدخال اسم الاختبار والدرجة")
                
                with tab4:
                    st.subheader("استرجاع QR Code للطالب")
                    
                    if st.button("🎫 إنشاء QR Code"):
                        qr_img = self.generate_qr_code(student_row['الكود'])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(qr_img, caption=f"كود الطالب {student_row['الاسم']}", width=300)
                        with col2:
                            # تحويل الصورة إلى bytes للتحميل
                            img_bytes = BytesIO()
                            Image.open(qr_img).save(img_bytes, format="PNG")
                            img_bytes.seek(0)
                            
                            st.download_button(
                                label="📥 تحميل QR Code",
                                data=img_bytes,
                                file_name=f"qr_code_{student_row['الكود']}.png",
                                mime="image/png"
                            )
            else:
                if search_query:
                    st.warning("لا يوجد طالب بهذا البحث")
        else:
            st.warning("لا يوجد طلاب مسجلين بعد")
    
    def view_analytics_tab(self):
        st.header("📊 الإحصائيات")
        
        # إنشاء تبويبات لكل مجموعة
        group_tabs = st.tabs([f"{group_name}" for group_name in self.groups_df.keys()])
        
        for i, (group_name, df) in enumerate(self.groups_df.items()):
            with group_tabs[i]:
                st.subheader(f"إحصائيات مجموعة {group_name}")
                
                if not df.empty:
                    # قسم منفصل للبحث عن طالب معين
                    st.markdown("---")
                    st.subheader("🔍 البحث عن طالب معين")
                    
                    # خيارات البحث: بالكود أو بالاسم مع البحث الذكي
                    search_option = st.radio(f"ابحث باستخدام في {group_name}:", ["الكود", "الاسم"], horizontal=True, key=f"search_{group_name}")
                    
                    student_data = pd.DataFrame()
                    
                    if search_option == "الكود":
                        search_query = st.text_input("اكتب كود الطالب", key=f"code_search_{group_name}")
                        if search_query:
                            suggestions = self.search_students(search_query, "code")
                            if suggestions:
                                selected_code = st.selectbox("الاقتراحات", suggestions, key=f"code_suggestions_{group_name}")
                                student_data = df[df['الكود'] == selected_code] if selected_code else pd.DataFrame()
                    else:
                        search_query = st.text_input("اكتب اسم الطالب", key=f"name_search_{group_name}")
                        if search_query:
                            suggestions = self.search_students(search_query, "name")
                            if suggestions:
                                selected_name = st.selectbox("الاقتراحات", suggestions, key=f"name_suggestions_{group_name}")
                                student_data = df[df['الاسم'] == selected_name] if selected_name else pd.DataFrame()
                    
                    if not student_data.empty:
                        student_row = student_data.iloc[0]
                        
                        st.markdown("### بيانات الطالب المفصلة")
                        st.markdown('<div class="student-info">', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### المعلومات الشخصية")
                            st.markdown(f"""
                            - **الكود**: {student_row['الكود']}
                            - **الاسم**: {student_row['الاسم']}
                            - **رقم الهاتف**: {student_row['رقم_الهاتف']}
                            - **ولي الأمر**: {student_row['ولي_الامر']}
                            - **تاريخ التسجيل**: {student_row['تاريخ_التسجيل']}
                            - **الحصص الحاضرة**: {student_row['الحصص_الحاضرة']}
                            """)
                        
                        with col2:
                            st.markdown("#### حالة الدفع للأشهر")
                            months_paid = [month for month in self.months if student_row[month]]
                            months_not_paid = [month for month in self.months if not student_row[month]]
                            
                            st.markdown("**الأشهر المدفوعة:**")
                            for month in months_paid:
                                st.markdown(f"- {month.replace('_', ' ')} ✅")
                            
                            if months_not_paid:
                                st.markdown("**الأشهر غير المدفوعة:**")
                                for month in months_not_paid:
                                    st.markdown(f"- {month.replace('_', ' ')} ❌")
                        
                        # عرض تواريخ الحضور
                        if pd.notna(student_row['تواريخ_الحضور']) and student_row['تواريخ_الحضور'] != '':
                            st.markdown("#### تواريخ الحضور")
                            dates = student_row['تواريخ_الحضور'].split(';')
                            st.markdown('<div class="attendance-dates">', unsafe_allow_html=True)
                            for i, date_str in enumerate(dates, 1):
                                if date_str.strip():
                                    st.markdown(f"- الحصة {i}: {date_str.strip()}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # عرض نتائج الاختبارات
                        if pd.notna(student_row['الاختبارات']) and student_row['الاختبارات'] != '':
                            st.markdown("#### نتائج الاختبارات")
                            tests = student_row['الاختبارات'].split(';')
                            for test in tests:
                                if test.strip():
                                    st.markdown(f"- {test.strip()}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # قسم منفصل لإحصائيات المجموعة ككل
                    st.markdown("---")
                    st.subheader("📈 إحصائيات المجموعة كاملة")
                    
                    total_students = len(df)
                    total_attendance = df['الحصص_الحاضرة'].sum()
                    avg_attendance = df['الحصص_الحاضرة'].mean()
                    total_paid_months = df[self.months].sum().sum()
                    
                    cols = st.columns(4)
                    
                    with cols[0]:
                        st.markdown(f"""
                        <div class='stats-card'>
                            <div style='font-size: 24px;'>{total_students}</div>
                            <div>عدد الطلاب</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[1]:
                        st.markdown(f"""
                        <div class='stats-card'>
                            <div style='font-size: 24px;'>{total_attendance}</div>
                            <div>إجمالي الحصص الحاضرة</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[2]:
                        st.markdown(f"""
                        <div class='stats-card'>
                            <div style='font-size: 24px;'>{avg_attendance:.1f}</div>
                            <div>متوسط الحضور لكل طالب</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with cols[3]:
                        st.markdown(f"""
                        <div class='stats-card'>
                            <div style='font-size: 24px;'>{total_paid_months}</div>
                            <div>إجمالي الأشهر المدفوعة</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # مخطط حالات الدفع
                    st.subheader("حالات الدفع للأشهر")
                    paid_counts = df[self.months].sum()
                    
                    fig = px.bar(
                        x=[m.replace('_', ' ') for m in self.months],
                        y=paid_counts.values,
                        labels={'x': 'الشهر', 'y': 'عدد الطلاب الذين دفعوا'},
                        color=paid_counts.values,
                        color_continuous_scale='blugrn'
                    )
                    st.plotly_chart(fig, use_container_width=True, key=f"plotly_{group_name}_{i}")
                    
                    # عرض بيانات الطلاب
                    st.subheader("بيانات جميع الطلاب")
                    display_df = df.copy()
                    display_df['الكود'] = display_df['الكود'].astype(str)
                    
                    # تحويل قيم الأشهر المنطقية إلى نص
                    for month in self.months:
                        display_df[month] = display_df[month].map({True: '✅ مدفوع', False: '❌ غير مدفوع'})
                    
                    st.dataframe(display_df, use_container_width=True)
                    
                    st.download_button(
                        label=f"📥 تصدير بيانات {group_name} لملف إكسل",
                        data=df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                        file_name=f"students_data_{group_name}.csv",
                        mime="text/csv",
                        key=f"export_{group_name}"
                    )
                else:
                    st.warning("لا توجد بيانات متاحة للعرض في هذه المجموعة")

if __name__ == "__main__":
    system = StudentAttendanceSystem()

