from flask import Flask, render_template, request, redirect, session, Response
from pypdf import PdfReader
from groq import Groq
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ================= GROQ API =================
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("Set GROQ_API_KEY in PowerShell")

client = Groq(api_key=API_KEY)

users = {}
pdf_text = ""
last_answer = ""

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

        if not u or not p:
            return render_template("signup.html", message="Fill all fields ❌")

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

    return render_template("index.html", message="", answer="")


# ================= UPLOAD PDF =================
@app.route('/upload', methods=['POST'])
def upload():
    global pdf_text

    if 'user' not in session:
        return redirect('/login')

    file = request.files.get('pdf')

    if not file or file.filename == "":
        return render_template("index.html", message="No file selected ❌")

    reader = PdfReader(file)
    pdf_text = ""

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pdf_text += text + "\n"

    if not pdf_text.strip():
        return render_template("index.html", message="PDF has no text ❌")

    return render_template("index.html", message="PDF uploaded successfully ✅")


# ================= ASK AI =================
@app.route('/ask', methods=['POST'])
def ask():
    global pdf_text, last_answer

    if 'user' not in session:
        return redirect('/login')

    question = request.form.get('question')

    if not question:
        return render_template("index.html", answer="Ask a question ❌")

    if not pdf_text.strip():
        return render_template("index.html", answer="Upload PDF first ❌")

    prompt = f"""
Answer ONLY from PDF content:

{pdf_text[:1200]}

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

        last_answer = response.choices[0].message.content

        return render_template("index.html", answer=last_answer)

    except Exception as e:
        return render_template("index.html", answer=f"AI error: {str(e)}")


# ================= DOWNLOAD ANSWER =================
@app.route('/download', methods=['POST'])
def download():
    global last_answer

    if not last_answer:
        last_answer = "No answer generated yet"

    return Response(
        last_answer,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=answer.txt"}
    )


# ================= CLEAR PDF =================
@app.route('/clear', methods=['POST'])
def clear():
    global pdf_text
    pdf_text = ""
    return render_template("index.html", message="PDF cleared 🧹")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)