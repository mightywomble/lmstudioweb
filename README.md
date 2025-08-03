# LM Studio Glass UI - Enhanced Edition

A stunning, self-hosted web interface for interacting with local language models running in LM Studio. This application provides a modern, responsive UI with chat history, persistence, theme customization, and advanced management features, all running from a single Python script.

![Screenshot](https://i.imgur.com/your-new-screenshot.png) <!-- Placeholder: Replace with a real screenshot of your new app -->

## ✨ Features

### Core Features
- **Beautiful Glassmorphism UI**: Advanced glass-morphic effects with depth and blur
- **Chat History Management**:
  - Slide-out sidebar with organized chat history
  - Pin important chats to the top
  - Edit chat titles inline
  - Delete unwanted chats with confirmation
  - Create new chats with a single click
- **Model Selection**: Dropdown menu to switch between any model loaded in LM Studio
- **Secure Configuration**: Firebase credentials stored separately in `config.py` (git-ignored)
- **Self-Contained**: Entire application in a single `app.py` file for easy deployment

### 🎨 New Features
- **5 Stunning Themes**:
  - 🌌 **Cosmic Purple** - Deep purple galaxy gradient (default)
  - 🌊 **Ocean Depths** - Serene blue-to-cyan gradient
  - 🌅 **Sunset Blaze** - Vibrant multi-color gradient
  - 🌲 **Midnight Forest** - Dark green nature theme
  - 🌌 **Aurora Borealis** - Northern lights inspired blue gradient
- **Enhanced Chat Management**:
  - **Pin/Unpin Chats**: Keep important conversations at the top
  - **Edit Chat Titles**: Rename chats for better organization
  - **Delete Chats**: Remove unwanted conversations with confirmation dialog
- **Improved Visual Design**:
  - Animated message bubbles with smooth fade-in effects
  - Custom typing indicator with animated dots
  - Gradient backgrounds for messages
  - Enhanced hover effects and transitions
  - Professional rounded corners and shadows
  - Better visual hierarchy and spacing
- **Persistent Preferences**: Theme selection saved across sessions

## 🛠 Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: React (served via CDN)
- **Database**: Google Firebase Firestore (for chat history)
- **Styling**: Tailwind CSS (served via CDN)
- **UI Design**: Glassmorphism with multiple theme support

---

## 📋 Setup Guide

Follow these steps to get the enhanced application running on your local machine.

### Step 1: Prerequisites

Ensure you have the following installed:

- **Python 3**: Check with `python3 --version`
- **pip3**: Python's package installer
- **LM Studio**: [Download from the official website](https://lmstudio.ai/)

### Step 2: LM Studio Configuration

1. **Install a Model**: Open LM Studio, search for a model (e.g., "Gemma 2 9B"), and download it
2. **Start the Server**:
   - Navigate to the **Local Server** tab (the `>_` icon on the left)
   - Select your downloaded model at the top
   - Click **"Start Server"**
   - The server will now be running at `http://localhost:1234`

### Step 3: Firebase Project Setup (Required for Chat History)

This application uses Firebase to save your chats. You will need a free Firebase account.

1. **Create a Firebase Project**:
   - Go to the [Firebase Console](https://console.firebase.google.com/)
   - Click **"Add project"**, give it a name (e.g., "LMStudio-Web-UI"), and create it

2. **Create a Web App**:
   - In your project dashboard, click the web icon (`</>`) to add a web app
   - Give it a nickname and click **"Register app"**
   - **You do not need to copy the SDK code shown on screen**

3. **Enable Authentication**:
   - From the left menu, go to **Build > Authentication**
   - Click **"Get started"**
   - Select **"Anonymous"** from the list of providers, enable it, and save

4. **Create Firestore Database**:
   - From the left menu, go to **Build > Firestore Database**
   - Click **"Create database"**
   - Select **"Start in production mode"** and click **Next**
   - Choose a location for your database and click **Enable**

5. **Set Firestore Security Rules** (Updated for delete functionality):
   - In the Firestore Database section, click the **"Rules"** tab
   - Replace the existing text with the following rules:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Allow users to read, write, and delete their own chats
       match /chats/{chatId} {
         allow read: if request.auth != null && request.auth.uid == resource.data.userId;
         allow create: if request.auth != null && request.auth.uid == request.resource.data.userId;
         allow update: if request.auth != null && request.auth.uid == resource.data.userId;
         allow delete: if request.auth != null && request.auth.uid == resource.data.userId;
       }
     }
   }
   ```
   - Click **"Publish"**

6. **Create Firestore Index**:
   - In the Firestore Database section, click the **"Indexes"** tab
   - Click **"Create index"**
   - Configure it exactly as follows:
     - **Collection ID**: `chats`
     - **Fields to index**:
       1. `userId` - **Ascending**
       2. `createdAt` - **Descending**
     - **Query scopes**: Collection
   - Click **"Create"** (this may take a few minutes to build)

### Step 4: Application Setup

1. **Clone the Repository**:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

2. **Create `requirements.txt`**:
   ```
   Flask
   Flask-Cors
   requests
   ```

3. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Create `.gitignore`**:
   ```
   config.py
   __pycache__/
   *.pyc
   .DS_Store
   logs/
   ```

5. **Run the Application**:
   ```bash
   python3 app.py
   ```

6. **Configure Firebase Credentials in the UI**:
   - Open your web browser and navigate to `http://localhost:5010`
   - The settings panel will open automatically
   - Go back to your Firebase project settings (gear icon > Project settings)
   - In the "General" tab, scroll down to "Your apps" section
   - Find your web app and copy the `firebaseConfig` values into the settings panel
   - Click **"Save Config"**

7. **Restart the Server**:
   - Stop the server (`Ctrl+C`)
   - Start it again: `python3 app.py`
   - Refresh your browser

### Step 5: Using the Enhanced Features

#### 🎨 Changing Themes
- Click the theme dropdown in the header (star icon)
- Select from 5 beautiful themes
- Your preference is saved automatically

#### 📌 Managing Chats
- **Pin a Chat**: Click the pin icon to keep important chats at the top
- **Edit Title**: Click the edit icon to rename a chat
- **Delete Chat**: Click the trash icon, then confirm deletion
- **New Chat**: Click the chat bubble icon or the "New Chat" button in the sidebar

#### 💬 Chat Interface
- Type your message in the input field at the bottom
- Select different models from the dropdown
- Watch the animated typing indicator while AI responds
- Error messages appear with distinct red styling

### Step 6: Optional - Running as a Service on macOS

To have the application start automatically and run in the background:

1. **Find your Python 3 Path**:
   ```bash
   which python3
   ```

2. **Create the Service File** (`~/Library/LaunchAgents/com.lmstudio.ui.plist`):
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.lmstudio.ui</string>
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/your/python3</string>
           <string>/path/to/your/app.py</string>
       </array>
       <key>WorkingDirectory</key>
       <string>/path/to/your/project</string>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <true/>
       <key>StandardOutPath</key>
       <string>/path/to/your/project/logs/stdout.log</string>
       <key>StandardErrorPath</key>
       <string>/path/to/your/project/logs/stderr.log</string>
   </dict>
   </plist>
   ```

3. **Create Logs Directory**:
   ```bash
   mkdir logs
   ```

4. **Load and Start the Service**:
   ```bash
   # Load the service
   launchctl load ~/Library/LaunchAgents/com.lmstudio.ui.plist

   # Start the service
   launchctl start com.lmstudio.ui
   ```

#### Service Management Commands
- **Stop**: `launchctl stop com.lmstudio.ui`
- **Unload**: `launchctl unload ~/Library/LaunchAgents/com.lmstudio.ui.plist`
- **Check logs**: `tail -f logs/stdout.log`

## 🚀 What's Next?

Future enhancements could include:
- Export chat history
- Search within chats
- Markdown rendering
- Code syntax highlighting
- File attachments
- Multi-user support
- Custom theme creation
- Voice input/output
- Chat templates

## 📝 License

MIT License - feel free to use and modify as needed!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Troubleshooting

### Delete function not working
- Ensure your Firebase rules include `allow delete` permission
- Check that you're authenticated (anonymous auth should be enabled)
- Verify the rules are published in Firebase Console

### Theme not persisting
- Check browser localStorage is enabled
- Try clearing browser cache if themes aren't switching

### Firebase connection errors
- Verify all Firebase configuration values are correct
- Check that Firestore and Authentication are enabled
- Ensure the index is created and active

---

Built with ❤️ for the local AI community
