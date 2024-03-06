from pydantic import BaseModel, AnyHttpUrl, Field
from typing import Optional, Literal, List
import requests
import fitz
import os
import json
from langdetect import detect
from datetime import datetime

INPUT_FILE = "./manual_urls.txt"
PDF_DIR = "./downloaded_pdfs"
OUTPUT_JSON_PATH = "./pdf_data.json"

class PDFData(BaseModel):
    """Data model for storing information extracted from PDFs."""
    id: int
    url: AnyHttpUrl
    text: str
    language: Literal["de", "en"]
    extraction_date: str = Field(default_factory=lambda: datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

class PDFProcessor:
    """Processes PDF files: downloads, extracts text, identifies language, and saves data to JSON."""
    
    def __init__(self, input_file, pdf_dir, output_json_path):
        """
        Initializes the PDFProcessor with paths for input, output, and storage.

        :param input_file: Path to the text file containing PDF URLs.
        :param pdf_dir: Directory path where PDFs will be downloaded and stored.
        :param output_json_path: Path where the extracted data will be saved as JSON.
        """
        self.input_file = input_file
        self.pdf_dir = pdf_dir
        self.output_json_path = output_json_path
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)
        self.data: List[PDFData] = []

    def process_url(self, url: str) -> str:
        """Extracts the PDF file URL up to the .pdf extension.

        :param url: The full URL of the PDF file.
        :return: The URL trimmed to end at '.pdf'.
        """
        idx = url.find(".pdf")
        return url[:idx + len(".pdf")]

    def download_pdf(self, url: str) -> str:
        """Downloads a PDF from a URL if not already downloaded, acting as a caching mechanism.

        :param url: The full URL of the PDF file.
        :return: The local file path to the downloaded or existing PDF.
        """
        filename = url.split("/")[-1]
        filepath = os.path.join(self.pdf_dir, filename)
        if not os.path.exists(filepath):
            response = requests.get(url)
            with open(filepath, 'wb') as f:
                f.write(response.content)
        return filepath

    def extract_text(self, filepath: str) -> str:
        """Extracts and returns the text from a PDF file.

        :param filepath: The local file path to the PDF.
        :return: Extracted text from the PDF.
        """
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def identify_language(self, text: str) -> str:
        """Identifies the language of the given text using langdetect.

        :param text: The text to analyze.
        :return: The identified language code (e.g., 'en', 'de').
        """
        return detect(text)

    def process_pdf(self):
        """Processes each PDF URL from the input file: downloads, extracts text, identifies language, and stores data."""
        with open(self.input_file, "r", encoding="UTF-8") as file:
            for idx, url in enumerate(file):
                processed_url = self.process_url(url)
                filepath = self.download_pdf(processed_url)
                text = self.extract_text(filepath)
                language = self.identify_language(text)
                pdf_data = PDFData(
                    id=idx,
                    url=processed_url,
                    language=language,
                    text=text
                )
                self.data.append(pdf_data)

    def save_to_json(self):
        """Processes PDFs and saves the extracted data to a JSON file."""
        self.process_pdf()
        with open(self.output_json_path, 'w') as f:
            # Convert Pydantic models to dictionaries for JSON serialization
            json.dump([data_obj.model_dump() for data_obj in self.data], f, indent=4, default=str)


# Example usage
processor = PDFProcessor(INPUT_FILE, PDF_DIR, OUTPUT_JSON_PATH)
processor.save_to_json()
