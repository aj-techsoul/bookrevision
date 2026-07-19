import fitz  # PyMuPDF
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import io
import re
from pathlib import Path
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIngester:
    """Handle document ingestion from various file formats."""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    def extract_text(self, file_path: str, file_type: str) -> Tuple[str, dict]:
        """
        Extract text from document based on file type.
        
        Args:
            file_path: Path to the document
            file_type: File extension (e.g., '.pdf', '.docx', '.txt')
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        file_type = file_type.lower()
        
        if file_type == '.pdf':
            return self._extract_pdf(file_path)
        elif file_type == '.docx':
            return self._extract_docx(file_path)
        elif file_type == '.txt':
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _extract_pdf(self, file_path: str) -> Tuple[str, dict]:
        """Extract text from PDF using PyMuPDF (faster) with fallback to pdfplumber."""
        text = ""
        metadata = {
            'page_count': 0,
            'extraction_method': 'PyMuPDF',
            'has_tables': False,
            'needs_ocr': False
        }
        
        try:
            # Try PyMuPDF first (faster)
            doc = fitz.open(file_path)
            metadata['page_count'] = len(doc)
            
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                text += page_text + "\n\n"
                
                # Check if page might need OCR (very little text)
                if len(page_text.strip()) < 50:
                    metadata['needs_ocr'] = True
            
            doc.close()
            
            # If extracted text is very short, try OCR
            if len(text.strip()) < 100 or metadata['needs_ocr']:
                logger.info("Text extraction yielded minimal content, attempting OCR...")
                try:
                    ocr_text = self._extract_pdf_ocr(file_path)
                    if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        metadata['extraction_method'] = 'OCR'
                except Exception as ocr_err:
                    logger.warning(f"OCR text extraction failed or Tesseract not installed: {ocr_err}")
                    if len(text.strip()) < 100:
                        raise
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            # Fallback to pdfplumber
            try:
                text, metadata = self._extract_pdf_plumber(file_path)
            except Exception as e2:
                logger.error(f"pdfplumber also failed: {e2}")
                raise
        
        return text, metadata
    
    def _extract_pdf_plumber(self, file_path: str) -> Tuple[str, dict]:
        """Extract text from PDF using pdfplumber (better for tables)."""
        text = ""
        metadata = {
            'page_count': 0,
            'extraction_method': 'pdfplumber',
            'has_tables': False
        }
        
        with pdfplumber.open(file_path) as pdf:
            metadata['page_count'] = len(pdf.pages)
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                
                # Check for tables
                tables = page.extract_tables()
                if tables:
                    metadata['has_tables'] = True
                    for table in tables:
                        for row in table:
                            if row:
                                text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                        text += "\n"
        
        return text, metadata
    
    def _extract_pdf_ocr(self, file_path: str) -> str:
        """Extract text from scanned PDF using OCR."""
        text = ""
        doc = fitz.open(file_path)
        
        for page_num, page in enumerate(doc):
            # Convert page to image
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            # Perform OCR
            page_text = pytesseract.image_to_string(img)
            text += page_text + "\n\n"
        
        doc.close()
        return text
    
    def _extract_docx(self, file_path: str) -> Tuple[str, dict]:
        """Extract text from DOCX file."""
        doc = Document(file_path)
        text = ""
        
        # Extract paragraphs
        for para in doc.paragraphs:
            text += para.text + "\n\n"
        
        # Extract tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text for cell in row.cells])
                text += row_text + "\n"
            text += "\n"
        
        metadata = {
            'page_count': 1,  # DOCX doesn't have pages
            'extraction_method': 'python-docx',
            'has_tables': len(doc.tables) > 0
        }
        
        return text, metadata
    
    def _extract_txt(self, file_path: str) -> Tuple[str, dict]:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        metadata = {
            'page_count': 1,
            'extraction_method': 'native',
            'has_tables': False
        }
        
        return text, metadata
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove page numbers (common pattern: standalone numbers)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Remove headers/footers (simple heuristic)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Normalize internal spaces on the line
            line = re.sub(r'[ \t]+', ' ', line)
            # Skip very short lines that might be headers/footers
            if len(line) > 3 or len(line) == 0:
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Normalize multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove special characters but keep basic punctuation, quotes, and newlines
        text = re.sub(r'[^\w\s\.\,\;\:\?\!\-\(\)\"\'\n]', '', text)
        
        return text.strip()
