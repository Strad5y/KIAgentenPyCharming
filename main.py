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
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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

def validate_pdf(file_path):
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            if len(reader.pages) > 0:
                return True
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return False
    return False

def pdf_to_text(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_num in range(len(reader.pages)):
            page_text = reader.pages[page_num].extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def clean_text(text):
    clean_text = re.sub(r'\\u\w{4}', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

def requests_retry_session(
    retries=5,
    backoff_factor=1,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA

def process_chunk(chunk, qa):
    prompt = f"""
    Extract the following key values from the PDF and format them strictly as a JSON object:
    {{
        "CO2 in t/annum": "",
        "NOX in t/annum": "",
        "Number of Electric Vehicles": "",
        "Impact": "Negative impact on climate change from a company's activities that the company addresses in the report.",
        "Risks": "Material risks from impact on the climate change.",
        "Opportunities": "Financial materiality from company's activities related to climate change.",
        "Strategy": "Company's strategy and business model in line with the transition to a sustainable economy.",
        "Actions": "Actions and resources in relation to material sustainability matters.",
        "Adopted policies": "Policies adopted to manage material sustainability matters.",
        "Targets": "Company's goals towards a sustainable economy."
    }}

    PDF Content:
    {chunk}
    """
    result = qa.run({"query": prompt})
    return result




def generation2(VectorStore, query, pdf_filename):
    retriever = VectorStore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    try:
        model = OpenAI(model_name="qwen1.5-72b-chat", openai_api_key=API_KEY, openai_api_base=BASE_URL)
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        return {"error": "Model initialization failed"}

    qa = RetrievalQA.from_chain_type(llm=model, chain_type="refine", retriever=retriever, return_source_documents=False, verbose=True)

    relevant_chunks = retriever.get_relevant_documents(query)
    logger.info(f"Number of relevant chunks retrieved: {len(relevant_chunks)}")

    all_results = []
    complete_result = {
        "CO2 in t/annum": None,
        "NOX in t/annum": None,
        "Number of Electric Vehicles": None,
        "Impact": None,
        "Risks": None,
        "Opportunities": None,
        "Strategy": None,
        "Actions": None,
        "Adopted policies": None,
        "Targets": None
    }

    for chunk in relevant_chunks:
        try:
            result = process_chunk(chunk.page_content, qa)  # Assuming chunk has a page_content attribute
            if isinstance(result, str):
                try:
                    result_json = json.loads(result)
                    all_results.append(result_json)
                    for key in complete_result.keys():
                        if not complete_result[key] and result_json.get(key):
                            complete_result[key] = result_json[key]

                    if all(complete_result[key] for key in complete_result):
                        break
                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON from result: {result}")
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")

    final_result = {
        "name": pdf_filename,
        **{key: complete_result[key] if complete_result[key] is not None else "" for key in complete_result}
    }

    return final_result





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
    model = request.json.get("model", "qwen1.5-72b-chat")
    vector_store = load_vector_store('vector_store.pkl')
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    retrieved_docs = retriever.invoke(user_message)

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    if os.path.exists(os.path.join(app.config['OUTPUT_FOLDER'], 'prompt2.json')):
        prompt_text1 = open(os.path.join(app.config['OUTPUT_FOLDER'], 'prompt1.json')).read()
        prompt_text2 = open(os.path.join(app.config['OUTPUT_FOLDER'], 'prompt2.json')).read()
        response_text1 = open(os.path.join(app.config['OUTPUT_FOLDER'], 'response1.json')).read()
        response_text2 = open(os.path.join(app.config['OUTPUT_FOLDER'], 'response2.json')).read()
        prompt = (
            f"Das folgende PDF wurde hochgeladen:\n\n{retrieved_docs}\n\n"
            f"Unsere bishereige Konversation:\n\nFrage 1:{prompt_text2} Antwort 1: {response_text2}\n"
            f"Frage 2:{prompt_text1} Antwort 2: {response_text1}\n"
            f"beantworte mit all den bisher gegebenden Informationen diese Frage:{user_message}"
        )
    elif os.path.exists(os.path.join(app.config['OUTPUT_FOLDER'], 'prompt1.json')):
        prompt_text1 = open(os.path.join(app.config['OUTPUT_FOLDER'], 'prompt1.json')).read()
        response_text1 = open(os.path.join(app.config['OUTPUT_FOLDER'], 'response1.json')).read()
        prompt = (
            f"Das folgende PDF wurde hochgeladen:\n\n{retrieved_docs}\n\n"
            f"Unsere bishereige Konversation:\n\nFrage 1:{prompt_text1} Antwort 1: {response_text1}\n"
            f"beantworte mit all den bisher gegebenden Informationen diese Frage:{user_message}"
        )
    else:
        prompt = f"Das folgende PDF wurde hochgeladen:\n\n{retrieved_docs}\n\nFrage: {user_message}"

    print(prompt)
    save_prompt([user_message])

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

    save_response(response_data)

    logger.info(f"API response: {response_data}")
    return jsonify(response_data)

def save_chunks(chunks, filename):
    chunk_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{filename}_chunks.pkl")
    with open(chunk_file, 'wb') as f:
        pickle.dump(chunks, f)

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400
        file = request.files['file']
        if file and allowed_file(file.filename):
            chunk_size = int(request.form.get('chunk_size'))
            logger.info(f"Chunk size: {chunk_size}")
            delete_files_in_folder(app.config['UPLOAD_FOLDER'])
            delete_files_in_folder(app.config['OUTPUT_FOLDER'])
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            if not os.path.exists(filepath):
                logger.error("File not saved properly")
                return jsonify({"error": "File not saved properly"}), 500

            logger.info("File saved successfully")

            if not validate_pdf(filepath):
                logger.error("Invalid or corrupted PDF file")
                return jsonify({"error": "Invalid or corrupted PDF file"}), 400

            text = pdf_to_text(filepath)
            chunks = chunk_processing(text, chunk_size)
            save_chunks(chunks, filename)
            vector_store = embeddings(chunks)
            save_vector_store(vector_store, 'vector_store.pkl')

            return jsonify({"filename": filename, "text": text})
        return jsonify({"error": "Invalid file format"}), 400
    except Exception as e:
        logger.error(f"Exception during file upload: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/download-json", methods=["GET"])
def download_json():
    pdf_filename = request.args.get('pdf', None)
    if not pdf_filename:
        return jsonify({"error": "No PDF file specified"}), 400

    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF file not found"}), 404

    vector_store = load_vector_store('vector_store.pkl')  # Laden des VectorStore
    result = generation2(vector_store, pdf_path, pdf_filename)

    if "error" in result:
        logger.error(f"Failed to extract key values: {result['error']}")
        return jsonify(result), 500

    output_file = os.path.join(app.config['OUTPUT_FOLDER'], 'extracted_key_values.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=4)

    return send_file(output_file, as_attachment=True)

def chunk_processing(text,chunk_s):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_s,
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

def save_response(response_data):
    output_folder = app.config['OUTPUT_FOLDER']
    response1_path = os.path.join(output_folder, 'response1.json')
    response2_path = os.path.join(output_folder, 'response2.json')

    if os.path.exists(response2_path):
        os.remove(response2_path)

    if os.path.exists(response1_path):
        os.rename(response1_path, response2_path)

    with open(response1_path, 'w') as f:
        json.dump(response_data, f)

def save_prompt(prompt_data):
    output_folder = app.config['OUTPUT_FOLDER']
    prompt1_path = os.path.join(output_folder, 'prompt1.json')
    prompt2_path = os.path.join(output_folder, 'prompt2.json')

    if os.path.exists(prompt2_path):
        os.remove(prompt2_path)

    if os.path.exists(prompt1_path):
        os.rename(prompt1_path, prompt2_path)

    prompt_data_list = list(prompt_data)

    with open(prompt1_path, 'w') as f:
        json.dump(prompt_data_list, f)

def delete_files_in_folder(folder_path):
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
                print(f"Deleted file: {file_path}")
            else:
                print(f"Skipping non-file item: {file_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=5004)
