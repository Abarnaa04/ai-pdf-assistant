from flask import Flask, render_template, request, redirect, session
from pypdf import PdfReader
from google import genai
import os
import time

app = Flask(__name__)
app.secret_key = "secret123"

# ================= API KEY =================
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("Set GOOGLE_API_KEY in PowerShell")

client = genai.Client(api_key=API_KEY)

# ================= SIMPLE USER DB =================
users = {}

pdf_text = ""

# ================= HOME =================
@app.route('/')
def home():
    return redirect('/login')


# ================= SIGNUP =================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users:
            return render_template("signup.html", message="User already exists ❌")

        users[username] = password
        return redirect('/login')

    return render_template("signup.html")


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username] == password:
            session['user'] = username
            return redirect('/dashboard')

        return render_template("login.html", message="Invalid credentials ❌")

    return render_template("login.html")


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return render_template("index.html")


# ================= UPLOAD PDF =================
@app.route('/upload', methods=['POST'])
def upload():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    file = request.files.get('pdf')

    if not file:
        return render_template("index.html", message="No file selected ❌")

    try:
        reader = PdfReader(file)
        pdf_text = ""

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_text += text + "\n"

        if not pdf_text.strip():
            return render_template("index.html", message="PDF has no readable text ❌")

        return render_template("index.html", message="PDF uploaded successfully ✅")

    except Exception as e:
        return render_template("index.html", message=f"Error: {str(e)}")


# ================= ASK AI =================
@app.route('/ask', methods=['POST'])
def ask():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    question = request.form.get('question')

    if not pdf_text.strip():
        return render_template("index.html", answer="Upload PDF first ❌")

    safe_pdf = pdf_text[:1500]

    prompt = f"""
Answer only from PDF:

{safe_pdf}

Question: {question}
"""

    # 🔥 SAFE RETRY SYSTEM
    for _ in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return render_template("index.html", answer=response.text)

        except Exception:
            time.sleep(2)

    return render_template(
        "index.html",
        answer="⚠️ AI temporarily busy / quota reached. Try again later."
    )


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)