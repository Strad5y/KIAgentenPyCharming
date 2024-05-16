from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import fitz  # PyMuPDF
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# LLM API Endpoint und Authentifizierung
LLM_API_URL = 'https://llm-chat.skynet.coypu.org/generate_text'
LLM_API_USER = 'llm-chat-user'
LLM_API_PASS = 'Nr17TT5m8Qj1oHS1'


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('message')
def handle_message(message):
    print('Received message from frontend:', message)

    headers = {
        'Content-Type': 'application/json'
    }

    instruction = "Please provide a detailed response to the user's query."
    data = {
        'messages': [
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': message}
        ]
    }

    try:
        print('Sending request to LLM API with data:', data)
        response = requests.post(LLM_API_URL, auth=(LLM_API_USER, LLM_API_PASS), headers=headers, json=data,
                                 verify=False)
        print('Response status code:', response.status_code)
        print('Response headers:', response.headers)
        print('Response content:', response.content.decode())

        if response.status_code == 200:
            response_json = response.json()
            print('Response JSON:', response_json)
            llm_reply = response_json.get('generated_text', 'Keine Antwort erhalten')
        else:
            llm_reply = 'Fehler beim Abrufen der Antwort von der LLM'

        print('Sending response back to frontend:', llm_reply)
        socketio.emit('message', llm_reply)
    except Exception as e:
        print('Error:', str(e))
        socketio.emit('message', 'Fehler beim Abrufen der Antwort von der LLM')


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

#open_pdf_button("Pdf Files/Pfannkuchen Grundrezept.pdf")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

