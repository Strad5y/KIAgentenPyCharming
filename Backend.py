from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import fitz  # PyMuPDF
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import os
from flask import send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_URL = 'https://chat-ai.academiccloud.de/v1/chat/completions'
DEFAULT_MODEL = 'intel-neural-chat-7b'
UPLOAD_FOLDER = 'PDF Files'

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    message = data.get('text')
    model = data.get('model', DEFAULT_MODEL)  # Use the model from the message or the default
    print(f'Received message: "{message}" using model: {model}')
    response = get_llm_response(message, model)
    socketio.send(response)

def get_llm_response(message, model):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': message}
        ],
        'temperature': 0.7
    }
    print(f'Sending request with model: {model}')
    response = requests.post(API_URL, headers=headers, json=data)
    response_json = response.json()
    print(f'Received response: {response_json}')
    return response_json['choices'][0]['message']['content']


# saves uploaded pdf file
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        open_pdf_button(filepath)
        return {'path': '/uploads/' + filename}, 200
    else:
        return 'No file uploaded', 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


def open_pdf_button(pdf_path):
    #save the pdf
    new_path = os.path.join("PDF Files", os.path.basename(pdf_path))
    os.rename(pdf_path, new_path)
    #text recognition from pdf
    text = pdf_ocr(new_path)
    #save the text as json
    json_file_path = "Json Files/myfile.json"
    save_text_as_json(text, json_file_path)

    #hier kommt der call hin das JSOn Datei mit prompt ans llm gesendet wird.

    # Example print the text to check if it works
    with open('Json Files/myfile.json', 'r') as file:
        data = json.load(file)
    print(json.dumps(data, indent=4))

#text recengnition from pdf
def pdf_ocr(pdf_path):
    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Initialize an empty string to store extracted text
    text = ""

    # Iterate through each page in the PDF
    for page_number in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_number)

        # Extract text from the page
        text += page.get_text()

    # Close the PDF
    pdf_document.close()

    return text

# OCR returns a text file so this saves the text as JSON
def save_text_as_json(text, json_file_path):
    # Create a dictionary to store the text
    data = {'text': text}

    # Write the dictionary to a JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False,allow_unsafe_werkzeug=True)
