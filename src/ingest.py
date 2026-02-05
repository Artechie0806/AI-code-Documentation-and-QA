# src/ingest.py
import os
import hashlib
from typing import List
from .models import CodeFile

# Configuration
INCLUDE_EXTENSIONS = {'.py', '.js', '.ts', '.java', '.go'}
EXCLUDE_DIRS = {'node_modules', 'venv', 'dist', 'build', '__pycache__', '.git'}

def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def scan_repository(repo_path: str) -> List[CodeFile]:
    results = []
    
    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext not in INCLUDE_EXTENSIONS:
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                loc = len(content.splitlines())
                file_hash = calculate_hash(content)
                
                # Basic language detection map
                lang_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript'}
                
                results.append(CodeFile(
                    file_path=rel_path,
                    language=lang_map.get(ext, 'unknown'),
                    content=content,
                    file_hash=file_hash,
                    loc=loc
                ))
            except Exception as e:
                print(f"Skipping {rel_path}: {e}")
                
    return results