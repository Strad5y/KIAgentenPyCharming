import fitz


def pdf_ocr(pdf_path):
    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    # Initialize an empty string to store extracted text
    text = ""

    # Iterate through each page in the PDF
    for page_number in range(len(pdf_document)):
        # Get the page
        page = pdf_document.load_page(page_number)

        # Extract text from the page
        text += page.get_text()

    # Close the PDF
    pdf_document.close()

    return text


# Example usage
pdf_path = "C:\\Users\\Timo\\Downloads\\08_Ampel.pdf"
extracted_text = pdf_ocr(pdf_path)
print(extracted_text)