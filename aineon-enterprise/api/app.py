from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Python app deployed successfully on Render!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/version')
def version():
    return f"Python app running on Render | Flask + Gunicorn"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
