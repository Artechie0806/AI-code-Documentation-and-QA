from src.ingest import scan_repository
from src.chunker import chunk_file
from src.ai_engine import generate_summary # Assuming you use the updated endpoint version
from src.writer import inject_docstrings
import os
from collections import defaultdict

def main():
    REPO_PATH = "D:/academics/python/Pong game" 
    
    # 1. Scan
    print(f"--- Phase 1: Scanning {REPO_PATH} ---")
    files = scan_repository(REPO_PATH)

    # 2. Chunk & Group by File
    print("\n--- Phase 2: Chunking ---")
    file_chunks_map = defaultdict(list)
    
    for file in files:
        if file.language == 'python':
            chunks = chunk_file(file)
            # We need the FULL system path for the writer to find the file
            full_path = os.path.join(REPO_PATH, file.file_path)
            
            for chunk in chunks:
                # Store full path in chunk for convenience, or map it
                file_chunks_map[full_path].append(chunk)
            
            print(f"  -> {file.file_path}: {len(chunks)} chunks prepared.")

    # 3. Generate & Inject
    print("\n--- Phase 3: AI Generation & Injection ---")
    
    for file_path, chunks in file_chunks_map.items():
        print(f"\nProcessing file: {os.path.basename(file_path)}")
        
        # A. Generate Summaries
        for chunk in chunks:
            print(f"  -> Generating summary for {chunk.chunk_id}...")
            # This calls your local LLM (Qwen/Llama)
            chunk.summary = generate_summary(chunk.code, chunk.chunk_id)
        
        # B. Inject back into code
        inject_docstrings(file_path, chunks)

    print("\nDone! Check your source code.")

if __name__ == "__main__":

    main()
