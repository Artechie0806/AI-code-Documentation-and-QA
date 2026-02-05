import os
import textwrap
from typing import List
from .models import CodeChunk

def get_indentation(line: str) -> str:
    """Calculates the leading whitespace of a line."""
    return line[:len(line) - len(line.lstrip())]

def inject_docstrings(file_path: str, chunks: List[CodeChunk]):
    """
    Injects AI-generated summaries. 
    Handles text wrapping for long summaries.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Sort chunks bottom-to-top to preserve line numbers
    chunks.sort(key=lambda x: x.start_line, reverse=True)

    modified_count = 0

    for chunk in chunks:
        if not chunk.summary:
            continue

        # 1. Identify insertion point
        def_line_idx = chunk.start_line - 1
        insert_idx = def_line_idx + 1

        # 2. Check for existing docstrings to avoid duplicates
        if insert_idx < len(lines):
            next_line = lines[insert_idx].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                print(f"Skipping {chunk.chunk_id}: Docstring already exists.")
                continue

        # 3. Calculate Indentation
        base_indent = get_indentation(lines[def_line_idx])
        doc_indent = base_indent + "    " # Standard 4-space indent
        
        # 4. Text Wrapping Logic
        # We calculate how much space we have left on an 80-char line
        # If the indent is deep, we ensure at least 40 chars of text width
        max_width = max(40, 88 - len(doc_indent))
        
        wrapped_lines = textwrap.wrap(chunk.summary, width=max_width)

        if len(wrapped_lines) > 1:
            # Multi-line Paragraph Format
            # """
            # Line 1...
            # Line 2...
            # """
            docstring_content = f'{doc_indent}"""\n'
            for line in wrapped_lines:
                docstring_content += f'{doc_indent}{line}\n'
            docstring_content += f'{doc_indent}"""\n'
        else:
            # Single-line Format
            # """Summary."""
            docstring_content = f'{doc_indent}"""{chunk.summary}"""\n'

        # 5. Insert
        lines.insert(insert_idx, docstring_content)
        modified_count += 1
        print(f"  -> Injected docstring for {chunk.chunk_id}")

    if modified_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Successfully updated {file_path} with {modified_count} docstrings.")
    else:
        print(f"No changes made to {file_path}.")