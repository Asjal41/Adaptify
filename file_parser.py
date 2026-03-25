import io


def parse_file(filename: str, file_bytes: bytes) -> str:
    """Extract text from DOCX, PDF, or TXT files."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "docx":
        return _parse_docx(file_bytes)
    elif ext == "pdf":
        return _parse_pdf(file_bytes)
    elif ext == "txt":
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Use .docx, .pdf, or .txt")


def _parse_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _parse_pdf(file_bytes: bytes) -> str:
    from PyPDF2 import PdfReader
    import io
    
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        
        if reader.is_encrypted:
            # Try to decrypt with empty password
            try:
                reader.decrypt("")
            except:
                raise ValueError("PDF is encrypted. Please upload a decrypted version.")

        text_parts = []
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
            except Exception as e:
                print(f"Warning: Failed to extract text from page {i}: {e}")
                continue
                
        full_text = "\n".join(text_parts)
        if not full_text:
            # Fallback or warning
            print("Warning: No text extracted from PDF. It might be an image-only scan.")
            
        return full_text
            
    except Exception as e:
        raise ValueError(f"PDF parsing failed: {str(e)}")
