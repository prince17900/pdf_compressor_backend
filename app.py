from flask import Flask, request, send_file, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import tempfile
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import subprocess
import os
import logging

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')


# ✅ Replace with your actual URI
MONGO_URI = "mongodb+srv://admin:Macbok123@logincluster.kybphm5.mongodb.net/?retryWrites=true&w=majority&appName=loginCluster"

client = MongoClient(MONGO_URI)
db = client["compressfast_db"]  # your database
users_collection = db["users"]  # your users collection


# ✅ Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 🔐 Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if not all([email, username, password]):
        return jsonify({'message': 'All fields are required'}), 400

    # Check if user already exists
    if users_collection.find_one({"email": email}):
        return jsonify({'message': 'User already exists'}), 409

    # Save user to DB
    users_collection.insert_one({
        "email": email,
        "username": username,
        "password": generate_password_hash(password)
    })

    return jsonify({'message': 'Signup successful'}), 200

# 🔐 Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({'message': 'Invalid credentials'}), 401

    session['user'] = user['username']
    return jsonify({
        'message': f'Welcome, {user["username"]}!',
        'user': {
            'username': user["username"],
            'email': user["email"]
        }
    }), 200

users_collection.create_index("email", unique=True)


# 📄 PDF Compression Route
@app.route('/compress', methods=['POST'])
def compress_pdf():
    logging.info("Received /compress POST request")

    if 'file' not in request.files:
        logging.warning("No file part in the request")
        return jsonify(error="No file uploaded"), 400

    file = request.files['file']
    if file.filename == '':
        logging.warning("Empty filename submitted")
        return jsonify(error="No selected file"), 400

    try:
        compression_level = int(request.form.get('compressionLevel', 5))
    except ValueError:
        logging.warning("Invalid compression level, using default 5")
        compression_level = 5

    if compression_level <= 3:
        gs_quality = "/screen"
    elif compression_level <= 7:
        gs_quality = "/ebook"
    else:
        gs_quality = "/printer"

    logging.info(f"Using Ghostscript quality: {gs_quality}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as input_pdf:
            file.save(input_pdf.name)
            input_path = input_pdf.name
        logging.info(f"Saved input file: {input_path}")

        ghostscript_output = tempfile.mktemp(suffix=".pdf")

        gs_cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={gs_quality}",
            "-dFastWebView=true",
            "-dSubsetFonts=true",
            "-dDownsampleColorImages=false",
            "-dDownsampleGrayImages=false",
            "-dDownsampleMonoImages=false",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={ghostscript_output}",
            input_path
        ]

        logging.info("Running Ghostscript compression...")
        subprocess.run(gs_cmd, check=True)
        logging.info(f"Ghostscript output: {ghostscript_output}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Ghostscript compression failed: {e}")
        return jsonify(error="Compression failed"), 500
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return jsonify(error="Server error occurred"), 500

    original_filename = request.form.get('originalFilename', 'compressed.pdf')
    base_name, _ = os.path.splitext(original_filename)
    final_filename = f"{base_name}-compressed.pdf"

    logging.info(f"Sending file back with name: {final_filename}")

    return send_file(
        ghostscript_output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=final_filename
    )

# ✅ Health check
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

# ✅ Global error handlers
@app.errorhandler(404)
def not_found(e):
    logging.warning("404 Not Found")
    return jsonify(error="Endpoint not found"), 404

@app.errorhandler(500)
def server_error(e):
    logging.exception("500 Internal Server Error")
    return jsonify(error="Internal server error"), 500

# ✅ Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
