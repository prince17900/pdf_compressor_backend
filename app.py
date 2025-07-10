import subprocess
import tempfile

@app.route('/compress', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    try:
        compression_level = int(request.form.get('compressionLevel', 5))
    except ValueError:
        compression_level = 5

    # Map compression level to Ghostscript quality presets
    if compression_level <= 3:
        gs_quality = "/screen"      # smallest, low quality
    elif compression_level <= 7:
        gs_quality = "/ebook"       # medium quality
    else:
        gs_quality = "/printer"     # high quality

    # Save uploaded PDF to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as input_pdf:
        file.save(input_pdf.name)

    output_pdf_path = tempfile.mktemp(suffix=".pdf")

    # Ghostscript command
    gs_cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={gs_quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pdf_path}",
        input_pdf.name
    ]

    try:
        subprocess.run(gs_cmd, check=True)
    except subprocess.CalledProcessError:
        return "Compression failed", 500

    return send_file(
        output_pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="compressed.pdf"
    )
