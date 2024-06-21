import re
import PyPDF2
import requests
import os
import json
import logging
import pickle
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
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
            text += reader.pages[page_num].extract_text() + "\n"
    print("Extracted PDF Text:\n", text)
    return text


def clean_text(text):
    clean_text = re.sub(r'\\u\w{4}', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()


def extract_key_values(pdf_text, pdf_filename):
    key_values = {
        "name": pdf_filename,
        "CO2": extract_value(pdf_text, [
            r"CO2\s*Emissions?:\s*([\d,\.]+)",
            r"CO2\s*in\s*t/annum:\s*([\d,\.]+)",
            r"CO2\s*emissions?\s*is\s*([\d,\.]+)"
        ]),
        "NOX": extract_value(pdf_text, [
            r"NOX\s*Emissions?:\s*([\d,\.]+)",
            r"NOX\s*in\s*t/annum:\s*([\d,\.]+)",
            r"NOX\s*emissions?\s*is\s*([\d,\.]+)"
        ]),
        "Number_of_Electric_Vehicles": extract_value(pdf_text, [
            r"Total\s*Electric\s*Vehicles:\s*(\d+)",
            r"Number\s*of\s*Electric\s*Vehicles:\s*(\d+)",
            r"Electric\s*Vehicles:\s*(\d+)",
            r"Count\s*of\s*Electric\s*Vehicles:\s*(\d+)"
        ]),
        "Impact": extract_section(pdf_text, ["Risks, opportunities and impacts", "Impact"],
                                  ["Uniform codes and standards worldwide", "Uniform standards"]),
        "Risks": extract_section(pdf_text, ["Risk assessment and due diligence", "Risk management"],
                                 ["Sustainability management", "Prevention tool"]),
        "Opportunities": extract_section(pdf_text, ["Risk assessment and due diligence", "Risk management"],
                                         ["Sustainability management", "Prevention tool"]),
        "Strategy": extract_section(pdf_text, ["Sustainability strategy", "Strategy"],
                                    ["TARGETS AND AMBITIONS", "RELEVANT TOPICS"]),
        "Actions": extract_section(pdf_text, ["Sustainability management", "Actions"], ["Policies and Goals", "Goals"]),
        "Adopted_policies": extract_section(pdf_text, ["Implemented Policies", "Adopted Policies"],
                                            ["Sustainability Goals", "Targets"]),
        "Targets": extract_section(pdf_text, ["TARGETS AND AMBITIONS", "Targets"], [r"Page\s*\d+", "End of document"])
    }

    for key, value in key_values.items():
        if value is None:
            logger.warning(f"Value for {key} not found in the document.")

    return key_values


def extract_value(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_section(text, start_markers, end_markers):
    for start_marker in start_markers:
        start = text.find(start_marker)
        if start != -1:
            start += len(start_marker)
            for end_marker in end_markers:
                end = text.find(end_marker, start)
                if end != -1:
                    return clean_text(text[start:end].strip())
            return clean_text(text[start:].strip())
    logger.warning(f"None of the start markers '{start_markers}' found.")
    return None


def generation2(pdf_text, vector_store_filename, api_key, base_url):
    vector_store = load_vector_store(vector_store_filename)
    retriever = vector_store.as_retriever()

    prompt = f'''Bitte extrahiere die folgenden Informationen aus dem PDF und gib sie im JSON-Format zurück: CO2-Emissionen, NOX-Emissionen, Anzahl der Elektrofahrzeuge, Auswirkungen, Risiken, Chancen, Strategie, Maßnahmen, verabschiedete Richtlinien, Ziele.\n\n{pdf_text}'''

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
        additional_info = generation2(text, 'vector_store.pkl', API_KEY, BASE_URL)
        return jsonify({"filename": filename, "text": text, "additional_info": additional_info})
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
    key_values = extract_key_values(pdf_text, pdf_filename)

    logger.info(f"Extracted Key Values: {key_values}")

    output_file = os.path.join(app.config['OUTPUT_FOLDER'], 'extracted_key_values.json')
    with open(output_file, 'w') as f:
        json.dump(key_values, f, indent=4)

    return send_file(output_file, as_attachment=True)


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


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="127.0.0.1", port=5004)
