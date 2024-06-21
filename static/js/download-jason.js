document.addEventListener('DOMContentLoaded', () => {
    const downloadButton = document.getElementById('download-button');

    downloadButton.addEventListener('click', () => {
        const urlParams = new URLSearchParams(window.location.search);
        const pdfFilename = urlParams.get('pdf');
        if (pdfFilename) {
            window.location.href = `/download-json?pdf=${encodeURIComponent(pdfFilename)}`;
        } else {
            alert('No PDF file specified.');
        }
    });
});
