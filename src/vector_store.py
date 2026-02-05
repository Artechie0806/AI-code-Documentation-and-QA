# src/vector_store.py
import chromadb
from typing import List
from .models import CodeChunk

class VectorStore:
    def __init__(self, persist_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(name="codebase_docs")

    def add_chunks(self, chunks: List[CodeChunk]):
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        # We will batch process this in a real app, but loop is fine for now
        from .ai_engine import get_embedding, generate_summary

        print(f"Processing {len(chunks)} chunks for indexing...")

        for chunk in chunks:
            print(f"  -> AI analyzing: {chunk.chunk_id}...")
            
            # 1. Generate Summary (The "Semantic" part)
            summary = generate_summary(chunk.code, chunk.chunk_id)
            chunk.summary = summary # Update the object
            
            # 2. Prepare Embedding Input (RAG Context)
            # We mix code + structural info + AI summary for better retrieval
            embed_text = f"""
            File: {chunk.file_path}
            Symbol: {chunk.chunk_id}
            Type: {chunk.chunk_type}
            Summary: {summary}
            Code:
            {chunk.code}
            """
            
            vector = get_embedding(embed_text)
            
            if vector:
                ids.append(chunk.chunk_id)
                documents.append(embed_text) # This is what we search against
                embeddings.append(vector)
                metadatas.append({
                    "file_path": chunk.file_path,
                    "type": chunk.chunk_type,
                    "parent": chunk.parent or "",
                    "summary": summary
                })

        # 3. Batch Insert into Chroma
        if ids:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Successfully indexed {len(ids)} chunks.")

    def search(self, query: str, n_results=3):
        from .ai_engine import get_embedding
        query_vec = get_embedding(query)
        
        return self.collection.query(
            query_embeddings=[query_vec],
            n_results=n_results
        )
