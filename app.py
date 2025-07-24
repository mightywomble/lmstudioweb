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
LM_STUDIO_BASE_URL = "http://macos:1234/v1"
APP_PORT = 5010

# --- Flask App Initialization ---
# We specify the 'static_folder' to be 'dist' where our index.html will live.
# However, for a single-file setup, we'll serve it directly.
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
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }
        
        /* Base styling for the glass effect */
        .glass-ui {
            background-color: rgba(28, 37, 54, 0.6); /* Semi-transparent background */
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="bg-gray-900 bg-gradient-to-br from-gray-900 to-slate-800">
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;

        // --- Helper Components ---

        const Spinner = () => (
            <div className="w-5 h-5 border-2 border-dashed rounded-full animate-spin border-white"></div>
        );

        const SettingsIcon = () => (
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-300 hover:text-white transition-colors">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 0 2l-.15.08a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1 0-2l.15-.08a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>
        );

        // --- Main Application ---
        const App = () => {
            // State Management
            const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hello! Select a model and ask me anything.' }]);
            const [userInput, setUserInput] = useState('');
            const [isLoading, setIsLoading] = useState(false);
            const [models, setModels] = useState([]);
            const [selectedModel, setSelectedModel] = useState('');
            const [isSettingsOpen, setIsSettingsOpen] = useState(false);
            
            // Default API URL, can be overridden by settings
            const [apiUrl, setApiUrl] = useState(() => {
                return localStorage.getItem('lmstudioApiUrl') || window.location.origin;
            });
            const [tempApiUrl, setTempApiUrl] = useState(apiUrl);

            const chatContainerRef = useRef(null);

            // --- Effects ---

            // Fetch available models on component mount
            useEffect(() => {
                const fetchModels = async () => {
                    if (!apiUrl) return;
                    setIsLoading(true);
                    try {
                        const response = await fetch(`${apiUrl}/api/models`);
                        if (!response.ok) throw new Error('Failed to fetch models.');
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
                        setMessages(prev => [...prev, { role: 'error', content: `Connection Error: Could not connect to the backend at ${apiUrl}. Check the URL in Settings.`}]);
                    } finally {
                        setIsLoading(false);
                    }
                };
                fetchModels();
            }, [apiUrl]);

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
                    const response = await fetch(`${apiUrl}/api/chat`, {
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

            const handleSaveSettings = () => {
                setApiUrl(tempApiUrl);
                localStorage.setItem('lmstudioApiUrl', tempApiUrl);
                setIsSettingsOpen(false);
                // Optionally, reload or re-fetch models
                window.location.reload(); 
            };

            // --- Render ---

            return (
                <div className="flex flex-col h-screen text-gray-200 font-sans">
                    {/* Header */}
                    <header className="p-4 glass-ui flex items-center justify-between z-10">
                        <div className="flex-1">
                            <h1 className="text-xl md:text-2xl font-bold text-white">LM Studio</h1>
                        </div>
                        <div className="flex-1 flex justify-center">
                            {models.length > 0 ? (
                                <select 
                                    value={selectedModel} 
                                    onChange={e => setSelectedModel(e.target.value)}
                                    className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:ring-2 focus:ring-cyan-400 focus:outline-none"
                                >
                                    {models.map(model => (
                                        <option key={model.id} value={model.id} className="bg-gray-800">
                                            {model.id.split('/').pop()}
                                        </option>
                                    ))}
                                </select>
                            ) : (
                                <span className="text-sm text-gray-400">No models loaded</span>
                            )}
                        </div>
                        <div className="flex-1 flex justify-end">
                            <button onClick={() => setIsSettingsOpen(true)} className="p-2 rounded-full hover:bg-white/10">
                                <SettingsIcon />
                            </button>
                        </div>
                    </header>

                    {/* Chat Area */}
                    <main ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto">
                        <div className="max-w-4xl mx-auto space-y-6">
                            {messages.map((msg, index) => {
                                const isUser = msg.role === 'user';
                                const isError = msg.role === 'error';
                                const bubbleClasses = isUser 
                                    ? 'bg-cyan-600/70 self-end' 
                                    : isError
                                    ? 'bg-red-500/70 self-start'
                                    : 'bg-slate-700/70 self-start';
                                return (
                                    <div key={index} className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-xl lg:max-w-3xl p-4 rounded-2xl text-white glass-ui ${bubbleClasses}`}>
                                            <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                                        </div>
                                    </div>
                                );
                            })}
                            {isLoading && !messages.some(m => m.role === 'assistant' && m.content === '') && (
                                <div className="flex justify-start">
                                    <div className="p-4 rounded-2xl flex items-center space-x-3 glass-ui bg-slate-700/70">
                                        <Spinner />
                                        <span className="text-white text-sm">Thinking...</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </main>

                    {/* Input Footer */}
                    <footer className="p-4 glass-ui z-10">
                        <div className="max-w-4xl mx-auto">
                            <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
                                <input
                                    type="text"
                                    value={userInput}
                                    onChange={(e) => setUserInput(e.target.value)}
                                    placeholder={selectedModel ? "Message " + selectedModel.split('/').pop() : "Please select a model..."}
                                    className="flex-1 p-3 bg-gray-800/50 rounded-xl border border-white/20 focus:ring-2 focus:ring-cyan-400 focus:outline-none text-white transition"
                                    disabled={isLoading || !selectedModel}
                                />
                                <button
                                    type="submit"
                                    className="p-3 bg-cyan-600 rounded-xl text-white font-bold hover:bg-cyan-500 disabled:bg-gray-500/50 disabled:cursor-not-allowed transition-colors flex items-center justify-center w-24"
                                    disabled={isLoading || !userInput.trim()}
                                >
                                    {isLoading ? <Spinner /> : 'Send'}
                                </button>
                            </form>
                        </div>
                    </footer>

                    {/* Settings Modal */}
                    {isSettingsOpen && (
                        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                            <div className="p-8 rounded-2xl glass-ui w-full max-w-md">
                                <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
                                <div className="space-y-2">
                                    <label htmlFor="apiUrlInput" className="block text-sm font-medium text-gray-300">Backend URL</label>
                                    <input
                                        id="apiUrlInput"
                                        type="text"
                                        value={tempApiUrl}
                                        onChange={e => setTempApiUrl(e.target.value)}
                                        className="w-full p-2 bg-gray-800/80 rounded-lg border border-white/20 focus:ring-2 focus:ring-cyan-400 focus:outline-none text-white"
                                    />
                                    <p className="text-xs text-gray-400">This is the address of the Python server (e.g., http://192.168.1.10:5010).</p>
                                </div>
                                <div className="mt-6 flex justify-end space-x-4">
                                    <button onClick={() => setIsSettingsOpen(false)} className="px-4 py-2 rounded-lg bg-gray-600/50 hover:bg-gray-500/50 text-white">Cancel</button>
                                    <button onClick={handleSaveSettings} className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold">Save & Reload</button>
                                </div>
                            </div>
                        </div>
                    )}
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
