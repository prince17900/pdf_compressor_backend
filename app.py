from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile
import subprocess
import os
import logging

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)

# ✅ Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

    # Map slider value to Ghostscript quality preset
    if compression_level <= 3:
        gs_quality = "/screen"
    elif compression_level <= 7:
        gs_quality = "/ebook"
    else:
        gs_quality = "/printer"

    logging.info(f"Using Ghostscript quality: {gs_quality}")

    try:
        # Save input file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as input_pdf:
            file.save(input_pdf.name)
            input_path = input_pdf.name
        logging.info(f"Saved input file: {input_path}")

        # Output of Ghostscript
        ghostscript_output = tempfile.mktemp(suffix=".pdf")

        # Run Ghostscript
        gs_cmd = [
    "gs",
    "-sDEVICE=pdfwrite",
    "-dCompatibilityLevel=1.4",
    f"-dPDFSETTINGS={gs_quality}",     # /screen, /ebook, or /printer
    "-dFastWebView=true",              # Speeds up web loading + structure
    "-dSubsetFonts=true",              # Only embeds used characters
    "-dDownsampleColorImages=false",   # Skip slow image downsampling
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

    logging.info("Compression successful, sending file back.")
    return send_file(
        ghostscript_output,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="compressed.pdf"
    )

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
