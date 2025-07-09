from flask import Flask, request, send_file
from flask_cors import CORS
import os
from datetime import datetime
from PIL import Image
import fitz  # PyMuPDF
import io

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/compress', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # Convert compressionLevel (1-10) to quality (90-10) and dpi (150-50)
    try:
        compression_level = int(request.form.get('compressionLevel', 5))
    except ValueError:
        compression_level = 5

    quality = max(60, 100 - compression_level * 4)   # JPEG quality
    dpi = max(100, 200 - compression_level * 10)      # DPI for rendering

    # Save uploaded file temporarily
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    # Load the original PDF
    doc = fitz.open(input_path)
    output_pdf = fitz.open()

    for page in doc:
        # Render page to image
        pix = page.get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Compress image to JPEG with desired quality
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="JPEG", quality=quality)
        img_buffer.seek(0)

        # Convert JPEG to PDF page
        img_pdf = fitz.open("pdf", fitz.open("jpeg", img_buffer).convert_to_pdf())
        output_pdf.insert_pdf(img_pdf)

    # Save final PDF to in-memory buffer
    pdf_output_stream = io.BytesIO()
    output_pdf.save(pdf_output_stream)
    pdf_output_stream.seek(0)

    # Cleanup
    doc.close()
    output_pdf.close()
    if os.path.exists(input_path):
        os.remove(input_path)

    # Return the compressed PDF
    return send_file(
        pdf_output_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="compressed.pdf"
    )

if __name__ == '__main__':
    app.run(debug=True, port=8081)
