import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_directory(self, directory_path: str):
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory {directory_path} not found.")

        logger.info(f"Loading documents from {directory_path}")
        loader = PyPDFDirectoryLoader(directory_path)
        documents = loader.load()

        logger.info(f"Loaded {len(documents)} documents. Splitting...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks.")
        
        # Extract text and metadata
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        return texts, metadatas

document_processor = DocumentProcessor()
