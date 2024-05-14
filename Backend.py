from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import fitz  # PyMuPDF
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    socketio.send('Echo: ' + message)  # Echo the received message

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
