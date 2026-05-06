import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
import plotly.express as px
import base64


if 'grades_data' not in st.session_state:
    st.session_state.grades_data = []
if 'students' not in st.session_state:
    st.session_state.students = {}


def init_database():
    conn = sqlite3.connect('grades.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS grades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id TEXT,
                  student_name TEXT,
                  subject TEXT,
                  assignment TEXT,
                  score REAL,
                  max_score REAL,
                  date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id TEXT UNIQUE,
                  student_name TEXT)''')
    conn.commit()
    conn.close()

init_database()


st.set_page_config(
    page_title="Advanced Grading System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
    :root {
        --primary: #00f5ff;
        --secondary: #8a2be2;
        --background: #0e1117;
        --card: #1a1c24;
        --text: #e0e0e0;
    }
    .stApp { background-color: var(--background); color: var(--text); }
    h1, h2, h3, h4, h5, h6 { color: var(--primary) !important; text-shadow: 0 0 10px var(--primary); }
    .stButton>button {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        border: 1px solid var(--primary);
        border-radius: 5px;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: linear-gradient(90deg, #1a1c24, #0d0f15); border-bottom: 2px solid #00f5ff; margin-bottom: 20px;">
        <h1>Advanced Grading System</h1>
        <div style="font-size: 14px; color: #00f5ff;">
            <span>QUANTUM ANALYTICS v2.0</span>
        </div>
    </div>
""", unsafe_allow_html=True)

PAGES = ["Dashboard", "Add Grade", "View Grades", "Reports", "Export Data"]

if 'page_index' not in st.session_state:
    st.session_state.page_index = 0

page = st.sidebar.selectbox(
    "SELECT MODULE",
    PAGES,
    index=st.session_state.page_index,
    key="sidebar_page"
)
st.session_state.page_index = PAGES.index(page)


conn = sqlite3.connect('grades.db')
c = conn.cursor()


if page == "Dashboard":
    st.subheader("SYSTEM DASHBOARD")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Students",
                  len(set([g['Student ID'] for g in st.session_state.grades_data])) if st.session_state.grades_data else 0)
    with col2:
        st.metric("Total Grades", len(st.session_state.grades_data))
    with col3:
        if st.session_state.grades_data:
            avg_score = np.mean([grade['Score'] for grade in st.session_state.grades_data])
            st.metric("Average Score", f"{avg_score:.2f}%")
        else:
            st.metric("Average Score", "0%")


elif page == "Add Grade":
    st.subheader("ADD NEW GRADE")
    with st.form("grade_form"):
        col1, col2 = st.columns(2)
        with col1:
            student_id = st.text_input("STUDENT ID")
            student_name = st.text_input("STUDENT NAME")
            subject = st.text_input("SUBJECT")
        with col2:
            assignment = st.text_input("ASSIGNMENT NAME")
            score = st.number_input("SCORE", min_value=0.0, max_value=100.0, step=0.1)
            max_score = st.number_input("MAXIMUM SCORE", min_value=1.0, value=100.0)

        submitted = st.form_submit_button("ADD GRADE")
        if submitted:
            if student_id and student_name and assignment:
                new_grade = {
                    'Student ID': student_id,
                    'Student Name': student_name,
                    'Subject': subject,
                    'Assignment': assignment,
                    'Score': score,
                    'Max Score': max_score,
                    'Date': datetime.now().strftime("%Y-%m-%d")
                }
                st.session_state.grades_data.append(new_grade)

                c.execute("""INSERT INTO grades (student_id, student_name, subject, assignment, score, max_score, date) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (student_id, student_name, subject, assignment, score, max_score,
                           datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                st.success("GRADE ADDED SUCCESSFULLY!")
            else:
                st.warning("PLEASE FILL IN ALL REQUIRED FIELDS")


elif page == "View Grades":
    st.subheader("GRADE RECORDS")
    if st.session_state.grades_data:
        df = pd.DataFrame(st.session_state.grades_data)
        st.dataframe(df)
    else:
        st.info("NO GRADES RECORDED YET. ADD SOME GRADES USING THE 'ADD GRADE' FORM.")

elif page == "Reports":
    st.subheader("GRADE REPORTS")
    if st.session_state.grades_data:
        df = pd.DataFrame(st.session_state.grades_data)
        if not df.empty:
            df['Percentage'] = (df['Score'] / df['Max Score']) * 100
            st.metric("TOTAL GRADES", len(df))
            st.metric("AVERAGE PERCENTAGE", f"{df['Percentage'].mean():.1f}%")

            st.subheader("GRADE DISTRIBUTION")
            fig = px.histogram(df, x="Percentage", nbins=20, title="Grade Distribution",
                               color_discrete_sequence=['#00f5ff'])
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("SUBJECT PERFORMANCE")
            subject_perf = df.groupby('Subject')['Percentage'].mean().reset_index()
            fig2 = px.bar(subject_perf, x='Subject', y='Percentage',
                          title="Average Score by Subject",
                          color_discrete_sequence=['#8a2be2'])
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("NO DATA AVAILABLE FOR REPORTING")


elif page == "Export Data":
    st.subheader("EXPORT DATA")
    if st.session_state.grades_data:
        df = pd.DataFrame(st.session_state.grades_data)
        st.download_button(
            label="DOWNLOAD CSV",
            data=df.to_csv().encode('utf-8'),
            file_name="grades_export.csv",
            mime="text/csv"
        )
        st.dataframe(df.head())

conn.close()