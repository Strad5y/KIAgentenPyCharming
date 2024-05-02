import fitz
import json
def open_pdf_button(pdf_path):
    text = pdf_ocr(pdf_path)
    json_file_path = "Json Files/myfile.json"
    save_text_as_json(text, json_file_path)
    # Example print to check if it works
    with open('Json Files/myfile.json', 'r') as file:
        data = json.load(file)

    print(json.dumps(data, indent=4))


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

def save_text_as_json(text, json_file_path):
    # Create a dictionary to store the text
    data = {'text': text}

    # Write the dictionary to a JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file)


# Example usage
pdf_path = "PDF Example Files/Estimation of the Gross Fixed Kapital using linear Regression.pdf"
open_pdf_button(pdf_path)