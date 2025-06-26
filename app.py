import os
import uuid
import subprocess
from flask import Flask, request, render_template, send_from_directory, flash, redirect, url_for, after_this_request

# --- Konfigurasi ---
# Folder untuk menyimpan file yang diunggah dan hasil konversi
UPLOAD_FOLDER = 'uploads' 
# Ekstensi file yang diizinkan (untuk keamanan dasar)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'mp3', 'wav', 'm4a', 'pdf', 'docx', 'pptx', 'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Batas ukuran file 50 MB
app.secret_key = 'super-secret-key-change-this' # Ganti dengan kunci rahasia Anda

# --- Fungsi Bantuan ---

def allowed_file(filename):
    """Mengecek apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_converter_command(input_path, output_path, target_format):
    """Membuat perintah command-line untuk konversi berdasarkan format."""
    
    # Logika Konversi Gambar menggunakan ImageMagick
    if target_format in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'ico']:
        return ['/usr/bin/convert', input_path, output_path] # Ditambahkan /usr/bin/ untuk konsistensi

    # Logika Konversi Video/Audio menggunakan FFmpeg
    if target_format in ['mp4', 'webm', 'ogv', 'avi', 'mov', 'mp3', 'wav', 'ogg', 'm4a']:
        return ['/usr/bin/ffmpeg', '-i', input_path, output_path] # Ditambahkan /usr/bin/ untuk konsistensi
    
    # --- LOGIKA PANDOC YANG DIPERLUAS ---
    # Daftar format dokumen yang didukung oleh Pandoc
    supported_doc_formats = ['pdf', 'docx', 'odt', 'html', 'md', 'rtf', 'txt']
    if target_format in supported_doc_formats:
        # Perintah pandoc tetap sama, sangat fleksibel!
        return ['/usr/bin/pandoc', input_path, '-o', output_path]

    # Jika tidak ada kondisi di atas yang cocok, format tidak didukung.
    return None
# --- Rute Aplikasi (Routes) ---

@app.route('/', methods=['GET'])
def index():
    """Menampilkan halaman utama."""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    """Menangani proses unggah dan konversi file."""
    if 'file' not in request.files:
        flash('Tidak ada bagian file')
        return redirect(url_for('index'))
        
    file = request.files['file']
    target_format = request.form.get('format')

    if file.filename == '':
        flash('Tidak ada file yang dipilih')
        return redirect(url_for('index'))

    if not target_format:
        flash('Format tujuan harus dipilih')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # Buat nama file yang aman dan unik untuk menghindari konflik
        original_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_id = uuid.uuid4().hex
        
        input_filename = f"{unique_id}.{original_extension}"
        output_filename = f"{unique_id}.{target_format}"
        
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # Simpan file yang diunggah
        file.save(input_path)
        
        # Atur penghapusan file input setelah request selesai
        @after_this_request
        def cleanup_input(response):
            try:
                # Untuk LibreOffice, file output memiliki nama yang sama dengan input
                # jadi kita periksa apakah file output sudah ada dengan nama yang berbeda
                real_output_filename = f"{unique_id}.{target_format}"
                real_output_path = os.path.join(app.config['UPLOAD_FOLDER'], real_output_filename)

                # Jika nama output berbeda dari input, hapus input
                if os.path.exists(input_path) and input_path != real_output_path:
                     os.remove(input_path)
            except Exception as e:
                app.logger.error(f"Error saat membersihkan file input: {e}")
            return response

        try:
            # Dapatkan perintah konversi
            command = get_converter_command(input_path, output_path, target_format)

            if command is None:
                flash(f'Konversi dari .{original_extension} ke .{target_format} tidak didukung.')
                return redirect(url_for('index'))

            # Jalankan perintah konversi di shell
            subprocess.run(command, check=True, timeout=120) # Timeout 2 menit

            # LibreOffice menghasilkan file dengan nama yang sama, hanya ekstensi berbeda.
            # Kita perlu rename jika perlu atau temukan file yang benar.
            if command[0] == 'libreoffice':
                # Nama output yang dihasilkan LibreOffice
                libre_output_filename = f"{unique_id}.{target_format}"
                libre_output_path = os.path.join(app.config['UPLOAD_FOLDER'], libre_output_filename)
                
                if not os.path.exists(libre_output_path):
                    raise FileNotFoundError("File hasil konversi LibreOffice tidak ditemukan.")
                
                output_path = libre_output_path # Gunakan path yang benar

            # Atur penghapusan file output setelah diunduh
            @after_this_request
            def cleanup_output(response):
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except Exception as e:
                    app.logger.error(f"Error saat membersihkan file output: {e}")
                return response
            
            # Kirim file hasil konversi untuk diunduh
            return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_path), as_attachment=True)

        except subprocess.CalledProcessError as e:
            flash(f'Terjadi error saat konversi: Perintah gagal.')
            app.logger.error(f"Conversion command failed: {e}")
            return redirect(url_for('index'))
        except subprocess.TimeoutExpired:
            flash('Proses konversi terlalu lama (melebihi batas waktu). Coba dengan file yang lebih kecil.')
            return redirect(url_for('index'))
        except FileNotFoundError:
             flash('Error: Alat konversi (misalnya FFmpeg/LibreOffice) tidak ditemukan. Pastikan sudah terinstal dan ada di PATH sistem.')
             return redirect(url_for('index'))
        except Exception as e:
            flash(f'Terjadi error yang tidak diketahui: {e}')
            app.logger.error(f"An unknown error occurred: {e}")
            return redirect(url_for('index'))

    else:
        flash('Jenis file tidak diizinkan.')
        return redirect(url_for('index'))


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True) # Set debug=False untuk production
