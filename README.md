# LM Studio Glass UI

A sleek, self-hosted web interface for interacting with local language models running in LM Studio. This application provides a modern, responsive UI with chat history, persistence, and management features, all running from a single Python script.

![Screenshot](https://i.imgur.com/example.png) <!-- Placeholder: Replace with a real screenshot of your app -->

## Features

- **Responsive Interface**: A beautiful "glassmorphism" theme that works seamlessly on desktop, tablet, and mobile.
- **Chat Persistence**: Chat history is saved automatically to a Firebase Firestore database.
- **Chat Management**:
    - Create, select, and delete multiple chat sessions.
    - Pin important chats to the top of the list.
    - Rename chats on the fly.
- **Collapsible Sidebar**: Maximize your chat space by collapsing the sidebar.
- **Model Selection**: Dynamically selects from the models currently loaded in your LM Studio server.
- **Secure Configuration**: Firebase credentials are not stored in the main source code. They are entered through the UI and saved locally in a `config.py` file, which can be ignored by Git.
- **Self-Contained**: The entire application (Python backend + React frontend) is contained within a single `app.py` file for easy deployment.

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: React (served via CDN)
- **Database**: Google Firebase Firestore (for chat history)
- **Styling**: Tailwind CSS (served via CDN)

---

## Setup Guide

Follow these steps to get the application running on your local machine (e.g., a Mac Mini).

### Step 1: Prerequisites

Ensure you have the following installed:

- **Python 3**: Check with `python3 --version`.
- **pip3**: Python's package installer.
- **LM Studio**: [Download from the official website](https://lmstudio.ai/).

### Step 2: LM Studio Configuration

1.  **Install a Model**: Open LM Studio, search for a model (e.g., "Gemma 2 9B"), and download it.
2.  **Start the Server**:
    - Navigate to the **Local Server** tab (the `>_` icon on the left).
    - Select your downloaded model at the top.
    - Click **"Start Server"**.
    - The server will now be running at `http://localhost:1234`.

### Step 3: Firebase Project Setup (Required for Chat History)

This application uses Firebase to save your chats. You will need a free Firebase account.

1.  **Create a Firebase Project**:
    - Go to the [Firebase Console](https://console.firebase.google.com/).
    - Click **"Add project"**, give it a name (e.g., "LMStudio-Web-UI"), and create it.

2.  **Create a Web App**:
    - In your project dashboard, click the web icon (`</>`) to add a web app.
    - Give it a nickname and click **"Register app"**.
    - **You do not need to copy the SDK code shown on screen.** We will get the config from a different place.

3.  **Enable Authentication**:
    - From the left menu, go to **Build > Authentication**.
    - Click **"Get started"**.
    - Select **"Anonymous"** from the list of providers, enable it, and save.

4.  **Create Firestore Database**:
    - From the left menu, go to **Build > Firestore Database**.
    - Click **"Create database"**.
    - Select **"Start in production mode"** and click **Next**.
    - Choose a location for your database and click **Enable**.

5.  **Set Firestore Security Rules**:
    - In the Firestore Database section, click the **"Rules"** tab.
    - Replace the existing text with the following rules, which allow users to manage their own chat documents:
      ```
      rules_version = '2';
      service cloud.firestore {
        match /databases/{database}/documents {
          match /chats/{chatId} {
            allow read, update, delete: if request.auth.uid == resource.data.userId;
            allow create: if request.auth.uid == request.resource.data.userId;
          }
        }
      }
      ```
    - Click **"Publish"**.

6.  **Create Firestore Index**:
    - In the Firestore Database section, click the **"Indexes"** tab.
    - Click **"Create index"**.
    - Configure it exactly as follows:
        - **Collection ID**: `chats`
        - **Fields to index**:
            1. `userId` - **Ascending**
            2. `createdAt` - **Descending**
        - **Query scopes**: Collection
    - Click **"Create"**. This may take a few minutes to build.

### Step 4: Application Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create `requirements.txt`**:
    Create a file named `requirements.txt` and add the following lines:
    ```
    Flask
    Flask-Cors
    requests
    ```

3.  **Install Dependencies**:
    ```bash
    pip3 install -r requirements.txt
    ```

4.  **Create `.gitignore`**:
    Create a file named `.gitignore` to ensure your credentials are not committed to Git. Add `config.py` to it:
    ```
    config.py
    __pycache__/
    *.pyc
    ```

5.  **Run the Application**:
    ```bash
    python3 app.py
    ```

6.  **Configure Firebase Credentials in the UI**:
    - Open your web browser and navigate to the server address (e.g., `http://localhost:5010`).
    - The settings panel will open automatically.
    - Go back to your Firebase project settings (click the gear icon > Project settings).
    - In the "General" tab, scroll down to the "Your apps" section.
    - Find your web app and copy the `firebaseConfig` values into the settings panel in the UI.
    - Click **"Save Config"**.

7.  **Restart the Server**:
    - The UI will now instruct you to restart the server.
    - Go to your terminal and stop the server (`Ctrl+C`).
    - Start it again: `python3 app.py`.
    - A `config.py` file will now be present in your project directory.

8.  **Reload the Web Page**:
    - Refresh your browser. The application is now fully configured and ready to use!

### Step 5: Optional - Running as a Service on macOS

To have the application start automatically when you log in and run continuously in the background, you can create a `launchd` service.

1.  **Find your Python 3 Path**:
    First, you need the full path to your `python3` executable. Open your terminal and run:
    ```bash
    which python3
    ```
    Copy the output. It will look something like `/usr/local/bin/python3` or `/opt/homebrew/bin/python3`.

2.  **Create the Service File**:
    Create a new file named `com.david.lmstudioui.plist` in the following directory: `~/Library/LaunchAgents/`.

    *Note: The `~/Library/` folder is hidden by default. In Finder, you can click **Go > Go to Folder...** and paste `~/Library/LaunchAgents/`.*

    Paste the following XML content into the file. **Make sure to replace `/path/to/your/python3` with the actual path you found in the previous step.**

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "[http://www.apple.com/DTDs/PropertyList-1.0.dtd](http://www.apple.com/DTDs/PropertyList-1.0.dtd)">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.david.lmstudioui</string>
        <key>ProgramArguments</key>
        <array>
            <string>/path/to/your/python3</string>
            <string>/Users/david/code/lmstudio_webinterface/app.py</string>
        </array>
        <key>WorkingDirectory</key>
        <string>/Users/david/code/lmstudio_webinterface</string>
        <key>RunAtLoad</key>
        <true/>
        <key>KeepAlive</key>
        <true/>
        <key>StandardOutPath</key>
        <string>/Users/david/code/lmstudio_webinterface/logs/stdout.log</string>
        <key>StandardErrorPath</key>
        <string>/Users/david/code/lmstudio_webinterface/logs/stderr.log</string>
    </dict>
    </plist>
    ```

3.  **Create a Logs Directory**:
    In your project folder (`/Users/david/code/lmstudio_webinterface/`), create a new directory named `logs`. The service will write its output here.
    ```bash
    cd /Users/david/code/lmstudio_webinterface
    mkdir logs
    ```

4.  **Load and Start the Service**:
    Open your terminal and run the following command to load the service. It will start automatically on your next login, but you can start it immediately for the current session.

    ```bash
    # Load the service (makes it active for future logins)
    launchctl load ~/Library/LaunchAgents/com.david.lmstudioui.plist

    # Start the service immediately
    launchctl start com.david.lmstudioui
    ```

The application should now be running in the background. You can access it at `http://localhost:5010`.

#### Managing the Service

-   **To stop the service**:
    ```bash
    launchctl stop com.david.lmstudioui
    ```
-   **To unload the service (so it doesn't start on login anymore)**:
    ```bash
    launchctl unload ~/Library/LaunchAgents/com.david.lmstudioui.plist
    ```
-   **To check the logs**:
    ```bash
    tail -f /Users/david/code/lmstudio_webinterface/logs/stdout.log
    ```

</markdown>