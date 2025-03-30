import io
import PyPDF2
from core.logging import logger

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_content (bytes): PDF file content

    Returns:
        str: Extracted text from PDF
    """
    try:
        logger.info("Extracting text from PDF")
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        logger.info(f"Extracted PDF text length: {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise