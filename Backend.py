from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')  # Stelle sicher, dass 'index.html' im 'templates' Verzeichnis liegt

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    socketio.send('Echo: ' + message)  # Verwende `send` Methode von socketio statt `emit`

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
