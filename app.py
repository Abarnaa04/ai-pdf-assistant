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
        u = request.form.get('username')
        p = request.form.get('password')

        if u in users:
            return render_template("signup.html", message="User exists ❌")

        users[u] = p
        return redirect('/login')

    return render_template("signup.html")


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')

        if u in users and users[u] == p:
            session['user'] = u
            return redirect('/dashboard')

        return render_template("login.html", message="Invalid ❌")

    return render_template("login.html")


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return render_template("index.html", answer="", message="")


# ================= UPLOAD =================
@app.route('/upload', methods=['POST'])
def upload():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    file = request.files.get('pdf')

    if not file:
        return render_template("index.html", message="No file ❌")

    reader = PdfReader(file)
    pdf_text = ""

    for page in reader.pages:
        t = page.extract_text()
        if t:
            pdf_text += t + "\n"

    return render_template("index.html", message="PDF uploaded ✅")


# ================= ASK AI (FIXED) =================
@app.route('/ask', methods=['POST'])
def ask():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    question = request.form.get('question')

    if not pdf_text.strip():
        return render_template("index.html", answer="Upload PDF first ❌")

    prompt = f"""
Answer ONLY from PDF:

{pdf_text[:1500]}

Question: {question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-pro-latest",
            contents=prompt
        )
        return render_template("index.html", answer=response.text)

    except Exception:
        return render_template(
            "index.html",
            answer="⚠️ AI busy / quota issue"
        )


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)