<h2>Aplikasi Konverter File</h2><br>
<p>Sebuah aplikasi web sederhana yang dibangun dengan Flask untuk mengkonversi berbagai format file secara gratis di lingkungan lokal.</p><br>
<h2>Prasyarat</h2><br>
<p>Sebelum memulai, pastikan sistem Anda (khususnya untuk sistem berbasis Debian/Ubuntu) memiliki semua dependensi yang diperlukan.</p><br>
<li>Python 3.8+</li>
<li>Pandoc</li>
<li>FFmpeg</li>
<li>TeX Live</li>
<li>ImageMagick</li>
<li>Ghostscript</li><br>
<h2>Instalasi & Konfigurasi</h2><br>
<p>Ikuti langkah-langkah berikut untuk menginstal dan menjalankan aplikasi di lingkungan lokal Anda.</p><br>
<li>Buat dan Aktifkan Virtual Environment</li><br>
<p>Perintah ini akan membuat folder venv di direktori proyek Anda untuk mengisolasi dependensi.</p><br>

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

<li>Instal Dependensi Sistem</li><br>
<p>Jalankan perintah berikut untuk menginstal semua tool yang dibutuhkan oleh aplikasi di level sistem operasi.</p><br>

   ```bash
   sudo apt update && sudo apt install pandoc ffmpeg texlive-latex-base texlive-latex-extra imagemagick ghostscript -y
   ```

<li>Instal Paket Python</li><br>
<p>Instal semua paket Python yang diperlukan oleh Flask dan proses konversi.</p><br>

   ```bash
   pip install Flask pdf2docx gunicorn
   ```
<i>Catatan: Disarankan untuk menyimpan daftar paket ini dalam file requirements.txt untuk instalasi yang lebih mudah (pip install -r requirements.txt).</i>

<h2>Menjalankan Aplikasi</h2><br>
<p>Setelah semua instalasi selesai, Anda dapat menjalankan aplikasi.</p><br>
<li>Jalankan Server Flask</li><br>
<p>Gunakan perintah berikut untuk memulai server pengembangan lokal. Ganti <i>konverter_fiks.py</i> dengan nama file utama aplikasi Anda.</p><br>

   ```bash
   python3 konverter_fiks.py
   ```

<li>Akses Aplikasi</li><br>
<p>Buka browser Anda dan akses URL berikut:</p><br>
<a href>http://127.0.0.1:5000</a><br>
<h4>Aplikasi konverter Anda sekarang sudah aktif dan siap digunakan.</h4>

<h2>Catatan Tambahan</h2><br>
<li><b>Lingkungan Lokal</b> : Pengaturan ini dirancang untuk berjalan di <b>localhost.</b></li><br>
<li><b>Deployment</b> : Untuk men-deploy aplikasi ini ke server publik, sangat disarankan untuk menggunakan production-ready web server seperti <b>Gunicorn</b> yang di-proxy oleh Nginx.</li>

# Lisensi

Skrip ini dirilis di bawah lisensi <a href="https://github.com/Kavleri/Web_konvert_Files/blob/main/LICENSE">MIT License</a>. Anda bebas untuk menggunakan, memodifikasi, dan mendistribusikan ulang skrip ini sesuai ketentuan lisensi.
