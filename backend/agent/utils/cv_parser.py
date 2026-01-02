"""
CV/Resume Text Extraction Utility

This module provides functions to download and extract text from PDF CVs
stored in Supabase storage.
"""

import io
import httpx
from typing import Optional
from PyPDF2 import PdfReader


async def download_and_extract_cv_text(cv_url: str, max_chars: int = 8000) -> str:
    """
    Download a PDF CV from URL and extract text content.
    
    Args:
        cv_url: Public or signed URL to the PDF file
        max_chars: Maximum characters to extract (to avoid token limits)
    
    Returns:
        Extracted text from the CV, or error message if extraction fails
    """
    if not cv_url:
        return "No CV provided"
    
    try:
        # Download the PDF file
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(cv_url)
            response.raise_for_status()
            pdf_bytes = response.content
        
        # Extract text from PDF
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        total_chars = 0
        
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
            total_chars += len(page_text)
            
            # Stop if we've extracted enough text
            if total_chars >= max_chars:
                break
        
        full_text = "\n".join(text_parts)
        
        # Truncate if too long
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "..."
        
        # Clean up the text
        full_text = _clean_cv_text(full_text)
        
        if not full_text.strip():
            return "CV appears to be empty or could not be parsed (possibly scanned image)"
        
        return full_text
    
    except httpx.HTTPStatusError as e:
        return f"Could not download CV: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Could not extract CV text: {str(e)}"


def _clean_cv_text(text: str) -> str:
    """Clean up extracted CV text by removing excessive whitespace."""
    import re
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove lines that are just whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    return '\n'.join(lines)


async def extract_cv_text_batch(cv_urls: list[str], max_chars_per_cv: int = 6000) -> dict[str, str]:
    """
    Extract text from multiple CVs in parallel.
    
    Args:
        cv_urls: List of CV URLs to process
        max_chars_per_cv: Maximum characters per CV
    
    Returns:
        Dictionary mapping URL to extracted text
    """
    import asyncio
    
    async def extract_one(url: str) -> tuple[str, str]:
        text = await download_and_extract_cv_text(url, max_chars_per_cv)
        return url, text
    
    tasks = [extract_one(url) for url in cv_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        url: (text if not isinstance(text, Exception) else f"Error: {text}")
        for url, text in results
    }
