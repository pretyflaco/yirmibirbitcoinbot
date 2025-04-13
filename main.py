from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "TRY to Satoshi Telegram Bot Server",
        "status": "running",
        "info": "This is the server for the Telegram bot that converts TRY to Satoshi"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)