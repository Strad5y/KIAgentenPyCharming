from flask import Flask, request, abort
import subprocess
import hmac
import hashlib

app = Flask(__name__)

# Geheimnis f�r GitHub Webhook
GITHUB_SECRET = b"mnjrmfkensnfjrvhr"

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
    subprocess.Popen(['git', '-C', '/home/jonne/Programme/KIAgentenPyCharming', 'pull'])
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
