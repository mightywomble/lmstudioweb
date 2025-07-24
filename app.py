# app.py
# ---
# This single Flask application does two things:
# 1. Serves the React-based web UI (index.html).
# 2. Acts as a proxy for the LM Studio API to avoid CORS issues.
#
# To Run:
# 1. Make sure you have Flask, Requests, and Flask-CORS installed:
#    pip3 install Flask requests Flask-Cors
# 2. Save this file as 'app.py'.
# 3. Run from your terminal:
#    python3 app.py
# 4. Open your web browser and go to http://<Your-Mac-Mini-IP>:5010

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import os

# --- Configuration ---
# The Python server will proxy requests to the LM Studio server at this address.
# This is not configurable from the UI.
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
APP_PORT = 5010

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- HTML Content ---
# The entire React frontend is stored in this multi-line string.
# This makes the application self-contained in a single Python file.
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LM Studio Glass UI</title>
    
    <!-- Tailwind CSS for styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- React and Babel for the UI component -->
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <style>
        /* Custom scrollbar for a sleeker look */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.25); border-radius: 4px; border: 1px solid rgba(0,0,0,0.2); }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }
        
        /* Enhanced glass effect */
        .glass-ui {
            background-color: rgba(30, 41, 59, 0.5); /* bg-slate-800 with 50% opacity */
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Background pattern to make the glass pop */
        body {
            background-color: #020617; /* bg-slate-950 */
            background-image: 
                radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0);
            background-size: 2rem 2rem;
        }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        
        // The API URL is now fixed to the origin where the page is served from.
        // This simplifies the app by removing the need for a settings panel.
        const API_BASE_URL = window.location.origin;

        // --- Helper Components ---

        const Spinner = () => (
            <div className="w-5 h-5 border-2 border-dashed rounded-full animate-spin border-white"></div>
        );

        // --- Main Application ---
        const App = () => {
            // State Management
            const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hello! Select a model and ask me anything.' }]);
            const [userInput, setUserInput] = useState('');
            const [isLoading, setIsLoading] = useState(false); // For message responses
            const [isFetchingModels, setIsFetchingModels] = useState(true); // For initial model load
            const [models, setModels] = useState([]);
            const [selectedModel, setSelectedModel] = useState('');
            
            const chatContainerRef = useRef(null);

            // --- Effects ---

            // Fetch available models on component mount
            useEffect(() => {
                const fetchModels = async () => {
                    setIsFetchingModels(true);
                    try {
                        const response = await fetch(`${API_BASE_URL}/api/models`);
                        if (!response.ok) throw new Error('Failed to fetch models from the server.');
                        const data = await response.json();
                        
                        const loadedModels = data.data || [];
                        setModels(loadedModels);

                        if (loadedModels.length > 0) {
                            setSelectedModel(loadedModels[0].id);
                        } else {
                            setMessages(prev => [...prev, { role: 'error', content: 'No models loaded in LM Studio. Please load a model in the desktop app.'}]);
                        }
                    } catch (error) {
                        console.error("Error fetching models:", error);
                        setMessages(prev => [...prev, { role: 'error', content: `Connection Error: Could not connect to the Python Server at ${API_BASE_URL}. Please ensure the server is running and accessible.`}]);
                    } finally {
                        setIsFetchingModels(false);
                    }
                };
                fetchModels();
            }, []); // Empty dependency array means this runs only once on mount

            // Auto-scroll chat
            useEffect(() => {
                chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
            }, [messages]);

            // --- Handlers ---

            const handleSendMessage = async (e) => {
                e.preventDefault();
                if (!userInput.trim() || isLoading || !selectedModel) return;

                const newUserMessage = { role: 'user', content: userInput.trim() };
                const updatedMessages = [...messages, newUserMessage];
                
                setMessages(updatedMessages);
                setUserInput('');
                setIsLoading(true);

                try {
                    const response = await fetch(`${API_BASE_URL}/api/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            messages: updatedMessages,
                            model: selectedModel // Pass the selected model
                        }),
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.details || 'An unknown error occurred.');
                    }

                    const data = await response.json();
                    const assistantMessage = data.choices[0].message;
                    setMessages(prev => [...prev, assistantMessage]);

                } catch (error) {
                    console.error("Error sending message:", error);
                    setMessages(prev => [...prev, { role: 'error', content: `Error: ${error.message}` }]);
                } finally {
                    setIsLoading(false);
                }
            };

            // --- Render ---

            return (
                <div className="flex flex-col h-screen text-gray-200 font-sans">
                    {/* Header */}
                    <header className="p-4 glass-ui flex items-center justify-center relative shadow-lg rounded-b-3xl mx-auto mt-4 w-[95%] max-w-4xl">
                        {isFetchingModels ? (
                            <span className="text-sm text-gray-300 animate-pulse">Fetching models...</span>
                        ) : models.length > 0 ? (
                            <select 
                                value={selectedModel} 
                                onChange={e => setSelectedModel(e.target.value)}
                                className="bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-sm text-white focus:ring-2 focus:ring-cyan-400 focus:outline-none appearance-none text-center cursor-pointer"
                            >
                                {models.map(model => (
                                    <option key={model.id} value={model.id} className="bg-slate-800">
                                        {model.id.split('/').pop()}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <span className="text-sm text-red-400">No Models Loaded in LM Studio</span>
                        )}
                    </header>

                    {/* Chat Area */}
                    <main ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto">
                        <div className="max-w-4xl mx-auto space-y-8">
                            {messages.map((msg, index) => {
                                const isUser = msg.role === 'user';
                                const isError = msg.role === 'error';
                                const bubbleClasses = isUser 
                                    ? 'bg-cyan-500/50 self-end' 
                                    : isError
                                    ? 'bg-red-500/60 self-start'
                                    : 'bg-slate-700/60 self-start';
                                return (
                                    <div key={index} className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-xl lg:max-w-3xl p-4 rounded-3xl text-white glass-ui ${bubbleClasses}`}>
                                            <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                                        </div>
                                    </div>
                                );
                            })}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="p-4 rounded-3xl flex items-center space-x-3 glass-ui bg-slate-700/60">
                                        <Spinner />
                                        <span className="text-white text-sm">Thinking...</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </main>

                    {/* Input Footer */}
                    <footer className="p-4 glass-ui rounded-t-3xl mx-auto mb-4 w-[95%] max-w-4xl">
                        <div className="max-w-4xl mx-auto">
                            <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
                                <input
                                    type="text"
                                    value={userInput}
                                    onChange={(e) => setUserInput(e.target.value)}
                                    placeholder={selectedModel ? "Message " + selectedModel.split('/').pop() : "Please select a model..."}
                                    className="flex-1 p-4 bg-slate-900/50 rounded-2xl border border-white/20 focus:ring-2 focus:ring-cyan-400 focus:outline-none text-white transition"
                                    disabled={isLoading || !selectedModel}
                                />
                                <button
                                    type="submit"
                                    className="p-4 bg-cyan-600 rounded-2xl text-white font-bold hover:bg-cyan-500 disabled:bg-slate-600/50 disabled:cursor-not-allowed transition-colors flex items-center justify-center w-28"
                                    disabled={isLoading || !userInput.trim()}
                                >
                                    {isLoading ? <Spinner /> : 'Send'}
                                </button>
                            </form>
                        </div>
                    </footer>
                </div>
            );
        };

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>
"""

# --- API Endpoints ---

@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return INDEX_HTML

@app.route('/api/models', methods=['GET'])
def get_models():
    """
    Fetches the list of currently loaded models from LM Studio.
    """
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/models")
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Could not connect to LM Studio server.", "details": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    """
    Proxies chat completion requests to the LM Studio server, including the selected model.
    """
    try:
        data = request.get_json()
        
        if 'messages' not in data or 'model' not in data:
            return jsonify({"error": "Missing 'messages' or 'model' in request body"}), 400

        payload = {
            "model": data['model'], # Pass the model identifier
            "messages": data['messages'],
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", -1),
            "stream": False,
        }

        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        response.raise_for_status()
        
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Could not get a response from LM Studio.", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    print(f"🚀 Server starting...")
    print(f"✅ LM Studio backend is expected at: {LM_STUDIO_BASE_URL}")
    print(f"✅ Web UI will be available at: http://0.0.0.0:{APP_PORT}")
    print(f"   (Access from other devices using your Mac's IP address, e.g., http://192.168.1.XX:{APP_PORT})")
    # The host '0.0.0.0' makes the server accessible on your local network
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
