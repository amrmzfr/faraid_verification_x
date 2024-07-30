# app/utils.py
import fitz
import re
import hashlib
import pyotp
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def process_pdf(pdf_file):
    extracted_text = ""

    doc = fitz.open(pdf_file)

    for page in doc:
        text = page.get_text()
        extracted_text += text
    
    doc.close()
    
    normalized_text = normalize_text(extracted_text)
    hashed_text = hashlib.sha256(normalized_text.encode()).hexdigest()
    
    return normalized_text, hashed_text

def normalize_text(text):


    normalized_text = text.lower()
    
    normalized_text = re.sub(r'\s+', ' ', normalized_text)

    normalized_text = re.sub(r'[^\w\s]', '', normalized_text)
    
    return normalized_text

