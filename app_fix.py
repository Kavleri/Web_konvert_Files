# GANTI TOTAL ISI app.py DENGAN KODE BARU INI
import os
import uuid
import subprocess
from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for, after_this_request
from pdf2docx import Converter # <- Import library baru

# --- Konfigurasi ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mp3', 'wav', 'm4a', 'pdf', 'docx', 'pptx', 'xlsx', 'odt', 'rtf', 'md', 'html'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.secret_key = 'super-secret-key-change-this'

# --- Fungsi Bantuan ---
def allowed_file(filename):
    """Mengecek apakah ekstensi file diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_subprocess_command(input_path, output_path, original_format, target_format):
    """Membuat perintah command-line untuk Pandoc, FFmpeg, ImageMagick."""
    # Gambar
    if original_format in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'] and target_format in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'ico', 'pdf']:
        return ['/usr/bin/convert', input_path, output_path]
    # Video/Audio
    if original_format in ['mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'm4a'] and target_format in ['mp4', 'webm', 'avi', 'mov', 'mp3', 'wav', 'm4a', 'ogg']:
        return ['/usr/bin/ffmpeg', '-i', input_path, output_path]
    # Dokumen via Pandoc
    if original_format in ['docx', 'odt', 'html', 'md', 'rtf'] and target_format in ['pdf', 'docx', 'odt', 'html', 'md', 'rtf', 'txt']:
        return ['/usr/bin/pandoc', input_path, '-o', output_path]
    return None

def convert_pdf_to_docx(input_path, output_path):
    """Fungsi khusus untuk konversi PDF ke DOCX menggunakan library."""
    try:
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        return True
    except Exception as e:
        app.logger.error(f"pdf2docx conversion failed: {e}")
        return False

# --- Rute Aplikasi ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        flash('Tidak ada bagian file')
        return redirect(request.url)
    file = request.files['file']
    target_format = request.form.get('format')

    if file.filename == '' or not target_format:
        flash('File atau format tujuan belum dipilih')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        original_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_id = uuid.uuid4().hex
        input_filename = f"{unique_id}.{original_extension}"
        output_filename = f"{unique_id}.{target_format}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        file.save(input_path)

        # Atur file input untuk dihapus setelah request selesai
        @after_this_request
        def cleanup_input(response):
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
            except Exception as e:
                app.logger.error(f"Error cleaning up input file: {e}")
            return response
        
        # === LOGIKA KONVERSI BARU ===
        success = False
        # Kasus 1: Konversi spesial PDF ke DOCX
        if original_extension == 'pdf' and target_format == 'docx':
            success = convert_pdf_to_docx(input_path, output_path)
        # Kasus 2: Konversi lain menggunakan command-line (Pandoc, FFmpeg, dll)
        else:
            command = get_subprocess_command(input_path, output_path, original_extension, target_format)
            if command:
                try:
                    subprocess.run(command, check=True, timeout=120)
                    success = True
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    app.logger.error(f"Subprocess failed: {e}")
                    success = False
            else:
                flash(f"Konversi dari .{original_extension} ke .{target_format} tidak didukung.")
                return redirect(url_for('index'))
        
        # === PENANGANAN HASIL ===
        if success and os.path.exists(output_path):
            # Atur file output untuk dihapus setelah diunduh
            @after_this_request
            def cleanup_output(response):
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception as e:
                    app.logger.error(f"Error cleaning up output file: {e}")
                return response
            return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)
        else:
            flash('Terjadi error saat konversi: Perintah gagal atau konversi tidak didukung.')
            return redirect(url_for('index'))

    else:
        flash('Jenis file tidak diizinkan.')
        return redirect(request.url)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
