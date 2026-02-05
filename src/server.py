# src/server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import os
from collections import defaultdict

# Import all your modules
from .ingest import scan_repository
from .chunker import chunk_file
from .vector_store import VectorStore
from .writer import inject_docstrings  # <--- CRITICAL IMPORT

app = FastAPI()
db = VectorStore()

class RepoRequest(BaseModel):
    path: str

class QueryRequest(BaseModel):
    query: str

async def ingest_stream(path: str):
    """
    Full pipeline: Scan -> Chunk -> Index -> Write Docs to Disk
    """
    try:
        # --- PHASE 1: Scan & Chunk ---
        yield json.dumps({"status": "starting", "message": "Phase 1: Scanning files..."}) + "\n"
        
        files = scan_repository(path)
        yield json.dumps({"status": "processing", "message": f"Found {len(files)} files."}) + "\n"
        
        all_chunks = []
        for file in files:
            if file.language == 'python':
                chunks = chunk_file(file)
                all_chunks.extend(chunks)
                yield json.dumps({"status": "processing", "message": f"Chunked {file.file_path} ({len(chunks)} chunks)"}) + "\n"

        # --- PHASE 2 & 3: AI Analysis & Indexing ---
        # Note: db.add_chunks() modifies the 'chunks' list in-place by adding summaries
        yield json.dumps({"status": "processing", "message": f"Phase 2: AI Analysis & Indexing ({len(all_chunks)} chunks)..."}) + "\n"
        
        # We process in batches to show progress
        batch_size = 5
        total = len(all_chunks)
        
        for i in range(0, total, batch_size):
            batch = all_chunks[i : i + batch_size]
            db.add_chunks(batch) # This generates the summaries!
            yield json.dumps({"status": "processing", "message": f"Analyzed & Indexed chunks {i} to {min(i+batch_size, total)}..."}) + "\n"

        # --- PHASE 4: Write Back to Disk ---
        yield json.dumps({"status": "processing", "message": "Phase 3: Writing Docstrings to Files..."}) + "\n"
        
        # Group chunks by their FULL file path so we can open the file once
        file_chunks_map = defaultdict(list)
        for chunk in all_chunks:
            # Construct full system path
            full_path = os.path.join(path, chunk.file_path)
            file_chunks_map[full_path].append(chunk)
            
        # Iterate over files and inject
        for file_path, chunks in file_chunks_map.items():
            file_name = os.path.basename(file_path)
            yield json.dumps({"status": "processing", "message": f"Updating {file_name}..."}) + "\n"
            
            # This is where the file modification happens
            inject_docstrings(file_path, chunks)

        yield json.dumps({"status": "complete", "message": "Ingestion & Documentation Complete!"}) + "\n"

    except Exception as e:
        yield json.dumps({"status": "error", "message": str(e)}) + "\n"

@app.post("/ingest")
async def ingest_repo(request: RepoRequest):
    if not os.path.exists(request.path):
        raise HTTPException(status_code=400, detail="Path not found")
        
    return StreamingResponse(ingest_stream(request.path), media_type="application/x-ndjson")

@app.post("/search")
async def search_docs(request: QueryRequest):
    results = db.search(request.query)
    response = []
    if results['documents']:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            response.append({
                "content": doc,
                "file": meta['file_path'],
                "summary": meta['summary']
            })
    return {"results": response}