# PDF Document Chunker

## Key Features:

1. **Two PDF extraction methods**:
- PyPDF2: Standard library, good for simple PDFs
- PyMuPDF: Better for complex layouts and formatting

3. **Smart chunking**:
- Respects your chunk_size=2000 and chunk_overlap=100 parameters
- Tries to break at sentence boundaries first, then word boundaries
- Avoids cutting words in half

3. **Text cleaning**: Removes excessive whitespace and normalizes formatting

4. **Metadata tracking**: Each chunk includes source file, position, character count, etc.
