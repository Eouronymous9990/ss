import streamlit as st
import pandas as pd
from datetime import date
import qrcode
from PIL import Image
from io import BytesIO
import plotly.express as px
import os
import time
import cv2
import numpy as np

class StudentAttendanceSystem:
    def __init__(self):
        st.set_page_config(page_title="نظام حضور الطلاب", layout="wide", page_icon="🎓")
        self.excel_path = "students_data.xlsx"
        self.load_data()
        self.setup_ui()
    
    def load_data(self):
        if os.path.exists(self.excel_path):
            self.df = pd.read_excel(self.excel_path)
            # توحيد أسماء الأعمدة
            self.df.columns = [
                'الكود',
                'الاسم', 
                'رقم_الهاتف',
                'ولي_الامر',
                'الحصص_الحاضرة',
                'الشهر_الأول',
                'الشهر_الثاني',
                'الشهر_الثالث', 
                'الشهر_الرابع',
                'الشهر_الخامس',
                'تاريخ_التسجيل',
                'ملاحظات',
                'الاختبارات'
            ]
            
            # تحويل أنواع البيانات
            self.df['الكود'] = self.df['الكود'].astype(str)
            self.df['رقم_الهاتف'] = self.df['رقم_الهاتف'].astype(str)
            self.df['ولي_الامر'] = self.df['ولي_الامر'].astype(str)
            
            if 'تاريخ_التسجيل' in self.df.columns:
                self.df['تاريخ_التسجيل'] = pd.to_datetime(self.df['تاريخ_التسجيل']).dt.date
                
            if 'الاختبارات' not in self.df.columns:
                self.df['الاختبارات'] = ''
        else:
            self.df = pd.DataFrame(columns=[
                'الكود',
                'الاسم', 
                'رقم_الهاتف',
                'ولي_الامر',
                'الحصص_الحاضرة',
                'الشهر_الأول',
                'الشهر_الثاني',
                'الشهر_الثالث', 
                'الشهر_الرابع',
                'الشهر_الخامس',
                'تاريخ_التسجيل',
                'ملاحظات',
                'الاختبارات'
            ])
    
    def save_data(self):
        df_to_save = self.df.copy()
        if 'تاريخ_التسجيل' in df_to_save.columns:
            df_to_save['تاريخ_التسجيل'] = df_to_save['تاريخ_التسجيل'].astype(str)
        df_to_save.to_excel(self.excel_path, index=False)
    
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
        </style>
        """, unsafe_allow_html=True)
        
        st.title("🎓 نظام حضور الطلاب")
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
        st.header("📷 تسجيل حضور الطالب")
        welcome_placeholder = st.empty()
        
        img_file = st.camera_input("امسح كود الطالب", key="qr_scanner")
        
        if img_file is not None:
            try:
                # محاولة استخدام OpenCV إذا فشل pyzbar
               
                
                # تحويل الصورة إلى مصفوفة numpy
                img = Image.open(img_file)
                frame = np.array(img)
                
                # تحويل إلى تدرج الرمادي
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # اكتشاف QR Code
                detector = cv2.QRCodeDetector()
                data, vertices, _ = detector.detectAndDecode(gray)
                
                if data:
                    self.process_student_attendance(data.strip(), welcome_placeholder)
                    return
                else:
                    st.warning("لم يتم التعرف على كود الطالب، حاول مرة أخرى")
                
        except Exception as e:
            st.error(f"خطأ في المسح: {str(e)}")
    
   
    
    def process_student_attendance(self, student_id, welcome_placeholder):
        if student_id in self.df['الكود'].values:
            student_row = self.df[self.df['الكود'] == student_id].iloc[0]
            
            # تحديث عدد الحصص
            self.df.loc[self.df['الكود'] == student_id, 'الحصص_الحاضرة'] += 1
            self.save_data()
            
            # عرض معلومات الطالب
            welcome_html = f"""
            <div class='welcome-message'>
                <div style='font-size: 48px;'>مرحباً</div>
                <div style='font-size: 56px;'>{student_row['الاسم']}</div>
                <div style='font-size: 24px; margin-top: 20px;'>
                    الحصص الحاضرة: <span style='color: #FFD700;'>{student_row['الحصص_الحاضرة']}</span>
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
                months = ['الشهر_الأول', 'الشهر_الثاني', 'الشهر_الثالث', 'الشهر_الرابع', 'الشهر_الخامس']
                months_paid = [month.replace('_', ' ') for month in months if student_row[month]]
                
                st.markdown(f"""
                - **الحصص الحاضرة**: {student_row['الحصص_الحاضرة']}
                - **الأشهر المدفوعة**: {', '.join(months_paid) if months_paid else 'لا يوجد'}
                """)
            
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
        st.header("➕ تسجيل طالب جديد")
        
        with st.form("student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                student_name = st.text_input("اسم الطالب بالكامل", placeholder="أدخل الاسم ثلاثي")
                student_id = st.text_input("كود الطالب", placeholder="رقم فريد لكل طالب")
                phone = st.text_input("رقم هاتف الطالب", placeholder="01012345678")
            
            with col2:
                parent_phone = st.text_input("رقم ولي الأمر", placeholder="01012345678")
                notes = st.text_area("ملاحظات إضافية")
            
            if st.form_submit_button("تسجيل الطالب"):
                if student_name and student_id:
                    if student_id in self.df['الكود'].values:
                        st.error("هذا الكود مسجل بالفعل لطالب آخر")
                    else:
                        qr_image = self.create_student(
                            student_id,
                            student_name,
                            phone,
                            parent_phone,
                            notes
                        )
                        
                        st.success("تم تسجيل الطالب بنجاح! ✅")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.image(qr_image, caption=f"كود الطالب {student_name}", width=300)
                        
                        with col2:
                            st.markdown(f"""
                            ### بيانات الطالب المسجل:
                            - **الاسم**: {student_name}
                            - **كود الطالب**: {student_id}
                            - **رقم الهاتف**: {phone}
                            - **ولي الأمر**: {parent_phone}
                            """)
                else:
                    st.error("الرجاء إدخال اسم الطالب وكود الطالب")
    
    def create_student(self, student_id, student_name, phone, parent_phone, notes):
        # إنشاء QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(student_id)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        img_bytes = BytesIO()
        qr_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # إضافة الطالب للبيانات
        new_row = pd.DataFrame({
            'الكود': [student_id],
            'الاسم': [student_name],
            'رقم_الهاتف': [phone],
            'ولي_الامر': [parent_phone],
            'الحصص_الحاضرة': [0],
            'الشهر_الأول': [False],
            'الشهر_الثاني': [False],
            'الشهر_الثالث': [False],
            'الشهر_الرابع': [False],
            'الشهر_الخامس': [False],
            'تاريخ_التسجيل': [date.today()],
            'ملاحظات': [notes],
            'الاختبارات': ['']
        })
        
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.save_data()
        
        return img_bytes
    
    def manage_students_tab(self):
        st.header("🔄 إدارة الطلاب")
        
        if not self.df.empty:
            # قسم البحث عن الطالب
            st.subheader("بحث عن الطالب")
            student_id = st.selectbox("اختر الطالب", self.df['الكود'].unique())
            
            if student_id:
                student_data = self.df[self.df['الكود'] == student_id]
                
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
                    tab1, tab2, tab3 = st.tabs(["الحضور", "الدفع", "الاختبارات"])
                    
                    with tab1:
                        st.subheader("إدارة الحضور")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("➕ تسجيل حضور إضافي"):
                                self.df.loc[self.df['الكود'] == student_id, 'الحصص_الحاضرة'] += 1
                                self.save_data()
                                st.success("تم تسجيل الحضور بنجاح!")
                                time.sleep(1)
                                st.rerun()
                        
                        with col2:
                            if st.button("➖ خصم حصة حضور"):
                                if student_row['الحصص_الحاضرة'] > 0:
                                    self.df.loc[self.df['الكود'] == student_id, 'الحصص_الحاضرة'] -= 1
                                    self.save_data()
                                    st.success("تم خصم الحصة بنجاح!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning("لا يمكن خصم حصة حيث أن عدد الحصص الحاضرة صفر")
                    
                    with tab2:
                        st.subheader("حالة الدفع للأشهر")
                        months = ['الشهر_الأول', 'الشهر_الثاني', 'الشهر_الثالث', 'الشهر_الرابع', 'الشهر_الخامس']
                        
                        cols = st.columns(5)
                        for i, month in enumerate(months):
                            with cols[i]:
                                current_status = student_row[month]
                                if st.button(f"{month.replace('_', ' ')} {'✅' if current_status else '❌'}", 
                                           key=f"month_{i}"):
                                    self.df.loc[self.df['الكود'] == student_id, month] = not current_status
                                    self.save_data()
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
                                
                                self.df.loc[self.df['الكود'] == student_id, 'الاختبارات'] = updated_tests
                                self.save_data()
                                st.success("تم إضافة نتيجة الاختبار بنجاح!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("الرجاء إدخال اسم الاختبار والدرجة")
                else:
                    st.warning("لا يوجد طالب بهذا الكود")
        else:
            st.warning("لا يوجد طلاب مسجلين بعد")
    
    def view_analytics_tab(self):
        st.header("📊 الإحصائيات")
        
        if not self.df.empty:
            st.subheader("📈 النظرة العامة")
            
            # عرض الإحصائيات الرئيسية
            total_students = len(self.df)
            total_attendance = self.df['الحصص_الحاضرة'].sum()
            avg_attendance = self.df['الحصص_الحاضرة'].mean()
            
            months = ['الشهر_الأول', 'الشهر_الثاني', 'الشهر_الثالث', 'الشهر_الرابع', 'الشهر_الخامس']
            total_paid_months = self.df[months].sum().sum()
            
            cols = st.columns(4)
            
            with cols[0]:
                st.markdown(f"""
                <div class='stats-card'>
                    <div style='font-size: 24px;'>{total_students}</div>
                    <div>إجمالي الطلاب</div>
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
            paid_counts = self.df[months].sum()
            
            fig = px.bar(
                x=[m.replace('_', ' ') for m in months],
                y=paid_counts.values,
                labels={'x': 'الشهر', 'y': 'عدد الطلاب الذين دفعوا'},
                color=paid_counts.values,
                color_continuous_scale='blugrn'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # عرض بيانات الطلاب
            st.subheader("بيانات جميع الطلاب")
            display_df = self.df.copy()
            display_df['الكود'] = display_df['الكود'].astype(str)
            st.dataframe(display_df, use_container_width=True)
            
            st.download_button(
                label="📥 تصدير البيانات لملف إكسل",
                data=self.df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'),
                file_name="students_data.csv",
                mime="text/csv"
            )
        else:
            st.warning("لا توجد بيانات متاحة للعرض")

if __name__ == "__main__":

    system = StudentAttendanceSystem()

