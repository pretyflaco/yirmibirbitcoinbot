from flask import Flask, render_template_string, jsonify, request, redirect
import os
import datetime
import requests
from config import BTCTURK_API_TICKER_URL

app = Flask(__name__)

# HTML template for the homepage
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRY to Satoshi Bot</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <style>
        .container {
            max-width: 800px;
            margin-top: 2rem;
        }
        .card {
            margin-bottom: 1.5rem;
            border: none;
            box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        }
        .card-header {
            font-weight: 600;
        }
        .telegram-button {
            background-color: #0088cc;
            color: white;
            border: none;
            transition: all 0.3s;
        }
        .telegram-button:hover {
            background-color: #006699;
            color: white;
        }
        .commands-list {
            list-style-type: none;
            padding-left: 0;
        }
        .commands-list li {
            margin-bottom: 0.5rem;
            padding: 0.5rem;
            background-color: var(--bs-dark);
            border-radius: 0.25rem;
        }
        .command-name {
            font-family: monospace;
            background-color: var(--bs-secondary-bg);
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            margin-right: 0.5rem;
        }
        .rate-display {
            font-size: 1.1rem;
            font-weight: 500;
        }
        .footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--bs-border-color);
            text-align: center;
            font-size: 0.9rem;
            color: var(--bs-secondary-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h3 class="mb-0">TRY to Satoshi Telegram Bot</h3>
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <span class="badge bg-success py-2 px-3">Status: Running</span>
                    <a href="{{ telegram_link }}" target="_blank" class="btn telegram-button">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-telegram me-2" viewBox="0 0 16 16">
                            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8.287 5.906c-.778.324-2.334.994-4.666 2.01-.378.15-.577.298-.595.442-.03.243.275.339.69.47l.175.055c.408.133.958.288 1.243.294.26.006.549-.1.868-.32 2.179-1.471 3.304-2.214 3.374-2.23.05-.012.12-.026.166.016.047.041.042.12.037.141-.03.129-1.227 1.241-1.846 1.817-.193.18-.33.307-.358.336a8.154 8.154 0 0 1-.188.186c-.38.366-.664.64.015 1.088.327.216.589.393.85.571.284.194.568.387.936.629.093.06.183.125.27.187.331.236.63.448.997.414.214-.02.435-.22.547-.82.265-1.417.786-4.486.906-5.751a1.426 1.426 0 0 0-.013-.315.337.337 0 0 0-.114-.217.526.526 0 0 0-.31-.093c-.3.005-.763.166-2.984 1.09z"/>
                        </svg>
                        Open @{{ bot_username }} on Telegram
                    </a>
                </div>
                
                <p class="lead">Convert Turkish Lira to Bitcoin satoshi with real-time exchange rates from BTCTurk.</p>
                
                {% if current_rate %}
                <div class="alert alert-info mt-3">
                    <div class="rate-display">Current exchange rate: 1 BTC = {{ current_rate }} TRY</div>
                    <div class="text-muted small">Updated: {{ current_time }}</div>
                </div>
                {% endif %}
                
                <h5 class="mt-4">Available Commands:</h5>
                <ul class="commands-list">
                    <li class="d-flex">
                        <span class="command-name">/start</span>
                        <span>Welcome message with bot introduction</span>
                    </li>
                    <li class="d-flex">
                        <span class="command-name">/help</span>
                        <span>Display help information and available commands</span>
                    </li>
                    <li class="d-flex">
                        <span class="command-name">/100lira</span>
                        <span>Convert 100 Turkish Lira to Bitcoin satoshi using current rate</span>
                    </li>
                </ul>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">About This Project</h5>
            </div>
            <div class="card-body">
                <p>This Telegram bot provides real-time conversion of Turkish Lira (TRY) to Bitcoin satoshi using the BTCTurk exchange API. The bot is designed to be simple and easy to use, offering quick access to current exchange rates.</p>
                <p>All responses are provided in Turkish language, making the service accessible to local users.</p>
            </div>
        </div>
        
        <div class="footer">
            <p>© {{ current_year }} TRY to Satoshi Bot | Built with Python, Flask and python-telegram-bot</p>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    bot_username = "100liratosatoshi_bot"  # Update with your actual bot username
    telegram_link = f"https://t.me/{bot_username}"
    
    # Get current exchange rate from BTCTurk
    current_rate = None
    try:
        response = requests.get(BTCTURK_API_TICKER_URL, timeout=10)
        data = response.json()
        
        # Find the BTCTRY pair
        for pair_data in data.get('data', []):
            if pair_data.get('pair') == 'BTCTRY':
                rate = float(pair_data.get('last', 0))
                current_rate = "{:,.2f}".format(rate)
                break
    except Exception as e:
        # If there's an error, just don't show the current rate
        pass
    
    # Get current time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_year = datetime.datetime.now().year
    
    # Render the HTML template with the data
    return render_template_string(
        HTML_TEMPLATE, 
        bot_username=bot_username, 
        telegram_link=telegram_link,
        current_rate=current_rate,
        current_time=current_time,
        current_year=current_year
    )

@app.route('/api/info')
def api_info():
    """API endpoint for bot information in JSON format"""
    bot_username = "100liratosatoshi_bot"  # Update with your actual bot username
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
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)