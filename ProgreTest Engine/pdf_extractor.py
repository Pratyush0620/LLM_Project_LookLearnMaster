"""
PDF Text Extraction Module
Extracts and cleans text content from uploaded PDF files.
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_file: Uploaded file object from Streamlit
        
    Returns:
        str: Extracted and cleaned text content
    """
    try:
        # Read the PDF bytes
        pdf_bytes = pdf_file.read()
        
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        text_content = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                text_content.append(f"--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        
        full_text = "\n\n".join(text_content)
        
        # Clean the text
        full_text = clean_text(full_text)
        
        return full_text
        
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and formatting issues.
    
    Args:
        text: Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    # Replace multiple newlines with double newline
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def get_content_summary(text: str, max_chars: int = 500) -> str:
    """
    Get a brief summary/preview of the content.
    
    Args:
        text: Full text content
        max_chars: Maximum characters for summary
        
    Returns:
        str: Content preview
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
