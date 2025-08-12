"""Text parsers for different file formats."""

import io
import re
from typing import Any, Protocol

from pydantic import BaseModel

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

from .ingest import FileInfo


class ParsedDocument(BaseModel):
    """Parsed document with extracted text."""

    file_info: FileInfo
    text: str
    media_type: str  # 'text', 'html', 'pdf'
    page_count: int = 1
    metadata: dict[str, str] = {}


class Parser(Protocol):
    """Protocol for file parsers."""

    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if this parser can handle the file."""
        ...

    def parse(self, file_info: FileInfo) -> ParsedDocument:
        """Parse the file and return extracted text."""
        ...


class PlaintextParser:
    """Parser for plain text files."""

    SUPPORTED_EXTENSIONS = {'txt', 'md', 'markdown', 'py', 'c', 'cpp', 'h', 'hpp', 'rs', 'swift'}

    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if file is plain text."""
        return file_info.extension in self.SUPPORTED_EXTENSIONS

    def parse(self, file_info: FileInfo) -> ParsedDocument:
        """Parse plain text file."""
        try:
            with open(file_info.path, encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_info.path, encoding='latin-1') as f:
                text = f.read()

        # Normalize whitespace but preserve paragraph breaks
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)

        return ParsedDocument(
            file_info=file_info,
            text=text,
            media_type='text',
            page_count=1
        )


class HTMLParser:
    """Parser for HTML files."""

    SUPPORTED_EXTENSIONS = {'html', 'htm'}

    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if file is HTML."""
        return file_info.extension in self.SUPPORTED_EXTENSIONS and HAS_BS4

    def parse(self, file_info: FileInfo) -> ParsedDocument:
        """Parse HTML file and extract text."""
        if not HAS_BS4:
            raise ImportError("BeautifulSoup4 required for HTML parsing")

        with open(file_info.path, encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract text with some structure preservation
        text_parts = []

        # Get title if available
        title = soup.find('title')
        if title:
            text_parts.append(f"# {title.get_text().strip()}\n")

        # Process body content
        body = soup.find('body') or soup

        if hasattr(body, 'find_all'):
            for element in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if element.name:
                    level = int(element.name[1])
                    prefix = '#' * level
                    text_parts.append(f"\n{prefix} {element.get_text().strip()}\n")

        # Get all text and clean it up
        text = soup.get_text()

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        return ParsedDocument(
            file_info=file_info,
            text=text.strip(),
            media_type='html',
            page_count=1,
            metadata={'title': title.get_text().strip() if title else ''}
        )


class PDFParser:
    """Parser for PDF files."""

    SUPPORTED_EXTENSIONS = {'pdf'}

    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if file is PDF."""
        return file_info.extension in self.SUPPORTED_EXTENSIONS and HAS_PYMUPDF

    def parse(self, file_info: FileInfo) -> ParsedDocument:
        """Parse PDF file and extract text."""
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF required for PDF parsing")

        text_parts = []
        page_count = 0

        try:
            doc = fitz.open(file_info.path)
            page_count = len(doc)

            for page_num in range(page_count):
                page = doc.load_page(page_num)

                # Try text extraction first
                page_text = page.get_text()

                # If no text or very little text, try OCR fallback
                if len(page_text.strip()) < 50 and HAS_OCR:
                    page_text = self._ocr_page(page)

                if page_text.strip():
                    text_parts.append(page_text.strip())

            doc.close()

        except Exception as e:
            raise ValueError(f"Failed to parse PDF {file_info.path}: {e}") from e

        # Join pages with double newlines
        full_text = '\n\n'.join(text_parts)

        # Clean up whitespace
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', full_text)

        return ParsedDocument(
            file_info=file_info,
            text=full_text.strip(),
            media_type='pdf',
            page_count=page_count
        )

    def _ocr_page(self, page: Any) -> str:
        """Perform OCR on a PDF page."""
        if not HAS_OCR:
            return ""

        try:
            # Render page to image
            pix = page.get_pixmap()
            img_data = pix.tobytes("ppm")

            # Convert to PIL Image and run OCR
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img)

            return str(text)

        except Exception:
            return ""


class DocumentParser:
    """Main document parser that delegates to format-specific parsers."""

    def __init__(self) -> None:
        self.parsers: list[Parser] = [
            PlaintextParser(),
            HTMLParser(),
            PDFParser(),
        ]

    def parse(self, file_info: FileInfo) -> ParsedDocument:
        """Parse document using appropriate parser."""
        for parser in self.parsers:
            if parser.can_parse(file_info):
                return parser.parse(file_info)

        raise ValueError(f"No parser available for file: {file_info.path}")

    def can_parse(self, file_info: FileInfo) -> bool:
        """Check if any parser can handle this file."""
        return any(parser.can_parse(file_info) for parser in self.parsers)
