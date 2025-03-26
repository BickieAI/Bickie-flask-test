 from flask import Flask, redirect, request, session, jsonify
import os
import logging
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Initialize Flask app
app = Flask(__name__)

# Set up logging configuration (this will log to console by default)
logging.basicConfig(level=logging.DEBUG)

# Session settings for production (ensure cookies are secure)
app.config['SESSION_COOKIE_SECURE'] = True  # Ensure cookies are sent over HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Allow cross-site cookies

# Secret key for Flask sessions
app.secret_key = "J4kH7aL9f8D2g5Z5sV3T5aP1mZ0nL7v9Xy5e9Zz3K1F3iR4"

# OAuth and Google credentials setup
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
CLIENT_SECRETS_FILE = "/etc/secrets/client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT_URI = "https://bickie-flask-test.onrender.com/oauth2callback"


@app.route("/authorize")
def authorize():
    # OAuth flow to request permission from the user
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return redirect(auth_url)


@app.route("/oauth2callback")
def oauth2callback():
    # OAuth callback endpoint to handle token exchange
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=request.url)

    # Save credentials to session
    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
    
    app.logger.debug("Credentials saved in session: %s", session.get("credentials"))

    return "✅ Google Drive is now connected. You can return to Bickie and upload your file."


@app.route("/upload", methods=["POST"])
def upload_file():
    # Debugging output to log request data
    app.logger.debug("Request Headers: %s", request.headers)
    app.logger.debug("FILES: %s", request.files)  # Log the received files
    app.logger.debug("FORM DATA: %s", request.form)  # Log any other form data sent

    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return "🚫 No file provided", 400  # If no file is provided, return error

    filename = uploaded_file.filename
    temp_path = os.path.join("/tmp", filename)
    uploaded_file.save(temp_path)

    creds_dict = session.get("credentials")
    if not creds_dict:
        return "🚫 Not authenticated with Google", 403

    credentials = Credentials(**creds_dict)
    drive_service = build("drive", "v3", credentials=credentials)

    file_metadata = {"name": filename}
    media = MediaFileUpload(temp_path, resumable=True)

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    return jsonify({
        "message": "✅ File uploaded!",
        "link": uploaded.get("webViewLink")
    })


@app.route("/")
def home():
    return "✅ Bickie uploader is working!"


@app.route("/ping")
def ping():
    return "pong"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)