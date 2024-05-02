from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Routen für statische Dateien
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket-Event-Handler für den Chat
@socketio.on('message')
def handle_message(msg):
    # Echo-Nachricht zurücksenden
    emit('message', msg)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

