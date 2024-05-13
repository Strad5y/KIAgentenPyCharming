from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    emit('message', 'Connected successfully!')

@socketio.on('message')
def handle_message(msg):
    # Echos die erhaltene Nachricht zurueck an den Absender
    emit('message', f'Echo: {msg}', broadcast=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
