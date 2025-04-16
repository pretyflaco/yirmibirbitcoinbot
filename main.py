"""Main Flask application for the Telegram Bitcoin Converter Bot.

This module provides a simple web server with health check endpoints
to verify that the bot is running correctly.
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Home endpoint that returns a status message.

    Returns:
        JSON response with status information
    """
    return jsonify({
        "message": "TRY to Satoshi Telegram Bot is running",
        "status": "ok"
    })

@app.route('/health')
def health():
    """Health check endpoint.

    Returns:
        JSON response with health status
    """
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)