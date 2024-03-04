from pydantic import BaseModel, AnyHttpUrl, Field
from typing import Optional, Literal, List
import requests
import fitz
import os
import json
from langdetect import detect
from datetime import datetime

INPUT_FILE = "./manual_urls.txt"
OUTPUT_DIR = "./downloaded_pdfs"
OUTPUT_JSON_PATH = "./pdf_data.json"

class PDFData(BaseModel):
    id: int
    url: AnyHttpUrl
    text: str
    language: Literal["de", "en"]
    manufacturer: Optional[str] = None # TODO: erase if not to be used
    extraction_date: str = Field(default_factory=lambda: datetime.now().strftime("%d.%m.%Y %H:%M:%S"))

class PDFProcessor:
    def __init__(self, input_file, output_dir, output_json_path):
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_json_path = output_json_path
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.data: List[PDFData] = []

    def process_url(self, url):
        idx = url.find(".pdf")
        return url[:idx + len(".pdf")]

    def download_pdf(self, url):
        response = requests.get(url)
        filename = url.split("/")[-1]
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath

    def extract_text(self, filepath):
        text = ""
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def identify_language(self, text):
        return detect(text)

    # def extract_manufacturer(self, filename):
    #     pattern = r""
    #     match = re.search(pattern, filename, re.IGNORECASE)
    #     return match.group(1) if match else "Unknown"

    def process_pdf(self):
        with open(self.input_file, "r", encoding="UTF-8") as file:
            for idx, url in enumerate(file):
                processed_url = self.process_url(url)
                filepath = self.download_pdf(processed_url)
                text = self.extract_text(filepath)
                # os.remove(filepath)  # TODO: decide whether to keep pdfs
                language = self.identify_language(text)
                #manufacturer = self.extract_manufacturer(filepath)
                pdf_data = PDFData(
                    id=idx,
                    url=processed_url,
                    language=language,
                    #manufacturer="",
                    text=text
                )
                self.data.append(pdf_data)

    def save_to_json(self):
        with open(self.output_json_path, 'w') as f:
            # Convert Pydantic models to dictionaries for JSON serialization
            json.dump([data_obj.model_dump() for data_obj in self.data], f, indent=4, default=str)


# Example usage
output_directory = "downloaded_pdfs"
processor = PDFProcessor(INPUT_FILE, OUTPUT_DIR, OUTPUT_JSON_PATH)
processor.process_pdf()
processor.save_to_json()
