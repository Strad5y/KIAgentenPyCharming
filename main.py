import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
import PyPDF2
import json
from langchain_text_splitters import RecursiveJsonSplitter


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
OUTPUT_FOLDER = 'output'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pdf_to_text(pdf_path):
    # wird geupdated zu ocr. Aber in und output format bleiben identisch
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

    #hier mit usser message splits der usser message retrieven
    pdf_text = request.json.get("pdf_text", "")


    # check if there are is any old resonses.
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    # add old respones to the prompt.
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
    response_data = response.json()

    # Speichere die Antwort in einer JSON-Datei
    output_file = os.path.join(app.config['OUTPUT_FOLDER'], 'last_response.json')
    with open(output_file, 'w') as f:
        json.dump(response_data, f)

    logger.info(f"API response: {response_data}")
    return jsonify(response_data)

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

        print(text)


        json_text = json.dumps({"text": text})
        splitter = RecursiveJsonSplitter(max_chunk_size=200)
        all_splits = splitter.split_json(json_data=json_text)
        print(all_splits)

        #hier methode zum spliten und abspeichern callen(text)

        return jsonify({"filename": filename, "text": text})
    return jsonify({"error": "Invalid file format"}), 400

@app.route("/download-json", methods=["GET"])
def download_json():
    output_file = os.path.join(app.config['OUTPUT_FOLDER'], 'last_response.json')
    return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=5004)
