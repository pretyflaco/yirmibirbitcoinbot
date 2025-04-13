from flask import Flask, render_template, jsonify, request, redirect
import os

app = Flask(__name__)

@app.route('/')
def home():
    bot_username = "yirmibir21bot"  # This is from the logs
    telegram_link = f"https://t.me/{bot_username}"
    
    return jsonify({
        "message": "TRY to Satoshi Telegram Bot Server",
        "status": "running",
        "bot_username": bot_username,
        "telegram_link": telegram_link,
        "commands": {
            "/start": "Welcome message",
            "/help": "Display help information",
            "/100lira": "Convert 100 Turkish Lira to Bitcoin satoshi"
        },
        "info": "This is the server for the Telegram bot that converts TRY to Satoshi using real-time exchange rates from BTCTurk"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)