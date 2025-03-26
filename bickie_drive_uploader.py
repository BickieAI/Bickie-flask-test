from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bickie uploader is working!"

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
