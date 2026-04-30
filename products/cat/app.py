import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Titan product online</h1>'

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5055)), debug=True)
