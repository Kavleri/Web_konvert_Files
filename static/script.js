document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file-input');
    const formatSelect = document.getElementById('format-select');
    const converterForm = document.getElementById('converter-form');
    const submitBtn = document.getElementById('submit-btn');
    const spinner = document.getElementById('spinner');

    const customOptionsContainer = document.getElementById('custom-options');
    const jpgQualityOption = document.getElementById('jpg-quality-option');
    const jpgQualitySlider = document.getElementById('jpg_quality');
    const jpgQualityValue = document.getElementById('jpg-quality-value'); 
    const conversionMap = {
        image: [
            { value: 'jpg', text: 'JPG' },
            { value: 'png', text: 'PNG' },
            { value: 'webp', text: 'WEBP' },
            { value: 'gif', text: 'GIF' },
            { value: 'ico', text: 'ICO (Icon)' }
        ],
        pdf: [
            { value: 'docx', text: 'DOCX (Word) - Kualitas Bervariasi' },
            { value: 'png', text: 'PNG (Halaman Pertama)' },
            { value: 'jpg', text: 'JPG (Halaman Pertama)' }
        ],
        video: [
            { value: 'mp4', text: 'MP4' },
            { value: 'webm', text: 'WEBM' },
            { value: 'avi', text: 'AVI' },
            { value: 'mov', text: 'MOV' },
            { value: 'mp3', text: 'MP3 (Ekstrak Audio)' }
        ],
        audio: [
            { value: 'mp3', text: 'MP3' },
            { value: 'wav', text: 'WAV' },
            { value: 'm4a', text: 'M4A' },
            { value: 'ogg', text: 'OGG' }
        ],
        document: [ 
            { value: 'pdf', text: 'PDF' },
            { value: 'docx', text: 'DOCX (Word)' },
            { value: 'odt', text: 'ODT (OpenDocument)' },
            { value: 'html', text: 'HTML' },
            { value: 'md', text: 'Markdown' },
            { value: 'rtf', text: 'RTF' },
            { value: 'txt', text: 'Plain Text' },
            { value: 'epub', text: 'EPUB (e-book)'}
        ]
    };

    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (!file) {
            resetSelect();
            return;
        }

        const extension = file.name.split('.').pop().toLowerCase();
        let fileType = '';
        
        const imageExt = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff'];
        const videoExt = ['mp4', 'mkv', 'flv', 'avi', 'mov', 'webm'];
        const audioExt = ['mp3', 'wav', 'ogg', 'm4a', 'flac'];
        const docExt = ['docx', 'doc', 'odt', 'rtf', 'md', 'html', 'txt', 'epub', 'tex'];

        if (imageExt.includes(extension)) {
            fileType = 'image';
        } else if (videoExt.includes(extension)) {
            fileType = 'video';
        } else if (audioExt.includes(extension)) {
            fileType = 'audio';
        } else if (extension === 'pdf') {
            fileType = 'pdf';
        } else if (docExt.includes(extension)) { 
            fileType = 'document';
        }

        updateFormatOptions(fileType, extension);
    });

    function updateFormatOptions(fileType, currentExtension) {
        formatSelect.innerHTML = '';
        submitBtn.disabled = true;
        if (!fileType || !conversionMap[fileType]) {
            resetSelect('Jenis file tidak didukung.');
            return;
        }
        const options = conversionMap[fileType];
        let defaultOption = document.createElement('option');
        defaultOption.value = "";
        defaultOption.textContent = "Pilih format...";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        formatSelect.appendChild(defaultOption);
        options.forEach(opt => {
            if (opt.value !== currentExtension) {
                let option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.text;
                formatSelect.appendChild(option);
            }
        });
        if (formatSelect.options.length > 1) {
            submitBtn.disabled = false;
        } else {
            resetSelect('Tidak ada opsi konversi untuk file ini.');
        }
    }

    formatSelect.addEventListener('change', function() {
        hideAllCustomOptions();
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption.dataset.hasQuality === 'true') {
            customOptionsContainer.style.display = 'block';
            jpgQualityOption.style.display = 'block';
        }
    });
    
    // Fungsi untuk menyembunyikan semua opsi kustom
    function hideAllCustomOptions() {
        customOptionsContainer.style.display = 'none';
        jpgQualityOption.style.display = 'none';
    }
    
    jpgQualitySlider.addEventListener('input', function() {
        jpgQualityValue.textContent = this.value;
    });

    function resetSelect(message = 'Pilih file dulu...') {
        formatSelect.innerHTML = `<option value="" disabled selected>${message}</option>`;
        submitBtn.disabled = true;
    }
    converterForm.addEventListener('submit', function(e) {
        if (!fileInput.files.length || !formatSelect.value) {
            e.preventDefault();
            return;
        }
        submitBtn.disabled = true;
        submitBtn.textContent = 'Memproses...';
        spinner.style.display = 'block';
        setTimeout(() => {
            spinner.style.display = 'none';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Konversi Sekarang';
            resetSelect();
            converterForm.reset();
        }, 4000);
    });
});
