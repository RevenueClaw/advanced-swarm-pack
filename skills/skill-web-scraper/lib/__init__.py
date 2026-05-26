"""
Web Scraping Specialist - Advanced Swarm Pack

Elite self-hosted web scraping with multi-layer stealth protection.
Supports: nodriver, camoufox, playwright, simple HTTP
NO paid/managed APIs - strictly self-hosted open-source tools.
"""

__version__ = "1.0.0"
__author__ = "Advanced Swarm Pack"

from .stealth_scraper import StealthScraper, ScrapeResult, ScrapeRequest, main
from .fingerprint_manager import FingerprintManager
from .proxy_rotator import ProxyRotator
from .behavior_engine import BehaviorEngine
from .content_extractor import ContentExtractor

__all__ = [
    "StealthScraper",
    "ScrapeResult",
    "ScrapeRequest",
    "FingerprintManager",
    "ProxyRotator",
    "BehaviorEngine",
    "ContentExtractor",
    "main",
]
