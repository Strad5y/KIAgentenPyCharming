import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from gunicorn.app.base import BaseApplication
from dotenv import load_dotenv
import requests
import PyPDF2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pdf_to_text(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

@app.route("/")
def home_route():
    return render_template("home.html")

@app.route("/chat")
def chat_route():
    pdf_filename = request.args.get('pdf', None)
    pdf_text = ""
    if pdf_filename:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf_text = pdf_to_text(pdf_path)
    return render_template("chat.html", pdf_filename=pdf_filename, pdf_text=pdf_text)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/api/chat", methods=["POST"])
def chat_api():
    user_message = request.json.get("message")
    model = request.json.get("model", "intel-neural-chat-7b")
    pdf_text = request.json.get("pdf_text", "")

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    prompt = f"Das folgende PDF wurde hochgeladen:\n\n{pdf_text}\n\nFrage: {user_message}"

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }

    response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=data)
    logger.info(f"API response: {response.json()}")
    return jsonify(response.json())



@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text = pdf_to_text(filepath)
        return jsonify({"filename": filename, "text": text})
    return jsonify({"error": "Invalid file format"}), 400

class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.application = app
        self.options = options or {}
        super().__init__()

    def load_config(self):
        # Apply configuration to Gunicorn
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == "__main__":
    options = {
        "bind": "0.0.0.0:5004",
        "workers": 4,
        "loglevel": "info",
        "accesslog": "-"
    }
    StandaloneApplication(app, options).run()
