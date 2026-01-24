"""RAG Pipeline for POLICYGUARD
Handles document chunking, embedding generation, and vector search
for RBI, AML, PMLA regulatory documents
"""

import os
import re
from typing import List, Dict, Tuple
import numpy as np
from datetime import datetime


class DocumentChunker:
    """Chunks regulatory documents into manageable pieces for RAG"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, document: str, doc_metadata: Dict) -> List[Dict]:
        """Split document into overlapping chunks with metadata"""
        # Clean and normalize text
        text = self._clean_text(document)
        
        # Split by sections first (preserve structure)
        sections = self._split_by_sections(text)
        
        chunks = []
        for section_idx, section in enumerate(sections):
            section_chunks = self._chunk_text(section['text'])
            
            for chunk_idx, chunk_text in enumerate(section_chunks):
                chunk = {
                    'chunk_id': f"{doc_metadata.get('doc_id', 'unknown')}_{section_idx}_{chunk_idx}",
                    'text': chunk_text,
                    'section': section['title'],
                    'doc_type': doc_metadata.get('doc_type', 'unknown'),
                    'source': doc_metadata.get('source', 'unknown'),
                    'date': doc_metadata.get('date', datetime.now().isoformat()),
                    'regulation': doc_metadata.get('regulation', 'RBI'),
                    'chunk_index': chunk_idx,
                    'total_chunks': len(section_chunks)
                }
                chunks.append(chunk)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize document text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        return text.strip()
    
    def _split_by_sections(self, text: str) -> List[Dict]:
        """Split document by sections (Chapter, Article, etc.)"""
        # Pattern for section headers
        section_pattern = r'(Chapter|Section|Article|Rule|Clause)\s+\d+[:\.]?\s*([^\n]+)'
        
        sections = []
        matches = list(re.finditer(section_pattern, text, re.IGNORECASE))
        
        if not matches:
            # No clear sections, treat as single section
            return [{'title': 'Main Content', 'text': text}]
        
        for i, match in enumerate(matches):
            section_title = match.group(0)
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start_pos:end_pos].strip()
            
            sections.append({
                'title': section_title,
                'text': section_text
            })
        
        return sections
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(' '.join(chunk_words))
        
        return chunks


class VectorSearchEngine:
    """Handles embedding generation and vector search"""
    
    def __init__(self):
        self.embeddings_cache = {}
        self.chunk_store = []
    
    def add_chunks(self, chunks: List[Dict]):
        """Add chunks to the vector store"""
        for chunk in chunks:
            # Generate embedding for chunk
            embedding = self._generate_embedding(chunk['text'])
            chunk['embedding'] = embedding
            self.chunk_store.append(chunk)
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text
        
        In production, this would use AWS Bedrock Titan Embeddings
        For now, using simple TF-IDF-like approach for demo
        """
        # Check cache
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        # Simple word-based embedding (replace with Bedrock in production)
        words = text.lower().split()
        vocab = ['transaction', 'kyc', 'aml', 'pmla', 'rbi', 'account', 
                'customer', 'risk', 'compliance', 'verification', 'limit',
                'suspicious', 'report', 'identity', 'document', 'regulation']
        
        # Create vector based on keyword frequency
        embedding = np.zeros(len(vocab))
        for i, keyword in enumerate(vocab):
            embedding[i] = sum(1 for word in words if keyword in word)
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        self.embeddings_cache[text] = embedding
        return embedding
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for most relevant chunks"""
        query_embedding = self._generate_embedding(query)
        
        # Calculate cosine similarity
        results = []
        for chunk in self.chunk_store:
            similarity = self._cosine_similarity(
                query_embedding, 
                chunk['embedding']
            )
            results.append({
                'chunk': chunk,
                'similarity': similarity
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class RAGPipeline:
    """Main RAG Pipeline orchestrator"""
    
    def __init__(self):
        self.chunker = DocumentChunker(chunk_size=512, overlap=50)
        self.vector_search = VectorSearchEngine()
        self.documents_processed = []
    
    def ingest_document(self, document: str, metadata: Dict):
        """Ingest and process a regulatory document"""
        print(f"📄 Ingesting document: {metadata.get('doc_id', 'unknown')}")
        
        # Chunk the document
        chunks = self.chunker.chunk_document(document, metadata)
        print(f"✂️  Created {len(chunks)} chunks")
        
        # Add to vector store
        self.vector_search.add_chunks(chunks)
        print(f"✅ Added to vector store")
        
        # Track processed documents
        self.documents_processed.append({
            'doc_id': metadata.get('doc_id'),
            'doc_type': metadata.get('doc_type'),
            'chunks_count': len(chunks),
            'processed_at': datetime.now().isoformat()
        })
    
    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Query the RAG system"""
        print(f"🔍 Searching for: {query_text}")
        
        results = self.vector_search.search(query_text, top_k=top_k)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'text': result['chunk']['text'],
                'section': result['chunk']['section'],
                'source': result['chunk']['source'],
                'regulation': result['chunk']['regulation'],
                'similarity_score': result['similarity'],
                'citation': f"{result['chunk']['regulation']} - {result['chunk']['section']}"
            })
        
        return formatted_results
    
    def get_stats(self) -> Dict:
        """Get RAG pipeline statistics"""
        return {
            'total_documents': len(self.documents_processed),
            'total_chunks': len(self.vector_search.chunk_store),
            'documents': self.documents_processed
        }


# Example usage
if __name__ == "__main__":
    # Initialize RAG Pipeline
    rag = RAGPipeline()
    
    # Example: Ingest RBI KYC document
    rbi_kyc_doc = """
    Chapter 2: Know Your Customer (KYC) Requirements
    
    Section 2.1: Customer Identification
    Every regulated entity shall obtain sufficient information necessary to establish, 
    to its satisfaction, the identity of each new customer and the purpose of the 
    intended nature of banking relationship.
    
    Section 2.2: Verification Requirements
    The customer identification procedure shall be completed before a business 
    relationship is established. For high-value transactions exceeding INR 50,000, 
    additional verification is mandatory.
    """
    
    rag.ingest_document(rbi_kyc_doc, {
        'doc_id': 'RBI_KYC_2024',
        'doc_type': 'KYC_Guidelines',
        'source': 'RBI Master Circular',
        'regulation': 'RBI',
        'date': '2024-01-15'
    })
    
    # Query the system
    results = rag.query("What are KYC requirements for high value transactions?")
    
    print("\n" + "="*80)
    print("SEARCH RESULTS")
    print("="*80)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['citation']}")
        print(f"   Similarity: {result['similarity_score']:.3f}")
        print(f"   Text: {result['text'][:200]}...")
    
    # Get stats
    stats = rag.get_stats()
    print(f"\n📊 Stats: {stats}")
