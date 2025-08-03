# app.py
# ---
# Enhanced Flask application with multiple themes and improved UI
# Features glassmorphism effects, 5 contrasting themes, and chat management

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
    <title>AI Chat - Enhanced</title>

    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

    <script type="module">
        const firebaseConfig = __FIREBASE_CONFIG_PLACEHOLDER__;

        if (firebaseConfig && firebaseConfig.apiKey) {
            try {
                const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
                const { getFirestore, collection, doc, onSnapshot, setDoc, addDoc, updateDoc, deleteDoc, query, where, orderBy, serverTimestamp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
                const { getAuth, signInAnonymously, onAuthStateChanged } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");

                const app = initializeApp(firebaseConfig);
                const db = getFirestore(app);
                const auth = getAuth(app);
                window.firebase = { db, auth, collection, doc, onSnapshot, setDoc, addDoc, updateDoc, deleteDoc, query, where, orderBy, serverTimestamp, signInAnonymously, onAuthStateChanged };
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');

        :root {
            --theme-font: 'Inter', sans-serif;
        }

        body {
            font-family: var(--theme-font);
            transition: background 0.5s ease;
        }

        /* Theme: Cosmic Purple (Default) */
        .theme-cosmic {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        /* Theme: Ocean Depths */
        .theme-ocean {
            background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%);
        }

        /* Theme: Sunset Blaze */
        .theme-sunset {
            background: linear-gradient(135deg, #FA8BFF 0%, #2BD2FF 52%, #2BFF88 100%);
        }

        /* Theme: Midnight Forest */
        .theme-forest {
            background: linear-gradient(135deg, #134E5E 0%, #71B280 100%);
        }

        /* Theme: Aurora Borealis */
        .theme-aurora {
            background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%);
        }

        .glass-panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }

        .glass-panel-dark {
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .glass-button {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }

        .glass-button:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .chat-area::-webkit-scrollbar { width: 8px; }
        .chat-area::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 4px; }
        .chat-area::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
            transition: background 0.3s;
        }
        .chat-area::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.5); }

        .sidebar-transition { transition: transform 300ms cubic-bezier(0.4, 0, 0.2, 1); }

        .message-bubble {
            animation: fadeInUp 0.3s ease;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.7;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }

        .theme-selector {
            backdrop-filter: blur(10px);
        }

        .delete-confirmation {
            animation: slideDown 0.3s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body class="theme-cosmic">
    <div id="root" class="overflow-hidden h-screen"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef } = React;
        const API_BASE_URL = window.location.origin;

        // --- Theme Configuration ---
        const THEMES = {
            cosmic: { name: "Cosmic Purple", class: "theme-cosmic", icon: "🌌" },
            ocean: { name: "Ocean Depths", class: "theme-ocean", icon: "🌊" },
            sunset: { name: "Sunset Blaze", class: "theme-sunset", icon: "🌅" },
            forest: { name: "Midnight Forest", class: "theme-forest", icon: "🌲" },
            aurora: { name: "Aurora Borealis", class: "theme-aurora", icon: "🌌" }
        };

        // --- Helper Components ---
        const Spinner = () => (
            <div className="w-4 h-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin"></div>
        );

        const Icon = ({ path, className = "w-6 h-6" }) => (
            <svg className={className} viewBox="0 0 24 24" fill="currentColor">
                <path d={path}></path>
            </svg>
        );

        const ICONS = {
            send: "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z",
            chatbot: "M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z",
            settings: "M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69-.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.09.49 0 .61.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z",
            history: "M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8H12z",
            close: "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
            pin: "M17 4a2 2 0 0 0-2-2H9c-1.1 0-2 .9-2 2v7l-2 3v2h6v5l1 1 1-1v-5h6v-2l-2-3V4z",
            edit: "M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34a.9959.9959 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z",
            delete: "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
            theme: "M12 2.5l2 4 4.5.5-3.5 3 1 4.5-4-2.5-4 2.5 1-4.5-3.5-3L10 6.5z",
            plus: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"
        };

        const SettingsModal = ({ isOpen, onClose, currentConfig }) => {
            const [config, setConfig] = useState(currentConfig);
            const [saveStatus, setSaveStatus] = useState('idle');

            useEffect(() => { setConfig(currentConfig) }, [currentConfig]);

            const handleChange = (e) => setConfig({ ...config, [e.target.name]: e.target.value });

            const handleSave = async () => {
                setSaveStatus('saving');
                try {
                    const response = await fetch('/api/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
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
                    <div className="p-8 rounded-3xl glass-panel w-full max-w-lg">
                        <h2 className="text-2xl font-bold text-white mb-6">Firebase Configuration</h2>
                        {saveStatus === 'success' ? (
                            <div className="text-center p-6 bg-green-500/20 border border-green-400/50 rounded-2xl">
                                <h3 className="font-bold text-lg text-green-300 mb-2">✨ Success!</h3>
                                <p className="text-amber-300 font-semibold mt-4">ACTION REQUIRED:</p>
                                <p className="text-amber-200">1. Stop the Python server (Ctrl+C)</p>
                                <p className="text-amber-200">2. Restart it: `python3 app.py`</p>
                                <p className="text-amber-200">3. Refresh this web page</p>
                                <button onClick={onClose} className="mt-6 px-6 py-3 rounded-xl glass-button text-white font-medium">
                                    Close
                                </button>
                            </div>
                        ) : (
                            <>
                                <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                                    {fields.map(field => (
                                        <div key={field}>
                                            <label className="block text-sm font-medium text-gray-200 mb-2">
                                                {field}
                                            </label>
                                            <input
                                                type="text"
                                                name={field}
                                                value={config[field] || ''}
                                                onChange={handleChange}
                                                className="w-full p-3 bg-black/30 rounded-xl border border-white/20 focus:ring-2 focus:ring-cyan-400 focus:outline-none text-white placeholder-gray-400"
                                            />
                                        </div>
                                    ))}
                                </div>
                                <div className="mt-8 flex justify-end items-center space-x-4">
                                    {saveStatus === 'error' && (
                                        <p className="text-red-400">Error: Could not save.</p>
                                    )}
                                    <button onClick={onClose} className="px-6 py-3 rounded-xl glass-button text-white font-medium">
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleSave}
                                        disabled={saveStatus === 'saving'}
                                        className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold disabled:opacity-50 flex items-center hover:shadow-lg transition-shadow"
                                    >
                                        {saveStatus === 'saving' && <Spinner />}
                                        &nbsp;{saveStatus === 'saving' ? 'Saving...' : 'Save Config'}
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
            const isError = msg.role === 'error';

            const bubbleBaseStyles = "message-bubble relative max-w-md lg:max-w-lg px-5 py-3 rounded-2xl text-white shadow-lg";
            const userStyles = "bg-gradient-to-br from-white/20 to-white/10 self-end ml-auto";
            const aiStyles = "bg-gradient-to-br from-white/25 to-white/15 self-start";
            const errorStyles = "bg-gradient-to-br from-red-500/30 to-red-600/20 border border-red-400/30 self-start";

            return (
                <div className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`${bubbleBaseStyles} ${isUser ? userStyles : isError ? errorStyles : aiStyles}`}>
                        {!isUser && !isError && (
                            <div className="absolute -left-2 -top-2 w-6 h-6 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center">
                                <span className="text-xs">AI</span>
                            </div>
                        )}
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                </div>
            );
        };

        const App = () => {
            const [user, setUser] = useState(null);
            const [chats, setChats] = useState([]);
            const [activeChatId, setActiveChatId] = useState(null);
            const [userInput, setUserInput] = useState('');
            const [isLoading, setIsLoading] = useState(false);
            const [models, setModels] = useState([]);
            const [selectedModel, setSelectedModel] = useState('');
            const [isSettingsOpen, setIsSettingsOpen] = useState(false);
            const [isHistoryOpen, setIsHistoryOpen] = useState(false);
            const [firebaseConfig, setFirebaseConfig] = useState({});
            const [firebaseReady, setFirebaseReady] = useState(false);
            const [currentTheme, setCurrentTheme] = useState('cosmic');
            const [deleteConfirmId, setDeleteConfirmId] = useState(null);
            const chatContainerRef = useRef(null);

            const activeChat = chats.find(c => c.id === activeChatId);
            const pinnedChats = chats.filter(c => c.pinned);
            const recentChats = chats.filter(c => !c.pinned);

            useEffect(() => {
                // Load saved theme
                const savedTheme = localStorage.getItem('chatTheme') || 'cosmic';
                setCurrentTheme(savedTheme);
                document.body.className = THEMES[savedTheme].class;
            }, []);

            useEffect(() => {
                fetch('/api/config').then(res => res.json()).then(data => {
                    setFirebaseConfig(data);
                    if (window.firebase) setFirebaseReady(true);
                    else if (!data || !data.apiKey) setIsSettingsOpen(true);
                });
                fetch(`${API_BASE_URL}/api/models`).then(res => res.json()).then(data => {
                    const loadedModels = data.data || [];
                    setModels(loadedModels);
                    if (loadedModels.length > 0) setSelectedModel(loadedModels[0].id);
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
                const { db, collection, query, where, orderBy, onSnapshot } = window.firebase;
                const q = query(collection(db, "chats"), where("userId", "==", user.uid), orderBy("createdAt", "desc"));
                const unsubscribe = onSnapshot(q, (querySnapshot) => {
                    const chatsData = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
                    setChats(chatsData);
                    if (!activeChatId && chatsData.length > 0) setActiveChatId(chatsData[0].id);
                }, (error) => {
                    console.error("Firestore error:", error);
                    alert("Firestore connection error. Please ensure your security rules and index are correct.");
                });
                return () => unsubscribe();
            }, [user, firebaseReady]);

            useEffect(() => {
                chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
            }, [activeChat?.messages]);

            const handleThemeChange = (theme) => {
                setCurrentTheme(theme);
                document.body.className = THEMES[theme].class;
                localStorage.setItem('chatTheme', theme);
            };

            const handleNewChat = async () => {
                if (!user || !firebaseReady) return;
                const { db, collection, addDoc, serverTimestamp } = window.firebase;
                const newChat = {
                    title: "New Chat",
                    messages: [{ role: 'assistant', content: 'Hello! How can I help you today?' }],
                    createdAt: serverTimestamp(),
                    userId: user.uid,
                    pinned: false,
                };
                const docRef = await addDoc(collection(db, "chats"), newChat);
                setActiveChatId(docRef.id);
                setIsHistoryOpen(false);
            };

            const handleDeleteChat = async (chatId) => {
                if (!firebaseReady) return;
                const { db, doc, deleteDoc } = window.firebase;
                await deleteDoc(doc(db, "chats", chatId));
                setDeleteConfirmId(null);
                if (chatId === activeChatId) {
                    const remainingChats = chats.filter(c => c.id !== chatId);
                    if (remainingChats.length > 0) {
                        setActiveChatId(remainingChats[0].id);
                    } else {
                        handleNewChat();
                    }
                }
            };

            const handleSendMessage = async (e) => {
                e.preventDefault();
                if (!userInput.trim() || isLoading || !selectedModel || !activeChat || !firebaseReady) return;
                const newUserMessage = { role: 'user', content: userInput.trim() };
                const updatedMessages = [...activeChat.messages, newUserMessage];
                setIsLoading(true);
                setUserInput('');
                const { db, doc, updateDoc } = window.firebase;
                const docRef = doc(db, "chats", activeChatId);
                const isNewChat = activeChat.title === "New Chat";
                const newTitle = isNewChat ? userInput.trim().substring(0, 30) : activeChat.title;
                await updateDoc(docRef, { messages: updatedMessages, title: newTitle });
                try {
                    const response = await fetch(`${API_BASE_URL}/api/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ messages: updatedMessages, model: selectedModel })
                    });
                    if (!response.ok) throw new Error((await response.json()).details || 'Unknown error');
                    const data = await response.json();
                    const assistantMessage = data.choices[0].message;
                    await updateDoc(docRef, { messages: [...updatedMessages, assistantMessage] });
                } catch (error) {
                    const errorMessage = { role: 'error', content: `Error: ${error.message}` };
                    await updateDoc(docRef, { messages: [...updatedMessages, errorMessage] });
                } finally {
                    setIsLoading(false);
                }
            };

            const HistoryItem = ({ chat, onSelect, onDelete, deleteConfirmId, setDeleteConfirmId }) => {
                const [isEditing, setIsEditing] = useState(false);
                const [title, setTitle] = useState(chat.title);
                const { db, doc, updateDoc } = window.firebase;

                const handleRename = async (e) => {
                    e.preventDefault();
                    if (title.trim() && title.trim() !== chat.title) {
                        await updateDoc(doc(db, "chats", chat.id), { title: title.trim() });
                    }
                    setIsEditing(false);
                };

                const handleTogglePin = async (e) => {
                    e.stopPropagation();
                    await updateDoc(doc(db, "chats", chat.id), { pinned: !chat.pinned });
                };

                return (
                    <>
                        <div
                            onClick={onSelect}
                            className={`group p-3 rounded-xl cursor-pointer transition-all ${
                                activeChatId === chat.id
                                    ? 'bg-white/25 shadow-lg'
                                    : 'hover:bg-white/15'
                            }`}
                        >
                            <div className="flex items-center justify-between">
                                {isEditing ? (
                                    <form onSubmit={handleRename} className="flex-grow">
                                        <input
                                            type="text"
                                            value={title}
                                            onChange={e => setTitle(e.target.value)}
                                            onBlur={handleRename}
                                            autoFocus
                                            className="w-full bg-transparent text-white outline-none border-b border-white/30"
                                        />
                                    </form>
                                ) : (
                                    <p className="text-white font-medium text-sm truncate">{chat.title}</p>
                                )}
                                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={handleTogglePin}
                                        className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                                        title="Pin chat"
                                    >
                                        <Icon path={ICONS.pin} className={`w-4 h-4 ${chat.pinned ? 'text-yellow-300' : 'text-white/60'}`} />
                                    </button>
                                    <button
                                        onClick={(e) => {e.stopPropagation(); setIsEditing(true)}}
                                        className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                                        title="Edit title"
                                    >
                                        <Icon path={ICONS.edit} className="w-4 h-4 text-white/60" />
                                    </button>
                                    <button
                                        onClick={(e) => {e.stopPropagation(); setDeleteConfirmId(chat.id)}}
                                        className="p-1.5 hover:bg-red-500/30 rounded-lg transition-colors"
                                        title="Delete chat"
                                    >
                                        <Icon path={ICONS.delete} className="w-4 h-4 text-white/60 hover:text-red-400" />
                                    </button>
                                </div>
                            </div>
                            <p className="text-gray-300 text-xs mt-1">
                                {new Date(chat.createdAt?.seconds * 1000).toLocaleDateString()}
                            </p>
                        </div>

                        {deleteConfirmId === chat.id && (
                            <div className="delete-confirmation p-3 mt-2 rounded-xl bg-red-500/20 border border-red-400/30">
                                <p className="text-white text-sm mb-2">Delete this chat?</p>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => onDelete(chat.id)}
                                        className="px-3 py-1 bg-red-500/50 hover:bg-red-500/70 rounded-lg text-white text-sm transition-colors"
                                    >
                                        Delete
                                    </button>
                                    <button
                                        onClick={() => setDeleteConfirmId(null)}
                                        className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm transition-colors"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                );
            };

            if (!firebaseReady && !isSettingsOpen) {
                return (
                    <div className="flex items-center justify-center h-screen text-white text-lg">
                        <div className="glass-panel p-8 rounded-3xl flex items-center space-x-3">
                            <Spinner/>
                            <span>Loading Configuration...</span>
                        </div>
                    </div>
                );
            }

            return (
                <>
                    <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} currentConfig={firebaseConfig} />

                    {/* History Sidebar Overlay */}
                    {isHistoryOpen && (
                        <div onClick={() => setIsHistoryOpen(false)} className="fixed inset-0 bg-black/40 backdrop-blur-sm z-30"></div>
                    )}

                    <div className={`fixed top-0 left-0 h-full p-4 sidebar-transition z-40 ${isHistoryOpen ? 'translate-x-0' : '-translate-x-full'}`} style={{width: '320px'}}>
                        <div className="h-full glass-panel rounded-3xl p-4 flex flex-col">
                            <div className="flex items-center justify-between mb-6 flex-shrink-0">
                                <h2 className="text-xl font-bold text-white">Chat History</h2>
                                <button
                                    onClick={() => setIsHistoryOpen(false)}
                                    className="p-2 rounded-xl hover:bg-white/10 transition-colors"
                                >
                                    <Icon path={ICONS.close} className="w-6 h-6 text-white"/>
                                </button>
                            </div>

                            <button
                                onClick={handleNewChat}
                                className="w-full mb-4 p-3 rounded-xl glass-button text-white font-medium flex items-center justify-center space-x-2"
                            >
                                <Icon path={ICONS.plus} className="w-5 h-5" />
                                <span>New Chat</span>
                            </button>

                            <div className="space-y-2 overflow-y-auto flex-grow chat-area">
                                {pinnedChats.length > 0 && (
                                    <h3 className="text-xs text-yellow-300 font-semibold uppercase px-2 mb-2">📌 Pinned</h3>
                                )}
                                {pinnedChats.map(chat => (
                                    <HistoryItem
                                        key={chat.id}
                                        chat={chat}
                                        onSelect={() => {setActiveChatId(chat.id); setIsHistoryOpen(false);}}
                                        onDelete={handleDeleteChat}
                                        deleteConfirmId={deleteConfirmId}
                                        setDeleteConfirmId={setDeleteConfirmId}
                                    />
                                ))}

                                {recentChats.length > 0 && (
                                    <h3 className="text-xs text-gray-300 font-semibold uppercase px-2 mt-4 mb-2">Recent</h3>
                                )}
                                {recentChats.map(chat => (
                                    <HistoryItem
                                        key={chat.id}
                                        chat={chat}
                                        onSelect={() => {setActiveChatId(chat.id); setIsHistoryOpen(false);}}
                                        onDelete={handleDeleteChat}
                                        deleteConfirmId={deleteConfirmId}
                                        setDeleteConfirmId={setDeleteConfirmId}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-center h-screen w-screen p-4">
                        <div className="glass-panel w-full max-w-5xl h-[90vh] max-h-[900px] rounded-3xl flex flex-col p-6 shadow-2xl">
                            {/* Header */}
                            <div className="flex-shrink-0 flex items-center justify-between pb-4 border-b border-white/20">
                                <div className="flex items-center space-x-3">
                                    <button
                                        onClick={handleNewChat}
                                        className="p-2.5 rounded-xl glass-button transition-all"
                                        title="New chat"
                                    >
                                        <Icon path={ICONS.chatbot} className="w-7 h-7 text-white"/>
                                    </button>
                                    <button
                                        onClick={() => setIsHistoryOpen(true)}
                                        className="p-2.5 rounded-xl glass-button transition-all"
                                        title="Chat history"
                                    >
                                        <Icon path={ICONS.history} className="w-6 h-6 text-white"/>
                                    </button>
                                </div>

                                <div className="flex items-center space-x-3">
                                    {/* Theme Selector */}
                                    <div className="relative">
                                        <select
                                            value={currentTheme}
                                            onChange={e => handleThemeChange(e.target.value)}
                                            className="theme-selector bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-sm text-white focus:ring-2 focus:ring-white/30 focus:outline-none appearance-none cursor-pointer pr-8"
                                        >
                                            {Object.entries(THEMES).map(([key, theme]) => (
                                                <option key={key} value={key} className="bg-gray-800">
                                                    {theme.icon} {theme.name}
                                                </option>
                                            ))}
                                        </select>
                                        <Icon path={ICONS.theme} className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white pointer-events-none" />
                                    </div>

                                    {/* Model Selector */}
                                    <select
                                        value={selectedModel}
                                        onChange={e => setSelectedModel(e.target.value)}
                                        className="bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-sm text-white focus:ring-2 focus:ring-white/30 focus:outline-none appearance-none cursor-pointer"
                                    >
                                        {models.map(model => (
                                            <option key={model.id} value={model.id} className="bg-gray-800">
                                                {model.id.split('/').pop()}
                                            </option>
                                        ))}
                                    </select>

                                    <button
                                        onClick={() => setIsSettingsOpen(true)}
                                        className="p-2.5 rounded-xl glass-button transition-all"
                                        title="Settings"
                                    >
                                        <Icon path={ICONS.settings} className="w-6 h-6 text-white"/>
                                    </button>
                                </div>
                            </div>

                            {/* Chat Area */}
                            <div ref={chatContainerRef} className="flex-1 py-6 overflow-y-auto chat-area">
                                <div className="space-y-4 pr-4">
                                    {activeChat?.messages.map((msg, index) => (
                                        <ChatMessage key={index} msg={msg} />
                                    ))}
                                    {isLoading && (
                                        <div className="flex justify-start">
                                            <div className="bg-gradient-to-br from-white/25 to-white/15 max-w-md lg:max-w-lg px-5 py-3 rounded-2xl text-white shadow-lg flex items-center space-x-3">
                                                <div className="typing-indicator">
                                                    <div className="typing-dot"></div>
                                                    <div className="typing-dot"></div>
                                                    <div className="typing-dot"></div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Input Area */}
                            <div className="flex-shrink-0 pt-4">
                                <form onSubmit={handleSendMessage} className="flex items-center space-x-3 bg-black/20 rounded-2xl p-2 border border-white/20">
                                    <input
                                        type="text"
                                        value={userInput}
                                        onChange={e => setUserInput(e.target.value)}
                                        placeholder="Type your message..."
                                        className="flex-1 bg-transparent px-4 py-2 text-white placeholder-gray-400 focus:outline-none"
                                        disabled={isLoading || !selectedModel || !firebaseReady}
                                    />
                                    <button
                                        type="submit"
                                        className="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-xl p-3 text-white hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                        disabled={isLoading || !userInput.trim() || !firebaseReady}
                                    >
                                        <Icon path={ICONS.send} className="w-5 h-5" />
                                    </button>
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
