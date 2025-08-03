# app.py
# ---
# This single Flask application serves a React UI and proxies API requests.
# It uses a minimalist, glassmorphism UI and loads Firebase credentials 
# securely from a separate `config.py` file.

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# --- Configuration ---
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
APP_PORT = 5010
CONFIG_FILE_PATH = 'config.py'

# --- Config Management ---

def load_firebase_config():
    """Loads the Firebase config from config.py."""
    if not os.path.exists(CONFIG_FILE_PATH):
        return {}
    try:
        from config import FIREBASE_CONFIG
        return FIREBASE_CONFIG
    except (ImportError, AttributeError, SyntaxError):
        return {}

def save_firebase_config(config_data):
    """Saves the Firebase config dict to config.py."""
    with open(CONFIG_FILE_PATH, 'w') as f:
        f.write("# This file is generated automatically. Do not edit manually.\n")
        f.write("# Add this file to your .gitignore to keep credentials secure.\n\n")
        f.write("FIREBASE_CONFIG = ")
        f.write(json.dumps(config_data, indent=4))
    print(f"Firebase configuration saved to {CONFIG_FILE_PATH}. Please restart the server.")

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- HTML Content ---
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat</title>
    
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <script type="module">
        const firebaseConfig = __FIREBASE_CONFIG_PLACEHOLDER__;

        if (firebaseConfig && firebaseConfig.apiKey) {
            try {
                const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
                const { getFirestore, doc, onSnapshot, setDoc } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
                const { getAuth, signInAnonymously, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");

                const app = initializeApp(firebaseConfig);
                const db = getFirestore(app);
                const auth = getAuth(app);
                window.firebase = { db, auth, doc, onSnapshot, setDoc, signInAnonymously, onAuthStateChanged };
            } catch (e) {
                console.error("Firebase initialization failed:", e);
                window.firebase = null;
            }
        } else {
            console.warn("Firebase configuration is missing.");
            window.firebase = null;
        }
    </script>
    
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); font-family: 'Inter', sans-serif; }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
        .glass-panel { background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37); }
        .chat-area::-webkit-scrollbar { width: 6px; }
        .chat-area::-webkit-scrollbar-track { background: transparent; }
        .chat-area::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.3); border-radius: 3px; }
        .chat-area::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.5); }
        .bubble::after { content: ''; position: absolute; width: 0; height: 0; border-style: solid; }
        .bubble-user::after { border-width: 0 0 15px 15px; border-color: transparent transparent transparent rgba(255, 255, 255, 0.3); right: -10px; bottom: 0; }
        .bubble-ai::after { border-width: 15px 15px 0 0; border-color: rgba(255, 255, 255, 0.4) transparent transparent transparent; left: -10px; bottom: 0; }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        const API_BASE_URL = window.location.origin;
        const CHAT_DOC_ID = "main_chat";

        // --- Helper Components ---
        const Spinner = () => <div className="w-4 h-4 border-2 border-dashed rounded-full animate-spin border-white"></div>;
        const Icon = ({ path, className = "w-6 h-6" }) => <svg className={className} viewBox="0 0 24 24" fill="currentColor"><path d={path}></path></svg>;
        const ICONS = {
            send: "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z",
            chatbot: "M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z",
            settings: "M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69-.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.09.49 0 .61.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"
        };
        
        const SettingsModal = ({ isOpen, onClose, currentConfig }) => {
            const [config, setConfig] = useState(currentConfig);
            const [saveStatus, setSaveStatus] = useState('idle');

            useEffect(() => { setConfig(currentConfig) }, [currentConfig]);

            const handleChange = (e) => setConfig({ ...config, [e.target.name]: e.target.value });

            const handleSave = async () => {
                setSaveStatus('saving');
                try {
                    const response = await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config) });
                    if (!response.ok) throw new Error('Server failed to save config.');
                    setSaveStatus('success');
                } catch (error) {
                    setSaveStatus('error');
                }
            };

            if (!isOpen) return null;
            const fields = ["apiKey", "authDomain", "projectId", "storageBucket", "messagingSenderId", "appId"];

            return (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4">
                    <div className="p-8 rounded-2xl glass-panel w-full max-w-lg">
                        <h2 className="text-2xl font-bold text-white mb-6">Firebase Configuration</h2>
                        {saveStatus === 'success' ? (
                            <div className="text-center p-4 bg-green-500/20 border border-green-500 rounded-lg">
                                <h3 className="font-bold text-lg text-green-300">Success!</h3>
                                <p className="text-amber-300 font-bold mt-4">ACTION REQUIRED:</p>
                                <p className="text-amber-200">1. Stop the Python server (Ctrl+C).</p>
                                <p className="text-amber-200">2. Restart it: `python3 app.py`.</p>
                                <p className="text-amber-200">3. Refresh this web page.</p>
                                <button onClick={onClose} className="mt-6 px-5 py-2 rounded-lg bg-gray-600/50 hover:bg-gray-500/50 text-white">Close</button>
                            </div>
                        ) : (
                            <>
                                <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                                    {fields.map(field => (
                                        <div key={field}>
                                            <label className="block text-sm font-medium text-gray-300 mb-1">{field}</label>
                                            <input type="text" name={field} value={config[field] || ''} onChange={handleChange} className="w-full p-2 bg-slate-900/70 rounded-lg border border-white/20 focus:ring-2 focus:ring-cyan-400 focus:outline-none text-white" />
                                        </div>
                                    ))}
                                </div>
                                <div className="mt-8 flex justify-end items-center space-x-4">
                                    {saveStatus === 'error' && <p className="text-red-400">Error: Could not save.</p>}
                                    <button onClick={onClose} className="px-5 py-2 rounded-lg bg-gray-600/50 hover:bg-gray-500/50 text-white">Cancel</button>
                                    <button onClick={handleSave} disabled={saveStatus === 'saving'} className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold disabled:bg-gray-500 flex items-center">
                                        {saveStatus === 'saving' && <Spinner />}&nbsp;
                                        {saveStatus === 'saving' ? 'Saving...' : 'Save Config'}
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            );
        };

        const ChatMessage = ({ msg }) => {
            const isUser = msg.role === 'user';
            const bubbleBaseStyles = "bubble relative max-w-md lg:max-w-lg px-5 py-3 rounded-2xl text-white shadow-md";
            const userStyles = "bubble-user bg-white/30 self-end";
            const aiStyles = "bubble-ai bg-white/40 self-start";
            return (
                <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`${bubbleBaseStyles} ${isUser ? userStyles : aiStyles}`}>
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                    </div>
                </div>
            );
        };

        const App = () => {
            const [user, setUser] = useState(null);
            const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hello! How can I help you today?' }]);
            const [userInput, setUserInput] = useState('');
            const [isLoading, setIsLoading] = useState(false);
            const [model, setModel] = useState(null);
            const [isSettingsOpen, setIsSettingsOpen] = useState(false);
            const [firebaseConfig, setFirebaseConfig] = useState({});
            const [firebaseReady, setFirebaseReady] = useState(false);
            const chatContainerRef = useRef(null);

            useEffect(() => {
                fetch('/api/config').then(res => res.json()).then(data => {
                    setFirebaseConfig(data);
                    if (window.firebase) {
                        setFirebaseReady(true);
                    } else if (!data || !data.apiKey) {
                        setIsSettingsOpen(true);
                    }
                });
                fetch(`${API_BASE_URL}/api/models`).then(res => res.json()).then(data => {
                    if (data.data && data.data.length > 0) setModel(data.data[0].id);
                });
            }, []);

            useEffect(() => {
                if (!firebaseReady) return;
                const { auth, onAuthStateChanged, signInAnonymously } = window.firebase;
                const unsubscribe = onAuthStateChanged(auth, currentUser => {
                    if (currentUser) setUser(currentUser);
                    else signInAnonymously(auth);
                });
                return unsubscribe;
            }, [firebaseReady]);

            useEffect(() => {
                if (!user || !firebaseReady) return;
                const { db, doc, onSnapshot } = window.firebase;
                const docRef = doc(db, "chats", CHAT_DOC_ID);
                const unsubscribe = onSnapshot(docRef, (docSnap) => {
                    if (docSnap.exists() && docSnap.data().messages) {
                        setMessages(docSnap.data().messages);
                    }
                }, (error) => {
                    console.error("Firestore error:", error);
                    alert("Firestore connection error. Check your security rules and ensure the database is created.");
                });
                return () => unsubscribe();
            }, [user, firebaseReady]);

            useEffect(() => {
                chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
            }, [messages]);

            const handleSendMessage = async (e) => {
                e.preventDefault();
                if (!userInput.trim() || isLoading || !model || !user || !firebaseReady) return;
                const newUserMessage = { role: 'user', content: userInput.trim() };
                const updatedMessages = [...messages, newUserMessage];
                setIsLoading(true);
                setUserInput('');
                const { db, doc, setDoc } = window.firebase;
                await setDoc(doc(db, "chats", CHAT_DOC_ID), { messages: updatedMessages, userId: user.uid });
                try {
                    const response = await fetch(`${API_BASE_URL}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: updatedMessages, model }) });
                    if (!response.ok) throw new Error((await response.json()).details || 'Unknown error');
                    const data = await response.json();
                    const assistantMessage = data.choices[0].message;
                    await setDoc(doc(db, "chats", CHAT_DOC_ID), { messages: [...updatedMessages, assistantMessage], userId: user.uid });
                } catch (error) {
                    const errorMessage = { role: 'error', content: `Error: ${error.message}` };
                    await setDoc(doc(db, "chats", CHAT_DOC_ID), { messages: [...updatedMessages, errorMessage], userId: user.uid });
                } finally {
                    setIsLoading(false);
                }
            };

            if (!firebaseReady && !isSettingsOpen) {
                return <div className="flex items-center justify-center h-screen text-white text-lg"><Spinner/>&nbsp;Loading Configuration...</div>
            }

            return (
                <>
                    <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} currentConfig={firebaseConfig} />
                    <div className="flex items-center justify-center h-screen w-screen p-4">
                        <div className="glass-panel w-full max-w-4xl h-[90vh] max-h-[800px] rounded-3xl flex flex-col p-6">
                            <div className="flex-shrink-0 flex items-center justify-between pb-4 border-b border-white/20">
                                <div className="flex items-center space-x-3">
                                    <Icon path={ICONS.chatbot} className="w-8 h-8 text-white" />
                                    <h1 className="text-xl font-bold text-white">{model ? model.split('/').pop().replace(/-/g, ' ') : 'AI Language Model'}</h1>
                                </div>
                                <button onClick={() => setIsSettingsOpen(true)} className="p-2 rounded-full hover:bg-white/10 transition-colors"><Icon path={ICONS.settings} className="w-6 h-6 text-white"/></button>
                            </div>
                            <div ref={chatContainerRef} className="flex-1 py-6 overflow-y-auto chat-area">
                                <div className="space-y-6 pr-4">
                                    {messages.map((msg, index) => <ChatMessage key={index} msg={msg} />)}
                                    {isLoading && <div className="flex justify-start"><div className="bubble bubble-ai bg-white/40 max-w-md lg:max-w-lg px-5 py-3 rounded-2xl text-white shadow-md flex items-center space-x-2"><Spinner /> <span>Thinking...</span></div></div>}
                                </div>
                            </div>
                            <div className="flex-shrink-0 pt-4">
                                <form onSubmit={handleSendMessage} className="flex items-center space-x-4 bg-black/20 rounded-full p-2 border border-white/20">
                                    <input type="text" value={userInput} onChange={e => setUserInput(e.target.value)} placeholder="Type your message..." className="flex-1 bg-transparent px-4 text-white placeholder-gray-300 focus:outline-none" disabled={isLoading || !model || !firebaseReady} />
                                    <button type="submit" className="bg-white/30 rounded-full p-3 text-white hover:bg-white/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed" disabled={isLoading || !userInput.trim() || !firebaseReady}><Icon path={ICONS.send} className="w-5 h-5" /></button>
                                </form>
                            </div>
                        </div>
                    </div>
                </>
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
    config_data = load_firebase_config()
    config_json = json.dumps(config_data)
    return INDEX_HTML.replace('__FIREBASE_CONFIG_PLACEHOLDER__', config_json)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'POST':
        config_data = request.get_json()
        if config_data:
            save_firebase_config(config_data)
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "No data received"}), 400
    else: # GET
        return jsonify(load_firebase_config())

@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/models")
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Could not connect to LM Studio server.", "details": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_proxy():
    try:
        data = request.get_json()
        if 'messages' not in data or 'model' not in data:
            return jsonify({"error": "Missing 'messages' or 'model' in request body"}), 400
        payload = {
            "model": data['model'], "messages": data['messages'],
            "temperature": data.get("temperature", 0.7), "max_tokens": data.get("max_tokens", -1),
            "stream": False,
        }
        response = requests.post(f"{LM_STUDIO_BASE_URL}/chat/completions", headers={"Content-Type": "application/json"}, data=json.dumps(payload))
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
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
