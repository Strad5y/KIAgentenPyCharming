from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json
import fitz  # PyMuPDF
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv('API_KEY')
API_URL = 'https://chat-ai.academiccloud.de/v1/chat/completions'
MODEL = 'intel-neural-chat-7b'

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    response = get_llm_response(message)
    socketio.send(response)

def get_llm_response(message):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': message}
        ],
        'temperature': 0.7
    }
    response = requests.post(API_URL, headers=headers, json=data)
    response_json = response.json()
    return response_json['choices'][0]['message']['content']

def open_pdf_button(pdf_path):
    text = pdf_ocr(pdf_path)
    json_file_path = "Json Files/myfile.json"
    save_text_as_json(text, json_file_path)
    # Example print to check if it works
    with open('Json Files/myfile.json', 'r') as file:
        data = json.load(file)
    print(json.dumps(data, indent=4))

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

def save_text_as_json(text, json_file_path):
    # Create a dictionary to store the text
    data = {'text': text}

    # Write the dictionary to a JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
