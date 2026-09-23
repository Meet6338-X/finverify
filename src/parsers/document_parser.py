import csv
import io
import json
import re
from typing import Union

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

class DocumentParsingError(Exception):
    """Exception raised for errors in the document parsing process."""
    pass

class DocumentParser:
    """Multi-format document parser for financial filings."""
    
    def __init__(self, max_length: int = 100000):
        self.max_length = max_length

    def parse(self, content: Union[str, bytes], content_format: str) -> str:
        """Route to appropriate parser based on format."""
        
        # Check length
        content_len = len(content)
        if content_len > self.max_length:
            raise DocumentParsingError(f"Content length {content_len} exceeds maximum allowed {self.max_length} characters/bytes.")
            
        content_format = content_format.lower().strip()
        
        if content_format in ['txt', 'text']:
            if not isinstance(content, str):
                content = content.decode('utf-8', errors='replace')
            return self._parse_text(content)
            
        elif content_format == 'json':
            if not isinstance(content, str):
                content = content.decode('utf-8', errors='replace')
            return self._parse_json(content)
            
        elif content_format == 'pdf':
            if not isinstance(content, bytes):
                raise DocumentParsingError("PDF content must be provided as bytes.")
            return self._parse_pdf(content)
            
        elif content_format in ['doc', 'docx']:
            if not isinstance(content, bytes):
                raise DocumentParsingError("DOCX content must be provided as bytes.")
            return self._parse_docx(content)
            
        elif content_format == 'csv':
            if not isinstance(content, str):
                content = content.decode('utf-8', errors='replace')
            return self._parse_csv(content)
            
        else:
            raise DocumentParsingError(f"Unsupported document format: {content_format}")

    def _parse_text(self, content: str) -> str:
        """Parse raw text (as-is)."""
        return content

    def _parse_json(self, content: str) -> str:
        """Parse JSON and flatten to text representation."""
        try:
            data = json.loads(content)
            
            # Simple heuristic for flattened textual representation
            if isinstance(data, dict):
                return "\n".join([f"{k}: {v}" for k, v in data.items()])
            elif isinstance(data, list):
                return "\n".join([str(item) for item in data])
            return str(data)
        except json.JSONDecodeError as e:
            raise DocumentParsingError(f"Invalid JSON content: {e}")

    def _parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF using pdfplumber."""
        if pdfplumber is None:
            raise DocumentParsingError("pdfplumber library is not installed.")
            
        try:
            text_pages = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_pages.append(page_text)
            return "\n\n".join(text_pages)
        except Exception as e:
            raise DocumentParsingError(f"Error parsing PDF: {e}")

    def _parse_docx(self, content: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        if docx is None:
            raise DocumentParsingError("python-docx library is not installed.")
            
        try:
            doc = docx.Document(io.BytesIO(content))
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        except Exception as e:
            raise DocumentParsingError(f"Error parsing DOCX: {e}")

    def _parse_csv(self, content: str) -> str:
        """Parse CSV rows into structured text representation."""
        try:
            text_lines = []
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                text_lines.append(" | ".join([str(cell).strip() for cell in row]))
            return "\n".join(text_lines)
        except Exception as e:
            raise DocumentParsingError(f"Error parsing CSV: {e}")

    def validate_metadata(self, cik: str, period: str) -> bool:
        """Validate CIK and period format."""
        if not re.match(r"^\d{1,10}$", cik):
            raise DocumentParsingError("Invalid CIK format. Must be up to 10 digits.")
            
        if not re.match(r"^\d{4}(?:-Q[1-4])?$", period):
            raise DocumentParsingError("Invalid period format. Must be YYYY or YYYY-QN.")
            
        return True
