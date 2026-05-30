"""
skill-hybrid-rag-v1 - Hybrid keyword + vector retrieval for local models.

v1.4.0 Local Intelligence & Cost Optimization

Usage:
    from skill_hybrid_rag import HybridRAG
    
    rag = HybridRAG()
    rag.ingest_document("my_doc.txt")
    results = rag.query("What are the key findings?")
"""

__version__ = "0.1.0"  # Scaffold
__author__ = "RockClaw"

from .lib.hybrid_rag import HybridRAG, EvidenceGrade
from .lib.document_ingester import DocumentIngester
from .lib.retriever import HybridRetriever, EvidencePack
from .lib.index_manager import IndexManager

__all__ = [
    "HybridRAG",
    "EvidenceGrade",
    "DocumentIngester",
    "HybridRetriever",
    "EvidencePack",
    "IndexManager",
]
