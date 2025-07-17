from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
import io

app = Flask(__name__)
CORS(app)

# PDF compression function
def compress_pdf(file_stream, quality='medium'):
    input_pdf = PdfReader(file_stream)
    output_pdf = PdfWriter()

    for page in input_pdf.pages:
        output_pdf.add_page(page)

    compressed_stream = io.BytesIO()
    output_pdf.write(compressed_stream)
    compressed_stream.seek(0)
    return compressed_stream

@app.route('/compress', methods=['POST'])
def compress():
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400

    pdf_file = request.files['pdf']
    quality = request.form.get('quality', 'medium')  # default quality is medium

    compressed_pdf = compress_pdf(pdf_file.stream, quality)

    filename = f"compressed_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return send_file(
        compressed_pdf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)