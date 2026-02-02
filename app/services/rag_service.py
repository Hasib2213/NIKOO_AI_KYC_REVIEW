"""
RAG (Retrieval Augmented Generation) Service
Handles document ingestion, vector storage, and context retrieval
"""
from typing import List, Dict, Optional
import logging
import os
from pathlib import Path
import asyncio

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class RAGService:
    """Manages document retrieval for AI responses"""
    
    def __init__(self, documents_path: str = "app/documents", index_path: str = "app/documents/faiss_index"):
        self.documents_path = Path(documents_path)
        self.index_path = Path(index_path)
        self.vector_store = None
        self.embeddings = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize embeddings and load documents or persisted index"""
        try:
            logger.info("Initializing RAG service...")
            
            # Initialize embeddings model
            await asyncio.to_thread(self._init_embeddings)
            
            # Try loading persisted index first (fast path)
            if self.index_path.exists():
                logger.info(f"Loading persisted vector store from {self.index_path}")
                await self.load_index(str(self.index_path))
                self.is_initialized = True
                logger.info("RAG service initialized from persisted index (fast load)")
                return
            
            # Otherwise load documents and create index (slow path)
            if self.documents_path.exists():
                logger.info("No persisted index found, loading documents from scratch...")
                await self.load_documents()
                
                # Save index for future loads
                if self.vector_store:
                    logger.info(f"Saving vector store to {self.index_path}")
                    await self.save_index(str(self.index_path))
            else:
                logger.warning(f"Documents path {self.documents_path} does not exist")
                self.documents_path.mkdir(parents=True, exist_ok=True)
            
            self.is_initialized = True
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            self.is_initialized = False
    
    def _init_embeddings(self):
        """Initialize Gemini embedding model (runs in thread)"""
        try:
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY is required for Gemini embeddings")

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=gemini_key
            )
            logger.info("Gemini embeddings loaded")
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            raise
    
    async def load_documents(self, force_reload: bool = False):
        """Load and index documents from the documents folder"""
        try:
            if not self.embeddings:
                await asyncio.to_thread(self._init_embeddings)
            
            if self.vector_store and not force_reload:
                logger.info("Vector store already loaded")
                return
            
            logger.info(f"Loading documents from {self.documents_path}")
            
            # Load documents in thread
            documents = await asyncio.to_thread(self._load_docs_sync)
            
            if not documents:
                logger.warning("No documents found to index")
                return
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            splits = await asyncio.to_thread(text_splitter.split_documents, documents)
            
            # Create vector store
            logger.info(f"Creating vector store with {len(splits)} chunks")
            self.vector_store = await asyncio.to_thread(
                FAISS.from_documents,
                splits,
                self.embeddings
            )
            
            logger.info(f"Loaded {len(documents)} documents, created {len(splits)} chunks")
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
    
    def _load_docs_sync(self) -> List[Document]:
        """Load documents synchronously"""
        documents = []
        
        # Load text files
        txt_files = list(self.documents_path.glob("*.txt"))
        for txt_file in txt_files:
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Error loading {txt_file}: {e}")
        
        # Load PDF files
        pdf_files = list(self.documents_path.glob("*.pdf"))
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Error loading {pdf_file}: {e}")
        
        return documents
    
    async def retrieve_context(
        self,
        query: str,
        k: int = 3,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Retrieve relevant document chunks for a query
        
        Args:
            query: User query
            k: Number of documents to retrieve
            score_threshold: Minimum similarity score
        
        Returns:
            List of relevant document chunks with metadata
        """
        try:
            if not self.is_initialized or not self.vector_store:
                logger.warning("RAG service not initialized or no documents loaded")
                return []
            
            # Perform similarity search with scores
            results = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                k=k
            )
            
            # Filter by score threshold and format results
            relevant_docs = []
            for doc, score in results:
                # FAISS returns distance (lower is better), convert to similarity
                similarity = 1 / (1 + score)
                
                if similarity >= score_threshold:
                    relevant_docs.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": similarity
                    })
            
            logger.info(f"Retrieved {len(relevant_docs)} relevant documents for query")
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    async def get_relevant_context_string(
        self,
        query: str,
        k: int = 3,
        max_length: int = 2000
    ) -> str:
        """
        Get relevant context as formatted string
        
        Args:
            query: User query
            k: Number of documents to retrieve
            max_length: Maximum total length of context
        
        Returns:
            Formatted context string
        """
        try:
            docs = await self.retrieve_context(query, k=k)
            
            if not docs:
                return ""
            
            # Build context string
            context_parts = ["Relevant information from documentation:"]
            current_length = len(context_parts[0])
            
            for i, doc in enumerate(docs, 1):
                content = doc["content"].strip()
                doc_text = f"\n\n{i}. {content}"
                
                if current_length + len(doc_text) > max_length:
                    break
                
                context_parts.append(doc_text)
                current_length += len(doc_text)
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            return ""
    
    async def add_document(self, content: str, metadata: Optional[Dict] = None):
        """Add a new document to the vector store and re-save index"""
        try:
            if not self.embeddings:
                await asyncio.to_thread(self._init_embeddings)
            
            doc = Document(page_content=content, metadata=metadata or {})
            
            # Split document
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents([doc])
            
            # Add to existing store or create new one
            if self.vector_store:
                await asyncio.to_thread(self.vector_store.add_documents, splits)
            else:
                self.vector_store = await asyncio.to_thread(
                    FAISS.from_documents,
                    splits,
                    self.embeddings
                )
            
            logger.info(f"Added document with {len(splits)} chunks")
            
            # Re-save index to persist changes
            if self.vector_store and self.index_path:
                await self.save_index(str(self.index_path))
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
    
    async def save_index(self, path: str = "app/documents/faiss_index"):
        """Save FAISS index to disk"""
        try:
            if not self.vector_store:
                logger.warning("No vector store to save")
                return
            
            await asyncio.to_thread(self.vector_store.save_local, path)
            logger.info(f"FAISS index saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    async def load_index(self, path: str = "app/documents/faiss_index"):
        """Load FAISS index from disk"""
        try:
            if not self.embeddings:
                await asyncio.to_thread(self._init_embeddings)
            
            if not Path(path).exists():
                logger.warning(f"Index path {path} does not exist")
                return
            
            self.vector_store = await asyncio.to_thread(
                FAISS.load_local,
                path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"FAISS index loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")


# Singleton instance
rag_service = RAGService()
