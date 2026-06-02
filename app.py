from flask import Flask, render_template, request, redirect, session
from pypdf import PdfReader
from groq import Groq
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ================= GROQ API KEY =================
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("Set GROQ_API_KEY in PowerShell")

client = Groq(api_key=API_KEY)

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

        if not username or not password:
            return render_template("signup.html", message="Fill all fields ❌")

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
    session.clear()
    return redirect('/login')


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return render_template("index.html", answer="", message="")


# ================= UPLOAD PDF =================
@app.route('/upload', methods=['POST'])
def upload():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    file = request.files.get('pdf')

    if not file or file.filename == '':
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


# ================= ASK AI (GROQ FIXED) =================
@app.route('/ask', methods=['POST'])
def ask():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    question = request.form.get('question')

    if not question:
        return render_template("index.html", answer="Ask a question ❌")

    if not pdf_text.strip():
        return render_template("index.html", answer="Upload PDF first ❌")

    prompt = f"""
You are a strict study assistant.
Answer ONLY from the PDF content.

PDF:
{pdf_text[:800]}

Question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful study assistant."},
                {"role": "user", "content": prompt}
            ]
        )    
        answer = response.choices[0].message.content

        return render_template("index.html", answer=answer)

    except Exception as e:
        return render_template(
            "index.html",
            answer=f"⚠️ AI error: {str(e)}"
        )


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)