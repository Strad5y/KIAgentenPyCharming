from flask import Flask, request, render_template, abort
from flask_socketio import SocketIO, emit
import subprocess
import hmac
import hashlib

app = Flask(__name__)
socketio = SocketIO(app)

# Geheimnis f�r GitHub Webhook
GITHUB_SECRET = b"your-webhook-secret"

@app.route('/')
def index():
    return render_template('index.html')

# WebSocket-Event-Handler f�r den Chat
@socketio.on('message')
def handle_message(msg):
    # Echo-Nachricht zur�cksenden
    emit('message', msg)

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        abort(400)

    sha_name, signature = signature.split('=')
    mac = hmac.new(GITHUB_SECRET, msg=request.data, digestmod=hashlib.sha256)

    if not hmac.compare_digest(mac.hexdigest(), signature):
        abort(400)

    # Git-Pull ausf�hren
    subprocess.Popen(['git', '-C', '/path/to/repo', 'pull'])
    return '', 204

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
