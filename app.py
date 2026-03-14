import streamlit as st
import sqlite3
import pandas as pd
import requests
import matplotlib.pyplot as plt
import bcrypt
import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- PAGE CONFIG ----------------

st.set_page_config(page_title="JobPilot AI", page_icon="🚀", layout="wide")

# ---------------- UI STYLE ----------------

st.markdown("""
<style>

header {visibility:hidden;}

.stApp{
background: linear-gradient(135deg,#0f172a,#020617);
color:white;
}

/* Sidebar */

section[data-testid="stSidebar"]{
background: linear-gradient(180deg,#020617,#0f172a);
}

section[data-testid="stSidebar"] *{
color:white !important;
}

/* Labels */

label{
color:white !important;
}

/* Inputs */

input{
background:#e5e7eb !important;
color:black !important;
}

textarea{
background:#e5e7eb !important;
color:black !important;
}

/* Selectbox */

div[data-baseweb="select"] *{
color:black !important;
}

/* Buttons */

.stButton>button{
background:linear-gradient(90deg,#22c55e,#16a34a);
color:white;
border-radius:8px;
font-weight:bold;
}

/* Metrics */

[data-testid="stMetricValue"]{
color:#22c55e !important;
font-size:36px !important;
font-weight:bold;
}

[data-testid="stMetricLabel"]{
color:white !important;
}

/* Tables */

[data-testid="stTable"]{
color:black;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.markdown("""
<h1 style='text-align:center;font-size:55px;color:#22c55e'>
🚀 JobPilot AI
</h1>

<p style='text-align:center;font-size:20px'>
Track Applications • Analyze Progress • Get Hired Faster
</p>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT,
password BLOB
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS applications(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user TEXT,
company TEXT,
role TEXT,
status TEXT,
date_applied TEXT,
interview_date TEXT,
job_description TEXT,
skills TEXT
)
""")

conn.commit()

# ---------------- PASSWORD FUNCTIONS ----------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

# ---------------- SIDEBAR ----------------

st.sidebar.title("💼 Job Tracker")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Account", menu)

# ---------------- REGISTER ----------------

if choice == "Register":

    st.subheader("Create Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):

        hashed = hash_password(password)

        cursor.execute(
            "INSERT INTO users VALUES(?,?)",
            (username, hashed)
        )

        conn.commit()

        st.success("Account Created Successfully")

# ---------------- LOGIN ----------------

elif choice == "Login":

    if "user" not in st.session_state:

        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):

            cursor.execute(
                "SELECT password FROM users WHERE username=?",
                (username,)
            )

            data = cursor.fetchone()

            if data and check_password(password, data[0]):

                st.session_state.user = username
                st.success("Login Successful")
                st.rerun()

            else:
                st.error("Invalid Credentials")

# ---------------- AFTER LOGIN ----------------

if "user" in st.session_state:

    user = st.session_state.user

    st.sidebar.success(f"Logged in as {user}")

    menu = [
        "🏠 Dashboard",
        "➕ Add Application",
        "📂 View Applications",
        "🔍 Search Applications",
        "📊 Analytics",
        "⏰ Interview Reminders",
        "🤖 AI Job Match",
        "📈 Success Predictor",
        "🌐 Job Search",
        "📤 Export Data",
        "🚪 Logout"
    ]

    choice = st.sidebar.selectbox("Menu", menu)

# ---------------- DASHBOARD ----------------

    if choice == "🏠 Dashboard":

        st.subheader("Career Dashboard")

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        total = len(df)
        interviews = len(df[df["status"] == "Interview"])
        offers = len(df[df["status"] == "Offer"])
        rejected = len(df[df["status"] == "Rejected"])

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Applications", total)
        c2.metric("Interviews", interviews)
        c3.metric("Offers", offers)
        c4.metric("Rejected", rejected)

# ---------------- ADD APPLICATION ----------------

    elif choice == "➕ Add Application":

        st.subheader("Add Job Application")

        company = st.text_input("Company")
        role = st.text_input("Role")

        status = st.selectbox(
            "Status",
            ["Applied", "Assessment", "Interview", "Rejected", "Offer"]
        )

        date_applied = st.date_input("Date Applied")
        interview_date = st.date_input("Interview Date")

        job_desc = st.text_area("Job Description")
        skills = st.text_input("Your Skills")

        if st.button("Save"):

            cursor.execute("""
            INSERT INTO applications
            (user,company,role,status,date_applied,interview_date,job_description,skills)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                user, company, role, status,
                str(date_applied), str(interview_date),
                job_desc, skills
            ))

            conn.commit()

            st.success("Application Saved")

# ---------------- VIEW APPLICATIONS ----------------

    elif choice == "📂 View Applications":

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        st.dataframe(df)

# ---------------- SEARCH ----------------

    elif choice == "🔍 Search Applications":

        keyword = st.text_input("Search Company or Role")

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        if keyword:

            result = df[
                df["company"].str.contains(keyword, case=False) |
                df["role"].str.contains(keyword, case=False)
            ]

            st.dataframe(result)

        else:
            st.dataframe(df)

# ---------------- ANALYTICS ----------------

    elif choice == "📊 Analytics":

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        if len(df) > 0:

            status_count = df["status"].value_counts()

            fig, ax = plt.subplots()

            ax.pie(
                status_count,
                labels=status_count.index,
                autopct="%1.1f%%"
            )

            st.pyplot(fig)

        else:
            st.info("No data yet")

# ---------------- INTERVIEW REMINDERS ----------------

    elif choice == "⏰ Interview Reminders":

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        today = datetime.date.today()
        found = False

        for _, row in df.iterrows():

            if row["interview_date"]:

                interview_date = datetime.datetime.strptime(
                    row["interview_date"],
                    "%Y-%m-%d"
                ).date()

                if interview_date >= today:

                    st.warning(f"{row['company']} interview on {interview_date}")
                    found = True

        if not found:
            st.info("No upcoming interviews")

# ---------------- AI JOB MATCH ----------------

    elif choice == "🤖 AI Job Match":

        st.subheader("AI Job Match Analyzer")

        skills = st.text_area("Enter your skills")
        job_desc = st.text_area("Paste job description")

        if st.button("Analyze Match"):

            if skills and job_desc:

                vectorizer = TfidfVectorizer()
                vectors = vectorizer.fit_transform([skills, job_desc])

                similarity = cosine_similarity(vectors)[0][1]
                score = round(similarity * 100, 2)

                st.success(f"Match Score: {score}%")

            else:
                st.warning("Enter both fields")

# ---------------- SUCCESS PREDICTOR ----------------

    elif choice == "📈 Success Predictor":

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        if len(df) < 5:

            st.warning("Add at least 5 applications")

        else:

            total = len(df)
            interviews = len(df[df["status"] == "Interview"])
            offers = len(df[df["status"] == "Offer"])

            success_rate = ((interviews + offers) / total) * 100

            st.metric(
                "Interview Probability",
                f"{round(success_rate,2)}%"
            )

# ---------------- JOB SEARCH ----------------

    elif choice == "🌐 Job Search":

        keyword = st.text_input("Enter Job Role")

        if st.button("Search Jobs"):

            url = "https://remoteok.com/api"
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(url, headers=headers)

            jobs = response.json()

            count = 0

            for job in jobs:

                if isinstance(job, dict):

                    title = job.get("position")
                    company = job.get("company")
                    link = job.get("url")

                    if title and keyword.lower() in title.lower():

                        st.write("###", title)
                        st.write("Company:", company)

                        if link:
                            st.write("Apply:", link)

                        st.write("---")

                        count += 1

                if count == 10:
                    break

# ---------------- EXPORT DATA ----------------

    elif choice == "📤 Export Data":

        df = pd.read_sql_query(
            "SELECT * FROM applications WHERE user=?",
            conn,
            params=(user,)
        )

        if len(df) > 0:

            csv = df.to_csv(index=False)

            st.download_button(
                "Download CSV",
                csv,
                "applications.csv",
                "text/csv"
            )

        else:
            st.info("No data available")

# ---------------- LOGOUT ----------------

    elif choice == "🚪 Logout":

        st.session_state.clear()
        st.success("Logged Out")
        st.rerun()

# ---------------- FOOTER ----------------

st.markdown("""
<hr>
<center>
Built with ❤️ by Manoj Kumar  
Smart Job Application Tracker
</center>
""", unsafe_allow_html=True)