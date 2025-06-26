# VERSI FINAL app.py DENGAN LOGIKA LIBREOFFICE SEBAGAI CADANGAN
import os
import uuid
import subprocess
from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for, after_this_request
from werkzeug.utils import secure_filename
# Library pdf2docx masih bisa kita simpan sebagai opsi
from pdf2docx import Converter

# --- Konfigurasi ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mp3', 'wav', 'm4a', 'pdf', 'docx', 'pptx', 'xlsx', 'bmp', 'tiff', 'ico', 'odt', 'mp4', 'rtf', 'md', 'html', 'mkv', 'webm', 'ogg', 'flac', 'md', 'rtf', 'txt', 'epub', 'tex'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # Naikkan jadi 100MB
app.secret_key = 'super-secret-key-change-this'

# (Fungsi allowed_file, get_subprocess_command, dan convert_pdf_to_docx tetap sama seperti sebelumnya)
# ... (Anda bisa copy-paste dari kode sebelumnya atau biarkan saja jika tidak berubah)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# GANTI FUNGSI LAMA DENGAN VERSI SUPER INI
def get_subprocess_command(input_path, output_path, original_format, target_format):
    """Membuat perintah command-line untuk Pandoc, FFmpeg, ImageMagick."""
    
    # === GAMBAR (ImageMagick) ===
    image_formats = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff']
    # PDF bisa menjadi input untuk konversi ke gambar
    if original_format in image_formats + ['pdf'] and target_format in image_formats + ['ico']:
        # Ambil halaman pertama jika inputnya PDF
        input_spec = f'{input_path}[0]' if original_format == 'pdf' else input_path
        return ['/usr/bin/convert', input_spec, output_path]

    # === VIDEO & AUDIO (FFmpeg) ===
    media_formats = ['mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'm4a', 'ogg', 'flac']
    if original_format in media_formats and target_format in media_formats:
        return ['/usr/bin/ffmpeg', '-i', input_path, output_path]

    # === DOKUMEN (Pandoc) - SEKARANG JAUH LEBIH KUAT ===
    # Daftar format input dokumen yang didukung Pandoc
    pandoc_input_formats = ['docx', 'odt', 'html', 'md', 'rtf', 'txt', 'epub', 'tex']
    # Daftar format output dokumen yang didukung Pandoc
    pandoc_output_formats = ['pdf', 'docx', 'odt', 'html', 'md', 'rtf', 'txt', 'epub']
    
    if original_format in pandoc_input_formats and target_format in pandoc_output_formats:
        # Pandoc sangat fleksibel, perintahnya tetap sama!
        return ['/usr/bin/pandoc', input_path, '-o', output_path]

    # Jika tidak ada kondisi di atas yang cocok, format tidak didukung.
    return None
def convert_pdf_to_docx_p2d(input_path, output_path):
    try:
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()
        return True
    except Exception:
        return False

# --- Rute Aplikasi ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    # ... (Bagian awal validasi file tetap sama)
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
        # Membersihkan nama file asli untuk keamanan
        safe_filename = secure_filename(file.filename)
        # Menghilangkan ekstensi asli
        filename_base = os.path.splitext(safe_filename)[0]
        # Gunakan nama file asli untuk output, dan nama unik untuk input sementara
        unique_id = uuid.uuid4().hex
        input_filename = f"{unique_id}.{original_extension}"
        output_filename = f"{filename_base}.{target_format}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        file.save(input_path)

        @after_this_request
        def cleanup_input(response):
            try:
                if os.path.exists(input_path): os.remove(input_path)
            except Exception: pass
            return response

        success = False

        # === LOGIKA KONVERSI DENGAN PRIORITAS ===
        # Prioritas 1: Coba LibreOffice untuk PDF ke DOCX (kualitas terbaik jika berhasil)
        if original_extension == 'pdf' and target_format == 'docx':
            try:
                output_dir = os.path.dirname(input_path)
                command = ['/usr/bin/libreoffice', '--headless', '--convert-to', 'docx', '--outdir', output_dir, input_path]
                subprocess.run(command, check=True, timeout=120)
                # Ganti nama file output LibreOffice agar sesuai dengan nama unik kita
                generated_file = os.path.join(output_dir, f"{unique_id}.docx")
                if os.path.exists(generated_file):
                    # Pindahkan ke nama file output yang kita inginkan jika berbeda (jarang terjadi)
                    os.rename(generated_file, output_path)
                    success = True
            except Exception as e:
                app.logger.error(f"LibreOffice failed: {e}. Falling back to pdf2docx.")
                success = False # Pastikan gagal jika LibreOffice error

            # Prioritas 2: Jika LibreOffice gagal, coba pdf2docx sebagai cadangan
            if not success:
                success = convert_pdf_to_docx_p2d(input_path, output_path)

        # Kasus lain: Gunakan subprocess command untuk semua konversi lainnya
        else:
            command = get_subprocess_command(input_path, output_path, original_extension, target_format)
            if command:
                try:
                    subprocess.run(command, check=True, timeout=120)
                    success = True
                except Exception as e:
                    app.logger.error(f"Subprocess failed: {e}")
                    success = False
            else:
                flash(f"Konversi dari .{original_extension} ke .{target_format} tidak didukung.")
                return redirect(url_for('index'))

        # ... (Bagian akhir untuk handling hasil tetap sama)
        if success and os.path.exists(output_path):
            @after_this_request
            def cleanup_output(response):
                try:
                    if os.path.exists(output_path): os.remove(output_path)
                except Exception: pass
                return response
            return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)
        else:
            flash('Terjadi error saat konversi: Kualitas mungkin buruk atau konversi gagal total.')
            return redirect(url_for('index'))

    else:
        flash('Jenis file tidak diizinkan.')
        return redirect(request.url)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
