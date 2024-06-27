import os
import logging
import pickle
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
import PyPDF2
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

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
    text = ""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(reader.pages)):
            page_text = reader.pages[page_num].extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def chunk_processing(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_text(text=text)
    return chunks

def embeddings(chunks):
    embeddings_model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    return vector_store

def save_vector_store(vector_store, filename):
    directory = 'vectorStore'
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    with open(filepath, 'wb') as f:
        pickle.dump(vector_store, f)

def load_vector_store(filename):
    directory = 'vectorStore'
    filepath = os.path.join(directory, filename)
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def generation2(pdf_text, api_key, base_url):
    prompt = f"""
    Please extract the following information from the provided PDF and return it in a structured JSON format:
    - CO2 emissions: [CO2 emissions in tonnes per annum]
    - NOx emissions: [NOx emissions in tonnes per annum]
    - Number of Electric Vehicles: [Total number of electric vehicles]
    - Impact: [Describe any negative impact on climate change from the company's activities]
    - Risks: [Outline material risks from the impact on climate change]
    - Opportunities: [Detail any financial materiality from the company's activities related to climate change]
    - Strategy: [Summarize the company's strategy and business model in line with the transition to a sustainable economy]
    - Actions: [Discuss actions and resources in relation to material sustainability matters]
    - Adopted Policies: [List policies adopted to manage material sustainability matters]
    - Targets: [State the company's goals towards a sustainable economy]

    PDF Content:
    {pdf_text}
    """

    response = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "intel-neural-chat-7b", "prompt": prompt, "max_tokens": 500}
    )

    if response.status_code != 200:
        logger.error(f"API request failed with status code {response.status_code}")
        return None

    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}")
        return None

    return result

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
    vector_store = load_vector_store('vector_store.pkl')
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    retrieved_docs = retriever.invoke(user_message)

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    prompt = f"Das folgende PDF wurde hochgeladen:\n\n{retrieved_docs}\n\nFrage: {user_message}"

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
        chunks = chunk_processing(text)
        vector_store = embeddings(chunks)
        save_vector_store(vector_store, 'vector_store.pkl')
        return jsonify({"filename": filename, "text": text})
    return jsonify({"error": "Invalid file format"}), 400

@app.route("/download-json", methods=["GET"])
def download_json():
    pdf_filename = request.args.get('pdf', None)
    if not pdf_filename:
        return jsonify({"error": "No PDF file specified"}), 400

    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF file not found"}), 404

    pdf_text = pdf_to_text(pdf_path)
    key_values = generation2(pdf_text, API_KEY, BASE_URL)

    if key_values is None:
        return jsonify({"error": "Failed to extract key values"}), 500

    output_file = os.path.join(app.config['OUTPUT_FOLDER'], 'last_response.json')
    with open(output_file, 'w') as f:
        json.dump(key_values, f)

    return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=5004)
