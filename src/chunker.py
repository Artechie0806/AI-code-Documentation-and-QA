import ast
from typing import List
from .models import CodeFile, CodeChunk

class PythonChunker(ast.NodeVisitor):
    def __init__(self, file_data: CodeFile):
        self.file_data = file_data
        self.chunks: List[CodeChunk] = []
        self.current_class = None
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Capture class context
        chunk_id = f"{node.name}"
        self._create_chunk(node, "class", chunk_id)
        
        # Enter the class to visit methods
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        # Determine if method or function
        if self.current_class:
            chunk_type = "method"
            chunk_id = f"{self.current_class}.{node.name}"
            parent = self.current_class
        else:
            chunk_type = "function"
            chunk_id = node.name
            parent = None

        self._create_chunk(node, chunk_type, chunk_id, parent)
        # We don't visit internal nodes of functions to keep chunks atomic
    
    def _create_chunk(self, node, chunk_type, chunk_id, parent=None):
        # Extract source code segment
        lines = self.file_data.content.splitlines()
        # ast line numbers are 1-based
        start = node.lineno - 1
        end = node.end_lineno
        chunk_code = "\n".join(lines[start:end])

        self.chunks.append(CodeChunk(
            chunk_id=chunk_id,
            chunk_type=chunk_type,
            file_path=self.file_data.file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            code=chunk_code,
            parent=parent,
            imports=list(set(self.imports)) # Attach current known imports
        ))

def chunk_file(file: CodeFile) -> List[CodeChunk]:
    if file.language != 'python':
        print(f"Skipping chunking for non-python file: {file.file_path}")
        return []
        
    try:
        tree = ast.parse(file.content)
        chunker = PythonChunker(file)
        chunker.visit(tree)
        return chunker.chunks
    except SyntaxError:
        print(f"Syntax Error in {file.file_path}")

        return []
