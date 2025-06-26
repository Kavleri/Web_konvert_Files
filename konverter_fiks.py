import os
import uuid
import subprocess
import zipfile
import glob
from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for, after_this_request
from werkzeug.utils import secure_filename

# --- Konfigurasi ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'ico', 'mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'm4a', 'ogg', 'flac', 'pdf', 'docx', 'odt', 'html', 'md', 'rtf', 'txt', 'epub', 'tex'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100MB
app.secret_key = 'super-secret-key-change-this'

# --- Fungsi Bantuan ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_subprocess_command(input_path, output_path, original_format, target_format, options={}):
    """Membuat perintah command-line dengan opsi kustom."""
    
    # === GAMBAR (ImageMagick) ===
    image_formats = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff']
    if original_format in image_formats and target_format in image_formats + ['ico', 'pdf']:
        command = ['/usr/bin/convert', input_path]
        # Opsi Kustomisasi Kualitas JPG
        if target_format == 'jpg' or target_format == 'jpeg':
            jpg_quality = options.get('jpg_quality', '85') # Default 85
            command.extend(['-quality', str(jpg_quality)])
        command.append(output_path)
        return command

    # === VIDEO & AUDIO (FFmpeg) ===
    media_formats = ['mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'm4a', 'ogg', 'flac']
    if original_format in media_formats and target_format in media_formats:
        return ['/usr/bin/ffmpeg', '-i', input_path, output_path]

    # === DOKUMEN (Pandoc) ===
    pandoc_input_formats = ['docx', 'odt', 'html', 'md', 'rtf', 'txt', 'epub', 'tex']
    pandoc_output_formats = ['pdf', 'docx', 'odt', 'html', 'md', 'rtf', 'txt', 'epub']
    if original_format in pandoc_input_formats and target_format in pandoc_output_formats:
        return ['/usr/bin/pandoc', input_path, '-o', output_path]

    return None

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
    
    # Ambil opsi kustomisasi dari form
    custom_options = {
        'jpg_quality': request.form.get('jpg_quality', '85')
    }

    if file.filename == '' or not target_format:
        flash('File atau format tujuan belum dipilih')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        original_extension = file.filename.rsplit('.', 1)[1].lower()
        safe_filename = secure_filename(file.filename)
        filename_base = os.path.splitext(safe_filename)[0]
        
        unique_id = uuid.uuid4().hex
        input_filename = f"{unique_id}.{original_extension}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        file.save(input_path)

        # Atur penghapusan file input
        @after_this_request
        def cleanup_input(response):
            if os.path.exists(input_path): os.remove(input_path)
            return response
        
        output_filename = f"{filename_base}.{target_format}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # === FITUR BARU: PDF Multi-Halaman ke ZIP Gambar ===
        if original_extension == 'pdf' and target_format in ['jpg', 'png']:
            try:
                # Buat folder sementara untuk menyimpan gambar hasil konversi
                temp_img_dir = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
                os.makedirs(temp_img_dir, exist_ok=True)
                
                # Perintah ImageMagick untuk mengubah SEMUA halaman
                img_output_pattern = os.path.join(temp_img_dir, f'page-%d.{target_format}')
                command = ['/usr/bin/convert', '-density', '150', input_path, '-quality', '85', img_output_pattern]
                subprocess.run(command, check=True, timeout=300)

                # Buat file ZIP dari semua gambar yang dihasilkan
                zip_filename = f"{filename_base}.zip"
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for img_file in glob.glob(os.path.join(temp_img_dir, f'*.{target_format}')):
                        zipf.write(img_file, os.path.basename(img_file))

                # Hapus gambar dan folder sementara setelah di-zip
                for img_file in glob.glob(os.path.join(temp_img_dir, f'*.{target_format}')):
                    os.remove(img_file)
                os.rmdir(temp_img_dir)
                
                # Atur agar file zip dihapus setelah diunduh
                @after_this_request
                def cleanup_zip(response):
                    if os.path.exists(zip_path): os.remove(zip_path)
                    return response
                
                return send_from_directory(app.config['UPLOAD_FOLDER'], zip_filename, as_attachment=True)

            except Exception as e:
                app.logger.error(f"PDF to images conversion failed: {e}")
                flash('Gagal mengonversi PDF ke gambar.')
                return redirect(url_for('index'))
        
        # === Logika Konversi Standar (untuk semua kasus lain) ===
        command = get_subprocess_command(input_path, output_path, original_extension, target_format, options=custom_options)

        if not command:
            flash(f"Konversi dari .{original_extension} ke .{target_format} tidak didukung.")
            return redirect(url_for('index'))
            
        try:
            subprocess.run(command, check=True, timeout=180)
            if os.path.exists(output_path):
                @after_this_request
                def cleanup_output(response):
                    if os.path.exists(output_path): os.remove(output_path)
                    return response
                return send_from_directory(app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)
            else:
                raise FileNotFoundError("File output tidak ditemukan setelah konversi.")
        except Exception as e:
            app.logger.error(f"Conversion failed for command {command}: {e}")
            flash('Terjadi error saat konversi.')
            return redirect(url_for('index'))
    else:
        flash('Jenis file tidak diizinkan.')
        return redirect(request.url)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
