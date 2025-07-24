# app.py
# ---
# This Flask application acts as a backend for the LM Studio Web UI.
# It proxies requests to the LM Studio local server, which is necessary
# to avoid Cross-Origin Resource Sharing (CORS) issues in the browser.

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

# --- Configuration ---
# Set the address of your LM Studio server.
# If LM Studio is running on the same machine, 'localhost' is correct.
# The default port is 1234.
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"

# --- Flask App Initialization ---
app = Flask(__name__)
# Enable CORS to allow the React frontend to make requests to this backend.
CORS(app)

# --- API Endpoints ---

@app.route('/api/models', methods=['GET'])
def get_models():
    """
    Fetches the list of currently loaded models from LM Studio.
    LM Studio's /v1/models endpoint provides this information.
    """
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/models")
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models from LM Studio: {e}")
        return jsonify({"error": "Could not connect to LM Studio server.", "details": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    """
    Proxies chat completion requests to the LM Studio server.
    It takes the message history from the frontend and forwards it.
    """
    try:
        # Get the JSON data sent from the frontend
        data = request.get_json()
        
        # Check if messages are present
        if 'messages' not in data:
            return jsonify({"error": "Missing 'messages' in request body"}), 400

        # These are common parameters for chat completions.
        # You can expose more of these to the frontend if needed.
        payload = {
            "messages": data['messages'],
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", -1), # -1 for infinite generation
            "stream": False, # Streaming is more complex to handle, so we'll keep it simple
        }

        # Forward the request to the LM Studio server
        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to LM Studio chat endpoint: {e}")
        return jsonify({"error": "Could not get a response from LM Studio.", "details": str(e)}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

# --- How to Run ---
# 1. Make sure you have Flask, Requests, and Flask-CORS installed:
#    pip install Flask requests Flask-Cors
#
# 2. Save this file as 'app.py'.
#
# 3. Run from your terminal:
#    flask --app app --debug run --host=0.0.0.0
#
#    Using --host=0.0.0.0 makes the server accessible from other
#    devices on your local network, not just from the Mac Mini itself.
if __name__ == '__main__':
    # This allows running the script directly with `python app.py`
    # The host '0.0.0.0' makes it accessible on your local network
    app.run(host='0.0.0.0', port=5001, debug=True)
