document.addEventListener('DOMContentLoaded', () => {
    const pdfUpload = document.getElementById('pdf-upload');
    const proceedButton = document.getElementById('proceed-button');

    proceedButton.disabled = true;
    proceedButton.classList.add('disabled');

    pdfUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file && file.type === 'application/pdf') {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.filename) {
                    proceedButton.dataset.filename = data.filename;
                    proceedButton.disabled = false;
                    proceedButton.classList.remove('disabled');
                    proceedButton.classList.add('shake-animation');
                    setTimeout(() => {
                        proceedButton.classList.remove('shake-animation');
                    }, 1000);
                } else {
                    alert('File upload failed');
                }
            })
            .catch(error => {
                console.error('Error uploading file:', error);
                alert('An error occurred while uploading the file.');
            });
        } else {
            alert('Please upload a valid PDF file.');
        }
    });

    proceedButton.addEventListener('click', () => {
        const filename = proceedButton.dataset.filename;
        if (filename) {
            window.location.href = `/chat?pdf=${encodeURIComponent(filename)}`;
        }
    });
});
