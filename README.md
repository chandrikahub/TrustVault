# TrustVault

TrustVault is a Python Flask web application for controlled document sharing, user management, and activity tracking.

## Features

- Login-based access to the application.
- Administrative user management.
- Document upload and storage.
- Sharing documents with selected users through permissions.
- Server-side permission checks before downloading documents.
- Audit history for recorded application activities.

## Technology Stack

- Python
- Flask
- SQLite
- HTML and CSS
- Git and GitHub
- Render

## Prerequisites

- Python 3 installed.
- Git installed.
- A web browser.

## Run Locally on Windows

Clone the repository:

```bash
git clone https://github.com/chandrikahub/TrustVault.git
cd TrustVault
```

Create and activate a virtual environment:

```bash
py -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set a local Flask secret key in PowerShell:

```powershell
$env:TRUSTVAULT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Start the application:

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Configuration

The application reads `TRUSTVAULT_SECRET_KEY` from an environment variable. Use a strong, randomly generated value. Never commit secret keys or passwords to GitHub.

Before running the application, review `app.py` to understand how the initial administrator account is created and how local database initialization works. Do not use a default demo password in a public deployment.

## Security Notes and Limitations

- Document download access is intended to be checked on the server.
- Only test documents should be used for this demonstration.
- The application currently uses SQLite and local file storage. On hosting platforms with ephemeral filesystems, database records and uploaded documents may be lost after restarts or redeployments.
- Automated authorization tests and broader security testing still need to be verified.

## Deployment

The application is deployed on Render:

https://trustvault-7zlh.onrender.com

The live service may take time to wake up after a period of inactivity.

## Project Status

This project demonstrates role-based document sharing and activity logging. Further work is needed to strengthen automated testing, persistent storage, and production security.
