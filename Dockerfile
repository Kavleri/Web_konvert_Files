# Gunakan gambar dasar Python versi 3.10
FROM python:3.10-slim

# Set direktori kerja di dalam kontainer
WORKDIR /code

# Salin file daftar paket sistem terlebih dahulu
COPY ./packages.txt /code/packages.txt

# Update, instal paket sistem dari packages.txt, lalu bersihkan cache
RUN apt-get update && apt-get install -y --no-install-recommends $(cat packages.txt) \
    && rm -rf /var/lib/apt/lists/*

# Salin file daftar library Python
COPY ./requirements.txt /code/requirements.txt

# Instal library Python
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Salin semua file proyek lainnya (app.py, static/, templates/)
COPY . /code/

# Beritahu dunia luar bahwa aplikasi berjalan di port 7860
EXPOSE 7860

# Perintah untuk menjalankan aplikasi saat kontainer dimulai
# Gunakan Gunicorn, dan arahkan ke port 7860 (port default Hugging Face)
# Ganti "konverter:app" jika nama file atau variabel Flask Anda berbeda
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:7860", "konverter:app"]