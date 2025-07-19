import os
from typing import List, Dict, Any
import PyPDF2
import fitz  # PyMuPDF
from pathlib import Path

class PDFChunker:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 100):
        """
        Initialize PDF chunker with specified chunk size and overlap.
        
        Args:
            chunk_size (int): Maximum size of each chunk in characters
            chunk_overlap (int): Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text from PDF using PyPDF2."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF with PyPDF2: {e}")
        return text
    
    def extract_text_pymupdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF (better for complex layouts)."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            print(f"Error reading PDF with PyMuPDF: {e}")
        return text
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace."""
        # Replace multiple whitespaces with single space
        import re
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def create_chunks(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks with specified size and overlap.
        
        Args:
            text (str): Input text to be chunked
            
        Returns:
            List[Dict]: List of chunks with metadata
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If we're not at the end of the text, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                sentence_end = text.rfind('.', start, end)
                if sentence_end != -1 and sentence_end > start + self.chunk_size - 200:
                    end = sentence_end + 1
                else:
                    # Fall back to word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end != -1 and word_end > start + self.chunk_size - 100:
                        end = word_end
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_pos': start,
                    'end_pos': end,
                    'char_count': len(chunk_text)
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Ensure we don't go backwards
            if start <= 0:
                break
                
        return chunks
    
    def process_pdf(self, pdf_path: str, use_pymupdf: bool = True) -> List[Dict[str, Any]]:
        """
        Process a single PDF file and return chunks.
        
        Args:
            pdf_path (str): Path to the PDF file
            use_pymupdf (bool): Whether to use PyMuPDF (True) or PyPDF2 (False)
            
        Returns:
            List[Dict]: List of text chunks with metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Extract text
        if use_pymupdf:
            raw_text = self.extract_text_pymupdf(pdf_path)
        else:
            raw_text = self.extract_text_pypdf2(pdf_path)
        
        # Clean text
        cleaned_text = self.clean_text(raw_text)
        
        # Create chunks
        chunks = self.create_chunks(cleaned_text)
        
        # Add file metadata to each chunk
        file_name = Path(pdf_path).name
        for chunk in chunks:
            chunk['source_file'] = file_name
            chunk['source_path'] = pdf_path
        
        return chunks
    
    def process_multiple_pdfs(self, pdf_paths: List[str], use_pymupdf: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process multiple PDF files.
        
        Args:
            pdf_paths (List[str]): List of paths to PDF files
            use_pymupdf (bool): Whether to use PyMuPDF (True) or PyPDF2 (False)
            
        Returns:
            Dict: Dictionary with file names as keys and chunks as values
        """
        results = {}
        
        for pdf_path in pdf_paths:
            try:
                chunks = self.process_pdf(pdf_path, use_pymupdf)
                file_name = Path(pdf_path).name
                results[file_name] = chunks
                print(f"Processed {file_name}: {len(chunks)} chunks created")
            except Exception as e:
                print(f"Error processing {pdf_path}: {e}")
        
        return results
    
    def save_chunks_to_text(self, chunks: List[Dict[str, Any]], output_path: str):
        """Save chunks to a text file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(f"=== CHUNK {chunk['chunk_id']} ===\n")
                f.write(f"Source: {chunk['source_file']}\n")
                f.write(f"Characters: {chunk['char_count']}\n")
                f.write(f"Position: {chunk['start_pos']}-{chunk['end_pos']}\n")
                f.write(f"{'-' * 50}\n")
                f.write(f"{chunk['text']}\n")
                f.write(f"{'=' * 50}\n\n")

# Example usage
def main():
    # Initialize chunker with your specifications
    chunker = PDFChunker(chunk_size=2000, chunk_overlap=100)
    
    # Example 1: Process a single PDF
    try:
        pdf_path = "example.pdf"  # Replace with your PDF path
        chunks = chunker.process_pdf(pdf_path)
        
        print(f"Total chunks created: {len(chunks)}")
        
        # Print first chunk as example
        if chunks:
            print(f"\nFirst chunk preview:")
            print(f"Characters: {chunks[0]['char_count']}")
            print(f"Text: {chunks[0]['text'][:200]}...")
        
        # Save chunks to file
        chunker.save_chunks_to_text(chunks, "output_chunks.txt")
        
    except FileNotFoundError:
        print("Example PDF not found. Please provide a valid PDF path.")
    
    # Example 2: Process multiple PDFs
    pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]  # Replace with your PDF paths
    existing_files = [f for f in pdf_files if os.path.exists(f)]
    
    if existing_files:
        results = chunker.process_multiple_pdfs(existing_files)
        
        # Print summary
        total_chunks = sum(len(chunks) for chunks in results.values())
        print(f"\nProcessed {len(results)} files with {total_chunks} total chunks")

if __name__ == "__main__":
    main()
