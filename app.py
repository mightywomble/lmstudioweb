# app.py
# ---
# This single Flask application does two things:
# 1. Serves the React-based web UI (index.html) with a full chat sidebar.
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
LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
APP_PORT = 5010

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- HTML Content ---
# The entire React frontend is stored in this multi-line string.
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
    
    <!-- Firebase SDK -->
    <script type="module">
        import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
        import { getFirestore, collection, onSnapshot, doc, setDoc, addDoc, updateDoc, deleteDoc, query, where, getDocs, serverTimestamp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
        import { getAuth, signInAnonymously, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
        
        // IMPORTANT: Replace with your actual Firebase config
        const firebaseConfig = {
            apiKey: "YOUR_API_KEY",
            authDomain: "YOUR_AUTH_DOMAIN",
            projectId: "YOUR_PROJECT_ID",
            storageBucket: "YOUR_STORAGE_BUCKET",
            messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
            appId: "YOUR_APP_ID"
        };

        // Initialize Firebase
        const app = initializeApp(firebaseConfig);
        const db = getFirestore(app);
        const auth = getAuth(app);

        // Expose to window for React component
        window.firebase = { db, auth, collection, onSnapshot, doc, setDoc, addDoc, updateDoc, deleteDoc, query, where, getDocs, serverTimestamp, signInAnonymously, onAuthStateChanged };
    </script>
    
    <style>
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.25); border-radius: 4px; border: 1px solid rgba(0,0,0,0.2); }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }
        .glass-ui {
            background-color: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        body {
            background-color: #020617;
            background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0);
            background-size: 2rem 2rem;
        }
        .sidebar-transition { transition: width 300ms cubic-bezier(0.2, 0, 0, 1) 0s; }
    </style>
</head>
<body>
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        const API_BASE_URL = window.location.origin;

        // --- Helper Components ---
        const Spinner = () => <div className="w-5 h-5 border-2 border-dashed rounded-full animate-spin border-white"></div>;
        const Icon = ({ path, className = "w-5 h-5" }) => <svg className={className} viewBox="0 0 24 24" fill="currentColor"><path d={path}></path></svg>;
        const ICONS = {
            plus: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
            chat: "M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z",
            pin: "M16 9V4h-2v5h-2V4H8v5H6V4H4v7h2v2h2v2h2v2h2v-2h2v-2h2V9h-2zm-4 5h-2v-2h2v2z",
            edit: "M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34a.9959.9959 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z",
            trash: "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
            menu: "M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z",
            send: "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"
        };
        
        // --- Main Application ---
        const App = () => {
            // State Management
            const [user, setUser] = useState(null);
            const [chats, setChats] = useState([]);
            const [activeChatId, setActiveChatId] = useState(null);
            const [userInput, setUserInput] = useState('');
            const [isLoading, setIsLoading] = useState(false);
            const [isFetchingModels, setIsFetchingModels] = useState(true);
            const [models, setModels] = useState([]);
            const [selectedModel, setSelectedModel] = useState('');
            const [sidebarOpen, setSidebarOpen] = useState(true);
            const chatContainerRef = useRef(null);

            const activeChat = chats.find(c => c.id === activeChatId);

            // --- Firebase Auth & Data Fetching ---
            useEffect(() => {
                const { auth, onAuthStateChanged, signInAnonymously, db, collection, query, where, onSnapshot } = window.firebase;
                onAuthStateChanged(auth, currentUser => {
                    if (currentUser) {
                        setUser(currentUser);
                        const q = query(collection(db, "chats"), where("userId", "==", currentUser.uid));
                        const unsubscribe = onSnapshot(q, (querySnapshot) => {
                            const chatsData = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                            setChats(chatsData.sort((a,b) => (b.createdAt?.seconds || 0) - (a.createdAt?.seconds || 0)));
                            if (!activeChatId && chatsData.length > 0) {
                                setActiveChatId(chatsData[0].id);
                            }
                        });
                        return () => unsubscribe();
                    } else {
                        signInAnonymously(auth);
                    }
                });
            }, [activeChatId]);

            // Fetch Models
            useEffect(() => {
                const fetchModels = async () => {
                    setIsFetchingModels(true);
                    try {
                        const response = await fetch(`${API_BASE_URL}/api/models`);
                        if (!response.ok) throw new Error('Failed to fetch models.');
                        const data = await response.json();
                        const loadedModels = data.data || [];
                        setModels(loadedModels);
                        if (loadedModels.length > 0) setSelectedModel(loadedModels[0].id);
                    } catch (error) { console.error("Error fetching models:", error); } 
                    finally { setIsFetchingModels(false); }
                };
                fetchModels();
            }, []);

            // Auto-scroll chat
            useEffect(() => {
                chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
            }, [activeChat]);

            // --- Handlers ---
            const handleNewChat = async () => {
                const { db, addDoc, collection, serverTimestamp } = window.firebase;
                const newChat = {
                    title: "New Chat",
                    messages: [{ role: 'assistant', content: 'Hello! How can I help you today?' }],
                    createdAt: serverTimestamp(),
                    userId: user.uid,
                    pinned: false,
                };
                const docRef = await addDoc(collection(db, "chats"), newChat);
                setActiveChatId(docRef.id);
            };
            
            const handleSendMessage = async (e) => {
                e.preventDefault();
                if (!userInput.trim() || isLoading || !selectedModel || !activeChat) return;

                const newUserMessage = { role: 'user', content: userInput.trim() };
                const updatedMessages = [...activeChat.messages, newUserMessage];
                
                const { db, doc, updateDoc } = window.firebase;
                await updateDoc(doc(db, "chats", activeChatId), { messages: updatedMessages });

                setUserInput('');
                setIsLoading(true);

                try {
                    const response = await fetch(`${API_BASE_URL}/api/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ messages: updatedMessages, model: selectedModel }),
                    });
                    if (!response.ok) throw new Error((await response.json()).details || 'Unknown error');
                    
                    const data = await response.json();
                    const assistantMessage = data.choices[0].message;
                    await updateDoc(doc(db, "chats", activeChatId), { messages: [...updatedMessages, assistantMessage] });

                } catch (error) {
                    console.error("Error sending message:", error);
                    const errorMessage = { role: 'error', content: `Error: ${error.message}` };
                    await updateDoc(doc(db, "chats", activeChatId), { messages: [...updatedMessages, errorMessage] });
                } finally {
                    setIsLoading(false);
                }
            };
            
            const handleRenameChat = async (chatId, newTitle) => {
                if (!newTitle.trim()) return;
                const { db, doc, updateDoc } = window.firebase;
                await updateDoc(doc(db, "chats", chatId), { title: newTitle.trim() });
            };

            const handleTogglePin = async (chatId, currentStatus) => {
                const { db, doc, updateDoc } = window.firebase;
                await updateDoc(doc(db, "chats", chatId), { pinned: !currentStatus });
            };

            const handleDeleteChat = async (chatId) => {
                if (confirm("Are you sure you want to delete this chat?")) {
                    const { db, doc, deleteDoc } = window.firebase;
                    await deleteDoc(doc(db, "chats", chatId));
                    if(activeChatId === chatId) setActiveChatId(chats.length > 1 ? chats[1].id : null);
                }
            };

            const ChatItem = ({ chat, isActive }) => {
                const [isEditing, setIsEditing] = useState(false);
                const [title, setTitle] = useState(chat.title);

                const onRename = (e) => {
                    e.preventDefault();
                    handleRenameChat(chat.id, title);
                    setIsEditing(false);
                };

                return (
                    <div
                        onClick={() => setActiveChatId(chat.id)}
                        className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer ${isActive ? 'bg-cyan-500/30' : 'hover:bg-white/10'}`}
                    >
                        {isEditing ? (
                            <form onSubmit={onRename} className="flex-grow">
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    onBlur={onRename}
                                    autoFocus
                                    className="w-full bg-transparent text-white focus:outline-none"
                                />
                            </form>
                        ) : (
                            <div className="flex items-center space-x-3 truncate">
                                <Icon path={ICONS.chat} className="w-5 h-5 flex-shrink-0" />
                                <span className="truncate">{chat.title}</span>
                            </div>
                        )}
                        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={(e) => { e.stopPropagation(); handleTogglePin(chat.id, chat.pinned); }} className="p-1 hover:bg-white/20 rounded-md"><Icon path={ICONS.pin} className={`w-4 h-4 ${chat.pinned ? 'text-cyan-400' : ''}`} /></button>
                            <button onClick={(e) => { e.stopPropagation(); setIsEditing(true); }} className="p-1 hover:bg-white/20 rounded-md"><Icon path={ICONS.edit} className="w-4 h-4" /></button>
                            <button onClick={(e) => { e.stopPropagation(); handleDeleteChat(chat.id); }} className="p-1 hover:bg-white/20 rounded-md"><Icon path={ICONS.trash} className="w-4 h-4" /></button>
                        </div>
                    </div>
                );
            };

            // --- Render ---
            if (!user) return <div className="flex items-center justify-center h-screen text-white"><Spinner />&nbsp;Authenticating...</div>;

            return (
                <div className="flex h-screen text-gray-200 font-sans">
                    {/* Sidebar */}
                    <aside className={`flex flex-col glass-ui rounded-r-3xl m-2 p-3 space-y-4 sidebar-transition ${sidebarOpen ? 'w-72' : 'w-20'}`}>
                        <button onClick={handleNewChat} className="flex items-center justify-center space-x-2 w-full p-3 bg-cyan-600 rounded-xl text-white font-bold hover:bg-cyan-500 transition-colors">
                            <Icon path={ICONS.plus} />
                            {sidebarOpen && <span>New Chat</span>}
                        </button>
                        <div className="flex-grow overflow-y-auto pr-1 space-y-4">
                            {sidebarOpen && chats.some(c => c.pinned) && (
                                <div>
                                    <h3 className="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Pinned</h3>
                                    {chats.filter(c => c.pinned).map(chat => <ChatItem key={chat.id} chat={chat} isActive={chat.id === activeChatId} />)}
                                </div>
                            )}
                            {sidebarOpen && (
                                <div>
                                    <h3 className="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Recent</h3>
                                    {chats.filter(c => !c.pinned).map(chat => <ChatItem key={chat.id} chat={chat} isActive={chat.id === activeChatId} />)}
                                </div>
                            )}
                        </div>
                    </aside>

                    {/* Main Content */}
                    <main className="flex-1 flex flex-col p-4">
                        <header className="flex items-center justify-between p-2">
                            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 glass-ui rounded-full hover:bg-white/20"><Icon path={ICONS.menu} /></button>
                            <div className="flex-1 flex justify-center">
                                {isFetchingModels ? (
                                    <span className="text-sm text-gray-300 animate-pulse">Fetching models...</span>
                                ) : models.length > 0 ? (
                                    <select value={selectedModel} onChange={e => setSelectedModel(e.target.value)} className="glass-ui rounded-xl px-4 py-2 text-sm text-white focus:ring-2 focus:ring-cyan-400 focus:outline-none appearance-none text-center cursor-pointer">
                                        {models.map(model => <option key={model.id} value={model.id} className="bg-slate-800">{model.id.split('/').pop()}</option>)}
                                    </select>
                                ) : (
                                    <span className="text-sm text-red-400">No Models Loaded</span>
                                )}
                            </div>
                            <div className="w-10"></div> {/* Spacer */}
                        </header>
                        
                        <div ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto">
                            <div className="max-w-4xl mx-auto space-y-8">
                                {activeChat?.messages.map((msg, index) => {
                                    const isUser = msg.role === 'user';
                                    const isError = msg.role === 'error';
                                    const bubbleClasses = isUser ? 'bg-cyan-500/50 self-end' : isError ? 'bg-red-500/60 self-start' : 'bg-slate-700/60 self-start';
                                    return (
                                        <div key={index} className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`max-w-xl lg:max-w-3xl p-4 rounded-3xl text-white glass-ui ${bubbleClasses}`}>
                                                <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                                            </div>
                                        </div>
                                    );
                                })}
                                {isLoading && <div className="flex justify-start"><div className="p-4 rounded-3xl flex items-center space-x-3 glass-ui bg-slate-700/60"><Spinner /><span className="text-white text-sm">Thinking...</span></div></div>}
                            </div>
                        </div>
                        
                        <footer className="p-4 glass-ui rounded-2xl mx-auto mb-2 w-full max-w-4xl">
                            <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
                                <input type="text" value={userInput} onChange={(e) => setUserInput(e.target.value)} placeholder={selectedModel ? "Message " + selectedModel.split('/').pop() : "Please select a model..."} className="flex-1 p-4 bg-slate-900/50 rounded-xl border border-transparent focus:ring-2 focus:ring-cyan-400 focus:outline-none text-white transition" disabled={isLoading || !selectedModel || !activeChat} />
                                <button type="submit" className="p-4 bg-cyan-600 rounded-xl text-white font-bold hover:bg-cyan-500 disabled:bg-slate-600/50 disabled:cursor-not-allowed transition-colors" disabled={isLoading || !userInput.trim() || !activeChat}><Icon path={ICONS.send}/></button>
                            </form>
                        </footer>
                    </main>
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
    return INDEX_HTML

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
            "model": data['model'],
            "messages": data['messages'],
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", -1),
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
    print(f"   (Access from other devices using your Mac's IP address, e.g., http://192.168.1.XX:{APP_PORT})")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
