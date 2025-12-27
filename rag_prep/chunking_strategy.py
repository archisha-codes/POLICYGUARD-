
"""
Phase-1 RAG Preparation
Chunking strategy: Regulatory-heading-based chunking
Owner: Archisha
"""

import re
from typing import List, Dict

HEADING_PATTERN = re.compile(
    r"""
    ^(
        \d+\.\s+[A-Z][A-Za-z\s()]+ |     # 4. Customer Acceptance Policy (CAP)
        \d+\.\d+\s+[A-Z][A-Za-z\s()]+ |  # 4.1 Sub-section style
        CHAPTER\s+[IVXLC]+ |             # CHAPTER II
        PRELIMINARY |                    # PRELIMINARY
        INTRODUCTION |                   # INTRODUCTION
        [A-Z][A-Z\s]{4,}                 # ALL CAPS HEADINGS
    )$
    """,
    re.VERBOSE
)



def chunk_by_heading(text: str, document_name: str) -> List[Dict]:
    chunks = []
    current = {
        "heading": "INTRODUCTION",
        "content": "",
        "metadata": {
            "document": document_name,
            "section": "INTRODUCTION"
        }
    }

    for line in text.split("\n"):
        line = line.strip()
        if HEADING_PATTERN.match(line):
            if current["content"].strip():
                chunks.append(current)
            current = {
                "heading": line,
                "content": "",
                "metadata": {
                    "document": document_name,
                    "section": line
                }
            }
        else:
            current["content"] += line + " "

    if current["content"].strip():
        chunks.append(current)

    return chunks
